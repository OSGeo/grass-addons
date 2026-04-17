#!/usr/bin/env python3

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestValidation(TestCase):
    """Test case built on van Vliet 2011 paper"""

    actual = "test_actual"
    original = "test_original"
    actual2 = "test_actual2"
    original2 = "test_original2"
    S1 = "test_S1"
    S2 = "test_S2"
    S3 = "test_S3"
    S4 = "test_S4"
    S5 = "test_S5"
    region = "test_region"
    output = "test_output"

    @classmethod
    def setUpClass(cls):
        cls.runModule(
            "r.unpack", input="data/actual.pack", flags="o", output=cls.actual
        )
        cls.runModule(
            "r.unpack", input="data/original.pack", flags="o", output=cls.original
        )
        cls.runModule(
            "r.unpack", input="data/actual2.pack", flags="o", output=cls.actual2
        )
        cls.runModule(
            "r.unpack", input="data/original2.pack", flags="o", output=cls.original2
        )
        cls.runModule("r.unpack", input="data/S1.pack", flags="o", output=cls.S1)
        cls.runModule("r.unpack", input="data/S2.pack", flags="o", output=cls.S2)
        cls.runModule("r.unpack", input="data/S3.pack", flags="o", output=cls.S3)
        cls.runModule("r.unpack", input="data/S4.pack", flags="o", output=cls.S4)
        cls.runModule("r.unpack", input="data/S5.pack", flags="o", output=cls.S5)
        cls.runModule("g.region", raster=cls.original)
        cls.runModule(
            "g.region", raster=cls.original, res=10, flags="au", save=cls.region
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[
                cls.actual,
                cls.original,
                cls.actual2,
                cls.original2,
                cls.S1,
                cls.S2,
                cls.S3,
                cls.S4,
                cls.S5,
            ],
        )
        cls.runModule(
            "g.remove",
            flags="f",
            type="vector",
            name=[cls.output],
        )
        cls.runModule(
            "g.remove",
            flags="f",
            type="region",
            name=[cls.region],
        )

    def test_validation_run(self):
        """Test if results is in expected limits"""
        module = SimpleModule(
            "r.futures.gridvalidation",
            original=self.original,
            simulated=self.S1,
            reference=self.actual,
            output=self.output,
            region=self.region,
            overwrite=True,
        )
        # test that module fails (ends with non-zero return code)
        self.assertModule(module)
        self.assertVectorFitsUnivar(
            map=self.output, column="kappasimulation", reference="min=0", precision=0.01
        )
        module.inputs["simulated"].value = self.S2
        self.assertModule(module)
        self.assertVectorFitsUnivar(
            map=self.output,
            column="kappasimulation",
            reference="min=-0.06",
            precision=0.01,
        )
        module.inputs["simulated"].value = self.S3
        self.assertModule(module)
        self.assertVectorFitsUnivar(
            map=self.output,
            column="kappasimulation",
            reference="min=0.15",
            precision=0.01,
        )
        module.inputs["simulated"].value = self.S4
        self.assertModule(module)
        self.assertVectorFitsUnivar(
            map=self.output,
            column="kappasimulation",
            reference="min=0.6",
            precision=0.01,
        )

    def test_validation2_run(self):
        """Test if results is in expected limits"""
        module = SimpleModule(
            "r.futures.gridvalidation",
            original=self.original2,
            simulated=self.S5,
            reference=self.actual2,
            output=self.output,
            region=self.region,
            overwrite=True,
        )
        # test that module fails (ends with non-zero return code)
        self.assertModule(module)
        self.assertVectorFitsUnivar(
            map=self.output,
            column="figure_of_merit",
            reference="min=0.1818",
            precision=0.0001,
        )


if __name__ == "__main__":
    test()
