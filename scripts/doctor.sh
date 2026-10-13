#!/usr/bin/env bash
# Bài thực hành 04 – kiểm tra môi trường TRƯỚC khi chạy mô phỏng.
#
#   ros2 run tb4_lab04 doctor.sh        (hoặc: bash scripts/doctor.sh khi chưa build)
#
# Không sửa gì trên máy, chỉ báo PASS / WARN / FAIL và gợi ý cách sửa.
# Mã thoát: 0 = không có lỗi chặn, 1 = có ít nhất một [FAIL].

set -uo pipefail

FAILS=0
WARNS=0
pass() { echo -e "  \e[32m[PASS]\e[0m $*"; }
warn() { echo -e "  \e[33m[WARN]\e[0m $*"; WARNS=$((WARNS + 1)); }
fail() { echo -e "  \e[31m[FAIL]\e[0m $*"; FAILS=$((FAILS + 1)); }
info() { echo -e "  [INFO] $*"; }

IS_WSL=0
if grep -qi microsoft /proc/version 2>/dev/null; then IS_WSL=1; fi

# ---------------------------------------------------------------------------------------------
echo "== 1. Hệ điều hành"
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  if [[ "${VERSION_ID:-}" == "22.04" ]]; then
    pass "Ubuntu ${VERSION_ID}"
  else
    fail "Cần Ubuntu 22.04 (ROS 2 Humble + Gazebo Fortress), đang là ${PRETTY_NAME:-?}"
  fi
fi
if (( IS_WSL )); then
  info "Đang chạy trong WSL2."
  if [[ -d /mnt/wslg || -n "${WAYLAND_DISPLAY:-}" ]]; then
    pass "Có WSLg (hiển thị cửa sổ Linux trên Windows)"
  else
    fail "Không thấy WSLg -> cần Windows 11 hoặc Windows 10 22H2 + 'wsl --update' (xem README mục 1.2)"
  fi
fi

# ---------------------------------------------------------------------------------------------
echo "== 2. ROS 2"
if [[ "${ROS_DISTRO:-}" == "humble" ]]; then
  pass "ROS_DISTRO=humble"
else
  fail "Chưa source ROS 2 Humble (ROS_DISTRO='${ROS_DISTRO:-}') -> source /opt/ros/humble/setup.bash"
fi
if ! command -v ros2 >/dev/null 2>&1; then
  fail "Không có lệnh ros2 -> sudo apt install ros-humble-desktop"
fi

# ---------------------------------------------------------------------------------------------
echo "== 3. Gói ROS cần thiết (và có bị workspace khác 'ghi đè' không)"
REQUIRED="turtlebot4_ignition_bringup turtlebot4_navigation turtlebot4_description turtlebot4_viz \
irobot_create_nodes irobot_create_msgs irobot_create_ignition_bringup ros_gz_bridge ros_gz_sim ros_ign_gazebo \
slam_toolbox nav2_bringup nav2_map_server nav2_amcl nav2_rviz_plugins rviz2 teleop_twist_keyboard \
topic_tools tf2_ros_py sensor_msgs_py"
if command -v python3 >/dev/null 2>&1; then
  # Một lần gọi Python cho tất cả gói (nhanh hơn gọi `ros2 pkg prefix` từng gói).
  PKG_REPORT="$(python3 - $REQUIRED <<'PY' 2>/dev/null
import sys
try:
    from ament_index_python.packages import get_package_prefix, PackageNotFoundError
except ImportError:
    print('NOAMENT')
    sys.exit(0)
for p in sys.argv[1:]:
    try:
        print('OK', p, get_package_prefix(p))
    except PackageNotFoundError:
        print('MISSING', p, '-')
