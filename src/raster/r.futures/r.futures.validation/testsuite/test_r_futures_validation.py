#!/usr/bin/env python3

import json

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
        # Multiclass data: change detection metrics should be skipped
        module_json = SimpleModule(
            "r.futures.validation",
            format_="json",
            original=self.original,
            simulated=self.S1,
            reference=self.actual,
        )
        self.assertModule(module_json)
        result = json.loads(module_json.outputs.stdout)
        for key in [
            "hits",
            "misses",
            "false_alarms",
            "null_successes",
            "figure_of_merit",
            "producer",
            "user",
            "initially_developed",
        ]:
            self.assertIsNone(result[key], msg=f"{key} should be None for multiclass")

    def test_validation2_run(self):
        """Test change detection metrics for S5"""
        module = SimpleModule(
            "r.futures.validation",
            format_="shell",
            original=self.original2,
            simulated=self.S5,
            reference=self.actual2,
        )
        self.assertModuleKeyValue(
            module,
            reference=dict(hits=0.04, figure_of_merit=0.1818),
            precision=0.0001,
            sep="=",
        )

    def test_json_with_original(self):
        """Test JSON output contains all keys and correct values with original"""
        module = SimpleModule(
            "r.futures.validation",
            format_="json",
            original=self.original2,
            simulated=self.S5,
            reference=self.actual2,
        )
        self.assertModule(module)
        result = json.loads(module.outputs.stdout)
        expected_keys = [
            "total_quantity",
            "total_allocation",
            "kappa",
            "kappasimulation",
            "misses",
            "hits",
            "false_alarms",
            "null_successes",
            "figure_of_merit",
            "producer",
            "user",
            "initially_developed",
        ]
        for key in expected_keys:
            self.assertIn(key, result, msg=f"Missing JSON key: {key}")
        self.assertAlmostEqual(result["hits"], 0.04, places=4)
        self.assertAlmostEqual(result["figure_of_merit"], 0.1818, places=4)

    def test_json_without_original(self):
        """Test JSON output without original exports None for simulation metrics"""
        module = SimpleModule(
            "r.futures.validation",
            format_="json",
            simulated=self.S1,
            reference=self.actual,
        )
        self.assertModule(module)
        result = json.loads(module.outputs.stdout)
        self.assertIsNone(result["kappasimulation"])
        self.assertIsNone(result["hits"])
        self.assertIsNone(result["misses"])
        self.assertIsNotNone(result["kappa"])
        self.assertAlmostEqual(result["kappa"], 0.7847, places=2)

    def test_json_change_detection_consistency(self):
        """Test change detection proportions sum to 1 and derived metrics are consistent"""
        module = SimpleModule(
            "r.futures.validation",
            format_="json",
            original=self.original2,
            simulated=self.S5,
            reference=self.actual2,
        )
        self.assertModule(module)
        result = json.loads(module.outputs.stdout)
        # Change detection proportions should sum to 1
        proportions = sum(
            result[k]
            for k in [
                "hits",
                "misses",
                "false_alarms",
                "null_successes",
                "initially_developed",
            ]
        )
        self.assertAlmostEqual(proportions, 1.0, places=4)
        # Verify derived metrics are consistent with components
        hits = result["hits"]
        misses = result["misses"]
        false_alarms = result["false_alarms"]
        if hits + misses > 0:
            self.assertAlmostEqual(result["producer"], hits / (misses + hits), places=4)
        if hits + false_alarms > 0:
            self.assertAlmostEqual(
                result["user"], hits / (hits + false_alarms), places=4
            )
        if misses + hits + false_alarms > 0:
            self.assertAlmostEqual(
                result["figure_of_merit"],
                hits / (misses + hits + false_alarms),
                places=4,
            )

    def test_json_perfect_simulation(self):
        """Test metrics when simulated equals reference"""
        module = SimpleModule(
            "r.futures.validation",
            format_="json",
            simulated=self.actual,
            reference=self.actual,
        )
        self.assertModule(module)
        result = json.loads(module.outputs.stdout)
        self.assertAlmostEqual(result["kappa"], 1.0, places=4)
        self.assertAlmostEqual(result["total_quantity"], 0.0, places=4)
        self.assertAlmostEqual(result["total_allocation"], 0.0, places=4)

    def test_json_quantity_allocation_nonnegative(self):
        """Test quantity and allocation disagreement are non-negative for all scenarios"""
        for simulated in [self.S1, self.S2, self.S3, self.S4]:
            module = SimpleModule(
                "r.futures.validation",
                format_="json",
                original=self.original,
                simulated=simulated,
                reference=self.actual,
            )
            self.assertModule(module)
            result = json.loads(module.outputs.stdout)
            self.assertGreaterEqual(result["total_quantity"], 0)
            self.assertGreaterEqual(result["total_allocation"], 0)


