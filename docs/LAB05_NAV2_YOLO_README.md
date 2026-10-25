# (Bài 5) TurtleBot 4 – Localization, Navigation tự động (Nav2) và nhận diện vật thể bằng YOLO

> Tài liệu của **bài trước** (vẫn chạy được trong repo này). Bài 6 – điều khiển bằng cử chỉ tay: [`../README.md`](../README.md).

ROS 2 Humble · Ignition Gazebo Fortress · TurtleBot 4 Simulator · Nav2 · nav2_simple_commander · ultralytics YOLO

Dùng lại **bản đồ của tuần trước** (`maps/map.yaml` + `maps/map.pgm`, world `maze`) để:

1. khởi chạy lại TurtleBot 4 trong đúng world `maze`, **thêm vật thể** (người, xe hơi, ghế, trụ cứu hoả, bình chữa
   cháy), nạp bản đồ và định vị bằng **AMCL**;
2. khảo sát, ghi toạ độ `(x, y, yaw)` của các điểm mục tiêu trên bản đồ;
3. một **ROS 2 node Python** (`waypoint_navigator.py`, thư viện `nav2_simple_commander`) tự đưa robot đi
   **Goal 1 → Goal 2 → Goal 3** – không chạm bàn phím, không đặt goal bằng chuột;
4. một **ROS 2 node YOLO** (`yolo_detector.py`) nhận ảnh camera `/oakd/rgb/preview/image_raw`, chuyển sang OpenCV
   bằng `cv_bridge`, nhận diện bằng YOLO, vẽ bounding box + tên lớp + độ tự tin lên cửa sổ OpenCV **và** topic
   `/yolo/image_annotated` (xem trên RViz2), in danh sách vật thể ra terminal.

| Phần của đề | Lệnh chính | Bằng chứng (quay video / đưa vào báo cáo) |
|---|---|---|
| 1 – Simulation + bản đồ + AMCL | `ros2 launch tb4_lab04 navigation.launch.py` | `localization_check.py` → `ĐẠT`; RViz2: chấm LiDAR trùng tường |
| 2 – Toạ độ mục tiêu | `ros2 run tb4_lab04 goal_recorder.py` (Publish Point / `/amcl_pose`) | `check_goals.py --plot` → ảnh bản đồ + goal |
| 3 – Navigation bằng code | `ros2 run tb4_lab04 waypoint_navigator.py` | bảng `TỔNG KẾT` → `ĐẠT`, `run.json` + ảnh quỹ đạo |
| 4 – YOLO | `ros2 launch tb4_lab04 yolo.launch.py` | cửa sổ YOLO, log `PHÁT HIỆN MỚI`, ảnh `best_<lớp>.jpg` |
| Tất cả một lệnh | `ros2 launch tb4_lab04 demo.launch.py` | – |
| Báo cáo PDF | `python3 docs/report/build_report.py` | `docs/report/BaoCao_Bai5_TurtleBot4_Nav2_YOLO.pdf` |

Chỉ cần danh sách lệnh: [`LAB05_HUONG_DAN_NHANH.md`](LAB05_HUONG_DAN_NHANH.md). Tài liệu bài tuần trước (cài đặt đầy đủ, SLAM):
[`LAB04_SLAM_README.md`](LAB04_SLAM_README.md).

---

## Mục lục

