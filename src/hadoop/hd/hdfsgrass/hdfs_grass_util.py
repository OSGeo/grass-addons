import csv
import os
import tempfile


def save_dict(fn, dict_rap):
    f = open(fn, "wb")
    w = csv.writer(f, delimiter="=")
    for key, val in dict_rap.items():
        if val is None or val == "":
            continue
        w.writerow([key, val])
    f.close()


def read_dict(fn):
    if os.path.exists(fn):
        f = open(fn, "r")
        dict_rap = {}
        try:
            for key, val in csv.reader(f, delimiter="="):
                try:
                    dict_rap[key] = eval(val)
                except:
                    val = '"' + val + '"'
                    dict_rap[key] = eval(val)
            f.close()
            return dict_rap
        except IOError as e:
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
    else:
        return {}


def get_tmp_folder():
    return tempfile.gettempdir()
