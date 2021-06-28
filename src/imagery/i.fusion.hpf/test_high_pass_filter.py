#!/usr/bin/env python

# author: Panagiotis Mavrogiorgos

""" Test High Pass Filtering functions.  """

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


from high_pass_filter import get_row, get_mid_row, get_kernel, get_center_cell


def test_get_row():
    for size in (3, 5, 7, 9):
        row = get_row(size)
        assert len(row) == size
        assert all(item == -1 for item in row)


def test_get_mid_row():
    center = -23
    for size in (3, 5, 7, 9):
        row = get_mid_row(size, center)
        assert len(row) == size
        assert row[size // 2] == center
        assert [item == -1 for item in row if item != center]


def test_get_kernel():
    for size, level in [(5, "Low"), (5, "Mid"), (7, "High")]:
        kernel = get_kernel(size, level)
        # test number of rows/columns
        assert len(kernel) == size
        assert all(len(row) == size for row in kernel)
        # test matrix contents
        mid_row = size // 2
        for i, row in enumerate(kernel):
            if i == mid_row:
                center = get_center_cell(level, size)
                assert row == get_mid_row(size, center)
            else:
                assert row == get_row(size)
