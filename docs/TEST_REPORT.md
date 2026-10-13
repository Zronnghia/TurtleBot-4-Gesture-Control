# Báo cáo kiểm thử

## 0. Đợt rà soát 2026-10-12 (bản hiện tại)

Mục tiêu: rà toàn bộ repo sau phản hồi "nhiều lỗi, không chạy được", sửa lỗi và viết lại hướng dẫn (README).

**Cách kiểm thử đợt này (nói rõ giới hạn):** Ubuntu 22.04 (chroot) + ROS 2 Humble core build từ mã nguồn
(rclpy, launch, launch_ros, tf2_ros, topic_tools 1.1.2, nav2_msgs, irobot_create_msgs, xacro). Các launch file
**chính thức** của `turtlebot4` / `turtlebot4_simulator` / `create3_sim` / `ros_gz` / `nav2_bringup` (nhánh
`humble`) được chạy thật; riêng các tiến trình nặng (Gazebo, SLAM Toolbox, các server Nav2, RViz2) được thay
bằng tiến trình giả ghi lại tham số dòng lệnh, và một "mô phỏng giả" ở mức ROS (`/clock`, `/odom`, TF, `/scan`
ray-cast, `/dock_status`, action `/undock`). Như vậy kiểm chứng được: đồ thị launch (thứ tự, điều kiện, tham
số, file cấu hình truyền cho từng node, event handler), các script và `topic_tools delay`; **không** kiểm
chứng lại vật lý/render của Gazebo hay thuật toán SLAM/Nav2 (đã chạy thật ở các mục 1–3c bên dưới).

| Bộ kiểm thử | Kết quả |
|---|---|
| Unit test `python3 test/test_pure_logic.py` (có ROS) | 52/52 OK |
| Đồ thị launch: 4 launch × các biến thể (`world`, `model`, `cliff_reflex`, `software_render`, `sync`, `use_nav2`, `explore`, thiếu/hỏng bản đồ, thiếu gói apt, `--show-args`, tắt sạch khi Ctrl+C) | 48/48 PASS |
| Script chạy với mô phỏng giả: `check_sensors`, `check_sim` (undock + lái + quay), `compare_pose`, `nav_monitor` (3 goal thành công + 1 thất bại), `check_map`, `clean_map`, `kill_sim`, `doctor`, `collect_debug` | 9/9 PASS |
| `pyflakes`, `shellcheck -S warning`, `py_compile` | sạch (pyflakes chỉ còn các biến giữ tham chiếu `TransformListener` có chủ đích) |

Lỗi/điểm yếu tìm thấy và đã sửa trong đợt này:

| # | Vấn đề | Sửa |
|---|---|---|
| R1 | Thiếu gói apt → `ros2 launch` in traceback `package '...' not found` khó hiểu | launch kiểm tra trước, in danh sách gói thiếu + đúng lệnh `sudo apt install ...` rồi dừng (không mở Gazebo) |
| R2 | Không có cách bật render bằng CPU từ launch (WSL2/driver lỗi là nguyên nhân hàng đầu của "LiDAR mù", undock `CANCELED`) | tham số `software_render:=true` cho mọi launch |
| R3 | 4 launch chép lặp cùng một khối (tham số, include TurtleBot 4, RViz) → dễ lệch nhau | gom vào `launch/tb4_lab04_common.py` (đồ thị launch trước/sau so khớp bằng harness) |
| R4 | Ctrl+C: `dock_obstacle.py`, `wait_for_sim.py`, `auto_explore.py` chết với `exit code -2` (log `[ERROR] process has died`) vì nhận SIGINT 2 lần (terminal + launch) | bỏ qua SIGINT lần 2 khi đang dọn dẹp → thoát mã 0 |
| R5 | `doctor.sh` không phát hiện workspace khác ghi đè gói hệ thống, không biết WSL2/D3D12 | thêm kiểm tra gói lấy từ đâu, AMENT_PREFIX_PATH, WSLg, renderer D3D12/llvmpipe, RAM WSL, bản đồ |
| R6 | Không có cách gom log để hỗ trợ từ xa | `collect_debug.sh` → `~/tb4_debug_<thời_gian>.txt` |
| R7 | `save_map.sh` in cảnh báo bằng nhãn đỏ `[LỖI]` dù vẫn lưu thành công | đổi thành `[CẢNH BÁO]` |
| R8 | Tài liệu nói "robot đen thui = render lỗi" – sai: ảnh `test_evidence/part1_gazebo_rviz.png` robot cũng đen mà cảm biến đúng | sửa tài liệu: tin `check_sensors.py`, không tin màu |
| R9 | `REPORT_DRAFT.md` ghi "thay đổi duy nhất là initial pose" và world `depot` – sai so với repo | liệt kê đúng các thay đổi; world `maze` |
| R10 | Hai bản hướng dẫn (`README.md`, `docs/HUONG_DAN_CHAY.md`) chồng chéo, lệch nhau | viết lại một README duy nhất; bỏ `HUONG_DAN_CHAY.md` |

