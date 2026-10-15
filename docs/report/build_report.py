#!/usr/bin/env python3
"""Dựng báo cáo PDF "Bài thực hành TurtleBot 4: Localization, Nav2 và YOLO" (theo bố cục báo cáo bài 4).

    python3 docs/report/diagrams.py        # vẽ lại sơ đồ khối (docs/report/fig/*.png) – chỉ khi cần
    python3 docs/report/build_report.py    # -> docs/report/BaoCao_Bai5_TurtleBot4_Nav2_YOLO.pdf

Ảnh chụp màn hình của bạn đặt trong docs/report/fig_user/ (thiếu ảnh nào thì PDF chèn khung "CHƯA CÓ ẢNH"):
    gazebo_world.png        Gazebo: world maze + vật thể, robot trong dock
    rviz_localization.png   RViz2: bản đồ, LiDAR trùng tường, hạt AMCL
    rviz_navigation.png     RViz2 khi robot đang đi: /plan, costmap, marker G1..G3
    yolo_window.png, goals_map.png, run_map.png, terminal_navigator.png  (đã có)
Họ tên / MSSV / link: docs/report_info.yaml (ho_ten, mssv, link_video, link_github).
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yaml
from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (Flowable, BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph,
                                Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, 'fig')
USER = os.path.join(HERE, 'fig_user')
OUT = os.path.join(HERE, 'BaoCao_Bai5_TurtleBot4_Nav2_YOLO.pdf')
BLUE = colors.HexColor('#1f4e79')
GREY = colors.HexColor('#666666')
RED = colors.HexColor('#b22222')

MISSING = []


# ------------------------------------------------------------------------------------------------ phông chữ
def register_fonts():
    cands = [
        ('/usr/share/fonts/truetype/liberation', ['LiberationSerif-Regular.ttf', 'LiberationSerif-Bold.ttf',
                                                  'LiberationSerif-Italic.ttf', 'LiberationSerif-BoldItalic.ttf',
                                                  'LiberationSans-Bold.ttf', 'LiberationMono-Regular.ttf']),
        ('/usr/share/fonts/truetype/dejavu', ['DejaVuSerif.ttf', 'DejaVuSerif-Bold.ttf', 'DejaVuSerif-Italic.ttf',
                                              'DejaVuSerif-BoldItalic.ttf', 'DejaVuSans-Bold.ttf',
                                              'DejaVuSansMono.ttf']),
    ]
    for d, files in cands:
        paths = [os.path.join(d, f) for f in files]
        if all(os.path.isfile(p) for p in paths):
            for name, p in zip(['Serif', 'Serif-B', 'Serif-I', 'Serif-BI', 'Sans-B', 'Mono'], paths):
                pdfmetrics.registerFont(TTFont(name, p))
            pdfmetrics.registerFontFamily('Serif', normal='Serif', bold='Serif-B', italic='Serif-I',
                                          boldItalic='Serif-BI')
            return
    sys.exit('Thiếu phông Liberation hoặc DejaVu: sudo apt install fonts-liberation fonts-dejavu-core')


register_fonts()

body = ParagraphStyle('body', fontName='Serif', fontSize=11, leading=14.6, alignment=TA_JUSTIFY,
                      firstLineIndent=0.7 * cm, spaceAfter=3.2)
body0 = ParagraphStyle('body0', parent=body, firstLineIndent=0)
h1 = ParagraphStyle('h1', fontName='Sans-B', fontSize=15, leading=19, textColor=BLUE, spaceBefore=16,
                    spaceAfter=9, keepWithNext=0)
h2 = ParagraphStyle('h2', fontName='Sans-B', fontSize=11.5, leading=15, textColor=BLUE, spaceBefore=11,
                    spaceAfter=6, keepWithNext=0)
cap = ParagraphStyle('cap', fontName='Serif-I', fontSize=9.6, leading=12, textColor=GREY, alignment=TA_CENTER,
                     spaceBefore=4, spaceAfter=12)
cell = ParagraphStyle('cell', fontName='Serif', fontSize=9.6, leading=11.6, alignment=TA_LEFT)
cellh = ParagraphStyle('cellh', parent=cell, fontName='Serif-B', textColor=colors.white)
codest = ParagraphStyle('code', fontName='Mono', fontSize=8.2, leading=10.6)
toc_title = ParagraphStyle('toct', fontName='Sans-B', fontSize=15, leading=19, textColor=BLUE, spaceAfter=14)


def M(t):
    """Đoạn mã / tên topic trong văn bản."""
    return '<font name="Mono" size="9.4">{}</font>'.format(t)


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ------------------------------------------------------------------------------------------------ thành phần
def P(text, first=False):
    return Paragraph(text, body0 if first else body)


def H1(text):
    return Paragraph(text, h1)


def H2(text):
    return Paragraph(text, h2)


def code(text):
    t = Table([[Preformatted(text.strip('\n'), codest)]], colWidths=[16.0 * cm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f2f2f2')),
                           ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                           ('LEFTPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 5),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    return [Spacer(1, 3), t, Spacer(1, 7)]


def table(header, rows, widths, caption, mono_cols=()):
    def c(txt, j, head=False):
        if head:
            return Paragraph(txt, cellh)
        if j in mono_cols:
            return Paragraph('<font name="Mono" size="8.2">{}</font>'.format(txt), cell)
        return Paragraph(txt, cell)

    data = [[c(h, j, True) for j, h in enumerate(header)]] + [[c(x, j) for j, x in enumerate(r)] for r in rows]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), BLUE),
                           ('LINEABOVE', (0, 0), (-1, 0), 0.9, colors.black),
                           ('LINEBELOW', (0, -1), (-1, -1), 0.9, colors.black),
                           ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('TOPPADDING', (0, 0), (-1, -1), 2.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.6),
                           ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5)]))
    if len(rows) < 6:
        return [KeepTogether([t, Paragraph(caption, cap)])]
    return [t, Paragraph(caption, cap)]


def _img(path, width_cm, crop=None):
    if os.path.basename(path) == 'yolo_window.png':        # bỏ thanh công cụ và dòng toạ độ chuột của cửa sổ
        with PILImage.open(path) as im:
            w, h = im.size
            out = os.path.join(FIG, '_yolo_window_crop.png')
            im.crop((0, 40, w, h - 24)).save(out)
        path = out
    with PILImage.open(path) as im:
        w, h = im.size
    return Image(path, width=width_cm * cm, height=width_cm * cm * h / w)


def placeholder(name, width_cm, ratio=0.62):
    MISSING.append(name)
    t = Table([[Paragraph('<font color="#b22222"><b>CHƯA CÓ ẢNH</b><br/>chép ảnh chụp màn hình vào<br/>'
                          '<font name="Mono" size="8">docs/report/fig_user/{}</font></font>'.format(name),
                          ParagraphStyle('ph', fontName='Serif', fontSize=9.5, leading=12, alignment=TA_CENTER))]],
              colWidths=[width_cm * cm], rowHeights=[width_cm * cm * ratio])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.8, RED), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff5f5'))]))
    return t


def user_or_placeholder(name, width_cm, ratio=0.62):
    p = os.path.join(USER, name)
    return _img(p, width_cm) if os.path.isfile(p) else placeholder(name, width_cm, ratio)


class FigBlock(Flowable):
    """Hình + chú thích; co hình tới MIN_SCALE để lấp chỗ trống cuối trang thay vì đẩy sang trang mới."""
    MIN_SCALE = 0.62

    def __init__(self, body, caption):
        super().__init__()
        self.body, self.capp = body, Paragraph(caption, cap)
        self.scale = 1.0

    def wrap(self, aw, ah):
        bw, bh = self.body.wrap(aw, 10000)
        cw, ch = self.capp.wrap(aw, 10000)
        self._bw, self._bh, self._ch = bw, bh, ch + cap.spaceBefore + cap.spaceAfter
        room = ah - self._ch - 4
        self.scale = 1.0 if bh <= room else max(min(room / bh, 1.0), 0)
        if self.scale < self.MIN_SCALE:
            self.scale = 1.0
        self.width = aw
        self.height = 4 + bh * self.scale + self._ch
        return aw, self.height

    def draw(self):
        c = self.canv
        bh = self._bh * self.scale
        c.saveState()
        c.translate((self.width - self._bw * self.scale) / 2, self._ch)
        c.scale(self.scale, self.scale)
        self.body.drawOn(c, 0, 0)
        c.restoreState()
        self.capp.drawOn(c, 0, self._ch - cap.spaceBefore - self.capp.height)


def figure(path, caption, width_cm=15.5, placeholder_name=None):
    if path and os.path.isfile(path):
        im = _img(path, width_cm)
    else:
        im = placeholder(placeholder_name or os.path.basename(path or '?'), width_cm)
    im.hAlign = 'LEFT'
    return [FigBlock(im, caption)]


def figure2(items, caption, width_cm=7.6):
    """Hai ảnh cạnh nhau, mỗi ảnh có chú thích (a)(b). items = [(đường dẫn|None, tên_ảnh_user, chú thích con)]."""
    row_im, row_cap = [], []
    for path, uname, sub in items:
        row_im.append(_img(path, width_cm) if path and os.path.isfile(path)
                      else user_or_placeholder(uname, width_cm, 0.75))
        row_cap.append(Paragraph(sub, ParagraphStyle('sub', parent=cap, spaceAfter=2, spaceBefore=3)))
    t = Table([row_im, row_cap], colWidths=[8.0 * cm] * len(items))
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, 0), 'MIDDLE'), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    return [FigBlock(t, caption)]


_EQ = {'n': 0}


def _eq_table(path, number):
    with PILImage.open(path) as im:
        w, h = im.size
    scale = 72.0 / 300 * 0.86
    t = Table([['', Image(path, width=w * scale, height=h * scale),
                Paragraph('({})'.format(number), ParagraphStyle('en', fontName='Serif', fontSize=11, alignment=2))]],
              colWidths=[1.2 * cm, 13.6 * cm, 1.2 * cm])
    t.setStyle(TableStyle([('ALIGN', (1, 0), (1, 0), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    return [Spacer(1, 2), t, Spacer(1, 4)]


def equation(latex, number, fontsize=13):
    _EQ['n'] += 1
    path = os.path.join(FIG, 'eq_{}.png'.format(_EQ['n']))
    fig = plt.figure(figsize=(0.1, 0.1))
    fig.text(0, 0, '${}$'.format(latex), fontsize=fontsize)
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.04, transparent=True)
    plt.close(fig)
    return _eq_table(path, number)


def equation_cases(lhs, rows, number, fontsize=13):
    """Hàm nhiều nhánh (mathtext không có môi trường cases): vẽ dấu ngoặc nhọn và từng dòng bằng tay."""
    _EQ['n'] += 1
    path = os.path.join(FIG, 'eq_{}.png'.format(_EQ['n']))
    n = len(rows)
    fig = plt.figure(figsize=(4.6, 0.36 * n + 0.1))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 4.6)
    ax.set_ylim(0, n)
    ax.axis('off')
    ax.text(0.0, n / 2, '${}$'.format(lhs), fontsize=fontsize, va='center')
    ax.text(0.78, n / 2, '$\\left\\{\\right.$' if False else '{', fontsize=fontsize * 2.6 * n / 3.0, va='center',
            ha='center', family='DejaVu Sans', fontweight='light')
    for i, (expr, cond) in enumerate(rows):
        y = n - i - 0.5
        ax.text(1.05, y, '${}$'.format(expr), fontsize=fontsize, va='center')
        ax.text(3.0, y, '${}$'.format(cond), fontsize=fontsize, va='center')
    fig.savefig(path, dpi=300, bbox_inches='tight', pad_inches=0.04, transparent=True)
    plt.close(fig)
    return _eq_table(path, number)


# ------------------------------------------------------------------------------------------------ tài liệu
class Doc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='f', leftPadding=0,
                      rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id='main', frames=[frame], onPage=self._footer)])

    @staticmethod
    def _footer(c, doc):
        c.saveState()
        c.setFont('Serif', 10.5)
        c.drawCentredString(A4[0] / 2, 1.25 * cm, str(doc.page))
        c.restoreState()

    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and fl.style.name in ('h1', 'h2'):
            level = 0 if fl.style.name == 'h1' else 1
            key = 'k{}'.format(id(fl))
            self.canv.bookmarkPage(key)
            self.notify('TOCEntry', (level, fl.getPlainText(), self.page, key))


def load_info():
    info = {}
    p = os.path.join(HERE, '..', 'report_info.yaml')
    try:
        with open(p, encoding='utf-8') as f:
            info = yaml.safe_load(f) or {}
    except OSError:
        pass
    return info


# ------------------------------------------------------------------------------------------------ nội dung
def content(info):
    S = []
    toc = TableOfContents()
    toc.dotsMinLevel = 0
    toc.levelStyles = [
        ParagraphStyle('t0', fontName='Serif-B', fontSize=11, leading=14.5, leftIndent=0, spaceBefore=7,
                       firstLineIndent=0),
        ParagraphStyle('t1', fontName='Serif', fontSize=11, leading=14, leftIndent=0.95 * cm, firstLineIndent=0),
    ]
    S += [Paragraph('MỤC LỤC', toc_title), toc, PageBreak()]

    # ===== 1
    S += [H1('1.  Cấu trúc chương trình'), H2('1.1.  Môi trường và tổ chức package')]
    S += [P('Bài thực hành được thực hiện trên Ubuntu 22.04, ROS 2 Humble và Ignition Gazebo Fortress, chạy trên '
            'cùng máy Acer Nitro AN515-57 (12 luồng CPU, 15 GB RAM, đồ hoạ Intel UHD qua Mesa) như bài trước. Robot '
            'là TurtleBot 4 Standard gồm đế iRobot Create 3, LiDAR RPLIDAR 2D và camera OAK-D, đặt trong world '
            + M('maze') + ' kích thước khoảng 20 m × 20 m. Bản đồ dùng lại của tuần trước (' + M('maps/map.yaml')
            + ', ' + M('map.pgm') + '): lưới 404 × 403 ô, độ phân giải 0,05 m/ô, gốc toạ độ (−10; −10,1) m.', True),
          P('Chương trình được tổ chức thành package ' + M('tb4_lab04') + ' (ament_cmake), kế thừa package của bài '
            'trước. Package không viết lại mô phỏng hay Nav2 mà dùng các launch chính thức của TurtleBot 4 và '
            'Navigation2; phần bổ sung gồm hai node ứng dụng (điều hướng qua danh sách goal và nhận diện YOLO), '
            'script thêm vật thể vào mô phỏng và các công cụ kiểm tra (Bảng 1).')]
    S += table(['Thư mục / file', 'Nội dung'], [
        ['launch/navigation.launch.py', 'Phần 1: Gazebo, TurtleBot 4, thêm vật thể, nạp bản đồ, AMCL, Nav2, RViz2'],
        ['launch/yolo.launch.py', 'node YOLO chạy riêng (tham số yolo_model, conf, device, show_window)'],
        ['launch/demo.launch.py', 'tất cả trong một lệnh: navigation + YOLO + node điều hướng'],
        ['scripts/waypoint_navigator.py', 'node điều hướng tự động G1 → G2 → G3 (nav2_simple_commander)'],
        ['scripts/yolo_detector.py', 'node nhận diện vật thể (cv_bridge + ultralytics YOLO)'],
        ['scripts/spawn_objects.py', 'tải model từ Gazebo Fuel và đặt vào world lúc chạy'],
        ['scripts/check_goals.py', 'kiểm tra goal (cách tường, tới được, camera nhìn thấy vật thể) và vẽ ảnh '
                                      'bản đồ, quỹ đạo, vị trí phát hiện'],
        ['scripts/goal_recorder.py', 'ghi toạ độ từ Publish Point (/clicked_point) hoặc /amcl_pose ra YAML'],
        ['scripts/localization_check.py', 'đo độ khớp giữa tia LiDAR và tường của bản đồ'],
        ['scripts/doctor.sh', 'kiểm tra môi trường, thư viện YOLO (numpy, cv_bridge, ultralytics)'],
        ['config/', 'goals.yaml, objects.yaml, yolo.yaml, localization.yaml, nav2.yaml (và cấu hình bài trước)'],
        ['maps/', 'map.yaml, map.pgm của tuần trước'],
        ['rviz/, test/', 'cấu hình RViz2 (panel ảnh YOLO, marker goal); kiểm thử đơn vị cho phần không phụ '
                            'thuộc ROS'],
    ], [6.0, 10.0], 'Bảng 1 – Cấu trúc package <font name="Mono" size="9">tb4_lab04</font>.', mono_cols=(0,))

    S += [H2('1.2.  Sơ đồ khối'),
          P('Sơ đồ khối của hệ thống được trình bày ở Hình 1, gồm năm tầng. Tầng dưới cùng là Gazebo mô phỏng world '
            + M('maze') + ' cùng các vật thể thêm vào (người, xe, ghế, trụ cứu hoả, bình chữa cháy), LiDAR, camera '
            'OAK-D, bánh vi sai và đế sạc. Tầng robot gồm ' + M('ros_gz_bridge') + ' chuyển dữ liệu giữa Gazebo và '
            'ROS 2, bộ điều khiển vi sai ' + M('diffdrive_controller') + ' phát odometry, và node ' + M('motion_control')
            + ' của Create 3 nhận lệnh vận tốc. Tầng định vị và dẫn đường gồm ' + M('map_server') + ' (nạp bản đồ '
            'tuần trước), ' + M('amcl') + ' (định vị trên bản đồ đó) và Nav2 (lập kế hoạch, điều khiển). Tầng bổ sung '
            'của package gồm node điều hướng ' + M('waypoint_navigator.py') + ' đóng vai trò client của Nav2 và node '
            + M('yolo_detector.py') + ' đọc ảnh camera. Trên cùng là người dùng, quan sát qua RViz2, terminal và cửa '
            'sổ OpenCV; người dùng không điều khiển robot trong lúc node điều hướng chạy.', True)]
    S += figure(os.path.join(FIG, 'fig_system.png'),
                'Hình 1 – Sơ đồ khối hệ thống (xanh: gói chính thức; cam: bổ sung của package <font name="Mono" '
                'size="9">tb4_lab04</font>).', 16.0)
    S += [P('Hai luồng dữ liệu độc lập chạy song song. Luồng điều hướng: node điều hướng gửi action '
            + M('NavigateToPose') + ' tới ' + M('bt_navigator') + '; Nav2 lập đường đi, sinh ' + M('/cmd_vel')
            + ' đưa tới ' + M('motion_control') + '. Luồng nhận diện: ảnh ' + M('/oakd/rgb/preview/image_raw')
            + ' đi qua ' + M('yolo_detector.py') + ' và trả ảnh đã vẽ khung ra cửa sổ OpenCV, ' + M('/yolo/image_annotated')
            + ' (xem trên RViz2) và ' + M('/yolo/detections') + '. Hai luồng chỉ gặp nhau ở vị trí robot: node YOLO '
            'ghi lại vị trí AMCL của robot lúc phát hiện từng vật thể để vẽ lên bản đồ.')]

    S += [H2('1.3.  Trình tự khởi động'),
          P('Nav2 và AMCL chỉ khởi động ổn định khi Gazebo đã chạy xong; khởi động cùng lúc trên máy đang tải nặng '
            'dễ làm các lifecycle node không kết nối được với nhau. Vì vậy các launch được thiết kế theo trình tự '
            'trên Hình 2. Trước tiên, launch kiểm tra gói ROS và bản đồ cần thiết; nếu thiếu thì in rõ thiếu gì và '
            'dừng, không khởi chạy nửa vời. Sau khi Gazebo, TurtleBot 4 và RViz2 khởi động, node ' + M('wait_for_sim.py')
            + ' chờ đến khi đồng hồ mô phỏng ' + M('/clock') + ' chạy ít nhất 2 s và đã có ' + M('/odom') + '. Khi node này '
            'thoát, ' + M('spawn_objects.py') + ' đặt 7 vật thể vào world, ' + M('map_server') + ', ' + M('amcl') + ', '
            + M('scan_delay') + ' và ' + M('dock_obstacle') + ' khởi động sau 2 s, Nav2 sau 8 s (hai tham số '
            + M('localization_delay') + ' và ' + M('nav2_delay') + '). Với ' + M('demo.launch.py') + ', node YOLO và node '
            'điều hướng chạy sau ' + M('navigator_delay') + ' = 25 s; ngoài ra node điều hướng còn tự chờ ' + M('amcl')
            + ' và ' + M('bt_navigator') + ' ở trạng thái active, nên máy chậm hơn dự kiến vẫn không gửi goal quá '
            'sớm.', True)]
    S += figure(os.path.join(FIG, 'fig_startup.png'), 'Hình 2 – Trình tự khởi động của <font name="Mono" '
                'size="9">demo.launch.py</font>.', 16.0)

    S += [H2('1.4.  Cây toạ độ'),
          P('Cây biến đổi toạ độ (TF) được thể hiện trên Hình 3. Biến đổi ' + M('odom→base_link') + ' do '
            + M('diffdrive_controller') + ' tính từ odometry bánh xe, liên tục nhưng trôi dần theo quãng đường. '
            + M('amcl') + ' bù sai số này bằng biến đổi ' + M('map→odom') + ', nhờ đó ' + M('map→base_link') + ' là '
            'pose đã hiệu chỉnh của robot trên bản đồ. Các biến đổi từ ' + M('base_link') + ' tới cảm biến là biến đổi '
            'tĩnh do ' + M('robot_state_publisher') + ' phát từ mô tả URDF. Frame ' + M('map') + ' của bản đồ tuần '
            'trước trùng với frame của world Gazebo (robot sinh ra tại (0, 0, 0) khi đang trong dock), nên toạ độ '
            'đọc từ bản đồ có thể dùng trực tiếp làm vị trí trong mô phỏng.', True)]
    S += figure(os.path.join(FIG, 'fig_tf.png'), 'Hình 3 – Cây TF và node phát từng biến đổi.', 9.2)

    S += [H2('1.5.  Các quyết định thiết kế đáng chú ý'),
          P('Phần lớn cấu hình giữ theo bản gốc của TurtleBot 4 và của bài trước. Các điểm bổ sung hoặc thay đổi '
            'trong bài này, cùng lý do, được liệt kê ở Bảng 2.', True)]
    S += table(['Quyết định', 'Lý do'], [
        ['Đặt vật thể lúc chạy bằng <font name="Mono" size="8.6">ros_gz_sim create</font>, không tạo world mới',
         'launch của TurtleBot 4 ghi đè <font name="Mono" size="8.6">IGN_GAZEBO_RESOURCE_PATH</font> và các topic '
         'cầu nối phụ thuộc tên world; world mới dễ làm hỏng cầu nối và không còn là đúng môi trường tuần trước. '
         'Thêm vật thể vào world <font name="Mono" size="8.6">maze</font> gốc giữ nguyên tường và vị trí dock nên '
         'bản đồ cũ dùng lại được'],
        ['AMCL khởi tạo tại (0, 0, 0); node điều hướng chỉ phát lại <font name="Mono" size="8.6">/initialpose</font>'
         ' khi robot còn trong dock',
         'pose (0, 0, 0) chỉ đúng khi robot ở dock. Chạy lại giữa mê cung thì giữ ước lượng hiện có của AMCL, '
         'không ghi đè bằng pose cũ'],
        ['Tự viết bước undock (giới hạn 60 s theo giờ mô phỏng)',
         'có giới hạn thời gian rõ ràng, theo đồng hồ mô phỏng, và không phụ thuộc gói <font name="Mono" '
         'size="8.6">turtlebot4_navigation</font>'],
        ['Giữ <font name="Mono" size="8.6">/scan_nav</font> (<font name="Mono" size="8.6">/scan</font> trễ 0,1 s) '
         'và <font name="Mono" size="8.6">dock_obstacle</font> của bài trước',
         'tránh lỗi TF khi scan đến trước biến đổi tương ứng; dock thấp hơn mặt phẳng quét LiDAR nên phải đưa vào '
         'costmap để Nav2 không lập đường xuyên qua dock'],
        ['Ghim <font name="Mono" size="8.6">numpy&lt;2</font> và <font name="Mono" size="8.6">opencv-python'
         '&lt;4.11</font>',
         '<font name="Mono" size="8.6">cv_bridge</font> của Humble được biên dịch với NumPy 1.x; lệnh '
         '<font name="Mono" size="8.6">pip install ultralytics opencv-python</font> theo đề kéo NumPy 2 về và làm '
         'hỏng chuyển đổi ảnh'],
        ['Ctrl+C huỷ goal đang chạy trước khi thoát',
         'để robot dừng hẳn thay vì tiếp tục đi theo goal cũ; kết quả đã chạy vẫn được lưu'],
    ], [6.2, 9.8], 'Bảng 2 – Các quyết định thiết kế và lý do.')

    # ===== 2
    S += [H1('2.  Các node và package chính'),
          P('Các node tham gia hệ thống được liệt kê trong Bảng 3. Ngoài các gói chính thức, package '
            + M('tb4_lab04') + ' bổ sung năm thành phần chạy kèm launch. Node ' + M('wait_for_sim.py') + ' quyết định '
            'thời điểm bật tầng định vị và Nav2. Node ' + M('dock_obstacle.py') + ' đưa thân dock vào costmap. Node '
            + M('spawn_objects.py') + ' đặt vật thể vào Gazebo. Hai node ứng dụng chính là ' + M('waypoint_navigator.py')
            + ' (Phần 3) và ' + M('yolo_detector.py') + ' (Phần 4).', True)]
    S += table(['Package', 'Node', 'Vai trò'], [
        ['ros_gz_sim', 'ign gazebo, create', 'mô phỏng vật lý và cảm biến; đặt vật thể'],
        ['ros_gz_bridge', 'parameter_bridge', 'chuyển topic giữa Gazebo và ROS 2 (/scan, camera, /clock...)'],
        ['robot_state_publisher', 'robot_state_publisher', 'phát TF tĩnh của robot từ URDF'],
        ['ros2_control', 'diffdrive_controller', 'điều khiển vi sai, phát /odom và TF odom→base_link'],
        ['irobot_create_nodes', 'motion_control', 'nhận /cmd_vel, áp giới hạn an toàn, thực hiện dock/undock'],
        ['nav2_map_server', 'map_server', 'nạp map.yaml / map.pgm và phát /map'],
        ['nav2_amcl', 'amcl', 'định vị trên bản đồ, phát TF map→odom và /amcl_pose'],
        ['nav2_bt_navigator', 'bt_navigator', 'nhận action NavigateToPose, điều phối bằng cây hành vi'],
        ['nav2_planner', 'planner_server', 'lập đường đi toàn cục (NavFn)'],
        ['nav2_controller', 'controller_server', 'bám đường đi, sinh lệnh vận tốc (DWB)'],
        ['nav2_behaviors', 'behavior_server', 'hành vi phục hồi: quay tại chỗ, lùi, chờ'],
        ['nav2_velocity_smoother', 'velocity_smoother', 'giới hạn vận tốc và gia tốc'],
        ['nav2_lifecycle_manager', 'lifecycle_manager', 'cấu hình và kích hoạt các node Nav2 theo thứ tự'],
        ['topic_tools', 'delay (scan_delay)', 'tạo /scan_nav = /scan trễ 0,1 s'],
        ['tb4_lab04', 'wait_for_sim, dock_obstacle, spawn_objects', 'chờ mô phỏng; dock vào costmap; đặt vật thể'],
        ['tb4_lab04', 'waypoint_navigator', 'gửi G1, G2, G3 tới Nav2 và tổng kết kết quả'],
        ['tb4_lab04', 'yolo_detector', 'nhận diện vật thể từ camera, vẽ khung, lưu kết quả'],
        ['rviz2', 'rviz2', 'hiển thị bản đồ, LiDAR, hạt AMCL, đường đi, ảnh YOLO; công cụ Publish Point'],
    ], [4.6, 4.4, 7.0], 'Bảng 3 – Các node và package chính.', mono_cols=(0, 1))

    # ===== 3
    S += [H1('3.  Các topic và action chính'),
          P('Bảng 4 tóm tắt các topic và action chính. Trong Phần 1, ' + M('/map') + ' do ' + M('map_server')
            + ' phát một lần, ' + M('/scan_nav') + ' vào ' + M('amcl') + ' và các costmap, còn TF ' + M('map→odom')
            + ' do AMCL phát. Trong Phần 3, node điều hướng gửi đích qua action ' + M('/navigate_to_pose') + ' và nhận '
            'phản hồi gồm khoảng cách còn lại, thời gian ước tính và số lần phục hồi; Nav2 phát đường đi ' + M('/plan')
            + ' và lệnh vận tốc ' + M('/cmd_vel') + '. Trong Phần 4, ảnh vào qua ' + M('/oakd/rgb/preview/image_raw')
            + ' (rgb8, 320 × 240) và kết quả ra qua hai topic ' + M('/yolo/*') + '.', True)]
    S += table(['Topic / action', 'Kiểu', 'Vai trò'], [
        ['/scan', 'sensor_msgs/LaserScan', 'khoảng cách từ RPLIDAR; nguồn của /scan_nav'],
        ['/scan_nav', 'sensor_msgs/LaserScan', '/scan trễ 0,1 s; vào AMCL và costmap'],
        ['/odom', 'nav_msgs/Odometry', 'odometry bánh xe từ diffdrive_controller'],
        ['/map', 'nav_msgs/OccupancyGrid', 'bản đồ do map_server phát (QoS transient local)'],
        ['/initialpose', 'geometry_msgs/<br/>PoseWithCovarianceStamped', 'pose ban đầu cho AMCL (node điều hướng hoặc RViz2)'],
        ['/amcl_pose', 'geometry_msgs/<br/>PoseWithCovarianceStamped', 'pose ước lượng của robot trong frame map'],
        ['/navigate_to_pose', 'action nav2_msgs/<br/>NavigateToPose', 'đích điều hướng; feedback: distance_remaining, '
                                                                   'estimated_time_remaining, number_of_recoveries'],
        ['/plan', 'nav_msgs/Path', 'đường đi toàn cục do planner_server lập'],
        ['/cmd_vel', 'geometry_msgs/Twist', 'lệnh vận tốc tới motion_control'],
        ['/undock, /dock', 'action irobot_create_msgs/<br/>Undock, Dock', 'rời và vào đế sạc'],
        ['/dock_status', 'irobot_create_msgs/<br/>DockStatus', 'robot có đang trong dock không (quyết định initial pose)'],
        ['/clicked_point', 'geometry_msgs/<br/>PointStamped', 'điểm bấm bằng Publish Point trên RViz2 (khảo sát goal)'],
        ['/oakd/rgb/preview/image_raw', 'sensor_msgs/Image', 'ảnh RGB từ camera OAK-D (đầu vào YOLO)'],
        ['/yolo/image_annotated', 'sensor_msgs/Image', 'ảnh đã vẽ khung, xem trên RViz2'],
        ['/yolo/detections', 'vision_msgs/<br/>Detection2DArray', 'danh sách vật thể phát hiện (lớp, độ tự tin, khung)'],
        ['/nav_goals/markers', 'visualization_msgs/<br/>MarkerArray', 'marker G1–G3, đổi màu theo trạng thái'],
    ], [5.2, 4.6, 6.2], 'Bảng 4 – Các topic và action chính.', mono_cols=(0, 1))

    # ===== 4
    S += [H1('4.  Khởi chạy mô phỏng, nạp bản đồ và định vị (Phần 1)'), H2('4.1.  World maze và các vật thể thêm vào'),
          P('Robot được khởi chạy lại trong đúng world ' + M('maze') + ' đã dùng để quét bản đồ, tại cùng vị trí '
            'xuất phát (robot đỗ trong dock ở (0, 0, 0)). Để bài toán nhận diện có đối tượng, bảy vật thể được thêm '
            'vào world lúc chạy (Bảng 5). Model lấy từ Gazebo Fuel (cần Internet ở lần đầu, sau đó dùng bản lưu '
            'trong ' + M('~/.ignition/fuel') + '), đặt bằng ' + M('ros_gz_sim create') + '. Toạ độ vật thể nằm trong '
            'frame của world, chính là frame ' + M('map') + ' của bản đồ. Mỗi vật thể được đặt ở khu vực khác nhau '
            'để ba goal có góc nhìn riêng.', True)]
    S += table(['Vật thể', 'Model Fuel', 'x (m)', 'y (m)', 'Lớp COCO kỳ vọng'], [
        ['car_1', 'Hatchback blue', '−8,70', '7,20', 'car'],
        ['person_1', 'Standing person', '−3,90', '2,40', 'person'],
        ['person_2', 'Casual female', '−6,00', '−5,60', 'person'],
        ['chair_1', 'Chair', '−4,75', '−5,25', 'chair'],
        ['fire_hydrant_1', 'Fire hydrant', '8,60', '−1,00', 'fire hydrant'],
        ['person_3', 'Male visitor', '9,00', '−2,60', 'person'],
        ['fire_extinguisher_1', 'Fire Extinguisher', '8,30', '−3,30', 'không có trong COCO'],
    ], [3.9, 4.0, 2.0, 2.0, 4.1], 'Bảng 5 – Vật thể thêm vào world <font name="Mono" size="9">maze</font>.',
        mono_cols=(0,))
    S += code('''
ros2 run tb4_lab04 spawn_objects.py --download-only   # tải model Fuel (lần đầu)
ros2 launch tb4_lab04 navigation.launch.py            # Gazebo + vật thể + AMCL + Nav2
''')

    S += [H2('4.2.  Nạp bản đồ và AMCL'),
          P('Node ' + M('map_server') + ' nạp ' + M('maps/map.yaml') + ' (ảnh ' + M('map.pgm') + ', ngưỡng '
            + M('occupied_thresh') + ' = 0,65 và ' + M('free_thresh') + ' = 0,15) rồi phát ' + M('/map') + '. AMCL '
            '(Adaptive Monte Carlo Localization) ước lượng pose của robot trên bản đồ đó bằng bộ lọc hạt. Mỗi hạt là '
            'một giả thuyết pose kèm trọng số. Chu kỳ xử lý gồm ba bước (Hình 4): dự đoán, dịch mỗi hạt theo '
            'odometry cộng nhiễu; cập nhật, tính trọng số theo độ khớp giữa scan và bản đồ; lấy mẫu lại, giữ các hạt '
            'trọng số cao và loại các hạt thấp. Với mô hình ' + M('likelihood_field') + ', nếu tia thứ i có điểm cuối '
            'cách vật cản gần nhất trên bản đồ một khoảng d_i thì trọng số của hạt k là', True)]
    S += equation(r'w^{[k]}\;\propto\;\prod_{i=1}^{N}\left(z_{\mathrm{hit}}\,\frac{1}{\sqrt{2\pi}\,\sigma_{\mathrm{hit}}}'
                  r'\,e^{-d_i^{2}/2\sigma_{\mathrm{hit}}^{2}}+\frac{z_{\mathrm{rand}}}{z_{\mathrm{max}}}\right)', 1)
    S += [P('Số hạt được điều chỉnh theo phương pháp KLD-sampling trong khoảng 500–2000: nhiều hạt khi còn bất định, '
            'ít hạt khi tập hạt đã hội tụ. Bộ lọc chỉ cập nhật khi robot di chuyển ít nhất 0,25 m hoặc quay ít nhất '
            '0,2 rad nên khi robot đứng yên tập hạt không đổi. Các tham số chính nằm trong Bảng 6.', False)]
    S += figure(os.path.join(FIG, 'fig_amcl.png'), 'Hình 4 – Chu kỳ xử lý của bộ lọc hạt AMCL.', 16.0)
    S += table(['Tham số', 'Giá trị', 'Ý nghĩa'], [
        ['min_particles / max_particles', '500 / 2000', 'giới hạn số hạt'],
        ['laser_model_type', 'likelihood_field', 'mô hình đo của LiDAR'],
        ['max_beams', '60', 'số tia dùng trong mỗi lần cập nhật'],
        ['alpha1 … alpha5', '0,2', 'hệ số nhiễu của mô hình chuyển động'],
        ['update_min_d / update_min_a', '0,25 m / 0,2 rad', 'ngưỡng chuyển động để cập nhật'],
        ['set_initial_pose', 'true, (0, 0, 0)', 'pose khởi tạo trùng điểm sinh robot'],
        ['scan_topic', '/scan_nav', '/scan trễ 0,1 s'],
    ], [5.2, 4.0, 6.8], 'Bảng 6 – Các tham số chính của AMCL (<font name="Mono" size="9">config/localization.yaml'
                          '</font>).', mono_cols=(0, 1))
    S += [P('Vì frame ' + M('map') + ' trùng điểm sinh robot nên AMCL được khởi tạo sẵn tại (0, 0, 0) bằng '
            + M('set_initial_pose') + ', không cần công cụ ' + M('2D Pose Estimate') + ' trên RViz2. Công cụ này '
            'chỉ cần khi tia LiDAR hiển thị lệch khỏi tường. Node điều hướng cũng phát lại ' + M('/initialpose')
            + ' (hiệp phương sai 0,25 cho x, y và 0,0685 cho yaw) khi phát hiện robot còn trong dock, và bỏ qua bước '
            'này khi robot đã rời dock để không ghi đè một ước lượng đang đúng.')]

    S += [H2('4.3.  Kiểm tra định vị'),
          P('Định vị được coi là đúng khi ba điều kiện cùng thoả trên RViz2 với Fixed Frame = ' + M('map')
            + ': bản đồ hiển thị đúng; vị trí và hướng robot trên bản đồ khớp với vị trí thực trong Gazebo; các điểm '
            'quét LiDAR ' + M('/scan') + ' trùng với các bức tường của bản đồ, còn hạt AMCL tụ quanh robot. Ngoài kiểm tra bằng mắt, script ' + M('localization_check.py') + ' có thể đo tỉ lệ tia '
            'LiDAR có điểm cuối cách tường của bản đồ không quá 0,15 m (ba ô lưới); tỉ lệ này từ 70% trở lên thì '
            'định vị được xem là đúng.', True)]
    S += code('ros2 run tb4_lab04 localization_check.py')

    # ===== 5
    S += [H1('5.  Khảo sát toạ độ mục tiêu (Phần 2)'),
          P('Ba goal được đặt ở ba khu vực khác nhau của bản đồ (Hình 5), toạ độ (x, y, yaw) trong frame ' + M('map')
            + '. Các toạ độ được xác định trên bản đồ ' + M('map.pgm') + ' và kiểm tra bằng ' + M('check_goals.py')
            + ' theo ba tiêu chí: (1) cách tường ít nhất 0,6 m; (2) tới được từ điểm xuất phát, kiểm tra bằng '
            'tìm đường A* trên bản đồ đã nở theo bán kính robot 0,175 m; (3) khi tới nơi, vật thể nằm trong trường '
            'nhìn 60° của camera. Có thể đối chiếu lại bằng công cụ Publish Point trên RViz2 và đọc ' + M('/clicked_point')
            + ' (script ' + M('goal_recorder.py') + ' in sẵn đoạn YAML), hoặc đặt robot tại vị trí mong muốn rồi đọc '
            + M('/amcl_pose') + '. Kết quả kiểm tra ở Bảng 7; yaw của G1 là 2,63 rad ≈ 151°.', True)]
    S += table(['Goal', 'x (m)', 'y (m)', 'yaw', 'Cách tường', 'Vật thể trong tầm nhìn camera'], [
        ['G1', '−5,50', '5,75', '151°', '0,75 m', 'car_1 (3,5 m, lệch +5°)'],
        ['G2', '−6,00', '−2,60', '−90°', '1,21 m', 'person_2 (3,0 m, +0°); chair_1 (2,9 m, +25°)'],
        ['G3', '5,30', '−2,00', '0°', '1,25 m', 'fire_hydrant_1 (3,4 m, +17°); person_3 (3,7 m, −9°); '
                                                  'fire_extinguisher_1 (3,3 m, −23°)'],
    ], [1.3, 1.6, 1.6, 1.5, 2.2, 7.8], 'Bảng 7 – Toạ độ ba goal và kết quả kiểm tra (<font name="Mono" size="9">'
                                        'check_goals.py</font>).')
    S += figure(os.path.join(USER, 'goals_map.png'),
                'Hình 5 – Bản đồ tuần trước, ba goal (mũi tên = hướng yaw; quạt vàng = vùng nhìn của camera 60°), '
                'vật thể (vòng tròn) và đường đi dự kiến (nét đứt xanh lá).', 12.2)

    # ===== 6
    S += [H1('6.  Điều hướng tự động bằng Nav2 (Phần 3)'), H2('6.1.  Kiến trúc Nav2'),
          P('Khi node điều hướng gửi một đích, action ' + M('NavigateToPose') + ' tới ' + M('bt_navigator') + ' (Hình 6). '
            'Cây hành vi mặc định lập lại đường đi với tần số 1 Hz, chuyển đường cho bộ điều khiển và gọi các hành vi '
            'phục hồi (xoá costmap, quay tại chỗ, lùi, chờ) khi robot bị kẹt. Việc lập lại đường đi định kỳ cho phép '
            'robot thích ứng khi LiDAR phát hiện vật cản chưa có trên bản đồ, ví dụ các vật thể vừa thêm vào.', True)]
    S += figure(os.path.join(FIG, 'fig_nav2.png'), 'Hình 6 – Các server của Nav2 và luồng dữ liệu tới bánh xe.', 16.0)

    S += [H2('6.2.  Costmap'),
          P('Global costmap (frame ' + M('map') + ') gồm lớp tĩnh từ ' + M('/map') + ', lớp vật cản từ ' + M('/scan_nav')
            + ', lớp dock và lớp vùng đệm (inflation). Local costmap (frame ' + M('odom') + ') là cửa sổ 3 × 3 m quanh '
            'robot, độ phân giải 0,06 m, cập nhật nhanh hơn để phục vụ bộ điều khiển. Robot được mô hình hoá là hình '
            'tròn bán kính 0,175 m. Lớp vùng đệm gán chi phí cho mỗi ô theo khoảng cách d tới vật cản gần nhất:', True)]
    S += equation_cases('c(d)=', [('253', r'd\leq r_{\mathrm{robot}}'),
                                  (r'252\,e^{-k\,(d-r_{\mathrm{robot}})}', r'r_{\mathrm{robot}}<d\leq R'),
                                  ('0', 'd>R')], 2)
    S += [P('với r_robot = 0,175 m, hệ số suy giảm k = 4,0 và bán kính vùng đệm R = 0,45 m. Chi phí 253 tương ứng va '
            'chạm chắc chắn nếu tâm robot nằm tại ô đó; phần chi phí giảm dần ra phía ngoài khiến bộ lập kế hoạch ưu '
            'tiên đường ở giữa hành lang thay vì men sát tường.')]

    S += [H2('6.3.  Lập kế hoạch và điều khiển'),
          P('Bộ lập kế hoạch NavFn dùng thuật toán Dijkstra trên global costmap để tìm đường có tổng chi phí nhỏ nhất '
            'từ vị trí hiện tại tới đích, kết quả phát lên ' + M('/plan') + '. Vì chi phí của mỗi ô gồm cả phí vùng '
            'đệm nên đường tìm được là đường cân bằng giữa độ dài và khoảng cách tới tường. Bộ điều khiển DWB chạy ở '
            '20 Hz: tại mỗi chu kỳ lấy mẫu các cặp vận tốc (v, ω) trong giới hạn v ≤ 0,26 m/s, ω ≤ 1,0 rad/s, mô '
            'phỏng quỹ đạo tương ứng trong 1,7 s và chấm điểm bằng các hàm chi phí (bám đường đi, hướng về đích, '
            'tránh vật cản trên local costmap). Lệnh vận tốc sau đó qua ' + M('velocity_smoother') + ' rồi tới '
            + M('motion_control') + ' của Create 3. Một goal được xem là đạt khi sai số vị trí không quá 0,25 m và '
            'sai số hướng không quá 0,25 rad:', True)]
    S += equation(r'\sqrt{(x-x_g)^2+(y-y_g)^2}\leq 0{,}25\ \mathrm{m},\qquad '
                  r'\left|\mathrm{wrap}(\theta-\theta_g)\right|\leq 0{,}25\ \mathrm{rad}', 3)

    S += [H2('6.4.  Node điều hướng waypoint_navigator.py'),
          P('Thay vì kéo thả Nav2 Goal bằng chuột, node ' + M('waypoint_navigator.py') + ' kế thừa ' + M('BasicNavigator')
            + ' của ' + M('nav2_simple_commander') + ', đọc danh sách goal từ ' + M('config/goals.yaml') + ' rồi gửi '
            'tuần tự G1 → G2 → G3. Luồng xử lý (Hình 7) gồm các bước sau.', True),
          P('Bước 1, chờ ' + M('amcl') + ' và ' + M('bt_navigator') + ' ở trạng thái active (kiểm tra qua dịch vụ '
            'lifecycle) thay vì chờ một khoảng thời gian cố định. Bước 2, quyết định pose ban đầu: nếu ' + M('/dock_status')
            + ' cho biết robot đang trong dock thì phát ' + M('/initialpose') + ' từ ' + M('goals.yaml') + ', ngược lại '
            'giữ ước lượng hiện có của AMCL. Bước 3, nếu robot đang trong dock thì gọi action ' + M('/undock') + ' '
            '(tối đa 60 s theo giờ mô phỏng). Bước 4, với mỗi goal gọi ' + M('goToPose') + ', in phản hồi (khoảng cách '
            'còn lại, thời gian ước tính, số lần hồi phục) mỗi 3 s; goal thất bại thì xoá costmap và thử lại tối đa '
            + M('max_retries') + ' lần, quá ' + M('goal_timeout') + ' thì huỷ. Khi tới nơi, node ghi sai số vị trí và '
            'hướng từ pose cuối cùng mà ' + M('bt_navigator') + ' báo, dừng ' + M('pause_at_goal') + ' giây để YOLO '
            'kịp quan sát, rồi sang goal kế. Bước 5, in bảng TỔNG KẾT và lưu ' + M('run.json') + ' (quỹ đạo, đường Nav2 '
            'lập) cùng ' + M('summary.csv') + ' vào ' + M('~/tb4_results/nav_&lt;thời gian&gt;/') + '. Nếu người dùng '
            'bấm Ctrl+C, node huỷ goal đang chạy để robot dừng và vẫn lưu kết quả của các goal đã đi. Các tham số '
            'điều chỉnh được nằm trong Bảng 8.')]
    S += figure(os.path.join(FIG, 'fig_navigator.png'), 'Hình 7 – Lưu đồ của node <font name="Mono" '
                'size="9">waypoint_navigator.py</font>.', 12.6)
    S += table(['Tham số', 'Mặc định', 'Ý nghĩa'], [
        ['goals_file', '(rỗng)', 'file goal; rỗng = config/goals.yaml'],
        ['initial_pose_mode', 'auto', 'auto: chỉ đặt pose khi robot trong dock; always; never'],
        ['undock', 'true', 'tự undock khi robot đang trong dock'],
        ['pause_at_goal', '2,0 s', 'thời gian dừng tại mỗi goal (giờ mô phỏng)'],
        ['goal_timeout', '300 s', 'giới hạn thời gian cho một goal (giờ mô phỏng)'],
        ['max_retries', '1', 'số lần thử lại một goal thất bại (sau khi xoá costmap)'],
        ['look_around', 'false', 'xoay 360° tại mỗi goal'],
        ['return_home, dock_at_end', 'false', 'quay về chỗ sau undock; vào dock ở cuối'],
        ['loops', '1', 'số vòng đi qua các goal'],
    ], [4.4, 2.6, 9.0], 'Bảng 8 – Tham số của <font name="Mono" size="9">waypoint_navigator.py</font>.',
        mono_cols=(0,))
    S += code('''
ros2 launch tb4_lab04 navigation.launch.py   # Terminal 1: mô phỏng + AMCL + Nav2
ros2 run tb4_lab04 waypoint_navigator.py     # Terminal 2: robot tự đi G1, G2, G3
''')

    S += [H2('6.5.  Kết quả điều hướng'),
          P('Node điều hướng được chạy một lần, không điều khiển tay và không đặt goal bằng chuột trong suốt quá '
            'trình. Cả ba goal đều ở trạng thái SUCCEEDED ngay lần thử đầu (Bảng 9, Hình 8). Tổng cộng robot đi '
            '30,5 m trong 118,2 s thời gian mô phỏng, tức tốc độ trung bình khoảng 0,26 m/s, bằng đúng vận tốc tối '
            'đa cấu hình cho DWB. Điều đó cho thấy robot gần như di chuyển liên tục với tốc độ tối đa, không mất '
            'thời gian đáng kể cho hành vi phục hồi. Quỹ đạo thực (đường đỏ) bám sát đường Nav2 lập (xanh lá), và '
            'đường đi ở cả ba chặng đều đi giữa hành lang, không men sát tường nhờ lớp vùng đệm.', True)]
    S += table(['Goal', 'Kết quả', 'Thời gian (s)', 'Quãng đường (m)', 'Sai số vị trí (m)', 'Sai số hướng', 'Số lần thử'], [
        ['G1', 'SUCCEEDED', '30,9', '7,7', '0,25', '6°', '1'],
        ['G2', 'SUCCEEDED', '39,5', '11,1', '0,24', '14°', '1'],
        ['G3', 'SUCCEEDED', '47,8', '11,7', '0,23', '14°', '1'],
        ['<b>Tổng</b>', '<b>3/3 đạt</b>', '<b>118,2</b>', '<b>30,5</b>', '', '', ''],
    ], [1.4, 3.0, 2.2, 2.6, 2.6, 2.2, 2.0], 'Bảng 9 – Kết quả ba goal (thời gian theo giờ mô phỏng; sai số so với '
                                           'pose AMCL tại thời điểm kết thúc).')
    S += figure(os.path.join(USER, 'run_map.png'),
                'Hình 8 – Đường Nav2 lập (xanh lá, <font name="Mono" size="9">/plan</font>), quỹ đạo robot (đỏ, '
                '<font name="Mono" size="9">/amcl_pose</font>) và vị trí robot khi YOLO phát hiện từng lớp (chấm màu).',
                12.2)
    S += [P('Sai số vị trí 0,23–0,25 m nằm sát ngưỡng ' + M('xy_goal_tolerance') + ' = 0,25 m: bộ kiểm tra goal kết '
            'thúc ngay khi robot vào trong ngưỡng, nên con số này phản ánh ngưỡng chấp nhận đã cấu hình chứ không '
            'phải độ chính xác tối đa của AMCL hay Nav2. Sai số hướng 6°–14° (0,10–0,24 rad) cũng nằm trong ngưỡng '
            '0,25 rad. Cần lưu ý các sai số này được tính so với pose mà AMCL ước lượng, không phải so với pose '
            'thật trong Gazebo.')]
    # ===== 7
    S += [H1('7.  Nhận diện vật thể bằng YOLO (Phần 4)'), H2('7.1.  Thiết kế node'),
          P('Node ' + M('yolo_detector.py') + ' (Hình 9) đăng ký topic ' + M('/oakd/rgb/preview/image_raw') + '. Hàm gọi '
            'lại chỉ giữ khung hình mới nhất; một luồng suy luận riêng lấy khung đó, chuyển ' + M('sensor_msgs/Image')
            + ' sang ảnh BGR của OpenCV bằng ' + M('cv_bridge') + ', đưa qua mô hình YOLO và nhận về danh sách (lớp, '
            'độ tự tin, khung bao). Cách làm này giúp suy luận chậm không làm hàng đợi ảnh phình ra: khung cũ bị bỏ, '
            'luôn xử lý khung gần nhất, tối đa 5 ảnh mỗi giây để dành CPU cho Gazebo và Nav2. Node vẽ khung bao, tên '
            'lớp, độ tự tin và dòng trạng thái (tên mô hình, FPS, số vật thể, vị trí robot trong frame ' + M('map')
            + ') lên ảnh, rồi hiển thị trên cửa sổ OpenCV, phát lên ' + M('/yolo/image_annotated') + ' để xem trên '
            'RViz2, phát ' + M('/yolo/detections') + ' và in ra terminal (lớp mới xuất hiện được in ngay, danh sách '
            'đầy đủ in mỗi giây). Vị trí robot lấy từ ' + M('/amcl_pose') + '. Khi kết thúc, node lưu ' + M('detections.csv')
            + ' cùng ảnh lần đầu thấy và ảnh tin cậy nhất của mỗi lớp vào ' + M('~/tb4_results/yolo_&lt;thời gian&gt;/')
            + '.', True)]
    S += figure(os.path.join(FIG, 'fig_yolo.png'), 'Hình 9 – Luồng xử lý của node <font name="Mono" '
                'size="9">yolo_detector.py</font>.', 16.0)
    S += [P('Quá trình lọc kết quả của YOLO dùng ngưỡng độ tự tin và loại bỏ khung trùng bằng NMS, trong đó hai khung '
            'A và B bị coi là trùng khi')]
    S += equation(r'\mathrm{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}>0{,}5', 4)
    S += [H2('7.2.  Mô hình và tham số'),
          P('Bài dùng YOLO11n của thư viện ultralytics, mô hình nhẹ nhất của họ YOLO11, đã huấn luyện sẵn trên bộ '
            'COCO (80 lớp) và chạy bằng PyTorch bản CPU. Ảnh camera mô phỏng chỉ có 320 × 240 điểm ảnh nên được '
            'phóng lên 640 khi suy luận để nhận vật nhỏ và xa tốt hơn (Bảng 10).', True)]
    S += table(['Tham số', 'Giá trị', 'Ý nghĩa'], [
        ['model', 'yolo11n.pt', 'mô hình; có thể đổi yolov8n.pt hoặc YOLO-World (yolov8s-worldv2.pt)'],
        ['conf', '0,35', 'ngưỡng độ tự tin; ảnh nhỏ nên không đặt quá cao'],
        ['iou', '0,5', 'ngưỡng NMS'],
        ['imgsz', '640', 'kích thước ảnh khi suy luận'],
        ['max_rate', '5 ảnh/s', 'giới hạn tốc độ để dành CPU cho Gazebo và Nav2'],
        ['window_scale', '2,0', 'phóng cửa sổ OpenCV cho dễ nhìn'],
    ], [3.4, 3.0, 9.6], 'Bảng 10 – Tham số chính của <font name="Mono" size="9">yolo_detector.py</font> '
                         '(<font name="Mono" size="9">config/yolo.yaml</font>).', mono_cols=(0,))
    S += code('''
ros2 launch tb4_lab04 yolo.launch.py  # node YOLO + cửa sổ camera
ros2 launch tb4_lab04 yolo.launch.py yolo_model:=yolo11s.pt conf:=0.5   # model lớn, conf cao
''')

    S += [H2('7.3.  Kết quả nhận diện'),
          P('Trong lần chạy, robot vừa di chuyển qua ba goal vừa nhận diện vật thể (Hình 10). Bảng 11 là bảng '
            'tổng kết do node in ra khi kết thúc; cột "Số khung" đếm số khung hình có xuất hiện lớp đó (mỗi khung '
            'đếm một lần cho mỗi lớp), không phải số vật thể.', True)]
    ypath = os.path.join(USER, 'yolo_window.png')
    S += figure(ypath, 'Hình 10 – Cửa sổ nhận diện YOLO khi robot ở gần G3: trụ cứu hoả (fire hydrant, 0,84) và người '
                       '(person) bị cắt ở mép ảnh.', 8.8, 'yolo_window.png')
    S += table(['Lớp', 'Số khung', 'Conf tối đa', 'Lần đầu (s)', 'Robot lúc thấy lần đầu (map)', 'Có trong mê cung?'], [
        ['person', '3484', '0,91', '57,5', '(−0,30; −0,02)', 'có (3 vật thể)'],
        ['fire hydrant', '2587', '0,88', '162,1', '(0,15; −3,55)', 'có'],
        ['car', '212', '0,93', '57,8', '(−0,31; −0,02)', 'có'],
        ['chair', '84', '0,86', '128,0', '(−5,47; −1,01)', 'có'],
        ['airplane', '388', '0,94', '63,1', '(−0,32; −0,02)', '<font color="#b22222">không</font>'],
        ['bench', '54', '0,79', '127,8', '(−5,40; −0,88)', '<font color="#b22222">không</font>'],
        ['traffic light', '14', '0,75', '53,0', '(0,01; −0,02)', '<font color="#b22222">không</font>'],
        ['sports ball', '6', '0,62', '63,1', '(−0,32; −0,02)', '<font color="#b22222">không</font>'],
        ['train', '1', '0,55', '52,2', '(0,01; −0,02)', '<font color="#b22222">không</font>'],
        ['parking meter', '1', '0,51', '102,7', '(−4,45; 4,93)', '<font color="#b22222">không</font>'],
    ], [2.9, 1.9, 2.2, 2.0, 4.1, 2.9], 'Bảng 11 – Tổng kết YOLO của lần chạy (thời gian theo giờ mô phỏng).')
    S += [P('Các lớp có thật trong mê cung (người, trụ cứu hoả, xe hơi, ghế) đều được nhận diện với độ tự tin cao '
            'nhất từ 0,86 đến 0,93. Số khung lớn của person và fire hydrant chủ yếu do hai vật thể này nằm trước '
            'camera khi robot dừng ở G3 nên nhiều khung gần như trùng nhau; con số không phản ánh số lượng vật thể. '
            'Vị trí robot lúc phát hiện được vẽ thành các chấm màu trên Hình 8, cho thấy từng lớp được nhìn thấy '
            'ở đoạn nào của đường đi.'),
          P('Bên cạnh đó có hai nhóm kết quả cần xem xét. Thứ nhất, sáu lớp không tồn tại trong mê cung vẫn xuất hiện: '
            'airplane (388 khung, độ tự tin tối đa 0,94), bench (54 khung) và bốn lớp còn lại chỉ vài khung. Với mô '
            'hình nhẹ trên ảnh mô phỏng 320 × 240 và ngưỡng 0,35, đây là các nhận nhầm; riêng airplane có độ tự tin '
            'cao và lặp lại nhiều khung nên nhiều khả năng là một vật thể hay bề mặt cố định bị nhận nhầm một cách '
            'có hệ thống. Thứ hai, bình chữa cháy không thuộc 80 lớp COCO nên YOLO11n không gọi được tên nó: trong '
            'Hình 10 khung "person" còn bao cả bình màu đỏ trước ngực. Muốn nhận đúng bình chữa cháy cần mô hình có '
            'lớp này, chẳng hạn YOLO-World với danh sách lớp tự đặt (package đã hỗ trợ) hoặc huấn luyện thêm. Để giảm '
            'nhận nhầm có thể nâng ngưỡng ' + M('conf') + ' lên 0,5 hoặc giới hạn tham số ' + M('classes') + ' vào các '
            'lớp cần quan tâm.')]

    # ===== 8
    S += [H1('8.  Nhận xét và hạn chế'),
          P('Hệ thống đáp ứng các yêu cầu của bài: (1) mô phỏng chạy lại trong đúng world ' + M('maze') + ' cùng bảy '
            'vật thể mới, bản đồ tuần trước được nạp và AMCL cùng Nav2 hoạt động; (2) ba goal được xác định và kiểm '
            'tra; (3) node điều hướng tự đưa robot đi qua G1 → G2 → G3 mà không điều khiển tay, cả ba goal đạt; '
            '(4) node YOLO chạy song song, hiển thị khung, tên lớp, độ tự tin và in ra terminal. Một số hạn chế cần '
            'nêu rõ.', True),
          P('Thứ nhất, kết quả điều hướng lấy từ một lần chạy duy nhất nên chưa đánh giá được độ ổn định giữa các '
            'lần, và lần chạy này chưa đo số lần va chạm bằng ' + M('nav_monitor.py') + '; nhận xét "không va chạm" '
            'cần dựa vào video. Thứ hai, sai số tới đích được tính so với pose AMCL, không phải pose thật trong '
            'Gazebo, và bị chặn bởi ngưỡng 0,25 m. Thứ ba, tọa độ goal được chọn từ bản đồ và kiểm tra bằng '
            'script, không phải do robot đứng tại chỗ đo. Thứ tư, YOLO11n còn nhận nhầm một số lớp, không nhận được '
            'bình chữa cháy, và chạy trên CPU nên bị giới hạn 5 ảnh/s; hướng cải thiện là nâng ngưỡng conf, lọc lớp, '
            'dùng YOLO-World hoặc mô hình lớn hơn khi có GPU.')]

    # ===== 9
    S += [H1('9.  Hình ảnh minh hoạ kết quả')]
    S += figure(os.path.join(USER, 'gazebo_world.png'),
                'Hình 11 – World <font name="Mono" size="9">maze</font> trong Gazebo Fortress (ảnh chụp ở bài trước, '
                'trước khi thêm vật thể; cùng world và vị trí dock).', 9.0, 'gazebo_world.png')
    S += figure(os.path.join(USER, 'terminal_navigator.png'),
                'Hình 12 – Terminal: bảng TỔNG KẾT của <font name="Mono" size="9">waypoint_navigator.py</font> '
                '(3/3 goal đạt).', 14.0)
    S += [P('Bản đồ kèm các goal ở Hình 5, đường Nav2 lập cùng quỹ đạo robot ở Hình 8, ảnh nhận diện YOLO ở '
            'Hình 10. Quá trình nạp bản đồ, định vị, robot tự đi qua từng goal và cửa sổ YOLO chạy song song được ghi '
            'lại trong video demo.', True)]

    # ===== 10
    vid = str(info.get('link_video') or '').strip()
    git = str(info.get('link_github') or '').strip()
    miss = '<font color="#b22222">[CHƯA CÓ LINK – điền vào docs/report_info.yaml rồi dựng lại báo cáo]</font>'
    if not vid:
        MISSING.append('link_video')
    if not git:
        MISSING.append('link_github')
    S += [H1('10.  Liên kết video demo và mã nguồn'),
          Paragraph('<b>Video demo</b> (Google Drive, chế độ công khai):', body0),
          Paragraph(M(esc(vid)) if vid else miss, body0), Spacer(1, 4),
          Paragraph('<b>Mã nguồn</b> (GitHub, chế độ Public):', body0),
          Paragraph(M(esc(git)) if git else miss, body0)]
    return S


# ------------------------------------------------------------------------------------------------ bìa
def make_cover(path, info):
    """Dùng lại trang bìa của báo cáo bài 4 (khung, logo, tên sinh viên), thay dòng số bài và tên bài."""
    base = os.path.join(HERE, 'assets', 'cover_base.pdf')
    ov = os.path.join(HERE, 'assets', '_cover_overlay.pdf')
    c = rl_canvas.Canvas(ov, pagesize=A4)
    c.setFillColor(colors.white)
    c.rect(82, 300, 432, 60, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont('Serif-B', 15.5)
    c.drawCentredString(A4[0] / 2, 338, 'BÀI THỰC HÀNH SỐ 5')
    c.setFont('Serif', 12.5)
    c.drawCentredString(A4[0] / 2, 316, 'TurtleBot 4: Localization, Nav2 và nhận diện vật thể YOLO trong Gazebo')
    c.save()
    r = PdfReader(base)
    page = r.pages[0]
    page.merge_page(PdfReader(ov).pages[0])
    w = PdfWriter()
    w.add_page(page)
    with open(path, 'wb') as f:
        w.write(f)
    os.remove(ov)


class FloatGroup(Flowable):
    """Hình + các đoạn văn ngay sau nó. Nếu hình không vừa chỗ còn lại, cho đoạn văn chảy lên trước
    để lấp trang, hình sang đầu trang sau (giống float trong LaTeX)."""

    def __init__(self, fig, paras):
        super().__init__()
        self.fig, self.paras = fig, paras

    def wrap(self, aw, ah):
        self.width = aw
        self.height = sum(f.wrap(aw, 10000)[1] + f.getSpaceBefore() + f.getSpaceAfter()
                          for f in [self.fig] + self.paras)
        return aw, self.height

    def split(self, aw, ah):
        fh = self.fig.wrap(aw, ah)[1]
        if fh <= ah:
            return [self.fig] + self.paras
        p0 = self.paras[0]
        room = ah - p0.getSpaceBefore()
        if p0.wrap(aw, room)[1] <= room or p0.split(aw, room):
            return self.paras + [self.fig]
        return []

    def draw(self):
        y = self.height
        for f in [self.fig] + self.paras:
            w, h = f.wrap(self.width, 10000)
            y -= f.getSpaceBefore() + h
            f.drawOn(self.canv, 0, y)
            y -= f.getSpaceAfter()


def group_floats(story):
    out, i = [], 0
    while i < len(story):
        fl = story[i]
        if isinstance(fl, FigBlock):
            j, paras = i + 1, []
            while j < len(story) and len(paras) < 4 and isinstance(story[j], Paragraph) \
                    and story[j].style.name not in ('h1', 'h2'):
                paras.append(story[j]); j += 1
            if paras:
                out.append(FloatGroup(fl, paras)); i = j; continue
        out.append(fl); i += 1
    return out


def fix_orphans(story, avail_w):
    """Chèn CondPageBreak trước tiêu đề khi phần tử ngay sau nó (hình, bảng) không còn chỗ trên trang."""
    out = []
    for i, fl in enumerate(story):
        if isinstance(fl, Paragraph) and fl.style.name in ('h1', 'h2'):
            hh = fl.wrap(avail_w, 1000)[1] + fl.style.spaceBefore + fl.style.spaceAfter
            j = i + 1
            while j < len(story) and isinstance(story[j], Spacer):
                j += 1
            nxt = story[j] if j < len(story) else None
            if isinstance(nxt, (Paragraph, FloatGroup)):
                need = hh + 62
            elif nxt is not None:
                try:
                    nh = nxt.wrap(avail_w, 10000)[1]
                except Exception:  # noqa: BLE001
                    nh = 200
                if isinstance(nxt, FigBlock):
                    nh = nh * FigBlock.MIN_SCALE
                need = hh + (min(nh, 150) if isinstance(nxt, Table) and not isinstance(nxt, KeepTogether)
                             else nh)
            else:
                need = hh + 40
            out.append(CondPageBreak(need))
        out.append(fl)
    return out


def main():
    info = load_info()
    body_pdf = os.path.join(HERE, '_body.pdf')
    cover_pdf = os.path.join(HERE, '_cover.pdf')
    doc = Doc(body_pdf, pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.3 * cm,
              bottomMargin=2.4 * cm, title='Báo cáo thực hành số 5 – TurtleBot 4: Localization, Nav2 và YOLO',
              author='Lê Trọng Nghĩa')
    doc.multiBuild(fix_orphans(group_floats(content(info)), doc.width))
    make_cover(cover_pdf, info)
    w = PdfWriter()
    for src in (cover_pdf, body_pdf):
        for pg in PdfReader(src).pages:
            w.add_page(pg)
    w.add_metadata({'/Title': 'Báo cáo thực hành số 5 – TurtleBot 4: Localization, Nav2 và YOLO',
                    '/Author': 'Lê Trọng Nghĩa'})
    with open(OUT, 'wb') as f:
        w.write(f)
    os.remove(body_pdf)
    os.remove(cover_pdf)
    print('Đã tạo:', OUT, '({} trang)'.format(len(PdfReader(OUT).pages)))
    miss = sorted(set(MISSING))
    if miss:
        print('CÒN THIẾU:', ', '.join(miss))


if __name__ == '__main__':
    main()
