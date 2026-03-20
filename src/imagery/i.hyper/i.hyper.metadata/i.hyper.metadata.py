#!/usr/bin/env python3

##############################################################################
# MODULE:    i.hyper.metadata
# AUTHOR(S): Based on hyper_meta.py design
# PURPOSE:   View and manage hyperspectral metadata for 3D raster maps.
# COPYRIGHT: (C) 2025 by the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: View and manage hyperspectral metadata for 3D raster maps.
# % keyword: imagery
# % keyword: hyperspectral
# % keyword: metadata
# %end

# %option G_OPT_R3_INPUT
# % key: map
# % description: Input 3D raster map
# % required: yes
# %end

# %option
# % key: operation
# % type: string
# % required: no
# % multiple: no
# % options: summary,full,bands,history,validate
# % answer: summary
# % description: Operation to perform
# % descriptions: summary;Print concise metadata summary;full;Print full metadata for current map;bands;List source bands;history;Show full recursive ordered history;validate;Check metadata and lineage consistency
# %end

# %option
# % key: format
# % type: string
# % required: no
# % options: json,text,csv
# % answer: json
# % description: Output format
# %end

# %option
# % key: wavelength_range
# % type: string
# % required: no
# % description: Filter bands by wavelength range (e.g., 400-700)
# %end

# %option
# % key: resolve_names
# % type: string
# % required: no
# % multiple: no
# % options: yes,no
# % answer: no
# % description: Resolve map names by dataset_id for display (full and history)
# %end

import copy
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import grass.script as gs


def _import_hyper_meta():
    """Import the hyper_meta module from i_hyper_lib."""
    from grass.script.utils import get_lib_path
    import importlib.util

    path = get_lib_path(modname="i_hyper_lib", libname="hyper_meta")
    if not path:
        gs.fatal("Library path for hyper_meta not found.")
    if path not in sys.path:
        sys.path.append(path)

    spec = importlib.util.find_spec("hyper_meta")
    if not spec or not spec.loader:
        gs.fatal(f"Module hyper_meta not found at {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def _parse_timestamp(ts):
    """Parse ISO timestamp for sorting; unknown timestamps are ordered last."""
    if not ts:
        return datetime.max.replace(tzinfo=timezone.utc)
    text = str(ts).strip()
    if not text:
        return datetime.max.replace(tzinfo=timezone.utc)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        value = datetime.fromisoformat(text)
    except ValueError:
        return datetime.max.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _read_json(path):
    with open(path, "r") as f:
        return json.load(f)


def _load_raw_metadata(hyper_metadata_class, map_name):
    """Load raw JSON metadata for one map."""
    json_path = hyper_metadata_class._get_metadata_path(map_name)
    if not json_path.exists():
        gs.fatal(
            f"JSON metadata file not found for map '{map_name}' at '{json_path}'."
        )
    return _read_json(json_path)


def _discover_dataset_index():
    """
    Build dataset_id -> metadata record index by scanning current LOCATION mapsets.
    """
    env = gs.gisenv()
    location_path = Path(env["GISDBASE"]) / env["LOCATION_NAME"]
    index = {}
    duplicates = {}
    for mapset_dir in location_path.iterdir():
        if not mapset_dir.is_dir():
            continue
        grid3_dir = mapset_dir / "grid3"
        if not grid3_dir.is_dir():
            continue
        for map_dir in grid3_dir.iterdir():
            if not map_dir.is_dir():
                continue
            meta_path = map_dir / "hyper.json"
            if not meta_path.is_file():
                continue
            try:
                data = _read_json(meta_path)
            except Exception:
                continue
            dataset_id = data.get("dataset_id")
            if not dataset_id:
                continue
            map_name = f"{map_dir.name}@{mapset_dir.name}"
            if dataset_id in index:
                duplicates.setdefault(dataset_id, [index[dataset_id]["map_name"]]).append(
                    map_name
                )
                continue
            index[dataset_id] = {
                "map_name": map_name,
                "data": data,
                "path": str(meta_path),
            }
    return index, duplicates


def _normalize_io_ref(item):
    if isinstance(item, dict):
        return {"id": item.get("id"), "map_name": item.get("map_name")}
    if item is None:
        return {"id": None, "map_name": None}
    return {"id": str(item), "map_name": None}


def _resolve_io_refs(io_refs, dataset_index):
    resolved = []
    for item in io_refs or []:
        ref = _normalize_io_ref(item)
        ref_id = ref.get("id")
        if ref_id and ref_id in dataset_index:
            ref["map_name"] = dataset_index[ref_id]["map_name"]
        resolved.append(ref)
    return resolved


def _resolve_history_names(history_entries, dataset_index):
    out = []
    for step in history_entries or []:
        out.append(
            {
                "command": step.get("command"),
                "timestamp": step.get("timestamp"),
                "inputs": _resolve_io_refs(step.get("inputs"), dataset_index),
                "outputs": _resolve_io_refs(step.get("outputs"), dataset_index),
            }
        )
    return out


def _collect_aggregated_history(root_data, dataset_index):
    """
    Recursively collect all history entries from origin to current dataset,
    following inputs[].id references.
    """
    root_id = root_data.get("dataset_id")
    visited_dataset_ids = set()
    collected = []
    order = 0

    def visit_dataset(dataset_id):
        nonlocal order
        if not dataset_id or dataset_id in visited_dataset_ids:
            return
        visited_dataset_ids.add(dataset_id)

        record = dataset_index.get(dataset_id)
        data = record["data"] if record else (root_data if dataset_id == root_id else None)
        if data is None:
            return

        for step in data.get("processing_history", []) or []:
            entry = {
                "command": step.get("command"),
                "timestamp": step.get("timestamp"),
                "inputs": [_normalize_io_ref(i) for i in step.get("inputs", [])],
                "outputs": [_normalize_io_ref(o) for o in step.get("outputs", [])],
            }
            collected.append((_parse_timestamp(entry.get("timestamp")), order, entry))
            order += 1
            for inp in entry["inputs"]:
                visit_dataset(inp.get("id"))

    visit_dataset(root_id)
    collected.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in collected]