**Kiểm tra bổ sung (lần 2 trong đợt):**

| Kiểm tra | Kết quả |
|---|---|
| Chạy lại toàn bộ với **đúng phiên bản apt Humble hiện hành** (rosdistro): `turtlebot4` 1.0.5, `turtlebot4_simulator` 1.0.3, `turtlebot4_desktop` 1.0.0, `create3_sim` 2.1.0, `ros_gz` 0.244.26, `navigation2` 1.1.20, `topic_tools` 1.1.2 | launch 48/48, script 9/9 PASS |
| **So khớp hồi quy** với bản gốc (bản đã chạy thật end-to-end ở các mục 1–3c): 7 biến thể launch, so tập tiến trình được khởi chạy + toàn bộ tham số dòng lệnh + **nội dung đầy đủ mọi file tham số** truyền cho từng node | 7/7 GIỐNG HỆT → thay đổi đợt này không làm khác hành vi đã kiểm chứng thật |
| **Ctrl+C trong terminal thật (pty)**: 4 launch, bấm ở cả lúc đang khởi động (3–14 s) lẫn lúc đã chạy; 5 lệnh `ros2 run` bấm sớm (0.6 s) và muộn | 12/12 launch thoát mã 0, 0 tiến trình sót, 0 lỗi/traceback từ node của repo; script không in traceback |

Lỗi tìm thêm và đã sửa ở lần 2:

| # | Vấn đề | Sửa |
|---|---|---|
| R11 | Ctrl+C khi `explore.launch.py` đang chờ hệ thống khởi động → `auto_explore.py` in traceback `KeyboardInterrupt` + `[ERROR] process has died` | bọc toàn bộ `main()` (cả giai đoạn chờ/khởi động) |
| R12 | Ctrl+C khi `check_sensors.py` đang đo → traceback, mã 254 | như trên |
| R13 | Ctrl+C đúng lúc `dock_obstacle.py` vừa khởi động (đang import rclpy) → `exit code -2` | import ROS trong `main()`, bọc `_run()`; áp dụng cho mọi script ROS của repo |
| R14 | Ctrl+C khi `auto_explore.py` đang nhận message: rclpy Humble ném `RuntimeError: Unable to convert call argument to Python object` (SIGINT cắt ngang lúc chuyển message) → traceback | ghi nhận Ctrl+C bằng cờ SIGINT; lỗi phát sinh sau Ctrl+C được coi là tắt bình thường (lỗi khi chưa bấm Ctrl+C vẫn báo) – áp dụng cho mọi script ROS |

Giới hạn còn lại (nói thẳng): đợt này không chạy lại Gazebo/SLAM/Nav2 thật (môi trường kiểm thử không tải được các
gói đó). Hành vi với Gazebo thật dựa trên (1) lần chạy thật ở mục 1–3c và (2) phép so khớp hồi quy ở trên. Lỗi phụ
thuộc máy người dùng (driver đồ hoạ, WSL2, workspace khác, máy quá yếu) không thể loại trừ từ xa – dùng
`doctor.sh`, `check_sensors.py`, `collect_debug.sh`.

### Đợt 2026-10-12 (tối) – tự khám phá: robot kẹt sát tường, chậm, bản đồ còn khuyết góc

Báo lỗi: `explore.launch.py` – robot đứng im sát góc tường, log lặp `Passing new path to controller`; chạy
chậm; bản đồ còn các góc chưa quét.

Nguyên nhân: (1) goal được đặt sát frontier – ở góc tường nghĩa là sát tường, robot lọt vào vùng chi phí cao
của costmap, DWB không tìm được quỹ đạo; Create 3 mặc định chỉ cho lùi ~0.15 m (`Reached backup limit!`)
nên recovery "lùi" của Nav2 cũng không gỡ được; bản cũ không có bước tự gỡ kẹt nên cứ gửi goal thất bại
rồi bỏ qua vị trí → bỏ sót cả vùng. (2) tốc độ: Nav2 0.26 m/s, Create 3 giới hạn 0.306 m/s, và robot xoay
đúng hướng ở mỗi goal. (3) góc khuyết: hệ quả của (1) + bỏ cụm frontier < 0.5 m.

Sửa: chọn chỗ đứng cách tường ≥ 0.4 m mà LiDAR nhìn thẳng qua frontier vào vùng chưa biết (≤ 1.5 m);
tự gỡ kẹt khi goal thất bại (kẹt thật 3 lần liên tiếp → dừng và lưu bản đồ, có thể chạy tiếp); Create 3 `safety_override` (`backup_only` mọi launch, `full` cho explore);
`config/nav2_explore.yaml` (0.40 m/s, bỏ hướng cuối, inflation 0.35 m); frontier tối thiểu 0.3 m.

