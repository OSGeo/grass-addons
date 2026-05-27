"""Conversion between GRASS vector maps and RichDEM depression hierarchy objects."""

import math
import os
import sqlite3
import grass.script as gs
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point

# std::numeric_limits<uint32_t>::max() — used as NO_VALUE / NO_PARENT sentinel
_NO_VALUE = 2**32 - 1

_SCHEMA_COLS = (
    "type VARCHAR(4), "
    "pit_cell INTEGER, out_cell INTEGER, "
    "parent INTEGER, odep INTEGER, lchild INTEGER, rchild INTEGER, geolink INTEGER, "
    "pit_elev DOUBLE PRECISION, out_elev DOUBLE PRECISION, "
    "ocean_parent INTEGER, cell_count INTEGER, "
    "dep_vol DOUBLE PRECISION, water_vol DOUBLE PRECISION, total_elevation DOUBLE PRECISION"
)

# Ordered list of the 15 data columns (excluding cat and dep_label)
_DATA_COLS = [c.split()[0] for c in _SCHEMA_COLS.split(",")]


def _flat_to_xy(flat_idx, region):
    row, col = divmod(int(flat_idx), int(region["cols"]))
    x = region["w"] + (col + 0.5) * region["ewres"]
    y = region["n"] - (row + 0.5) * region["nsres"]
    return x, y


def _null_int(val):
    v = int(val)
    return None if v == _NO_VALUE else v


def _null_float(val):
    f = float(val)
    return None if math.isinf(f) or math.isnan(f) else f


def _dep_row(dep):
    """Return the 15 data-column values for a Depression, in _DATA_COLS order."""
    return (
        "leaf" if int(dep.lchild) == _NO_VALUE else "meta",
        int(dep.pit_cell), int(dep.out_cell),
        _null_int(dep.parent), _null_int(dep.odep),
        _null_int(dep.lchild), _null_int(dep.rchild), _null_int(dep.geolink),
        _null_float(dep.pit_elev), _null_float(dep.out_elev),
        int(dep.ocean_parent), int(dep.cell_count),
        float(dep.dep_vol), float(dep.water_vol), float(dep.total_elevation),
    )


def depressions_to_grass(deps, labels, flowdirs, map_name, overwrite=False):
    """Write a RichDEM depression hierarchy to a GRASS vector map.

    Layer 1 (depressions table): one feature per depression.
      - Leaf depressions: area polygon (from labels raster) + centroid inside area.
      - Metadepressions: point at out_cell (the saddle between child depressions).
    Layer 2 (ocean_links table): one row per ocean_linked entry.
    """
    from _richdem.depression_hierarchy import OCEAN
    from librichdem.raster import rdarray_to_grass

    OCEAN_val = int(OCEAN)
    region = gs.region()

    # --- Step 1: labels raster → leaf depression areas ---
    tmp = f"tmp_rdlabels_{os.getpid()}"
    rdarray_to_grass(labels, tmp, overwrite=True)
    # Null OCEAN cells so r.to.vect only creates areas for actual depressions
    gs.run_command("r.null", map=tmp, setnull=str(OCEAN_val), quiet=True)
    gs.run_command(
        "r.to.vect",
        input=tmp, output=map_name, type="area",
        column="dep_label", flags="s", overwrite=overwrite, quiet=True,
    )
    gs.run_command("g.remove", type="raster", name=tmp, flags="f", quiet=True)

    # --- Step 2: add schema columns ---
    gs.run_command(
        "v.db.addcolumn", map=map_name, columns=_SCHEMA_COLS, quiet=True,
    )

    # --- Step 3: populate attribute table ---
    db_info = gs.vector_db(map=map_name)
    db_path = db_info[1]["database"]
    tbl = db_info[1]["table"]
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    set_clause = ", ".join(f"{c}=?" for c in _DATA_COLS)

    # Update leaf rows (already created by r.to.vect, keyed by dep_label column).
    for dep in deps:
        if dep.dep_label == OCEAN_val or int(dep.lchild) != _NO_VALUE:
            continue
        cur.execute(
            f"UPDATE {tbl} SET {set_clause} WHERE dep_label=?",
            _dep_row(dep) + (dep.dep_label,),
        )

    # Determine the next free cat so metadepression rows don't collide with
    # the sequential cats that r.to.vect assigned to leaf areas.
    cur.execute(f"SELECT MAX(cat) FROM {tbl}")
    next_cat = (cur.fetchone()[0] or 0) + 1

    # Assign a stable cat to each metadepression and write the point geometry.
    meta_deps = [d for d in deps if d.dep_label != OCEAN_val and int(d.lchild) != _NO_VALUE]
    meta_cat = {dep.dep_label: next_cat + i for i, dep in enumerate(meta_deps)}

    with VectorTopo(map_name, mode="rw") as vmap:
        for dep in meta_deps:
            x, y = _flat_to_xy(dep.out_cell, region)
            vmap.write(Point(x, y), cat=meta_cat[dep.dep_label])

    insert_cols = f"cat, dep_label, {', '.join(_DATA_COLS)}"
    insert_placeholders = ", ".join(["?"] * (2 + len(_DATA_COLS)))
    for dep in meta_deps:
        cur.execute(
            f"INSERT INTO {tbl} ({insert_cols}) VALUES ({insert_placeholders})",
            (meta_cat[dep.dep_label], dep.dep_label) + _dep_row(dep),
        )

    # --- Step 5: ocean_links junction table as layer 2 ---
    cur.execute(
        "CREATE TABLE ocean_links "
        "(cat INTEGER PRIMARY KEY, dep_label INTEGER, linked_label INTEGER)"
    )
    cur.executemany(
        "INSERT INTO ocean_links (dep_label, linked_label) VALUES (?, ?)",
        [(dep.dep_label, lnk) for dep in deps for lnk in dep.ocean_linked],
    )
    conn.commit()
    conn.close()

    gs.run_command(
        "v.db.connect", map=map_name, table="ocean_links",
        layer=2, key="cat", quiet=True,
    )


