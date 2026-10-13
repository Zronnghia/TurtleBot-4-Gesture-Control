#!/usr/bin/env python3
"""Unit test cho phần logic thuần (không cần ROS đang chạy).

    cd ~/tb4_ws/src/tb4_lab04 && python3 -m pytest test/ -q     # hoặc
    python3 test/test_pure_logic.py

Phần kiểm tra hàm trong navigation.launch.py chỉ chạy khi import được `launch`
(tức là đã `source /opt/ros/humble/setup.bash`); nếu không sẽ tự bỏ qua.
"""
import importlib.util
import math
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from make_test_map import make_map  # noqa: E402


def load(rel_path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


check_sim = load('scripts/check_sim.py', 'check_sim')
compare_pose = load('scripts/compare_pose.py', 'compare_pose')
nav_monitor = load('scripts/nav_monitor.py', 'nav_monitor')
check_map = load('scripts/check_map.py', 'check_map')
explore = load('scripts/auto_explore.py', 'auto_explore')
clean_map = load('scripts/clean_map.py', 'clean_map')


def q(yaw):
    return 0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2)


class TestAngles(unittest.TestCase):
    def test_yaw_roundtrip(self):
        for yaw in (-3.0, -1.0, 0.0, 0.5, 3.1):
            self.assertAlmostEqual(check_sim.yaw_from_quaternion(*q(yaw)), yaw, places=9)
            self.assertAlmostEqual(compare_pose.yaw_from_quaternion(*q(yaw)), yaw, places=9)

    def test_wrap(self):
        for f in (check_sim.wrap_angle, compare_pose.wrap_angle):
            self.assertAlmostEqual(f(3 * math.pi / 2), -math.pi / 2)
            self.assertAlmostEqual(f(-3 * math.pi / 2), math.pi / 2)
            self.assertAlmostEqual(f(math.pi), math.pi)
            self.assertAlmostEqual(f(0.1), 0.1)


class TestScanGeometry(unittest.TestCase):
    def test_count_valid(self):
        self.assertEqual(check_sim.count_valid_ranges(
            [0.1, 0.5, float('inf'), float('nan'), 13.0, 12.0], 0.16, 12.0), 2)

    def test_rotated_lidar_front_obstacle(self):
        # LiDAR quay +90°: tia ở góc -90° (trong frame LiDAR) chính là phía trước robot.
        n = 360
        inc = 2 * math.pi / n
        ranges = [5.0] * n
        i_front = int(round((-math.pi / 2 - (-math.pi)) / inc))
        ranges[i_front] = 0.5
        pts = check_sim.scan_points_in_base(ranges, -math.pi, inc, 0.16, 12.0,
                                            0.0, 0.0, math.pi / 2)
        self.assertFalse(check_sim.path_is_clear(pts, 0.8, 0.25))
        ranges[i_front] = 5.0
        pts = check_sim.scan_points_in_base(ranges, -math.pi, inc, 0.16, 12.0,
                                            0.0, 0.0, math.pi / 2)
        self.assertTrue(check_sim.path_is_clear(pts, 0.8, 0.25))

    def test_obstacle_behind_is_ignored(self):
        pts = [(-0.3, 0.0), (0.5, 0.6), (1.5, 0.0)]
        self.assertTrue(check_sim.path_is_clear(pts, 0.8, 0.25))

    def test_stream_stats(self):
        s = check_sim.StreamStats()
        for i in range(11):
            s.add(100.0 + i * 0.2, 5.0 + i * 0.1)
        self.assertAlmostEqual(s.wall_rate(), 5.0)
        self.assertAlmostEqual(s.stamp_rate(), 10.0)
        self.assertEqual(check_sim.StreamStats().wall_rate(), 0.0)


