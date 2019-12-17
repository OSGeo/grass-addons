import hashlib
import os
import pathlib
import shlex
import subprocess
import tempfile
import uuid


def exec_grass(mapset, cmd, **kwargs):
    cmd = f"grass {mapset} --exec {cmd}"
    process = subprocess.run(shlex.split(cmd), check=True, **kwargs)
    return process


def construct_r_estimap_command(test_case):
    flags = " ".join(test_case["flags"])
    inputs = " ".join([f"{k}={','.join(v)}" for (k, v) in test_case["inputs"].items()])
    output_maps = " ".join([f"{k}={v['name']}" for (k, v) in test_case["outputs"]["maps"].items()])
    output_csvs = " ".join([f"{k}={v['name']}" for (k, v) in test_case["outputs"]["csvs"].items()])
    cmd = f"r.estimap.recreation {flags} {inputs} {output_maps} {output_csvs}"
    return cmd


def generate_univar_md5sum(mapset, map_name):
    txt = pathlib.Path("/tmp") / f"{uuid.uuid4().hex}.txt"
    exec_grass(mapset, f"r.univar --o -e {map_name} output={txt.as_posix()}")
    m = hashlib.md5()
    m.update(txt.read_bytes())
    return m.hexdigest()


def generate_csv_md5sum(mapset, csv_file):
    m = hashlib.md5()
    m.update(pathlib.Path(csv_file).read_bytes())
    return m.hexdigest()
