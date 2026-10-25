#!/usr/bin/env python3
"""Dựng báo cáo ngắn Bài 6 "Giao tiếp phi ngôn ngữ – điều khiển TurtleBot 4 bằng cử chỉ tay".

    python3 docs/report/diagrams_bai6.py        # vẽ lại sơ đồ (docs/report/fig/fig6_*.png) – chỉ khi sửa
    python3 docs/report/build_report_bai6.py    # -> docs/report/BaoCao_Bai6_TurtleBot4_Gesture.pdf

Ảnh thực nghiệm CỦA BẠN đặt trong docs/report/fig_user/ (thiếu ảnh nào thì dùng ảnh kiểm thử trong môi trường ảo
ở docs/report/fig/test6_*.png và script in CẢNH BÁO – nhớ thay trước khi nộp):
    gesture_wave.png, gesture_pointing.png, gesture_victory.png, gesture_thumb.png,
    gesture_palm.png, gesture_fist.png         cửa sổ webcam lúc nhận từng cử chỉ (có tên + % tin cậy)
    gazebo_gesture.png                          Gazebo + cửa sổ webcam cùng lúc (robot đang thực hiện hành vi)
    trajectory.png                              ảnh của `ros2 run tb4_lab04 plot_gesture_run.py`
    terminal_behavior.png                       terminal của robot_behavior_node (log [trạng thái])
Link: docs/report_info.yaml (link_video, link_github).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_report as br  # noqa: E402  (phông chữ, kiểu chữ, bảng, hình, bố cục – dùng chung với báo cáo bài 5)
from build_report import H1, H2, M, P, cm, colors  # noqa: E402
from pypdf import PdfReader, PdfWriter  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas  # noqa: E402
from reportlab.platypus import PageBreak, Paragraph, Spacer  # noqa: E402
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402

FIG = os.path.join(HERE, 'fig')
USER = os.path.join(HERE, 'fig_user')
OUT = os.path.join(HERE, 'BaoCao_Bai6_TurtleBot4_Gesture.pdf')
TITLE = 'Báo cáo thực hành số 6 – Điều khiển TurtleBot 4 bằng cử chỉ tay'
TEST_USED = []


def exp(user_name, test_name):
    """Ảnh thực nghiệm: ưu tiên ảnh của sinh viên, không có thì ảnh kiểm thử trong môi trường ảo."""
    p = os.path.join(USER, user_name)
    if os.path.isfile(p):
        return p, ''
    t = os.path.join(FIG, test_name)
    if os.path.isfile(t):
        TEST_USED.append(user_name)
        return t, ' <i>(ảnh kiểm thử trong môi trường ảo)</i>'
    return None, ''


def link(url, empty='(chưa điền – docs/report_info.yaml)'):
    url = (url or '').strip()
    if not url:
        br.MISSING.append('link trong docs/report_info.yaml')
        return '<font color="#b22222">{}</font>'.format(empty)
    return '<link href="{0}" color="blue"><u>{0}</u></link>'.format(br.esc(url))


def content(info):
    S = []
    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [
        ParagraphStyle('t0', fontName='Serif-B', fontSize=11, leading=14.5, spaceBefore=6),
        ParagraphStyle('t1', fontName='Serif', fontSize=11, leading=14, leftIndent=0.95 * cm),
    ]
    S += [Paragraph('MỤC LỤC', br.toc_title), toc, Spacer(1, 10)]
    S += br.table(['Nội dung nộp', 'Liên kết'], [
        ['Video demo (Google Drive, công khai)', link(info.get('link_video'))],
        ['GitHub repository (Public)', link(info.get('link_github'))],
    ], [5.2, 10.8], 'Bảng 0 – Liên kết video demo và mã nguồn.')
    S += [PageBreak()]

    # ===== 1
    S += [H1('1.  Mục tiêu và môi trường'),
          P('Bài thực hành xây dựng kênh giao tiếp phi ngôn ngữ giữa người và robot: người dùng ra cử chỉ tay trước '
            'webcam laptop, hệ thống nhận diện cử chỉ bằng mô hình học máy MediaPipe Gesture Recognizer và điều khiển '
            'TurtleBot 4 trong Gazebo thực hiện hành vi tương ứng qua ROS 2. Robot chỉ thực hiện hành vi sau cử chỉ '
            'xác nhận, không dùng bàn phím trong lúc demo, có cơ chế chống nhận diện nhiễu và luôn dừng khi có tín '
            'hiệu dừng hoặc mất tín hiệu điều khiển.', True),
          P('Môi trường: Ubuntu 22.04, ROS 2 Humble, Ignition Gazebo Fortress, TurtleBot 4 Simulator (Create 3 + '
            'RPLIDAR), Python 3.10, OpenCV 4.10, MediaPipe 0.10.21 (NumPy 1.26 để không xung đột với '
            + M('cv_bridge') + ' của Humble). Mã nguồn nằm trong package ' + M('tb4_lab04') + ' của các bài trước, '
            'bổ sung hai node ' + M('gesture_recognition_node') + ', ' + M('robot_behavior_node') + ', module logic '
            + M('gesture_logic.py') + ' (có kiểm thử đơn vị), ba launch file và world ' + M('gesture_arena')
            + ' – sân phẳng 9 m × 9 m không vật cản để các hành vi không va chạm.')]
    S += br.table(['File', 'Vai trò'], [
        ['launch/gesture_sim.launch.py', 'Phần 1: Gazebo + TurtleBot 4 trong world gesture_arena'],
        ['launch/gesture.launch.py', 'Phần 2 + 3: hai node cử chỉ, tham số config/gesture.yaml'],
        ['launch/gesture_demo.launch.py', 'tất cả trong một lệnh (node cử chỉ bật khi mô phỏng sẵn sàng)'],
        ['scripts/gesture_recognition_node.py', 'webcam → MediaPipe → lọc nhiễu → /detected_gesture'],
        ['scripts/robot_behavior_node.py', '/detected_gesture → máy trạng thái → /cmd_vel'],
        ['scripts/gesture_logic.py', 'WaveDetector, GestureStabilizer, BehaviorStateMachine, SegmentRunner'],
        ['scripts/webcam_test.py, check_cmd_vel.py', 'Phần 1: hiển thị webcam (OpenCV); kiểm tra robot nhận /cmd_vel'],
        ['worlds/gesture_arena.sdf, models/', 'sân mô phỏng; model gesture_recognizer.task (float16, 8,4 MB)'],
    ], [6.4, 9.6], 'Bảng 1 – Các file chính của Bài 6.', mono_cols=(0,))

    # ===== 2
    S += [H1('2.  Sơ đồ kiến trúc hệ thống'),
          P('Hệ thống gồm ba tầng (Hình 1). Tầng người dùng: bàn tay trước webcam; người dùng theo dõi kết quả trên '
            'cửa sổ OpenCV (tên cử chỉ, độ tin cậy, trạng thái robot) và trên Gazebo. Tầng ứng dụng gồm hai node ROS 2 '
            'tự viết, nối với nhau bằng topic ' + M('/detected_gesture') + ' (' + M('std_msgs/String') + '). Tầng mô '
            'phỏng là TurtleBot 4 chính thức: ' + M('motion_control') + ' của Create 3 nhận ' + M('/cmd_vel')
            + ', ' + M('diffdrive_controller') + ' phát ' + M('/odom') + ', ' + M('ros_gz_bridge') + ' đưa '
            + M('/scan') + ' và ' + M('/dock_status') + ' từ Gazebo sang ROS 2.', True)]
    S += br.figure(os.path.join(FIG, 'fig6_system.png'),
                   'Hình 1 – Kiến trúc hệ thống (cam: phần tự viết trong package tb4_lab04; xanh: gói chính thức).', 16.0)

    # ===== 3
    S += [H1('3.  Các node, topic và luồng xử lý'), H2('3.1.  Node và topic')]
    S += br.table(['Node', 'Subscribe', 'Publish', 'Vai trò'], [
        ['gesture_recognition_node', '/robot_behavior/state', '/detected_gesture<br/>/detected_gesture/info',
         'đọc webcam bằng OpenCV, nhận diện bằng MediaPipe, suy ra vẫy tay, lọc nhiễu, hiển thị'],
        ['robot_behavior_node', '/detected_gesture<br/>/odom, /scan<br/>/dock_status',
         '/cmd_vel<br/>/robot_behavior/state', 'máy trạng thái, thực hiện hành vi, watchdog, an toàn, undock '
                                               '(action client /undock)'],
        ['motion_control (Create 3)', '/cmd_vel', '–', 'áp giới hạn an toàn, chuyển lệnh tới bộ điều khiển bánh'],
        ['diffdrive_controller', '–', '/odom, TF', 'odometry bánh xe (dùng để đo quãng đường / góc quay)'],
    ], [4.3, 3.6, 3.6, 4.5], 'Bảng 2 – Các node chính và topic vào/ra.', mono_cols=(0, 1, 2))
    S += br.table(['Topic / action', 'Kiểu', 'Ý nghĩa'], [
        ['/detected_gesture', 'std_msgs/String', 'tên cử chỉ ĐÃ LỌC (Wave, Pointing_Up, Victory, Thumb_Up, Open_Palm, '
                                                 'Closed_Fist, Thumb_Down, ILoveYou, None), gửi mỗi khung ~30 Hz'],
        ['/detected_gesture/info', 'std_msgs/String (JSON)', 'nhãn thô của khung, độ tin cậy, tỉ lệ phiếu, FPS'],
        ['/robot_behavior/state', 'std_msgs/String (JSON)', 'trạng thái, hành vi đã chọn / đang chạy, tiến độ'],
        ['/cmd_vel', 'geometry_msgs/Twist', 'lệnh vận tốc 20 Hz khi đang thực hiện; 5 lệnh 0 khi dừng'],
        ['/odom', 'nav_msgs/Odometry', 'đo tiến độ từng đoạn chuyển động, phát hiện robot bị kẹt'],
        ['/scan', 'sensor_msgs/LaserScan', 'dừng khi có vật cản &lt; 0,40 m theo hướng đang chạy'],
        ['/dock_status, /undock', 'irobot_create_msgs', 'robot ở dock lúc khởi động → tự undock + ra giữa sân 1 m'],
    ], [4.2, 4.4, 7.4], 'Bảng 3 – Các topic và action.', mono_cols=(0, 1))

    S += [H2('3.2.  Luồng xử lý trong node nhận diện'),
          P('Mỗi khung hình đi qua chuỗi xử lý trên Hình 2. OpenCV đọc webcam ở luồng riêng và luôn lấy khung mới '
            'nhất (bộ đệm 1 khung) nên không bị trễ dồn khi xử lý chậm hơn tốc độ camera. Ảnh được lật gương rồi đưa '
            'vào MediaPipe Gesture Recognizer chạy ở chế độ ' + M('VIDEO') + ': mô hình phát hiện lòng bàn tay định '
            'vị bàn tay, mô hình landmark trả 21 điểm khớp 3D, bộ phân loại cử chỉ (mạng nơ-ron nhỏ trên vector '
            'landmark) trả một trong 7 lớp kèm điểm tin cậy. Chế độ VIDEO dùng lại vị trí tay của khung trước nên '
            'không phải chạy bộ phát hiện ở mọi khung.', True),
          P('Vẫy tay không có trong 7 lớp của mô hình nên được suy ra bằng luật trên landmark (' + M('WaveDetector')
            + '): theo dõi hoành độ tâm lòng bàn tay ở các khung có bàn tay xoè; trong 1,5 s gần nhất có ít nhất 3 '
            'nhịp qua lại, mỗi nhịp dài ít nhất 6 % bề ngang ảnh thì coi là vẫy. Khung có điểm tin cậy dưới 0,55 '
            'được coi là "None". Cuối cùng ' + M('GestureStabilizer') + ' bỏ phiếu trong cửa sổ thời gian: một nhãn '
            'chỉ được công bố khi chiếm ít nhất 70 % số khung trong 0,5 s gần nhất (0,2 s với Open_Palm để dừng '
            'nhanh). Nhãn ổn định được publish ở mọi khung; nếu camera lỗi thì node ngừng publish.')]
    S += br.figure(os.path.join(FIG, 'fig6_pipeline.png'), 'Hình 2 – Xử lý một khung hình trong '
                   'gesture_recognition_node.', 15.5)

    S += [H2('3.3.  Máy trạng thái và nguyên lý điều khiển robot'),
          P('Node hành vi là một máy trạng thái (Hình 3). Cử chỉ chọn (vẫy tay, một ngón, hai ngón) chỉ ghi nhớ '
            'hành vi; ngón cái mới chuyển sang ' + M('EXECUTING') + '. Khi thực hiện, mỗi hành vi là một chuỗi đoạn '
            'chuyển động (vận tốc thẳng v, vận tốc góc ω, đích là quãng đường hoặc góc). ' + M('SegmentRunner')
            + ' publish ' + M('/cmd_vel') + ' 20 Hz và đo tiến độ bằng ' + M('/odom') + ' (không hẹn giờ): đoạn '
            'tiến/lùi kết thúc khi robot đi đủ 0,35 m, đoạn quay khi yaw tích luỹ đủ góc, quỹ đạo tròn khi quay '
            'đủ 360° với v = 0,15 m/s, ω = v/r = 0,3 rad/s. Lệnh được tăng tốc dần và giảm tốc gần đích theo '
            'v ≤ √(2·a·s) (có bù trễ đáp ứng 0,15 s) nên robot không vượt đích; các hành vi đối xứng nên robot '
            'kết thúc gần đúng chỗ và hướng ban đầu.', True)]
    S += br.figure(os.path.join(FIG, 'fig6_states.png'), 'Hình 3 – Máy trạng thái của robot_behavior_node.', 15.0)

    # ===== 4
    S += [H1('4.  Bảng ánh xạ cử chỉ tay và hành vi robot')]
    S += br.table(['Cử chỉ', 'Nhãn (MediaPipe)', 'Hành vi robot', 'Thông số'], [
        ['Vẫy tay', 'Wave (suy ra từ Open_Palm + chuyển động)', 'chọn "chào lại": xoay trái–phải',
         '±0,6 rad, 1 rad/s, 2 lần; ~5 s'],
        ['Giơ 1 ngón tay', 'Pointing_Up', 'chọn tiến–lùi 4 lần', '0,35 m, 0,2 m/s; ~20 s'],
        ['Giơ 2 ngón tay', 'Victory', 'chọn quỹ đạo tròn', 'r = 0,5 m, 0,15 m/s, 1 vòng; ~21 s'],
        ['Giơ ngón cái', 'Thumb_Up', 'xác nhận, thực hiện hành vi đã chọn', 'chỉ khi đã chọn'],
        ['Xoè bàn tay', 'Open_Palm', 'dừng ngay (giữ lựa chọn)', 'giữ 0,2 s; không cooldown'],
        ['Nắm tay', 'Closed_Fist', 'huỷ hành vi, xoá lựa chọn, về chờ', '–'],
        ['(thêm)', 'Thumb_Down, ILoveYou', 'chỉ hiển thị / publish', 'tổng 8 cử chỉ'],
    ], [2.8, 4.4, 4.6, 4.2], 'Bảng 4 – Ánh xạ cử chỉ → hành vi.', mono_cols=(1,))
    S += [P('Đề bài vừa ghi "vẫy tay → robot xoay trái–phải để chào lại" vừa yêu cầu "robot chỉ thực hiện hành vi '
            'sau khi nhận được cử chỉ xác nhận". Mặc định ' + M('wave_requires_confirm: true') + ' thoả cả hai: vẫy '
            'tay chọn hành vi chào, ngón cái xác nhận; đặt ' + M('false') + ' nếu muốn robot chào lại ngay.', True)]

    S += [H2('4.1.  Đáp ứng các yêu cầu an toàn và chống nhiễu')]
    S += br.table(['Yêu cầu', 'Cách thực hiện'], [
        ['Chỉ chạy sau xác nhận', 'cử chỉ chọn chỉ ghi nhớ; Thumb_Up khi chưa chọn bị bỏ qua; chạy xong xoá lựa '
                                  'chọn; lựa chọn hết hạn sau 15 s'],
        ['Không dùng bàn phím', 'mọi lệnh qua /detected_gesture; undock và ra giữa sân tự động'],
        ['Chống nhiễu kích hoạt liên tục', 'ngưỡng tin cậy 0,55; bỏ phiếu ≥ 70 % trong 0,5 s; chỉ phản ứng khi nhãn '
                                           'ổn định ĐỔI (giữ ngón cái lâu vẫn chỉ 1 lệnh); cooldown 1 s mỗi cử chỉ; '
                                           'đang chạy thì bỏ qua cử chỉ chọn / xác nhận'],
        ['Dừng khi có tín hiệu dừng', 'Open_Palm ưu tiên cao nhất → Twist 0 ngay, gửi lặp 5 chu kỳ, huỷ hành vi'],
        ['Dừng khi mất tín hiệu', '&gt; 1 s không có /detected_gesture (node nhận diện tắt, camera lỗi) → dừng, huỷ '
                                  '(SIGNAL_LOST); Ctrl+C node hành vi → gửi Twist 0 trước khi thoát'],
        ['Không va chạm', 'sân 9 m × 9 m trống; hành vi nằm trong bán kính 1,05 m quanh điểm bắt đầu (cách tường '
                          '≥ 2,5 m); LiDAR: vật cản &lt; 0,40 m theo hướng chạy → dừng; ra lệnh mà odom không đổi '
                          '4 s → dừng (kẹt); bước rời dock bị huỷ (còn trong dock hoặc mới lùi ra nửa chừng) → '
                          'xác nhận đầu tiên sẽ rời dock / quay ra xa dock và ra giữa sân trước'],
    ], [4.4, 11.6], 'Bảng 5 – Yêu cầu của đề và cách đáp ứng.')

    # ===== 5
    S += [H1('5.  Kết quả thực nghiệm')]
    imgs = [('gesture_wave.png', 'test6_wave.png', '(a) Wave'),
            ('gesture_pointing.png', 'test6_pointing.png', '(b) Pointing_Up'),
            ('gesture_victory.png', 'test6_victory.png', '(c) Victory'),
            ('gesture_thumb.png', 'test6_thumb.png', '(d) Thumb_Up'),
            ('gesture_palm.png', 'test6_palm.png', '(e) Open_Palm'),
            ('gesture_fist.png', 'test6_fist.png', '(f) Closed_Fist')]
    note = ''
    for i in range(0, 6, 2):
        items = []
        for uname, tname, sub in imgs[i:i + 2]:
            path, n = exp(uname, tname)
            note = note or n
            items.append((path, uname, sub))
        S += br.figure2(items, 'Hình {} – Cửa sổ nhận diện: landmark, tên cử chỉ, độ tin cậy, nhãn ổn định và trạng '
                               'thái robot{}.'.format(4 + i // 2, note), 7.6)
    path, n = exp('gazebo_gesture.png', 'test6_gazebo.png')
    S += br.figure(path, 'Hình 7 – Gazebo và cửa sổ webcam khi robot đang thực hiện hành vi{}.'.format(n), 15.5,
                   placeholder_name='gazebo_gesture.png')
    path, n = exp('trajectory.png', 'test6_trajectory.png')
    S += br.figure(path, 'Hình 8 – Quỹ đạo robot (odom) theo từng hành vi, vẽ bằng plot_gesture_run.py{}.'.format(n),
                   12.5, placeholder_name='trajectory.png')
    S += [P('Ngoài thử nghiệm với webcam, hệ thống được kiểm thử tích hợp tự động: TurtleBot 4 Simulator chạy '
            'thật trong Gazebo (máy ảo không GPU, real-time factor chỉ 0,06), node hành vi nhận chuỗi cử chỉ giống '
            'hệt node nhận diện gửi, script kiểm tra đợi từng chuyển trạng thái và đo vận tốc / vị trí robot từ '
            + M('/odom') + '. Tất cả các bước đều đạt (Bảng 6); số đo lấy từ ' + M('odom.csv') + ' của các lần chạy đó.', True)]
    S += br.table(['Kịch bản (tự động, Gazebo)', 'Kết quả đo'], [
        ['Khởi động ở dock → undock + chạy thẳng 1 m', 'quãng đường 0,999 m, sau đó IDLE'],
        ['Ngón cái khi chưa chọn', 'bỏ qua, robot đứng yên'],
        ['Vẫy tay → ngón cái (chào)', 'xoay +34,9° / −34,2°, kết thúc lệch hướng 0,0°, không dịch chuyển'],
        ['1 ngón → ngón cái (giữ ngón cái thêm 3 s)', 'chỉ 1 lần chạy; 4 lần tiến–lùi 0,34 m, về lệch 1 mm'],
        ['2 ngón → ngón cái → xoè tay ở 30 %', 'STOPPED &lt; 0,6 s, vận tốc về 0; ngón cái → chạy lại'],
        ['Quỹ đạo tròn (sau khi chạy lại)', 'đường kính 1,00 m (r = 0,5 m), điểm cuối cách điểm đầu 1,1 cm'],
        ['1 ngón → ngón cái → nắm tay giữa chừng', 'dừng, IDLE, xoá lựa chọn'],
        ['Đang chạy thì ngừng gửi /detected_gesture', 'SIGNAL_LOST sau ~1 s, robot dừng (vận tốc 0)'],
        ['Ctrl+C node hành vi', 'gửi Twist 0 rồi thoát sạch'],
        ['Xoè tay khi robot mới lùi khỏi dock 0,2 m (còn quay mặt vào dock) → 2 ngón → ngón cái',
         'robot quay ra xa dock, chạy ra giữa sân rồi mới vòng tròn; không lúc nào tiến lại gần dock (8/8 bước)'],
    ], [7.0, 9.0], 'Bảng 6 – Kiểm thử tích hợp tự động trong môi trường ảo.')
    res = info.get('ket_qua') or []
    if res:
        S += br.table(['Thử nghiệm (webcam)', 'Kết quả'], [[str(a), str(b)] for a, b in res], [7.0, 9.0],
                      'Bảng 7 – Kết quả thử nghiệm với webcam.')
    obs = (info.get('nhan_xet') or '').strip()
    if obs:
        S += [P(br.esc(obs), True)]

    # ===== 6
    S += [H1('6.  Nhận xét và giới hạn'),
          P('MediaPipe nhận ổn định các cử chỉ tĩnh rõ ràng (nắm tay, xoè tay, ngón cái, một ngón, hai ngón) khi đủ '
            'sáng và bàn tay cách webcam khoảng 0,4–1 m; độ tin cậy giảm khi bàn tay nghiêng, bị che hoặc nền lẫn màu '
            'da. Bộ lọc thời gian làm chậm phản hồi khoảng 0,2–0,5 s nhưng loại được các khung nhận nhầm lẻ tẻ. Vẫy '
            'tay là luật tự đặt trên landmark nên phụ thuộc biên độ, tốc độ vẫy và FPS (cần khoảng 10 FPS trở lên – khi máy '
            'quá tải, chuyển động bị lấy mẫu thiếu và không nhận được); vì vẫy tay bắt đầu bằng bàn tay xoè, '
            'vẫy khi robot đang chạy sẽ làm robot dừng – chấp nhận để lệnh dừng luôn được ưu tiên.', True),
          P('Robot chạy vòng hở theo odometry (không dùng bản đồ / Nav2) nên sai số tích luỹ theo thời gian; an '
            'toàn va chạm dựa vào sân trống, kích thước hành vi nhỏ và lớp kiểm tra LiDAR theo hướng chạy (không áp '
            'dụng khi quay tại chỗ). Khi mô phỏng chạy chậm hơn thời gian thực, hành vi kéo dài hơn nhưng quãng đường '
            'và góc quay vẫn đúng vì được đo bằng odometry.')]
    return S


def make_cover(path):
    base = os.path.join(HERE, 'assets', 'cover_base.pdf')
    ov = os.path.join(HERE, 'assets', '_cover_overlay6.pdf')
    c = rl_canvas.Canvas(ov, pagesize=A4)
    c.setFillColor(colors.white)
    c.rect(82, 300, 432, 60, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont('Serif-B', 15.5)
    c.drawCentredString(A4[0] / 2, 338, 'BÀI THỰC HÀNH SỐ 6')
    c.setFont('Serif', 12.5)
    c.drawCentredString(A4[0] / 2, 316, 'Giao tiếp phi ngôn ngữ: điều khiển TurtleBot 4 bằng cử chỉ tay')
    c.save()
    page = PdfReader(base).pages[0]
    page.merge_page(PdfReader(ov).pages[0])
    w = PdfWriter()
    w.add_page(page)
    with open(path, 'wb') as f:
        w.write(f)
    os.remove(ov)


def main():
    info = br.load_info()
    body_pdf = os.path.join(HERE, '_body6.pdf')
    cover_pdf = os.path.join(HERE, '_cover6.pdf')
    doc = br.Doc(body_pdf, pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.3 * cm,
                 bottomMargin=2.4 * cm, title=TITLE, author=str(info.get('ho_ten') or 'Lê Trọng Nghĩa'))
    doc.multiBuild(br.fix_orphans(br.group_floats(content(info)), doc.width))
    make_cover(cover_pdf)
    w = PdfWriter()
    for src in (cover_pdf, body_pdf):
        for pg in PdfReader(src).pages:
            w.add_page(pg)
    w.add_metadata({'/Title': TITLE, '/Author': str(info.get('ho_ten') or 'Lê Trọng Nghĩa')})
    with open(OUT, 'wb') as f:
        w.write(f)
    os.remove(body_pdf)
    os.remove(cover_pdf)
    print('Đã tạo:', OUT, '({} trang)'.format(len(PdfReader(OUT).pages)))
    miss = sorted(set(br.MISSING))
    if miss:
        print('CÒN THIẾU:', ', '.join(miss))
    if TEST_USED:
        print('CẢNH BÁO: đang dùng ảnh KIỂM THỬ (môi trường ảo) cho: {} – chép ảnh của bạn vào docs/report/fig_user/ '
              'trước khi nộp.'.format(', '.join(sorted(set(TEST_USED)))))


if __name__ == '__main__':
    main()
