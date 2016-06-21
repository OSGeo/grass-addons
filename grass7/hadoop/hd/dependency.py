owslib=False
try:
    import sqlalchemy
except:
    print'sqlalchemy library is missing.'

try:
    from snakebite.client import Client, HAClient, Namenode
except:
    print'snakebite library is missing.'

try:
    import thrift
except:
    print('thrift library is missing.')

try:
    import hdfs
except:
    print('hdfs library is missing.')

import hdfs
import thrift
from snakebite.client import Client, HAClient, Namenode
import sqlalchemy

