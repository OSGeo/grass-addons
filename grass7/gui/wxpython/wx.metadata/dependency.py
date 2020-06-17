owslib=False
try:
    import owslib
    owslib=True
except:
    print('owslib library is missing. Check requirements on the manual page < https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support >')

if owslib:
    import owslib
    owsvs= owslib.__version__
    try:
        from owslib.iso import *

        MD_Metadata()
    except:
        print('Installed version of owslib library is < %s >.'%owsvs)
        print('owslib >=0.9 is required. Check requirements on the manual page < https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support >')


try:
    import jinja2
except:
    print('jinja2 library is missing. Check requirements on the manual page < https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support >')
pycsw=False

try:
    import pycsw
    pycsw=True
except:
    print('pycsw library is missing. Check requirements on the manual page < https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support >')

try:
    import reportlab
except:
    print('python-import reportlab library is missing. Check requirements on the manual page < https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support >')

if pycsw:
    import pycsw
    cswvs= pycsw.__version__
    try:
        from pycsw.core import admin
    except:
        print('Installed version of pycsw library is < %s >.'%cswvs)
        print('pycsw >=2.0 is required. Check requirements on the manual page < https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support >')


from owslib.iso import *
import jinja2
from pycsw.core import admin
import reportlab

