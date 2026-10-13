# test/e2e – công cụ tự kiểm thử end-to-end

Hai script đã dùng để chạy thử toàn bộ dự án mà không cần người ngồi điều khiển
(kết quả trong `docs/TEST_REPORT.md`). **Chỉ để tự kiểm tra máy/cấu hình** – video nộp bài
phải dùng **teleop** (Phần 2) và nút **Nav2 Goal trên RViz2** (Phần 4) như đề yêu cầu.

| Script | Thay cho | Cách chạy (sau khi đã `source` workspace) |
|---|---|---|
| `explore.py` | teleop ở Phần 2 | `python3 test/e2e/explore.py 900` – undock rồi bám tường phải 900 s (giờ mô phỏng), ≤ 0.15 m/s |
| `send_goals.py` | bấm Nav2 Goal ở Phần 4 | `python3 test/e2e/send_goals.py maps/map.yaml 3` – tự chọn 3 điểm trống cách tường ≥ 0.8 m, gửi lần lượt qua action `NavigateToPose` |

Môi trường đã chạy thử: Ubuntu 22.04 + ROS 2 Humble (bản phát hành 2026-09-14) + Ignition
Gazebo Fortress 6.18, toàn bộ gói TurtleBot 4 / Create 3 / Nav2 / SLAM Toolbox / ros_gz build từ
đúng tag của bản apt Humble; hiển thị qua Xvfb + Mesa llvmpipe (không GPU).
