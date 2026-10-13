# Bài thực hành 04 – Phần 3 + 4: Localization (AMCL) và Navigation (Nav2) trên bản đồ đã tạo.
#
# Khởi chạy: Gazebo + TurtleBot 4 (spawn lại ở CÙNG vị trí như lúc mapping)
#            + map_server/AMCL (turtlebot4_navigation/localization.launch.py,
#              config/localization.yaml)
#            + Nav2 (turtlebot4_navigation/nav2.launch.py, config/nav2.yaml)
#            + RViz2 (fixed frame map, có công cụ "Nav2 Goal").
#
#   ros2 launch tb4_lab04 navigation.launch.py                     # tự tìm maps/map.yaml của repo
#   ros2 launch tb4_lab04 navigation.launch.py use_nav2:=false     # chỉ localization (Phần 3)
#   ros2 launch tb4_lab04 navigation.launch.py map:=/duong/dan/map.yaml
#
# Thứ tự tìm bản đồ khi KHÔNG truyền map:=
#   1) <thư mục source của package>/maps/map.yaml  (nơi save_map.sh lưu – luôn là bản mới nhất)
#   2) <install>/share/tb4_lab04/maps/map.yaml     (bản được copy lúc colcon build)
# Không tìm thấy hoặc file hỏng -> báo lỗi rõ ràng và dừng, KHÔNG khởi chạy nửa vời.
#
# Xem "LƯU Ý KỸ THUẬT" trong tb4_lab04_common.py về scope của launch configuration ở Humble.

import os
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
                            LogInfo, OpaqueFunction, Shutdown,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tb4_lab04_common as common  # noqa: E402

PKG = common.PKG
BOND_TIMEOUT = 15.0
SCAN_DELAY = 0.1


def _source_dir(pkg_share):
    """Đọc đường dẫn thư mục source mà CMake ghi lại lúc build (có thể không tồn tại)."""
    marker = os.path.join(pkg_share, 'source_dir.txt')
    try:
        with open(marker, 'r', encoding='utf-8') as f:
            path = f.read().strip()
    except OSError:
        return None
    return path if path and os.path.isdir(path) else None


def find_map(user_map, pkg_share):
    """Trả về (đường_dẫn_map, None) hoặc (None, thông_báo_lỗi)."""
    if user_map:
        path = os.path.abspath(os.path.expanduser(user_map))
        if not os.path.isfile(path):
            return None, 'Không tìm thấy file bản đồ: {}'.format(path)
        return path, None
    tried = []
    src = _source_dir(pkg_share)
    if src:
        tried.append(os.path.join(src, 'maps', 'map.yaml'))
    tried.append(os.path.join(pkg_share, 'maps', 'map.yaml'))
    for path in tried:
        if os.path.isfile(path):
            return path, None
    return None, ('Chưa có bản đồ. Đã tìm ở:\n    ' + '\n    '.join(tried) +
                  '\n  -> Làm Phần 2 và chạy `ros2 run tb4_lab04 save_map.sh` trước, '
                  'hoặc truyền map:=/duong/dan/tuyet/doi/map.yaml')


