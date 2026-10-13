# Báo cáo Bài thực hành 04 – TurtleBot 4 Simulation (BẢN NHÁP)

> Bản nháp để chuyển thành PDF. Các chỗ `[[...]]` là phần bạn phải tự điền/chụp.
> Chuyển sang PDF: mở bằng VS Code + extension "Markdown PDF", hoặc
> `pandoc REPORT_DRAFT.md -o report.pdf` (cần `sudo apt install pandoc texlive-xetex`,
> thêm `--pdf-engine=xelatex -V mainfont="DejaVu Sans"` để hiện tiếng Việt).

- Họ tên / MSSV: [[...]]
- Video demo (Google Drive, công khai): [[link]]
- GitHub repository (Public): [[link]]
- Môi trường: Ubuntu 22.04, ROS 2 Humble, Ignition Gazebo Fortress [[phiên bản `ign gazebo --versions`]],
  world `maze` [[đổi nếu bạn dùng world khác]].

---

## 1. Cấu trúc chương trình

Package `tb4_lab04` (ament_cmake) không tự viết simulator/controller mà ghép các launch chính thức:

| Launch | Thành phần khởi chạy | Dùng cho |
|---|---|---|
| `sim.launch.py` | `turtlebot4_ignition_bringup/turtlebot4_ignition.launch.py` + RViz2 (fixed frame `odom`) | Phần 1 |
| `mapping.launch.py` | như trên + `turtlebot4_navigation/slam.launch.py` (SLAM Toolbox sync) + RViz2 (`map`) | Phần 2 |
| `navigation.launch.py` | như trên + `localization.launch.py` (map_server, AMCL) + `nav2.launch.py` (Nav2) | Phần 3, 4 |

Phần dùng chung của 3 launch (kiểm tra gói đã cài, tham số chung, include TurtleBot 4, RViz2) nằm trong
`launch/tb4_lab04_common.py`.

Cấu hình: `config/slam.yaml`, `config/localization.yaml`, `config/nav2.yaml` dựa trên bản gốc
TurtleBot 4. Các thay đổi (lý do chi tiết ở README mục 9.3):
- AMCL tự đặt initial pose (0, 0, 0) – trùng điểm spawn, cũng là gốc frame `map` khi mapping;
- AMCL và 2 costmap đọc `/scan_nav` (= `/scan` trễ 0.1 s bằng `topic_tools delay`) để tránh treo TF trên Humble;
- thêm lớp costmap `dock_layer` (dock thấp hơn mặt quét LiDAR nên bản đồ không có dock);
- `bond_timeout` của lifecycle manager 15 s; tắt riêng phản xạ cliff của Create 3 (`cliff_reflex:=false`).

Script hỗ trợ: `check_sensors.py`, `check_sim.py`, `save_map.sh`, `check_map.py`, `compare_pose.py`,
`nav_monitor.py`; `wait_for_sim.py` và `dock_obstacle.py` do launch tự gọi.

[[Hình: sơ đồ `rqt_graph` hoặc sơ đồ khối dưới đây]]

```
 Gazebo (Fortress) ──ros_gz_bridge──► /scan, /clock, ...        ┌──────────────┐
     ▲   diffdrive_controller (ros2_control) ──► /odom, TF odom→base_link        │
     │                                                          │   RViz2       │
 /cmd_vel ◄── motion_control (Create 3) ◄── /cmd_vel ◄──┬── teleop (Phần 2)    │
                                                        └── velocity_smoother ◄─ controller_server (Nav2)
 /scan + TF ──► slam_toolbox ──► /map, TF map→odom      (Phần 2)
 /map (map_server) + /scan + TF ──► amcl ──► TF map→odom, /amcl_pose, /particle_cloud  (Phần 3, 4)
```

## 2. Các node / package chính