class TestValidationEdgeCases(TestCase):
    """Test edge cases that trigger division-by-zero and empty data paths"""

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", rows=10, cols=10, n=10, s=0, e=10, w=0)
        # Single category rasters (all cells = 1)
        cls.runModule("r.mapcalc", expression="edge_single_cat = 1")
        # All null rasters
        cls.runModule("r.mapcalc", expression="edge_all_null = null()")
        # All developed original (all 1s), reference and simulated with both 0 and 1
        cls.runModule("r.mapcalc", expression="edge_orig_all_dev = 1")
        cls.runModule("r.mapcalc", expression="edge_ref_mixed = if(row() <= 5, 0, 1)")
        cls.runModule("r.mapcalc", expression="edge_sim_mixed = if(col() <= 5, 0, 1)")

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[
                "edge_single_cat",
                "edge_all_null",
                "edge_orig_all_dev",
                "edge_ref_mixed",
                "edge_sim_mixed",
            ],
        )
        cls.del_temp_region()

    def test_single_category_kappa_none(self):
        """Kappa is None when all cells are the same category (division by zero)"""
        module = SimpleModule(
            "r.futures.validation",
            format_="json",
            simulated="edge_single_cat",
            reference="edge_single_cat",
            original="edge_single_cat",
        )
        self.assertModule(module)
        result = json.loads(module.outputs.stdout)
        self.assertIsNone(result["kappa"])
        self.assertIsNone(result["kappasimulation"])
        self.assertAlmostEqual(result["total_quantity"], 0, places=4)
        self.assertAlmostEqual(result["total_allocation"], 0, places=4)

    def test_all_null_returns_none(self):
        """All metrics are None when rasters contain only null values"""
        module = SimpleModule(
            "r.futures.validation",
            format_="json",
            simulated="edge_all_null",
            reference="edge_all_null",
        )
        self.assertModule(module)
        result = json.loads(module.outputs.stdout)
        self.assertIsNone(result["kappa"])
        self.assertIsNone(result["total_quantity"])
        self.assertIsNone(result["total_allocation"])

    def test_all_initially_developed(self):
        """Change metrics are zero when original has no undeveloped cells"""
        module = SimpleModule(
            "r.futures.validation",
            format_="json",
            original="edge_orig_all_dev",
            simulated="edge_sim_mixed",
            reference="edge_ref_mixed",
        )
        self.assertModule(module)
        result = json.loads(module.outputs.stdout)
        self.assertEqual(result["figure_of_merit"], 0)
        self.assertEqual(result["producer"], 0)
        self.assertEqual(result["user"], 0)
        self.assertAlmostEqual(result["hits"], 0, places=4)
        self.assertAlmostEqual(result["misses"], 0, places=4)
        self.assertAlmostEqual(result["false_alarms"], 0, places=4)
        self.assertAlmostEqual(result["null_successes"], 0, places=4)
        self.assertAlmostEqual(result["initially_developed"], 1.0, places=4)


if __name__ == "__main__":
    test()
