import subprocess
import shlex
import shutil
from .utilities import (
    exec_grass,
    construct_r_estimap_command,
    generate_univar_md5sum,
    generate_csv_md5sum,
)
from . import GRASSDB


def estimap_test_runner(test_case):
    mapset = f"{GRASSDB}/{test_case['mapset']}"

    # check if the mapset already exists
    cmd = f"grass {GRASSDB}/PERMANENT --exec g.mapset -l"
    proc = subprocess.run(shlex.split(cmd), check=True, universal_newlines=True, stdout=subprocess.PIPE)
    if test_case["mapset"] in proc.stdout:
        # The mapset already exists. Cleanup maps and remove it.
        # Cleaning up the maps is necessary due to GRASS linking maps
        exec_grass(mapset, "g.remove -f type=all pattern=*")
        shutil.rmtree(mapset, ignore_errors=True)

    # create temporary mapset
    cmd = f"grass -c -e {mapset}"
    proc = subprocess.run(shlex.split(cmd), check=True)

    # add the 'sample_data' Mapset to the current Mapset's search path
    exec_grass(mapset, "g.mapsets sample_data operation=add")

    # set region
    exec_grass(mapset, "g.region raster=input_area_of_interest")

    # run the test
    estimap_cmd = construct_r_estimap_command(test_case)
    exec_grass(mapset, f"{estimap_cmd}")

    # check map hashes
    for i, (key, data) in enumerate(test_case["outputs"]["maps"].items()):
        map_name = data["name"]
        expected_hash = data["hash"]
        generated_hash = generate_univar_md5sum(mapset, map_name)
        assert expected_hash == generated_hash, f"map hash mismatch: {map_name}"

    # check csv hashes
    for i, (key, data) in enumerate(test_case["outputs"]["csvs"].items()):
        csv_name = data["name"]
        expected_hash = data["hash"]
        generated_hash = generate_csv_md5sum(mapset, csv_name)
        assert expected_hash == generated_hash, f"csv hash mismatch: {csv_name}"
