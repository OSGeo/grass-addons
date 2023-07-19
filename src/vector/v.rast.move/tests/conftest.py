"""Setup dataset for v.rast.move test"""

from types import SimpleNamespace

import pytest

import grass.script as gs

LINES = """\
VERTI:
L  9 1
 0.0984456    0.61658031
 0.15025907   0.68264249
 0.2642487    0.76943005
 0.39119171   0.79792746
 0.52202073   0.80181347
 0.62953368   0.78367876
 0.68134715   0.73056995
 0.71243523   0.64637306
 0.73445596   0.54663212
 1     1
L  8 1
 0.09455959   0.40544041
 0.31217617   0.40673575
 0.61917098   0.40932642
 0.75518135   0.41580311
 0.86658031   0.41580311
 0.86528497   0.35621762
 0.87305699   0.20595855
 0.87823834   0.08290155
 1     2
"""

MIX = """\
VERTI:
L  9 1
 0.0984456    0.61658031
 0.15025907   0.68264249
 0.2642487    0.76943005
 0.39119171   0.79792746
 0.52202073   0.80181347
 0.62953368   0.78367876
 0.68134715   0.73056995
 0.71243523   0.64637306
 0.73445596   0.54663212
 1     1
P  1 1
 0.09455000   0.40540000
 1     3
"""


@pytest.fixture(scope="module")
def line_dataset(tmp_path_factory):
    """Create a session and fill mapset with data"""
    tmp_path = tmp_path_factory.mktemp("line_dataset")
    location = "test"
    lines_name = "lines"
    mix_name = "mix"
    gs.core._create_location_xy(tmp_path, location)  # pylint: disable=protected-access
    with gs.setup.init(tmp_path / location):
        gs.write_command(
            "v.in.ascii", input="-", output=lines_name, stdin=LINES, format="standard"
        )
        gs.run_command("g.region", vector=lines_name, grow=0.1, res=0.01, flags="a")

        x_name = "x"
        y_name = "y"
        x_value = 2.0
        y_value = 5.3
        nulls_name = "null_only"
        gs.mapcalc(f"{x_name} = {x_value}")
        gs.mapcalc(f"{y_name} = {y_value}")
        gs.mapcalc(f"{nulls_name} = 0.0 + null()")

        gs.write_command(
            "v.in.ascii", input="-", output=mix_name, stdin=MIX, format="standard"
        )

        yield SimpleNamespace(
            name=lines_name,
            x=x_name,
            y=y_name,
            x_value=x_value,
            y_value=y_value,
            nulls=nulls_name,
            mix_name=mix_name,
        )
