#!/usr/bin/env python3

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestValidation(TestCase):
    """Test case built on van Vliet 2011 paper"""

    actual = "test_actual"
    original = "test_original"
    S1 = "test_S1"
    S2 = "test_S2"
    S3 = "test_S3"
    S4 = "test_S4"

    @classmethod
    def setUpClass(cls):
        cls.runModule(
            "r.unpack", input="data/actual.pack", flags="o", output=cls.actual
        )
        cls.runModule(
            "r.unpack", input="data/original.pack", flags="o", output=cls.original
        )
        cls.runModule("r.unpack", input="data/S1.pack", flags="o", output=cls.S1)
        cls.runModule("r.unpack", input="data/S2.pack", flags="o", output=cls.S2)
        cls.runModule("r.unpack", input="data/S3.pack", flags="o", output=cls.S3)
        cls.runModule("r.unpack", input="data/S4.pack", flags="o", output=cls.S4)
        cls.runModule("g.region", raster=cls.original)

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[cls.actual, cls.original, cls.S1, cls.S2, cls.S3, cls.S4],
        )

    def test_validation_run(self):
        """Test if results is in expected limits"""
        module = SimpleModule(
            "r.futures.validation",
            format_="shell",
            original=self.original,
            simulated=self.S1,
            reference=self.actual,
        )
        # test that module fails (ends with non-zero return code)
        self.assertModule(module)
        self.assertModuleKeyValue(
            module,
            reference=dict(kappasimulation=0, kappa=0.79),
            precision=0.01,
            sep="=",
        )
        module.inputs["simulated"].value = self.S2
        self.assertModuleKeyValue(
            module,
            reference=dict(kappasimulation=-0.06, kappa=0.64),
            precision=0.01,
            sep="=",
        )
        module.inputs["simulated"].value = self.S3
        self.assertModuleKeyValue(
            module,
            reference=dict(kappasimulation=0.15, kappa=0.71),
            precision=0.01,
            sep="=",
        )
        module.inputs["simulated"].value = self.S4
        self.assertModuleKeyValue(
            module,
            reference=dict(kappasimulation=0.6, kappa=0.89),
            precision=0.01,
            sep="=",
        )


if __name__ == "__main__":
    test()