**Sửa tiếp (13/10, sau ảnh bản đồ của người dùng):** bản 12/10 cho quay 1.5 rad/s – SAI: SLAM Toolbox xử lý 1
scan mỗi ≥ 0.25 s và chỉ dò góc ±0.349 rad (`coarse_search_angle_offset`), 1.5 rad/s = 0.375 rad/scan vượt vùng
dò → khớp scan kém → mép tường lốm đốm/dày hơn bản đồ cũ. Đã đưa về 1.0 rad/s (0.25 rad/scan, như cấu hình
gốc TurtleBot 4); giữ 0.40 m/s thẳng (0.10 m/scan, trong vùng dò ±0.25 m). Thêm lượt quét lại các đoạn biên/vị
trí đã bỏ qua trước khi kết thúc (các góc còn xám trên bản đồ người dùng: hốc chữ L bên trái, góc trên-phải,
một hốc ở dãy răng cưa bên phải). Lưu ý: mô phỏng gọn dùng SLAM giả (khớp tuyệt đối) nên KHÔNG đo được chất
lượng scan matching – phần này dựa trên phân tích tham số.

Cùng đợt (R15): Ctrl+C rất sớm (0.25–0.75 s sau `ros2 run`, đúng lúc rclpy đang tạo Executor/guard condition)
thỉnh thoảng in `Exception ignored in: Executor.__del__ ... AttributeError: _sigint_gc` hoặc traceback
`KeyboardInterrupt` trong importlib (5/40 lần với `compare_pose.py`). Vô hại (thoát mã 1 đúng như mong đợi) nhưng
trông như lỗi → mọi script ROS chỉ nuốt các thông báo rác này SAU khi đã bấm Ctrl+C. Kiểm lại: `compare_pose.py`
45/45, `nav_monitor.py` 20/20, `check_sensors.py` 20/20 lần Ctrl+C ngẫu nhiên – 0 traceback, 0 treo.

R16: Ctrl+C `explore.launch.py` lúc đang khám phá → `[ERROR] [auto_explore.py]: process has died [exit code 1]`
hoặc treo 5–15 s rồi bị launch SIGTERM/SIGKILL. Nguyên nhân: (a) `finished_reason` khởi tạo sẵn = "không còn
frontier" nên Ctrl+C bị coi là khám phá XONG → script còn ra lệnh quay về điểm xuất phát rồi lưu; (b) lưu bản đồ khi
SLAM Toolbox cũng đang tắt cùng launch thì chắc chắn hỏng, `subprocess` chờ tới timeout; (c) rclpy chỉ tắt context
khi nhận SIGTERM chứ không thoát. Sửa: Ctrl+C → lý do "người dùng dừng"; trong `explore.launch.py`
(`save_on_ctrl_c: false`) thoát ngay, chỉ đường tới `maps/autosave/`; chạy bằng `ros2 run` thì vẫn thử lưu (SLAM ở
terminal khác còn sống); SIGTERM xử lý như Ctrl+C. Kiểm lại: Ctrl+C lúc đang khám phá → thoát 0.8 s, mã 0, không log đỏ.

R17: Ctrl+C khi Gazebo còn đang khởi động (`wait_for_sim.py` đang chờ) → `wait_for_sim.py` thoát mã 1 (log đỏ) và
`OnProcessExit` vẫn bật SLAM/Nav2 trong lúc launch đang tắt → in "Khởi động SLAM Toolbox ..." và launch mất ~20 s mới
thoát (chờ hết TimerAction). Sửa: `wait_for_sim.py` thoát 0 khi Ctrl+C; `after_sim_ready()` (launch/tb4_lab04_common.py)
không bật gì khi launch đang tắt (có unit test). Kiểm lại với Gazebo giả khởi động chậm 25 s: mapping/explore/navigation
Ctrl+C ở 8–20 s → thoát 0.4 s, không log đỏ, không bật SLAM/Nav2.

