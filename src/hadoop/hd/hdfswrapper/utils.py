import errno
import json
import shutil
from tempfile import mkdtemp

try:
    from cryptography.fernet import Fernet
except:
    pass


def TemporaryDirectory(suffix="", prefix=None, dir=None):
    name = mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
    try:
        yield name
    finally:
        try:
            shutil.rmtree(name)
        except OSError as e:
            # ENOENT - no such file or directory
            if e.errno != errno.ENOENT:
                raise e


def generate_fernet_key():
    try:
        FERNET_KEY = Fernet.generate_key().decode()
    except NameError:
        FERNET_KEY = "cryptography_not_found_storing_passwords_in_plain_text"
    return FERNET_KEY


def string2dict(string):
    try:
        print(string)
        return json.loads(string.replace("'", '"'))

    except Exception as e:
        print("Dictionary is not valid: %s" % e)
        return None


def find_ST_fnc(hsql):
    """
    Parse hsql query and find ST_ functions.
    :param hsql: string of hive query.
    :type hsql: string
    :return: dict {ST_fce: com.esri.hadoop.hive.ST_fce} (name: java path )
    :rtype: dict
    """
    first = "ST_"
    last = "("
    ST = {}
    for s in hsql.split("("):
        if s.find("ST_"):
            s = s.split("ST_")
            fc = "ST_%s" % s[0]
            if fc not in ST:
                ST[s] = "com.esri.hadoop.hive.%s" % fc

    return ST