PY
)"
  if [[ "$PKG_REPORT" == "NOAMENT" || -z "$PKG_REPORT" ]]; then
    fail "Không đọc được danh sách gói ROS (chưa source /opt/ros/humble/setup.bash?)"
  else
    MISSING=""
    OVERRIDDEN=0
    while read -r st p prefix; do
      if [[ "$st" == "MISSING" ]]; then
        MISSING="$MISSING ros-humble-${p//_/-}"
        fail "$p chưa cài"
      elif [[ "$prefix" != "/opt/ros/humble" ]]; then
        # Gói hệ thống bị một workspace khác che: nguồn gây lỗi rất khó hiểu (vd. ros_gz build cho
        # Gazebo Harmonic từ một workspace UR/khác).
        warn "$p đang lấy từ '$prefix' thay vì /opt/ros/humble (workspace khác ghi đè gói hệ thống)"
        OVERRIDDEN=1
      else
        pass "$p"
      fi
    done <<< "$PKG_REPORT"
    if [[ -n "$MISSING" ]]; then
      echo "        -> sudo apt update && sudo apt install -y$MISSING"
    fi
    if (( OVERRIDDEN )); then
      echo "        -> Nếu bạn KHÔNG cố ý build các gói trên từ source, đó rất có thể là nguyên nhân lỗi:"
      echo "           bỏ dòng 'source <workspace đó>/install/setup.bash' khỏi ~/.bashrc rồi mở terminal mới."
    fi
  fi
fi
if command -v ros2 >/dev/null 2>&1 && ros2 pkg prefix tb4_lab04 >/dev/null 2>&1; then
  pass "tb4_lab04 (đã build và source workspace: $(ros2 pkg prefix tb4_lab04))"
else
  warn "tb4_lab04 chưa thấy -> cd ~/tb4_ws && colcon build && source install/setup.bash"
fi

echo "== 4. Workspace đang được source (AMENT_PREFIX_PATH)"
OTHER=""
IFS=':' read -r -a PREFIXES <<< "${AMENT_PREFIX_PATH:-}"
for p in "${PREFIXES[@]}"; do
  [[ -z "$p" ]] && continue
  case "$p" in
    /opt/ros/humble) ;;
    */install/tb4_lab04|*/install) ;;
    *) OTHER="$OTHER $p" ;;
  esac
done
if [[ -n "$OTHER" ]]; then
  warn "Đang source thêm workspace khác:$OTHER"
  echo "        Nếu gặp lỗi lạ, mở terminal mới KHÔNG source các workspace đó (xem ~/.bashrc)."
else
  pass "Chỉ có /opt/ros/humble và workspace của bài"
fi

# ---------------------------------------------------------------------------------------------
echo "== 5. Ignition Gazebo Fortress"
if command -v ign >/dev/null 2>&1; then
  V="$(timeout 20 ign gazebo --versions 2>/dev/null | head -n 1)"
  if [[ "$V" == 6.* ]]; then pass "ign gazebo $V (Fortress)"; else warn "ign gazebo --versions = '${V:-không rõ}' (Fortress là 6.x)"; fi
else
  fail "Không có lệnh 'ign' -> sudo apt install ignition-fortress (xem README bước cài đặt)"
fi
if [[ -n "${GZ_VERSION:-}${IGNITION_VERSION:-}" ]]; then
  warn "Đang đặt GZ_VERSION/IGNITION_VERSION='${GZ_VERSION:-}${IGNITION_VERSION:-}' – TurtleBot 4 Humble cần Fortress; hãy unset nếu không chắc"
fi

# ---------------------------------------------------------------------------------------------
echo "== 6. Mạng ROS 2"
if [[ "${ROS_LOCALHOST_ONLY:-0}" == "1" ]]; then
  pass "ROS_LOCALHOST_ONLY=1"
elif [[ -n "${ROS_DOMAIN_ID:-}" && "${ROS_DOMAIN_ID}" != "0" ]]; then
  pass "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
else
  warn "Đang dùng domain mặc định 0 trên mạng chung -> export ROS_LOCALHOST_ONLY=1 (thêm vào ~/.bashrc)"
fi
if [[ "${RMW_IMPLEMENTATION:-}" == "rmw_cyclonedds_cpp" && "${ROS_LOCALHOST_ONLY:-0}" == "1" ]]; then
  warn "CycloneDDS + ROS_LOCALHOST_ONLY=1 trên Humble hay lỗi 'failed to create domain' -> unset RMW_IMPLEMENTATION"
