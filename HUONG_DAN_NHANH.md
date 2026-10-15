# Hướng dẫn nhanh – Localization + Navigation tự động + YOLO

Chi tiết, giải thích, xử lý sự cố: [`README.md`](README.md). Workspace giả định `~/workspaces/tb4_gazebo`.

## 0. Cài thêm (1 lần) và build

```bash
sudo apt update
sudo apt install -y ros-humble-turtlebot4-navigation ros-humble-nav2-simple-commander \
  ros-humble-cv-bridge ros-humble-vision-msgs ros-humble-ros-gz-sim ros-humble-topic-tools \
  python3-pip python3-matplotlib python3-yaml fonts-dejavu-core
# YOLO – CÁCH NHANH: bash ~/workspaces/tb4_gazebo/src/tb4_lab04/scripts/install_yolo_deps.sh  (cài + tự kiểm tra; bỏ qua 2 dòng pip dưới)
# YOLO – máy không có GPU NVIDIA: cài PyTorch bản CPU trước (nhẹ hơn nhiều)
pip3 install --user torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip3 install --user "numpy<2" "opencv-python<4.11" ultralytics      # GHIM numpy<2 (cv_bridge)

cd ~/workspaces/tb4_gazebo && source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select tb4_lab04 && source install/setup.bash
export ROS_LOCALHOST_ONLY=1

ros2 run tb4_lab04 spawn_objects.py --download-only   # tải model vật thể Gazebo Fuel (cần Internet)
ros2 run tb4_lab04 doctor.sh                          # phải: "không có lỗi chặn"
```

Mỗi terminal mới: `source /opt/ros/humble/setup.bash && source ~/workspaces/tb4_gazebo/install/setup.bash && export ROS_LOCALHOST_ONLY=1`
(WSL2 / Gazebo crash → thêm `software_render:=true` vào mọi lệnh `ros2 launch`.)

## 1. Simulation + nạp bản đồ + AMCL (Terminal 1)

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 navigation.launch.py
```

Chờ RViz2 có bản đồ, panel Navigation 2: `Navigation: active`. Kiểm tra LiDAR trùng tường (Terminal 2):

```bash
ros2 run tb4_lab04 localization_check.py      # phải: ĐẠT
ros2 run tb4_lab04 compare_pose.py            # (tuỳ chọn) so với vị trí thật Gazebo, Ctrl+C -> ĐẠT
```

Lệch → RViz2 **2D Pose Estimate** đặt lại vị trí robot.

## 2. Toạ độ goal (Terminal 2)

```bash
ros2 run tb4_lab04 goal_recorder.py   # RViz2 "Publish Point" + click, hoặc Enter = pose robot; q = lưu + thoát
# dán đoạn YAML in ra vào ~/workspaces/tb4_gazebo/src/tb4_lab04/config/goals.yaml (hoặc giữ 3 goal mẫu)
ros2 run tb4_lab04 check_goals.py --plot      # phải: các goal HỢP LỆ; ảnh ~/tb4_results/goals_map.png
```

## 3. YOLO (Terminal 2) – bật trước khi robot chạy

```bash
ros2 launch tb4_lab04 yolo.launch.py                    # cửa sổ "YOLO - camera TurtleBot 4" + panel YOLO trên RViz2
# ros2 launch tb4_lab04 yolo.launch.py yolo_model:=yolov8n.pt
```

## 4. Navigation tự động (Terminal 3) – không chạm bàn phím/chuột sau lệnh này

```bash
ros2 run tb4_lab04 waypoint_navigator.py               # undock -> G1 -> G2 -> G3 -> "ĐẠT"
# ros2 run tb4_lab04 nav_monitor.py                    # (Terminal 4, tuỳ chọn) theo dõi độc lập, Ctrl+C -> ĐẠT
```

## 5. Ảnh + báo cáo

```bash
ros2 run tb4_lab04 check_goals.py --plot ~/tb4_results/map_run.png \
   --run $(ls -d ~/tb4_results/nav_* | tail -1)/run.json \
   --detections $(ls -d ~/tb4_results/yolo_* | tail -1)/detections.csv
ls ~/tb4_results/yolo_*/best_*.jpg
pip3 install --user reportlab
cd ~/workspaces/tb4_gazebo/src/tb4_lab04 && nano docs/report_info.yaml && python3 docs/report/build_report.py   # -> docs/report/BaoCao_Bai5_TurtleBot4_Nav2_YOLO.pdf
```

## Tất cả một lệnh

```bash
ros2 run tb4_lab04 kill_sim.sh && ros2 launch tb4_lab04 demo.launch.py
```

## Kết thúc / khi lỗi

```bash
# Ctrl+C mọi terminal, rồi:
ros2 run tb4_lab04 kill_sim.sh
ros2 run tb4_lab04 doctor.sh
ros2 run tb4_lab04 collect_debug.sh    # chạy khi launch còn mở, gửi file ~/tb4_debug_*.txt
```

## GitHub

```bash
cd ~/workspaces/tb4_gazebo/src/tb4_lab04
git add -A && git commit -m "TurtleBot 4: AMCL + Nav2 waypoint navigator + YOLO detector"
git remote set-url origin https://github.com/<ten-ban>/<repo-moi>.git && git push -u origin main
```
