# Hướng dẫn nhanh – Bài 6: điều khiển TurtleBot 4 bằng cử chỉ tay

Chi tiết, giải thích, xử lý sự cố: [`README.md`](README.md). Workspace giả định `~/workspaces/tb4_gazebo`.

## 0. Cài (1 lần) và build

```bash
sudo apt update && sudo apt install -y ros-humble-turtlebot4-simulator ros-humble-irobot-create-msgs \
  ros-humble-tf2-ros python3-pip python3-matplotlib python3-yaml v4l-utils
cd ~/workspaces/tb4_gazebo/src/tb4_lab04 && bash scripts/install_gesture_deps.sh   # MediaPipe + OpenCV (ghim numpy<2)
cd ~/workspaces/tb4_gazebo && source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select tb4_lab04 && source install/setup.bash
export ROS_LOCALHOST_ONLY=1
python3 src/tb4_lab04/test/test_gesture_logic.py     # tất cả test phải OK
```

Mỗi terminal mới: `source /opt/ros/humble/setup.bash && source ~/workspaces/tb4_gazebo/install/setup.bash && export ROS_LOCALHOST_ONLY=1`

## 1. Phần 1 – Simulation, /cmd_vel, webcam

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 gesture_sim.launch.py          # T1 (WSL2/driver lỗi: software_render:=true)
ros2 run tb4_lab04 check_cmd_vel.py                  # T2 -> "KẾT QUẢ: ĐẠT"
ros2 run tb4_lab04 webcam_test.py                    # cửa sổ webcam + FPS (q để thoát)
```

## 2+3. Nhận diện cử chỉ + điều khiển robot

```bash
ros2 launch tb4_lab04 gesture.launch.py              # T2 (T1 vẫn chạy gesture_sim) – chờ "Robot: IDLE"
ros2 topic echo /detected_gesture                    # T3 (tuỳ chọn)
```

| Cử chỉ | Robot |
|---|---|
| Vẫy tay / 1 ngón / 2 ngón | CHỌN chào / tiến–lùi 4 lần / quỹ đạo tròn |
| Ngón cái | XÁC NHẬN → thực hiện |
| Xoè tay | DỪNG ngay (ngón cái = chạy lại) |
| Nắm tay | HUỶ → chờ |

Giữ mỗi cử chỉ ~1 s, hạ tay giữa hai cử chỉ. Tắt node nhận diện → robot dừng sau 1 s.

Một lệnh: `ros2 launch tb4_lab04 gesture_demo.launch.py` · Không webcam:
`ros2 launch tb4_lab04 gesture.launch.py run_recognition:=false` + `ros2 run tb4_lab04 gesture_sequence.py --ros-args -p preset:=all`

## 4. Kết quả + báo cáo

```bash
ros2 run tb4_lab04 plot_gesture_run.py               # ~/tb4_results/gesture_<thời_gian>/trajectory.png
nano docs/report_info.yaml                           # link video, link GitHub
python3 docs/report/build_report_bai6.py             # -> docs/report/BaoCao_Bai6_TurtleBot4_Gesture.pdf
```
