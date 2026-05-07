"""Tests for r.out.3mf using grass.gunittest."""

import os
import re
import tempfile
import zipfile

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


def _max_vertex_z(model_xml):
    """Get maximum Z value from serialized 3MF model XML."""
    z_values = [float(value) for value in re.findall(r' z="([^"]+)"', model_xml)]
    return max(z_values)


class TestROut3mf(TestCase):
    """Basic integration tests for 3MF export."""

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="elevation")

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()

    def test_export_creates_valid_3mf_package(self):
        """The module should produce a readable 3MF ZIP with mesh content."""
        with tempfile.NamedTemporaryFile(suffix=".3mf", delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            module = SimpleModule(
                "r.out.3mf",
                input="elevation",
                output=output_path,
                size=80,
                resolution=4,
                zscale=2,
                base_height=2,
                overwrite=True,
            )
            self.assertModule(module)
            self.assertTrue(os.path.exists(output_path))

            with zipfile.ZipFile(output_path) as zip_file:
                members = zip_file.namelist()
                self.assertIn("[Content_Types].xml", members)
                self.assertIn("_rels/.rels", members)
                self.assertIn("3D/3dmodel.model", members)

                model_xml = zip_file.read("3D/3dmodel.model").decode("utf-8")
                self.assertIn("<vertices>", model_xml)
                self.assertIn("<triangles>", model_xml)
                self.assertGreater(model_xml.count("<vertex "), 0)
                self.assertGreater(model_xml.count("<triangle "), 0)
        finally:
            gs.try_remove(output_path)

    def test_normalize_flag_changes_z_scale(self):
        """The -n flag should produce a different vertical scale than default."""
        with tempfile.NamedTemporaryFile(suffix=".3mf", delete=False) as plain_file:
            plain_path = plain_file.name
        with tempfile.NamedTemporaryFile(suffix=".3mf", delete=False) as norm_file:
            norm_path = norm_file.name

        try:
            plain = SimpleModule(
                "r.out.3mf",
                input="elevation",
                output=plain_path,
                size=60,
                resolution=6,
                zscale=10,
                base_height=2,
                overwrite=True,
            )
            normalized = SimpleModule(
                "r.out.3mf",
                input="elevation",
                output=norm_path,
                size=60,
                resolution=6,
                zscale=10,
                base_height=2,
                flags="n",
                overwrite=True,
            )

            self.assertModule(plain)
            self.assertModule(normalized)

            with zipfile.ZipFile(plain_path) as plain_zip:
                plain_xml = plain_zip.read("3D/3dmodel.model").decode("utf-8")
            with zipfile.ZipFile(norm_path) as norm_zip:
                norm_xml = norm_zip.read("3D/3dmodel.model").decode("utf-8")

            plain_max_z = _max_vertex_z(plain_xml)
            norm_max_z = _max_vertex_z(norm_xml)

            # The two modes use different vertical-scale formulas (geographic-true
            # vs. zscale-as-mm-of-relief), so the resulting heights should differ.
            self.assertGreater(abs(plain_max_z - norm_max_z), 1.0)
        finally:
            gs.try_remove(plain_path)
            gs.try_remove(norm_path)


if __name__ == "__main__":
    test()
