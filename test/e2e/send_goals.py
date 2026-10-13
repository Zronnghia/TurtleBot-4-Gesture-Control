#!/usr/bin/env python3
"""Pick 3 well-separated reachable free goals from map.yaml and send them to Nav2, one by one.

Usage: send_goals.py <map.yaml> [n_goals] [timeout_wall_s]
Emulates a user clicking 'Nav2 Goal' in RViz (same NavigateToPose action, default BT).
"""
import math
import os
import sys
import time
from collections import deque

import rclpy
import yaml
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.time import Time
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def load_map(path):
    meta = yaml.safe_load(open(path))
    img = meta['image'] if os.path.isabs(meta['image']) else os.path.join(os.path.dirname(path), meta['image'])
    data = open(img, 'rb').read()
    toks, pos = [], 0
    while len(toks) < 4:
        while data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b'#':
            while data[pos:pos + 1] not in (b'\n', b''):
                pos += 1
            continue
        s = pos
        while not data[pos:pos + 1].isspace():
            pos += 1
        toks.append(data[s:pos])
    w, h = int(toks[1]), int(toks[2])
    px = data[pos + 1:pos + 1 + w * h]
    free = [[px[(h - 1 - y) * w + x] >= 250 for x in range(w)] for y in range(h)]   # y up
    occ = [[px[(h - 1 - y) * w + x] < 50 for x in range(w)] for y in range(h)]
    return meta, w, h, free, occ


def main():
    path = sys.argv[1]
    n_goals = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    tmo = float(sys.argv[3]) if len(sys.argv) > 3 else 900.0
    meta, w, h, free, occ = load_map(path)
    res = float(meta['resolution'])
    ox, oy = meta['origin'][0], meta['origin'][1]
    # clearance (cells) from obstacles/unknown via BFS
    INF = 10 ** 9
    dist = [[INF] * w for _ in range(h)]
    q = deque()
    for y in range(h):
        for x in range(w):
            if not free[y][x]:
                dist[y][x] = 0
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = x + dx, y + dy
            if 0 <= a < w and 0 <= b < h and dist[b][a] > dist[y][x] + 1:
                dist[b][a] = dist[y][x] + 1
                q.append((a, b))
    need = int(math.ceil(0.8 / res))

    rclpy.init()
    node = Node('goal_sender', parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)])
    log = node.get_logger()
    buf = Buffer()
    tl = TransformListener(buf, node)  # noqa
    pose = None
    while pose is None:
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            t = buf.lookup_transform('map', 'base_link', Time())
            pose = (t.transform.translation.x, t.transform.translation.y)
        except TransformException:
            pass
    # Drop the TF listener now (Python TF parsing is CPU heavy on a 2-core box).
    node.destroy_subscription(tl.tf_sub)
    node.destroy_subscription(tl.tf_static_sub)
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
    amcl = {'p': None}
    node.create_subscription(PoseWithCovarianceStamped, 'amcl_pose',
                             lambda m: amcl.__setitem__('p', m.pose.pose.position),
                             QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                                        reliability=ReliabilityPolicy.RELIABLE))
    sx, sy = int((pose[0] - ox) / res), int((pose[1] - oy) / res)
    # reachable region (clearance >= 0.3 m) from robot cell
    reach = set()
    passable = int(math.ceil(0.3 / res))
    best = min(((abs(x - sx) + abs(y - sy), x, y) for y in range(h) for x in range(w)
                if dist[y][x] >= passable), default=None)
    q = deque([(best[1], best[2])])
    reach.add((best[1], best[2]))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = x + dx, y + dy
            if 0 <= a < w and 0 <= b < h and (a, b) not in reach and dist[b][a] >= passable:
                reach.add((a, b))
                q.append((a, b))
    cands = [c for c in reach if dist[c[1]][c[0]] >= need]
    log.info('robot at (%.2f, %.2f); reachable cells %d, candidate goal cells %d' % (
        pose[0], pose[1], len(reach), len(cands)))
    goals, pts = [], [(sx, sy)]
    maxd = (7.0 / res) ** 2
    for _ in range(n_goals):
        last = pts[-1]
        near = [c for c in cands if (c[0] - last[0]) ** 2 + (c[1] - last[1]) ** 2 <= maxd] or cands
        c = max(near, key=lambda c: min((c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 for p in pts))
        pts.append(c)
        goals.append((ox + (c[0] + 0.5) * res, oy + (c[1] + 0.5) * res))

    client = ActionClient(node, NavigateToPose, 'navigate_to_pose')
    client.wait_for_server()
    ok = 0
    for i, (gx, gy) in enumerate(goals):
        g = NavigateToPose.Goal()
        g.pose = PoseStamped()
        g.pose.header.frame_id = 'map'
        g.pose.header.stamp = node.get_clock().now().to_msg()
        g.pose.pose.position.x, g.pose.pose.position.y = gx, gy
        g.pose.pose.orientation.w = 1.0
        log.info('GOAL %d -> (%.2f, %.2f)' % (i + 1, gx, gy))
        f = client.send_goal_async(g)
        rclpy.spin_until_future_complete(node, f)
        gh = f.result()
        if not gh.accepted:
            log.error('goal rejected')
            continue
        rf = gh.get_result_async()
        t0 = time.monotonic()
        while not rf.done() and time.monotonic() - t0 < tmo:
            rclpy.spin_once(node, timeout_sec=0.1)
        if not rf.done():
            log.error('goal timeout -> cancel')
            gh.cancel_goal_async()
            continue
        st = rf.result().status
        p = amcl['p']
        err = math.hypot(p.x - gx, p.y - gy) if p is not None else float('nan')
        log.info('GOAL %d status=%d (4=SUCCEEDED) final error %.2f m, wall %.0f s' % (
            i + 1, st, err, time.monotonic() - t0))
        ok += st == 4
    log.info('SUMMARY %d/%d goals succeeded' % (ok, len(goals)))
    rclpy.shutdown()
    return 0 if ok == len(goals) else 1


if __name__ == '__main__':
    sys.exit(main())