def _summary_from_data(data):
    bands = data.get("bands") or {}
    wavelengths = [w for w in (bands.get("wavelength") or []) if isinstance(w, (int, float))]
    summary = {
        "schema_version": data.get("schema_version"),
        "dataset_id": data.get("dataset_id"),
        "data_type": data.get("data_type"),
        "sensor": data.get("sensor"),
        "bands_count": bands.get("count"),
        "bands_count_valid": bands.get("count_valid"),
        "wavelength_units": data.get("wavelength_units"),
        "radiometric_quantity": data.get("radiometric_quantity"),
        "radiometric_units": data.get("radiometric_units"),
        "acquisition_datetime": data.get("acquisition_datetime"),
        "solar_zenith_angle": data.get("solar_zenith_angle"),
        "solar_azimuth_angle": data.get("solar_azimuth_angle"),
        "satellite_zenith_angle": data.get("satellite_zenith_angle"),
        "satellite_azimuth_angle": data.get("satellite_azimuth_angle"),
        "wavelength_min": min(wavelengths) if wavelengths else None,
        "wavelength_max": max(wavelengths) if wavelengths else None,
        "processing_steps_local": len(data.get("processing_history", []) or []),
    }
    return summary


def _write_csv(headers, rows):
    writer = csv.writer(sys.stdout)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)


def _print_summary(summary, output_format):
    if output_format == "json":
        print(json.dumps(summary, indent=2))
        return
    if output_format == "csv":
        _write_csv(list(summary.keys()), [list(summary.values())])
        return
    print("=" * 60)
    print("HYPERSPECTRAL METADATA SUMMARY")
    print("=" * 60)
    for key, value in summary.items():
        print(f"{key}: {value}")


def _to_csv_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return value


def _print_full(data, output_format):
    if output_format in ("json", "text"):
        print(json.dumps(data, indent=2))
        return
    rows = [(key, _to_csv_value(value)) for key, value in data.items()]
    _write_csv(["key", "value"], rows)


def _parse_wavelength_range(wavelength_range):
    if not wavelength_range:
        return None, None
    try:
        parts = wavelength_range.split("-")
        wl_min = float(parts[0]) if parts[0] else None
        wl_max = float(parts[1]) if len(parts) > 1 and parts[1] else None
        return wl_min, wl_max
    except ValueError:
        gs.fatal(f"Invalid wavelength range: {wavelength_range}")


def _build_band_rows(data, wavelength_range=None):
    bands = data.get("bands") or {}
    wavelengths = bands.get("wavelength") or []
    fwhm = bands.get("fwhm") or []
    validity = bands.get("validity") or []
    wl_min, wl_max = _parse_wavelength_range(wavelength_range)

    rows = []
    for i, wl in enumerate(wavelengths, start=1):
        if wl is None:
            continue
        if wl_min is not None and wl < wl_min:
            continue
        if wl_max is not None and wl > wl_max:
            continue
        rows.append(
            {
                "index": i,
                "wavelength": wl,
                "fwhm": fwhm[i - 1] if i - 1 < len(fwhm) else None,
                "validity": validity[i - 1] if i - 1 < len(validity) else None,
            }
        )
    return rows


