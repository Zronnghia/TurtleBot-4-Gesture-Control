cmake_minimum_required(VERSION 3.8)
project(tb4_lab04)

find_package(ament_cmake REQUIRED)

# Launch, cấu hình (goal, vật thể, YOLO, Nav2...), RViz và bản đồ -> share/tb4_lab04/
# (thư mục maps/ luôn có README.md nên không bao giờ rỗng -> install không lỗi
#  ngay cả khi chưa làm Phần 2)
install(
  DIRECTORY launch config rviz maps
  DESTINATION share/${PROJECT_NAME}
)

# Script chạy bằng `ros2 run tb4_lab04 <tên>`
install(
  PROGRAMS
    scripts/check_sim.py
    scripts/check_sensors.py
    scripts/dock_obstacle.py
    scripts/auto_explore.py
    scripts/compare_pose.py
    scripts/nav_monitor.py
    scripts/check_map.py
    scripts/clean_map.py
    scripts/wait_for_sim.py
    scripts/waypoint_navigator.py
    scripts/yolo_detector.py
    scripts/spawn_objects.py
    scripts/goal_recorder.py
    scripts/check_goals.py
    scripts/localization_check.py
    scripts/save_map.sh
    scripts/kill_sim.sh
    scripts/doctor.sh
    scripts/install_yolo_deps.sh
    scripts/collect_debug.sh
  DESTINATION lib/${PROJECT_NAME}
)

# Module Python dùng chung, được các script trên `import lab_common` (cùng thư mục, không chạy trực tiếp)
install(
  FILES scripts/lab_common.py
  DESTINATION lib/${PROJECT_NAME}
)

# Ghi lại đường dẫn thư mục source để navigation.launch.py / save_map.sh
# luôn dùng maps/map.yaml mới nhất mà không cần build lại sau khi lưu bản đồ.
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/source_dir.txt "${CMAKE_CURRENT_SOURCE_DIR}")
install(
  FILES ${CMAKE_CURRENT_BINARY_DIR}/source_dir.txt
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