R18 (tự khám phá): robot tì sát tường **bên hông** → "Tự gỡ kẹt: đã dịch 0.00 m" 3 lần → dừng vì kẹt (2/3 lần chạy thử
trong đợt này; một lần chỉ phủ 83.6 %). Nguyên nhân: kiểm tra "trống phía trước/sau" dùng hành lang rộng ±0.2 m > bán
kính robot 0.17 m nên chính bức tường ở hông bị tính là chắn trước/sau 0 m (log chẩn đoán mới: "trống phía sau 0.00 m,
phía trước 0.00 m, hướng thoáng nhất 3.24 m"). Sửa: hành lang ±0.15 m khi gỡ kẹt + quay lưng lại vật cản gần nhất
(< 0.35 m) trước khi tiến ra; log gỡ kẹt in các khoảng trống để chẩn đoán. Sau sửa: 2/2 lần chạy, 12/12 lần gỡ kẹt đều
dịch được 0.10–0.52 m, độ phủ vùng đi tới được **100 %** (mô hình kẹt 0 và 0.25 m).

R19 (13/10 chiều, ảnh người dùng: hốc giữa 2 đoạn tường, tam giác xám lòi ra sau khối hộp, góc dọc bậc thang):
khi đã tới chỗ đứng tốt nhất mà LiDAR không quét thêm được (bị góc che, nhìn xiên vào hốc), bản cũ đánh dấu cả
đoạn biên "chết"; còn chỗ đứng thử 2 lần thì bị loại – nhưng `find_candidates` chỉ trả MỘT chỗ đứng/cụm nên loại
chỗ đứng = bỏ luôn cả cụm, dù đứng phía khác vẫn nhìn được. Lượt quét lại cũng chọn đúng chỗ đứng cũ nên vô ích.
Sửa: `find_candidates(avoid=...)` loại riêng chỗ đứng đã thất bại (bán kính 0.6 m) và chọn chỗ đứng tốt nhất còn lại
cho cùng cụm; chỉ bỏ đoạn biên sau `max_views_per_frontier` = 3 chỗ đứng khác nhau; lượt quét lại giữ danh sách chỗ
đứng "không thấy gì" để nhìn từ chỗ mới; bảng kết quả in toạ độ `Biên chưa quét`. Unit test mới cho cơ chế này.
Mô phỏng gọn (2 lần, mô hình kẹt 0 / 0.25 m): độ phủ vùng tới được 100 %, nhanh hơn (873–906 s so với 1058–1119 s
mô phỏng), log cho thấy nhiều lần "thử chỗ đứng khác" rồi quét được. Giới hạn: SLAM giả khớp tuyệt đối, nhìn
xiên vẫn ghi nhận đủ – nên chưa tái hiện được đúng các hốc trong ảnh; cơ chế được kiểm bằng unit test + log.

Kết quả chạy lại cuối đợt 13/10 (sau mọi sửa ở trên): unit test 62/62 OK; đồ thị launch 53/53 PASS; so khớp hồi quy
với bản gốc 7/7 GIỐNG HỆT; Ctrl+C trong terminal thật 14/15 launch sạch (1 lần treo ở giây thứ 3 = lỗi `launch` Humble
nêu trên), 5/5 `ros2 run` không traceback; pyflakes/shellcheck sạch.

Không sửa được trong repo (ghi vào README 8.4): Ctrl+C trong ~1–3 s đầu, đúng lúc `ros2 launch` đang tạo tiến trình,
làm chính `launch` của Humble treo (`TypeError: RunningProcessEvent.__init__() missing ... 'pid'`, Ctrl+C lần 2 không
ăn). Bản gốc của bạn cũng bị (3/12 lần, cửa sổ 1.3–1.9 s; bản mới 2.0–2.9 s vì nạp launch lâu hơn chút). Đã kiểm:
`kill_sim.sh` ở terminal khác gỡ được (SIGKILL launch treo + dọn tiến trình sót) 2/2 lần.

Kiểm thử bằng mô phỏng gọn với **đúng hình học `maze.sdf`** (40 khối hộp; diện tích trống tính ra 281.7 m²,
khớp 282 m² của bản đồ mẫu chính thức), SLAM giả (ray-cast LiDAR), Nav2 giả (A* trên `/map` có nới bán kính
robot, chặn khi gặp tường chưa thấy, và mô hình "kẹt": robot bắt đầu goal khi đang cách tường < ngưỡng thì
Nav2 thất bại). `auto_explore.py` chạy thật, lưu bản đồ thật qua `save_map.sh`:

| Phiên bản / mô hình kẹt | Kết thúc | Độ phủ vùng đi tới được | Goal tới nơi / thất bại | Tự gỡ kẹt |
|---|---|---|---|---|
| Bản cũ, chỉ kẹt khi robot nằm trong vùng chết (0.175 m) | sau 1036 s mô phỏng, kẹt từ goal thứ 4 | 52.6 % | 3 / 81 | không có |
| Bản mới, như trên | 741 s mô phỏng, hết frontier | **99.9 %** | 91 / 0 | 0 |
| Bản mới, kẹt nếu cách tường < 0.25 m | hết frontier | 99.3 % | 82 / 2 | 2 |
| Bản mới, kẹt nếu cách tường < 0.45 m (cố ý rất khắt khe: hành lang < 0.9 m là kẹt) | dừng vì kẹt, **tự lưu bản đồ** | 90.3 % | 35 / 29 | 29 |
| ↳ như trên, lái robot ra chỗ thoáng rồi `ros2 run tb4_lab04 auto_explore.py` (cùng bản đồ SLAM) | hết frontier | 82.2 % → **99.9 %** | 41 / 0 | 0 |

Phần còn thiếu ở bản mới chỉ là khoang kín bên trong các khối tường (robot và LiDAR không thể tới) và một hốc
0.5 m². Giới hạn: Nav2 giả không mô phỏng động lực DWB/va chạm vật lý; hành vi Nav2 thật với tham số mới
chưa chạy lại trong đợt này.

---

## Các đợt trước

### Báo cáo chạy thử end-to-end (môi trường mô phỏng dựng lại)

Mục tiêu: chạy **thật** toàn bộ dự án `tb4_lab04` – Gazebo, TurtleBot 4, SLAM Toolbox, AMCL, Nav2,
RViz2 và các script – trước khi giao, để tìm và sửa các lỗi chỉ xuất hiện lúc chạy.

## 1. Môi trường kiểm thử

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| Hệ điều hành | Ubuntu 22.04 (jammy) | chroot dựng bằng `debootstrap` |
| ROS 2 | Humble, bản phát hành chính thức 2026-09-14 (tarball `ros2-humble-*-linux-jammy-amd64`) | cùng mã nguồn với gói apt |
| Ignition Gazebo | Fortress 6.18.0 (ign-rendering 6.6.4, ign-sensors 6.9.0, ign-msgs 8.7.1 …) | build từ mã nguồn, tag mới nhất của Fortress – tương đương bản apt của OSRF |
| TurtleBot 4 | `turtlebot4` 1.0.5, `turtlebot4_simulator` 1.0.3, `turtlebot4_desktop` 1.0.0 | build từ tag đúng bản apt |
| Create 3 | `create3_sim` 2.1.0, `irobot_create_msgs` 2.1.0 | như trên |
| Nav2 / SLAM | `navigation2` 1.1.20, `slam_toolbox` 2.6.10 | như trên |
| Cầu nối Gazebo | `ros_gz` 0.244.26, `gz_ros2_control` 0.7.21, `ros2_control` 2.54.3 | như trên |
| Phần cứng | 2 vCPU, 8 GB RAM, **không GPU** | hiển thị qua Xvfb + Mesa llvmpipe (render bằng CPU) |

### Khác biệt CHỈ có trong môi trường kiểm thử (không nằm trong repo)

Máy kiểm thử không có GPU nên Gazebo chỉ đạt real-time factor (RTF) ≈ 0.03 với cấu hình gốc. Để
chạy hết quy trình trong thời gian chấp nhận được, môi trường kiểm thử đã:

1. Phần 1 chạy **đúng nguyên bản** (có cửa sổ Gazebo, RViz2, cảm biến đủ tần số). Từ Phần 2 trở đi
   chạy Gazebo không cửa sổ (`-s`) và giảm tần số cảm biến **trong bản cài của TurtleBot 4**:
   camera OAK-D 30→1 Hz, 11 cảm biến IR/cliff 62→5 Hz, LiDAR 62→20 Hz. RTF tăng lên ≈ 0.29.
2. Phần 4 giới hạn RTF của world `maze` ở 0.12 để CPU còn dư cho Nav2.
3. Thay người lái bằng script: teleop được thay bằng một node bám tường (chỉ publish `/cmd_vel`,
   ≤ 0.15 m/s, ≤ 0.5 rad/s); thao tác "Nav2 Goal" trên RViz2 được thay bằng client gửi đúng action
   `NavigateToPose` (cùng action mà nút Nav2 Goal gửi).
4. Chỉ world `maze` được chạy thử: `depot`/`warehouse` cần tải model từ Gazebo Fuel, không truy cập
   được từ môi trường kiểm thử.

## 2. Kết quả

| Phần | Lệnh | Kết quả |
|---|---|---|
| 1 | `sim.launch.py` + `check_sim.py` | **8/8 PASS**: `/scan` 640 tia @ 62 Hz (giờ sim), `/odom` @ 62 Hz, TF `odom→base_link`, TF `base_link→turtlebot4/rplidar_link/rplidar`, `/cmd_vel` có subscriber, undock thành công, tiến 0.287 m, quay 1.76 rad. Gazebo GUI + RViz2 (`sim.rviz`, Global Status OK) – ảnh `test_evidence/part1_gazebo_rviz.png` |
| 2 | `mapping.launch.py` + lái tự động 1500 s sim + `save_map.sh` | Bản đồ 406 × 405 ô (0.05 m), **280 m² đã khám phá** (map mẫu chính thức của maze: 282 m²), tường thẳng, không nhân đôi – `test_evidence/map.png`. `save_map.sh` chạy cả lúc đang mapping (lưu tiến độ) và lúc cuối, `check_map.py` không cảnh báo |
| 3 | `navigation.launch.py use_nav2:=false` + `compare_pose.py` | AMCL tự đặt pose (0,0,0); trong 10 phút robot di chuyển: **sai số vị trí TB 0.050 m, lớn nhất 0.170 m; sai số góc TB 3.4°** → ĐẠT |
| 4 | `navigation.launch.py` + undock + 3 goal + `nav_monitor.py` | Với bản cuối của repo: **3/3 goal SUCCEEDED liên tiếp** (3 khu vực khác nhau, mỗi goal 6–7 m đường chim bay), sai số dừng 0.21–0.29 m, **0 recovery, 0 va chạm, 0 lỗi TF** – `test_evidence/nav2_goal.png`. Chạy tiếp goal thứ 4 trong cùng phiên (tổng ~55 phút): bị huỷ vì lifecycle manager mất heartbeat của `controller_server` 15 s do máy kiểm thử quá tải (CPU 2 lõi render bằng phần mềm), **không** phải deadlock TF (gdb sạch, 0 lỗi TF) |

## 3. Lỗi tìm thấy khi chạy thật và cách đã sửa

| # | Lỗi | Nguyên nhân | Sửa |
|---|---|---|---|
| 1 | `check_sim.py` crash: `ValueError: Logger severity cannot be changed between calls` | rclpy cấm gọi `log.info`/`log.error` xen kẽ tại **cùng một dòng lệnh** (`(log.info if ok else log.error)(...)`) | tách thành 2 nhánh `if/else` (cả `check_sim.py` và `nav_monitor.py`) |
| 2 | Undock bị báo FAIL dù robot vẫn đang undock | chờ kết quả action theo giờ thực 120 s; ở RTF thấp robot chưa kịp undock | chờ theo **giờ mô phỏng** (tối đa 60 s sim) |
| 3 | Máy chậm: không kịp nhận `/dock_status` trong 5 s → script tưởng robot đã ra khỏi dock và lái | `/dock_status` chạy theo giờ mô phỏng | chờ tới 30–120 s; **không biết trạng thái dock thì không lái** |
| 4 | `/scan`, `/odom` có thể FAIL oan trên máy chậm | so tần số theo giờ thực | so theo `header.stamp` (giờ mô phỏng) |
| 5 | `Server amcl was unable to be reached after 4.00s by bond` → localization không "active" | bật AMCL/Nav2 sau 5–10 s cố định, đúng lúc Gazebo còn đang khởi động và CPU quá tải | `wait_for_sim.py`: chỉ bật SLAM/AMCL/Nav2 khi `/clock` chạy và có `/odom` (sự kiện `OnProcessExit`); `bond_timeout` = 15 s |
| 6 | **Nav2 treo vĩnh viễn** sau ~15 phút: log lặp `Transform data too old when converting from map to odom`, `Received plan with zero length`; robot đứng yên/quay recovery | **deadlock trong `tf2_ros` (Humble 0.25.24)**: luồng nhận TF giữ khoá trong `BufferCore::setTransformImpl` và gọi callback cần khoá của `Buffer`, trong khi luồng `MessageFilter::add` (scan của costmap) giữ khoá `Buffer` trong `waitForTransform` và chờ khoá kia. Xác nhận bằng `gdb` (backtrace của `controller_server` và `planner_server`) ở **5 lần chạy**, với cả FastDDS lẫn CycloneDDS | AMCL + 2 costmap đọc `/scan_nav` = `/scan` trễ 0.1 s (giờ sim) bằng `topic_tools/delay`: khi scan tới, transform tương ứng đã có sẵn nên không phát sinh yêu cầu chờ TF – điều kiện cần của deadlock. Trước khi sửa: deadlock ở 5/5 lần chạy, sau ~15 phút. Sau khi sửa: 3/3 goal, 0 lỗi TF trong ~55 phút chạy liên tục. `nav_monitor.py` vẫn có bộ phát hiện "Nav2 ĐỨNG HÌNH" phòng khi gặp lại |
| 7 | `nav_monitor.py` đếm 185 "va chạm" cho 1 lần chạm | `/hazard_detection` lặp lại liên tục khi bumper còn bị ép | chỉ đếm sườn lên (mỗi lần chạm = 1) |
| 8 | RViz2 mở ra chỉ thấy ~4 m quanh gốc, bản đồ bị xoay lệch 2.5° | góc nhìn mặc định của TurtleBot 4 (Scale 127, Angle −1.615) | Scale 35, Angle 0 |

### Vấn đề của gói chính thức (không sửa được trong repo) – đã ghi vào README mục 8

- Máy quá tải lâu: lifecycle manager có thể báo `CRITICAL FAILURE: SERVER controller_server IS
  DOWN after not receiving a heartbeat` và tắt Nav2 (gặp 1 lần sau ~55 phút trên máy kiểm thử).
  Repo đã nâng `bond_timeout` từ 4 s lên 15 s; nếu vẫn gặp: chạy lại.
- `gz_ros2_control` có thể **treo khi lấy `robot_description`** lúc máy quá tải (Gazebo đứng,
  không có `/clock`); gặp 1 lần. `wait_for_sim.py` sẽ báo rõ sau 300 s; cách xử lý: chạy lại.
- CycloneDDS + `ROS_LOCALHOST_ONLY=1` trên Humble: `failed to create domain` (interface `lo`
  không multicast). Repo mặc định dùng FastDDS nên không bị; README ghi cách dùng nếu đổi RMW.
- Các log sau là **bình thường** trong mô phỏng TurtleBot 4 Humble, không phải lỗi của bài:
  `Service oakd/stop_camera unavailable`, `Service stop_motor unavailable`, `Desired controller
  update period (0.001 s) is faster than the gazebo simulation period`, `kdl_parser ... root link
  ... has an inertia`, `minimum laser range setting (0.0 m) exceeds the capabilities`.

## 3b. Tự khám phá (`explore.launch.py` + `auto_explore.py`) – chạy thật

Cấu hình: world `maze`, Gazebo không cửa sổ, RTF giới hạn 0.2 (thực tế đạt ~0.1 vì SLAM + Nav2 +
Gazebo trên 2 vCPU), tham số mặc định của repo.

| Chỉ số | Kết quả |
|---|---|
| Kết thúc | tự kết thúc: "không còn frontier đi tới được" (xác nhận 3 lần), quay về điểm xuất phát, tự lưu `map.yaml/map.pgm` |
| Thời gian | 1001 s mô phỏng (≈ 2 h 45 phút thực ở RTF ~0.1; ở RTF 0.5 sẽ ≈ 35 phút) |
| Diện tích | **297 m²** đã khám phá (bản đồ lái bám tường 1500 s: 280 m²; map mẫu chính thức: 282 m²) – phủ cả vùng bậc thang góc trên phải mà cách bám tường bỏ sót |
| Goal | 60 tới nơi, 2 thất bại, 8 huỷ giữa chừng vì cụm đã được quét xong; 16 vị trí bị đánh dấu bỏ qua (đều là đoạn biên sát tường/khe mà LiDAR không quét thêm được) |
| Chất lượng | tường thẳng, không nhân đôi (`test_evidence/explore_map.png`); `check_map.py` không cảnh báo |
| Ổn định | 0 tiến trình chết, 0 `CRITICAL`, 0 deadlock TF trong ~2 h 45 phút |

Lỗi tìm thấy qua 6 lần chạy thật và đã sửa (unit test tương ứng trong `test/test_pure_logic.py`):

| # | Lỗi | Sửa |
|---|---|---|
| E1 | Robot đi "khám phá" vệt trống rộng 1 ô bên trong khối tường (tia LiDAR lọt vào) | bỏ vệt rộng 1–2 ô bằng phép mở hình thái (erode → dilate) trước khi tìm frontier |
| E2 | Robot đi tới vùng "trống" hình tam giác bên trong khối tường rỗng – tia lọt qua khe 1 ô ở góc tường; không bao giờ quét xong | chỉ nhận frontier liền với vùng trống của robot khi đã bịt khe ≤ 2 ô (nới tường 1 ô) |
| E3 | Đánh dấu cả cụm frontier 18 m là "không quét được" sau 1 lần tới gần | chỉ đánh dấu đoạn 1 m quanh điểm đã tới, và chỉ khi lượng ô mới quét được quanh đó < 0.1 m² (dựa trên bản đồ MỚI sau khi tới) |
| E4 | Đuổi theo các cụm nhỏ gần nhất (bậc thang), bỏ quên vùng lớn → chậm | chi phí = quãng đường − độ dài cụm (tối đa 4 m): 280 m² sau ~1 h thay vì 156 m² |
| E5 | Lần chạy sau lỗi discovery: `robot_state_publisher service not available`, spawner chết, log `RTPS_TRANSPORT_SHM ... open_and_lock_file failed` | file `/dev/shm/fastrtps_*` cũ do tiến trình bị SIGKILL. `kill_sim.sh` nay tự xoá các file này khi không còn tiến trình ROS nào. Đây có thể chính là lỗi bạn gặp trên máy mình |

Còn lại (không sửa trong repo): sau ~2.5 h ở RTF 0.1, SLAM Toolbox (chế độ sync) bắt đầu tồn hàng đợi
scan (`Queue size has grown to: 111`) – máy kiểm thử quá yếu; không ảnh hưởng bản đồ đã lưu.

## 3c. Lỗi undock / dock chắn đường (báo từ máy người dùng) – tái hiện và sửa

Triệu chứng người dùng gửi: undock `CANCELED` + `is_docked: false`, robot gần như không lùi (x = -0.018),
log `Reached backup limit!`, `Reflex Exceeded Runtime without clearing hazard`; dock vẫn chắn phía trước;
`explore.launch.py` kết thúc sau 13 s với "0 m²" và bản đồ costmap `7 X 7` ô; robot trong Gazebo đen thui.

Phân tích mã nguồn `create3_sim` 2.1.0: LiDAR và 4 cảm biến cliff đều là `gpu_lidar` (đo bằng render). Cliff báo
"hụt chân" khi min(range) > 0.03 m (bình thường 0.0009–0.016 m). Phản xạ (reflex) chạy khi robot nhúc nhích mà có
hazard BUMP/CLIFF/STALL/WHEEL_DROP, và huỷ undock (`stop_on_new_behavior`). Undock chuẩn = lùi 0.4 m + quay 180°.

| Thử nghiệm (môi trường kiểm thử, `maze`) | Kết quả |
|---|---|
| Undock, cảm biến bình thường | SUCCEEDED, robot tới x = -0.353, yaw -169° (dock ở phía sau) |
| Bơm số đo cliff sai (inf, 100 Hz) + cấu hình cũ | **tái hiện đúng lỗi**: CANCELED, is_docked False, lùi 0.01–0.12 m, `Reached backup limit!`; `check_sim` bản mới báo Undock FAIL (bản cũ cho PASS) |
| Như trên + đổi tham số reflex lúc chạy | bị từ chối (motion_control: "Reflexes ... reject all changes") |
| Như trên + `cliff_reflex:=false` (mặc định mới, đặt lúc khởi động) | undock SUCCEEDED, lùi 0.35 m, quay 180°; `check_sim` toàn bộ PASS |
| `explore.launch.py` + lỗi cliff suốt từ đầu | undock SUCCEEDED, "cách thân dock 0.55 m, mặt quay ra xa dock", khám phá tới 278 m² (máy kiểm thử bị thu hồi trước khi xong; bản tự lưu 260 m², `check_map` không cảnh báo) |
| `explore.launch.py max_duration:=240` | dừng đúng hạn, về điểm SAU undock (-0.35, 0) (không về chỗ dock), đường về đi vòng qua dock, 0 va chạm, tự lưu 153 m² |
| `auto_explore` với LiDAR giả "mù" (mọi tia 0.165 m) | dừng ngay, mã 2, không lái, không lưu, in cách sửa |
| `check_sensors.py` bình thường / có lỗi cliff | OK / FAIL đúng cảm biến bị lỗi |
| `save_map.sh` sau khi tắt ROS daemon | lưu thành công |

Dock vô hình với LiDAR (dock cao ~0.1 m): costmap toàn cục tại thân dock = 100 với `dock_layer`, bản đồ SLAM = 0.

| Phiên bản `dock_layer` | Phần 4 (navigation.launch + bản đồ 280 m², goal đi qua dock) |
|---|---|
| đánh dấu khít ±0.08 m, neo odom | robot chạm góc dock (106 tin bumper) |
| ±0.16 m, neo odom | robot kẹt sát dock: odom trôi sau ~7 m nên dock ảo lệch khỏi dock thật dù AMCL đúng 2 cm; kẹt rồi bánh trượt làm odom lệch thêm 0.75 m |
| **±0.16 m, neo map (bản cuối)** | 4/4 goal SUCCEEDED (2 lượt đi qua dock), **0 va chạm**; đường đi Nav2 cách tâm dock ≥ 0.55 m. Odom trôi tới ~1 m so với map trong cùng lượt – xác nhận không được neo theo odom |

Lỗi phụ tìm thấy và sửa trong đợt này: `kill_sim.sh` không dừng tiến trình `ros2 run` (một `compare_pose.py` cũ còn
chạy sang phiên mới) và có thể giết shell có dòng lệnh khớp mẫu; `dock_obstacle.py` dùng TransformListener tốn
~8 % CPU (đổi sang đọc `/tf_static`: ~3 %); lưới điểm dock hụt mép (unit test bắt được).

Chưa xác nhận: cảm biến trên máy người dùng có thật sự sai vì render hay không (cần kết quả `check_sensors.py`).

## 4. Những gì CHƯA được kiểm chứng

- World `depot`, `warehouse` (cần Internet tới Gazebo Fuel).
- Chạy với GPU thật ở RTF ≈ 1 và tần số cảm biến gốc (máy của bạn). Logic không đổi, nhưng thời
  gian khởi động/đáp ứng sẽ khác – mọi chỗ chờ trong repo đều theo sự kiện hoặc giờ mô phỏng.
- Thao tác chuột trên RViz2 (2D Pose Estimate, Nav2 Goal) – đã thay bằng action/topic tương đương.
- WSL2.