| Package | Node | Vai trò |
|---|---|---|
| `ros_gz_sim` (`ign gazebo`) | Gazebo server + GUI | mô phỏng vật lý, cảm biến |
| `ros_gz_bridge` | `parameter_bridge` (nhiều node) | chuyển topic Ignition ↔ ROS 2 (`/scan`, `/clock`, …) |
| `robot_state_publisher` | `robot_state_publisher` | URDF → TF các link cố định, `/robot_description` |
| `controller_manager` (ros2_control) | `diffdrive_controller`, `joint_state_broadcaster` | động học vi sai: nhận vận tốc, phát `/odom` + TF `odom→base_link` |
| `irobot_create_nodes` | `motion_control`, `hazards_vector_publisher`, … | nhận `/cmd_vel`, áp giới hạn an toàn Create 3, dock/undock, bumper |
| `turtlebot4_node` | `turtlebot4_node` | chức năng riêng TurtleBot 4 (nút, đèn, menu) |
| `slam_toolbox` | `slam_toolbox` (sync) | SLAM dạng đồ thị (Karto scan matching + Ceres) |
| `nav2_map_server` | `map_server` | load `map.yaml/pgm`, publish `/map` |
| `nav2_amcl` | `amcl` | định vị Monte Carlo trên bản đồ có sẵn |
| `nav2_planner` | `planner_server` (NavFn) | lập đường đi toàn cục |
| `nav2_controller` | `controller_server` (DWB) | bám đường, sinh vận tốc |
| `nav2_velocity_smoother` | `velocity_smoother` | làm mượt/giới hạn gia tốc → `/cmd_vel` |
| `nav2_behaviors` | `behavior_server` | recovery: spin, backup, wait, … |
| `nav2_bt_navigator` | `bt_navigator` | Behavior Tree điều phối toàn bộ quá trình |
| `nav2_lifecycle_manager` | `lifecycle_manager_*` | cấu hình/kích hoạt các lifecycle node theo thứ tự |
| `topic_tools` | `scan_delay` | tạo `/scan_nav` = `/scan` trễ 0.1 s cho AMCL và costmap (tránh deadlock tf2 trên Humble) |
| `tb4_lab04` | `wait_for_sim` | chờ mô phỏng chạy thật (`/clock`, `/odom`) rồi mới bật SLAM/AMCL/Nav2 |
| `rviz2` | `rviz2` | hiển thị, công cụ 2D Pose Estimate / Nav2 Goal |

## 3. Các topic chính

| Topic | Kiểu | Publisher → Subscriber |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | bridge (RPLIDAR mô phỏng) → slam_toolbox, scan_delay, RViz |
| `/scan_nav` | `sensor_msgs/LaserScan` | scan_delay → amcl, global/local costmap |
| `/odom` | `nav_msgs/Odometry` | diffdrive_controller → Nav2 (controller, velocity_smoother), motion_control |
| `/cmd_vel` | `geometry_msgs/Twist` | teleop hoặc velocity_smoother → motion_control |
| `/cmd_vel_nav` | `geometry_msgs/Twist` | controller_server → velocity_smoother |
| `/tf`, `/tf_static` | `tf2_msgs/TFMessage` | nhiều node; cây `map → odom → base_link → sensor` |
| `/clock` | `rosgraph_msgs/Clock` | Gazebo → mọi node (`use_sim_time: true`) |
| `/map` | `nav_msgs/OccupancyGrid` | slam_toolbox (Phần 2) / map_server (Phần 3-4) |
| `/initialpose` | `geometry_msgs/PoseWithCovarianceStamped` | RViz 2D Pose Estimate → amcl |
| `/amcl_pose`, `/particle_cloud` | pose ước lượng, tập hạt | amcl → RViz |
| `/plan`, `/local_plan` | `nav_msgs/Path` | planner / controller → RViz |
| `/global_costmap/costmap`, `/local_costmap/costmap` | `nav_msgs/OccupancyGrid` | costmap → RViz |
| `/navigate_to_pose` | action `nav2_msgs/NavigateToPose` | RViz (Nav2 Goal) → bt_navigator |
| `/dock_status`, `/hazard_detection` | `irobot_create_msgs` | Create 3 → script kiểm tra |

[[Hình: kết quả `check_sim.py` – bảng PASS]]  [[Hình: `ros2 run tf2_tools view_frames`]]

## 4. Quá trình xây dựng bản đồ (SLAM Toolbox)

1. SLAM Toolbox nhận `/scan` và TF `odom→base_link` (odometry bánh xe).
2. Với mỗi scan mới (cách ≥ 0.25 s), **scan matching** tương quan scan với các scan gần đó để
   hiệu chỉnh pose do odometry đưa ra (odometry bị trôi dần theo thời gian).
3. Mỗi pose đã hiệu chỉnh thành một **nút** trong đồ thị pose; ràng buộc giữa các nút là phép biến
   đổi tương đối đo được.
