# TurtleBot 4 – Giao tiếp phi ngôn ngữ: điều khiển bằng cử chỉ tay (Bài 6)

ROS 2 Humble · Ignition Gazebo Fortress · TurtleBot 4 Simulator · OpenCV · MediaPipe Gesture Recognizer

Webcam laptop → **`gesture_recognition_node`** (OpenCV + MediaPipe, nhận diện 7 cử chỉ + vẫy tay) →
`/detected_gesture` → **`robot_behavior_node`** (máy trạng thái chọn → xác nhận → thực hiện, chống nhiễu,
watchdog) → `/cmd_vel` → TurtleBot 4 trong Gazebo.

| Cử chỉ | Tên trên `/detected_gesture` | Hành vi robot |
|---|---|---|
| Vẫy tay | `Wave` | **chọn** “chào lại”: xoay trái–phải (±34°, 2 lần) |
| Giơ 1 ngón tay | `Pointing_Up` | **chọn** tiến–lùi 4 lần (0,35 m mỗi lần) |
| Giơ 2 ngón tay | `Victory` | **chọn** quỹ đạo tròn (r = 0,5 m, 1 vòng) |
| Ngón cái | `Thumb_Up` | **xác nhận** → thực hiện hành vi đã chọn |
| Xoè bàn tay | `Open_Palm` | **dừng ngay** (giữ lựa chọn – ngón cái lần nữa = chạy lại từ đầu) |
| Nắm tay | `Closed_Fist` | **huỷ** hành vi + xoá lựa chọn → trạng thái chờ |

Model MediaPipe còn nhận `Thumb_Down`, `ILoveYou` (hiển thị/publish nhưng không gắn hành vi) → tổng cộng
**8 cử chỉ** (yêu cầu tối thiểu 5).

| Phần của đề | Lệnh | Bằng chứng |
|---|---|---|
| 1 – Simulation + `/cmd_vel` + webcam | `ros2 launch tb4_lab04 gesture_sim.launch.py` · `ros2 run tb4_lab04 check_cmd_vel.py` · `ros2 run tb4_lab04 webcam_test.py` | robot quay/tiến/lùi, `KẾT QUẢ: ĐẠT`; cửa sổ webcam + FPS |
| 2 – Nhận diện cử chỉ | `ros2 launch tb4_lab04 gesture.launch.py run_behavior:=false` · `ros2 topic echo /detected_gesture` | cửa sổ: landmark, tên cử chỉ, % tin cậy |
| 3 – Điều khiển robot | `ros2 launch tb4_lab04 gesture.launch.py` | robot làm đúng 6 hành vi; log `[trạng thái]`; `plot_gesture_run.py` |
| Tất cả một lệnh | `ros2 launch tb4_lab04 gesture_demo.launch.py` | – |
| Báo cáo PDF | `python3 docs/report/build_report_bai6.py` | `docs/report/BaoCao_Bai6_TurtleBot4_Gesture.pdf` |

Repo vẫn giữ nguyên các bài trước (SLAM, Nav2 + YOLO): [`docs/LAB05_NAV2_YOLO_README.md`](docs/LAB05_NAV2_YOLO_README.md),
[`docs/LAB04_SLAM_README.md`](docs/LAB04_SLAM_README.md). Tên package vẫn là `tb4_lab04` (đổi tên sẽ làm hỏng
workspace và lệnh của các bài trước).

---

## Mục lục