fi

# ---------------------------------------------------------------------------------------------
echo "== 7. Tiến trình còn sót"
if pgrep -u "$(id -u)" -f 'ign gazebo|gz sim' >/dev/null 2>&1; then
  warn "Còn Gazebo đang chạy -> ros2 run tb4_lab04 kill_sim.sh"
else
  pass "Không có Gazebo cũ"
fi

# ---------------------------------------------------------------------------------------------
echo "== 8. Đồ hoạ"
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  fail "Không có DISPLAY/WAYLAND_DISPLAY: Gazebo GUI và RViz2 sẽ không mở được"
else
  pass "Có màn hình (${DISPLAY:-}${WAYLAND_DISPLAY:+ wayland:$WAYLAND_DISPLAY})"
fi
if [[ "${LIBGL_ALWAYS_SOFTWARE:-}" == "1" || "${LIBGL_ALWAYS_SOFTWARE:-}" == "true" ]]; then
  info "LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE} -> đang ép render bằng CPU (đúng nhưng chậm)"
fi
if command -v glxinfo >/dev/null 2>&1; then
  R="$(timeout 20 glxinfo -B 2>/dev/null | awk -F': ' '/OpenGL renderer/ {print $2}')"
  if [[ -z "$R" ]]; then
    warn "glxinfo không lấy được OpenGL renderer (driver đồ hoạ có vấn đề?)"
  elif [[ "$R" == *D3D12* ]]; then
    warn "OpenGL: $R (GPU qua WSL2). Nếu Gazebo crash hoặc check_sensors.py báo LiDAR/cliff sai -> thêm software_render:=true vào lệnh launch"
  elif [[ "$R" == *llvmpipe* || "$R" == *softpipe* ]]; then
    warn "OpenGL: $R (render bằng CPU) -> Gazebo chạy được nhưng chậm (RTF thấp)"
  else
    pass "OpenGL: $R"
  fi
else
  info "Bỏ qua kiểm tra GPU – cài 'mesa-utils' để có glxinfo: sudo apt install -y mesa-utils"
fi

# ---------------------------------------------------------------------------------------------
echo "== 9. RAM / CPU"
MEM_GB=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo)
if (( MEM_GB >= 8 )); then
  pass "RAM ${MEM_GB} GB"
elif (( IS_WSL )); then
  warn "RAM của WSL2 chỉ ${MEM_GB} GB -> tăng trong %UserProfile%\\.wslconfig (memory=8GB), rồi 'wsl --shutdown'"
else
  warn "RAM ${MEM_GB} GB (< 8 GB) – Gazebo + Nav2 có thể rất chậm"
fi
CPUS=$(nproc)
if (( CPUS >= 4 )); then pass "${CPUS} CPU"; else warn "${CPUS} CPU (< 4) – có thể rất chậm"; fi

# ---------------------------------------------------------------------------------------------
echo "== 10. Bản đồ (cần cho Phần 3, 4)"
MAPDIR=""
if command -v ros2 >/dev/null 2>&1 && PREFIX="$(ros2 pkg prefix tb4_lab04 2>/dev/null)"; then
  MARKER="$PREFIX/share/tb4_lab04/source_dir.txt"
  [[ -f "$MARKER" ]] && MAPDIR="$(head -n 1 "$MARKER")/maps"
fi
if [[ -n "$MAPDIR" && -f "$MAPDIR/map.yaml" && -f "$MAPDIR/map.pgm" ]]; then
  pass "Có $MAPDIR/map.yaml + map.pgm"
else
  info "Chưa có maps/map.yaml + map.pgm -> làm Phần 2 rồi chạy: ros2 run tb4_lab04 save_map.sh"
fi

echo
if (( FAILS == 0 )); then
  echo -e "\e[32mKết luận: không có lỗi chặn ($WARNS cảnh báo).\e[0m"
  exit 0
fi
echo -e "\e[31mKết luận: $FAILS lỗi cần sửa trước khi chạy ($WARNS cảnh báo).\e[0m"
exit 1
