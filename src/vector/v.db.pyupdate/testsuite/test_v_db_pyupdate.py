#!/usr/bin/env python3

"""Test of v.db.pyupdate module

Author: Vaclav Petras
"""

import json

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

import grass.script as gs


class TestVDbPyUpdate(TestCase):
    """Test v.db.pyupdate module"""

    vector_name = "test_hospitals"

    def setUp(self):
        """Copy vector to current mapset"""
        self.runModule("g.copy", vector=("hospitals", self.vector_name))

    def tearDown(self):
        """Remove vector"""
        self.runModule("g.remove", flags="f", type="vector", name=self.vector_name)

    def test_minimal(self):
        """Check if module with minimal set of parameters"""
        self.runModule(
            "v.db.addcolumn", map=self.vector_name, columns="display_phone text"
        )
        self.assertModule(
            "v.db.pyupdate",
            map=self.vector_name,
            column="display_phone",
            expression="f'Phone num. {phone}'",
        )
        table = json.loads(
            gs.read_command("v.db.select", map=self.vector_name, format="json")
        )["records"]
        for row in table:
            self.assertTrue(
                row["display_phone"].startswith("Phone num. "),
                msg="Table does not have expected values for row: {row}".format(
                    **locals()
                ),
            )

    def test_main_parameters(self):
        """Check if module with the main set of parameters"""
        self.runModule(
            "v.db.addcolumn", map=self.vector_name, columns="display_phone text"
        )
        self.assertModule(
            "v.db.pyupdate",
            map=self.vector_name,
            column="display_phone",
            expression="f'Phone num. {phone}'",
            condition="phone.startswith('(919)')",
            where="phone is not null",
        )
        table = json.loads(
            gs.read_command("v.db.select", map=self.vector_name, format="json")
        )["records"]
        for row in table:
            if row["PHONE"]:
                if row["PHONE"].startswith("(919)"):
                    self.assertTrue(
                        row["display_phone"].startswith("Phone num. (919)"),
                        msg="Column does not contain the expected prefix: {row}".format(
                            **locals()
                        ),
                    )
                else:
                    self.assertTrue(row["display_phone"] is None)


if __name__ == "__main__":
    test()
