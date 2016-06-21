from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import sys

import grass.script as grass
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

BASE_LOG_URL = 'log'
GISDBASE = grass.gisenv()['GISDBASE']
LOCATION_NAME = grass.gisenv()['LOCATION_NAME']
MAPSET = grass.gisenv()['MAPSET']
MAPSET_PATH = os.path.join(GISDBASE, LOCATION_NAME, MAPSET)

SQL_ALCHEMY_CONN = 'sqlite:////%s' % os.path.join(MAPSET_PATH, 'sqlite', 'sqlite.db')

LOGGING_LEVEL = logging.INFO

engine_args = {}
if 'sqlite' not in SQL_ALCHEMY_CONN:
    # Engine args not supported by sqlite
    engine_args['pool_size'] = 5
    engine_args['pool_recycle'] = 3600

# print(SQL_ALCHEMY_CONN)
engine = create_engine(SQL_ALCHEMY_CONN, **engine_args)

Session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine))

LOG_FORMAT = (
    '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')
SIMPLE_LOG_FORMAT = '%(asctime)s %(levelname)s - %(message)s'

grass_config = os.path.join(MAPSET_PATH, 'grasshdfs.conf')


# print(grass_config)



def configure_logging():
    logging.root.handlers = []
    logging.basicConfig(
        format=LOG_FORMAT, stream=sys.stdout, level=LOGGING_LEVEL)


configure_logging()