def depressions_from_grass(map_name):
    """Read a GRASS depression hierarchy vector map back into a Depression list."""
    db_info = gs.vector_db(map=map_name)
    if 1 not in db_info:
        gs.fatal(f"Vector map {map_name} has no layer 1 attribute table.")

    db_path = db_info[1]["database"]
    tbl = db_info[1]["table"]
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(f"""
        SELECT dep_label, pit_cell, out_cell, parent, odep, lchild, rchild,
               geolink, pit_elev, out_elev, ocean_parent, cell_count,
               dep_vol, water_vol, total_elevation
        FROM {tbl}
        GROUP BY dep_label
        ORDER BY dep_label
    """)
    rows = cur.fetchall()

    cur.execute("SELECT dep_label, linked_label FROM ocean_links ORDER BY dep_label")
    from collections import defaultdict
    ocean_linked = defaultdict(list)
    for dep_label, linked_label in cur.fetchall():
        ocean_linked[dep_label].append(linked_label)

    conn.close()

    def restore_int(val):
        """NULL in SQLite means NO_VALUE sentinel for uint32 fields."""
        return _NO_VALUE if val is None else int(val)

    def restore_float(val):
        """NULL in SQLite means infinity for unset elevation fields."""
        return float("inf") if val is None else float(val)

    from _richdem.depression_hierarchy import Depression

    deps = []
    for row in rows:
        (dep_label, pit_cell, out_cell, parent, odep, lchild, rchild,
         geolink, pit_elev, out_elev, ocean_parent, cell_count,
         dep_vol, water_vol, total_elevation) = row

        d = Depression()
        d.dep_label       = int(dep_label)
        d.pit_cell        = int(pit_cell)
        d.out_cell        = int(out_cell)
        d.parent          = restore_int(parent)
        d.odep            = restore_int(odep)
        d.lchild          = restore_int(lchild)
        d.rchild          = restore_int(rchild)
        d.geolink         = restore_int(geolink)
        d.pit_elev        = restore_float(pit_elev)
        d.out_elev        = restore_float(out_elev)
        d.ocean_parent    = bool(ocean_parent)
        d.cell_count      = int(cell_count)
        d.dep_vol         = float(dep_vol)
        d.water_vol       = float(water_vol)
        d.total_elevation = float(total_elevation)
        d.ocean_linked    = ocean_linked.get(dep_label, [])
        deps.append(d)

    return deps


def update_water_vol(deps, map_name):
    """Write updated water_vol values from Depression list back to the vector map."""
    db_info = gs.vector_db(map=map_name)
    db_path = db_info[1]["database"]
    tbl = db_info[1]["table"]
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executemany(
        f"UPDATE {tbl} SET water_vol = ? WHERE dep_label = ?",
        [(d.water_vol, d.dep_label) for d in deps],
    )
    conn.commit()
    conn.close()
