"""g.rename.many tests"""

import os
import tempfile
from stat import S_IREAD

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class CiteAllCase(TestCase):
    """Test if g.citation works for core modules and addons"""

    @classmethod
    def setUpClass(cls):
        """Setup that is required for all tests"""
        cls.output = tempfile.NamedTemporaryFile(suffix=".txt", mode="w+")

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary file"""
        cls.output.close()

    def truncate_temp_file(self):
        self.output.file.seek(0)
        self.output.file.truncate()

    def test_core_modules(self):
        """Test that citation information is collected for all core modules"""
        module = SimpleModule("g.citation", flags="ad")
        self.assertModule(module)

    def test_core_modules_formats(self):
        """Test that citation information is collected for all core modules
        in different formats"""
        for fmt in ["json", "pretty-json", "chicago-footnote", "dict", "plain"]:
            # format citeproc requires citeproc-py library but requires
            # cleanest input together with cff-format, csl-json
            # which currently do not succeed for all modules
            module = SimpleModule("g.citation", flags="ad", format=fmt)
            self.assertModule(module)

    def test_addons(self):
        """Test that citation information is retrieved from addons"""
        module = SimpleModule("g.citation", module="g.citation")
        self.assertModule(module)

    def test_core_modules_output_file(self):
        """Test that citation information is collected for all core modules
        and are written to the output file
        """
        module = SimpleModule("g.citation", flags="ad", output=self.output.name)
        self.assertModule(module)
        self.assertIn("v_surf_rst", self.output.file.read())

    def test_core_modules_formats_output_file(self):
        """Test that citation information is collected for all core modules
        in different formats and are written to the output file"""
        for fmt in ["json", "pretty-json", "chicago-footnote", "dict", "plain"]:
            # format citeproc requires citeproc-py library but requires
            # cleanest input together with cff-format, csl-json
            # which currently do not succeed for all modules
            self.truncate_temp_file()
            module = SimpleModule(
                "g.citation",
                flags="ad",
                format=fmt,
                output=self.output.name,
            )
            self.assertModule(module)
            self.assertIn("v.surf.rst", self.output.file.read())

    def test_addons_output_file(self):
        """Test that citation information is retrieved from addons and
        are written to the output file"""
        self.truncate_temp_file()
        module = SimpleModule(
            "g.citation",
            module="g.citation",
            output=self.output.name,
        )
        self.assertModule(module)
        self.assertIn("g_citation", self.output.file.read())

    def test_core_modules_output_file_doesnt_exists(self):
        """Test that citation information is collected for all core modules
        and written to the output file whose path does not exist"""
        home_dir = os.path.expanduser("~")
        module = SimpleModule(
            "g.citation",
            flags="ad",
            output=os.path.join(
                home_dir,
                "non_exist_dir",
                "non_exist_output_file.txt",
            ),
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("No such file or directory", module.outputs.stderr)

    def test_core_modules_output_file_doesnt_have_write_permission(self):
        """Test that citation information is collected for all core modules
        and tries to write it to an output file that does not have write
        permission"""
        os.chmod(self.output.name, S_IREAD)
        module = SimpleModule(
            "g.citation",
            flags="ad",
            output=self.output.name,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("Permission denied", module.outputs.stderr)


if __name__ == "__main__":
    test()
