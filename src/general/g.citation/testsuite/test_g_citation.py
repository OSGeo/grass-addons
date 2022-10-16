"""g.rename.many tests"""

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class CiteAllCase(TestCase):
    """Test if g.citation works for core modules and addons"""

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


if __name__ == "__main__":
    test()
