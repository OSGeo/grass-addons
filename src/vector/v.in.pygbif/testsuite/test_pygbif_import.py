"""Test v.in.pygbif

(C) 2020 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Stefan Blumentrath
"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule


class TestPyGBIFImport(TestCase):
    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region"""
        cls.use_temp_region()
        cls.runModule("g.region", raster="elev_state_500m")

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region"""
        cls.runModule("g.remove", flags="rf", type="vector", name="gbif_poa3")
        cls.del_temp_region()

    def test_poa_taxon_match(self):

        v_in_pygbif_match = SimpleModule(
            "v.in.pygbif", taxa="Poa", output="gbif_poa1", flags="g", verbose=True
        )
        self.assertModule(v_in_pygbif_match)
        stdout_match = v_in_pygbif_match.outputs.stdout

        self.assertTrue(stdout_match.startswith("match=Poa"))

    def test_poa_taxon_count(self):

        v_in_pygbif_count = SimpleModule(
            "v.in.pygbif", taxa="Poa", output="gbif_poa2", overwrite=True, verbose=True
        )
        self.assertModule(v_in_pygbif_count)
        stdout_count = v_in_pygbif_count.outputs.stdout

        self.assertTrue(int(stdout_count.split(" ")[1]) >= 250)

    def test_poa_map(self):

        v_in_pygbif_map = SimpleModule(
            "v.in.pygbif", taxa="Poa", output="gbif_poa3", verbose=True
        )
        self.assertModule(v_in_pygbif_map)


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
