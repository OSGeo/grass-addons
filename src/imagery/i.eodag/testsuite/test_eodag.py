############################################################################
#
# MODULE:      i.eodag
#
# AUTHOR(S):   Hamed Elgizery <hamedashraf2004 gmail.com>
# MENTOR(S):   Luca Delucchi, Veronica Andreo, Stefan Blumentrath
#
# PURPOSE:     Tests i.eodag input parsing / searching results.
#              Uses NC Full data set.
#
# COPYRIGHT:   (C) 2024-2025 by Hamed Elgizery, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

from grass.gunittest.case import TestCase
from grass.gunittest.gutils import get_current_mapset, is_map_in_mapset
from grass.exceptions import CalledModuleError
from grass.pygrass.modules import Module
from subprocess import PIPE


class TestEodag(TestCase):
    """When testing searching, we are using peps when testing because it gives
    consistent results, unlike cop_dataspace & creodias.
    """

    @classmethod
    def setUpClass(cls):
        """Use temporary region settings"""
        cls.use_temp_region()
        cls.runModule(
            "v.extract",
            input="urbanarea",
            where="NAME = 'Durham'",
            output="durham",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Delete temporary region settings"""
        cls.del_temp_region()

    def test_search_without_date(self):
        """Test"""
        self.assertModule(
            "i.eodag", flags="l", producttype="S2_MSI_L2A", clouds=30, quiet=True
        )

    def test_search_S2_MSI_L2A_default(self):
        """Test"""
        output = r"""S2A_MSIL2A_20240113T160621_N0510_R097_T17SPV_20240113T202049 2024-01-13T16:06:21  4% S2MSI2A
S2A_MSIL2A_20240113T160621_N0510_R097_T17SPA_20240113T202049 2024-01-13T16:06:21  7% S2MSI2A
S2B_MSIL2A_20240108T160639_N0510_R097_T17SPA_20240108T203022 2024-01-08T16:06:39 12% S2MSI2A
S2B_MSIL2A_20240118T160609_N0510_R097_T17SPV_20240118T203136 2024-01-18T16:06:09 22% S2MSI2A"""
        # provider used shall be creodias by default
        i_eodag = Module(
            "i.eodag",
            flags="l",
            producttype="S2_MSI_L2A",
            clouds=30,
            map="durham",
            start="2024-01-01",
            end="2024-02-01",
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_pattern_option(self):
        """Test"""
        i_eodag = Module(
            "i.eodag",
            flags="l",
            provider="planetary_computer",
            map="durham",
            producttype="LANDSAT_C2L2",
            pattern="LC09.*T1",
            clouds=30,
            quiet=True,
            stdout_=PIPE,
        )
        import re

        pattern = re.compile("LC09.*T1")
        lines = i_eodag.outputs["stdout"].value.strip().split("\n")
        for line in lines:
            scene_id = line.split(" ")[0]
            self.assertTrue(pattern.fullmatch(scene_id))

    def test_query_option(self):
        """Test"""
        output = r"""S2B_MSIL1C_20240207T160429_N0510_R097_T17SPA_20240207T193750 2024-02-07T16:04:29  0% S2MSI1C
S2B_MSIL1C_20240207T160429_N0510_R097_T17SPV_20240207T193750 2024-02-07T16:04:29  0% S2MSI1C
S2A_MSIL1C_20240222T160251_N0510_R097_T17SPV_20240222T193942 2024-02-22T16:02:51  0% S2MSI1C
S2B_MSIL1C_20240407T155819_N0510_R097_T17SPA_20240407T193929 2024-04-07T15:58:19  0% S2MSI1C
S2B_MSIL1C_20240407T155819_N0510_R097_T17SPV_20240407T193929 2024-04-07T15:58:19  0% S2MSI1C
S2A_MSIL1C_20240422T155821_N0510_R097_T17SPA_20240422T214102 2024-04-22T15:58:21  0% S2MSI1C
S2A_MSIL1C_20240422T155821_N0510_R097_T17SPA_20240423T121422 2024-04-22T15:58:21  0% S2MSI1C
S2A_MSIL1C_20240502T155901_N0510_R097_T17SPA_20240502T212005 2024-05-02T15:59:01  0% S2MSI1C
S2A_MSIL1C_20240502T155901_N0510_R097_T17SPV_20240502T212005 2024-05-02T15:59:01  1% S2MSI1C
S2A_MSIL1C_20240522T155901_N0510_R097_T17SPV_20240522T212715 2024-05-22T15:59:01  1% S2MSI1C"""
        # provider used shall be creodias by default
        i_eodag = Module(
            "i.eodag",
            flags="l",
            provider="peps",
            producttype="S2_MSI_L1C",
            map="durham",
            start="2024-01-01",
            end="2024-06-01",
            query="relativeOrbitNumber=97",
            limit=10,
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_query_and_pattern(self):
        """Test"""
        output = r"""S2B_MSIL1C_20240527T155819_N0510_R097_T17SPV_20240527T205026 2024-05-27T15:58:19 100% S2MSI1C
S2B_MSIL1C_20240517T155819_N0510_R097_T17SPV_20240517T193612 2024-05-17T15:58:19 100% S2MSI1C
S2B_MSIL1C_20240517T155819_N0510_R097_T17SPA_20240517T193612 2024-05-17T15:58:19 100% S2MSI1C
S2B_MSIL1C_20240417T155819_N0510_R097_T17SPV_20240417T212826 2024-04-17T15:58:19 100% S2MSI1C
S2B_MSIL1C_20240417T155819_N0510_R097_T17SPA_20240417T212826 2024-04-17T15:58:19 100% S2MSI1C
S2B_MSIL1C_20240328T155819_N0510_R097_T17SPV_20240328T205036 2024-03-28T15:58:19 100% S2MSI1C
S2B_MSIL1C_20240328T155819_N0510_R097_T17SPA_20240328T205036 2024-03-28T15:58:19 100% S2MSI1C
S2B_MSIL1C_20240318T155859_N0510_R097_T17SPV_20240318T205233 2024-03-18T15:58:59 100% S2MSI1C
S2B_MSIL1C_20240308T155959_N0510_R097_T17SPA_20240308T205655 2024-03-08T15:59:59 100% S2MSI1C
S2B_MSIL1C_20240227T160129_N0510_R097_T17SPV_20240227T193844 2024-02-27T16:01:29 100% S2MSI1C
S2B_MSIL1C_20240227T160129_N0510_R097_T17SPA_20240227T193844 2024-02-27T16:01:29 100% S2MSI1C
S2B_MSIL1C_20240217T160239_N0510_R097_T17SPV_20240217T193811 2024-02-17T16:02:39 100% S2MSI1C
S2B_MSIL1C_20240527T155819_N0510_R097_T17SPA_20240527T205026 2024-05-27T15:58:19 99% S2MSI1C
S2B_MSIL1C_20240128T160529_N0510_R097_T17SPA_20240128T194012 2024-01-28T16:05:29 98% S2MSI1C
S2B_MSIL1C_20240118T160609_N0510_R097_T17SPA_20240118T193643 2024-01-18T16:06:09 95% S2MSI1C
S2B_MSIL1C_20240108T160639_N0510_R097_T17SPV_20240108T193844 2024-01-08T16:06:39 90% S2MSI1C
S2B_MSIL1C_20240217T160239_N0510_R097_T17SPA_20240217T193811 2024-02-17T16:02:39 76% S2MSI1C
S2B_MSIL1C_20240318T155859_N0510_R097_T17SPA_20240318T205233 2024-03-18T15:58:59 73% S2MSI1C
S2B_MSIL1C_20240308T155959_N0510_R097_T17SPV_20240308T205655 2024-03-08T15:59:59 69% S2MSI1C
S2B_MSIL1C_20240427T155819_N0510_R097_T17SPA_20240427T193820 2024-04-27T15:58:19 35% S2MSI1C"""
        i_eodag = Module(
            "i.eodag",
            flags="l",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2024-01-01",
            end="2024-06-01",
            order="desc",
            pattern="S2B.*",
            query="relativeOrbitNumber=97,sensorMode=INS-NOBS",
            map="durham",
            limit=20,
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_query_multiple_value(self):
        """Test"""
        output = r"""S2B_MSIL1C_20240308T155959_N0510_R097_T17SPV_20240308T205655 2024-03-08T15:59:59 69% S2MSI1C
S2B_MSIL1C_20240427T155819_N0510_R097_T17SPA_20240427T193820 2024-04-27T15:58:19 35% S2MSI1C
S2B_MSIL1C_20240128T160529_N0510_R097_T17SPV_20240128T194012 2024-01-28T16:05:29 35% S2MSI1C"""
        i_eodag = Module(
            "i.eodag",
            flags="l",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2024-01-01",
            end="2024-06-01",
            sort="cloudcover",
            order="desc",
            pattern="S2B.*",
            query="relativeOrbitNumber=97|54,sensorMode=INS-NOBS,cloudCover=30;gt,cloudCover=70;lt",
            map="durham",
            limit=10,
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_text_file_with_ids(self):
        """Test"""
        output = r"""S2B_MSIL2A_20240529T081609_N0510_R121_T37SED_20240529T105453 2024-05-29T08:16:09  1% S2MSI2A
S2B_MSIL2A_20240529T081609_N0510_R121_T37TDE_20240529T124818 2024-05-29T08:16:09  6% S2MSI2A"""
        i_eodag = Module(
            "i.eodag",
            flags="l",
            file="data/ids_list.txt",
            provider="cop_dataspace",
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_end_comes_first_fail(self):
        """Test"""
        self.assertModuleFail(
            "i.eodag", start="2020-01-04", end="2020-01-01", quiet=True
        )

    def test_minimum_overlap(self):
        """Test"""
        # i.eodag -l provider=creodias producttype=S2_MSI_L2A start=2022-05-01 end=2022-06-01 clouds=50 map=durham minimum_overlap=70
        output = r"""S2B_MSIL1C_20220108T160639_N0301_R097_T17SPV_20220108T194213 2022-01-08T16:06:39  0% S2MSI1C
S2B_MSIL1C_20220118T160559_N0301_R097_T17SPV_20220118T194707 2022-01-18T16:05:59  0% S2MSI1C
S2A_MSIL1C_20220304T160151_N0400_R097_T17SPV_20220304T200444 2022-03-04T16:01:51  0% S2MSI1C
S2A_MSIL1C_20220403T155821_N0400_R097_T17SPV_20220403T214354 2022-04-03T15:58:21  0% S2MSI1C
S2A_MSIL1C_20220423T155831_N0400_R097_T17SPV_20220423T212937 2022-04-23T15:58:31  0% S2MSI1C
S2B_MSIL1C_20220428T155819_N0400_R097_T17SPV_20220428T193905 2022-04-28T15:58:19  0% S2MSI1C
S2B_MSIL1C_20220428T155819_N0400_R097_T17SPV_20220712T074719 2022-04-28T15:58:19  0% S2MSI1C
S2A_MSIL1C_20220123T160551_N0301_R097_T17SPV_20220123T195033 2022-01-23T16:05:51  1% S2MSI1C
S2B_MSIL1C_20220528T155819_N0400_R097_T17SPV_20220528T194637 2022-05-28T15:58:19  1% S2MSI1C
S2A_MSIL1C_20220202T160501_N0400_R097_T17SPV_20220202T195450 2022-02-02T16:05:01 18% S2MSI1C
S2A_MSIL1C_20220212T160401_N0400_R097_T17SPV_20220212T195334 2022-02-12T16:04:01 29% S2MSI1C
S2B_MSIL1C_20220408T155819_N0400_R097_T17SPV_20220408T195945 2022-04-08T15:58:19 29% S2MSI1C"""
        i_eodag = Module(
            "i.eodag",
            flags="l",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-01-01",
            end="2022-06-01",
            clouds=50,
            map="durham",
            minimum_overlap=70,
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_minimum_overlap_b(self):
        """Test"""
        # i.eodag -lb provider=peps producttype=S2_MSI_L1C start=2022-05-01 end=2022-06-01 clouds=50 map=durham minimum_overlap=70
        output = r"""S2B_MSIL1C_20220528T155819_N0400_R097_T17SPV_20220528T194637 2022-05-28T15:58:19  1% S2MSI1C"""
        i_eodag = Module(
            "i.eodag",
            flags="lb",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-05-01",
            end="2022-06-01",
            clouds=50,
            map="durham",
            minimum_overlap=70,
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_area_relation(self):
        """Test"""
        output = r"""S2B_MSIL1C_20220528T155819_N0400_R097_T17SPV_20220528T194637 2022-05-28T15:58:19  1% S2MSI1C
S2A_MSIL1C_20220602T155831_N0400_R097_T17SPV_20220602T211840 2022-06-02T15:58:31  3% S2MSI1C
S2B_MSIL1C_20220617T155829_N0400_R097_T17SPV_20220618T113811 2022-06-17T15:58:29  8% S2MSI1C"""
        i_eodag = Module(
            "i.eodag",
            flags="lb",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-05-01",
            end="2022-07-01",
            clouds=50,
            area_relation="Contains",
            limit=3,
            map="durham",
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
