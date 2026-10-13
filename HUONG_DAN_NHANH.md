# Hướng dẫn nhanh – ghi đè dự án và chạy

Đặt đường dẫn workspace của bạn (sửa nếu khác), file tải về ở `~/Downloads/tb4_lab04.tar.gz`:

```bash
export WS=~/workspaces/tb4_gazebo      # hoặc ~/tb4_ws
```

## 1. Ghi đè bản mới (giữ bản đồ cũ)

Ctrl+C mọi terminal đang chạy mô phỏng, rồi:

```bash
source /opt/ros/humble/setup.bash
sudo apt update && sudo apt install -y ros-humble-topic-tools mesa-utils
cd $WS/src
rm -rf /tmp/tb4_maps_backup && cp -a tb4_lab04/maps /tmp/tb4_maps_backup
mv tb4_lab04 ~/tb4_lab04_old_$(date +%Y%m%d_%H%M%S)
tar -xzf ~/Downloads/tb4_lab04.tar.gz -C $WS/src
cp -a /tmp/tb4_maps_backup/. tb4_lab04/maps/
cd $WS && rm -rf build/tb4_lab04 install/tb4_lab04
colcon build --packages-select tb4_lab04
source install/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 run tb4_lab04 kill_sim.sh
ros2 run tb4_lab04 doctor.sh           # phải ra: không có lỗi chặn
```

Mỗi terminal mới đều chạy 3 dòng (hoặc thêm vào `~/.bashrc`):

```bash
source /opt/ros/humble/setup.bash
source $WS/install/setup.bash
export ROS_LOCALHOST_ONLY=1
```

> WSL2 / Gazebo crash / `check_sensors.py` FAIL → thêm `software_render:=true` vào **mọi** lệnh `ros2 launch` bên dưới.

## 2. Phần 1 – Simulation

```bash
# Terminal 1
ros2 launch tb4_lab04 sim.launch.py
# Terminal 2
ros2 run tb4_lab04 check_sensors.py    # phải: số đo LiDAR và cliff hợp lý
ros2 run tb4_lab04 check_sim.py        # phải: TẤT CẢ ĐỀU ĐẠT
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.5}}"   # Ctrl+C để dừng
```

Kết thúc: Ctrl+C Terminal 1 → `ros2 run tb4_lab04 kill_sim.sh`

## 3. Phần 2 – SLAM tự động + tự lưu bản đồ (auto_explore)

```bash
# Terminal 1 – robot tự undock, tự khám phá, xong tự về chỗ xuất phát và tự lưu maps/map.yaml + map.pgm
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 explore.launch.py
#   tuỳ chọn: max_duration:=1200 (giới hạn giây mô phỏng)   software_render:=true (WSL2/driver lỗi)
#             fast:=false (giữ giới hạn tốc độ mặc định 0.306 m/s của Create 3; mặc định chạy tới 0.40 m/s)
```

Robot tự chọn chỗ đứng cách tường ≥ 0.4 m mà vẫn nhìn được vào góc, goal thất bại thì tự lùi/quay/tiến ra
("Tự gỡ kẹt" trong log) rồi đi tiếp. Tốc độ nhìn thấy = tốc độ lệnh × RTF (% góc dưới phải Gazebo).
Nếu log báo `robot kẹt ... dừng và lưu bản đồ hiện có`: để Terminal 1 chạy, lái teleop ra chỗ thoáng, rồi
`ros2 run tb4_lab04 auto_explore.py` ở terminal khác để khám phá tiếp trên cùng bản đồ.

Đoạn biên nào nhìn từ một chỗ không quét được thì robot tự thử chỗ đứng khác (tối đa 3). Còn sót thì bảng kết
quả in `Biên chưa quét : (x, y) ...` – lái teleop tới đó (mapping vẫn chạy) rồi `save_map.sh`. Vùng xám nằm
BÊN TRONG đường viền khối tường là bình thường (LiDAR không nhìn vào trong vật đặc).

Chờ tới khi Terminal 1 in bảng `KẾT QUẢ TỰ KHÁM PHÁ` và dòng `Bản đồ : .../maps/map.yaml`
(trong lúc chạy, cứ 300 s mô phỏng tự lưu bản dự phòng vào `maps/autosave/`).