0. [Đọc trước – những điều hay làm hỏng bài](#0-đọc-trước--những-điều-hay-làm-hỏng-bài)
1. [Cài đặt](#1-cài-đặt)
2. [Phần 1 – Simulation, kiểm tra /cmd_vel, webcam](#2-phần-1--simulation-kiểm-tra-cmd_vel-webcam)
3. [Phần 2 – Node nhận diện cử chỉ](#3-phần-2--node-nhận-diện-cử-chỉ)
4. [Phần 3 – Node điều khiển hành vi](#4-phần-3--node-điều-khiển-hành-vi)
5. [Chạy demo và kịch bản quay video](#5-chạy-demo-và-kịch-bản-quay-video)
6. [Thử không cần webcam](#6-thử-không-cần-webcam)
7. [Kết quả, log, ảnh quỹ đạo](#7-kết-quả-log-ảnh-quỹ-đạo)
8. [Nộp bài: GitHub, Google Drive, PDF](#8-nộp-bài-github-google-drive-pdf)
9. [Xử lý sự cố](#9-xử-lý-sự-cố)
10. [Kiến trúc: node, topic, luồng xử lý](#10-kiến-trúc-node-topic-luồng-xử-lý)
11. [Tham số](#11-tham-số)
12. [Kiểm thử và giới hạn](#12-kiểm-thử-và-giới-hạn)

---

## 0. Đọc trước – những điều hay làm hỏng bài

1. **Webcam phải thấy được từ Ubuntu.** Ubuntu cài thẳng trên máy: OK. **Máy ảo** (VirtualBox/VMware): bật
   chuyển webcam vào máy ảo (VirtualBox: *Devices → Webcams*). **WSL2**: phải chuyển USB bằng `usbipd` (webcam
   laptop nhiều khi không làm được) – nên dùng Ubuntu cài thật. Kiểm tra: `ls /dev/video*`, `webcam_test.py`.
2. **`pip install mediapipe` (bản mới nhất) kéo NumPy 2 về → `cv_bridge` và node YOLO của bài trước hỏng.**
   Dùng `bash scripts/install_gesture_deps.sh` (ghim `mediapipe==0.10.21`, `numpy<2`, OpenCV 4.10).
3. **Không bật conda** trong terminal chạy ROS (`(base)` ở đầu dòng → `conda deactivate`).
4. **Robot khởi động khi đang ở dock.** `robot_behavior_node` tự **undock + chạy thẳng 1 m ra giữa sân** (mất
   ~20–40 s, cửa sổ webcam ghi `Robot: SETUP`). Chờ tới khi hiện `Robot: IDLE` / `WAITING` rồi mới ra cử chỉ.
   Nếu bước này bị huỷ (xoè tay / nắm tay / mất tín hiệu), lần xác nhận đầu tiên sẽ làm nốt trước rồi mới chạy
   hành vi: còn trong dock → undock + ra giữa sân; đã lùi ra nửa chừng (có thể còn quay mặt vào dock) → quay mặt
   ra xa dock rồi chạy ra giữa sân. Không bao giờ chạy tiến / vòng tròn ngay cạnh dock.
5. **Robot chỉ chạy sau ngón cái xác nhận** và chỉ phản ứng khi cử chỉ **thay đổi**. Giữ một cử chỉ ~0,5 s cho
   tới khi dòng `ON DINH -> /detected_gesture` đổi, sau đó **hạ tay** (hoặc đổi cử chỉ) rồi mới ra lệnh tiếp.
6. **Vẫy tay bắt đầu bằng bàn tay xoè** → robot nhận `Open_Palm` (dừng) trước, rồi `Wave`. Đó là thiết kế
   (dừng luôn được ưu tiên); vẫy khi robot đang chạy sẽ làm robot dừng.
7. **Không có cử chỉ nào trong 1 s (node nhận diện tắt / camera lỗi) → robot dừng** (`SIGNAL_LOST`). Tay ra khỏi
   khung hình thì KHÔNG dừng (node vẫn gửi `None`) – robot tiếp tục hành vi đã xác nhận.
8. Một phiên mô phỏng một lúc: `Ctrl+C` rồi `ros2 run tb4_lab04 kill_sim.sh` trước khi chạy lại. Script còn xoá
   file shared-memory cũ của FastDDS (`/dev/shm/fastrtps_*`) – khi kiểm thử, các file này (do tiến trình bị
   kill để lại) đã làm Gazebo đứng ở bước nạp world, không bao giờ có `/odom`.
9. Log đỏ/vàng của mô phỏng TurtleBot 4 phần lớn là bình thường
   ([danh sách](docs/LAB04_SLAM_README.md#81-log-trông-như-lỗi-nhưng-bình-thường)).

---

## 1. Cài đặt

### 1.1. Gói ROS

Đã có môi trường các bài trước (ROS 2 Humble, Gazebo Fortress, TurtleBot 4 simulator). Máy mới:
[`docs/LAB04_SLAM_README.md` mục 1](docs/LAB04_SLAM_README.md#1-cài-đặt-làm-một-lần). Bài này chỉ cần thêm
`irobot_create_msgs` (đã có cùng simulator) và `tf2_ros`:

```bash
sudo apt update
sudo apt install -y ros-humble-turtlebot4-simulator ros-humble-irobot-create-msgs ros-humble-tf2-ros \
  python3-pip python3-matplotlib python3-yaml v4l-utils
```

### 1.2. Workspace và build

```bash
mkdir -p ~/workspaces/tb4_gazebo/src && cd ~/workspaces/tb4_gazebo/src
# A) từ file nén:  tar -xJf ~/Downloads/tb4_lab06.tar.xz -C ~/workspaces/tb4_gazebo/src
# B) từ GitHub:    git clone https://github.com/<ten-ban>/<repo>.git tb4_lab04
cd ~/workspaces/tb4_gazebo
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select tb4_lab04
source install/setup.bash
```

Đã có thư mục `tb4_lab04` của bài trước: đổi tên nó (`mv tb4_lab04 ~/tb4_lab04_bai5`) rồi giải nén bản này vào,
xoá `build/tb4_lab04 install/tb4_lab04` và build lại.

Mỗi terminal mới (hoặc thêm vào `~/.bashrc`):

```bash
source /opt/ros/humble/setup.bash
source ~/workspaces/tb4_gazebo/install/setup.bash
export ROS_LOCALHOST_ONLY=1
```

### 1.3. OpenCV + MediaPipe

```bash
cd ~/workspaces/tb4_gazebo/src/tb4_lab04
bash scripts/install_gesture_deps.sh
```

Script cài `mediapipe==0.10.21`, `numpy<2`, `opencv-python<4.11`, `opencv-contrib-python<4.11` (cả hai OpenCV
cùng bản 4.10 vì chúng ghi chung thư mục `cv2`), rồi in `[PASS]/[FAIL]` cho NumPy, OpenCV (có GUI), MediaPipe
(chạy thử model), cv_bridge, và liệt kê webcam. Cài tay:

```bash
pip3 install --user "mediapipe==0.10.21" "numpy<2" "opencv-python<4.11" "opencv-contrib-python<4.11"
```

Model `models/gesture_recognizer.task` (MediaPipe, float16, 8,4 MB, Apache 2.0) đã có sẵn trong repo – không cần
tải. Thiếu file thì node tự tải từ
`https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task`
về `~/.cache/tb4_lab04/models/`.

---

## 2. Phần 1 – Simulation, kiểm tra /cmd_vel, webcam

**Terminal 1** – Gazebo + TurtleBot 4 trong world **`gesture_arena`** (sân phẳng 9 m × 9 m, tường thấp bao
quanh, không vật cản bên trong – `worlds/gesture_arena.sdf`):

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 gesture_sim.launch.py
#   tuỳ chọn: software_render:=true (WSL2/driver lỗi), use_rviz:=true, world:=maze (world bài trước)
```

Robot xuất hiện trong dock ở gốc toạ độ. (Thời lượng các bước của `check_cmd_vel.py` tính theo giờ mô phỏng nên
máy chậm vẫn đo đúng – số liệu dưới đây là lần chạy thật trong môi trường kiểm thử.) Vòng tròn màu xanh nhạt trên sàn (bán kính 1,6 m) đánh dấu vùng làm
việc của các hành vi cử chỉ – chỉ để nhìn, không có va chạm.

**Terminal 2** – kiểm tra robot nhận `/cmd_vel` (tự undock nếu đang ở dock, quay trái/phải, tiến/lùi, đo bằng
`/odom`):

```bash
ros2 run tb4_lab04 check_cmd_vel.py
```

```
Robot đang ở dock -> /undock
Undock xong
Pose trước: x=-0.35 y=-0.00 yaw=-169°
/cmd_vel: quay trái 0.5 rad/s, 3 s
  -> đã quay 86°
/cmd_vel: quay phải 0.5 rad/s, 3 s
/cmd_vel: tiến 0.1 m/s, 2 s
  -> đã đi 0.20 m
/cmd_vel: lùi 0.1 m/s, 2 s
Pose sau: x=-0.35 y=0.00 yaw=-169° (lệch 0.01 m so với trước)
KẾT QUẢ: ĐẠT – robot nhận lệnh /cmd_vel
```

Kiểm tra bằng lệnh ROS thuần (đưa vào video/báo cáo cũng được):

```bash
ros2 topic info /cmd_vel                                   # Subscription count >= 1
ros2 topic pub -r 10 -t 30 /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.5}}"
ros2 topic echo /odom --field twist.twist                  # angular.z ~ 0.5
```

**Webcam bằng OpenCV** (không cần ROS chạy):

```bash
ros2 run tb4_lab04 webcam_test.py          # cửa sổ hình webcam + độ phân giải + FPS; q để thoát
ros2 run tb4_lab04 webcam_test.py --list   # dò camera 0..3
ros2 run tb4_lab04 webcam_test.py 1        # webcam USB
```

---

## 3. Phần 2 – Node nhận diện cử chỉ

```bash
ros2 launch tb4_lab04 gesture.launch.py run_behavior:=false     # chỉ nhận diện
ros2 topic echo /detected_gesture                               # terminal khác
```

Cửa sổ **“Gesture Recognition - TurtleBot 4”** (ảnh đã lật gương):

- 21 landmark bàn tay + khung xương;
- dòng 1 `Khung: Thumb Up (ngon cai) 87%` – cử chỉ MediaPipe trả về ở khung hiện tại + **độ tin cậy**
  (thanh `conf`);
- dòng 2 `ON DINH -> /detected_gesture: Thumb_Up` – kết quả đã lọc nhiễu, đúng giá trị đang publish
  (thanh `vote` = tỉ lệ khung đồng thuận);
- FPS, số nhịp vẫy `wave n/3`, bảng chú giải cử chỉ → hành vi;
- dải dưới: trạng thái robot (`IDLE`, `SELECTED`, `EXECUTING (45%)`...) nhận từ `/robot_behavior/state`.

Terminal in mỗi lần nhãn ổn định đổi: `Cử chỉ ổn định: Victory (khung: Victory 0.91)`.

### 3.1. Cách hoạt động (`scripts/gesture_recognition_node.py`)

1. **OpenCV** đọc webcam ở luồng riêng (`cv2.VideoCapture`, V4L2, 640×480, buffer 1 khung – luôn lấy khung mới
   nhất nên không trễ dồn), lật gương.
2. **MediaPipe Gesture Recognizer** (Tasks API, chế độ `VIDEO`): mô hình phát hiện lòng bàn tay → mô hình
   21 landmark 3D → bộ phân loại cử chỉ (7 lớp: `Closed_Fist, Open_Palm, Pointing_Up, Thumb_Down, Thumb_Up,
   Victory, ILoveYou` + `None`) trả **tên + độ tin cậy**. Chế độ VIDEO dùng lại vị trí tay của khung trước
   (tracking) nên nhanh và ổn định hơn chạy từng ảnh rời.
3. **Vẫy tay** (model gốc không có lớp này) – `WaveDetector`: lấy hoành độ tâm lòng bàn tay ở các khung có
   bàn tay xoè (`Open_Palm` hoặc ≥ 4 ngón duỗi); trong 1,5 s gần nhất phải có ≥ 3 nhịp qua lại, mỗi nhịp dài
   ≥ 6 % bề ngang ảnh. Tay đứng yên / rung nhẹ không thành `Wave`.
4. **Ngưỡng tin cậy**: cử chỉ có điểm < `min_score` (0,55) coi như `None`.
5. **Chống nhiễu** – `GestureStabilizer` (bỏ phiếu theo thời gian): nhãn L chỉ được publish khi trong `hold`
   giây gần nhất ≥ 70 % khung là L (`hold` = 0,5 s cho chọn/xác nhận/huỷ, 0,2 s cho `Open_Palm` để dừng nhanh,
   0,15 s cho `Wave`, 0,4 s cho `None`). 1–2 khung nhận nhầm không làm đổi kết quả.
6. **Publish** nhãn ổn định lên `/detected_gesture` (`std_msgs/String`) ở **mỗi khung** (~30 Hz) – vừa là kết
   quả, vừa là “nhịp tim” cho watchdog của node hành vi. Chi tiết từng khung (JSON) ở `/detected_gesture/info`.
7. Camera lỗi / rút webcam: KHÔNG publish (→ robot dừng), thử mở lại mỗi 2 s.

Nguồn ảnh khác (thử nghiệm): `camera_source:=1` (webcam USB), `camera_source:=/dev/video2`,
`camera_source:=~/video.mp4` (phát đúng nhịp thời gian thực), `camera_source:=~/thu_muc_anh` (mỗi ảnh 2 s).

---

## 4. Phần 3 – Node điều khiển hành vi

```bash
ros2 launch tb4_lab04 gesture.launch.py          # cả 2 node (Terminal 1 đang chạy gesture_sim)
```

### 4.1. Máy trạng thái (`gesture_logic.BehaviorStateMachine`)

```
 WAITING --(tin nhắn đầu)--> IDLE <-------------------------------------------+
 SETUP (undock + ra giữa sân) --xong/huỷ--> IDLE                              |
 IDLE/STOPPED --Wave | Pointing_Up | Victory--> SELECTED(hành vi)             |
 SELECTED --Thumb_Up--> EXECUTING --hoàn thành--> IDLE (xoá lựa chọn) --------+
 SELECTED --Closed_Fist / quá 15 s không xác nhận--> IDLE
 EXECUTING --Open_Palm / vật cản / kẹt--> STOPPED (giữ lựa chọn) --Thumb_Up--> EXECUTING (chạy lại từ đầu)
 EXECUTING/STOPPED --Closed_Fist--> IDLE
 mọi trạng thái --không có /detected_gesture > 1 s--> SIGNAL_LOST (dừng) --có tín hiệu lại--> IDLE
```

### 4.2. Yêu cầu của đề → cách đáp ứng

| Yêu cầu | Cách làm |
|---|---|
| Chỉ thực hiện sau cử chỉ xác nhận | `Pointing_Up`/`Victory`/`Wave` chỉ **chọn**; `Thumb_Up` mới chạy. Ngón cái khi chưa chọn → bỏ qua. Chạy xong → xoá lựa chọn (muốn chạy lại phải chọn + xác nhận lại). Lựa chọn hết hạn sau 15 s |
| Không dùng bàn phím | mọi lệnh đi qua `/detected_gesture`; node không đọc bàn phím; undock tự động |
| Tránh nhiễu kích hoạt liên tục | (1) ngưỡng tin cậy 0,55; (2) bỏ phiếu theo thời gian ở node nhận diện; (3) node hành vi **chỉ bắt sườn** (nhãn đổi) – giữ ngón cái 10 s vẫn chỉ 1 lệnh; (4) **cooldown** 1 s cho mỗi cử chỉ; (5) đang chạy thì bỏ qua cử chỉ chọn/xác nhận |
| Dừng khi có tín hiệu dừng | `Open_Palm` (hold chỉ 0,2 s, không cooldown, ưu tiên cao nhất) → gửi `Twist` 0 ngay + 5 lần liên tiếp, huỷ hành vi |
| Dừng khi mất tín hiệu | watchdog: > 1 s không có `/detected_gesture` → dừng, huỷ hành vi (`SIGNAL_LOST`); `Ctrl+C` node hành vi → gửi `Twist` 0 trước khi thoát |
| Khu vực đủ rộng, không va chạm | world `gesture_arena` 9 m × 9 m trống; robot undock rồi chạy 1 m ra giữa sân; mọi hành vi nằm trong bán kính 1,05 m quanh điểm bắt đầu và kết thúc gần đúng chỗ cũ (đối xứng) → cách tường ≥ 2,5 m; thêm lớp an toàn LiDAR: vật cản < 0,40 m theo hướng đang chạy → dừng; robot kẹt (ra lệnh mà odom không đổi 4 s) → dừng |

### 4.3. Hành vi (đo bằng `/odom`, không phải hẹn giờ)

| Hành vi | Chuỗi chuyển động | Thời gian danh định |
|---|---|---|
| `greet` (chào) | quay trái 0,6 rad → phải 1,2 → trái 1,2 → phải 1,2 → trái 0,6 (1 rad/s) – về đúng hướng ban đầu | ~5 s |
| `forward_back` | 4 × (tiến 0,35 m, nghỉ 0,3 s, lùi 0,35 m), 0,2 m/s | ~20 s |
| `circle` | v = 0,15 m/s, ω = 0,3 rad/s (r = 0,5 m) tới khi yaw tích luỹ đủ 360° | ~21 s |

`SegmentRunner` tăng tốc dần (0,5 m/s², 2 rad/s²), giảm tốc gần đích (v ≤ √(2·a·s), có bù trễ đáp ứng 0,15 s)
nên không vọt đích; không có `/odom` thì quy đổi theo thời gian (kém chính xác hơn, có cảnh báo).

---

## 5. Chạy demo và kịch bản quay video

```bash
# Terminal 1
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 gesture_sim.launch.py
# Terminal 2 (khi Gazebo đã lên)
ros2 launch tb4_lab04 gesture.launch.py
# Terminal 3 (tuỳ chọn – cho người xem thấy topic)
ros2 topic echo /detected_gesture
```

Hoặc một lệnh: `ros2 launch tb4_lab04 gesture_demo.launch.py` (node cử chỉ tự bật khi Gazebo sẵn sàng).

**Kịch bản video** (OBS Studio, quay toàn màn hình: Gazebo bên trái, cửa sổ webcam bên phải, terminal nhỏ
phía dưới; **không chạm bàn phím** sau khi chạy lệnh Terminal 2):

1. *Phần 1 (~1 phút)*: Gazebo + robot trong dock; `check_cmd_vel.py` → robot quay, tiến, lùi → `ĐẠT`;
   `webcam_test.py` vài giây.
2. Chạy `gesture.launch.py`, chờ robot tự undock + ra giữa sân (`Robot: IDLE`).
3. Lần lượt **6 cử chỉ** (mỗi cử chỉ giữ ~1 s, hạ tay giữa các cử chỉ):
   - **Vẫy tay** → `SELECTED greet` → **ngón cái** → robot xoay trái–phải.
   - **1 ngón** → `SELECTED forward_back` → **ngón cái** → tiến–lùi 4 lần.
   - **2 ngón** → `SELECTED circle` → **ngón cái** → đi vòng tròn; giữa chừng **xoè tay** → robot dừng ngay
     (`STOPPED`) → **ngón cái** → chạy lại → để chạy hết vòng.
   - **1 ngón** → ngón cái → robot tiến–lùi → **nắm tay** → dừng + về `IDLE`.
   - Chứng minh chống nhiễu: giữ ngón cái lâu khi chưa chọn → robot không chạy (`Chua chon hanh vi`).
   - Chứng minh mất tín hiệu: chọn + xác nhận tiến–lùi rồi **đóng cửa sổ webcam** (hoặc Ctrl+C node nhận diện
     ở terminal khác) → robot dừng sau ~1 s, log `MAT TIN HIEU`.
4. Kết thúc: `ros2 run tb4_lab04 plot_gesture_run.py` → mở ảnh quỹ đạo.

---

## 6. Thử không cần webcam

Kiểm tra node hành vi + Gazebo bằng chuỗi cử chỉ giả (chỉ để kiểm thử – video nộp bài phải dùng webcam):

```bash
ros2 launch tb4_lab04 gesture.launch.py run_recognition:=false
ros2 run tb4_lab04 gesture_sequence.py --ros-args -p preset:=all     # đủ 6 cử chỉ, ~2,5 phút
ros2 run tb4_lab04 gesture_sequence.py --ros-args -p sequence:="Victory:1.5,None:1,Thumb_Up:1.5,None:30"
```

Kiểm tra node nhận diện bằng video quay sẵn: `ros2 run tb4_lab04 gesture_recognition_node.py --ros-args -p camera_source:=~/thu.mp4`.

Unit test (không cần ROS): `python3 test/test_gesture_logic.py`.

---

## 7. Kết quả, log, ảnh quỹ đạo

`robot_behavior_node` ghi `~/tb4_results/gesture_<thời_gian>/`:
- `events.csv` – mọi cử chỉ ổn định, lệnh `start`/`stop`, trạng thái;
- `odom.csv` – quỹ đạo 10 Hz kèm hành vi đang chạy.

```bash
ros2 run tb4_lab04 plot_gesture_run.py           # lần chạy mới nhất -> trajectory.png + bảng sự kiện
```

---

## 8. Nộp bài: GitHub, Google Drive, PDF

**GitHub (Public)** – nên tạo repo mới cho bài này:

```bash
cd ~/workspaces/tb4_gazebo/src/tb4_lab04
git add -A && git commit -m "Bai 6: dieu khien TurtleBot 4 bang cu chi tay (MediaPipe)"
git remote set-url origin https://github.com/<ten-ban>/<repo-moi>.git
git push -u origin main
```

**Google Drive**: upload video → *Share* → *General access: Anyone with the link* (Viewer) → copy link.

**Báo cáo PDF**:

```bash
pip3 install --user reportlab pypdf
nano docs/report_info.yaml                    # link_video, link_github
# chép ảnh chụp màn hình CỦA BẠN vào docs/report/fig_user/ (tên file: xem đầu build_report_bai6.py)
python3 docs/report/diagrams_bai6.py          # vẽ lại sơ đồ (chỉ khi sửa)
python3 docs/report/build_report_bai6.py      # -> docs/report/BaoCao_Bai6_TurtleBot4_Gesture.pdf
```

---

## 9. Xử lý sự cố

| Triệu chứng | Nguyên nhân → cách sửa |
|---|---|
| `Không mở được camera 0` | `ls /dev/video*`; thử `camera_source:=1`; `sudo usermod -aG video $USER` rồi đăng nhập lại; tắt Zoom/Meet/Cheese; máy ảo/WSL2: chuyển webcam vào (mục 0) |
| `Không import được MediaPipe` | chưa chạy `install_gesture_deps.sh`; đang bật conda (`conda deactivate`) |
| `_ARRAY_API not found`, `numpy.core.multiarray failed to import`, node YOLO bài trước chết | NumPy 2 → `pip3 install --user "numpy<2" "opencv-python<4.11" "opencv-contrib-python<4.11"` |
| Cửa sổ không mở, log `Không mở được cửa sổ OpenCV` | có `opencv-python-headless` → `pip3 uninstall -y opencv-python-headless && pip3 install --user --force-reinstall --no-deps "opencv-contrib-python<4.11"` |
| Log `W0000 ... inference_feedback_manager`, `GPU suport is not available ... Unable to initialize EGL`, `Created TensorFlow Lite XNNPACK delegate` | bình thường – MediaPipe chạy bằng CPU (đủ nhanh, ~20–30 FPS trên laptop) |
| `QFontDatabase: Cannot find font directory` | đã tự xử lý trong node; nếu vẫn thấy: `sudo apt install fonts-dejavu-core` (vô hại) |
| Nhận sai / chập chờn | đủ sáng, tay cách webcam 0,4–1 m, lòng bàn tay hướng vào camera, nền không lẫn màu da; xem `conf` trên cửa sổ; tăng `hold_time` (0,7) hoặc `min_score` (0,65) trong `config/gesture.yaml` |
| Vẫy tay không ra `Wave` | FPS trên cửa sổ phải ≥ 10 (FPS thấp thì chuyển động bị lấy mẫu thiếu – node cảnh báo `FPS thấp`); vẫy rộng hơn (≥ 1/6 bề ngang ảnh), ~1–2 lần qua lại/giây; giảm `wave_min_amplitude` 0,04 |
| FPS thấp (< 15) dù máy rảnh | nhiều webcam chỉ đạt 30 FPS ở chế độ MJPG: `camera_fourcc: "MJPG"` trong `config/gesture.yaml`; đủ sáng (thiếu sáng webcam tự giảm FPS) |
| Ra cử chỉ mà robot không làm gì | robot đang `SETUP`/`EXECUTING` (xem dải dưới cửa sổ); chưa chọn trước khi ngón cái; giữ nguyên cử chỉ từ trước (phải đổi cử chỉ / hạ tay); cooldown 1 s |
| Robot dừng giữa chừng, log `MAT TIN HIEU` | node nhận diện tắt/treo, camera lỗi, máy quá tải (FPS < 2) → `max_fps: 15`, đóng bớt ứng dụng |
| Log `VẬT CẢN cách 0.3x m` | có vật/tường gần theo hướng chạy – đúng thiết kế. Đang ở world `maze` (hành lang hẹp) → dùng `gesture_arena` |
| Log `robot không nhúc nhích ... (kẹt / va chạm?)` | robot bị kẹt / Gazebo đứng (`ros2 topic hz /clock`); `software_render:=true` |
| Undock không thành công | `ros2 run tb4_lab04 kill_sim.sh`, chạy lại sim; WSL2/driver lỗi: `software_render:=true` ([chi tiết](docs/LAB04_SLAM_README.md#82-đồ-hoạ--cảm-biến-hay-gặp-nhất-nhất-là-wsl2)) |
| `world gesture_arena` không tìm thấy | chưa build lại sau khi cập nhật repo (`colcon build ...`), hoặc Gazebo Fortress quá cũ (< 6.16 không đọc `GZ_SIM_RESOURCE_PATH`) → `sudo apt upgrade` hoặc dùng `world:=depot` |

---

## 10. Kiến trúc: node, topic, luồng xử lý

```
 Webcam ──> gesture_recognition_node ──/detected_gesture (String, ~30 Hz)──> robot_behavior_node ──/cmd_vel──> Create 3
            OpenCV → MediaPipe → Wave →  <──/robot_behavior/state (JSON)──   state machine → SegmentRunner      (Gazebo)
            ngưỡng → bỏ phiếu                                               watchdog, cooldown, an toàn LiDAR
                                                     /odom, /scan, /dock_status, action /undock  <──────────────┘
```

| Node | File | Vai trò |
|---|---|---|
| `gesture_recognition_node` | `scripts/gesture_recognition_node.py` | webcam → MediaPipe → lọc nhiễu → `/detected_gesture`, cửa sổ hiển thị |
| `robot_behavior_node` | `scripts/robot_behavior_node.py` | cử chỉ → máy trạng thái → `/cmd_vel`; undock; an toàn; ghi kết quả |
| (logic thuần) | `scripts/gesture_logic.py` | WaveDetector, GestureStabilizer, BehaviorStateMachine, SegmentRunner – có unit test |
| Gazebo + TurtleBot 4 | `turtlebot4_ignition_bringup` (qua `gesture_sim.launch.py`) | mô phỏng, `motion_control` nhận `/cmd_vel` |

| Topic / action | Kiểu | Pub → Sub |
|---|---|---|
| `/detected_gesture` | `std_msgs/msg/String` | gesture_recognition_node → robot_behavior_node |
| `/detected_gesture/info` | `std_msgs/msg/String` (JSON) | gesture_recognition_node → (debug) |
| `/robot_behavior/state` | `std_msgs/msg/String` (JSON) | robot_behavior_node → gesture_recognition_node (hiển thị) |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | robot_behavior_node → motion_control (Create 3) |
| `/odom` | `nav_msgs/msg/Odometry` | diffdrive_controller → robot_behavior_node |
| `/scan` | `sensor_msgs/msg/LaserScan` | RPLIDAR (Gazebo) → robot_behavior_node |
| `/dock_status` | `irobot_create_msgs/msg/DockStatus` | Create 3 → robot_behavior_node |
| `/undock` (action) | `irobot_create_msgs/action/Undock` | robot_behavior_node → Create 3 |
| `/gesture/image` | `sensor_msgs/msg/Image` | chỉ khi `publish_image:=true` |

```
tb4_lab04/
├── launch/gesture_sim.launch.py, gesture.launch.py, gesture_demo.launch.py   # Bài 6
├── scripts/gesture_recognition_node.py, robot_behavior_node.py, gesture_logic.py,
│           webcam_test.py, check_cmd_vel.py, gesture_sequence.py, plot_gesture_run.py,
│           install_gesture_deps.sh
├── config/gesture.yaml          # tham số 2 node
├── worlds/gesture_arena.sdf     # sân 9 m x 9 m
├── models/gesture_recognizer.task
├── test/test_gesture_logic.py
├── docs/report/build_report_bai6.py, diagrams_bai6.py
└── (các file của bài 4, 5: SLAM, Nav2, YOLO – xem docs/)
```

---

## 11. Tham số

Đầy đủ, có chú thích: [`config/gesture.yaml`](config/gesture.yaml). Tham số launch của `gesture.launch.py`:
`camera_source`, `show_window`, `mirror`, `wave_requires_confirm`, `auto_undock`, `setup_forward`,
`window_position` (vd `1000,0` – đặt cửa sổ webcam cạnh Gazebo khi quay video),
`run_recognition`, `run_behavior`, `gesture_params_file`. `gesture_sim.launch.py`: `world` (mặc định
`gesture_arena`), `use_rviz` (false), `software_render`, `x y z yaw`, `model`.

`wave_requires_confirm` (mặc định **true**): đề vừa ghi “Vẫy tay → robot xoay trái–phải để chào lại”, vừa yêu
cầu “robot chỉ thực hiện hành vi sau khi nhận được cử chỉ xác nhận”. Mặc định chọn cách thoả cả hai: vẫy tay
**chọn** hành vi chào, ngón cái xác nhận. Muốn robot chào lại ngay khi vẫy:
`ros2 launch tb4_lab04 gesture.launch.py wave_requires_confirm:=false`.

---

## 12. Kiểm thử và giới hạn

Đã kiểm thử trong môi trường ảo (ROS 2 Humble + TurtleBot 4 Simulator + Gazebo Fortress 6.16 headless, MediaPipe
0.10.21/NumPy 1.26 trên Python 3.10 và MediaPipe 1.1/NumPy 2 trên Python 3.12):
- `python3 test/test_gesture_logic.py` – 60 test (lọc nhiễu, vẫy tay, máy trạng thái, kế hoạch chuyển động
  trên robot động học có trễ, an toàn LiDAR, cấu hình);
- MediaPipe trên ảnh tay thật (bộ ảnh mẫu HaGRID): nhận đúng `Closed_Fist, Open_Palm, Pointing_Up, Thumb_Up,
  Thumb_Down, Victory` (độ tin cậy 0,59–0,83) và `Wave` từ ảnh bàn tay xoè dịch qua lại;
- end-to-end: video thử → `gesture_recognition_node` → `robot_behavior_node` → TurtleBot 4 trong Gazebo;
- kiểm thử tích hợp tự động với TurtleBot 4 Simulator (22/22 bước đạt): undock + ra giữa sân 0,999 m; chào
  ±34°, về đúng hướng (lệch 0,0°); tiến–lùi 4 lần về lệch 1 mm (giữ ngón cái thêm 3 s vẫn chỉ chạy 1 lần);
  xoè tay → dừng < 0,6 s, ngón cái → chạy lại; vòng tròn đường kính 1,00 m, khép kín sai 1,1 cm; nắm tay → huỷ;
  ngừng gửi cử chỉ → dừng sau ~1 s; Ctrl+C → gửi Twist 0 rồi thoát;
- xoè tay khi robot mới lùi khỏi dock 0,2 m (còn quay mặt vào dock) rồi xác nhận vòng tròn: robot quay ra xa
  dock, chạy ra giữa sân rồi mới chạy vòng tròn – không lúc nào tiến lại gần dock (8/8 bước);
- nhận diện từ video thử: xử lý đủ 30 FPS (giới hạn `max_fps` không còn bỏ nhầm khung).

Giới hạn (nói thẳng):
- Không kiểm thử được webcam thật trong môi trường ảo – độ chính xác thực tế phụ thuộc ánh sáng, nền, khoảng
  cách; ngưỡng mặc định là điểm khởi đầu, có thể phải chỉnh trong `config/gesture.yaml`.
- `Wave` là luật tự đặt trên landmark (không phải model học máy): vẫy quá chậm/hẹp, hoặc FPS < ~8 (máy quá
  tải), sẽ không nhận – đã gặp khi kiểm thử trên máy ảo 2 nhân chạy cùng Gazebo.
- `Open_Palm` vừa là “dừng” vừa là tư thế đầu của “vẫy tay” → vẫy khi robot đang chạy sẽ dừng robot (an toàn
  được ưu tiên hơn tiện lợi).
- Hành vi chạy vòng hở theo `/odom` (không có bản đồ / Nav2): odometry trôi theo thời gian; lớp an toàn LiDAR
  chỉ xét quạt ±34° theo hướng chạy, không xét khi quay tại chỗ.
- Mô phỏng chậm (real-time factor < 1) làm hành vi kéo dài theo thời gian thực, nhưng quãng đường / góc vẫn
  đúng vì đo bằng odom; mọi giới hạn thời gian của chuyển động (tăng/giảm tốc, phát hiện kẹt, undock) tính theo
  **giờ mô phỏng** (stamp của `/odom`) nên máy yếu không bị báo "quá thời gian" oan (đã thử ở real-time factor
  0,05–0,07). Watchdog cử chỉ thì tính theo giờ thực.

Tài liệu tham khảo: [MediaPipe Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) ·
[OpenCV](https://docs.opencv.org/) · [TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/) ·
[HaGRID dataset](https://github.com/hukenovs/hagrid) (ảnh mẫu dùng khi kiểm thử).
