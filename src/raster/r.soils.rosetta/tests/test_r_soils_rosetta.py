import numpy as np

from grass.tools import Tools


def test_output_exists(session):
    tools = Tools(session=session, consistent_return_value=False)
    output = tools.r_soils_rosetta(input="data", output=np.array)
    # check that output raster exists
    assert output is not None
    # check that output raster has no NaN values
    assert np.any(np.isnan(output))