def _print_bands(rows, output_format):
    if output_format == "json":
        print(json.dumps(rows, indent=2))
        return
    if output_format == "csv":
        csv_rows = []
        for row in rows:
            csv_rows.append(
                [row["index"], row["wavelength"], row["fwhm"], row["validity"]]
            )
        _write_csv(["index", "wavelength", "fwhm", "validity"], csv_rows)
        return
    print(f"{'Band':>5} {'Wavelength':>12} {'FWHM':>10} {'Validity':>10}")
    print("-" * 45)
    for row in rows:
        fwhm_str = f"{row['fwhm']:.2f}" if row["fwhm"] is not None else "-"
        validity = row["validity"]
        if validity is True:
            status = "VALID"
        elif validity is False:
            status = "INVALID"
        else:
            status = "UNKNOWN"
        print(f"{row['index']:>5} {row['wavelength']:>12.2f} {fwhm_str:>10} {status:>10}")
    print(f"\nTotal: {len(rows)} bands")


def _print_history(entries, output_format):
    if output_format == "json":
        print(json.dumps(entries, indent=2))
        return

    if output_format == "csv":
        csv_rows = []
        for idx, step in enumerate(entries, start=1):
            inputs = step.get("inputs", []) or []
            outputs = step.get("outputs", []) or []
            in_ids = ";".join([i.get("id") or "" for i in inputs])
            in_maps = ";".join([i.get("map_name") or "" for i in inputs])
            out_ids = ";".join([o.get("id") or "" for o in outputs])
            out_maps = ";".join([o.get("map_name") or "" for o in outputs])
            csv_rows.append(
                [
                    idx,
                    step.get("timestamp"),
                    step.get("command"),
                    in_ids,
                    in_maps,
                    out_ids,
                    out_maps,
                ]
            )
        _write_csv(
            [
                "step",
                "timestamp",
                "command",
                "input_ids",
                "input_map_names",
                "output_ids",
                "output_map_names",
            ],
            csv_rows,
        )
        return

    if not entries:
        print("No processing history recorded.")
        return

    print("PROCESSING HISTORY (AGGREGATED)")
    print("=" * 60)
    for idx, step in enumerate(entries, start=1):
        print(f"\nStep {idx}:")
        print(f"  Command: {step.get('command') or ''}")
        print(f"  Timestamp: {step.get('timestamp') or ''}")
        inputs = step.get("inputs", []) or []
        outputs = step.get("outputs", []) or []
        print("  Inputs:")
        if not inputs:
            print("    -")
        for item in inputs:
            print(f"    id={item.get('id')} map_name={item.get('map_name')}")
        print("  Outputs:")
        if not outputs:
            print("    -")
        for item in outputs:
            print(f"    id={item.get('id')} map_name={item.get('map_name')}")


def _validate_metadata(meta, data, map_name, dataset_index, duplicate_dataset_ids=None):
    issues = []

    # Base API validation
    issues.extend(meta.validate())

    # New-schema required fields
    for required in ("schema_version", "dataset_id", "data_type", "bands", "processing_history"):
        if required not in data:
            issues.append(f"Missing required top-level key: {required}")

    bands = data.get("bands") or {}
    count = bands.get("count")
    count_valid = bands.get("count_valid")
    wavelengths = bands.get("wavelength")
    fwhm = bands.get("fwhm")
    validity = bands.get("validity")

    if count is None:
        issues.append("bands.count is missing")
    if count_valid is None:
        issues.append("bands.count_valid is missing")

    if wavelengths is not None and not isinstance(wavelengths, list):
        issues.append("bands.wavelength must be an array")
    if fwhm is not None and not isinstance(fwhm, list):
        issues.append("bands.fwhm must be an array")
    if validity is not None and not isinstance(validity, list):
        issues.append("bands.validity must be an array")

    if isinstance(count, int) and count >= 0:
        if isinstance(wavelengths, list) and len(wavelengths) != count:
            issues.append("bands.count does not match len(bands.wavelength)")
        if isinstance(fwhm, list) and len(fwhm) != count:
            issues.append("bands.count does not match len(bands.fwhm)")
        if isinstance(validity, list) and len(validity) != count:
            issues.append("bands.count does not match len(bands.validity)")

    if isinstance(count, int) and isinstance(count_valid, int) and count_valid > count:
        issues.append("bands.count_valid cannot be larger than bands.count")

    if isinstance(validity, list) and isinstance(count_valid, int):
        valid_sum = int(sum(bool(v) for v in validity))
        if valid_sum != count_valid:
            issues.append(
                "bands.count_valid does not match sum(bands.validity)"
            )

    # Raster depth consistency
    try:
        info = gs.parse_command("r3.info", map=map_name, flags="g")
        depth = int(float(info.get("depths")))
        expected_depth = None
        if isinstance(count_valid, int):
            expected_depth = count_valid
        elif isinstance(count, int):
            expected_depth = count
        if expected_depth is not None and depth != expected_depth:
            issues.append(
                f"Raster depth mismatch: depths={depth}, expected={expected_depth}"
            )
    except Exception as exc:
        issues.append(f"Could not validate raster depth with r3.info: {exc}")

    # Lineage consistency: one producer per output dataset_id in aggregated history
    aggregated = _collect_aggregated_history(data, dataset_index)
    producer_counts = {}
    referenced_input_ids = set()
    for step in aggregated:
        for out in step.get("outputs", []) or []:
            out_id = out.get("id")
            if out_id:
                producer_counts[out_id] = producer_counts.get(out_id, 0) + 1
        for inp in step.get("inputs", []) or []:
            in_id = inp.get("id")
            if in_id:
                referenced_input_ids.add(in_id)

    for dataset_id, n_producers in producer_counts.items():
        if n_producers > 1:
            issues.append(
                f"Dataset '{dataset_id}' has multiple producing history entries ({n_producers})"
            )

    root_dataset_id = data.get("dataset_id")
    if root_dataset_id:
        n_root = producer_counts.get(root_dataset_id, 0)
        if n_root == 0:
            issues.append(
                f"Current dataset_id '{root_dataset_id}' has no producing history entry"
            )
        elif n_root > 1:
            issues.append(
                f"Current dataset_id '{root_dataset_id}' has multiple producing history entries ({n_root})"
            )

    for input_id in sorted(referenced_input_ids):
        if input_id not in dataset_index and input_id not in producer_counts:
            issues.append(
                f"Input dataset_id '{input_id}' cannot be resolved in current LOCATION"
            )

    if duplicate_dataset_ids:
        for dsid, maps in sorted(duplicate_dataset_ids.items()):
            joined = ", ".join(maps)
            issues.append(f"Duplicate dataset_id '{dsid}' found in maps: {joined}")

    # Deduplicate while keeping order
    unique = []
    seen = set()
    for issue in issues:
        if issue in seen:
            continue
        seen.add(issue)
        unique.append(issue)
    return unique


