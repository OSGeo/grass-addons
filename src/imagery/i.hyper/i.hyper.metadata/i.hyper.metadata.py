#!/usr/bin/env python3

##############################################################################
# MODULE:    i.hyper.metadata
# AUTHOR(S): Based on hyper_meta.py design
#            Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
#            Anna Petrasova, NCSU GeoForAll Lab
# PURPOSE:   View and manage hyperspectral metadata for 3D raster maps.
# COPYRIGHT: (C) 2025 by the authors
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
# % options: summary,full,resolved,extended,bands,history,validate,copy,derive,merge-overrides,add-history
# % answer: summary
# % description: Operation to perform
# % descriptions: summary;Print concise metadata summary;full;Print raw metadata for current map;resolved;Print metadata with inherited values materialized and form-value fields unwrapped;extended;Print selected parts of extended_metadata;bands;List source bands;history;Show full recursive ordered history;validate;Check metadata and lineage consistency;copy;Copy metadata from another hyperspectral cube and preserve this map's last local processing step;derive;Create derived metadata from one source map with a new dataset ID and one local history entry;merge-overrides;Apply top-level metadata overrides and merge extended_metadata into an existing map;add-history;Append a processing history entry to an existing map
# %end

# %option G_OPT_R3_INPUT
# % key: source_map
# % description: Source 3D raster map (required for operation=copy, operation=derive, and operation=add-history)
# % required: no
# %end

# %option
# % key: overrides
# % type: string
# % required: no
# % multiple: no
# % description: JSON string of metadata overrides for operation=derive or operation=merge-overrides
# %end

# %option
# % key: overrides_file
# % type: string
# % required: no
# % description: JSON metadata overrides file for operation=derive, or - to read standard input
# %end

# %option
# % key: command
# % type: string
# % required: no
# % multiple: no
# % description: Command line string to store in processing history (for operation=derive or operation=add-history)
# %end

# %option
# % key: format
# % type: string
# % required: no
# % options: json,text,csv,kv
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

# %option
# % key: extended_select
# % type: string
# % required: no
# % multiple: yes
# % answer: all
# % description: Selector for operation=extended: all, branch, or dot path (e.g., acquisition,geometry.sun_zenith_deg)
# %end

# %flag
# % key: q
# % description: Quiet mode for operation=copy — do not add a history entry for the copy operation
# %end

# %rules
# % exclusive: overrides,overrides_file
# %end

import copy
import csv
import json
import os
import sys

import grass.script as gs


