import pathlib
import shlex
import shutil
import subprocess

from ruamel.yaml import YAML

yaml=YAML(typ="safe", pure=True)

TEST_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = TEST_DIR / "data"
ROOT_DIR = TEST_DIR.parent
GRASSDB = DATA_DIR / "grassdb_estimap_recreation"
GRASSDB_TAR = DATA_DIR / "example_grassdb_epsg_3035.tar.gz"


def check_wget_availability():
    if not shutil.which("wget"):
        raise ValueError("wget is missing, please install it and re-run")


def download_data():
    cmd = "wget https://gitlab.com/natcapes/r.estimap.recreation.data/raw/master/example_grassdb_epsg_3035.tar.gz"
    proc = subprocess.run(shlex.split(cmd), cwd=DATA_DIR, check=True)


def extract_data():
    # cleanup (needed in case data files have changed and we have manually updated the tar)
    print("Cleaning up existing data fixtures")
    cmd = f"rm -rf {GRASSDB.as_posix()}"
    proc = subprocess.run(shlex.split(cmd), cwd=DATA_DIR, check=True)
    # extract
    print("Extracting data fixtures")
    cmd = "tar xf example_grassdb_epsg_3035.tar.gz"
    proc = subprocess.run(shlex.split(cmd), cwd=DATA_DIR, check=True)


def ensure_data_availability():
    if not GRASSDB.exists():
        check_wget_availability()
        print("Downloading data")
        download_data()
        extract_data()


ensure_data_availability()
