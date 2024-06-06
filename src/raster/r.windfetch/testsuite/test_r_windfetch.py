import json

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestRWindfetch(TestCase):
    input = "test_input"
    input_points = "test_input_points"
    output = "test_output"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=11, s=0, e=11, w=0, res=1)
        cls.runModule("r.circle", output=cls.input, coordinates=(5.5, 5.5), flags="b",
                      min=5, max=10)
        cls.runModule("r.null", map=cls.input, null=0)
        cls.runModule("v.in.ascii", input="-", output=cls.input_points, stdin="5.5|5.5\n5.5|5.5")

    @classmethod
    def tearDownClass(cls):
        cls.runModule("g.remove", flags="f", type="raster", name=cls.input)
        cls.runModule("g.remove", flags="f", type="vector", name=cls.input_points)
        cls.del_temp_region()

    def test_json_single_minor_direction(self):
        """Test json output with single minor direction"""
        module = SimpleModule("r.windfetch", input=self.input, coordinates=(5.5, 5.5),
                          step=90, direction=0, minor_directions=1, format="json")
        self.assertModule(module)
        stdout_json = json.loads(module.outputs.stdout)
        reference_directions = list(range(0, 360, 90))
        self.assertListEqual(reference_directions, stdout_json[0]["directions"])
        reference_fetch = [5.] * len(reference_directions)
        self.assertListEqual(reference_fetch, stdout_json[0]["fetch"])
        
    def test_json_multiple_minor_directions(self):
        """Test json output with multiple minor directions"""
        module = SimpleModule("r.windfetch", input=self.input, coordinates=(5.5, 5.5),
                          step=90, direction=0, minor_directions=3, minor_step=90, format="json")
        self.assertModule(module)
        stdout_json = json.loads(module.outputs.stdout)
        reference_directions = list(range(0, 360, 90))
        self.assertListEqual(reference_directions, stdout_json[0]["directions"])
        reference_fetch = [5.] * len(reference_directions)
        self.assertListEqual(reference_fetch, stdout_json[0]["fetch"])
        
    def test_csv_single_minor_direction(self):
        """Test csv output with single minor direction"""
        module = SimpleModule("r.windfetch", input=self.input, coordinates=(5.5, 5.5),
                          step=90, direction=0, minor_directions=1, format="csv")
        self.assertModule(module)
        reference = ("x,y,direction_0,direction_90,direction_180,direction_270\n"
                    "5.5,5.5,5.0,5.0,5.0,5.0\n")
        self.assertMultiLineEqual(reference, module.outputs.stdout)

    def test_json_input_points_single_minor_direction(self):
        """Test json output with input points"""
        module = SimpleModule("r.windfetch", input=self.input, points=self.input_points,
                          step=90, direction=0, minor_directions=1, format="json")
        self.assertModule(module)
        stdout_json = json.loads(module.outputs.stdout)
        reference_directions = list(range(0, 360, 90))
        self.assertEqual(2, len(stdout_json))
        self.assertListEqual(reference_directions, stdout_json[0]["directions"])
        self.assertListEqual(reference_directions, stdout_json[1]["directions"])
        reference_fetch = [5.] * len(reference_directions)
        self.assertListEqual(reference_fetch, stdout_json[0]["fetch"])
        self.assertListEqual(reference_fetch, stdout_json[1]["fetch"])
        
        
    def test_json_test_complex(self):
        """Test case with more complex input, results can't be easily verified"""
        module = SimpleModule("r.windfetch", input=self.input, coordinates=(3, 9),
                           step=15, direction=0, minor_directions=5, minor_step=3, format="json")
        self.assertModule(module)
        stdout_json = json.loads(module.outputs.stdout)
        reference_directions = list(range(0, 360, 15))
        self.assertListEqual(reference_directions, stdout_json[0]["directions"])
        reference_fetch = [
            5.4331052,
            3.536746,
            2.0716972,
            1.414214,
            1.3313712,
            1.0,
            1.0,
            1.0,
            1.0828428,
            1.414214,
            1.3313712,
            1.0,
            1.0,
            1.0,
            1.2472136,
            3.0386972,
            5.0147186,
            6.8758972,
            8.4373548,
            9.2073382,
            9.782832,
            9.5116254,
            8.4017286,
            7.1749058
        ]
        for each in reference_fetch:
            self.assertAlmostEqual(each, stdout_json[0]["fetch"].pop(0), places=6)


if __name__ == "__main__":
    test()