# maps/

Thư mục chứa bản đồ do **SLAM Toolbox** tạo ở Phần 2.

Sau khi chạy `ros2 run tb4_lab04 save_map.sh`, thư mục này sẽ có:

- `map.yaml` – metadata (độ phân giải, gốc toạ độ, ngưỡng occupied/free)
- `map.pgm`  – ảnh bản đồ (trắng = trống, đen = vật cản, xám = chưa biết)

`navigation.launch.py` tự động dùng `maps/map.yaml` trong thư mục này.
Các bản cũ được chuyển vào `backup_<thời_gian>/` (đã nằm trong `.gitignore`).

> Nhớ `git add maps/map.yaml maps/map.pgm` trước khi nộp bài.
