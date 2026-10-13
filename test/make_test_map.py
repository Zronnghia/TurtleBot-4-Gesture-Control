#!/usr/bin/env python3
"""Tạo một bản đồ giả theo đúng định dạng map_saver_cli của Nav2 Humble (dùng cho test).

    python3 test/make_test_map.py <thư_mục> [free_thresh]

Bản đồ 200x150 ô, 0.05 m/ô: tường bao (đen 0), bên trong trống (254), một mảng chưa biết (205).
"""
import os
import sys


def make_map(out_dir, free_thresh=0.15, name='map'):
    os.makedirs(out_dir, exist_ok=True)
    w, h = 200, 150
    px = bytearray([254]) * (w * h)
    for y in range(h):
        for x in range(w):
            if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
                px[y * w + x] = 0
            elif 150 <= x < 190 and 10 <= y < 40:
                px[y * w + x] = 205
    with open(os.path.join(out_dir, name + '.pgm'), 'wb') as f:
        f.write(b'P5\n# CREATOR: test\n%d %d\n255\n' % (w, h))
        f.write(bytes(px))
    with open(os.path.join(out_dir, name + '.yaml'), 'w') as f:
        f.write('image: {}.pgm\nmode: trinary\nresolution: 0.05\norigin: [-5, -3.75, 0]\n'
                'negate: 0\noccupied_thresh: 0.65\nfree_thresh: {}\n'.format(name, free_thresh))
    return os.path.join(out_dir, name + '.yaml')


if __name__ == '__main__':
    print(make_map(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.15))
