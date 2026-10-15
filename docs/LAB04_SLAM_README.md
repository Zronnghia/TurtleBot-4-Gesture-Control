> **Tài liệu của bài tuần trước** (mô phỏng, SLAM Toolbox, lưu bản đồ). Bài hiện tại (Localization + Navigation tự động + YOLO) xem [`README.md`](../README.md). Các lệnh dưới đây vẫn dùng được; đường dẫn tương đối (`docs/...`, `HUONG_DAN_NHANH.md`) tính từ thư mục gốc repo. Lưu ý: `navigation.launch.py` nay mặc định thêm vật thể vào world (`spawn_objects:=false` để có world trống như tuần trước).

# Bài thực hành 04 – TurtleBot 4 Simulation: SLAM Toolbox + Nav2 (ROS 2 Humble)

Mô phỏng TurtleBot 4 trong **Ignition Gazebo Fortress**, xây dựng bản đồ bằng **SLAM Toolbox**,
lưu bản đồ, định vị lại bằng **AMCL** và điều hướng tự động bằng **Nav2**, quan sát toàn bộ trên **RViz2**.

Repo **không viết lại** simulator hay controller: mọi thứ dùng launch/cấu hình chính thức của TurtleBot 4
(`turtlebot4_ignition_bringup`, `turtlebot4_navigation`). Phần của repo là các launch file ghép các bước
theo đúng thứ tự, cấu hình (SLAM / AMCL / Nav2 / RViz) và các script kiểm tra để có **bằng chứng định
lượng** cho từng phần của bài.

| Phần | Lệnh chính | Kiểm tra |
|---|---|---|
| 0 – Môi trường | `ros2 run tb4_lab04 doctor.sh` | không còn dòng `[FAIL]` |
| 1 – Simulation | `ros2 launch tb4_lab04 sim.launch.py` | `check_sensors.py`, `check_sim.py` |
| 2 – SLAM | `ros2 launch tb4_lab04 mapping.launch.py` + teleop | `save_map.sh`, `check_map.py` |
| 3 – Localization | `ros2 launch tb4_lab04 navigation.launch.py use_nav2:=false` | `compare_pose.py` |
| 4 – Nav2 | `ros2 launch tb4_lab04 navigation.launch.py` + Nav2 Goal | `nav_monitor.py` |
| Khi gặp lỗi | `ros2 run tb4_lab04 collect_debug.sh` | gửi file `~/tb4_debug_*.txt` |

Chỉ cần danh sách lệnh: xem [`HUONG_DAN_NHANH.md`](../HUONG_DAN_NHANH.md).

---

## Mục lục

