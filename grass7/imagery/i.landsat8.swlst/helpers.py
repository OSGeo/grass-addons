import os
import grass.script as grass
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import general as g
from landsat8_mtl import Landsat8_MTL

def cleanup():
    """
    Clean up temporary maps
    """
    grass.run_command('g.remove', flags='f', type="rast",
                      pattern='tmp.{pid}*'.format(pid=os.getpid()), quiet=True)

    if grass.find_file(name='MASK', element='cell')['file']:
        r.mask(flags='r', verbose=True)


def tmp_map_name(name):
    """
    Return a temporary map name, for example:

    tmp_avg_lse = tmp + '.avg_lse'
    """
    temporary_file = grass.tempfile()
    tmp = "tmp." + grass.basename(temporary_file)  # use its basename
    return tmp + '.' + str(name)


def run(cmd, **kwargs):
    """
    Pass required arguments to grass commands (?)
    """
    grass.run_command(cmd, quiet=True, **kwargs)


def save_map(mapname):
    """
    Helper function to save some in-between maps, assisting in debugging
    """
    # run('r.info', map=mapname, flags='r')
    run('g.copy', raster=(mapname, 'DebuggingMap'))


def extract_number_from_string(string):
    """
    Extract the (integer) number from a string. Meant to be used with band
    names. For example:

    print(extract_number_from_string('B10'))

    will return

    10
    """
    import re
    return str(re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
               string)[-1])


def add_timestamp(mtl_filename, outname):
    """
    Retrieve metadata from MTL file.
    """
    import datetime
    metadata = Landsat8_MTL(mtl_filename)

    # required format is: day=integer month=string year=integer time=hh:mm:ss.dd
    acquisition_date = str(metadata.date_acquired)  ### FixMe ###
    acquisition_date = datetime.datetime.strptime(acquisition_date, '%Y-%m-%d').strftime('%d %b %Y')
    acquisition_time = str(metadata.scene_center_time)[0:8]
    date_time_string = acquisition_date + ' ' + acquisition_time

    #msg = "Date and time of acquisition: " + date_time_string
    #grass.verbose(msg)

    run('r.timestamp', map=outname, date=date_time_string)


def mask_clouds(qa_band, qa_pixel):
    """
    ToDo:

    - a better, independent mechanism for QA. --> see also Landsat8 class.
    - support for multiple qa_pixel values (eg. input as a list of values)

    Create and apply a cloud mask based on the Quality Assessment Band
    (BQA.) Source: <http://landsat.usgs.gov/L8QualityAssessmentBand.php

    See also:
    http://courses.neteler.org/processing-landsat8-data-in-grass-gis-7/#Applying_the_Landsat_8_Quality_Assessment_%28QA%29_Band
    """
    msg = ('\n|i Masking for pixel values <{qap}> '
           'in the Quality Assessment band.'.format(qap=qa_pixel))
    g.message(msg)

    #tmp_cloudmask = tmp_map_name('cloudmask')
    #qabits_expression = 'if({band} == {pixel}, 1, null())'.format(band=qa_band,
    #                                                              pixel=qa_pixel)

    #cloud_masking_equation = equation.format(result=tmp_cloudmask,
    #                                         expression=qabits_expression)
    #grass.mapcalc(cloud_masking_equation)

    r.mask(raster=qa_band, maskcats=qa_pixel, flags='i', overwrite=True)

    # save for debuging
    #save_map(tmp_cloudmask)