0. [Đọc trước – những điều hay làm hỏng bài](#0-đọc-trước--những-điều-hay-làm-hỏng-bài)
1. [Cài đặt](#1-cài-đặt)
2. [Phần 1 – Simulation, nạp bản đồ, Localization](#2-phần-1--simulation-nạp-bản-đồ-localization)
3. [Phần 2 – Khảo sát toạ độ mục tiêu](#3-phần-2--khảo-sát-toạ-độ-mục-tiêu)
4. [Phần 3 – Navigation tự động bằng code](#4-phần-3--navigation-tự-động-bằng-code)
5. [Phần 4 – Nhận diện vật thể bằng YOLO](#5-phần-4--nhận-diện-vật-thể-bằng-yolo)
6. [Chạy tất cả bằng một lệnh](#6-chạy-tất-cả-bằng-một-lệnh)
7. [Kịch bản quay video demo](#7-kịch-bản-quay-video-demo)
8. [Nộp bài: GitHub, video, báo cáo PDF](#8-nộp-bài-github-video-báo-cáo-pdf)
9. [Xử lý sự cố](#9-xử-lý-sự-cố)
10. [Kiến trúc: package, node, topic, action](#10-kiến-trúc-package-node-topic-action)
11. [Tham số](#11-tham-số)
12. [Kiểm thử và giới hạn](#12-kiểm-thử-và-giới-hạn)

---

## 0. Đọc trước – những điều hay làm hỏng bài

1. **Ubuntu 22.04 + ROS 2 Humble + Gazebo Fortress** – như tuần trước. Mỗi terminal chỉ `source` ROS 2 Humble và
   workspace này; luôn `export ROS_LOCALHOST_ONLY=1` (phòng lab nhiều máy).
2. **`pip install ultralytics` có thể kéo NumPy 2.x về → `cv_bridge` của Humble (build với NumPy 1.x) hỏng.**
   Luôn cài kèm `"numpy<2" "opencv-python<4.11"` như mục 1.3. `doctor.sh` phát hiện lỗi này.
3. **World + vị trí spawn phải giống lúc làm bản đồ** (mặc định `world:=maze`, x = y = yaw = 0). Toạ độ map của
   bản đồ tuần trước trùng toạ độ Gazebo – vì vậy initial pose (0, 0, 0) đúng và goal mẫu dùng được.
4. **Robot khởi động khi đang đỗ trong dock.** `waypoint_navigator.py` tự undock; chạy tay thì phải undock trước.
5. **Vật thể lấy từ Gazebo Fuel – lần đầu cần Internet.** Tải trước 1 lần: `spawn_objects.py --download-only`.
   Không có mạng thì bài vẫn chạy (world trống), chỉ thiếu vật thể cho YOLO.
6. **Chỉ một phiên mô phỏng một lúc**: trước mỗi lần chạy lại `Ctrl+C` rồi `ros2 run tb4_lab04 kill_sim.sh`.
7. **Không điều khiển tay sau khi chạy node điều hướng** (đề yêu cầu): tắt teleop, không dùng Nav2 Goal.
8. **Không bật Anaconda/conda trong terminal chạy ROS.** Khi `(base)` hiện đầu dòng lệnh, `python3` là Python của
   conda → `rclpy`, `cv_bridge` lỗi import và `pip` cài YOLO nhầm chỗ. Chạy `conda deactivate`
   (tắt hẳn: `conda config --set auto_activate_base false`). `doctor.sh` kiểm tra điều này.
9. Log đỏ/vàng của mô phỏng TurtleBot 4 phần lớn là bình thường (danh sách ở
   [LAB04_SLAM_README.md mục 8.1](LAB04_SLAM_README.md#81-log-trông-như-lỗi-nhưng-bình-thường)).
   Đánh giá bằng các script kiểm tra.

---

## 1. Cài đặt

### 1.1. Gói ROS / hệ thống

Đã cài đủ môi trường tuần trước (ROS 2 Humble, Gazebo Fortress, TurtleBot 4 simulator, Nav2, SLAM Toolbox – xem
[LAB04_SLAM_README.md mục 1](LAB04_SLAM_README.md#1-cài-đặt-làm-một-lần) nếu cài máy mới). Thêm các
gói của bài này:

```bash
sudo apt update
sudo apt install -y ros-humble-turtlebot4-navigation ros-humble-nav2-simple-commander \
  ros-humble-cv-bridge ros-humble-vision-msgs ros-humble-ros-gz-sim ros-humble-topic-tools \
  python3-pip python3-matplotlib python3-yaml fonts-dejavu-core
```

### 1.2. Workspace và build

```bash
mkdir -p ~/workspaces/tb4_gazebo/src && cd ~/workspaces/tb4_gazebo/src
# A) từ file nén:   tar -xzf ~/Downloads/tb4_lab04.tar.gz -C ~/workspaces/tb4_gazebo/src
# B) từ GitHub:     git clone https://github.com/<ten-ban>/<repo>.git tb4_lab04
cd ~/workspaces/tb4_gazebo
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -y      # cài nốt gói apt còn thiếu (theo package.xml)
colcon build --symlink-install --packages-select tb4_lab04   # chỉ build gói này (workspace có thể chứa gói khác)
source install/setup.bash
```

`--symlink-install`: sửa script/config trong `src/` là có hiệu lực ngay, không cần build lại. Bản đồ, `goals.yaml`,
`objects.yaml` luôn được đọc từ thư mục **source** (`src/tb4_lab04/...`), kể cả khi không dùng symlink.

Đã có bản cũ của dự án (bài tuần trước) – thay bằng bản này nhưng **giữ bản đồ của bạn**:

```bash
cd ~/workspaces/tb4_gazebo/src
cp -a tb4_lab04/maps /tmp/tb4_maps_backup
mv tb4_lab04 ~/tb4_lab04_old_$(date +%Y%m%d_%H%M%S)
tar -xzf ~/Downloads/tb4_lab04.tar.gz -C ~/workspaces/tb4_gazebo/src
cp -a /tmp/tb4_maps_backup/map.yaml /tmp/tb4_maps_backup/map.pgm tb4_lab04/maps/
cd ~/workspaces/tb4_gazebo && rm -rf build/tb4_lab04 install/tb4_lab04
colcon build --symlink-install --packages-select tb4_lab04 && source install/setup.bash
```

> Bản đồ trong repo là bản đồ world `maze` đã nộp tuần trước. Nếu bạn thay bằng bản đồ khác, **phải** chạy lại
> `check_goals.py` (mục 3) – goal mẫu có thể rơi vào tường của bản đồ mới.

Mỗi terminal mới (hoặc thêm vào cuối `~/.bashrc`):

```bash
source /opt/ros/humble/setup.bash
source ~/workspaces/tb4_gazebo/install/setup.bash
export ROS_LOCALHOST_ONLY=1
```

### 1.3. Python cho YOLO

**Cách nhanh nhất (khuyến nghị): một lệnh cài hết và tự kiểm tra** (chạy trong thư mục dự án, KHÔNG ở môi trường conda):

```bash
bash scripts/install_yolo_deps.sh          # máy có GPU NVIDIA: thêm --gpu
```

Script cài gói apt cần thiết, ghim `numpy<2` + `opencv-python<4.11`, cài PyTorch (CPU), ultralytics, tải sẵn `yolo11n.pt`, rồi in `[PASS]/[FAIL]` cho numpy, cv2, torch, ultralytics, cv_bridge, vision_msgs. Cài thủ công từng bước:

```bash
# (Khuyến nghị cho máy KHÔNG có GPU NVIDIA) PyTorch bản CPU: ~200 MB thay vì ~3 GB bản CUDA
pip3 install --user torch torchvision --index-url https://download.pytorch.org/whl/cpu

# ultralytics + GHIM NumPy 1.x để không làm hỏng cv_bridge của ROS 2 Humble
pip3 install --user "numpy<2" "opencv-python<4.11" ultralytics
```

Đề ghi `pip install ultralytics opencv-python`: lệnh đó (năm 2026) cài `opencv-python` 4.12+ **bắt buộc NumPy 2.x**,
mà `cv_bridge` (apt) được biên dịch với NumPy 1.x → lỗi `_ARRAY_API not found` / `numpy.core.multiarray failed to
import` khi node YOLO chuyển ảnh. Hai ràng buộc `"numpy<2" "opencv-python<4.11"` tránh đúng lỗi này (đã kiểm:
NumPy 1.26.4, OpenCV 4.10, ultralytics 8.4, PyTorch 2.x trên Ubuntu 22.04 / Python 3.10).

Đã lỡ cài NumPy 2: chạy lại dòng `pip3 install --user "numpy<2" "opencv-python<4.11" ultralytics`.

### 1.4. Tải trước model (1 lần, cần Internet)

```bash
ros2 run tb4_lab04 spawn_objects.py --download-only     # 7 model Gazebo Fuel -> ~/.ignition/fuel
python3 -c "from ultralytics import YOLO; YOLO('$HOME/.cache/tb4_lab04/models/yolo11n.pt')"   # ~5 MB
```

(Bỏ qua bước này cũng được: lần chạy đầu tự tải, chỉ chậm hơn.)

### 1.5. Kiểm tra môi trường

```bash
ros2 run tb4_lab04 doctor.sh
```

Phải kết thúc bằng `Kết luận: không có lỗi chặn`. Mục 11 kiểm tra NumPy/OpenCV/cv_bridge/ultralytics, mục 12 kiểm tra
model vật thể đã tải chưa. Mỗi `[FAIL]` có kèm lệnh sửa.

---

## 2. Phần 1 – Simulation, nạp bản đồ, Localization

### 2.1. Khởi chạy

**Terminal 1:**

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 navigation.launch.py
```

Launch làm theo thứ tự (log có tiền tố `[tb4_lab04]`):

1. Gazebo + TurtleBot 4 trong world `maze` (đúng world, đúng vị trí spawn như lúc làm bản đồ), robot đỗ trong dock;
2. chờ mô phỏng **thật sự chạy** (`wait_for_sim.py`: có `/clock` và `/odom`);
3. **spawn vật thể** (`spawn_objects.py`, `config/objects.yaml`) – log `[spawn_objects] + person_1 ...`,
   `Đã thêm 7/7 vật thể`;
4. sau 2 s: `map_server` nạp `maps/map.yaml` + **AMCL** (`config/localization.yaml`) – AMCL tự đặt initial pose
   (0, 0, 0) = chỗ robot đỗ;
5. sau 8 s: **Nav2** (`config/nav2.yaml`) – panel *Navigation 2* trên RViz2: `Navigation: active`,
   `Localization: active`.

Tuỳ chọn: `software_render:=true` (WSL2 / driver đồ hoạ lỗi), `spawn_objects:=false` (world trống),
`map:=/duong/dan/map.yaml`, `use_rviz:=false`.

### 2.2. Kiểm tra initial pose: LiDAR phải trùng tường

Trên RViz2 (Fixed Frame `map`):

- bản đồ của tuần trước (xám/đen/trắng);
- robot nằm đúng chỗ dock (gốc toạ độ), mũi tên hạt AMCL (*Amcl Particle Swarm*) tụ quanh robot;
- **chấm đỏ LiDAR trùng khít các bức tường đen**. Các cụm chấm không trùng tường là vật thể mới thêm (người,
  xe…) – chúng không có trên bản đồ tuần trước, đó là bình thường.

Kiểm tra định lượng (**Terminal 2**):

```bash
ros2 run tb4_lab04 localization_check.py
```

```
Scan khớp tường:  96.1 % (330 tia, lệch trung vị 0.000 m) | robot (map) (0.00, 0.00, 0°)
...
============ KIỂM TRA LOCALIZATION ============
Tỉ lệ tia khớp    : TB 96.1 %, thấp nhất 96.1 %
=> ĐẠT: LiDAR trùng tường của bản đồ – initial pose / AMCL đúng
```

(Số liệu từ lần kiểm thử của tác giả – trên Gazebo thật tỉ lệ thường thấp hơn vài % vì nhiễu LiDAR và vật thể mới.)

So với vị trí **thật** trong Gazebo (`/sim_ground_truth_pose`): `ros2 run tb4_lab04 compare_pose.py` (Ctrl+C để xem
tổng kết; `ĐẠT` khi sai số trung bình ≤ 0.25 m).

Nếu LiDAR lệch tường (spawn khác chỗ, AMCL nhảy sai): nút **2D Pose Estimate** trên RViz2 → click vào vị trí thật
của robot → kéo theo hướng robot đang nhìn → chạy lại `localization_check.py`.

---

## 3. Phần 2 – Khảo sát toạ độ mục tiêu

Goal nằm trong `config/goals.yaml` (frame `map`, mét, yaw tính bằng radian; có thể ghi `yaw_deg`). Repo có sẵn 3
goal ở 3 khu vực khác nhau của mê cung, mỗi goal quay mặt về phía vật thể để YOLO nhận diện khi tới nơi:

| Goal | x (m) | y (m) | yaw | Khu vực | Camera nhìn thấy khi tới |
|---|---|---|---|---|---|
| G1 | −5.50 | 5.75 | 2.63 rad (151°) | phòng trên-trái | xe hơi (`car_1`, ~3.5 m) |
| G2 | −6.00 | −2.60 | −1.57 rad (−90°) | khu dưới-trái | người (`person_2`), ghế (`chair_1`) |
| G3 | 5.30 | −2.00 | 0 rad (0°) | hành lang phải | trụ cứu hoả, người (`person_3`), bình chữa cháy |

**Lấy toạ độ của bạn** (đề yêu cầu tự khảo sát – nên làm và quay vào video). Terminal 1 vẫn chạy
`navigation.launch.py`; **Terminal 2:**

```bash
ros2 run tb4_lab04 goal_recorder.py
```

- Cách 1 (đề gợi ý): RViz2 → nút **Publish Point** → click lên ô trắng của bản đồ. Terminal in
  `Goal 1: x=-5.48  y=5.80  yaw=...` (yaw = hướng từ điểm trước tới điểm này; sửa lại nếu muốn robot nhìn về vật thể).
  Xem topic thô: `ros2 topic echo /clicked_point`.
- Cách 2 (đề gợi ý): nhấn **Enter** → ghi pose hiện tại của robot từ `/amcl_pose` (có yaw).
  Xem topic thô: `ros2 topic echo /amcl_pose`.
- `u` = xoá điểm cuối, `w` = ghi file, `q` = ghi file và thoát. File: `~/tb4_results/goals_recorded.yaml`; khi thoát
  terminal in sẵn đoạn YAML – dán vào `config/goals.yaml`.

**Kiểm tra goal trước khi chạy** (không cần mô phỏng):

```bash
ros2 run tb4_lab04 check_goals.py --plot
```

```
#           x        y    yaw° cách tường   quãng đg  tên
G1      -5.50     5.75     151     0.75 m      8.0 m  Goal 1 - phong tren-trai (xe hoi)
G2      -6.00    -2.60     -90     1.21 m      9.3 m  Goal 2 - khu duoi-trai (nguoi + ghe)
G3       5.30    -2.00       0     1.25 m     12.1 m  Goal 3 - hanh lang phai (...)
Camera tại mỗi goal (FOV 60°):
  G1: car_1 3.5 m +5° (giữa khung)
  G2: person_2 3.0 m +0° (giữa khung); chair_1 2.9 m +25° (giữa khung)
  G3: fire_hydrant_1 3.4 m +17° (giữa khung); person_3 3.7 m -9° (giữa khung); fire_extinguisher_1 3.3 m -23° ...
KẾT LUẬN: các goal HỢP LỆ.
Đã vẽ: /home/<bạn>/tb4_results/goals_map.png
```

Script báo **LỖI** nếu goal nằm trên tường / vùng xám / ngoài bản đồ, cách vật cản < bán kính robot, hoặc không có
đường đi đủ rộng từ goal trước (tính trên bản đồ + footprint vật thể); **CẢNH BÁO** nếu cách tường < 0.45 m (Nav2 hay
báo `Failed to make progress`). Ảnh `goals_map.png` (bản đồ + goal + hướng + vùng nhìn của camera + vật thể) dùng
cho báo cáo.

---

## 4. Phần 3 – Navigation tự động bằng code

**Terminal 1** vẫn chạy `navigation.launch.py` (Nav2 đã `active`). **Không** chạy teleop. **Terminal 3:**

```bash
ros2 run tb4_lab04 waypoint_navigator.py
```

Node (`scripts/waypoint_navigator.py`, lớp con của `nav2_simple_commander.BasicNavigator`) tự làm:

```
[1/5] Chờ AMCL và Nav2 (bt_navigator) ở trạng thái active ...
  amcl : active
[2/5] Initial pose cho AMCL
  Đặt initial pose (0.00, 0.00, yaw 0.00) – robot đang ở trong dock = đúng điểm spawn của lúc làm bản đồ
  AMCL: (0.00, 0.00, 0°)  độ lệch chuẩn x=0.48 m y=0.49 m yaw=15°
  bt_navigator : active
[3/5] Rời dock
Undock ... (robot lùi ra khỏi dock rồi quay 180°)
Undock thành công (is_docked = False)
[4/5] Bắt đầu đi qua 3 goal – KHÔNG điều khiển tay từ lúc này
=== G1 / 3: Goal 1 - phong tren-trai (xe hoi) -> (-5.50, 5.75, 151°)
  -> G1: còn 6.12 m | ETA ~24 s | đã đi 9 s | recovery 0
<<< G1: TỚI NƠI sau 38.5 s, đi 8.0 m, sai số 0.23 m / 0°
    dừng 2 s tại G1 (YOLO quan sát)
=== G2 / 3 ...
[5/5] TỔNG KẾT
#    kết quả    thời gian  quãng đg sai số xy sai số yaw thử  tên
G1   SUCCEEDED     38.5s     8.0 m    0.23 m        0°    1  Phòng trên-trái (xe hơi)
G2   SUCCEEDED     45.0s    11.6 m    0.21 m       14°    1  Khu dưới-trái (người, ghế)
G3   SUCCEEDED     46.9s    11.6 m    0.23 m       14°    1  Hành lang phải (trụ cứu hoả, người, bình chữa cháy)
Goal thành công: 3/3
=> ĐẠT: robot tự đi qua 3 goal liên tiếp
[tb4_lab04] Đã lưu kết quả: ~/tb4_results/nav_<thời_gian>/run.json, summary.csv
```

(Số liệu ở trên lấy từ lần kiểm thử của tác giả, thời gian tính theo giờ mô phỏng; trên máy bạn sẽ khác tuỳ real-time factor của Gazebo. Sai số dừng ~0.2 m / ≤ 14° là dung sai mặc định của Nav2: 0.25 m / 0.25 rad.)

Chi tiết hành vi:

- **Initial pose** chỉ được đặt khi robot **còn trong dock** (chắc chắn đang ở điểm spawn). Chạy node lần 2 khi
  robot đã ở giữa mê cung thì node **giữ** ước lượng của AMCL (đặt lại (0,0,0) lúc đó sẽ làm AMCL sai). Ép buộc:
  `-p initial_pose_mode:=always|never`. Initial pose được gửi kèm hiệp phương sai như nút 2D Pose Estimate (bản
  gốc `setInitialPose` của nav2_simple_commander gửi hiệp phương sai 0 → mọi hạt AMCL trùng một điểm).
- Goal thất bại (`ABORTED`) → xoá costmap, thử lại 1 lần (`max_retries`); quá `goal_timeout` (300 s mô phỏng)
  → huỷ, chuyển goal tiếp theo.
- Trên RViz2: mũi tên + nhãn **G1, G2, G3** (topic `/nav_goals/markers`): vàng = chờ, xanh dương = đang đi,
  xanh lá = tới nơi, đỏ = thất bại. Đường xanh lá = global plan Nav2 vừa lập (`/plan`).
- **Ctrl+C**: node huỷ goal đang chạy (robot dừng) rồi mới thoát.
- Tuỳ chọn: `-p look_around:=true` (xoay 360° tại mỗi goal cho camera quét), `-p return_home:=true`
  (về chỗ sau undock), `-p loops:=2`, `-p goals_file:=/duong/dan/goals.yaml`.

Theo dõi độc lập (bằng chứng không điều khiển tay, không va chạm) – **Terminal 4** (tuỳ chọn):
`ros2 run tb4_lab04 nav_monitor.py` → Ctrl+C sau khi xong: `ĐẠT (>= 3 goal thành công, không va chạm)`.

**Ảnh cho báo cáo** – bản đồ + goal + đường Nav2 đã lập + quỹ đạo thật của robot (+ vị trí robot lúc YOLO phát hiện
vật thể):

```bash
ros2 run tb4_lab04 check_goals.py --plot ~/tb4_results/map_run.png \
    --run ~/tb4_results/nav_<thời_gian>/run.json \
    --detections ~/tb4_results/yolo_<thời_gian>/detections.csv
```

---

## 5. Phần 4 – Nhận diện vật thể bằng YOLO

**Terminal 2** (chạy song song khi robot di chuyển – nên bật **trước** `waypoint_navigator.py`):

```bash
ros2 launch tb4_lab04 yolo.launch.py
# hoặc: ros2 run tb4_lab04 yolo_detector.py
```

- Cửa sổ OpenCV **"YOLO - camera TurtleBot 4"** (phóng ×2): bounding box, `tên_lớp độ_tự_tin`, FPS, vị trí robot.
- RViz2: panel **YOLO** (nhóm *Camera*) hiển thị `/yolo/image_annotated`.
- Terminal:

```
[yolo_detector]: Model sẵn sàng sau 3.0 s: 80 lớp, thiết bị cpu, 2 luồng CPU, ~120 ms/ảnh
[yolo_detector]: *** PHÁT HIỆN MỚI: person (conf 0.86) – robot tại (-5.95, -2.71)
[yolo_detector]: [t=212.4s | robot (-5.95, -2.71)] 2 vật thể: person 0.86 [139,30,201,231], chair 0.52 [...]
...
================ TỔNG KẾT YOLO ================
lớp                số khung  conf max lần đầu (s)  robot lúc thấy lần đầu (map)
car                      41      0.81      118.2  (-4.80, 5.41)
person                  133      0.90      150.3  (-3.10, 1.62)
...
Kết quả: ~/tb4_results/yolo_<thời_gian> (detections.csv, first_*.jpg, best_*.jpg)
```

- `first_<lớp>.jpg` / `best_<lớp>.jpg`: khung hình đầu tiên / tự tin nhất của mỗi lớp – dùng làm ảnh báo cáo.
- `/yolo/detections` (`vision_msgs/msg/Detection2DArray`) cho node khác dùng.

Model và tham số (`config/yolo.yaml`, hoặc tham số launch):

| Muốn | Lệnh |
|---|---|
| YOLOv8 thay YOLO11 | `ros2 launch tb4_lab04 yolo.launch.py yolo_model:=yolov8n.pt` |
| Chính xác hơn (chậm hơn) | `yolo_model:=yolo11s.pt` |
| Nhận "fire extinguisher" (COCO không có lớp này) | `yolo_model:=yolov8s-worldv2.pt` (YOLO-World, lớp ở `world_classes`; lần đầu tự cài gói CLIP – cần Internet) |
| Máy yếu | sửa `config/yolo.yaml`: `imgsz: 320`, `max_rate: 3.0` |
| GPU NVIDIA | `device:=0` |

Về chất lượng nhận diện trong mô phỏng (nói thẳng): camera mô phỏng chỉ 320×240, model Gazebo là mô hình 3D đơn
giản, nên YOLO nhận **người** và **xe hơi** ổn định nhất; ghế, trụ cứu hoả có thể độ tự tin thấp hoặc lúc có lúc
không; **bình chữa cháy không thuộc 80 lớp COCO** – YOLO11/YOLOv8 chuẩn sẽ không nhận ra (có thể nhận nhầm thành
`bottle`), cần YOLO-World. Ghi đúng điều này trong báo cáo thay vì cố ép kết quả.

---

## 6. Chạy tất cả bằng một lệnh

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 demo.launch.py
```

= `navigation.launch.py` + `yolo.launch.py` + (sau 25 s) `waypoint_navigator.py`. Tham số của cả ba dùng chung,
ví dụ `software_render:=true yolo_model:=yolov8n.pt run_navigator:=false`. Để quay video nên dùng nhiều terminal
(mục 7) – người xem thấy rõ từng bước; `demo.launch.py` tiện để chạy thử.

---

## 7. Kịch bản quay video demo

Quay toàn màn hình (OBS Studio). Bố trí: RViz2 (lớn) + Gazebo + cửa sổ YOLO + các terminal.

1. **Load bản đồ + localization (~1.5 phút)**: `kill_sim.sh`, `ros2 launch tb4_lab04 navigation.launch.py`;
   Gazebo có người/xe/ghế…; RViz2 hiện bản đồ tuần trước, robot ở dock, hạt AMCL tụ quanh robot, **LiDAR trùng
   tường** (phóng to); `localization_check.py` → `ĐẠT`; (tuỳ chọn) so vị trí robot Gazebo ↔ RViz2.
2. **Toạ độ goal (~1 phút)**: `goal_recorder.py` + Publish Point vài điểm; mở `config/goals.yaml`;
   `check_goals.py --plot` + mở ảnh.
3. **YOLO**: `ros2 launch tb4_lab04 yolo.launch.py` – cửa sổ YOLO mở ra.
4. **Navigation tự động**: `ros2 run tb4_lab04 waypoint_navigator.py`; **bỏ tay khỏi bàn phím/chuột**. Quay cho
   thấy: robot tự undock, đường xanh (global plan) trên RViz2, robot đi G1 → G2 → G3, marker đổi màu, cửa sổ YOLO
   vẽ bbox khi gặp người/xe…, terminal in `PHÁT HIỆN MỚI`. Có thể tua nhanh đoạn di chuyển dài.
5. **Kết quả**: bảng `TỔNG KẾT` (3/3 SUCCEEDED, `ĐẠT`), Ctrl+C YOLO → bảng tổng kết YOLO; mở `best_person.jpg`.

---

## 8. Nộp bài: GitHub, video, báo cáo PDF

### 8.1. GitHub (Public)

Nên tạo repo mới cho bài này (vd. `tb4-nav2-yolo`) để không lẫn với repo tuần trước:

```bash
cd ~/workspaces/tb4_gazebo/src/tb4_lab04
git add -A
git status                 # phải có maps/map.yaml, maps/map.pgm, config/goals.yaml, scripts/*.py, launch/*.py
git commit -m "TurtleBot 4: AMCL + Nav2 waypoint navigator + YOLO detector"
git remote set-url origin https://github.com/<ten-ban>/<repo-moi>.git    # hoặc: git remote add origin ...
git push -u origin main
```

Repo đã có: source code (`scripts/` – node điều hướng `waypoint_navigator.py`, node YOLO `yolo_detector.py`),
launch (`launch/`), bản đồ (`maps/`), cấu hình (`config/`, `rviz/`), README này. `.gitignore` đã loại
`build/ install/ log/`, file model `*.pt`, kết quả chạy.

### 8.2. Video

Google Drive → Share → General access: **Anyone with the link** (Viewer) → copy link.

### 8.3. Báo cáo PDF

```bash
pip3 install --user reportlab pypdf matplotlib
cd ~/workspaces/tb4_gazebo/src/tb4_lab04
nano docs/report_info.yaml               # link video, link GitHub, phần nhận xét
python3 docs/report/diagrams.py          # vẽ lại sơ đồ khối (docs/report/fig/)
python3 docs/report/build_report.py      # -> docs/report/BaoCao_Bai5_TurtleBot4_Nav2_YOLO.pdf
```

Ảnh chụp màn hình dùng trong báo cáo nằm ở `docs/report/fig_user/`. Script in ra danh sách mục còn thiếu (ảnh, link).

---

## 9. Xử lý sự cố

| Triệu chứng | Nguyên nhân → cách sửa |
|---|---|
| `yolo_detector`: `NumPy 2.x không dùng được với cv_bridge` / `_ARRAY_API not found` / node chết với `exit code -11` (segfault) | NumPy 2.x → `pip3 install --user "numpy<2" "opencv-python<4.11"` (mục 1.3) |
| `Không import được ultralytics/torch` | chưa cài mục 1.3 (chú ý `--user`, cùng `python3` của ROS) |
| `ModuleNotFoundError: No module named 'rclpy'` khi `ros2 run` / đầu dòng lệnh có `(base)` | đang bật conda → `conda deactivate`, mở terminal mới, cài lại mục 1.3 nếu đã cài trong conda |
| Cửa sổ YOLO không mở, log `Không mở được cửa sổ OpenCV` | đang dùng `opencv-python-headless` → `pip3 uninstall -y opencv-python-headless && pip3 install --user "opencv-python<4.11"`; vẫn xem được trên RViz2 (panel YOLO) |
| `Chưa nhận ảnh nào trên /oakd/rgb/preview/image_raw` | mô phỏng chưa chạy / `ros2 topic hz /oakd/rgb/preview/image_raw`; `software_render:=true` thì camera rất chậm (vài ảnh/giây) – bình thường |
| YOLO quá chậm, Gazebo giật | `config/yolo.yaml`: `imgsz: 320`, `max_rate: 2.0`; dùng `yolo11n.pt` |
| Không thấy vật thể trong Gazebo, log `[spawn_objects] KHÔNG tải được` | không có Internet tới `fuel.gazebosim.org` → có mạng thì `spawn_objects.py --download-only` rồi chạy lại launch (hoặc spawn khi sim đang chạy: `ros2 run tb4_lab04 spawn_objects.py`) |
| `[spawn_objects] ! Spawn ... thất bại` | world không phải `maze` (truyền `world:=...` giống lúc launch) hoặc vật thể đã có (chạy lại spawner 2 lần) |
| Navigator đứng ở `Chờ amcl ... (trạng thái: chưa có node)` | Terminal 1 chưa chạy `navigation.launch.py` hoặc chưa lên xong (chờ log `Khởi động Nav2`) |
| `Undock thất bại: status=... CANCELED` | phản xạ an toàn Create 3 / cảm biến cliff đo sai (WSL2) → không truyền `cliff_reflex:=true`; thử `software_render:=true` ([chi tiết](LAB04_SLAM_README.md#82-đồ-hoạ--cảm-biến-hay-gặp-nhất-nhất-là-wsl2)) |
| Goal `ABORTED`, log Nav2 `Failed to make progress` / `No valid path` | goal sát tường / trong vùng xám / bị vật thể chặn → `check_goals.py`, dời goal ra xa tường ≥ 0.5 m |
| Robot đi sai hướng ngay từ đầu | initial pose sai (spawn khác chỗ / world khác) → Ctrl+C navigator, 2D Pose Estimate trên RViz2, `localization_check.py`, chạy lại navigator (nó sẽ không ghi đè vì robot đã rời dock) |
| Chạy navigator lần 2: robot còn ở giữa mê cung | bình thường – node giữ pose AMCL, bỏ qua undock, đi lại các goal |
| `nav_monitor.py` báo Nav2 "ĐỨNG HÌNH" | máy quá tải → `kill_sim.sh`, đóng bớt ứng dụng, giảm `max_rate` của YOLO |

Lỗi cài đặt / Gazebo / đồ hoạ / WSL2 chung: [LAB04_SLAM_README.md mục 8](LAB04_SLAM_README.md#8-xử-lý-sự-cố).
Gom log gửi người hỗ trợ: `ros2 run tb4_lab04 collect_debug.sh` → `~/tb4_debug_*.txt`.

---

## 10. Kiến trúc: package, node, topic, action

### 10.1. Cấu trúc repo

```
tb4_lab04/                               # package ament_cmake "tb4_lab04"
├── launch/
│   ├── navigation.launch.py             # Gazebo + vật thể + map_server/AMCL + Nav2 + RViz2   (Phần 1, 3)
│   ├── yolo.launch.py                   # node YOLO + config/yolo.yaml                        (Phần 4)
│   ├── demo.launch.py                   # tất cả + node điều hướng
│   ├── tb4_lab04_common.py              # phần dùng chung: kiểm tra gói, include TurtleBot 4, RViz
│   └── sim.launch.py, mapping.launch.py, explore.launch.py      # bài tuần trước (SLAM)
├── scripts/
│   ├── waypoint_navigator.py            # NODE ĐIỀU HƯỚNG: nav2_simple_commander, Goal 1 -> 2 -> 3
│   ├── yolo_detector.py                 # NODE YOLO: Image -> cv_bridge -> YOLO -> bbox/terminal/topic
│   ├── spawn_objects.py                 # thêm vật thể Gazebo Fuel vào world maze
│   ├── goal_recorder.py                 # ghi toạ độ goal từ /clicked_point, /amcl_pose
│   ├── check_goals.py                   # kiểm tra goal trên bản đồ + vẽ ảnh báo cáo
│   ├── localization_check.py            # LiDAR có trùng tường bản đồ (đánh giá initial pose)
│   ├── lab_common.py                    # tiện ích dùng chung (Ctrl+C, đường dẫn, góc)
│   ├── compare_pose.py, nav_monitor.py, dock_obstacle.py, wait_for_sim.py, doctor.sh, kill_sim.sh, ...
├── config/
│   ├── goals.yaml                       # toạ độ Goal 1..3 (frame map)
│   ├── objects.yaml                     # vật thể: model Fuel, toạ độ, footprint, lớp COCO
│   ├── yolo.yaml                        # tham số node YOLO
│   ├── localization.yaml, nav2.yaml     # AMCL + map_server, Nav2 (gốc TurtleBot 4 + chỉnh sửa có lý do)
│   └── slam.yaml, nav2_explore.yaml, create3_*.yaml
├── maps/map.yaml, maps/map.pgm          # bản đồ world maze của tuần trước
├── rviz/nav.rviz                        # map + LiDAR + AMCL + costmap + plan + panel YOLO + marker goal
├── docs/                                # report/ (mã dựng báo cáo PDF), report_info.yaml, LAB04_SLAM_README.md
└── test/                                # unit test
```

### 10.2. Luồng dữ liệu

```
                 ┌──────────────────── Gazebo Fortress (world maze + vật thể Fuel) ───────────────────┐
                 │  TurtleBot 4: RPLIDAR, OAK-D (rgbd_camera 320x240), Create 3 (diff drive, dock)     │
                 └──┬───────────┬──────────────────┬──────────────────────┬────────────────▲─────────┘
            /scan (LaserScan)  /odom, TF odom→base_link  /oakd/rgb/preview/image_raw   /cmd_vel│
                    │           │                    │                                     │
  topic_tools delay ▼ /scan_nav │                    ▼                                     │
  maps/map.yaml ─► map_server ─► /map ─┐       yolo_detector ─► /yolo/image_annotated      │
                    │                  ▼          (cv_bridge,     /yolo/detections         │
                    └──────────────► amcl ─► TF map→odom, /amcl_pose   YOLO)  cửa sổ OpenCV  │
                                         ▲ /initialpose                                    │
  goals.yaml ─► waypoint_navigator ──────┘                                                 │
   (BasicNavigator)  │ action /undock (Create 3)                                           │
                     │ action /navigate_to_pose ─► bt_navigator (Behavior Tree)            │
                     │                              ├► planner_server (NavFn, global costmap) ─► /plan
                     │                              ├► controller_server (DWB, local costmap) ─► velocity_smoother ┘
                     │                              └► behavior_server (spin/backup/wait – recovery)
                     └► /nav_goals/markers (RViz2)
```

### 10.3. Node / package chính

| Node | Package | Vai trò |
|---|---|---|
| Gazebo + `ros_gz_bridge`, `motion_control`… | `turtlebot4_ignition_bringup`, `irobot_create_*` | mô phỏng robot, cảm biến, dock |
| `spawn_objects.py` → `create` | `tb4_lab04`, `ros_gz_sim` | thêm vật thể vào world |
| `map_server` | `nav2_map_server` | nạp `map.yaml/map.pgm` → `/map` |
| `amcl` | `nav2_amcl` | định vị Monte Carlo trên bản đồ → TF `map→odom` |
| `scan_delay` | `topic_tools` | `/scan` → `/scan_nav` trễ 0.1 s (tránh deadlock tf2 của Humble) |
| `bt_navigator`, `planner_server`, `controller_server`, `behavior_server`, `smoother_server`, `velocity_smoother`, `waypoint_follower`, `lifecycle_manager_*` | `nav2_*` (qua `turtlebot4_navigation/nav2.launch.py`) | Nav2 |
| `tb4_lab04_dock_obstacle` | `tb4_lab04` | đánh dấu dock (thấp hơn LiDAR) là vật cản trong costmap |
| `tb4_waypoint_navigator` | `tb4_lab04` + `nav2_simple_commander` | **node điều hướng của bài** |
| `yolo_detector` | `tb4_lab04` + `cv_bridge` + `ultralytics` | **node nhận diện của bài** |

### 10.4. Topic / action / service chính

| Tên | Kiểu | Dùng cho |
|---|---|---|
| `/scan` → `/scan_nav` | `sensor_msgs/msg/LaserScan` | AMCL, costmap, `localization_check.py` |
| `/odom`, `/tf`, `/tf_static` | `nav_msgs/msg/Odometry`, `tf2_msgs/msg/TFMessage` | cây frame `map → odom → base_link → cảm biến` |
| `/map` | `nav_msgs/msg/OccupancyGrid` | map_server → AMCL, global costmap, RViz2 |
| `/initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | navigator / 2D Pose Estimate → AMCL |
| `/amcl_pose`, `/particle_cloud` | `PoseWithCovarianceStamped`, `nav2_msgs/msg/ParticleCloud` | pose ước lượng, tập hạt |
| `/clicked_point` | `geometry_msgs/msg/PointStamped` | RViz2 Publish Point → `goal_recorder.py` |
| `/navigate_to_pose` (action) | `nav2_msgs/action/NavigateToPose` | navigator → bt_navigator (feedback: quãng đường còn lại, ETA, recovery) |
| `/spin` (action) | `nav2_msgs/action/Spin` | `look_around` |
| `/undock`, `/dock` (action), `/dock_status` | `irobot_create_msgs` | rời / vào dock |
| `/<node>/get_state` (service) | `lifecycle_msgs/srv/GetState` | navigator chờ `amcl`, `bt_navigator` active |
| `/global_costmap/clear_entirely_global_costmap`, `/local_costmap/...` (service) | `nav2_msgs/srv/ClearEntireCostmap` | xoá costmap trước khi thử lại goal |
| `/plan`, `/local_plan` | `nav_msgs/msg/Path` | đường đi toàn cục / cục bộ |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Nav2 → Create 3 |
| `/oakd/rgb/preview/image_raw` | `sensor_msgs/msg/Image` (rgb8 320x240) | camera → YOLO |
| `/yolo/image_annotated` | `sensor_msgs/msg/Image` (bgr8) | ảnh đã vẽ bbox → RViz2 |
| `/yolo/detections` | `vision_msgs/msg/Detection2DArray` | kết quả nhận diện |
| `/nav_goals/markers` | `visualization_msgs/msg/MarkerArray` | goal trên RViz2 |

### 10.5. Nav2 lập kế hoạch thế nào (tóm tắt cho báo cáo)

1. `waypoint_navigator` gửi goal (PoseStamped, frame `map`) qua action `/navigate_to_pose`.
2. `bt_navigator` chạy cây hành vi mặc định `navigate_to_pose_w_replanning_and_recovery`: cứ **1 Hz** gọi
   `planner_server` lập lại đường, giao đường cho `controller_server`; thất bại thì chạy nhánh recovery (xoá costmap,
   xoay, chờ, lùi) rồi thử lại.
3. `planner_server` – **NavFn** (Dijkstra) trên **global costmap** = bản đồ tĩnh + vật cản LiDAR (`/scan_nav`) + dock +
   vùng thổi phồng (`inflation_radius` 0.45 m, `robot_radius` 0.175 m) → `/plan`.
4. `controller_server` – **DWB**: mỗi chu kỳ 20 Hz lấy mẫu các cặp (v, ω) trong giới hạn gia tốc, mô phỏng quỹ đạo
   1.7 s trên **local costmap** (3×3 m quanh robot, frame `odom`), chấm điểm bằng các critic (bám đường, hướng tới
   goal, tránh vật cản, chống dao động) → `/cmd_vel` (≤ 0.26 m/s) qua `velocity_smoother`.
5. Goal đạt khi robot cách goal ≤ 0.25 m và lệch hướng ≤ 0.25 rad (`general_goal_checker`).
6. AMCL cập nhật TF `map→odom` liên tục từ LiDAR, nên dù odometry trôi, đường đi vẫn đúng trên bản đồ.

---

## 11. Tham số

`navigation.launch.py`: chung (`world` maze, `model` standard|lite, `x y z yaw`, `use_rviz`, `rviz_config`,
`software_render`, `cliff_reflex`) + `map`, `use_nav2`, `spawn_objects` (true), `objects_file`,
`localization_params_file`, `nav2_params_file`, `localization_delay` (2 s), `nav2_delay` (8 s).

`yolo.launch.py`: `yolo_params_file`, `yolo_model`, `conf`, `device`, `image_topic`, `show_window`.

`demo.launch.py`: tất cả ở trên + `run_navigator` (true), `navigator_delay` (25 s), `goals_file`, `run_yolo` (true).

`waypoint_navigator.py` (`--ros-args -p tên:=giá_trị`): `goals_file`, `initial_pose_mode` (auto|always|never),
`undock` (true), `pause_at_goal` (2 s), `look_around` (false), `goal_timeout` (300 s), `max_retries` (1),
`loops` (1), `return_home` (false), `dock_at_end` (false), `startup_timeout` (300 s), `results_dir`.

`yolo_detector.py`: xem chú thích trong `config/yolo.yaml`.

Xem đầy đủ: `ros2 launch tb4_lab04 <file>.launch.py --show-args`.

---

## 12. Kiểm thử

```bash
cd ~/workspaces/tb4_gazebo/src/tb4_lab04
python3 test/test_nav_yolo_logic.py      # logic bài này (đọc goal, kiểm tra goal, cache Fuel, YOLO helper, ...)
python3 test/test_pure_logic.py          # logic bài tuần trước
```

Tài liệu tham khảo: [TurtleBot 4 Navigator](https://turtlebot.github.io/turtlebot4-user-manual/tutorials/turtlebot4_navigator.html) ·
[Nav2 Simple Commander API](https://docs.nav2.org/commander_api/index.html) ·
[Ultralytics YOLO](https://docs.ultralytics.com/) · [TurtleBot 4 Simulator](https://github.com/turtlebot/turtlebot4_simulator) ·
[Gazebo Fuel](https://app.gazebosim.org/fuel/models)