def validate_map_yaml(path):
    """Kiểm tra nhanh file map.yaml theo đúng cách nav2_map_server đọc. Trả về lỗi hoặc None."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        return 'Không đọc được {}: {}'.format(path, exc)
    if not isinstance(data, dict):
        return '{} không phải YAML dạng map (key: value)'.format(path)
    for key in ('image', 'resolution', 'origin'):
        if key not in data:
            return '{} thiếu khoá bắt buộc "{}"'.format(path, key)
    image = str(data['image'])
    if not image:
        return '{}: khoá "image" rỗng'.format(path)
    if not os.path.isabs(image):
        image = os.path.join(os.path.dirname(path), image)
    if not os.path.isfile(image):
        return 'File ảnh bản đồ không tồn tại: {} (khai báo trong {})'.format(image, path)
    try:
        if float(data['resolution']) <= 0.0:
            return '{}: resolution phải > 0'.format(path)
    except (TypeError, ValueError):
        return '{}: resolution không phải số'.format(path)
    origin = data['origin']
    if not isinstance(origin, (list, tuple)) or len(origin) != 3:
        return '{}: origin phải có dạng [x, y, yaw]'.format(path)
    return None


def launch_setup(context, *args, **kwargs):
    pkg_lab = get_package_share_directory(PKG)
    pkg_tb4_nav = get_package_share_directory('turtlebot4_navigation')

    map_path, err = find_map(LaunchConfiguration('map').perform(context).strip(), pkg_lab)
    if err is None:
        err = validate_map_yaml(map_path)
    if err is not None:
        return [
            LogInfo(msg='\n\n[tb4_lab04] LỖI BẢN ĐỒ: ' + err + '\n'),
            Shutdown(reason='tb4_lab04: thiếu hoặc hỏng file bản đồ'),
        ]

    # Scope nằm TRONG TimerAction (nếu đặt ngược, scope đã đóng khi timer kích hoạt).
    localization = TimerAction(
        period=LaunchConfiguration('localization_delay'),
        actions=[
            LogInfo(msg='[tb4_lab04] Khởi động map_server + AMCL với bản đồ ' + map_path),
            GroupAction(
                scoped=True,
                actions=[
                    # Máy chậm: heartbeat bond mặc định 4 s của lifecycle_manager hay hết hạn
                    # ("Server amcl was unable to be reached after 4.00s by bond").
                    SetParameter(name='bond_timeout', value=BOND_TIMEOUT),
                    # /scan_nav = /scan trễ 0.1 s (giờ mô phỏng) cho AMCL và 2 costmap của Nav2.
                    # Lý do: tf2_ros trên Humble có deadlock (Buffer::waitForTransform <->
                    # BufferCore::setTransformImpl) khi scan đến TRƯỚC transform odom->base_link
                    # tương ứng; đã tái hiện và xác nhận bằng gdb (docs/TEST_REPORT.md). Trễ 0.1 s
                    # đảm bảo transform luôn có sẵn khi scan tới -> không phát sinh yêu cầu chờ TF.
                    Node(package='topic_tools', executable='delay', name='scan_delay',
                         output='screen',
                         parameters=[{'input_topic': '/scan', 'output_topic': '/scan_nav',
                                      'delay': SCAN_DELAY, 'use_sim_time': True}]),
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource(
                            os.path.join(pkg_tb4_nav, 'launch', 'localization.launch.py')),
                        launch_arguments={
                            'namespace': '',
                            'use_sim_time': 'true',
                            'map': map_path,
                            'params': LaunchConfiguration('localization_params_file'),
                        }.items(),
                    ),
                ],
            ),
        ],
    )

    nav2 = TimerAction(
        period=LaunchConfiguration('nav2_delay'),
        condition=IfCondition(LaunchConfiguration('use_nav2')),
        actions=[
            LogInfo(msg='[tb4_lab04] Khởi động Nav2 ...'),
            GroupAction(
                scoped=True,
                actions=[
                    SetParameter(name='bond_timeout', value=BOND_TIMEOUT),
                    # Dock thấp hơn mặt quét LiDAR -> đánh dấu cho costmap (dock_layer, nav2.yaml).
                    Node(package='tb4_lab04', executable='dock_obstacle.py',
                         name='tb4_lab04_dock_obstacle', output='screen'),
                    IncludeLaunchDescription(
                        PythonLaunchDescriptionSource(
                            os.path.join(pkg_tb4_nav, 'launch', 'nav2.launch.py')),
                        launch_arguments={
                            'namespace': '',
                            'use_sim_time': 'true',
                            'params_file': LaunchConfiguration('nav2_params_file'),
                        }.items(),
                    ),
                ],
            ),
        ],
    )

    # Chỉ bật localization + Nav2 khi mô phỏng THỰC SỰ chạy (wait_for_sim.py thoát).
    wait_for_sim = common.wait_for_sim_node()
    start_stack = common.after_sim_ready(wait_for_sim, [localization, nav2])

    return [
        LogInfo(msg='[tb4_lab04] Dùng bản đồ: ' + map_path),
        common.rviz_node(),
        common.turtlebot4_sim(),
        wait_for_sim,
        start_stack,
    ]


def generate_launch_description():
    abort = common.abort_if_missing(common.PKGS_SIM + common.PKGS_NAV)
    if abort is not None:
        return abort
    pkg_lab = get_package_share_directory(PKG)

    arguments = common.sim_arguments(
        'nav.rviz', world_note='PHẢI giống world lúc mapping (vị trí spawn x, y, yaw cũng vậy)') + [
        DeclareLaunchArgument('map', default_value='',
                              description='Đường dẫn map.yaml (để trống = tự tìm maps/map.yaml)'),
        DeclareLaunchArgument('use_nav2', default_value='true', choices=['true', 'false'],
                              description='false = chỉ chạy localization (Phần 3)'),
        DeclareLaunchArgument('localization_params_file',
                              default_value=os.path.join(pkg_lab, 'config', 'localization.yaml'),
                              description='Tham số AMCL + map_server'),
        DeclareLaunchArgument('nav2_params_file',
                              default_value=os.path.join(pkg_lab, 'config', 'nav2.yaml'),
                              description='Tham số Nav2'),
        DeclareLaunchArgument('localization_delay', default_value='2.0',
                              description='Số giây chờ thêm (sau khi mô phỏng đã chạy) '
                                          'rồi mới bật localization'),
        DeclareLaunchArgument('nav2_delay', default_value='8.0',
                              description='Số giây chờ thêm (sau khi mô phỏng đã chạy) '
                                          'rồi mới bật Nav2'),
    ]

    return LaunchDescription(arguments + common.render_env()
                             + [OpaqueFunction(function=launch_setup)])
