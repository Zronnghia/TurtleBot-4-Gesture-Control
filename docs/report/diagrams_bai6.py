#!/usr/bin/env python3
"""Sơ đồ cho báo cáo Bài 6 (cử chỉ tay) -> docs/report/fig/fig6_*.png.   Chạy: python3 docs/report/diagrams_bai6.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diagrams import arrow, box, canvas, layer, save  # noqa: E402


def poly(ax, pts, label=None, lpos=None, fs=5.2, color='#444444', ls='-'):
    """Đường gấp khúc, mũi tên ở điểm cuối; nhãn đặt tại lpos (x, y)."""
    for a, b in zip(pts[:-2], pts[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=0.8, ls=ls, solid_capstyle='butt')
    arrow(ax, pts[-2], pts[-1], color=color, ls=ls)
    if label:
        ax.text(lpos[0], lpos[1], label, fontsize=fs, ha='center', va='center', color='#222222',
                family='DejaVu Sans Mono', bbox=dict(fc='white', ec='none', pad=0.6, alpha=0.95))


def fig6_system():
    fig, ax = canvas(7.8, 96, y0=4)
    # ---- người dùng
    layer(ax, 1, 82, 99, 95, 'Người dùng (không dùng bàn phím khi demo)')
    box(ax, 12, 88, 20, 7, 'Bàn tay: cử chỉ\ntrước webcam laptop', 'white', bold=True)
    box(ax, 50, 88, 30, 7, 'Cửa sổ OpenCV: landmark, tên cử chỉ,\nđộ tin cậy, trạng thái robot', 'white')
    box(ax, 86, 88, 20, 7, 'Gazebo GUI:\nTurtleBot 4 chuyển động', 'white')
    # ---- node nhận diện
    layer(ax, 1, 50, 44, 78, 'gesture_recognition_node', '#d9783a', center=True, bottom=True)
    box(ax, 11.5, 70, 18, 6.5, 'OpenCV VideoCapture\n640×480, lật gương', 'orange')
    box(ax, 33, 70, 18, 6.5, 'MediaPipe Gesture\nRecognizer (VIDEO)', 'orange')
    box(ax, 11.5, 58, 18, 7, 'WaveDetector\ntay xoè dao động\nngang ≥ 3 nhịp', 'orange')
    box(ax, 33, 58, 18, 7, 'GestureStabilizer\nngưỡng conf + bỏ\nphiếu theo thời gian', 'orange')
    arrow(ax, (20.5, 70), (24, 70))
    arrow(ax, (27, 66.75), (17, 61.5), 'landmark', 0.5, fs=5.0)
    arrow(ax, (37, 66.75), (37, 61.5), 'gesture, score', 0.5, fs=5.0)
    arrow(ax, (20.5, 58), (24, 58))
    # ---- node hành vi
    layer(ax, 56, 50, 99, 78, 'robot_behavior_node', '#d9783a', center=True, bottom=True)
    box(ax, 67, 70, 19, 7, 'BehaviorStateMachine\nchọn → xác nhận →\nthực hiện / dừng / huỷ', 'orange')
    box(ax, 89, 70, 17, 7, 'Watchdog 1 s,\ncooldown 1 s,\nchỉ bắt sườn', 'orange')
    box(ax, 67, 58, 19, 7, 'SegmentRunner\nđo bằng /odom,\ntăng / giảm tốc', 'orange')
    box(ax, 89, 58, 17, 7, 'An toàn LiDAR\nvật cản < 0,40 m\n→ dừng', 'orange')
    arrow(ax, (76.5, 70), (80.5, 70), both=True)
    arrow(ax, (67, 66.5), (67, 61.5))
    arrow(ax, (76.5, 58), (80.5, 58), both=True)
    # ---- topic giữa 2 node / hiển thị
    poly(ax, [(42, 58), (50, 58), (50, 70), (57.5, 70)], '/detected_gesture\n(String)', (50, 64), fs=5.0)
    arrow(ax, (62, 73.5), (58, 84.5), '/robot_behavior/state', 0.45, fs=5.0, loff=(7.5, 0))
    arrow(ax, (33, 73.25), (42, 84.5), 'frame + result', 0.5, fs=5.0, loff=(-4.5, 0))
    arrow(ax, (12, 84.5), (11.5, 73.25), 'webcam', 0.5, fs=5.0)
    # ---- mô phỏng
    layer(ax, 1, 14, 99, 46, 'TurtleBot 4 Simulator – Ignition Gazebo Fortress, world gesture_arena (sân 9 m × 9 m)',
          '#777777', center=True, bottom=True)
    box(ax, 67, 39, 19, 6, 'motion_control\n(irobot_create_nodes)')
    box(ax, 89, 39, 15, 6, 'action /undock\n(Create 3)')
    box(ax, 67, 29, 19, 6, 'diffdrive_controller\n(ros2_control)')
    box(ax, 30, 29, 24, 6, 'ros_gz_bridge\n/scan, /dock_status, /clock')
    box(ax, 50, 20.5, 76, 4.5, 'Gazebo: Create 3 (bánh vi sai, bumper), RPLIDAR, dock, tường sân', 'grey')
    arrow(ax, (67, 54.5), (67, 42), '/cmd_vel (Twist)', 0.42, fs=5.2, loff=(0, 0))
    arrow(ax, (67, 36), (67, 32))
    arrow(ax, (67, 26), (67, 22.75))
    arrow(ax, (30, 22.75), (30, 26))
    poly(ax, [(76.5, 29), (79, 29), (79, 54.5)], '/odom', (79, 48))
    poly(ax, [(30, 32), (30, 48), (86, 48), (86, 54.5)], '/scan, /dock_status', (44, 48))
    arrow(ax, (93, 54.5), (93, 42), 'startup', 0.5, fs=5.0)
    poly(ax, [(88, 22.75), (98, 22.75), (98, 84.5), (94, 84.5)], color='#999999', ls='--')
    # ---- chú giải
    for x, t, k in ((13, 'gói chính thức', 'blue'), (35, 'bổ sung – package tb4_lab04', 'orange'),
                    (57, 'Gazebo', 'grey'), (79, 'hiển thị cho người dùng', 'white')):
        box(ax, x, 8, 19, 4, t, k, fs=5.8)
    save(fig, 'fig6_system.png')


def fig6_pipeline():
    fig, ax = canvas(7.6, 60)
    xs = [9, 27, 45, 63, 81]
    labels = ['Khung BGR\nwebcam', 'MediaPipe:\npalm detector\n→ 21 landmark\n→ phân loại',
              'Nhãn khung\n(conf ≥ 0,55\nnếu không: None)', 'Bỏ phiếu\ncửa sổ hold\n(≥70 % khung)',
              'publish\n/detected_gesture\n(mỗi khung)']
    for x, t in zip(xs, labels):
        box(ax, x, 45, 16, 12, t, 'orange' if x != xs[0] else 'white', fs=6.3)
    for a, b in zip(xs, xs[1:]):
        arrow(ax, (a + 8, 45), (b - 8, 45))
    box(ax, 45, 23, 22, 11, 'WaveDetector\nx tâm bàn tay xoè\ntrong 1,5 s: ≥ 3 nhịp\nbiên độ ≥ 6 % ảnh', 'orange', fs=6.2)
    arrow(ax, (31, 39), (39, 28.5), 'landmark', 0.5, fs=5.2)
    arrow(ax, (45, 28.5), (45, 39), '"Wave"', 0.5, fs=5.2, loff=(3.5, 0))
    box(ax, 81, 23, 22, 11, 'hold: 0,5 s (chọn/xác\nnhận/huỷ), 0,2 s Open_Palm,\n0,15 s Wave, 0,4 s None', 'white', fs=5.8)
    arrow(ax, (63, 39), (76, 28.5), '', 0.5, color='#999999', ls='--')
    ax.text(50, 6, 'Một khung nhận nhầm không đủ phiếu → nhãn ổn định không đổi. Không có camera → không publish → robot dừng.',
            fontsize=6.0, ha='center', style='italic', color='#444444')
    save(fig, 'fig6_pipeline.png')


def lab(ax, x, y, text, fs=5.6):
    """Nhãn mũi tên bằng phông sans (DejaVu Sans Mono vẽ dấu tiếng Việt bị lệch)."""
    ax.text(x, y, text, fontsize=fs, ha='center', va='center', color='#222222', linespacing=1.15,
            bbox=dict(fc='white', ec='none', pad=0.5, alpha=0.95))


def fig6_states():
    fig, ax = canvas(7.6, 80, y0=4)
    box(ax, 12, 70, 19, 7, 'WAITING\nchưa có tín hiệu', 'white', fs=6.2)
    box(ax, 12, 52, 19, 7, 'SETUP\nundock + ra giữa sân', 'grey', fs=6.2)
    box(ax, 42, 61, 18, 7, 'IDLE\nchờ lệnh', 'blue', fs=6.8, bold=True)
    box(ax, 80, 61, 26, 7, 'SELECTED\ngreet | forward_back | circle', 'orange', fs=6.2)
    box(ax, 80, 30, 26, 7, 'EXECUTING\npublish /cmd_vel 20 Hz', 'green', fs=6.4, bold=True)
    box(ax, 42, 30, 20, 7, 'STOPPED\n(giữ lựa chọn)', 'red', fs=6.2)
    box(ax, 12, 20, 19, 7, 'SIGNAL_LOST\nrobot dừng', 'red', fs=6.2)
    arrow(ax, (21.5, 68), (33, 63.5)); lab(ax, 27, 68.5, 'tin nhắn đầu tiên')
    arrow(ax, (21.5, 54), (33, 58.5)); lab(ax, 27, 53.5, 'xong / huỷ')
    arrow(ax, (51, 63), (67, 63)); lab(ax, 59, 66.5, 'Wave / Pointing_Up / Victory')
    arrow(ax, (67, 59), (51, 59)); lab(ax, 59, 55.5, 'Closed_Fist / hết hạn 15 s')
    arrow(ax, (80, 57.5), (80, 33.5)); lab(ax, 88, 45.5, 'Thumb_Up\n(xác nhận)')
    arrow(ax, (67, 32), (52, 32)); lab(ax, 59.5, 35.5, 'Open_Palm / vật cản / kẹt')
    arrow(ax, (52, 28), (67, 28)); lab(ax, 59.5, 24.5, 'Thumb_Up (chạy lại)')
    arrow(ax, (73, 33.5), (47, 57.5)); lab(ax, 63, 44, 'hoàn thành')
    arrow(ax, (40, 33.5), (40, 57.5)); lab(ax, 40, 45.5, 'Closed_Fist')
    arrow(ax, (32, 28), (21.5, 22)); lab(ax, 22, 31, 'mất /detected_gesture > 1 s\n(từ mọi trạng thái)')
    arrow(ax, (16, 23.5), (36, 57.5), ls='--', color='#888888'); lab(ax, 25.5, 40, 'có tín hiệu lại')
    ax.text(50, 10.5, 'Chỉ phản ứng khi nhãn ổn định ĐỔI (bắt sườn) + cooldown 1 s cho mỗi cử chỉ; Open_Palm luôn có hiệu lực.\n'
                      'Đang EXECUTING: cử chỉ chọn / xác nhận bị bỏ qua. Chưa ra giữa sân khi xác nhận -> rời dock trước.',
            fontsize=5.9, ha='center', va='center', style='italic', color='#444444')
    save(fig, 'fig6_states.png')


def main():
    fig6_system()
    fig6_pipeline()
    fig6_states()


if __name__ == '__main__':
    main()