class TestPoseCompare(unittest.TestCase):
    def test_world_to_map_identity(self):
        for a, b in zip(compare_pose.world_to_map(1.0, 2.0, 0.3, 0, 0, 0), (1.0, 2.0, 0.3)):
            self.assertAlmostEqual(a, b)

    def test_world_to_map_offset(self):
        x, y, yaw = compare_pose.world_to_map(1.0, 3.0, math.pi / 2 + 0.1,
                                              1.0, 2.0, math.pi / 2)
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(yaw, 0.1)

    def test_error(self):
        e_pos, e_yaw = compare_pose.pose_error((0, 0, math.pi - 0.05), (0.3, 0.4, -math.pi + 0.05))
        self.assertAlmostEqual(e_pos, 0.5)
        self.assertAlmostEqual(e_yaw, 0.1)

    def test_stats(self):
        s = compare_pose.ErrorStats()
        self.assertIsNone(s.summary())
        s.add(0.1, 0.02)
        s.add(0.3, 0.04)
        r = s.summary()
        self.assertAlmostEqual(r['mean_pos'], 0.2)
        self.assertAlmostEqual(r['max_yaw'], 0.04)


class TestGoalBook(unittest.TestCase):
    def test_lifecycle(self):
        b = nav_monitor.GoalBook()
        self.assertEqual(b.update('a', 2, 0.0), [('a', None, 2)])
        self.assertEqual(b.update('a', 2, 1.0), [])
        self.assertEqual(b.active(), ['a'])
        self.assertEqual(b.update('a', 4, 5.0), [('a', 2, 4)])
        self.assertEqual(b.goals['a']['t_end'], 5.0)
        b.update('b', 6, 6.0)
        b.update('c', 5, 7.0)
        self.assertEqual(b.active(), [])
        self.assertEqual(b.summary(), {'SUCCEEDED': 1, 'ABORTED': 1, 'CANCELED': 1, 'OTHER': 0})

    def test_goal_id(self):
        self.assertEqual(nav_monitor.goal_id_str([255, 1] + [0] * 14), 'ff010000')


class TestCheckMap(unittest.TestCase):
    def test_saver_format_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = make_map(d, free_thresh=0.15)
            r = check_map.analyze(path)
            self.assertEqual((r['width'], r['height']), (200, 150))
            self.assertEqual(r['unknown'], 40 * 30)
            self.assertEqual(r['occupied'], 200 * 150 - 196 * 146)
            self.assertEqual(r['free'], 196 * 146 - 40 * 30)
            self.assertEqual(check_map.main([path]), 0)

    def test_unknown_as_free_detected(self):
        self.assertTrue(check_map.unknown_loads_as_free(0.25))    # mặc định của map_saver_cli
        self.assertFalse(check_map.unknown_loads_as_free(0.15))   # save_map.sh dùng giá trị này
        self.assertFalse(check_map.unknown_loads_as_free(0.196))
        with tempfile.TemporaryDirectory() as d:
            path = make_map(d, free_thresh=0.25)
            r = check_map.analyze(path)
            self.assertEqual(r['unknown'], 0)                     # 205 bị đọc thành trống
            self.assertEqual(check_map.main([path]), 1)           # và bị cảnh báo

    def test_ascii_pgm_and_comments(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'a.pgm'), 'wb') as f:
                f.write(b'P2\n# c\n3 2\n# c2\n255\n254 0 205\n254 254 0\n')
            w, h, mx, px = check_map.read_pgm(os.path.join(d, 'a.pgm'))
            self.assertEqual((w, h, mx, px), (3, 2, 255, [254, 0, 205, 254, 254, 0]))

    def test_truncated_pgm(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'b.pgm')
            with open(p, 'wb') as f:
                f.write(b'P5\n10 10\n255\n' + bytes(50))
            with self.assertRaises(ValueError):
                check_map.read_pgm(p)

    def test_missing_file(self):
        self.assertEqual(check_map.main(['/khong/ton/tai/map.yaml']), 1)


try:
    import launch  # noqa: F401
    import launch_ros  # noqa: F401
    HAVE_LAUNCH = True
except ImportError:
    HAVE_LAUNCH = False


