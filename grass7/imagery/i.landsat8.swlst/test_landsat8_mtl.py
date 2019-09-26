#!/usr/bin/python\<nl>\
# -*- coding: utf-8 -*-

"""
@author nik |
"""

from landsat8_mtl import Landsat8_MTL


MTLFILE = 'mtl.txt'


def test(mtlfile):
    """
    Test the class.
    """

    print("! No file defined, testing with default MTl file!")
    mtl = Landsat8_MTL(MTLFILE)
    print()

    print("| Test the object's __str__ method:", mtl)
    print("| Test method _get_mtl_lines:\n ", mtl._get_mtl_lines())
    print()

    print("| Basic metadata:")
    print("  > id (original field name is 'LANDSAT_SCENE_ID'):", mtl.scene_id)
    print("  > WRS path:", mtl.wrs_path)
    print("  > WRS row:", mtl.wrs_row)
    print("  > Acquisition date:", mtl.date_acquired)
    print("  > Scene's center time:", mtl.scene_center_time)
    print("  > Upper left corner:", mtl.corner_ul)
    print("  > Lower right corner:", mtl.corner_lr)
    print("  > Upper left (projected):", mtl.corner_ul_projection)
    print("  > Lower right (projected):", mtl.corner_lr_projection)
    print("  > Cloud cover:", mtl.cloud_cover)


def main():
    """
    Main program.
    """
    test(MTLFILE)

if __name__ == "__main__":
    main()
