#!/usr/bin/env python3
"""Automated 'teleop' for the test environment: undock, then right-hand wall following.

Publishes /cmd_vel exactly like teleop_twist_keyboard would (Twist, 10 Hz), slow speeds.
Usage: explore.py <duration_sim_seconds>
"""
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from irobot_create_msgs.action import Undock
from irobot_create_msgs.msg import DockStatus
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener


def main():
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 600.0
    rclpy.init()
    n = Node('explorer', parameter_overrides=[Parameter('use_sim_time', Parameter.Type.BOOL, True)])
    st = {'scan': None, 'dock': None}
    n.create_subscription(LaserScan, '/scan', lambda m: st.__setitem__('scan', m), qos_profile_sensor_data)
    n.create_subscription(DockStatus, '/dock_status', lambda m: st.__setitem__('dock', m), qos_profile_sensor_data)
    pub = n.create_publisher(Twist, '/cmd_vel', 10)
    buf = Buffer()
    tl = TransformListener(buf, n)  # noqa
    log = n.get_logger()

    def spin(t):
        e = time.monotonic() + t
        while time.monotonic() < e:
            rclpy.spin_once(n, timeout_sec=0.02)

    while st['scan'] is None or st['dock'] is None:
        spin(0.2)
    lidar_yaw = None
    while lidar_yaw is None:
        try:
            tf = buf.lookup_transform('base_link', st['scan'].header.frame_id, Time())
            q = tf.transform.rotation
            lidar_yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        except TransformException:
            spin(0.2)
    log.info('lidar yaw in base_link = %.3f' % lidar_yaw)

    if st['dock'].is_docked:
        c = ActionClient(n, Undock, '/undock')
        c.wait_for_server()
        f = c.send_goal_async(Undock.Goal())
        rclpy.spin_until_future_complete(n, f)
        r = f.result().get_result_async()
        rclpy.spin_until_future_complete(n, r)
        log.info('undock result is_docked=%s' % r.result().result.is_docked)

    def sector(a0, a1):
        s = st['scan']
        best = 99.0
        for i, r in enumerate(s.ranges):
            if not (math.isfinite(r) and s.range_min < r < s.range_max):
                continue
            a = s.angle_min + i * s.angle_increment + lidar_yaw
            a = math.atan2(math.sin(a), math.cos(a))
            if a0 <= a <= a1:
                best = min(best, r)
        return best

    start = n.get_clock().now().nanoseconds * 1e-9
    target = 0.55
    while rclpy.ok():
        now = n.get_clock().now().nanoseconds * 1e-9
        if now - start > duration:
            break
        front = sector(-0.35, 0.35)
        fright = sector(-1.1, -0.5)
        right = sector(-1.75, -1.35)
        tw = Twist()
        if front < 0.55 or fright < 0.35:
            tw.angular.z = 0.5
        elif right > 1.1:
            tw.linear.x, tw.angular.z = 0.12, -0.45
        else:
            tw.linear.x = 0.15
            tw.angular.z = max(-0.45, min(0.45, 1.5 * (target - right)))
        pub.publish(tw)
        spin(0.1)
    for _ in range(5):
        pub.publish(Twist())
        spin(0.05)
    log.info('exploration done')
    rclpy.shutdown()


if __name__ == '__main__':
    main()