def _print_validate(issues, output_format):
    valid = len(issues) == 0
    if output_format == "json":
        print(json.dumps({"valid": valid, "issues": issues}, indent=2))
        return 0 if valid else 1

    if output_format == "csv":
        rows = []
        if valid:
            rows.append(["OK", "Metadata validation passed"])
        else:
            for issue in issues:
                rows.append(["ISSUE", issue])
        _write_csv(["status", "message"], rows)
        return 0 if valid else 1

    if valid:
        print("Metadata validation passed")
        return 0
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
    return 1


def main():
    options, _ = gs.parser()

    map_name = options["map"]
    operation = options["operation"]
    output_format = options["format"]
    wavelength_range = options.get("wavelength_range")
    resolve_names = options.get("resolve_names", "no") == "yes"

    # Import metadata API
    hyper_meta = _import_hyper_meta()
    HyperMetadata = hyper_meta.HyperMetadata

    # Check map exists and normalize to full map name
    found = gs.find_file(map_name, element="grid3")
    if not found["fullname"]:
        gs.fatal(f"3D raster map '{map_name}' not found")
    full_map_name = found["fullname"]

    # Load both object and raw JSON
    try:
        meta = HyperMetadata.load(full_map_name)
        raw = _load_raw_metadata(HyperMetadata, full_map_name)
    except Exception as e:
        gs.fatal(f"Failed to load metadata: {e}")

    # Build dataset index where needed
    need_index = operation in ("full", "history", "validate") or resolve_names
    if need_index:
        dataset_index, duplicate_dataset_ids = _discover_dataset_index()
    else:
        dataset_index, duplicate_dataset_ids = {}, {}
    dataset_id = raw.get("dataset_id")
    if dataset_id:
        dataset_index[dataset_id] = {
            "map_name": full_map_name,
            "data": raw,
            "path": str(HyperMetadata._get_metadata_path(full_map_name)),
        }

    if operation == "summary":
        summary = _summary_from_data(raw)
        _print_summary(summary, output_format)
        return 0

    if operation == "full":
        full_data = copy.deepcopy(raw)
        if resolve_names:
            full_data["processing_history"] = _resolve_history_names(
                full_data.get("processing_history", []), dataset_index
            )
        _print_full(full_data, output_format)
        return 0

    if operation == "bands":
        rows = _build_band_rows(raw, wavelength_range)
        _print_bands(rows, output_format)
        return 0

    if operation == "history":
        entries = _collect_aggregated_history(raw, dataset_index)
        if resolve_names:
            entries = _resolve_history_names(entries, dataset_index)
        _print_history(entries, output_format)
        return 0

    if operation == "validate":
        issues = _validate_metadata(
            meta,
            raw,
            full_map_name,
            dataset_index,
            duplicate_dataset_ids=duplicate_dataset_ids,
        )
        return _print_validate(issues, output_format)

    gs.fatal(f"Unsupported operation: {operation}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
