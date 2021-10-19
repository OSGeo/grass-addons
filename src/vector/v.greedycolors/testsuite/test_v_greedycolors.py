"""
Name:      vdbselect_test
Purpose:   v.db.select decimation test

Author:    Luca Delucchi
Copyright: (C) 2015 by Luca Delucchi and the GRASS Development Team
Licence:   This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

import os
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule

out_greedyclrs = """greedyclr|count(greedyclr)
1|361
2|293
3|261
4|11
"""


class SelectTest(TestCase):
    """Test case for v.db.select"""

    invect = "boundary_county"
    outvect = "my_boundary_county"
    col = "greedyclr"
    outfile = "greedycolors.csv"

    def testRun(self):
        """Module runs with minimal parameters and give output."""

        sel = SimpleModulesel = SimpleModule(
            "g.copy", vector=(self.invect, self.outvect)
        )
        sel.run()
        sel = SimpleModule("v.greedycolors", map=self.outvect)
        sel.run()
        sel = SimpleModule(
            "db.select",
            sql="select greedyclr,count(greedyclr) from my_boundary_county group by greedyclr",
        )
        sel.run()
        self.assertLooksLike(reference=out_greedyclrs, actual=sel.outputs.stdout)


if __name__ == "__main__":
    test()