def _import_hyper_meta():
    """Import the hyper_meta module from i_hyper_lib."""
    from grass.script.utils import get_lib_path
    import importlib.util
    import os

    path = get_lib_path(modname="i_hyper_lib", libname="hyper_meta")
    if not path:
        gs.fatal("Library path for hyper_meta not found.")
    module_file = os.path.join(path, "hyper_meta.py")
    if not os.path.exists(module_file):
        gs.fatal(f"Module file not found: {module_file}")
    if path not in sys.path:
        sys.path.append(path)

    spec = importlib.util.spec_from_file_location("hyper_meta", module_file)
    if not spec or not spec.loader:
        gs.fatal(f"Failed to load module spec from {module_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["hyper_meta"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop("hyper_meta", None)
        raise
    return module


def _load_raw_metadata(hyper_metadata_class, map_name):
    """Load raw JSON metadata for one map."""
    return hyper_metadata_class.load_raw(map_name)


def _get_raster_depth(map_name):
    """Return the actual 3D raster depth for a map."""
    try:
        info = gs.parse_command("r3.info", map=map_name, flags="g")
        return int(float(info["depths"]))
    except Exception as error:
        gs.fatal(f"Failed to read 3D raster depth for '{map_name}': {error}")


def _get_copy_command():
    """Return the executed command line for history recording."""
    return os.environ.get("CMDLINE") or " ".join(sys.argv)


def _discover_dataset_index(hyper_metadata_class):
    """Build dataset_id -> metadata record index by scanning current LOCATION mapsets."""
    return hyper_metadata_class.discover_dataset_index()


def _resolve_history_names(history_entries, dataset_index, hyper_metadata_class):
    return hyper_metadata_class.resolve_history_names(history_entries, dataset_index)


def _collect_aggregated_history(root_data, dataset_index, hyper_metadata_class):
    return hyper_metadata_class.collect_aggregated_history(root_data, dataset_index)


def _summary_from_data(data, hyper_metadata_class):
    return hyper_metadata_class.summarize_data(data)


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


def _kv_escape(value):
    """Escape scalar strings for the line-oriented key/value format."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("=", "\\=")
    )


def _print_key_value(data):
    """Print nested metadata as dotted paths for machine consumers."""

    def emit(path, value):
        if isinstance(value, dict):
            for key, item in value.items():
                emit(f"{path}.{key}" if path else key, item)
            return
        if isinstance(value, list):
            if all(
                isinstance(item, (int, float)) and not isinstance(item, bool)
                for item in value
            ):
                print(f"{path}=" + ",".join(str(item) for item in value))
            else:
                print(f"{path}={_kv_escape(json.dumps(value, separators=(',', ':')))}")
            return
        if value is None:
            print(f"{path}=")
            return
        if isinstance(value, bool):
            print(f"{path}={'true' if value else 'false'}")
            return
        print(f"{path}={_kv_escape(value)}")

    emit("", data)


def _unwrap_form_values(value):
    """Materialize schema form-value dictionaries for metadata consumers."""
    if isinstance(value, list):
        return [_unwrap_form_values(item) for item in value]
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    if "value" in value and "form" in value:
        return _unwrap_form_values(value["value"])
    return {key: _unwrap_form_values(item) for key, item in value.items()}


def _resolved_metadata_view(meta):
    """Return a fully materialized, read-only view of HyperMetadata."""
    bands = {}
    if meta.n_bands_source is not None:
        bands["count"] = int(meta.n_bands_source)
    if meta.n_bands_valid is not None:
        bands["count_valid"] = int(meta.n_bands_valid)
    if meta.wavelengths is not None:
        bands["wavelength"] = copy.deepcopy(meta.wavelengths)
    if meta.fwhm is not None:
        bands["fwhm"] = copy.deepcopy(meta.fwhm)
    if meta.validity is not None:
        bands["validity"] = [bool(item) for item in meta.validity]
    if meta.component_labels is not None:
        bands["labels"] = copy.deepcopy(meta.component_labels)

    return {
        "schema_version": meta.schema_version,
        "dataset_id": meta.dataset_id,
        "derived": bool(meta.derived),
        "data_type": meta.data_type,
        "sensor": meta.sensor,
        "wavelength_units": meta.wavelength_units,
        "radiometric_quantity": meta.radiometric_quantity,
        "radiometric_units": meta.radiometric_units,
        "acquisition_datetime": meta.acquisition_datetime,
        "region": copy.deepcopy(meta.region),
        "bands": bands,
        "extended_metadata": _unwrap_form_values(meta.extended_metadata),
        "dimensionality_reduction": copy.deepcopy(meta.dimensionality_reduction),
    }


def _parse_extended_selectors(selector_text):
    """Parse extended metadata selectors from option string."""
    if not selector_text:
        return ["all"]

    selectors = []
    for token in str(selector_text).split(","):
        item = token.strip()
        if not item:
            continue
        if item == "extended_metadata":
            selectors.append("all")
        elif item.startswith("extended_metadata."):
            selectors.append(item[len("extended_metadata.") :])
        else:
            selectors.append(item)

    if not selectors:
        return ["all"]
    if "all" in selectors:
        return ["all"]

    # Deduplicate while preserving order
    seen = set()
    out = []
    for item in selectors:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _get_nested_value(data, selector):
    """Get nested dict value by dot path; return (found, value)."""
    current = data
    for part in selector.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _set_nested_value(data, selector, value):
    """Set nested dict value by dot path."""
    parts = selector.split(".")
    current = data
    for part in parts[:-1]:
        next_val = current.get(part)
        if not isinstance(next_val, dict):
            next_val = {}
            current[part] = next_val
        current = next_val
    current[parts[-1]] = value


def _select_extended_metadata(raw_data, selector_text):
    """
    Return selected extended metadata.

    Selector supports:
    - all
    - branch name (e.g. acquisition)
    - dot path (e.g. geometry.sun_zenith_deg)
    - multiple selectors (comma-separated)
    """
    ext = raw_data.get("extended_metadata", {})
    if not isinstance(ext, dict):
        return {}

    selectors = _parse_extended_selectors(selector_text)
    if selectors == ["all"]:
        return copy.deepcopy(ext)

    selected = {}
    for selector in selectors:
        found, value = _get_nested_value(ext, selector)
        if not found:
            gs.warning(f"extended_select item not found: {selector}")
            continue
        _set_nested_value(selected, selector, copy.deepcopy(value))
    return selected


def _build_band_rows(data, wavelength_range=None, hyper_metadata_class=None):
    try:
        return hyper_metadata_class.build_band_rows(data, wavelength_range)
    except ValueError:
        gs.fatal(f"Invalid wavelength range: {wavelength_range}")


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
        wl = row["wavelength"]
        wl_str = f"{wl:.2f}" if wl is not None else "-"
        fwhm_str = f"{row['fwhm']:.2f}" if row["fwhm"] is not None else "-"
        validity = row["validity"]
        if validity is True:
            status = "VALID"
        elif validity is False:
            status = "INVALID"
        else:
            status = "UNKNOWN"
        print(f"{row['index']:>5} {wl_str:>12} {fwhm_str:>10} {status:>10}")
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


def _validate_metadata(
    meta,
    data,
    map_name,
    dataset_index,
    hyper_metadata_class,
    duplicate_dataset_ids=None,
):
    return hyper_metadata_class.validate_strict(
        meta=meta,
        raw_data=data,
        map_name=map_name,
        dataset_index=dataset_index,
        duplicate_dataset_ids=duplicate_dataset_ids,
    )


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


def _copy_metadata_from_other_cube(
    hyper_metadata_class,
    source_map,
    target_map,
    *,
    overwrite=False,
    record_history=True,
):
    try:
        source_meta = hyper_metadata_class.load(source_map)
        source_raw = _load_raw_metadata(hyper_metadata_class, source_map)
    except Exception as error:
        gs.fatal(f"Failed to load metadata for copy: {error}")

    target_has_metadata = hyper_metadata_class.exists(target_map)
    if target_has_metadata and not overwrite:
        gs.fatal(
            f"Metadata already exists for target map '{target_map}'. Use --overwrite to replace it"
        )

    target_raw = {}
    if target_has_metadata:
        try:
            target_raw = _load_raw_metadata(hyper_metadata_class, target_map)
        except Exception as error:
            gs.fatal(f"Failed to load existing target metadata for copy: {error}")

    source_depth = _get_raster_depth(source_map)
    target_depth = _get_raster_depth(target_map)
    if target_depth != source_depth:
        gs.fatal(
            f"Cannot copy metadata from '{source_map}' to '{target_map}': "
            f"target raster depth is {target_depth}, but source raster depth is {source_depth}"
        )

    source_history = hyper_metadata_class._normalize_history_entries(
        source_raw.get("processing_history", [])
    )
    target_history = hyper_metadata_class._normalize_history_entries(
        target_raw.get("processing_history", [])
    )
    target_last_step = copy.deepcopy(target_history[-1]) if target_history else None

    source_dataset_id = source_raw.get("dataset_id")
    if target_last_step and source_dataset_id:
        input_ids = {
            item.get("id")
            for item in hyper_metadata_class._normalize_io_refs(
                target_last_step.get("inputs") or []
            )
            if item.get("id")
        }
        if input_ids and source_dataset_id not in input_ids:
            gs.warning(
                "The current map's last processing step does not reference the selected source_map dataset_id. "
                "Copied metadata will keep that last local step unchanged."
            )

    source_meta.dataset_id = hyper_metadata_class.new_dataset_id()
    if record_history:
        source_meta.processing_history = source_history
        if target_last_step:
            source_meta.processing_history.append(target_last_step)
        elif target_has_metadata:
            gs.warning(
                "The current map has no local processing history. Metadata was copied without appending a local last step."
            )
    else:
        source_meta.processing_history = []

    if record_history:
        source_meta.add_history_entry(
            command=_get_copy_command(),
            inputs=[
                {
                    "id": source_raw.get("dataset_id"),
                    "map_name": source_map,
                }
            ],
            outputs=[
                {
                    "map_name": target_map,
                    "id": source_meta.dataset_id,
                }
            ],
        )

    try:
        source_meta.save(target_map, save_region=True)
    except Exception as error:
        gs.fatal(f"Failed to save copied metadata: {error}")

    gs.message(
        f"Copied metadata from '{source_map}' to '{target_map}'"
        + (
            " and appended the current map's last local processing step."
            if target_last_step
            else "."
        )
    )


def _merge_overrides(
    hyper_metadata_class,
    target_map,
    *,
    overrides_json=None,
):
    """Apply top-level metadata overrides and merge extended_metadata.

    Loads metadata from *target_map*, applies top-level keys
    (e.g. ``radiometric_quantity``) and deep-merges ``extended_metadata``
    from the ``overrides_json``, then saves the result in-place.
    """
    try:
        metadata = hyper_metadata_class.load(target_map)
    except Exception as error:
        gs.fatal(f"Failed to load metadata for merge-overrides: {error}")

    overrides = {}
    if overrides_json:
        try:
            overrides = json.loads(overrides_json)
        except json.JSONDecodeError as error:
            gs.fatal(f"Invalid overrides JSON: {error}")
    if not isinstance(overrides, dict):
        overrides = {}

    for key in (
        "radiometric_quantity",
        "radiometric_units",
        "data_type",
        "sensor",
        "wavelength_units",
        "region",
    ):
        if key in overrides and overrides[key] is not None:
            setattr(metadata, key, overrides[key])

    bands = overrides.get("bands")
    if isinstance(bands, dict):
        band_fields = {
            "count": "n_bands_source",
            "count_valid": "n_bands_valid",
            "wavelength": "wavelengths",
            "fwhm": "fwhm",
            "validity": "validity",
            "labels": "component_labels",
        }
        for key, attribute in band_fields.items():
            if key in bands and bands[key] is not None:
                setattr(metadata, attribute, copy.deepcopy(bands[key]))
        if "validity" in bands and "count_valid" not in bands:
            metadata.n_bands_valid = sum(bool(value) for value in metadata.validity)

    if "extended_metadata" in overrides:
        metadata.merge_extended_metadata(overrides["extended_metadata"])

    try:
        metadata.save(target_map, save_region=True)
    except Exception as error:
        gs.fatal(f"Failed to save merged metadata: {error}")

    gs.message(f"Merged overrides into metadata for '{target_map}'")


def _load_overrides(overrides_json=None, overrides_file=None):
    """Load an optional metadata override object from text, a file, or stdin."""
    if overrides_file:
        try:
            if overrides_file == "-":
                overrides_json = sys.stdin.read()
            else:
                with open(overrides_file, "r") as stream:
                    overrides_json = stream.read()
        except OSError as error:
            gs.fatal(f"Failed to read overrides file '{overrides_file}': {error}")

    if not overrides_json:
        return {}
    try:
        overrides = json.loads(overrides_json)
    except json.JSONDecodeError as error:
        gs.fatal(f"Invalid overrides JSON: {error}")
    if not isinstance(overrides, dict):
        gs.fatal("Metadata overrides must be a JSON object")
    return overrides


def _apply_derive_overrides(metadata, overrides):
    """Apply the generic metadata keys accepted by merge-overrides."""
    for key in (
        "radiometric_quantity",
        "radiometric_units",
        "data_type",
        "sensor",
        "wavelength_units",
        "region",
    ):
        if key in overrides and overrides[key] is not None:
            setattr(metadata, key, overrides[key])

    bands = overrides.get("bands")
    if isinstance(bands, dict):
        band_fields = {
            "count": "n_bands_source",
            "count_valid": "n_bands_valid",
            "wavelength": "wavelengths",
            "fwhm": "fwhm",
            "validity": "validity",
            "labels": "component_labels",
        }
        for key, attribute in band_fields.items():
            if key in bands and bands[key] is not None:
                setattr(metadata, attribute, copy.deepcopy(bands[key]))
        if "validity" in bands and "count_valid" not in bands:
            metadata.n_bands_valid = sum(bool(value) for value in metadata.validity)

    if getattr(metadata, "data_type", None) == "component":
        metadata.wavelengths = None
        metadata.fwhm = None
        metadata.n_components = metadata.n_bands_source
        if not isinstance(bands, dict) or "validity" not in bands:
            metadata.validity = [True] * int(metadata.n_bands_source or 0)
            metadata.n_bands_valid = metadata.n_bands_source

    if "extended_metadata" in overrides:
        metadata.merge_extended_metadata(overrides["extended_metadata"])
    if "dimensionality_reduction" in overrides:
        metadata.dimensionality_reduction = copy.deepcopy(
            overrides["dimensionality_reduction"]
        )


def _validate_derive_bands(metadata, target_map, target_depth):
    """Require all emitted band metadata to match the target cube depth."""
    count = metadata.n_bands_source
    if isinstance(count, bool) or not isinstance(count, int) or count != target_depth:
        gs.fatal(
            f"Cannot derive metadata for '{target_map}': bands.count must equal "
            f"target raster depth {target_depth}, got {count!r}"
        )

    for name, values in (
        ("wavelength", metadata.wavelengths),
        ("fwhm", metadata.fwhm),
        ("validity", metadata.validity),
        ("labels", metadata.component_labels),
    ):
        if values is not None and (
            not isinstance(values, list) or len(values) != target_depth
        ):
            length = len(values) if isinstance(values, list) else "non-list"
            gs.fatal(
                f"Cannot derive metadata for '{target_map}': bands.{name} "
                f"length must equal target raster depth {target_depth}, got {length}"
            )

    count_valid = metadata.n_bands_valid
    if count_valid is not None:
        if (
            isinstance(count_valid, bool)
            or not isinstance(count_valid, int)
            or count_valid < 0
            or count_valid > target_depth
        ):
            gs.fatal(
                f"Cannot derive metadata for '{target_map}': bands.count_valid "
                f"must be an integer from 0 to {target_depth}"
            )
        if metadata.validity is not None and count_valid != sum(
            bool(value) for value in metadata.validity
        ):
            gs.fatal(
                f"Cannot derive metadata for '{target_map}': bands.count_valid "
                "does not match bands.validity"
            )


def _derive_metadata(
    hyper_metadata_class,
    source_map,
    target_map,
    *,
    command,
    overwrite=False,
    overrides=None,
):
    """Create one derived metadata record from a source dataset."""
    if hyper_metadata_class.exists(target_map) and not overwrite:
        gs.fatal(
            f"Metadata already exists for target map '{target_map}'. Use --overwrite to replace it"
        )

    try:
        source_raw = hyper_metadata_class.load_raw(source_map)
        metadata = hyper_metadata_class.load(source_map)
    except Exception as error:
        gs.fatal(f"Failed to load metadata for derive: {error}")

    source_dataset_id = source_raw.get("dataset_id")
    if not isinstance(source_dataset_id, str) or not source_dataset_id:
        gs.fatal(
            f"Cannot derive metadata from '{source_map}': source metadata has no "
            "persisted dataset_id"
        )
    source_snapshots = copy.deepcopy(
        getattr(metadata, "input_datasets_metadata", {}) or {}
    )
    source_snapshots[source_dataset_id] = copy.deepcopy(source_raw)
    metadata.input_datasets_metadata = source_snapshots
    source_depth = _get_raster_depth(source_map)
    target_depth = _get_raster_depth(target_map)
    bands = (overrides or {}).get("bands", {})
    expected_depth = (
        bands.get("count", source_depth) if isinstance(bands, dict) else source_depth
    )
    if target_depth != expected_depth:
        gs.fatal(
            f"Cannot derive metadata for '{target_map}': target raster depth is "
            f"{target_depth}, expected {expected_depth}"
        )

    metadata.dataset_id = hyper_metadata_class.new_dataset_id()
    metadata.derived = True
    metadata.processing_history = []
    metadata.dimensionality_reduction = None
    _apply_derive_overrides(metadata, overrides or {})
    _validate_derive_bands(metadata, target_map, target_depth)
    metadata.add_history_entry(
        command=command,
        inputs=[{"id": source_dataset_id, "map_name": source_map}],
        outputs=[{"id": metadata.dataset_id, "map_name": target_map}],
    )

    try:
        metadata.save(target_map, save_region="region" not in (overrides or {}))
    except Exception as error:
        gs.fatal(f"Failed to save derived metadata: {error}")

    gs.message(f"Derived metadata for '{target_map}' from '{source_map}'")


def _add_history_entry(
    hyper_metadata_class,
    target_map,
    *,
    source_map=None,
    command=None,
):
    """Append a processing history entry to an existing map.

    Loads metadata from *target_map*, adds an entry recording
    *command* with *source_map* as input, and saves in-place.
    """
    try:
        target_meta = hyper_metadata_class.load(target_map)
    except Exception as error:
        gs.fatal(f"Failed to load metadata for add-history: {error}")

    source_id = None
    if source_map:
        try:
            source_meta = hyper_metadata_class.load(source_map)
            source_id = source_meta.dataset_id
        except Exception:
            source_id = None

    inputs = []
    if source_id and source_map:
        inputs.append({"id": source_id, "map_name": source_map})

    cmd = command or os.environ.get("CMDLINE") or "unknown"
    target_meta.add_history_entry(
        command=cmd,
        inputs=inputs,
        outputs=[{"id": target_meta.dataset_id, "map_name": target_map}],
    )

    try:
        target_meta.save(target_map, save_region=True)
    except Exception as error:
        gs.fatal(f"Failed to save history entry: {error}")

    gs.message(f"Added history entry to '{target_map}'")


def main():
    options, flags = gs.parser()

    map_name = options["map"]
    operation = options["operation"]
    output_format = options["format"]
    wavelength_range = options.get("wavelength_range")
    resolve_names = options.get("resolve_names", "no") == "yes"
    extended_select = options.get("extended_select")
    source_map = options.get("source_map")
    overrides_json = options.get("overrides")
    overrides_file = options.get("overrides_file")
    command = options.get("command")

    if output_format == "kv" and operation != "resolved":
        gs.fatal("format=kv is supported only for operation=resolved")

    # Import metadata API
    hyper_meta = _import_hyper_meta()
    HyperMetadata = hyper_meta.HyperMetadata

    # Check map exists and normalize to full map name
    found = gs.find_file(map_name, element="grid3")
    if not found["fullname"]:
        gs.fatal(f"3D raster map '{map_name}' not found")
    full_map_name = found["fullname"]

    if operation == "copy":
        if not source_map:
            gs.fatal("Option <source_map> is required for operation=copy")
        source_found = gs.find_file(source_map, element="grid3")
        if not source_found["fullname"]:
            gs.fatal(f"Source 3D raster map '{source_map}' not found")
        if source_found["fullname"] == full_map_name:
            gs.fatal("source_map must be different from map")
        _copy_metadata_from_other_cube(
            HyperMetadata,
            source_found["fullname"],
            full_map_name,
            overwrite=gs.overwrite(),
            record_history=not flags.get("q", False),
        )
        return 0

    if operation == "derive":
        if not source_map:
            gs.fatal("Option <source_map> is required for operation=derive")
        if not command:
            gs.fatal("Option <command> is required for operation=derive")
        source_found = gs.find_file(source_map, element="grid3")
        if not source_found["fullname"]:
            gs.fatal(f"Source 3D raster map '{source_map}' not found")
        if source_found["fullname"] == full_map_name:
            gs.fatal("source_map must be different from map")
        _derive_metadata(
            HyperMetadata,
            source_found["fullname"],
            full_map_name,
            command=command,
            overwrite=gs.overwrite(),
            overrides=_load_overrides(overrides_json, overrides_file),
        )
        return 0

    if operation == "merge-overrides":
        _merge_overrides(
            HyperMetadata,
            full_map_name,
            overrides_json=overrides_json,
        )
        return 0

    if operation == "add-history":
        if not source_map:
            gs.fatal("Option <source_map> is required for operation=add-history")
        source_found = gs.find_file(source_map, element="grid3")
        if not source_found["fullname"]:
            gs.fatal(f"Source 3D raster map '{source_map}' not found")
        _add_history_entry(
            HyperMetadata,
            full_map_name,
            source_map=source_found["fullname"],
            command=command,
        )
        return 0

    # Load both object and raw JSON
    try:
        meta = HyperMetadata.load(full_map_name)
        raw = _load_raw_metadata(HyperMetadata, full_map_name)
    except Exception as e:
        gs.fatal(f"Failed to load metadata: {e}")

    # Build dataset index where needed
    need_index = operation in ("full", "history", "validate") or resolve_names
    if need_index:
        dataset_index, duplicate_dataset_ids = _discover_dataset_index(HyperMetadata)
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
        summary = _summary_from_data(_resolved_metadata_view(meta), HyperMetadata)
        summary["processing_steps_local"] = len(raw.get("processing_history", []) or [])
        _print_summary(summary, output_format)
        return 0

    if operation == "full":
        full_data = copy.deepcopy(raw)
        if resolve_names:
            full_data["processing_history"] = _resolve_history_names(
                full_data.get("processing_history", []), dataset_index, HyperMetadata
            )
        _print_full(full_data, output_format)
        return 0

    if operation == "resolved":
        resolved = _resolved_metadata_view(meta)
        if output_format == "kv":
            _print_key_value(resolved)
        else:
            _print_full(resolved, output_format)
        return 0

    if operation == "extended":
        # Use resolved metadata from HyperMetadata.load(), so selectors work
        # for derived datasets that inherit extended_metadata from lineage.
        selected = _select_extended_metadata(
            {"extended_metadata": meta.extended_metadata or {}},
            extended_select,
        )
        _print_full(selected, output_format)
        return 0

    if operation == "bands":
        rows = _build_band_rows(
            _resolved_metadata_view(meta), wavelength_range, HyperMetadata
        )
        _print_bands(rows, output_format)
        return 0

    if operation == "history":
        entries = _collect_aggregated_history(raw, dataset_index, HyperMetadata)
        if resolve_names:
            entries = _resolve_history_names(entries, dataset_index, HyperMetadata)
        _print_history(entries, output_format)
        return 0

    if operation == "validate":
        issues = _validate_metadata(
            meta,
            raw,
            full_map_name,
            dataset_index,
            HyperMetadata,
            duplicate_dataset_ids=duplicate_dataset_ids,
        )
        return _print_validate(issues, output_format)

    gs.fatal(f"Unsupported operation: {operation}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
