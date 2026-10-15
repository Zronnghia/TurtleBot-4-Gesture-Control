#!/usr/bin/env python3
"""Vẽ các sơ đồ khối cho báo cáo (docs/report/fig/*.png). Chạy: python3 docs/report/diagrams.py"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fig')
os.makedirs(OUT, exist_ok=True)
plt.rcParams['font.family'] = 'DejaVu Sans'

KIND = {                       # (nền, viền)
    'blue': ('#dbe8f7', '#4a76a8'),     # gói chính thức (TurtleBot 4, Nav2, ROS)
    'orange': ('#fde4d0', '#d9783a'),   # bổ sung của package tb4_lab04
    'green': ('#e2f0d9', '#5b9a3a'),    # dữ liệu / bản đồ / kết quả
    'grey': ('#eeeeee', '#777777'),     # Gazebo, thành phần ngoài
    'red': ('#f8d7d7', '#c0504d'),      # lỗi / dừng
    'white': ('#ffffff', '#555555'),
}


def canvas(w_in, h_units, w_units=100, y0=0):
    fig = plt.figure(figsize=(w_in, w_in * (h_units - y0) / w_units))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w_units)
    ax.set_ylim(y0, h_units)
    ax.axis('off')
    return fig, ax


def layer(ax, x0, y0, x1, y1, title, color='#8899aa', center=False, bottom=False):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle='round,pad=0,rounding_size=1.2',
                                fc='none', ec=color, lw=0.9, ls=(0, (4, 3))))
    ax.text((x0 + x1) / 2 if center else x0 + 1.2, (y0 + 1.0) if bottom else (y1 - 1.1), title, fontsize=6.3,
            style='italic', color=color, va='bottom' if bottom else 'top', ha='center' if center else 'left')


def box(ax, cx, cy, w, h, text, kind='blue', fs=6.6, mono=False, bold=False):
    fc, ec = KIND[kind]
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle='round,pad=0,rounding_size=0.9',
                                fc=fc, ec=ec, lw=0.9))
    ax.text(cx, cy, text, fontsize=fs, ha='center', va='center', linespacing=1.25,
            family='DejaVu Sans Mono' if mono else 'DejaVu Sans', fontweight='bold' if bold else 'normal')


def diamond(ax, cx, cy, w, h, text, kind='orange', fs=6.4):
    fc, ec = KIND[kind]
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
                         closed=True, fc=fc, ec=ec, lw=0.9))
    ax.text(cx, cy, text, fontsize=fs, ha='center', va='center', linespacing=1.25)


def arrow(ax, p0, p1, label=None, lpos=0.5, fs=5.6, color='#444444', rad=0.0, ls='-', rot=0,
          loff=(0, 0), both=False):
    ax.annotate('', xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle='<|-|>' if both else '-|>', color=color, lw=0.8, ls=ls, shrinkA=0,
                                shrinkB=0, mutation_scale=7, connectionstyle='arc3,rad={}'.format(rad)))
    if label:
        x = p0[0] + (p1[0] - p0[0]) * lpos + loff[0]
        y = p0[1] + (p1[1] - p0[1]) * lpos + loff[1]
        ax.text(x, y, label, fontsize=fs, ha='center', va='center', rotation=rot, color='#222222',
                family='DejaVu Sans Mono', bbox=dict(fc='white', ec='none', pad=0.6, alpha=0.9))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=230, facecolor='white', bbox_inches='tight', pad_inches=0.06)
    plt.close(fig)
    print('đã vẽ', name)


# ---------------------------------------------------------------------------------------- Hình 1
def fig_system():
    fig, ax = canvas(7.6, 90)
    layer(ax, 1, 77, 99, 89, 'Người dùng')
    box(ax, 12, 82.5, 20, 6.6, 'Terminal: log điều hướng\nvà bảng TỔNG KẾT', 'white')
    box(ax, 42, 82.5, 36, 6.6, 'RViz2: bản đồ, LiDAR, hạt AMCL, /plan,\nmarker goal, ảnh YOLO, Publish Point')
    box(ax, 88, 82.5, 18, 6.6, 'Cửa sổ OpenCV\n(ảnh + bounding box)', 'white')

    layer(ax, 1, 51, 99, 71, 'Bổ sung của package tb4_lab04', '#d9783a', center=True)
    box(ax, 15, 60, 23, 9.5, 'waypoint_navigator.py\nBasicNavigator: G1→G2→G3\n(undock, initial pose, retry)', 'orange', 6.2)
    box(ax, 41, 60, 17, 9.5, 'dock_obstacle.py\nvật cản = thân dock\ntrong costmap', 'orange', 6.2)
    box(ax, 63, 60, 17, 9.5, 'scan_delay\n(topic_tools)\n/scan → /scan_nav', 'orange', 6.2)
    box(ax, 88, 60, 20, 9.5, 'yolo_detector.py\ncv_bridge → YOLO11n\nvẽ bbox, lưu kết quả', 'orange', 6.2)

    layer(ax, 1, 28, 76, 48, 'Định vị và dẫn đường', bottom=True)
    box(ax, 13, 37, 16, 8, 'map_server\nmap.yaml, map.pgm')
    box(ax, 34, 37, 16, 8, 'amcl\n(bộ lọc hạt)')
    box(ax, 62, 37, 26, 11, 'Nav2: bt_navigator, planner_server,\ncontroller_server, behavior_server,\nvelocity_smoother, costmap', fs=6.2)

    layer(ax, 1, 11, 99, 25, 'Robot TurtleBot 4 / Create 3', center=True)
    box(ax, 13, 16.5, 19, 7, 'robot_state_publisher\n(TF tĩnh từ URDF)')
    box(ax, 38, 16.5, 19, 7, 'diffdrive_controller\n(ros2_control)')
    box(ax, 63, 16.5, 19, 7, 'motion_control\n(Create 3, dock/undock)')
    box(ax, 89, 16.5, 17, 7, 'ros_gz_bridge')

    box(ax, 58, 4.2, 76, 6.2, 'Gazebo Fortress – world maze + vật thể (người, xe, ghế, trụ cứu hoả, bình chữa cháy)\n'
        'RPLIDAR 2D, camera OAK-D, bánh vi sai, bumper, dock sạc', 'grey', 6.3)
    box(ax, 9.5, 4.2, 16, 6.2, 'spawn_objects.py\n(model từ Fuel)', 'orange', 6.2)

    # người dùng
    arrow(ax, (12, 65), (12, 79.2), 'log, TỔNG KẾT', 0.5, rot=90, fs=5.2)
    arrow(ax, (25, 65), (30, 79.2), '/nav_goals/markers', 0.5, rot=75, fs=4.8)
    arrow(ax, (84, 65), (60, 79.2), '/yolo/image_annotated', 0.5, fs=5.2)
    arrow(ax, (94, 65), (94, 79.2), None)
    # navigator -> amcl / nav2
    arrow(ax, (10, 55.2), (29, 41), '/initialpose', 0.45)
    arrow(ax, (21, 55.2), (50, 42.5), 'NavigateToPose', 0.55)
    # scan, dock
    arrow(ax, (59, 55.2), (37, 41), '/scan_nav', 0.22)
    arrow(ax, (66, 55.2), (66, 42.5), '/scan_nav', 0.5)
    arrow(ax, (42, 55.2), (56, 42.5), '/dock_obstacle', 0.72, fs=5.0)
    # camera, scan
    arrow(ax, (94, 20.0), (94, 55.2), '/oakd/rgb/preview/image_raw', 0.5, rot=90, fs=5.4)
    arrow(ax, (84, 20.0), (73, 55.2), '/scan', 0.7, rot=78)
    # map, tf
    arrow(ax, (21, 37), (26, 37), '/map', 0.5, loff=(0, 2.6), fs=5.2)
    arrow(ax, (42, 37), (49, 37), 'TF map→odom', 0.5, loff=(0, 3.4), fs=5.0)
    # nav2 -> robot
    arrow(ax, (62, 31.5), (62, 20.0), '/cmd_vel', 0.5)
    arrow(ax, (53.5, 16.5), (47.5, 16.5), 'v, ω', 0.5, loff=(0, 2.2))
    arrow(ax, (36, 20.0), (36, 33), '/odom, TF odom→base_link', 0.5, rot=90, fs=5.0)
    # gazebo
    for x in (38, 63, 89):
        arrow(ax, (x, 7.3), (x, 13.0), None, both=True)
    arrow(ax, (20, 4.2), (17.5, 4.2), None)
    save(fig, 'fig_system.png')


# ---------------------------------------------------------------------------------------- Hình 2
def fig_startup():
    fig, ax = canvas(7.6, 44)
    box(ax, 10, 23, 15, 9, 'ros2 launch\ntb4_lab04\ndemo.launch.py', 'grey', 6.4, mono=True)
    diamond(ax, 30, 23, 15, 12, 'Đủ gói ROS\nvà bản đồ?')
    box(ax, 30, 5.5, 20, 8.5, 'In thiếu gì + lệnh apt\nrồi dừng (không\nkhởi chạy nửa vời)', 'red', 6.2)
    box(ax, 52, 23, 17, 9, 'Gazebo + TurtleBot 4\n+ RViz2\n(world maze)', 'blue', 6.4)
    box(ax, 72, 23, 17, 9, 'wait_for_sim.py\n/clock chạy ≥ 2 s\nvà có /odom', 'orange', 6.4)
    box(ax, 92, 36, 15.5, 7.5, 'spawn_objects.py\nđặt 7 vật thể', 'orange', 6.2)
    box(ax, 92, 25.5, 15.5, 9, '+2 s: map_server,\namcl, scan_delay,\ndock_obstacle', 'blue', 6.2)
    box(ax, 92, 14, 15.5, 7, '+8 s: Nav2', 'blue', 6.2)
    box(ax, 72, 5.5, 20, 7.5, '+25 s: yolo_detector.py\n+ waypoint_navigator.py', 'orange', 6.2)
    arrow(ax, (17.5, 23), (22.5, 23))
    arrow(ax, (37.5, 23), (43.5, 23), 'đủ', 0.5, loff=(0, 2.0))
    arrow(ax, (30, 17), (30, 9.8), 'thiếu', 0.5, loff=(3.2, 0))
    arrow(ax, (60.5, 23), (63.5, 23))
    arrow(ax, (80.5, 25), (84, 25.5), None)
    arrow(ax, (80.5, 29), (84.2, 35), None)
    arrow(ax, (80.5, 21), (84.2, 15), None)
    arrow(ax, (72, 18.5), (72, 9.3), 'sau navigator_delay', 0.55, loff=(7.5, 0), fs=5.2)
    ax.text(50, 41.5, 'Navigator tự chờ amcl và bt_navigator ở trạng thái active trước khi gửi goal\n'
            '(không phụ thuộc đúng vào mốc 25 s – máy chậm vẫn an toàn)', fontsize=5.8, ha='center', color='#a05a20',
            style='italic')
    save(fig, 'fig_startup.png')


# ---------------------------------------------------------------------------------------- Hình 3 (TF)
def fig_tf():
    fig, ax = canvas(4.4, 62, 70)
    box(ax, 35, 56, 16, 5, 'map', 'green', 7.5, mono=True)
    box(ax, 35, 38, 16, 5, 'odom', 'green', 7.5, mono=True)
    box(ax, 59, 38, 17, 5, 'std_dock_link', 'grey', 6.4, mono=True)
    box(ax, 35, 20, 16, 5, 'base_link', 'green', 7.5, mono=True)
    box(ax, 10, 4, 18, 6, 'rplidar_link\n→ /scan', 'blue', 6.0, mono=True)
    box(ax, 35, 4, 18, 6, 'oakd_*_link\n(camera RGB)', 'blue', 6.0, mono=True)
    box(ax, 60, 4, 18, 6, 'wheel_*, bumper,\ncliff, ir_*…', 'blue', 6.0, mono=True)
    arrow(ax, (35, 53.4), (35, 40.6))
    ax.text(36.5, 47, 'amcl (map → odom)\nbù trôi odometry', fontsize=5.6, ha='left', va='center', style='italic',
            color='#335577')
    arrow(ax, (35, 35.4), (35, 22.6))
    ax.text(36.5, 29, 'diffdrive_controller\nodometry bánh xe', fontsize=5.6, ha='left', va='center', style='italic',
            color='#335577')
    arrow(ax, (43.2, 38), (50.3, 38), 'TF tĩnh', 0.5, loff=(0, 2.2), fs=5.2)
    for x in (10, 35, 60):
        arrow(ax, (35, 17.4), (x, 7.2))
    ax.text(62, 12.5, 'robot_state_publisher\n(TF tĩnh từ URDF)', fontsize=5.6, ha='left', style='italic', color='#335577')
    save(fig, 'fig_tf.png')


# ---------------------------------------------------------------------------------------- Hình 4 (AMCL)
def fig_amcl():
    fig, ax = canvas(7.6, 34)
    box(ax, 10, 26, 17, 8, 'Khởi tạo 500–2000 hạt\nquanh (0, 0, 0) hoặc\n/initialpose', 'grey', 6.2)
    box(ax, 36, 26, 19, 8, 'Dự đoán: dịch mỗi hạt theo\nodometry + nhiễu (α1…α5)', 'blue', 6.2)
    diamond(ax, 62, 26, 21, 12, 'Robot đi ≥ 0,25 m\nhoặc quay ≥ 0,2 rad?', 'orange', 6.0)
    box(ax, 89, 26, 18, 8, 'Cập nhật trọng số\n= độ khớp /scan_nav với\nbản đồ (likelihood field)', 'blue', 6.0)
    box(ax, 89, 9, 18, 8, 'Lấy mẫu lại (resample),\nKLD điều chỉnh số hạt;\nlặp lại từ bước dự đoán', 'blue', 6.0)
    box(ax, 55, 9, 24, 8, 'Phát TF map→odom\nvà /amcl_pose (pose + hiệp phương sai)', 'green', 6.2)
    arrow(ax, (18.5, 26), (26.5, 26))
    arrow(ax, (45.5, 26), (51.5, 26))
    arrow(ax, (72.5, 26), (80, 26), 'có', 0.5, loff=(0, 2.2))
    arrow(ax, (89, 22), (89, 13), None)
    arrow(ax, (80, 9), (67, 9), None)
    # nhánh "chưa": quay lại bước dự đoán, đứng yên thì giữ nguyên tập hạt
    ax.plot([62, 62, 36, 36], [20, 15.5, 15.5, 22], color='#444444', lw=0.8)
    ax.annotate('', xy=(36, 22), xytext=(36, 20.5), arrowprops=dict(arrowstyle='-|>', color='#444444', lw=0.8,
                                                                    mutation_scale=7))
    ax.text(49, 17.2, 'chưa: giữ nguyên tập hạt (robot đứng yên)', fontsize=5.6, ha='center', color='#222222',
            family='DejaVu Sans')
    save(fig, 'fig_amcl.png')


# ---------------------------------------------------------------------------------------- Hình 5 (Nav2)
def fig_nav2():
    fig, ax = canvas(7.6, 50)
    box(ax, 13, 40, 20, 8, 'waypoint_navigator.py\n(BasicNavigator.goToPose)', 'orange', 6.2)
    box(ax, 40, 40, 20, 9, 'bt_navigator\nBehavior Tree: lập lại\nkế hoạch 1 Hz + hồi phục', 'blue', 6.2)
    box(ax, 66, 40, 20, 8, 'planner_server\nNavFn (Dijkstra)', 'blue', 6.2)
    box(ax, 90, 40, 17, 8, 'global costmap\nstatic + obstacle\n+ dock + inflation', 'blue', 6.0)
    box(ax, 40, 24, 20, 8, 'behavior_server\nspin, backup, wait', 'blue', 6.2)
    box(ax, 66, 24, 20, 8, 'controller_server\nDWB, 20 Hz', 'blue', 6.2)
    box(ax, 90, 24, 17, 8, 'local costmap\n3×3 m, voxel\n+ dock + inflation', 'blue', 6.0)
    box(ax, 40, 8, 20, 8, 'motion_control\n(Create 3) → bánh xe', 'grey', 6.2)
    box(ax, 66, 8, 20, 8, 'velocity_smoother\ngiới hạn v, a', 'blue', 6.2)
    box(ax, 90, 8, 17, 8, 'map_server /map\n/scan_nav, TF (AMCL)\n/dock_obstacle', 'green', 5.6)
    arrow(ax, (23, 40), (30, 40), 'NavigateToPose', 0.5, loff=(0, 2.4), fs=5.0)
    arrow(ax, (50, 40), (56, 40), 'ComputePath\nToPose', 0.5, loff=(0, 5.2), fs=4.6)
    arrow(ax, (76, 40), (81.5, 40), None, both=True)
    arrow(ax, (40, 35.5), (40, 28), 'hồi phục', 0.5, loff=(4, 0), fs=5.2)
    arrow(ax, (47, 36), (58, 28), 'FollowPath', 0.62, loff=(3.5, 1.6), fs=5.0)
    arrow(ax, (66, 36), (66, 28), '/plan', 0.5, loff=(3, 0), fs=5.2)
    arrow(ax, (76, 24), (81.5, 24), None, both=True)
    arrow(ax, (66, 20), (66, 12), '/cmd_vel_nav', 0.5, loff=(5.5, 0), fs=5.0)
    arrow(ax, (56, 8), (50, 8), '/cmd_vel', 0.5, loff=(0, 2.2), fs=5.2)
    arrow(ax, (90, 12), (90, 20), None)
    ax.plot([98.5, 99.6, 99.6], [8, 8, 40], color='#444444', lw=0.8)
    arrow(ax, (99.6, 40), (98.5, 40), None)
    save(fig, 'fig_nav2.png')


# ---------------------------------------------------------------------------------------- Hình 6 (navigator)
def fig_navigator():
    fig, ax = canvas(6.4, 100)
    box(ax, 40, 94, 26, 7, 'Chờ amcl và bt_navigator\nở trạng thái active', 'blue', 6.3)
    diamond(ax, 40, 82, 28, 11, 'Robot đang\nở dock?', 'orange', 6.4)
    box(ax, 82, 82, 30, 10, 'Đặt /initialpose\n(goals.yaml, hiệp phương sai 0,25)\nrồi undock (≤ 60 s mô phỏng)', 'blue', 5.8)
    box(ax, 40, 64, 26, 8, 'goToPose(Gk)\ngửi NavigateToPose', 'blue', 6.3)
    box(ax, 40, 51, 26, 9, 'Theo dõi feedback: in\ncòn ... m, ETA, số lần hồi phục', 'blue', 5.8)
    diamond(ax, 40, 38, 28, 11, 'Kết quả\ntask?', 'orange', 6.4)
    box(ax, 84, 38, 24, 11, 'SUCCEEDED: lưu sai số\nvị trí/hướng; dừng\npause_at_goal giây', 'green', 5.6)
    box(ax, 11, 38, 20, 11, 'FAILED / TIMEOUT:\nclearAllCostmaps,\nthử lại ≤ max_retries', 'red', 5.4)
    box(ax, 84, 16, 24, 10, 'Hết goal: in bảng\nTỔNG KẾT, lưu run.json\nvà summary.csv', 'green', 5.6)
    box(ax, 18, 16, 32, 10, 'Ctrl+C bất kỳ lúc nào: huỷ goal đang\nchạy, robot dừng, vẫn lưu kết quả', 'red', 5.6)

    arrow(ax, (40, 90.5), (40, 87.5))
    arrow(ax, (54, 82), (67, 82), 'có', 0.5, loff=(0, 2.4), fs=5.4)
    arrow(ax, (40, 76.5), (40, 68), 'không: giữ pose AMCL,\nkhông undock', 0.5, fs=5.2)
    ax.plot([82, 82], [77, 64], color='#444444', lw=0.8)
    arrow(ax, (84, 64), (53, 64), None)
    ax.plot([84, 84], [43.5, 64], color='#444444', lw=0.8)
    ax.text(86.5, 54, 'còn goal', fontsize=5.4, rotation=90, ha='center', va='center', family='DejaVu Sans Mono')
    arrow(ax, (40, 60), (40, 55.5))
    arrow(ax, (40, 46.5), (40, 43.5))
    arrow(ax, (54, 38), (72, 38), 'tới nơi', 0.5, loff=(0, 2.4), fs=5.4)
    arrow(ax, (26, 38), (21, 38), None)
    ax.text(23.5, 40.6, 'lỗi', fontsize=5.4, ha='center', family='DejaVu Sans Mono')
    ax.plot([11, 11], [43.5, 64], color='#444444', lw=0.8)
    arrow(ax, (11, 64), (27, 64), 'thử lại', 0.5, loff=(0, 2.4), fs=5.4)
    arrow(ax, (84, 32.5), (84, 21), 'hết goal', 0.5, rot=90, fs=5.4)
    save(fig, 'fig_navigator.png')


# ---------------------------------------------------------------------------------------- Hình 7 (YOLO)
def fig_yolo():
    fig, ax = canvas(7.6, 42, y0=-5.5)
    box(ax, 9, 32, 15, 8, 'Camera OAK-D\n(Gazebo) 320×240\nrgb8, 30 Hz', 'grey', 6.0)
    box(ax, 31, 32, 19, 8, 'ros_gz_bridge\n/oakd/rgb/preview/\nimage_raw', 'blue', 5.8)
    box(ax, 54, 32, 20, 8, 'yolo_detector.py\ncallback: giữ khung mới\nnhất (QoS sensor data)', 'orange', 5.8)
    box(ax, 80, 32, 22, 8, 'Luồng suy luận: cv_bridge\n(sensor_msgs/Image\n→ BGR OpenCV)', 'orange', 5.8)
    box(ax, 80, 15, 22, 9, 'YOLO11n (ultralytics)\nimgsz 640, conf 0,35,\nIoU 0,5, ≤ 5 ảnh/s\n→ lớp, conf, bbox', 'blue', 5.8)
    box(ax, 52, 15, 22, 9, 'Vẽ bounding box,\ntên lớp, độ tự tin;\nHUD: FPS, pose robot', 'orange', 5.8)
    box(ax, 12, 24, 20, 6.5, 'Cửa sổ OpenCV\n(window_scale 2)', 'white', 5.8)
    box(ax, 12, 13, 20, 6.5, '/yolo/image_annotated\n→ panel YOLO trong RViz2', 'blue', 5.6)
    box(ax, 12, 2, 20, 6.5, '/yolo/detections\n(vision_msgs)', 'blue', 5.6)
    box(ax, 48, -1, 30, 6.5, 'In Terminal + ~/tb4_results/yolo_*/\ndetections.csv, first_*, best_*', 'green', 5.6)
    arrow(ax, (16.5, 32), (21.5, 32))
    arrow(ax, (40.5, 32), (44, 32))
    arrow(ax, (64, 32), (69, 32))
    arrow(ax, (80, 28), (80, 19.5))
    arrow(ax, (69, 15), (63, 15))
    arrow(ax, (41, 17), (22, 24), None)
    arrow(ax, (41, 15), (22, 13), None)
    arrow(ax, (41, 13), (22, 3.5), None)
    arrow(ax, (50, 10.5), (50, 2.3), None)
    save(fig, 'fig_yolo.png')


def main():
    fig_system()
    fig_startup()
    fig_tf()
    fig_amcl()
    fig_nav2()
    fig_navigator()
    fig_yolo()


if __name__ == '__main__':
    main()
