# import os
# import sys
# import pytest
# import numpy as np
# from unittest.mock import patch, MagicMock
# from grass.script import array as garray
# from PIL import Image
# from grass.gunittest.case import TestCase
# from grass.gunittest.main import test


# @pytest.fixture(scope="module")
# def mock_torch():
#     with patch('torch.cuda.is_available') as mock_is_available:
#         mock_is_available.return_value = False
#         yield mock_is_available


# @pytest.fixture(scope="module")
# def mock_run_langsam_segmentation():
#     with patch('i.sam2.run_langsam_segmentation') as mock_run_langsam:
#         # Define the mock return value
#         mock_run_langsam.return_value = [np.random.randint(0, 2, (100, 100), dtype=np.uint8) for _ in range(3)]
#         yield mock_run_langsam


# class TestISam2(TestCase):

#     RED_BAND = "lsat7_2002_30"
#     GREEN_BAND = "lsat7_2002_20"
#     BLUE_BAND = "lsat7_2002_10"

#     def _create_imagery_group(cls):
#         cls.runModule("i.group", group="test_group", input=','.join([cls.RED_BAND, cls.GREEN_BAND, cls.BLUE_BAND]))

#     @classmethod
#     def setUpClass(cls):
#         """Ensures expected computational region"""
#         # to not override mapset's region (which might be used by other tests)
#         cls.use_temp_region()
#         cls.runModule("g.region", raster="elev_lid792_1m", res=30)
#         cls._create_imagery_group(cls)

#     @classmethod
#     def tearDown(self):
#         """
#         Remove the outputs created from the centroids module
#         This is executed after each test run.
#         """
#         self.runModule("g.remove", flags="f", type="raster", name="test_output")

#     @pytest.mark.usefixtures("mock_torch", "mock_run_langsam")
#     def test_main_with_text_prompt(self):
#         options = {
#             "group": "test_group",
#             "output": "test_output",
#             "model_path": None,
#             "text_prompt": "Waterbodies",
#             "text_threshold": "0.24",
#             "box_threshold": "0.24"
#         }

#         self.assertModule("i.sam2", **options)


# if __name__ == "__main__":
#     test()