@unittest.skipUnless(HAVE_LAUNCH, 'cần source ROS 2 Humble (thiếu module launch)')
class TestNavigationLaunchHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nav = load('launch/navigation.launch.py', 'navigation_launch')

    def test_find_and_validate(self):
        with tempfile.TemporaryDirectory() as share, tempfile.TemporaryDirectory() as src:
            os.makedirs(os.path.join(src, 'maps'))
            with open(os.path.join(share, 'source_dir.txt'), 'w') as f:
                f.write(src + '\n')
            path, err = self.nav.find_map('', share)
            self.assertIsNone(path)
            self.assertIn('Chưa có bản đồ', err)
            make_map(os.path.join(src, 'maps'))
            path, err = self.nav.find_map('', share)
            self.assertEqual(path, os.path.join(src, 'maps', 'map.yaml'))
            self.assertIsNone(self.nav.validate_map_yaml(path))
            os.remove(os.path.join(src, 'maps', 'map.pgm'))
            self.assertIn('không tồn tại', self.nav.validate_map_yaml(path))

    def test_explicit_path_relative(self):
        with tempfile.TemporaryDirectory() as d:
            make_map(d)
            old = os.getcwd()
            os.chdir(d)
            try:
                path, err = self.nav.find_map('map.yaml', '/nonexistent')
            finally:
                os.chdir(old)
            self.assertIsNone(err)
            self.assertTrue(os.path.isabs(path))
            path, err = self.nav.find_map('/khong/co.yaml', '/nonexistent')
            self.assertIsNone(path)

    def test_bad_yaml(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.yaml')
            for content, needle in (('- a\n- b\n', 'không phải'), ('image: a.pgm\n', 'thiếu'),
                                    ('image: [\n', 'Không đọc được')):
                with open(p, 'w') as f:
                    f.write(content)
                self.assertIn(needle, self.nav.validate_map_yaml(p))


@unittest.skipUnless(HAVE_LAUNCH, 'cần source ROS 2 Humble (thiếu module launch)')
class TestLaunchCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.common = load('launch/tb4_lab04_common.py', 'tb4_lab04_common_test')

    def test_missing_package_message_has_apt_command(self):
        msg = self.common.missing_packages_message(['goi_khong_ton_tai_abc', 'nav2_khong_co'])
        self.assertIn('THIẾU GÓI ROS', msg)
        self.assertIn('sudo apt install -y ros-humble-goi-khong-ton-tai-abc ros-humble-nav2-khong-co',
                      msg)
        self.assertIsNotNone(self.common.abort_if_missing(['goi_khong_ton_tai_abc']))

    def test_present_package_passes(self):
        self.assertIsNone(self.common.missing_packages_message(['launch']))   # luôn có khi đã source ROS 2
        self.assertIsNone(self.common.abort_if_missing(['launch']))

    def test_worlds_and_package_lists(self):
        self.assertEqual(self.common.WORLDS, ['maze', 'depot', 'warehouse'])
        self.assertIn('topic_tools', self.common.PKGS_NAV)   # /scan_nav cần topic_tools/delay
        self.assertIn('slam_toolbox', self.common.PKGS_SLAM)

    def test_after_sim_ready_skips_when_shutting_down(self):
        """Ctrl+C lúc đang chờ Gazebo -> wait_for_sim thoát -> KHÔNG được bật SLAM/Nav2 nữa."""
        from launch import LaunchContext
        from launch.actions import LogInfo
        acts = [LogInfo(msg='a'), LogInfo(msg='b')]
        handler = self.common.after_sim_ready(self.common.wait_for_sim_node(), acts).event_handler
        ctx = LaunchContext()
        self.assertEqual(handler.handle(object(), ctx), acts)
        ctx._set_is_shutdown(True)
        self.assertEqual(handler.handle(object(), ctx), [])


class TestFrontierExploration(unittest.TestCase):
    """Logic frontier của auto_explore.py trên bản đồ giả (0.05 m/ô)."""
    RES = 0.05

    def room(self, h=60, w=60):
        import numpy as np
        g = np.full((h, w), -1, dtype=np.int16)      # mọi thứ chưa biết
        g[5:55, 5:55] = 0                             # phòng trống 2.5 x 2.5 m
        g[5, 5:55] = g[54, 5:55] = 100                # tường
        g[5:55, 5] = g[5:55, 54] = 100
        return g

    def test_shift_and_dilate(self):
        import numpy as np
        m = np.zeros((5, 5), dtype=bool)
        m[2, 2] = True
        self.assertTrue(explore.shift(m, 1, 0)[3, 2])
        self.assertTrue(explore.shift(m, 0, -2)[2, 0])
        self.assertEqual(int(explore.dilate(m, 1).sum()), 5)      # chữ thập
        self.assertEqual(int(explore.dilate(m, 2).sum()), 13)

    def test_closed_room_has_no_frontier(self):
        cands, groups, start = explore.find_candidates(self.room(), (30, 30), self.RES)
        self.assertEqual(cands, [])
        self.assertEqual(groups, 0)
        self.assertEqual(start, (30, 30))

    def test_door_to_unknown_is_reachable_frontier(self):
        g = self.room()
        g[25:35, 54] = 0                              # cửa rộng 0.5 m ở tường phải
        g[25:35, 55] = -1
        cands, _, _ = explore.find_candidates(g, (30, 15), self.RES)
        self.assertEqual(len(cands), 1)
        c = cands[0]
        self.assertTrue(25 <= c.goal_cell[0] < 35)
        self.assertGreater(c.goal_cell[1], 40)        # goal nằm gần cửa
        self.assertGreater(c.path_cells, 20)

    def test_narrow_gap_robot_only_looks_through(self):
        g = self.room()
        g[29:32, 54] = 0                              # khe 0.15 m < đường kính robot
        g[20:40, 55:59] = 0                           # vùng trống thấy qua khe
        g[20:40, 59] = -1                             # xa hơn: chưa biết
        cands, _, _ = explore.find_candidates(g, (30, 15), self.RES, min_frontier_cells=2)
        # Được phép tới SÁT khe để nhìn qua, nhưng không có goal nào ở phía bên kia khe,
        # và cụm frontier xa (cột 58) không được chọn vì không tới được.
        self.assertTrue(all(c.goal_cell[1] < 54 for c in cands))
        self.assertTrue(all(c.frontier_cell[1] < 58 for c in cands))

    def test_unknown_pocket_behind_wall_is_not_reachable(self):
        g = self.room()
        g[30, 6:54] = 100                             # tường ngăn đôi phòng
        g[40:45, 20:30] = -1                          # vùng chưa biết ở nửa dưới
        cands, groups, _ = explore.find_candidates(g, (15, 30), self.RES)
        self.assertGreaterEqual(groups, 1)
        self.assertEqual(cands, [])                   # robot ở nửa trên không tới được
        cands, _, _ = explore.find_candidates(g, (48, 30), self.RES)
        self.assertEqual(len(cands), 1)               # robot ở nửa dưới thì tới được

    def test_small_cluster_is_noise(self):
        g = self.room()
        g[30, 30] = -1                                # 1 ô chưa biết -> cụm 4 ô
        self.assertEqual(explore.find_candidates(g, (15, 15), self.RES)[0], [])
        self.assertEqual(len(explore.find_candidates(g, (15, 15), self.RES,
                                                     min_frontier_cells=2)[0]), 1)

    def test_robot_against_wall_still_plans(self):
        g = self.room()
        g[25:35, 54] = 0
        g[25:35, 55] = -1
        cands, _, start = explore.find_candidates(g, (7, 7), self.RES)   # sát góc tường
        self.assertIsNotNone(start)
        self.assertEqual(len(cands), 1)

    def test_nearest_first_with_size_bonus(self):
        a = explore.Candidate((0, 0), (0, 0), size=10, path_cells=40, centroid=(0, 0))
        b = explore.Candidate((0, 0), (0, 0), size=10, path_cells=200, centroid=(0, 0))
        self.assertLess(explore.score(a, self.RES), explore.score(b, self.RES))

    def test_frontier_still_there(self):
        g = self.room()
        g[25:35, 54] = 0
        g[25:35, 55] = -1
        self.assertTrue(explore.frontier_still_there(g, (30, 54), 6))
        self.assertFalse(explore.frontier_still_there(g, (30, 20), 6))
        g[25:35, 55] = 100                            # đã quét: cửa thành tường
        self.assertFalse(explore.frontier_still_there(g, (30, 54), 6))

    def test_lidar_streak_inside_wall_block_is_ignored(self):
        g = self.room()
        g[20:40, 20:40] = -1                          # khối tường chưa biết bên trong
        g[20, 20:40] = g[39, 20:40] = g[20:40, 20] = g[20:40, 39] = 100
        for i in range(21, 39):                       # vệt tia LiDAR lọt vào (rộng 1 ô)
            g[i, i] = 0
        cands, _, _ = explore.find_candidates(g, (10, 10), self.RES, min_frontier_cells=2)
        self.assertEqual(cands, [])

    def test_blocked_frontier_is_skipped(self):
        g = self.room()
        g[25:35, 54] = 0
        g[25:35, 55] = -1
        blocked = explore.stamp_discs(g.shape, [(30, 54)], 6)
        self.assertEqual(explore.find_candidates(g, (30, 15), self.RES, blocked=blocked)[0], [])
        small = explore.stamp_discs(g.shape, [(26, 54)], 1)   # chỉ chặn 1 đầu cụm
        self.assertEqual(len(explore.find_candidates(g, (30, 15), self.RES, min_frontier_cells=2,
                                                     blocked=small)[0]), 1)

    def test_lidar_leak_through_wall_gap_is_ignored(self):
        g = self.room()
        g[20:40, 20:40] = -1                          # khối tường rỗng (chưa biết bên trong)
        g[20, 20:40] = g[39, 20:40] = g[20:40, 20] = g[20:40, 39] = 100
        g[20, 21] = 0                                 # khe 1 ô ở góc
        g[21:30, 21:30] = 0                           # vùng "trống" do tia lọt vào
        cands, _, _ = explore.find_candidates(g, (10, 10), self.RES)
        self.assertEqual(cands, [])

    def test_known_cells_around(self):
        g = self.room()
        self.assertEqual(explore.known_cells_around(g, (30, 30), 2), 13)
        g[29:32, 29:32] = -1
        self.assertEqual(explore.known_cells_around(g, (30, 30), 2), 13 - 9)
        self.assertEqual(explore.known_cells_around(g, (0, 0), 2), 0)   # góc: toàn chưa biết

    def test_place_key(self):
        self.assertEqual(explore.place_key(0.1, 0.2), explore.place_key(0.4, 0.45))
        self.assertNotEqual(explore.place_key(0.1, 0.2), explore.place_key(0.6, 0.2))


class TestCleanMap(unittest.TestCase):
    """clean_map.py: xoá vệt trắng trong khối tường, bịt khe nhỏ, không đụng lối đi thật."""

    def base(self):
        import numpy as np
        img = np.full((60, 60), 254, dtype=np.uint8)            # sàn trống
        img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = 0      # tường bao
        img[20:40, 20:40] = 205                                  # khối tường rỗng
        img[20, 20:40] = img[39, 20:40] = img[20:40, 20] = img[20:40, 39] = 0
        return img

    def test_leak_inside_block_removed_and_gap_plugged(self):
        img = self.base()
        img[20, 25] = 254                       # khe 1 ô
        img[21:30, 21:30] = 254                 # vệt trắng bên trong khối
        out, plugged, orphan = clean_map.clean(img, (5, 5))
        self.assertEqual(out[20, 25], 0)        # khe đã thành tường
        self.assertTrue((out[21:30, 21:30] == 205).all())
        self.assertGreaterEqual(plugged, 1)
        self.assertEqual(orphan, 81)

    def test_real_doorway_is_kept(self):
        img = self.base()
        img[20, 25:33] = 254                    # cửa rộng 8 ô (0.4 m) – lối thật
        img[21:39, 21:39] = 254                 # phòng bên trong
        out, plugged, orphan = clean_map.clean(img, (5, 5))
        self.assertEqual(orphan, 0)
        self.assertTrue((out[21:39, 21:39] == 254).all())
        self.assertTrue((out[20, 27:31] == 254).all())

    def test_clean_map_is_unchanged(self):
        img = self.base()
        out, plugged, orphan = clean_map.clean(img, (5, 5))
        self.assertEqual((plugged, orphan), (0, 0))
        self.assertTrue((out == img).all())

    def test_seed_on_wall_falls_back(self):
        img = self.base()
        img[21:30, 21:30] = 254                 # túi trống kín (không khe)
        out, _, orphan = clean_map.clean(img, (0, 0))   # điểm xuất phát nằm trên tường bao
        self.assertEqual(orphan, 81)


check_sensors = load('scripts/check_sensors.py', 'check_sensors')


class TestSensorHealth(unittest.TestCase):
    """check_sensors.py: phân biệt LiDAR/cliff bình thường với LiDAR 'mù' do render hỏng."""

    def test_normal_maze_scan_ok(self):
        ranges = [1.0 + 3.0 * abs(math.sin(i * 0.01)) for i in range(640)]
        ranges[5] = float('inf')
        self.assertEqual(check_sensors.scan_health(ranges, 0.164, 12.0)['verdict'], 'ok')

    def test_scan_stuck_at_range_min_is_blind(self):
        # Triệu chứng máy người dùng: SLAM chỉ vẽ được 7 x 7 ô (~0.35 m) quanh robot.
        ranges = [0.164] * 600 + [0.5] * 40
        h = check_sensors.scan_health(ranges, 0.164, 12.0)
        self.assertEqual(h['verdict'], 'near_min')
        self.assertGreater(h['frac_near_min'], 0.9)

    def test_scan_all_inf_or_all_close(self):
        self.assertEqual(check_sensors.scan_health([float('inf')] * 640, 0.164, 12.0)['verdict'],
                         'no_returns')
        self.assertEqual(check_sensors.scan_health([0.4] * 640, 0.164, 12.0)['verdict'],
                         'all_close')
        self.assertEqual(check_sensors.scan_health([], 0.164, 12.0)['verdict'], 'empty')

    def test_cliff_like_create3(self):
        # Giá trị thật trong môi trường thử khi robot đứng trên sàn: [0.0157, 0.0] -> không báo.
        self.assertFalse(check_sensors.cliff_triggered([0.0157, 0.0]))
        self.assertTrue(check_sensors.cliff_triggered([0.15, 0.15]))       # hụt chân
        self.assertTrue(check_sensors.cliff_triggered([float('inf')] * 2))  # render hỏng
        self.assertFalse(check_sensors.cliff_triggered([float('nan'), 0.01]))


class TestUndockGeometry(unittest.TestCase):
    """auto_explore.py: xác định robot đã rời dock ĐÚNG CÁCH (xa dock, mặt quay ra ngoài)."""

    def setUp(self):
        self.dock = explore.dock_body_xy(explore.DEFAULT_DOCK_POSE)

    def test_dock_body_position(self):
        x, y = self.dock
        self.assertAlmostEqual(x, 0.202, places=3)   # 0.157 + 0.045 (dock quay pi)
        self.assertAlmostEqual(y, 0.0, places=6)

    def test_still_docked_facing_dock_is_not_ok(self):
        ok, d, err = explore.undock_state((0.0, 0.0, 0.0), self.dock)
        self.assertFalse(ok)
        self.assertLess(d, 0.25)
        self.assertGreater(err, math.radians(170))

    def test_cancelled_undock_few_cm_is_not_ok(self):
        # Kết quả thực của người dùng: x = -0.018 sau undock CANCELED.
        ok, _, _ = explore.undock_state((-0.018, 0.0, 0.0), self.dock)
        self.assertFalse(ok)

    def test_normal_undock_is_ok(self):
        # Đo trong môi trường thử: lùi tới x = -0.353, quay tới -169 độ.
        ok, d, err = explore.undock_state((-0.353, 0.0, math.radians(-169)), self.dock)
        self.assertTrue(ok)
        self.assertAlmostEqual(d, 0.555, places=2)
        self.assertLess(err, math.radians(15))

    def test_backed_off_but_still_facing_dock_is_not_ok(self):
        ok, _, _ = explore.undock_state((-0.353, 0.0, 0.0), self.dock)
        self.assertFalse(ok)

    def test_front_free_distance(self):
        pts = [(1.0, 0.0), (0.5, 0.5), (0.3, -0.25), (-0.2, 0.0)]
        self.assertAlmostEqual(explore.front_free_distance(pts, half_width=0.2), 1.0)
        self.assertAlmostEqual(explore.front_free_distance(pts, half_width=0.3), 0.3)
        self.assertEqual(explore.front_free_distance([], max_x=5.0), 5.0)


class TestViewBasedGoals(unittest.TestCase):
    """Chọn chỗ đứng nhìn được frontier từ chỗ thoáng (không chui sát góc tường)."""

    def test_visible_from_blocked_by_wall(self):
        import numpy as np
        free = np.ones((20, 20), dtype=bool)
        free[0:16, 10] = False                      # bức tường dọc
        vis, d = explore.visible_from(free, [(5, 5)], 12)
        self.assertTrue(vis[5, 8])
        self.assertAlmostEqual(d[5, 8], 3.0, delta=0.6)
        self.assertFalse(vis[5, 15])                # sau tường
        self.assertFalse(vis[5, 10])                # chính tường

    def test_viewpoint_must_see_past_frontier(self):
        import numpy as np
        free = np.ones((40, 40), dtype=bool)
        unknown = np.zeros((40, 40), dtype=bool)
        free[0:10, :] = False
        unknown[0:10, :] = True                      # phía bắc chưa biết, frontier ở hàng 10
        vis, _ = explore.visible_from(free, [(10, 20)], 15, unknown=unknown)
        self.assertTrue(vis[20, 20])                 # đứng phía nam: nhìn xuyên frontier vào vùng chưa biết
        self.assertFalse(vis[10, 30])                # đứng cùng hàng: chỉ nhìn dọc mép, không thấy gì mới
        vis_all, _ = explore.visible_from(free, [(10, 20)], 15)
        self.assertTrue(vis_all[10, 30])             # không xét unknown thì vẫn "thấy"

    def corner_room(self):
        import numpy as np
        g = np.zeros((100, 100), dtype=np.int16)     # phòng 5 x 5 m, 0.05 m/ô, đã biết là trống
        g[0, :] = g[-1, :] = g[:, 0] = g[:, -1] = 100
        g[1:12, 1:12] = -1                           # góc trên-trái chưa biết (sát 2 bức tường)
        return g

    @staticmethod
    def clearance_cells(g, cell):
        import numpy as np
        occ = np.argwhere(g >= 65)
        return float(np.sqrt(((occ - np.array(cell)) ** 2).sum(axis=1)).min())

    def test_goal_keeps_clearance_and_sees_frontier(self):
        g = self.corner_room()
        cands, _, _ = explore.find_candidates(g, (80, 80), 0.05, robot_radius=0.22,
                                              min_frontier_cells=4, view_radius=1.5, clearance=0.4)
        self.assertEqual(len(cands), 1)
        c = cands[0]
        self.assertGreaterEqual(self.clearance_cells(g, c.goal_cell), 8.0)   # >= 0.4 m tới tường
        free = (g >= 0) & (g < 25)
        (r0, c0), (r1, c1) = c.frontier_cell, c.goal_cell
        n = int(max(abs(r1 - r0), abs(c1 - c0)) * 2) + 1
        line = [(round(r0 + (r1 - r0) * i / n), round(c0 + (c1 - c0) * i / n)) for i in range(n + 1)]
        self.assertTrue(all(free[p] for p in line))                           # nhìn thẳng tới frontier
        self.assertLessEqual(((r1 - r0) ** 2 + (c1 - c0) ** 2) ** 0.5, 30.5)   # trong view_radius

    def test_old_mode_unchanged_when_view_disabled(self):
        g = self.corner_room()
        cands, _, _ = explore.find_candidates(g, (80, 80), 0.05, robot_radius=0.22,
                                              min_frontier_cells=4)
        self.assertEqual(len(cands), 1)
        # không có view/clearance: chỗ đứng sát frontier (<= approach_radius 0.35 m = 7 ô)
        fr = cands[0].frontier_cell
        gc = cands[0].goal_cell
        self.assertLessEqual(((fr[0] - gc[0]) ** 2 + (fr[1] - gc[1]) ** 2) ** 0.5, 7.5)

    def test_avoided_viewpoint_gives_another_view_not_dropped_cluster(self):
        """Đứng ở chỗ tốt nhất mà không quét thêm được (bị che) -> lần sau phải chọn chỗ đứng KHÁC cho
        cùng cụm (lỗi cũ: bỏ cả cụm -> góc khuyết trên bản đồ)."""
        g = self.corner_room()
        first, _, _ = explore.find_candidates(g, (80, 80), 0.05, robot_radius=0.22, min_frontier_cells=4,
                                              view_radius=1.5, clearance=0.4)
        g1 = first[0].goal_cell
        avoid = explore.stamp_discs(g.shape, [g1], 12)          # 0.6 m quanh chỗ đứng đã thất bại
        again, _, _ = explore.find_candidates(g, (80, 80), 0.05, robot_radius=0.22, min_frontier_cells=4,
                                              view_radius=1.5, clearance=0.4, avoid=avoid)
        self.assertEqual(len(again), 1)                         # cụm vẫn còn
        g2 = again[0].goal_cell
        self.assertGreater(((g1[0] - g2[0]) ** 2 + (g1[1] - g2[1]) ** 2) ** 0.5, 12.0)
        self.assertFalse(avoid[g2])
        # mọi chỗ đứng đều bị loại -> cụm mới bị bỏ
        import numpy as np
        none, _, _ = explore.find_candidates(g, (80, 80), 0.05, robot_radius=0.22, min_frontier_cells=4,
                                             view_radius=1.5, clearance=0.4,
                                             avoid=np.ones(g.shape, dtype=bool))
        self.assertEqual(none, [])


class TestEscapeStuck(unittest.TestCase):
    """Hình học cho bước tự gỡ kẹt của auto_explore.py (robot tì sát góc tường)."""

    @staticmethod
    def wall(x0, y0, x1, y1, n=40):
        return [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(n + 1)]

    def test_corner_points_to_open_side(self):
        # Tường ngay trước mặt (x = 0.2) và bên trái (y = 0.2): hướng thoáng nhất phải ở nửa phải/sau.
        pts = self.wall(0.2, -2.0, 0.2, 2.0) + self.wall(-2.0, 0.2, 0.2, 0.2)
        h, c = explore.best_open_heading(pts)
        self.assertLess(h, -0.5)            # quay sang phải / ra sau
        self.assertGreater(c, 1.0)          # hướng đó thật sự thoáng

    def test_open_ahead_prefers_no_turn(self):
        h, c = explore.best_open_heading([])
        self.assertEqual(h, 0.0)

    def test_rear_free_distance(self):
        pts = [(-0.5, 0.0), (-0.3, 0.5), (0.4, 0.0)]
        self.assertAlmostEqual(explore.rear_free_distance(pts), 0.5)
        self.assertEqual(explore.rear_free_distance([(1.0, 0.0)], max_x=5.0), 5.0)

    def test_side_wall_does_not_block_escape(self):
        # Robot tì sát tường bên trái (y = 0.18, thân 0.17 m), trước/sau thoáng: lỗi cũ (hành lang 0.2 m)
        # tính điểm tường hông là "chắn trước/sau 0 m" -> không nhúc nhích -> dừng vì kẹt.
        pts = self.wall(-3.0, 0.18, 3.0, 0.18, n=240)
        self.assertLess(explore.front_free_distance(pts, half_width=0.2), 0.05)       # hành vi cũ
        self.assertGreater(explore.front_free_distance(pts, half_width=0.15), 3.0)
        self.assertGreater(explore.rear_free_distance(pts, half_width=0.15), 3.0)
        near = explore.nearest_obstacle(pts)
        self.assertAlmostEqual(near[1], 0.18, places=2)
        self.assertAlmostEqual(near[0], math.pi / 2, places=1)
        h, c = explore.best_open_heading(pts, avoid=(near[0], math.radians(100.0)))
        self.assertLess(h, -0.15)           # quay lưng lại bức tường (sang phải), không đi dọc sát tường
        self.assertGreater(c, 1.0)
        self.assertIsNone(explore.nearest_obstacle([]))


class TestDockObstacle(unittest.TestCase):
    def test_points_cover_dock_body(self):
        try:
            mod = load('scripts/dock_obstacle.py', 'dock_obstacle')
        except ImportError as exc:  # cần rclpy/sensor_msgs_py
            self.skipTest('không có ROS: {}'.format(exc))
        pts = mod.dock_points(*mod.DEFAULT_DOCK)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # Thân dock (collision box) nằm ở x 0.182..0.222, |y| <= 0.065 trong odom.
        self.assertLessEqual(min(xs), 0.182)
        self.assertGreaterEqual(max(xs), 0.222)
        self.assertLessEqual(min(ys), -0.065)
        self.assertGreaterEqual(max(ys), 0.065)
        # Có biên an toàn ngang (lần thử đầu |y| <= 0.08 thì robot chạm góc dock khi đi ngang qua).
        self.assertLessEqual(min(ys), -0.15)
        self.assertGreaterEqual(max(ys), 0.15)
        # Không lấn vào chỗ robot đứng khi đã undock (x ~ -0.35): mép gần nhất cách >= 0.4 m.
        self.assertGreater(min(xs), 0.05)
        self.assertGreater(min(xs) - (-0.353), 0.4)


if __name__ == '__main__':
    unittest.main(verbosity=2)