0. [Đọc trước – 7 điều hay làm hỏng bài](#0-đọc-trước--7-điều-hay-làm-hỏng-bài)
1. [Cài đặt (làm một lần)](#1-cài-đặt-làm-một-lần)
2. [Phần 1 – TurtleBot 4 Simulation](#2-phần-1--turtlebot-4-simulation)
3. [Phần 2 – Xây dựng bản đồ bằng SLAM Toolbox](#3-phần-2--xây-dựng-bản-đồ-bằng-slam-toolbox)
4. [Phần 3 – Localization](#4-phần-3--localization)
5. [Phần 4 – Navigation với Nav2](#5-phần-4--navigation-với-nav2)
6. [Kịch bản quay video demo](#6-kịch-bản-quay-video-demo)
7. [Nộp bài](#7-nộp-bài)
8. [Xử lý sự cố](#8-xử-lý-sự-cố)
9. [Cấu trúc repo và pipeline](#9-cấu-trúc-repo-và-pipeline)
10. [Tham số launch](#10-tham-số-launch)

---

## 0. Đọc trước – 7 điều hay làm hỏng bài

1. **Chỉ dùng Ubuntu 22.04 + ROS 2 Humble + Gazebo Fortress.** TurtleBot 4 bản Humble không chạy với
   Gazebo Classic hay Gazebo Harmonic. Ubuntu 24.04 / ROS 2 Jazzy là bộ khác – lệnh trong README này không áp dụng.
2. **Terminal "sạch".** Mỗi terminal chỉ được `source` ROS 2 Humble và workspace của bài này. Nếu `~/.bashrc`
   đang `source` một workspace khác (ví dụ workspace UR, workspace tự build `ros_gz`…), gói của workspace đó
   có thể **ghi đè** gói hệ thống và gây lỗi rất khó hiểu. `doctor.sh` phát hiện chuyện này.
3. **Chỉ chạy một phiên mô phỏng một lúc.** Trước mỗi lần chạy lại: `Ctrl+C` rồi
   `ros2 run tb4_lab04 kill_sim.sh`. Gazebo cũ còn sót = 2 đồng hồ `/clock`, robot "nhảy", AMCL không hội tụ.
4. **Robot luôn khởi động khi đang đỗ trong dock (đế sạc), mặt quay VÀO dock.** Phải **undock** trước khi lái.
   Undock đúng = `SUCCEEDED`, robot lùi ~0.4 m rồi quay 180°.
5. **LiDAR và cảm biến cliff của mô phỏng đo bằng GPU (render đồ hoạ).** Driver đồ hoạ lỗi (hay gặp trên WSL2)
   thì topic vẫn chạy nhưng số đo sai → SLAM không vẽ được, undock bị huỷ. Luôn chạy `check_sensors.py` ở
   Phần 1; nếu FAIL thì thêm `software_render:=true` vào **mọi** lệnh launch (mục 8.2).
6. **Bản đồ do bạn tạo.** Repo không kèm sẵn `maps/map.yaml` + `map.pgm` – bạn tạo ở Phần 2 (đề bắt buộc quay
   video quá trình này). Phần 3, 4 không chạy được nếu chưa có bản đồ.
7. **World và vị trí spawn phải giống nhau ở Phần 2, 3, 4** (mặc định `world:=maze`, x = y = yaw = 0).
   Đổi world thì thêm `world:=...` vào **mọi** lệnh launch.

> **Log đỏ/vàng không có nghĩa là hỏng.** Mô phỏng TurtleBot 4 in rất nhiều cảnh báo bình thường (danh sách
> ở mục 8.1). Hãy đánh giá bằng các script kiểm tra, không phải bằng số dòng màu đỏ.

---

## 1. Cài đặt (làm một lần)

Yêu cầu máy: CPU ≥ 4 nhân, RAM ≥ 8 GB, nên có GPU. Máy yếu vẫn chạy được nhưng mô phỏng chậm
(real-time factor thấp).

### 1.1. Chọn nền tảng

| | Ubuntu 22.04 cài trực tiếp (khuyến nghị) | WSL2 + Ubuntu 22.04 trên Windows |
|---|---|---|
| Hiệu năng Gazebo | tốt nhất | chậm hơn; GPU qua lớp D3D12 |
| Rủi ro đồ hoạ | thấp (cài driver GPU chuẩn) | cao hơn: Gazebo có thể crash/đen, LiDAR đo sai → dùng `software_render:=true` |
| Yêu cầu | – | Windows 11, hoặc Windows 10 bản 22H2 trở lên (có WSLg) |

Nếu cài Ubuntu trực tiếp: dùng bản **Ubuntu 22.04 Desktop**, cài driver GPU (Software & Updates →
Additional Drivers), rồi sang mục 1.3.

### 1.2. (Chỉ WSL2) Cài Ubuntu 22.04 trên Windows

Trong **PowerShell (Run as Administrator)**:

```powershell
wsl --install -d Ubuntu-22.04
wsl --update
wsl --version          # phải thấy "WSLg version" – đó là phần hiển thị cửa sổ Linux
```

Khởi động lại máy nếu được yêu cầu, mở "Ubuntu 22.04" từ Start menu và tạo user.

Tăng RAM cho WSL2 (mặc định chỉ ~50 % RAM máy): tạo file `%UserProfile%\.wslconfig` với nội dung

```ini
[wsl2]
memory=8GB
processors=4
swap=8GB
```

rồi chạy `wsl --shutdown` trong PowerShell và mở lại Ubuntu.

Driver GPU: chỉ cần cài **driver mới nhất cho Windows** (NVIDIA/AMD/Intel). **Không** cài driver NVIDIA
bên trong Ubuntu WSL.

Kiểm tra hiển thị + GPU trong Ubuntu WSL:

```bash
sudo apt update && sudo apt install -y mesa-utils x11-apps
xeyes                               # phải hiện cửa sổ đôi mắt -> WSLg hoạt động (Ctrl+C để tắt)
glxinfo -B | grep "OpenGL renderer" # "D3D12 (...)" = dùng GPU ; "llvmpipe" = render bằng CPU
```

### 1.3. Cài ROS 2 Humble Desktop

Theo hướng dẫn chính thức (docs.ros.org → Humble → Installation → Ubuntu deb packages):

```bash
# Locale UTF-8
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Kho Universe + kho ROS 2 (gói ros2-apt-source tự quản lý khoá GPG)
sudo apt install -y software-properties-common curl
sudo add-apt-repository -y universe
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb

# Cài ROS 2 Humble Desktop + công cụ build
sudo apt update && sudo apt upgrade -y
sudo apt install -y ros-humble-desktop ros-dev-tools
```

> Máy đã cài ROS từ trước mà `sudo apt update` báo lỗi khoá (`EXPKEYSIG` / `NO_PUBKEY`): khoá cũ của
> packages.ros.org đã hết hạn năm 2025. Xoá cấu hình cũ rồi chạy lại đoạn "Kho Universe + kho ROS 2" ở trên:
> `sudo rm -f /etc/apt/sources.list.d/ros2.list /usr/share/keyrings/ros-archive-keyring.gpg`

Kiểm tra nhanh:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker      # thấy "Publishing: Hello World" -> Ctrl+C
```

### 1.4. Cài Gazebo Fortress, TurtleBot 4 Simulator, SLAM Toolbox, Nav2

```bash
# Kho Gazebo của OSRF (nguồn của Ignition Fortress – theo TurtleBot 4 User Manual)
sudo apt install -y lsb-release gnupg
sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt update
sudo apt install -y ignition-fortress

# TurtleBot 4 (mô phỏng + RViz) , SLAM Toolbox, Nav2, teleop và công cụ phụ
sudo apt install -y \
  ros-humble-turtlebot4-simulator ros-humble-irobot-create-nodes \
  ros-humble-turtlebot4-desktop ros-humble-turtlebot4-navigation \
  ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-teleop-twist-keyboard ros-humble-topic-tools \
  mesa-utils git

ign gazebo --versions               # phải in ra 6.x.x (Fortress)
```

`ros-humble-topic-tools` là **bắt buộc** (Phần 3–4 dùng nó để tạo `/scan_nav`, xem mục 9.3).

### 1.5. Tạo workspace và build package

```bash
mkdir -p ~/workspaces/tb4_gazebo/src
# Cách A – từ file nén:
tar -xzf ~/Downloads/tb4_lab04.tar.gz -C ~/workspaces/tb4_gazebo/src
# Cách B – từ GitHub (sau khi đã push, mục 7):
# git clone https://github.com/<ten-ban>/tb4_lab04.git ~/workspaces/tb4_gazebo/src/tb4_lab04

cd ~/workspaces/tb4_gazebo
source /opt/ros/humble/setup.bash
sudo rosdep init 2>/dev/null; rosdep update
rosdep install --from-paths src --ignore-src -y
colcon build
source install/setup.bash
```

> Workspace của bạn có thể nằm chỗ khác (ví dụ `~/workspaces/tb4_gazebo`) – khi đó thay `~/workspaces/tb4_gazebo` bằng
> đường dẫn của bạn ở **mọi** lệnh. Sau khi sửa file trong repo (launch, config, script) phải `colcon build`
> lại. Bản đồ thì **không** cần build lại (launch tự đọc từ thư mục source).

**Đã có bản cũ của dự án và muốn thay bằng bản này** (giữ lại bản đồ đã tạo):

```bash
# Ctrl+C mọi terminal đang chạy mô phỏng trước
cd ~/workspaces/tb4_gazebo/src
rm -rf /tmp/tb4_maps_backup && cp -a tb4_lab04/maps /tmp/tb4_maps_backup   # giữ bản đồ
mv tb4_lab04 ~/tb4_lab04_old_$(date +%Y%m%d_%H%M%S)        # cất bản cũ (xoá sau nếu muốn)
tar -xzf ~/Downloads/tb4_lab04.tar.gz -C ~/workspaces/tb4_gazebo/src
cp -a /tmp/tb4_maps_backup/. tb4_lab04/maps/
cd ~/workspaces/tb4_gazebo && rm -rf build/tb4_lab04 install/tb4_lab04
source /opt/ros/humble/setup.bash && colcon build && source install/setup.bash
```

Thay cả thư mục (không chép đè từng file) để không sót file cũ mâu thuẫn với bản mới.

### 1.6. Thiết lập terminal

Thêm vào cuối `~/.bashrc` để mọi terminal mới đều sẵn sàng:

```bash
echo 'source /opt/ros/humble/setup.bash'   >> ~/.bashrc
echo 'source ~/workspaces/tb4_gazebo/install/setup.bash'  >> ~/.bashrc
echo 'export ROS_LOCALHOST_ONLY=1'         >> ~/.bashrc
source ~/.bashrc
ros2 daemon stop
```

- `ROS_LOCALHOST_ONLY=1`: trong phòng lab nhiều máy cùng mạng chạy TurtleBot 4 với cùng domain → các máy
  "thấy" robot của nhau (robot tự chạy, TF loạn). Biến này giới hạn ROS 2 trong máy của bạn.
  **Mọi terminal phải cùng giá trị** – lệch là các node không thấy nhau.
- Mở `~/.bashrc` (`nano ~/.bashrc`) xem có dòng `source` workspace khác không; có thì thêm `#` vào đầu dòng.
- Không đặt `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` cùng `ROS_LOCALHOST_ONLY=1` (lỗi trên Humble).
  Cứ để mặc định (FastDDS).

### 1.7. Kiểm tra môi trường

```bash
ros2 run tb4_lab04 doctor.sh
```

Phải kết thúc bằng `Kết luận: không có lỗi chặn`. Mỗi `[FAIL]` có kèm lệnh sửa ngay bên dưới.
`[WARN]` là khuyến nghị (máy yếu, render bằng CPU, …) – vẫn chạy được.

---

## 2. Phần 1 – TurtleBot 4 Simulation

### 2.1. Khởi chạy

**Terminal 1:**

```bash
ros2 run tb4_lab04 kill_sim.sh        # dọn phiên cũ (nếu có)
ros2 launch tb4_lab04 sim.launch.py
```

Lần đầu mất 1–3 phút. Kết quả mong đợi:

- Cửa sổ **Gazebo**: world `maze`, robot đang nằm trong dock. Mô phỏng tự chạy; nếu thấy nút ▶ ở góc dưới
  trái thì bấm nó. Con số % ở góc dưới phải là real-time factor (RTF).
- Cửa sổ **RViz2** (Fixed Frame `odom`): mô hình robot + các chấm LiDAR quanh robot.

Tuỳ chọn: `world:=depot|warehouse` (cần Internet lần đầu để tải model), `use_rviz:=false`,
`software_render:=true` (xem mục 8.2).

### 2.2. Kiểm tra tự động (dùng làm bằng chứng)

**Terminal 2** – kiểm tra số đo cảm biến có hợp lý (chạy khi robot còn trong dock):

```bash
ros2 run tb4_lab04 check_sensors.py
```

Mong đợi: `KẾT LUẬN: số đo LiDAR và cliff hợp lý.` Nếu FAIL → mục 8.2 trước khi làm tiếp.

Sau đó kiểm tra topic + lái thử:

```bash
ros2 run tb4_lab04 check_sim.py
```

Script đo `/scan`, `/odom`, TF, kiểm tra `/cmd_vel` có node nhận, **tự undock**, lái tiến ~0.3 m (chỉ khi
phía trước trống) và quay tại chỗ ~1.8 rad, đo lại bằng `/odom`. Mong đợi:

```
=================== KẾT QUẢ KIỂM TRA ===================
  [PASS] /scan                      frame=turtlebot4/rplidar_link/rplidar | 640 tia ...
  [PASS] /scan: số đo hợp lý        min/trung vị/max = ...
  [PASS] /odom                      frame=odom -> base_link | ...
  [PASS] TF odom->base_link         OK
  [PASS] TF base_link->turtlebot4/rplidar_link/rplidar ...
  [PASS] /cmd_vel có subscriber     1 subscriber
  [PASS] Undock                     status=SUCCEEDED, is_docked=False, robot đã lùi 0.3x m ...
  [PASS] cmd_vel: tiến thẳng        quãng đường đo từ /odom = 0.3xx m (kỳ vọng ~0.3 m)
  [PASS] cmd_vel: quay tại chỗ      góc quay đo từ /odom = 1.8x rad (kỳ vọng ~1.8 rad)
TẤT CẢ ĐỀU ĐẠT.
```

Tần số được đánh giá theo **giờ mô phỏng** nên máy chậm không bị FAIL oan; script in thêm RTF ước lượng.
Chỉ kiểm tra topic, không lái: `check_sim.py --no-drive`.

### 2.3. Kiểm tra thủ công (nên quay vào video)

```bash
ros2 topic list | grep -E "^/(scan|odom|cmd_vel|tf|clock)$"
ros2 topic info /scan            # Type: sensor_msgs/msg/LaserScan
ros2 topic hz /scan              # Ctrl+C để dừng
ros2 topic echo /odom --once     # nav_msgs/msg/Odometry: frame odom -> base_link
ros2 topic info /cmd_vel -v      # có Subscription của node "motion_control"
```

Robot nhận lệnh vận tốc (robot phải **đã undock** – `check_sim.py` đã làm, hoặc dùng lệnh ở 2.4):

```bash
ros2 topic pub --rate 10 /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.5}}"
# robot quay tại chỗ; Ctrl+C -> robot tự dừng sau ~0.5 s (Create 3 có timeout cho /cmd_vel)
```

### 2.4. Undock bằng tay

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock "{}"
```

`SUCCEEDED` + robot lùi ra rồi quay 180° là đúng. `CANCELED` (dù `is_docked: false`) nghĩa là phản xạ an
toàn của Create 3 cắt ngang – xem mục 8.2. Các launch của repo mặc định `cliff_reflex:=false` (tắt riêng
phản xạ chống rơi – world phẳng, không có chỗ hụt) để cảm biến cliff đo sai không huỷ undock; phản xạ
bumper vẫn bật.

### 2.5. Thấy gì trên RViz2 (`rviz/sim.rviz`)

- Fixed Frame `odom` (Phần 1 chưa có frame `map` – các display Map/Nav2 tắt sẵn).
- **RobotModel**: mô hình TurtleBot 4. **LaserScan** `/scan`: chấm trắng = tường/vật cản quanh robot.
- **TF**: cây frame `odom → base_link → …` (bỏ tick nếu rối mắt).

Dừng: `Ctrl+C` ở Terminal 1, rồi **luôn** `ros2 run tb4_lab04 kill_sim.sh`.

---

## 3. Phần 2 – Xây dựng bản đồ bằng SLAM Toolbox

### 3.1. Khởi chạy

**Terminal 1:**

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 mapping.launch.py
```

Launch **chờ tới khi mô phỏng thật sự chạy** (log `[tb4_lab04_wait_for_sim]: Mô phỏng đã chạy ...`: có
`/clock` và `/odom`), thêm 2 s rồi mới in `[tb4_lab04] Khởi động SLAM Toolbox ...`. Trên RViz2 (Fixed Frame
`map`) bản đồ xám/đen/trắng bắt đầu hiện quanh robot.

Tuỳ chọn: `sync:=false` (SLAM bất đồng bộ – nhẹ hơn cho máy yếu, bản đồ có thể kém hơn).

### 3.2. Undock và mở teleop

**Terminal 2:**

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock "{}"
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.2 -p turn:=0.5
```

Phím (terminal teleop phải đang được chọn): `i` tiến, `j`/`l` quay trái/phải tại chỗ, `u`/`o` vừa tiến vừa
rẽ, `k` dừng. Thả phím ~0.5 s là robot tự dừng.
**Hạn chế lùi (`,`)**: lùi được (repo đặt `safety_override: backup_only` cho Create 3 – mặc định chỉ cho lùi
~0.15 m), nhưng phía sau robot không có cảm biến nên dễ va; muốn đổi hướng thì quay tại chỗ bằng `j`/`l`.

### 3.3. Cách lái để bản đồ đạt yêu cầu (không nhân đôi tường, không lệch)

1. **Chậm**: tiến ≤ 0.2 m/s, quay ≤ 0.5 rad/s. Tường bị nhân đôi gần như luôn do **quay nhanh**.
2. Đi dọc hành lang, cách tường ~0.5–1 m; đi hết các nhánh, vòng quanh các khối vật cản.
3. **Khép vòng (loop closure)**: định kỳ quay lại khu đã đi (nhất là gần điểm xuất phát) để SLAM Toolbox nối
   vòng và kéo thẳng sai số tích luỹ.
4. Theo dõi RViz2: xám = chưa biết. Lái tới khi phần lớn khu vực đi được đã trắng, tường thành nét đen liền.
5. Thấy tường lệch/nhân đôi rõ: dừng, quay chậm tại chỗ vài giây; vẫn hỏng thì làm lại từ đầu
   (`Ctrl+C`, `kill_sim.sh`, launch lại) – nhanh hơn cố sửa.

### 3.4. Lưu bản đồ (khi `mapping.launch.py` **vẫn đang chạy**)

**Terminal 3:**

```bash
ros2 run tb4_lab04 save_map.sh
```

Kết quả: `~/workspaces/tb4_gazebo/src/tb4_lab04/maps/map.yaml` + `map.pgm`, kèm thống kê (độ phân giải, % ô
trống/vật cản/chưa biết, diện tích đã khám phá). Bản đồ cũ (nếu có) được chuyển vào `maps/backup_<thời_gian>/`;
lưu thất bại thì bản cũ giữ nguyên. Xem ảnh: `eog ~/workspaces/tb4_gazebo/src/tb4_lab04/maps/map.pgm`.
Kiểm tra lại bất kỳ lúc nào: `ros2 run tb4_lab04 check_map.py`.

> `save_map.sh` gọi `nav2_map_server map_saver_cli` với `--free 0.15`: mặc định 0.25 của Nav2 làm ô
> "chưa biết" (xám 205) bị đọc thành ô **trống** khi load lại → Nav2 có thể lập đường đi xuyên vùng chưa khảo sát.

(Tuỳ chọn) Xoá "vệt trắng" do tia LiDAR lọt qua khe tường vào trong khối tường:
`ros2 run tb4_lab04 clean_map.py --dry-run` (xem trước) rồi `clean_map.py` (bản gốc được sao lưu).
Đây là bước hậu xử lý – nếu dùng, ghi rõ trong báo cáo.

### 3.5. Kết thúc

`Ctrl+C` ở Terminal 2 và 1, rồi `ros2 run tb4_lab04 kill_sim.sh`.

### 3.6. (Tuỳ chọn) Tự khám phá + tự lưu bản đồ – `explore.launch.py`

> Đề yêu cầu Phần 2 lái bằng **teleop** – muốn nộp video tự khám phá hãy hỏi giảng viên trước.

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 explore.launch.py        # xong: in "KẾT QUẢ TỰ KHÁM PHÁ", tự lưu maps/map.yaml + map.pgm
ros2 run tb4_lab04 clean_map.py                # (tuỳ chọn) làm đẹp bản đồ
ros2 run tb4_lab04 check_map.py
```

Cách hoạt động (`scripts/auto_explore.py`, frontier exploration): tìm biên giữa vùng đã biết và chưa biết,
chọn **chỗ đứng cách tường ≥ 0.4 m mà LiDAR nhìn thẳng được tới biên đó** (trong 1.5 m) – nên quét được cả các
góc mê cung mà không phải chui sát vào góc (nơi Nav2 hay kẹt); gửi goal cho Nav2; goal thất bại thì **tự gỡ
kẹt** (lùi ra, quay về hướng thoáng nhất theo LiDAR, tiến ra) rồi chọn chỗ khác; hết biên thì về điểm xuất
phát và lưu. Đứng tới nơi mà LiDAR không quét thêm được đoạn biên (góc tường che, nhìn xiên vào hốc) thì lần
sau **chọn chỗ đứng khác** cho chính đoạn biên đó (cách chỗ cũ ≥ 0.6 m, thường là vòng sang phía khác), tối đa 3 chỗ
rồi mới bỏ. Trước khi kết luận "hết", quét lại 1 lượt các đoạn biên đã bỏ qua. Bảng `KẾT QUẢ TỰ KHÁM PHÁ` liệt kê
**toạ độ các đoạn biên còn sót** (`Biên chưa quét`) để lái teleop tới nếu cần.

> Vùng xám **bên trong** đường viền một khối tường/hộp là bình thường: LiDAR không thể nhìn vào trong vật đặc.
> Chỉ phần xám **lòi ra ngoài** đường viền (hình tam giác, hốc giữa 2 đoạn tường) mới là chỗ chưa quét.
Cứ 300 s mô phỏng tự lưu bản dự phòng vào `maps/autosave/`.

> Vì sao không cho quay nhanh hơn 1.0 rad/s? SLAM Toolbox chỉ xử lý 1 scan mỗi ≥ 0.25 s và chỉ dò góc lệch
> trong ±0.349 rad giữa 2 scan; quay 1.5 rad/s (0.375 rad/scan) vượt vùng dò → khớp scan sai → tường dày,
> lốm đốm, lệch. Muốn bản đồ đẹp nhất: tốc độ thấp hơn nữa, hoặc lái teleop chậm (mục 3.3).

Tốc độ: launch này dùng `config/nav2_explore.yaml` (tới 0.40 m/s, quay tối đa 1.0 rad/s, không xoay đúng hướng ở mỗi
goal, vùng đệm tường 0.35 m) và đặt `safety_override: full` cho Create 3 (giới hạn 0.46 m/s thay vì 0.306 m/s).
`fast:=false` để giữ giới hạn mặc định của Create 3. Tốc độ **nhìn thấy** còn nhân với RTF của Gazebo
(con số % góc dưới phải) – máy chậm thì robot vẫn chậm theo giờ thật.

Nếu robot kẹt thật (tự gỡ 3 lần liên tiếp không nhúc nhích), node dừng và **lưu bản đồ đang có**. Muốn
khám phá tiếp trên cùng bản đồ: để launch chạy, lái teleop ra chỗ thoáng, rồi ở terminal khác
`ros2 run tb4_lab04 auto_explore.py` (bản đồ SLAM vẫn giữ, xong lại tự lưu).

Tham số hay dùng: `max_duration:=1200` (giây mô phỏng), `fast:=false`, `return_home:=false`,
`software_render:=true`. Dừng sớm mà vẫn giữ bản đồ: `ros2 run tb4_lab04 save_map.sh` ở terminal khác **trước**
khi Ctrl+C (Ctrl+C tắt luôn SLAM Toolbox nên lúc đó không lưu được nữa; bản tự lưu gần nhất nằm ở
`maps/autosave/`).

---

## 4. Phần 3 – Localization

Yêu cầu đề: dừng SLAM, khởi động lại robot trong cùng môi trường, load bản đồ vừa tạo, chạy localization.

### 4.1. Khởi chạy (chỉ localization)

**Terminal 1:**

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 navigation.launch.py use_nav2:=false
```

- Launch tự tìm `maps/map.yaml` của repo (in `[tb4_lab04] Dùng bản đồ: ...`). File khác:
  `map:=/duong/dan/tuyet/doi/map.yaml`. Chưa có/hỏng bản đồ → dừng ngay với thông báo `LỖI BẢN ĐỒ`.
- Khi mô phỏng đã chạy: `map_server` load bản đồ, `amcl` khởi động và **tự đặt initial pose (0, 0, 0)** –
  đúng chỗ robot spawn, vì frame `map` của SLAM Toolbox trùng vị trí robot lúc bắt đầu mapping.

Trên RViz2 phải thấy: bản đồ đã lưu; robot nằm ở chỗ dock; đám mũi tên xanh (**Amcl Particle Swarm**) tụ
quanh robot; **chấm LiDAR trùng khít tường đen của bản đồ**.

Nếu chấm LiDAR lệch khỏi tường (ví dụ bạn spawn khác chỗ): bấm **2D Pose Estimate** trên RViz2, click vào
vị trí thật của robot và kéo theo hướng robot đang nhìn.

### 4.2. Đối chiếu với vị trí thật trong Gazebo

**Terminal 2:** undock rồi lái thử một đoạn (teleop như 3.2) để AMCL hội tụ, đồng thời ở **Terminal 3**:

```bash
ros2 run tb4_lab04 compare_pose.py          # Ctrl+C để xem tổng kết
```

Script so pose AMCL (TF `map → base_link`) với pose thật của Gazebo (`/sim_ground_truth_pose`) và in sai số;
tổng kết `ĐẠT` khi sai số vị trí trung bình ≤ 0.25 m. Nên quay vào video.

---

## 5. Phần 4 – Navigation với Nav2

### 5.1. Khởi chạy

**Terminal 1:**

```bash
ros2 run tb4_lab04 kill_sim.sh
ros2 launch tb4_lab04 navigation.launch.py
```

Như Phần 3, thêm Nav2 sau localization ~8 s. Panel **Navigation 2** trên RViz2 chuyển sang
`Navigation: active`, `Localization: active`.

### 5.2. Undock trước khi đặt goal

**Terminal 2:**

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock "{}"
```

(Dock thấp hơn mặt quét LiDAR nên không có trên bản đồ; repo tự đánh dấu dock là vật cản trong costmap –
`dock_obstacle.py` – để Nav2 không lập đường đi xuyên qua dock.)

### 5.3. Theo dõi kết quả (bằng chứng)

**Terminal 3:**

```bash
ros2 run tb4_lab04 nav_monitor.py
```

Script **không điều khiển robot**, chỉ ghi lại từng goal (kết quả, thời gian, số lần recovery), báo va chạm
(bumper) và cảnh báo nếu có teleop đang publish `/cmd_vel` trong lúc chạy goal. `Ctrl+C` để in tổng kết
(`ĐẠT` khi ≥ 3 goal thành công, không va chạm).

### 5.4. Đặt goal trên RViz2

1. **Tắt teleop** (đề yêu cầu không điều khiển tay sau khi đặt goal).
2. Bấm **Nav2 Goal** trên thanh công cụ RViz2 → click vào ô **trắng** (vùng trống đã biết) → giữ chuột và
   kéo để chọn hướng đến → thả.
3. Robot tự lập đường (đường xanh – global plan), bám đường (local plan) và tránh vật cản. Chờ tới khi
   `nav_monitor.py` in `SUCCEEDED`.
4. Lặp lại cho **ít nhất 3 goal ở các khu vực khác nhau** (ví dụ 3 nhánh hành lang khác nhau, cách nhau vài mét).

Mẹo: chọn goal cách tường ≥ 0.5 m; không đặt goal vào vùng xám (chưa biết) hoặc trong vùng tô màu quanh
tường (inflation); đặt goal tiếp theo khi goal trước đã xong.

---

## 6. Kịch bản quay video demo

Quay toàn màn hình bằng **OBS Studio** (Ubuntu: `sudo apt install obs-studio`; WSL2: cài OBS cho Windows và quay
màn hình Windows – các cửa sổ Gazebo/RViz2 của WSLg hiện như cửa sổ Windows bình thường).

1. **Phần 1 (~1 phút)**: `sim.launch.py`, Gazebo + RViz2; `check_sensors.py`, `check_sim.py` → `TẤT CẢ ĐỀU ĐẠT`;
   `ros2 topic hz /scan`, `ros2 topic echo /odom --once`, `ros2 topic pub /cmd_vel ...` thấy robot quay.
2. **Phần 2 (tua nhanh được)**: `mapping.launch.py`, undock, teleop; RViz2 thấy bản đồ lớn dần; bản đồ hoàn chỉnh;
   `save_map.sh` + mở `map.pgm`.
3. **Phần 3**: `Ctrl+C`, `kill_sim.sh`, `navigation.launch.py use_nav2:=false`; bản đồ được load lại, particle
   tụ quanh robot, LiDAR khớp tường; `compare_pose.py` → `ĐẠT`; so sánh vị trí robot Gazebo ↔ RViz2.
4. **Phần 4**: `navigation.launch.py`, undock, `nav_monitor.py`; **3 goal** ở 3 khu vực, không chạm bàn phím
   lái; tổng kết `nav_monitor.py` → `ĐẠT`.

---

## 7. Nộp bài

### 7.1. GitHub (Public)

```bash
cd ~/workspaces/tb4_gazebo/src/tb4_lab04
git init -b main                      # bỏ qua nếu đã là repo git
git add .
git status                            # PHẢI thấy maps/map.yaml và maps/map.pgm
git commit -m "Lab04: TurtleBot 4 SLAM Toolbox + Nav2"
git remote add origin https://github.com/<ten-ban>/tb4_lab04.git
git push -u origin main
```

Repo chứa: source code (`scripts/`), launch file (`launch/`), `maps/map.yaml`, `maps/map.pgm`, cấu hình
(`config/`, `rviz/`), README này. `.gitignore` đã loại `build/ install/ log/` và các bản sao lưu bản đồ.
GitHub yêu cầu Personal Access Token thay cho mật khẩu khi push qua HTTPS.

### 7.2. Video

Upload Google Drive → Share → General access: **Anyone with the link** (Viewer) → copy link.

### 7.3. Báo cáo PDF

Báo cáo bài tuần trước đã nộp riêng. Báo cáo bài này dựng bằng `docs/report/build_report.py` (xem README).

---

## 8. Xử lý sự cố

Nguyên tắc: **sửa lỗi ĐẦU TIÊN** trong log (các lỗi sau thường là hệ quả). Không tự xử lý được →
`ros2 run tb4_lab04 collect_debug.sh` (tốt nhất khi launch vẫn đang mở) và gửi file `~/tb4_debug_*.txt`
cùng ảnh chụp Gazebo/RViz2 cho người hỗ trợ.

### 8.1. Log trông như lỗi nhưng BÌNH THƯỜNG

| Log | Vì sao không sao |
|---|---|
| `[ERROR] ... process has died ... exit code -2` / `-15` **sau khi bấm Ctrl+C** | Ctrl+C gửi tín hiệu dừng 2 lần (terminal + launch); một số node C++ báo vậy khi tắt |
| `ign_args is deprecated, migrate to gz_args!` | cảnh báo của launch chính thức |
| `Service oakd/stop_camera unavailable`, `Service stop_motor unavailable` | mô phỏng không có camera/motor LiDAR thật |
| RViz2: `GLSL link result : active samplers with a different type refer to the same texture image unit` (`indexed_8bit_image`) | lỗi shader đã biết của RViz2 Humble với driver Mesa (Intel/AMD/WSL2/llvmpipe); bản đồ vẫn hiển thị. Chỉ cần xử lý nếu ô Map trên RViz2 trống |
| `Desired controller update period (0.001 s) is faster than the gazebo simulation period` | cấu hình chính thức của Create 3 |
| `kdl_parser ... The root link ... has an inertia specified` | cảnh báo URDF chính thức |
| `minimum laser range setting (0.0 m) exceeds the capabilities` | cảnh báo của SLAM Toolbox |
| `Old-style arguments are deprecated` (static_transform_publisher) | cảnh báo cú pháp của launch chính thức |
| `[CẢNH BÁO] Chưa thấy node nào publish /map` khi chạy `save_map.sh` | chỉ là kiểm tra trước; script vẫn lưu nếu SLAM đang chạy |
| RViz2 Phần 1: `No transform from [map]` | Phần 1 chưa có `map` (Fixed Frame là `odom`) |
| Nav2 lúc mới khởi động: `Timed out waiting for transform from base_link to map` vài lần | chờ AMCL phát TF đầu tiên; tự hết |

### 8.2. Đồ hoạ / cảm biến (hay gặp nhất, nhất là WSL2)

| Triệu chứng | Cách xử lý |
|---|---|
| Gazebo crash ngay, log có `Ogre::UnimplementedException`, `GL3Plus`, `OGRE EXCEPTION`; hoặc cửa sổ Gazebo đen/trắng | Render bằng CPU: thêm **`software_render:=true`** vào lệnh launch. Chậm hơn nhưng đúng |
| `check_sensors.py` FAIL `/scan` (gần như mọi tia ~0.16 m hoặc toàn inf); SLAM chỉ vẽ một ô vuông nhỏ | Như trên: `software_render:=true`. Laptop 2 card trên Ubuntu cài thật: thử `export __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia` trước khi launch |
| `check_sensors.py` FAIL cliff, undock `CANCELED`, log `Reached backup limit!` | Đảm bảo **không** truyền `cliff_reflex:=true`; nếu LiDAR cũng FAIL thì `software_render:=true` |
| Robot màu đen trong Gazebo | Khi render bằng CPU robot cũng có thể đen mà cảm biến vẫn đúng – tin `check_sensors.py`, không tin màu |
| Cửa sổ Gazebo mở nhưng trống, đứng ở `Requesting list of world names` | GUI không tìm thấy server qua mạng nội bộ (hay gặp khi có VPN/Docker/WSL2): `kill_sim.sh`, rồi `export IGN_IP=127.0.0.1` trong terminal đó và launch lại |
| WSL2: log `failed to open /dev/dri/renderD128: Permission denied` | `sudo usermod -aG render $USER`, rồi `wsl --shutdown` trong PowerShell và mở lại Ubuntu |
| Chạy trong máy ảo VirtualBox/VMware | 3D của máy ảo thường không đủ cho Gazebo Fortress → `software_render:=true`; tốt nhất dùng Ubuntu cài thật hoặc WSL2 |
| RTF rất thấp (< 0.3), mọi thứ chậm | Cắm sạc + chế độ hiệu năng cao; đóng trình duyệt/IDE; WSL2: tăng RAM/CPU trong `.wslconfig`; dùng `use_rviz:=false` khi không cần |

Mỗi lần đổi cách render: `Ctrl+C` → `kill_sim.sh` → launch lại → chạy lại `check_sensors.py`.
`software_render:=true` phải thêm vào **mọi** launch (sim, mapping, navigation).

### 8.3. Cài đặt / môi trường

| Triệu chứng | Nguyên nhân → cách sửa |
|---|---|
| `Package 'tb4_lab04' not found` | chưa `source ~/workspaces/tb4_gazebo/install/setup.bash` (hoặc chưa `colcon build`) |
| `[tb4_lab04] THIẾU GÓI ROS: ...` | chạy đúng lệnh `sudo apt install ...` in ngay bên dưới |
| `doctor.sh` cảnh báo `... đang lấy từ '<đường dẫn>' thay vì /opt/ros/humble` | workspace khác đang ghi đè gói hệ thống → bỏ `source` workspace đó khỏi `~/.bashrc`, mở terminal mới |
| `ign: command not found` / `ign gazebo --versions` không ra 6.x | cài lại mục 1.4 (`ignition-fortress`) |
| `sudo apt update` lỗi `EXPKEYSIG`/`NO_PUBKEY` của ROS | xem ghi chú ở mục 1.3 |
| Terminal này không thấy topic của terminal kia (`ros2 topic list` thiếu) | lệch `ROS_LOCALHOST_ONLY`/`ROS_DOMAIN_ID` giữa các terminal → sửa `~/.bashrc`, `ros2 daemon stop` |

### 8.4. Khi chạy

| Triệu chứng | Nguyên nhân → cách sửa |
|---|---|
| Log lặp `Đang chờ mô phỏng khởi động... (chưa có: /odom)` | Gazebo chưa lên xong (máy chậm) hoặc kẹt. Chờ; quá 5 phút → `Ctrl+C`, `kill_sim.sh`, launch lại |
| Gazebo đứng ở `asking for robot_description` | lỗi treo đã biết của `gz_ros2_control` khi máy quá tải → `kill_sim.sh`, launch lại |
| Robot không chạy khi teleop | chưa undock; terminal teleop không được chọn; robot đang chạy phản xạ (log `Ignoring velocities commanded while an autonomous behavior is running`) → chờ vài giây, đi xa tường |
| `Server amcl was unable to be reached ... by bond` | máy quá tải lúc khởi động → `kill_sim.sh`, launch lại (repo đã nâng `bond_timeout` lên 15 s) |
| `LỖI BẢN ĐỒ: Chưa có bản đồ` | chưa làm Phần 2 / chưa `save_map.sh` |
| AMCL lệch, LiDAR không khớp tường | dùng **2D Pose Estimate**; kiểm tra cùng world và vị trí spawn như lúc mapping |
| Nav2 goal `ABORTED`, log `Failed to make progress` / `No valid path` | goal ở vùng xám/sát tường → chọn ô trắng cách tường ≥ 0.5 m; robot còn trong dock → undock |
| `nav_monitor.py` báo Nav2 "ĐỨNG HÌNH" | máy quá tải → `kill_sim.sh`, launch lại, đóng bớt ứng dụng |
| Bấm `Ctrl+C` ngay vài giây đầu (lúc launch đang khởi tạo tiến trình) → terminal **treo**, có thể kèm `TypeError: RunningProcessEvent.__init__() missing ... 'pid'` | lỗi của chính `ros2 launch` bản Humble (gói `launch`, không phải repo – bản gốc cũng bị); bấm `Ctrl+C` lần 2 không ăn → mở terminal khác chạy `ros2 run tb4_lab04 kill_sim.sh` (nó tự `SIGKILL` launch bị treo). Tránh: chờ launch lên hẳn rồi mới `Ctrl+C` |

---

## 9. Cấu trúc repo và pipeline

### 9.1. Cấu trúc

```
tb4_lab04/
├── package.xml, CMakeLists.txt        # package ament_cmake "tb4_lab04"
├── launch/
│   ├── tb4_lab04_common.py            # phần dùng chung: kiểm tra gói, tham số, include TurtleBot 4, RViz
│   ├── sim.launch.py                  # Phần 1: Gazebo + TurtleBot 4 + RViz2 (fixed frame odom)
│   ├── mapping.launch.py              # Phần 2: + SLAM Toolbox
│   ├── navigation.launch.py           # Phần 3+4: + map_server/AMCL (+ Nav2)
│   └── explore.launch.py              # (tuỳ chọn) SLAM + Nav2 + tự khám phá
├── config/
│   ├── slam.yaml                      # SLAM Toolbox (bản gốc TurtleBot 4)
│   ├── localization.yaml              # AMCL + map_server (gốc + initial pose + /scan_nav)
│   ├── nav2.yaml                      # Nav2 (gốc + /scan_nav + dock_layer) – Phần 4
│   ├── nav2_explore.yaml              # Nav2 cho tự khám phá (nhanh hơn, inflation 0.35 m)
│   ├── create3_fast.yaml              # Create 3 safety_override full (chỉ explore, fast:=true)
│   └── create3_no_cliff_reflex.yaml   # Create 3: tắt phản xạ cliff + bỏ giới hạn lùi (backup_only)
├── rviz/sim.rviz, rviz/nav.rviz       # RViz2 cho Phần 1 và Phần 2–4 (có Nav2 Goal)
├── maps/                              # map.yaml + map.pgm do bạn tạo ở Phần 2
├── scripts/
│   ├── doctor.sh, collect_debug.sh    # kiểm tra môi trường / gom thông tin chẩn đoán
│   ├── check_sensors.py, check_sim.py # Phần 1
│   ├── save_map.sh, check_map.py, clean_map.py   # Phần 2
│   ├── compare_pose.py                # Phần 3
│   ├── nav_monitor.py                 # Phần 4
│   ├── wait_for_sim.py, dock_obstacle.py         # được launch gọi tự động
│   ├── auto_explore.py                # (tuỳ chọn) frontier exploration
│   └── kill_sim.sh                    # dọn Gazebo/ROS còn sót
├── test/                              # unit test: python3 test/test_pure_logic.py
└── docs/                              # tài liệu
```

### 9.2. Node / topic chính

```
Gazebo Fortress ──ros_gz_bridge──► /scan (LaserScan), /clock, cảm biến Create 3
   ▲                diffdrive_controller ──► /odom + TF odom→base_link
   │ /cmd_vel ◄── motion_control (Create 3) ◄── /cmd_vel ◄─┬─ teleop_twist_keyboard (Phần 1–3)
   │                                                        └─ velocity_smoother ◄─ controller_server (Nav2)
Phần 2:   /scan + TF ──► slam_toolbox ──► /map + TF map→odom ──► map_saver_cli ──► map.yaml/map.pgm
Phần 3–4: map.yaml ──► map_server ──► /map ;  /scan_nav + /map + TF ──► amcl ──► TF map→odom, /amcl_pose
Phần 4:   Nav2 Goal (RViz2) ──► bt_navigator ──► planner_server (NavFn, global costmap) ──► /plan
                                            └──► controller_server (DWB, local costmap) ──► /cmd_vel_nav
```

| Topic | Kiểu | Vai trò |
|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | LiDAR RPLIDAR mô phỏng → SLAM, RViz |
| `/scan_nav` | `sensor_msgs/msg/LaserScan` | `/scan` trễ 0.1 s (giờ mô phỏng) → AMCL, costmap Nav2 |
| `/odom` | `nav_msgs/msg/Odometry` | odometry bánh xe → Nav2, motion_control |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | lệnh vận tốc → motion_control của Create 3 |
| `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | cây frame `map → odom → base_link → cảm biến` |
| `/clock` | `rosgraph_msgs/msg/Clock` | giờ mô phỏng (mọi node `use_sim_time: true`) |
| `/map` | `nav_msgs/msg/OccupancyGrid` | slam_toolbox (Phần 2) hoặc map_server (Phần 3–4) |
| `/initialpose`, `/amcl_pose`, `/particle_cloud` | | 2D Pose Estimate → AMCL; pose ước lượng; tập hạt |
| `/navigate_to_pose` (action) | `nav2_msgs/action/NavigateToPose` | nút Nav2 Goal → bt_navigator |
| `/plan`, `/local_plan`, `/global_costmap/costmap`, `/local_costmap/costmap` | | đường đi và costmap hiển thị trên RViz2 |
| `/undock` (action), `/dock_status` | `irobot_create_msgs` | rời dock / trạng thái dock |

### 9.3. Những điểm khác cấu hình gốc của TurtleBot 4 (và vì sao)

| Thay đổi | Lý do |
|---|---|
| SLAM/AMCL/Nav2 chỉ bật khi `wait_for_sim.py` thấy `/clock` chạy và có `/odom` | bật trong lúc Gazebo còn khởi động làm máy quá tải, lifecycle Nav2 lỗi bond |
| AMCL tự đặt initial pose (0, 0, 0) | frame `map` của SLAM trùng điểm spawn; khỏi phải bấm 2D Pose Estimate |
| AMCL + costmap đọc `/scan_nav` (= `/scan` trễ 0.1 s bằng `topic_tools delay`) | tránh treo TF (deadlock `tf2_ros` trên Humble) đã tái hiện khi scan đến trước transform tương ứng |
| Lớp costmap `dock_layer` + `dock_obstacle.py` | dock thấp hơn mặt quét LiDAR, costmap không thấy → Nav2 có thể lái đâm vào dock |
| `bond_timeout` 15 s | máy chậm hay vượt mức 4 s mặc định |
| `cliff_reflex:=false` mặc định | world phẳng; cảm biến cliff đo sai khi render lỗi sẽ huỷ undock |
| Create 3 `safety_override: backup_only` | bỏ giới hạn "chỉ được lùi 0.15 m": khi tì sát tường, phản xạ bumper + giới hạn lùi làm robot đứng im mãi (`Reached backup limit!`) |
| (chỉ `explore.launch.py`) `nav2_explore.yaml` + `safety_override: full` | khám phá nhanh hơn (0.40 m/s), không mất thời gian xoay hướng ở mỗi goal; Phần 4 vẫn dùng `nav2.yaml` gốc |
| `save_map.sh` dùng `--free 0.15` | để ô "chưa biết" không bị đọc thành ô trống khi load lại |

---

## 10. Tham số launch

Chung cho mọi launch:

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `world` | `maze` | `maze` \| `depot` \| `warehouse` (2 world sau cần Internet lần đầu) |
| `model` | `standard` | `standard` \| `lite` |
| `x`, `y`, `z`, `yaw` | `0.0` | vị trí spawn – Phần 2, 3, 4 phải giống nhau |
| `use_rviz` | `true` | mở RViz2 |
| `rviz_config` | `rviz/sim.rviz` (Phần 1), `rviz/nav.rviz` (còn lại) | file cấu hình RViz2 |
| `software_render` | `false` | `true` = render bằng CPU (`LIBGL_ALWAYS_SOFTWARE=1`) – cho WSL2/driver lỗi |
| `cliff_reflex` | `false` | bật lại phản xạ chống rơi của Create 3 |

`mapping.launch.py`: `sync` (`true`), `slam_params_file`, `slam_delay` (2 s).
`navigation.launch.py`: `map` (trống = tự tìm `maps/map.yaml`), `use_nav2` (`true`),
`localization_params_file`, `nav2_params_file`, `localization_delay` (2 s), `nav2_delay` (8 s).
`explore.launch.py`: `fast` (`true`), `explore`, `save_map`, `map_dir`, `max_duration`, `return_home`, `nav2_params_file` (`config/nav2_explore.yaml`), … (xem `--show-args`).

Xem đầy đủ: `ros2 launch tb4_lab04 <file>.launch.py --show-args`.

---

Tài liệu tham khảo: [TurtleBot 4 Simulator](https://github.com/turtlebot/turtlebot4_simulator) ·
[TurtleBot 4 User Manual](https://turtlebot.github.io/turtlebot4-user-manual/) ·
[ROS 2 Humble – cài đặt](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) ·
[SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox) · [Nav2](https://docs.nav2.org/)
