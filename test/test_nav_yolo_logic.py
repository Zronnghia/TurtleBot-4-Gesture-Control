#!/usr/bin/env python3
"""Unit test cho phần logic thuần của bài Navigation tự động + YOLO (không cần ROS đang chạy).

    cd ~/workspaces/tb4_gazebo/src/tb4_lab04 && python3 -m pytest test/ -q     # hoặc
    python3 test/test_nav_yolo_logic.py
"""
import importlib.util
import math
import os
import sys
import tempfile
import unittest

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
sys.path.insert(0, HERE)


def load(rel_path, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lc = load('scripts/lab_common.py', 'lab_common')
cg = load('scripts/check_goals.py', 'check_goals')
wn = load('scripts/waypoint_navigator.py', 'waypoint_navigator')
so = load('scripts/spawn_objects.py', 'spawn_objects')
yd = load('scripts/yolo_detector.py', 'yolo_detector')
gr = load('scripts/goal_recorder.py', 'goal_recorder')
lcheck = load('scripts/localization_check.py', 'localization_check')

MAP = os.path.join(ROOT, 'maps', 'map.yaml')
GOALS = os.path.join(ROOT, 'config', 'goals.yaml')
OBJECTS = os.path.join(ROOT, 'config', 'objects.yaml')


def write_map(tmp, pixels, res=0.1, origin=(0.0, 0.0, 0.0), p2=False):
    h, w = pixels.shape
    pgm = os.path.join(tmp, 'm.pgm')
    with open(pgm, 'wb') as f:
        if p2:
            f.write('P2\n# test\n{} {}\n255\n'.format(w, h).encode())
            f.write(' '.join(str(int(v)) for v in pixels.flatten()).encode())
        else:
            f.write('P5\n{} {}\n255\n'.format(w, h).encode())
            f.write(pixels.astype(np.uint8).tobytes())
    yml = os.path.join(tmp, 'm.yaml')
    with open(yml, 'w') as f:
        yaml.safe_dump({'image': 'm.pgm', 'resolution': res, 'origin': list(origin), 'negate': 0,
                        'occupied_thresh': 0.65, 'free_thresh': 0.15, 'mode': 'trinary'}, f)
    return yml


def corridor_map(tmp, p2=False):
    """10 x 4 m, tường bao quanh (0.1 m/ô), một cột chắn giữa có khe 1.2 m ở trên."""
    img = np.full((40, 100), 254, np.uint8)
    img[0, :] = img[-1, :] = 0
    img[:, 0] = img[:, -1] = 0
    img[12:, 50] = 0                  # hàng 0 = mép TRÊN ảnh = y lớn nhất
    img[30:34, 80:84] = 205           # ô chưa biết
    return write_map(tmp, img, p2=p2)


class TestLabCommon(unittest.TestCase):
    def test_angles(self):
        for yaw in (-3.1, -1.0, 0.0, 0.7, 3.1):
            self.assertAlmostEqual(lc.yaw_from_quat(*lc.quat_from_yaw(yaw)), yaw, places=9)
        self.assertAlmostEqual(lc.normalize_angle(3 * math.pi / 2), -math.pi / 2)
        self.assertAlmostEqual(lc.normalize_angle(math.pi), math.pi)
        self.assertAlmostEqual(lc.normalize_angle(-math.pi), math.pi)

    def test_find_config_source(self):
        path, tried = lc.find_config('config', 'goals.yaml')
        self.assertTrue(path and os.path.isfile(path), tried)

    def test_results_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get('TB4_RESULTS_DIR')
            os.environ['TB4_RESULTS_DIR'] = tmp
            try:
                d = lc.results_dir('a', 'b')
                self.assertTrue(os.path.isdir(d) and d.startswith(tmp))
            finally:
                if old is None:
                    del os.environ['TB4_RESULTS_DIR']
                else:
                    os.environ['TB4_RESULTS_DIR'] = old


class TestGridMap(unittest.TestCase):
    def test_read_p5_p2_same(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = cg.GridMap(corridor_map(tmp)).occ
        with tempfile.TemporaryDirectory() as tmp:
            b = cg.GridMap(corridor_map(tmp, p2=True)).occ
        self.assertTrue((a == b).all())

    def test_trinary_and_orientation(self):
        with tempfile.TemporaryDirectory() as tmp:
            gm = cg.GridMap(corridor_map(tmp))
        self.assertEqual(gm.occ.shape, (40, 100))
        # mép TRÊN ảnh -> hàng cuối của occ (y lớn nhất)
        self.assertEqual(gm.occ[-1, 10], 100)
        i, j = gm.to_cell(2.0, 2.0)
        self.assertEqual(gm.occ[j, i], 0)
        # ô chưa biết ở ảnh hàng 30..33 -> y = (40-34..40-30)*0.1
        i, j = gm.to_cell(8.15, 0.75)
        self.assertEqual(gm.occ[j, i], -1)

    def test_repo_map_loads(self):
        gm = cg.GridMap(MAP)
        self.assertGreater((gm.occ == 0).sum(), 50000)
        self.assertAlmostEqual(gm.res, 0.05)


class TestGoalsFile(unittest.TestCase):
    def test_repo_goals(self):
        init, goals = cg.load_goals(GOALS)
        self.assertEqual(init, (0.0, 0.0, 0.0))
        self.assertGreaterEqual(len(goals), 3)

    def _load(self, text):
        with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as f:
            f.write(text)
        try:
            return cg.load_goals(f.name)
        finally:
            os.unlink(f.name)

    def test_yaw_deg_and_default_name(self):
        _, goals = self._load('goals:\n  - {x: 1, y: 2, yaw_deg: 90}\n  - {x: 0, y: 0, yaw: 7.0}\n')
        self.assertAlmostEqual(goals[0]['yaw'], math.pi / 2)
        self.assertEqual(goals[0]['name'], 'Goal 1')
        self.assertAlmostEqual(goals[1]['yaw'], lc.normalize_angle(7.0))

    def test_errors(self):
        for text in ('goals: []\n', 'goals:\n  - {x: 1}\n', 'foo: 1\n', 'goals:\n  - {x: a, y: 1}\n',
                     'goals:\n  - {x: .nan, y: 1}\n', '- 1\n- 2\n'):
            with self.assertRaises(ValueError, msg=text):
                self._load(text)


class TestAnalyse(unittest.TestCase):
    def test_repo_scenario_valid(self):
        """Toạ độ mẫu của repo: không lỗi, mỗi goal nhìn thấy ít nhất 1 vật thể đúng thiết kế."""
        gm = cg.GridMap(MAP)
        init, goals = cg.load_goals(GOALS)
        objs = cg.load_objects(OBJECTS)
        res = cg.analyse(gm, init, goals, objs)
        self.assertEqual([i for i in res['issues'] if i[0] == 'LỖI'], [])
        for k in range(len(goals)):
            self.assertTrue(any(v['visible'] for v in res['views'][k]), 'G{}'.format(k + 1))
            self.assertGreaterEqual(res['legs'][k]['clearance'], 0.6)
        seen = {v['object'] for k in res['views'] for v in res['views'][k] if v['visible']}
        self.assertTrue({'car_1', 'person_2', 'chair_1', 'fire_hydrant_1', 'person_3'} <= seen, seen)

    def test_detects_bad_goals(self):
        with tempfile.TemporaryDirectory() as tmp:
            gm = cg.GridMap(corridor_map(tmp))
        init = (1.0, 2.0, 0.0)
        goals = [{'name': 'ok', 'x': 8.0, 'y': 2.8, 'yaw': 0.0},          # qua khe phía trên
                 {'name': 'wall', 'x': 5.05, 'y': 1.0, 'yaw': 0.0},
                 {'name': 'unknown', 'x': 8.15, 'y': 0.75, 'yaw': 0.0},
                 {'name': 'outside', 'x': 20.0, 'y': 1.0, 'yaw': 0.0},
                 {'name': 'near', 'x': 9.75, 'y': 2.0, 'yaw': 0.0}]
        res = cg.analyse(gm, init, goals, [])
        text = '\n'.join(m for _, m in res['issues'])
        self.assertIsNotNone(res['legs'][0]['length'])
        self.assertIn('Goal 2 (wall): nằm trên tường', text)
        self.assertIn('Goal 3 (unknown): nằm trên vùng CHƯA BIẾT', text)
        self.assertIn('Goal 4 (outside)', text)
        self.assertIn('Goal 5 (near): cách vật cản', text)

    def test_object_blocks_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            gm = cg.GridMap(corridor_map(tmp))
        goals = [{'name': 'g', 'x': 8.0, 'y': 2.8, 'yaw': 0.0}]
        blocker = {'name': 'b', 'x': 5.0, 'y': 3.4, 'footprint': {'radius': 0.6}}
        res = cg.analyse(gm, (1.0, 2.0, 0.0), goals, [blocker])
        self.assertIsNone(res['legs'][0]['length'])
        self.assertTrue(any('KHÔNG đi tới được' in m for _, m in res['issues']))

    def test_camera_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            gm = cg.GridMap(corridor_map(tmp))
        walls = gm.occ == 100
        obj = {'name': 'p', 'x': 4.0, 'y': 2.0, 'footprint': {'radius': 0.3}}
        m = cg.footprint_mask(gm, obj)
        ok, d, b, _ = cg.camera_view(gm, walls, (1.0, 2.0, 0.0), obj, m)
        self.assertTrue(ok)
        self.assertAlmostEqual(d, 3.0)
        ok, *_ , note = cg.camera_view(gm, walls, (1.0, 2.0, math.pi), obj, m)
        self.assertFalse(ok)
        self.assertEqual(note, 'ngoài FOV')
        behind = {'name': 'q', 'x': 7.0, 'y': 0.6, 'footprint': {'radius': 0.2}}
        ok, *_ , note = cg.camera_view(gm, walls, (3.0, 0.6, 0.0), behind, cg.footprint_mask(gm, behind))
        self.assertFalse(ok)
        self.assertEqual(note, 'bị che')

    def test_box_footprint_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            gm = cg.GridMap(corridor_map(tmp))
        car = {'name': 'c', 'x': 3.0, 'y': 2.0, 'yaw': math.pi / 2, 'footprint': {'box': [-1.0, 1.0, -0.3, 0.3]}}
        m = cg.footprint_mask(gm, car)
        i, j = gm.to_cell(3.0, 2.9)       # dài theo trục y sau khi quay 90°
        self.assertTrue(m[j, i])
        i, j = gm.to_cell(3.9, 2.0)
        self.assertFalse(m[j, i])

    def test_distance_field_fallback_matches_scipy_roughly(self):
        blocked = np.zeros((30, 30), bool)
        blocked[15, 15] = True
        d = cg.distance_field(blocked, 1.0)
        self.assertAlmostEqual(d[15, 25], 10.0, delta=0.6)

    def test_astar(self):
        grid = np.ones((10, 10), bool)
        grid[1:, 5] = False
        path = cg.astar(grid, (1, 5), (8, 5))
        self.assertIsNotNone(path)
        self.assertIn((5, 0), path)
        grid[0, 5] = False
        self.assertIsNone(cg.astar(grid, (1, 5), (8, 5)))


class TestNavigatorLogic(unittest.TestCase):
    def test_initial_pose_decision(self):
        self.assertTrue(wn.decide_initial_pose('auto', True)[0])
        self.assertFalse(wn.decide_initial_pose('auto', False)[0])
        self.assertTrue(wn.decide_initial_pose('auto', None)[0])
        self.assertTrue(wn.decide_initial_pose('ALWAYS', False)[0])
        self.assertFalse(wn.decide_initial_pose('never', True)[0])
        with self.assertRaises(ValueError):
            wn.decide_initial_pose('sometimes', True)

    def test_pose_std_and_length(self):
        cov = [0.0] * 36
        cov[0], cov[7], cov[35] = 0.04, 0.09, 0.01
        sx, sy, syaw = wn.pose_std(cov)
        self.assertAlmostEqual(sx, 0.2)
        self.assertAlmostEqual(sy, 0.3)
        self.assertAlmostEqual(syaw, 0.1)
        self.assertAlmostEqual(wn.path_length([(0, 0), (3, 4), (3, 5)]), 6.0)

    def test_summary_excludes_home(self):
        base = {'duration': 10.0, 'distance': 2.0, 'error_xy': 0.1, 'error_yaw': 0.05, 'attempts': 1}
        res = [dict(base, label='G1', name='a', status='SUCCEEDED'),
               dict(base, label='G2', name='b', status='FAILED', error_xy=None),
               dict(base, label='HOME', name='home', status='SUCCEEDED', extra=True)]
        lines, ok, total = wn.summary_lines(res)
        self.assertEqual((ok, total), (1, 2))
        self.assertIn('1/2', lines[-1])


class TestSpawnObjects(unittest.TestCase):
    def test_parse_uri(self):
        self.assertEqual(so.parse_fuel_uri('https://fuel.gazebosim.org/1.0/OpenRobotics/models/Standing person'),
                         ('fuel.gazebosim.org', 'OpenRobotics', 'Standing person'))
        self.assertEqual(so.parse_fuel_uri('https://fuel.gazebosim.org/1.0/OpenRobotics/models/Fire%20hydrant/2'),
                         ('fuel.gazebosim.org', 'OpenRobotics', 'Fire hydrant'))
        self.assertIsNone(so.parse_fuel_uri('model://foo'))
        self.assertIsNone(so.parse_fuel_uri('https://fuel.gazebosim.org/1.0/OpenRobotics/worlds/X'))

    def test_cache_lookup_case_insensitive_latest(self):
        with tempfile.TemporaryDirectory() as root:
            base = os.path.join(root, 'fuel.ignitionrobotics.org', 'openrobotics', 'models', 'standing person')
            for v in ('1', '3'):
                os.makedirs(os.path.join(base, v))
                open(os.path.join(base, v, 'model.config'), 'w').close()
            os.makedirs(os.path.join(base, '7'))          # thư mục rỗng (tải dở) -> bỏ qua
            got = so.cached_model_dir('https://fuel.gazebosim.org/1.0/OpenRobotics/models/Standing person',
                                      roots=[root])
            self.assertEqual(got, os.path.join(base, '3'))
            self.assertIsNone(so.cached_model_dir(
                'https://fuel.gazebosim.org/1.0/OpenRobotics/models/Chair', roots=[root]))

    def test_create_command(self):
        cmd = so.create_command('maze', {'name': 'p1', 'uri': ' https://x/1.0/o/models/A b ', 'x': 1,
                                         'y': -2.5, 'yaw': 3.14159}, 'ros_gz_sim')
        self.assertEqual(cmd[:4], ['ros2', 'run', 'ros_gz_sim', 'create'])
        self.assertEqual(cmd[cmd.index('-file') + 1], 'https://x/1.0/o/models/A b')
        self.assertEqual(cmd[cmd.index('-world') + 1], 'maze')
        self.assertEqual(cmd[cmd.index('-y') + 1], '-2.500')
        self.assertEqual(cmd[cmd.index('-z') + 1], '0.000')

    def test_repo_objects_file(self):
        world, objs = so.load_objects_file(OBJECTS)
        self.assertEqual(world, 'maze')
        self.assertGreaterEqual(len(objs), 5)
        for o in objs:
            self.assertIsNotNone(so.parse_fuel_uri(o['uri']), o['uri'])
        coco = {o.get('coco') for o in objs}
        self.assertTrue({'person', 'car', 'chair'} <= coco)

    def test_duplicate_names(self):
        with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as f:
            f.write('objects:\n  - {name: a, uri: u, x: 0, y: 0}\n  - {name: a, uri: u, x: 1, y: 0}\n')
        try:
            with self.assertRaises(ValueError):
                so.load_objects_file(f.name)
        finally:
            os.unlink(f.name)


class TestYoloHelpers(unittest.TestCase):
    def test_split_list(self):
        self.assertEqual(yd.split_list(' person, car ,,fire hydrant'), ['person', 'car', 'fire hydrant'])
        self.assertEqual(yd.split_list(''), [])
        self.assertEqual(yd.split_list(['a', ' ', 'b']), ['a', 'b'])

    def test_model_path(self):
        self.assertEqual(yd.resolve_model_path('yolo11n.pt', '/w'), '/w/yolo11n.pt')
        self.assertEqual(yd.resolve_model_path('/abs/m.pt', '/w'), '/abs/m.pt')
        self.assertEqual(yd.resolve_model_path('runs/best.pt', '/w'), 'runs/best.pt')
        self.assertTrue(yd.is_world_model('yolov8s-worldv2.pt'))
        self.assertFalse(yd.is_world_model('yolo11n.pt'))

    def test_colors_stable(self):
        self.assertEqual(yd.class_color('person'), yd.class_color('person'))
        self.assertEqual(len(yd.class_color('car')), 3)

    def test_detection_log(self):
        log = yd.DetectionLog()
        self.assertEqual(log.add('person', 0.5, 1.0, (0, 0, 0)), (True, True))
        self.assertEqual(log.add('person', 0.4, 2.0, None), (False, False))
        self.assertEqual(log.add('person', 0.9, 3.0, None), (False, True))
        s = log.stats['person']
        self.assertEqual((s['frames'], s['max_conf'], s['first_t']), (3, 0.9, 1.0))
        self.assertIn('person', '\n'.join(log.lines()))

    def test_format(self):
        self.assertEqual(yd.format_detections([('car', 0.5, (1, 2, 3, 4))]), 'car 0.50 [1,2,3,4]')

    def test_draw(self):
        try:
            import cv2
        except ImportError:
            self.skipTest('không có OpenCV')
        img = np.zeros((240, 320, 3), np.uint8)
        out = yd.draw(img, [('person', 0.9, (10, 5, 100, 200))], ['hud'], cv2)
        self.assertGreater(int(out.sum()), 0)


class TestRecorderAndLocalization(unittest.TestCase):
    def test_recorder_yaml_roundtrip(self):
        pts = [(1.0, 2.0, 0.5, 'Publish Point'), (-3.25, 4.0, -1.2, 'amcl_pose')]
        with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as f:
            f.write(gr.to_yaml(pts))
        try:
            init, goals = cg.load_goals(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(len(goals), 2)
        self.assertAlmostEqual(goals[1]['x'], -3.25)
        self.assertAlmostEqual(goals[1]['yaw'], -1.2, places=3)
        self.assertAlmostEqual(gr.heading((0, 0), (0, 2)), math.pi / 2)
        self.assertEqual(gr.heading(None, (1, 1)), 0.0)

    def test_scan_endpoints_and_match(self):
        pts = lcheck.scan_endpoints([1.0, float('inf'), 0.01, 2.0, 11.99], 0.0, math.pi / 2, 0.1, 12.0)
        self.assertEqual(len(pts), 2)
        self.assertAlmostEqual(pts[0][0], 1.0)
        self.assertAlmostEqual(pts[1][0], 0.0, places=6)
        self.assertAlmostEqual(pts[1][1], -2.0, places=6)
        field = np.full((10, 10), 1.0)
        field[5, 5] = 0.0
        ratio, med = lcheck.match_ratio(field, 1.0, 0.0, 0.0, [(5.5, 5.5), (2.5, 2.5)], 0.15)
        self.assertAlmostEqual(ratio, 0.5)


class TestConfigFiles(unittest.TestCase):
    def test_yolo_yaml(self):
        with open(os.path.join(ROOT, 'config', 'yolo.yaml')) as f:
            p = yaml.safe_load(f)['yolo_detector']['ros__parameters']
        self.assertEqual(p['image_topic'], '/oakd/rgb/preview/image_raw')
        for key in ('classes', 'world_classes', 'device'):
            self.assertIsInstance(p[key], str, key)       # mảng rỗng không suy ra được kiểu ở Humble

    def test_rviz_has_yolo_and_goals(self):
        with open(os.path.join(ROOT, 'rviz', 'nav.rviz')) as f:
            d = yaml.safe_load(f)
        text = yaml.safe_dump(d)
        self.assertIn('/yolo/image_annotated', text)
        self.assertIn('/nav_goals/markers', text)
        self.assertIn('rviz_default_plugins/PublishPoint', text)

    def test_cmake_installs_scripts(self):
        with open(os.path.join(ROOT, 'CMakeLists.txt')) as f:
            cmake = f.read()
        for s in ('waypoint_navigator.py', 'yolo_detector.py', 'spawn_objects.py', 'goal_recorder.py',
                  'check_goals.py', 'localization_check.py', 'lab_common.py'):
            self.assertIn('scripts/' + s, cmake)
            self.assertTrue(os.path.isfile(os.path.join(ROOT, 'scripts', s)))
        for s in ('waypoint_navigator.py', 'yolo_detector.py', 'spawn_objects.py', 'goal_recorder.py',
                  'check_goals.py', 'localization_check.py'):
            self.assertTrue(os.access(os.path.join(ROOT, 'scripts', s), os.X_OK), s + ' chưa chmod +x')


if __name__ == '__main__':
    unittest.main(verbosity=2)
