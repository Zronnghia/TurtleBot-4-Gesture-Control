#!/usr/bin/env python3
"""Unit test Bài 6 – logic cử chỉ / máy trạng thái / kế hoạch chuyển động (không cần ROS, webcam, MediaPipe).

    python3 test/test_gesture_logic.py          # hoặc: python3 -m pytest test/ -q
"""
import importlib.util
import math
import os
import sys
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))


def load(rel_path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gl = load('scripts/gesture_logic.py', 'gesture_logic')
grn = load('scripts/gesture_recognition_node.py', 'gesture_recognition_node')
gs = load('scripts/gesture_sequence.py', 'gesture_sequence')


def feed(stab, label, t0, dur, fps=30.0):
    """Đưa cùng một nhãn vào bộ lọc trong `dur` giây; trả (danh sách nhãn ổn định đã đổi, t cuối)."""
    changes = []
    n = int(round(dur * fps))
    t = t0
    for i in range(n):
        t = t0 + i / fps
        st, ch = stab.update(t, label)
        if ch:
            changes.append((round(t, 3), st))
    return changes, t + 1.0 / fps


def open_hand(cx=0.5, cy=0.5, s=0.2):
    """21 landmark giả của bàn tay xoè (ngón hướng lên)."""
    pts = [(cx, cy + s)] * 21
    pts = list(pts)
    pts[0] = (cx, cy + s)
    bases = {5: -0.06, 9: -0.02, 13: 0.02, 17: 0.06}
    for base, dx in bases.items():
        pts[base] = (cx + dx * s / 0.2, cy)
        pts[base + 1] = (cx + dx * s / 0.2, cy - 0.3 * s)
        pts[base + 2] = (cx + dx * s / 0.2, cy - 0.55 * s)
        pts[base + 3] = (cx + dx * s / 0.2, cy - 0.8 * s)
    for i, k in enumerate((1, 2, 3, 4)):
        pts[k] = (cx - 0.1 * s / 0.2 - 0.05 * i, cy + 0.6 * s - 0.15 * i * s)
    return pts


def fist(cx=0.5, cy=0.5, s=0.2):
    pts = open_hand(cx, cy, s)
    for base in (5, 9, 13, 17):
        bx, by = pts[base]
        pts[base + 1] = (bx, by + 0.15 * s)   # PIP
        pts[base + 2] = (bx, by + 0.30 * s)
        pts[base + 3] = (bx, by + 0.35 * s)   # đầu ngón gập về phía cổ tay
    return pts


class TestNames(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(gl.canonical_gesture('thumb_up'), 'Thumb_Up')
        self.assertEqual(gl.canonical_gesture('Thumb Up'), 'Thumb_Up')
        self.assertEqual(gl.canonical_gesture('OPEN-PALM'), 'Open_Palm')
        self.assertEqual(gl.canonical_gesture('wave'), 'Wave')
        self.assertEqual(gl.canonical_gesture(''), 'None')
        self.assertEqual(gl.canonical_gesture(None), 'None')
        self.assertEqual(gl.canonical_gesture('rock'), 'None')

    def test_parse_message(self):
        self.assertEqual(gl.parse_gesture_message('Victory'), 'Victory')
        self.assertEqual(gl.parse_gesture_message('Victory 0.91'), 'Victory')
        self.assertEqual(gl.parse_gesture_message('{"gesture": "pointing_up"}'), 'Pointing_Up')
        self.assertEqual(gl.parse_gesture_message('{bad json'), 'None')
        self.assertEqual(gl.parse_gesture_message(''), 'None')

    def test_to_ascii(self):
        self.assertEqual(gl.to_ascii('Đã ra giữa sân – sẵn sàng'), 'Da ra giua san - san sang')
        self.assertEqual(gl.to_ascii('DUNG KHAN'), 'DUNG KHAN')

    def test_as_bool(self):
        for v in ('true', 'True', '1', 'yes', 'on', True, 1):
            self.assertTrue(gl.as_bool(v))
        for v in ('false', 'False', '0', 'no', 'off', '', False, 0):
            self.assertFalse(gl.as_bool(v))

    def test_at_least_five_gestures_mapped(self):
        used = set(gl.SELECT_GESTURES) | {gl.CONFIRM_GESTURE, gl.STOP_GESTURE, gl.CANCEL_GESTURE}
        self.assertEqual(used, {'Wave', 'Pointing_Up', 'Victory', 'Thumb_Up', 'Open_Palm', 'Closed_Fist'})
        for g in used:
            self.assertIn(g, gl.ALL_GESTURES)
            self.assertIn(g, gl.DISPLAY_NAME)


class TestHandGeometry(unittest.TestCase):
    def test_extended_fingers(self):
        self.assertEqual(gl.count_extended_fingers(open_hand()), 4)
        self.assertEqual(gl.count_extended_fingers(fist()), 0)

    def test_palm_center(self):
        cx, cy = gl.palm_center(open_hand(0.3, 0.6))
        self.assertAlmostEqual(cx, 0.3, delta=0.02)

    def test_count_swings(self):
        self.assertEqual(gl.count_swings([0.5] * 10, 0.05), 0)
        self.assertEqual(gl.count_swings([0.5, 0.52, 0.49, 0.51, 0.5], 0.05), 0)   # rung tay
        xs = [0.5 + 0.1 * math.sin(2 * math.pi * 2.0 * t / 30.0) for t in range(30)]  # 2 Hz, 1 s
        self.assertGreaterEqual(gl.count_swings(xs, 0.06), 3)
        self.assertEqual(gl.count_swings([0.3, 0.4, 0.5, 0.6], 0.06), 1)              # trượt một chiều


class TestWaveDetector(unittest.TestCase):
    def test_wave_detected(self):
        w = gl.WaveDetector(window=1.5, min_swings=3, min_amplitude=0.06, latch=1.0)
        hit = None
        for i in range(60):
            t = i / 30.0
            x = 0.5 + 0.1 * math.sin(2 * math.pi * 1.5 * t)
            if w.update(t, x, True) and hit is None:
                hit = t
        self.assertIsNotNone(hit)
        self.assertLess(hit, 1.6)
        self.assertGreaterEqual(w.confidence(), 1.0)

    def test_still_palm_not_wave(self):
        w = gl.WaveDetector()
        for i in range(90):
            self.assertFalse(w.update(i / 30.0, 0.5 + 0.005 * ((-1) ** i), True))

    def test_closed_hand_not_wave(self):
        w = gl.WaveDetector()
        for i in range(60):
            t = i / 30.0
            self.assertFalse(w.update(t, 0.5 + 0.1 * math.sin(2 * math.pi * 1.5 * t), False))

    def test_latch_expires_and_gap_resets(self):
        w = gl.WaveDetector(latch=0.5)
        t = 0.0
        for i in range(60):
            t = i / 30.0
            w.update(t, 0.5 + 0.1 * math.sin(2 * math.pi * 1.5 * t), True)
        self.assertTrue(w.update(t + 0.05, 0.5, True))      # vẫn xoè tay ngay sau khi vẫy -> Wave
        self.assertFalse(w.update(t + 0.1, None, False))    # khung không có tay -> không phải Wave
        self.assertFalse(w.update(t + 0.15, 0.5, False))    # ngón cái/nắm tay ngay sau khi vẫy
        self.assertFalse(w.update(t + 1.0, None, False))
        self.assertEqual(w.history, [])
        self.assertFalse(w.update(t + 1.05, 0.5, True))     # giơ lại tay đứng yên: không kế thừa Wave

    def test_frame_label(self):
        self.assertEqual(gl.frame_label('Open_Palm', 0.9, 0.55, True, True), 'Wave')
        self.assertEqual(gl.frame_label('Open_Palm', 0.9, 0.55, True, False), 'Open_Palm')
        self.assertEqual(gl.frame_label('Thumb_Up', 0.4, 0.55, True, False), 'None')
        self.assertEqual(gl.frame_label('Thumb_Up', 0.9, 0.55, False, False), 'None')
        self.assertEqual(gl.frame_label('None', 0.9, 0.55, True, False), 'None')


class TestStabilizer(unittest.TestCase):
    def make(self):
        return gl.GestureStabilizer(hold_time=0.5, hold_overrides={'Open_Palm': 0.2, 'None': 0.4, 'Wave': 0.15},
                                    vote_ratio=0.7, min_frames=2)

    def test_needs_hold_time(self):
        s = self.make()
        ch, t = feed(s, 'Thumb_Up', 0.0, 0.3)
        self.assertEqual(ch, [])
        ch, t = feed(s, 'Thumb_Up', t, 0.5)
        self.assertEqual([c[1] for c in ch], ['Thumb_Up'])
        self.assertLessEqual(ch[0][0], 0.5)

    def test_single_glitch_ignored(self):
        s = self.make()
        _, t = feed(s, 'Victory', 0.0, 1.0)
        self.assertEqual(s.stable, 'Victory')
        st, ch = s.update(t, 'Thumb_Up')          # 1 khung nhận nhầm
        self.assertFalse(ch)
        _, t = feed(s, 'Victory', t + 0.033, 0.5)
        self.assertEqual(s.stable, 'Victory')

    def test_flicker_never_stable(self):
        s = self.make()
        labels = ['Thumb_Up', 'Pointing_Up', 'None'] * 30
        for i, lb in enumerate(labels):
            s.update(i / 30.0, lb)
        self.assertNotIn(s.stable, ('Thumb_Up', 'Pointing_Up'))

    def test_open_palm_fast(self):
        s = self.make()
        _, t = feed(s, 'Victory', 0.0, 1.0)
        ch, _ = feed(s, 'Open_Palm', t, 0.4)
        self.assertEqual(ch[0][1], 'Open_Palm')
        self.assertLess(ch[0][0] - t, 0.45)       # dừng nhanh hơn hold 0.5 s + đủ phiếu

    def test_none_after_hand_lost(self):
        s = self.make()
        _, t = feed(s, 'Thumb_Up', 0.0, 1.0)
        ch, _ = feed(s, 'None', t, 0.8)
        self.assertEqual(ch[-1][1], 'None')

    def test_low_fps(self):
        s = self.make()
        ch, _ = feed(s, 'Pointing_Up', 0.0, 1.5, fps=8)
        self.assertEqual(ch[0][1], 'Pointing_Up')


class TestPlans(unittest.TestCase):
    def test_plans_symmetric_and_small(self):
        for name, rmax_lim in (('greet', 0.01), ('forward_back', 0.40), ('circle', 1.05)):
            plan = gl.build_plan(name)
            r, end = gl.plan_extent(plan)
            self.assertLessEqual(r, rmax_lim, name)
            self.assertLess(math.hypot(end[0], end[1]), 0.03, name)     # về gần chỗ cũ
            self.assertLess(abs(end[2]), 0.05, name)                    # cùng hướng

    def test_forward_back_four_times(self):
        plan = gl.build_plan('forward_back')
        fwd = [s for s in plan if s.kind == 'dist' and s.lin > 0]
        back = [s for s in plan if s.kind == 'dist' and s.lin < 0]
        self.assertEqual(len(fwd), 4)
        self.assertEqual(len(back), 4)

    def test_greet_left_right(self):
        plan = gl.build_plan('greet')
        signs = [math.copysign(1, s.ang) for s in plan if s.kind == 'angle']
        self.assertEqual(signs[0], 1.0)
        self.assertTrue(all(a != b for a, b in zip(signs, signs[1:])))
        self.assertTrue(all(s.lin == 0 for s in plan))

    def test_circle_one_lap(self):
        plan = gl.build_plan('circle')
        self.assertEqual(len(plan), 1)
        self.assertAlmostEqual(plan[0].target, 2 * math.pi)
        self.assertAlmostEqual(plan[0].lin / plan[0].ang, 0.5)

    def test_clear_dock_plan(self):
        # bước chuẩn bị bị huỷ khi robot đã lùi 0,2 m nhưng còn quay mặt vào dock (yaw 0, dock ở +x)
        r = gl.SegmentRunner(gl.clear_dock_plan((-0.2, 0.0, 0.0), 1.35))
        bot = FakeRobot()
        bot.x, bot.y, bot.th = -0.2, 0.0, 0.0
        t = 0.0
        min_x = bot.x
        while t < 60 and not r.done and not r.error:
            bot.step(r.update(t, bot.pose()), 0.05)
            t += 0.05
        self.assertTrue(r.done, r.error)
        self.assertAlmostEqual(math.hypot(bot.x, bot.y), 1.35, delta=0.05)   # đã ra xa dock
        self.assertLess(bot.x, -1.2)                                          # đi về phía -x, không lao vào dock
        self.assertGreater(abs(bot.th), 2.9)                                  # mặt quay ra xa dock
        # đã ở xa và đúng hướng -> không làm gì đáng kể
        plan = gl.clear_dock_plan((-1.4, 0.1, math.atan2(0.1, -1.4)), 1.35)
        self.assertEqual([s.kind for s in plan], ['time'])
        # sát gốc -> mặc định quay về -x
        plan = gl.clear_dock_plan((0.0, 0.0, 0.0), 1.35)
        self.assertAlmostEqual(plan[0].target, math.pi, delta=0.01)

    def test_bad_behavior(self):
        with self.assertRaises(ValueError):
            gl.build_plan('dance')
        with self.assertRaises(ValueError):
            gl.Segment('x', 0, 0, 1, 'meters')


class FakeRobot:
    """Mô phỏng động học robot vi sai có trễ bậc nhất (gần giống Create 3) cho SegmentRunner."""

    def __init__(self, tau=0.15):
        self.x = self.y = self.th = 0.0
        self.v = self.w = 0.0
        self.tau = tau

    def step(self, cmd, dt):
        self.v += (cmd[0] - self.v) * min(1.0, dt / self.tau)
        self.w += (cmd[1] - self.w) * min(1.0, dt / self.tau)
        self.x += self.v * math.cos(self.th) * dt
        self.y += self.v * math.sin(self.th) * dt
        self.th = math.atan2(math.sin(self.th + self.w * dt), math.cos(self.th + self.w * dt))

    def pose(self):
        return (self.x, self.y, self.th)


def run_plan(plan, use_odom=True, blocked=False, max_t=120.0):
    r = gl.SegmentRunner(plan)
    bot = FakeRobot()
    t, dt = 0.0, 0.05
    path = []
    while t < max_t and not r.done and not r.error:
        cmd = r.update(t, bot.pose() if use_odom else None)
        bot.step((0.0, 0.0) if blocked else cmd, dt)
        path.append(bot.pose())
        t += dt
    return r, bot, t, path


class TestSegmentRunner(unittest.TestCase):
    def test_forward_back_returns(self):
        r, bot, t, path = run_plan(gl.build_plan('forward_back'))
        self.assertTrue(r.done, r.error)
        self.assertLess(math.hypot(bot.x, bot.y), 0.05)
        self.assertAlmostEqual(max(p[0] for p in path), 0.35, delta=0.04)

    def test_greet_returns_heading(self):
        r, bot, t, path = run_plan(gl.build_plan('greet'))
        self.assertTrue(r.done, r.error)
        self.assertLess(abs(bot.th), 0.08)
        self.assertAlmostEqual(max(p[2] for p in path), 0.6, delta=0.08)

    def test_circle_closes(self):
        r, bot, t, path = run_plan(gl.build_plan('circle'))
        self.assertTrue(r.done, r.error)
        self.assertLess(math.hypot(bot.x, bot.y), 0.12)
        self.assertAlmostEqual(max(p[1] for p in path), 1.0, delta=0.06)   # đường kính 2r

    def test_time_fallback_without_odom(self):
        r, bot, t, path = run_plan(gl.build_plan('forward_back'), use_odom=False)
        self.assertTrue(r.done)
        self.assertFalse(r.used_odom)

    def test_stall_detected(self):
        r, bot, t, path = run_plan(gl.build_plan('forward_back'), blocked=True)
        self.assertIsNotNone(r.error)
        self.assertIn('không nhúc nhích', r.error)
        self.assertLess(t, 6.0)

    def test_odom_dropout_holds_progress(self):
        # odom mất 1 s giữa chừng: không được kết thúc đoạn sớm theo ước lượng thời gian
        plan = [gl.Segment('tien', 0.2, 0.0, 0.5, 'dist')]
        r = gl.SegmentRunner(plan)
        bot = FakeRobot()
        t = 0.0
        while t < 30 and not r.done and not r.error:
            drop = 1.0 <= t < 2.0
            cmd = r.update(t, None if drop else bot.pose())
            bot.step(cmd, 0.05)
            t += 0.05
        self.assertTrue(r.done, r.error)
        self.assertAlmostEqual(bot.x, 0.5, delta=0.06)

    def test_odom_lost_errors(self):
        r = gl.SegmentRunner([gl.Segment('tien', 0.2, 0.0, 2.0, 'dist')], stall_timeout=2.0)
        bot = FakeRobot()
        t = 0.0
        while t < 20 and not r.error:
            cmd = r.update(t, bot.pose() if t < 1.0 else None)
            bot.step(cmd, 0.05)
            t += 0.05
        self.assertIn('mất /odom', r.error)

    def test_progress(self):
        r = gl.SegmentRunner(gl.build_plan('greet'))
        self.assertEqual(r.overall_progress(), 0.0)
        run = run_plan(gl.build_plan('greet'))[0]
        self.assertEqual(run.overall_progress(), 1.0)

    def test_accel_limited(self):
        r = gl.SegmentRunner(gl.build_plan('forward_back'))
        bot = FakeRobot()
        prev = 0.0
        for i in range(40):
            cmd = r.update(i * 0.05, bot.pose())
            bot.step(cmd, 0.05)
            self.assertLessEqual(abs(cmd[0] - prev), 0.5 * 0.05 + 1e-6)
            prev = cmd[0]


class TestStateMachine(unittest.TestCase):
    def sm(self, **kw):
        m = gl.BehaviorStateMachine(**kw)
        m.on_message('None', 0.0)
        return m

    @staticmethod
    def kinds(actions):
        return [a[0] for a in actions]

    def test_needs_confirmation(self):
        m = self.sm()
        acts = m.on_message('Pointing_Up', 1.0)
        self.assertNotIn('start', self.kinds(acts))
        self.assertEqual(m.state, gl.SELECTED)
        self.assertEqual(m.selected, 'forward_back')
        m.on_message('None', 1.5)
        acts = m.on_message('Thumb_Up', 2.0)
        self.assertIn(('start', 'forward_back'), acts)
        self.assertEqual(m.state, gl.EXECUTING)

    def test_thumb_without_selection(self):
        m = self.sm()
        acts = m.on_message('Thumb_Up', 1.0)
        self.assertNotIn('start', self.kinds(acts))
        self.assertEqual(m.state, gl.IDLE)

    def test_victory_and_wave(self):
        m = self.sm()
        m.on_message('Victory', 1.0)
        self.assertEqual(m.selected, 'circle')
        m.on_message('Wave', 2.0)
        self.assertEqual(m.selected, 'greet')
        self.assertEqual(m.state, gl.SELECTED)
        m2 = self.sm(wave_requires_confirm=False)
        self.assertIn(('start', 'greet'), m2.on_message('Wave', 1.0))

    def test_held_gesture_triggers_once(self):
        m = self.sm()
        m.on_message('Victory', 1.0)
        m.on_message('None', 1.2)
        starts = 0
        for i in range(100):                      # giữ ngón cái 5 s
            starts += self.kinds(m.on_message('Thumb_Up', 2.0 + i * 0.05)).count('start')
        self.assertEqual(starts, 1)

    def test_cooldown(self):
        m = self.sm(cooldown=1.0)
        m.on_message('Victory', 1.0)
        m.on_message('None', 1.1)
        m.on_message('Thumb_Up', 1.2)            # chạy
        m.on_message('Open_Palm', 1.4)           # dừng
        m.on_message('None', 1.5)
        acts = m.on_message('Thumb_Up', 1.7)     # < 1 s sau lần trước -> bỏ qua
        self.assertNotIn('start', self.kinds(acts))
        m.on_message('None', 2.0)
        acts = m.on_message('Thumb_Up', 2.5)
        self.assertIn(('start', 'circle'), acts)

    def test_open_palm_stops_and_keeps_selection(self):
        m = self.sm()
        m.on_message('Victory', 1.0)
        m.on_message('Thumb_Up', 2.0)
        acts = m.on_message('Open_Palm', 3.0)
        self.assertEqual(acts[0][0], 'stop')
        self.assertEqual(m.state, gl.STOPPED)
        self.assertEqual(m.selected, 'circle')
        self.assertIsNone(m.active)
        acts = m.on_message('Thumb_Up', 4.5)
        self.assertIn(('start', 'circle'), acts)

    def test_resume_after_long_execution(self):
        # hành vi chạy 60 s rồi mới xoè tay: vẫn phải chạy lại được bằng ngón cái (lỗi tìm thấy khi chạy Gazebo)
        m = self.sm(selection_timeout=15.0)
        m.on_message('Victory', 1.0)
        m.on_message('Thumb_Up', 2.0)
        for t in range(3, 62):
            m.on_message('None', float(t))
            m.tick(float(t))
        self.assertEqual(m.state, gl.EXECUTING)
        m.on_message('Open_Palm', 62.0)
        m.on_message('None', 62.5)
        m.tick(63.0)
        self.assertEqual(m.state, gl.STOPPED)
        self.assertIn(('start', 'circle'), m.on_message('Thumb_Up', 64.0))

    def test_open_palm_no_cooldown(self):
        m = self.sm(cooldown=5.0)
        for t in (1.0, 1.2, 1.4):
            self.assertEqual(m.on_message('Open_Palm', t)[0][0], 'stop')
            m.on_message('None', t + 0.1)

    def test_fist_cancels(self):
        m = self.sm()
        m.on_message('Pointing_Up', 1.0)
        m.on_message('Thumb_Up', 2.0)
        acts = m.on_message('Closed_Fist', 3.0)
        self.assertEqual(acts[0][0], 'stop')
        self.assertEqual(m.state, gl.IDLE)
        self.assertIsNone(m.selected)
        self.assertNotIn('start', self.kinds(m.on_message('Thumb_Up', 4.5)))

    def test_ignore_selection_while_executing(self):
        m = self.sm()
        m.on_message('Pointing_Up', 1.0)
        m.on_message('Thumb_Up', 2.0)
        acts = m.on_message('Victory', 3.0)
        self.assertEqual(self.kinds(acts), ['info'])
        self.assertEqual(m.active, 'forward_back')

    def test_finish_clears_selection(self):
        m = self.sm()
        m.on_message('Pointing_Up', 1.0)
        m.on_message('Thumb_Up', 2.0)
        m.on_behavior_finished(True)
        self.assertEqual(m.state, gl.IDLE)
        self.assertIsNone(m.selected)
        m.on_message('None', 3.0)
        self.assertNotIn('start', self.kinds(m.on_message('Thumb_Up', 4.0)))

    def test_failure_stops(self):
        m = self.sm()
        m.on_message('Victory', 1.0)
        m.on_message('Thumb_Up', 2.0)
        acts = m.on_behavior_finished(False, 'vật cản')
        self.assertEqual(acts[0][0], 'stop')
        self.assertEqual(m.state, gl.STOPPED)

    def test_signal_lost(self):
        m = self.sm(signal_timeout=1.0)
        m.on_message('Victory', 1.0)
        m.on_message('Thumb_Up', 2.0)
        self.assertEqual(m.tick(2.5), [])
        acts = m.tick(3.2)
        self.assertEqual(acts[-1][0], 'stop')
        self.assertEqual(m.state, gl.SIGNAL_LOST)
        self.assertIsNone(m.active)
        m.on_message('None', 5.0)
        self.assertEqual(m.state, gl.IDLE)

    def test_no_watchdog_before_first_message(self):
        m = gl.BehaviorStateMachine()
        self.assertEqual(m.tick(100.0), [])
        self.assertEqual(m.state, gl.WAITING)

    def test_selection_timeout(self):
        m = self.sm(selection_timeout=5.0)
        m.on_message('Victory', 1.0)
        for t in range(2, 8):
            m.on_message('None', float(t))
            m.tick(float(t))
        self.assertEqual(m.state, gl.IDLE)
        self.assertIsNone(m.selected)

    def test_setup_phase(self):
        m = gl.BehaviorStateMachine()
        m.begin_setup()
        self.assertEqual(m.state, gl.SETUP)
        acts = m.on_message('Victory', 1.0)
        self.assertEqual(self.kinds(acts), ['info'])
        acts = m.on_message('Open_Palm', 1.5)
        self.assertIn('abort_setup', self.kinds(acts))
        m.end_setup(False)
        self.assertEqual(m.state, gl.IDLE)

    def test_describe_json(self):
        import json
        m = self.sm()
        json.dumps(m.describe())


class TestObstacle(unittest.TestCase):
    def test_front_and_back(self):
        n = 360
        inc = 2 * math.pi / n
        ranges = [5.0] * n
        # vật cản ở hướng +x của base_link; LiDAR quay +90° -> trong frame LiDAR là góc -90°
        idx = int(round((-math.pi / 2 - (-math.pi)) / inc))
        ranges[idx] = 0.3
        hit, d = gl.obstacle_in_path(ranges, -math.pi, inc, 0.15, 12.0, math.pi / 2, +1, 0.4, 0.6)
        self.assertTrue(hit)
        self.assertAlmostEqual(d, 0.3)
        hit, d = gl.obstacle_in_path(ranges, -math.pi, inc, 0.15, 12.0, math.pi / 2, -1, 0.4, 0.6)
        self.assertFalse(hit)

    def test_invalid_ranges_ignored(self):
        ranges = [float('inf'), float('nan'), 0.0, 0.01] * 90
        hit, d = gl.obstacle_in_path(ranges, -math.pi, 2 * math.pi / 360, 0.15, 12.0, 0.0, 1, 0.4, 0.6)
        self.assertFalse(hit)
        self.assertIsNone(d)


class TestNodeHelpers(unittest.TestCase):
    def test_camera_source(self):
        self.assertEqual(grn.parse_camera_source('0'), 0)
        self.assertEqual(grn.parse_camera_source(' 2 '), 2)
        self.assertEqual(grn.parse_camera_source(1), 1)
        self.assertEqual(grn.parse_camera_source('/dev/video2'), '/dev/video2')
        self.assertTrue(grn.parse_camera_source('~/a.mp4').endswith('/a.mp4'))

    def test_window_position(self):
        self.assertEqual(grn.parse_window_position('1000,40'), (1000, 40))
        self.assertIsNone(grn.parse_window_position(''))
        self.assertIsNone(grn.parse_window_position('abc'))

    def test_bundled_model(self):
        path = os.path.join(ROOT, 'models', grn.MODEL_FILE)
        self.assertTrue(os.path.isfile(path), 'thiếu models/gesture_recognizer.task')
        self.assertEqual(grn.sha256_of(path), grn.MODEL_SHA256)
        self.assertEqual(grn.resolve_model('', 'http://invalid', None), os.path.abspath(path))

    def test_sequence_parse(self):
        self.assertEqual(gs.parse_sequence('Victory:1.5, None:2'), [('Victory', 1.5), ('None', 2.0)])
        for name, seq in gs.PRESETS.items():
            for g, _ in gs.parse_sequence(seq):
                self.assertEqual(gl.canonical_gesture(g), g, name)


class TestConfig(unittest.TestCase):
    def test_gesture_yaml(self):
        with open(os.path.join(ROOT, 'config', 'gesture.yaml')) as f:
            d = yaml.safe_load(f)
        rec = d['gesture_recognition_node']['ros__parameters']
        beh = d['robot_behavior_node']['ros__parameters']
        self.assertIsInstance(rec['camera_source'], str)
        self.assertEqual(rec['gesture_topic'], '/detected_gesture')
        self.assertEqual(beh['gesture_topic'], '/detected_gesture')
        self.assertEqual(beh['cmd_vel_topic'], '/cmd_vel')
        self.assertEqual(int(beh['fb_repeats']), 4)
        for k in gl.DEFAULT_BEHAVIOR_PARAMS:
            self.assertIn(k, beh)

    def test_world(self):
        import xml.etree.ElementTree as ET
        root = ET.parse(os.path.join(ROOT, 'worlds', 'gesture_arena.sdf')).getroot()
        self.assertEqual(root.find('world').get('name'), 'gesture_arena')

    def test_cmake(self):
        with open(os.path.join(ROOT, 'CMakeLists.txt')) as f:
            cmake = f.read()
        for s in ('gesture_recognition_node.py', 'robot_behavior_node.py', 'webcam_test.py',
                  'check_cmd_vel.py', 'gesture_sequence.py', 'plot_gesture_run.py', 'gesture_logic.py'):
            self.assertIn('scripts/' + s, cmake)
        for s in ('gesture_recognition_node.py', 'robot_behavior_node.py', 'webcam_test.py',
                  'check_cmd_vel.py', 'gesture_sequence.py', 'plot_gesture_run.py', 'install_gesture_deps.sh'):
            self.assertTrue(os.access(os.path.join(ROOT, 'scripts', s), os.X_OK), s)
        self.assertIn('worlds', cmake)
        self.assertIn('models', cmake)


if __name__ == '__main__':
    unittest.main(verbosity=2)