```bash
# Terminal 2 – CHỈ khi muốn dừng sớm: lưu bản đồ hiện tại TRƯỚC khi Ctrl+C Terminal 1
ros2 run tb4_lab04 save_map.sh
```

Làm đẹp + kiểm tra bản đồ (sau khi đã lưu; không cần mô phỏng đang chạy):

```bash
ros2 run tb4_lab04 clean_map.py --dry-run   # xem sẽ bịt bao nhiêu khe tường / xoá bao nhiêu vệt trắng
ros2 run tb4_lab04 clean_map.py             # sửa maps/map.pgm (bản gốc tự sao lưu vào maps/backup_*_truoc_clean/)
ros2 run tb4_lab04 check_map.py             # thống kê: % trống / vật cản / chưa biết, diện tích
eog $WS/src/tb4_lab04/maps/map.pgm          # xem ảnh bản đồ
```

Kết thúc: Ctrl+C Terminal 1 → `ros2 run tb4_lab04 kill_sim.sh`

> Đề yêu cầu Phần 2 điều khiển bằng **teleop** – hỏi giảng viên trước khi nộp video tự khám phá.
> Cách lái tay (thay cho explore.launch.py):
> `ros2 launch tb4_lab04 mapping.launch.py` → terminal khác: `ros2 action send_goal /undock irobot_create_msgs/action/Undock "{}"`
> rồi `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.2 -p turn:=0.5`
> → đủ bản đồ thì `ros2 run tb4_lab04 save_map.sh` (khi mapping vẫn chạy) → `clean_map.py`, `check_map.py` như trên.

## 4. Phần 3 – Localization

```bash
# Terminal 1
ros2 launch tb4_lab04 navigation.launch.py use_nav2:=false
# Terminal 2
ros2 action send_goal /undock irobot_create_msgs/action/Undock "{}"
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.2 -p turn:=0.5
# Terminal 3
ros2 run tb4_lab04 compare_pose.py     # Ctrl+C → phải: ĐẠT
```

LiDAR lệch tường trên RViz2 → nút **2D Pose Estimate**, click vị trí thật của robot.
Kết thúc: Ctrl+C các terminal → `ros2 run tb4_lab04 kill_sim.sh`

## 5. Phần 4 – Nav2 (≥ 3 goal)

```bash
# Terminal 1
ros2 launch tb4_lab04 navigation.launch.py
# Terminal 2
ros2 action send_goal /undock irobot_create_msgs/action/Undock "{}"
ros2 run tb4_lab04 nav_monitor.py      # để chạy suốt; Ctrl+C cuối cùng → phải: ĐẠT
```

Trên RViz2: **Nav2 Goal** → click ô trắng cách tường ≥ 0.5 m, kéo chọn hướng → chờ `SUCCEEDED`.
Lặp lại 3 goal ở 3 khu vực khác nhau. Không chạy teleop trong lúc này.
Kết thúc: Ctrl+C → `ros2 run tb4_lab04 kill_sim.sh`

## 6. Nộp GitHub

```bash
cd $WS/src/tb4_lab04
git init -b main 2>/dev/null; git add . && git status   # phải thấy maps/map.yaml, maps/map.pgm
git commit -m "Lab04: TurtleBot 4 SLAM Toolbox + Nav2"
git remote add origin https://github.com/<ten-ban>/tb4_lab04.git
git push -u origin main
```

## Khi lỗi

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 run tb4_lab04 doctor.sh
ros2 run tb4_lab04 collect_debug.sh    # chạy khi launch còn mở, gửi file ~/tb4_debug_*.txt
```

Log đỏ sau khi bấm Ctrl+C (`exit code -2`) và các cảnh báo trong README mục 8.1 là bình thường.
Bấm Ctrl+C ngay vài giây đầu mà terminal treo (lỗi của `ros2 launch` Humble) → terminal khác: `ros2 run tb4_lab04 kill_sim.sh`.

Bản đồ mới kém hơn bản cũ? Mỗi lần lưu, bản trước được chuyển vào `maps/backup_<thời_gian>/` → lấy lại:

```bash
ls -d $WS/src/tb4_lab04/maps/backup_*                       # chọn thư mục của bản đồ tốt
cp $WS/src/tb4_lab04/maps/backup_<thời_gian>/map.* $WS/src/tb4_lab04/maps/
```
Chi tiết đầy đủ: `README.md`.