4. Khi robot quay lại nơi đã đi qua, **loop closure** tìm khớp với scan cũ, thêm ràng buộc vòng và
   bộ tối ưu Ceres điều chỉnh toàn bộ đồ thị → giảm sai số tích luỹ (chống tường bị nhân đôi).
5. Từ các nút và scan, SLAM Toolbox dựng **occupancy grid** 0.05 m/ô và publish `/map`; đồng thời
   publish TF `map→odom` để bù sai số odometry.
6. Lưu bản đồ: `map_saver_cli` → `map.pgm` (trắng = trống, đen = vật cản, xám = chưa biết) và
   `map.yaml` (độ phân giải, gốc toạ độ, ngưỡng).

Cách lái: tốc độ ≤ 0.2 m/s, quay ≤ 0.5 rad/s, đi dọc tường và khép vòng nhiều lần.
[[Hình: map đang xây trên RViz2]]  [[Hình: map.pgm cuối cùng]]  [[Bảng thống kê của `check_map.py`]]

## 5. Quá trình localization (AMCL)

1. Khởi động lại mô phỏng (SLAM đã tắt), `map_server` load `map.yaml`.
2. AMCL khởi tạo tập hạt (500–2000 hạt) quanh initial pose (0, 0, 0) – đúng chỗ robot spawn vì
   frame `map` của SLAM Toolbox trùng pose lúc bắt đầu mapping.
3. **Dự đoán**: khi robot di chuyển, mỗi hạt được dịch theo odometry cộng nhiễu (mô hình chuyển
   động vi sai, tham số `alpha1..5`).
4. **Cập nhật**: mỗi hạt được chấm điểm bằng mức khớp giữa scan và bản đồ (mô hình
   `likelihood_field`, 60 tia).
5. **Resample**: giữ lại hạt có trọng số cao → tập hạt hội tụ quanh vị trí thật.
6. AMCL publish TF `map→odom` để `map→base_link` = pose ước lượng.

Kết quả so sánh với vị trí thật trong Gazebo (`compare_pose.py`):
sai số vị trí trung bình [[...]] m, lớn nhất [[...]] m; sai số góc trung bình [[...]]°.
[[Hình: particle cloud hội tụ, scan trùng tường]]

## 6. Nav2 lập kế hoạch và điều khiển TurtleBot 4

1. Người dùng đặt goal bằng **Nav2 Goal** → action `NavigateToPose` tới `bt_navigator`.
2. `bt_navigator` chạy Behavior Tree mặc định *navigate_to_pose_w_replanning_and_recovery*:
   lập lại đường đi ~1 Hz, bám đường, và gọi recovery khi thất bại.
3. **Costmap**: global costmap (frame `map`: static layer từ `/map` + obstacle layer từ `/scan_nav` +
   inflation 0.45 m) và local costmap (frame `odom`, cửa sổ trượt 3 × 3 m, voxel layer). Robot
   coi là hình tròn bán kính 0.175 m.
4. **Planner** `NavFn` (Dijkstra) tìm đường chi phí thấp nhất trên global costmap → `/plan`.
5. **Controller** `DWB` (20 Hz) lấy mẫu nhiều cặp (v, ω), mô phỏng quỹ đạo 1.7 s, chấm điểm bằng
   các critic (bám đường, hướng tới goal, tránh vật cản, chống dao động) và chọn quỹ đạo tốt nhất
   → `/cmd_vel_nav` (v ≤ 0.26 m/s, ω ≤ 1.0 rad/s).
6. `velocity_smoother` giới hạn gia tốc → `/cmd_vel` → `motion_control` của Create 3 → diff drive.
7. Goal coi là tới nơi khi sai số ≤ 0.25 m và ≤ 0.25 rad. Nếu kẹt: recovery (xoá costmap, quay
   tại chỗ, lùi, chờ) rồi lập lại kế hoạch.

Kết quả (`nav_monitor.py`): [[bảng 3 goal: vị trí, thời gian, SUCCEEDED, bump = 0]]
[[Hình: RViz2 với đường đi và robot tới goal 1, 2, 3]]

## 7. Trả lời câu hỏi phần "Nội dung cần hiểu"

[[Đề bài bạn gửi không kèm danh sách câu hỏi của phần này – chép câu hỏi vào đây và trả lời.
Các mục 4–6 ở trên đã có sẵn phần lớn kiến thức cần dùng.]]

## 8. Hình ảnh minh hoạ kết quả

[[Gazebo + RViz Phần 1]] [[Map hoàn chỉnh]] [[Localization]] [[3 goal]]
