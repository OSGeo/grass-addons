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
# % options: view,json,validate,bands,history
# % answer: view
# % description: Operation to perform
# % descriptions: view;Print human-readable metadata summary;json;Print raw JSON metadata;validate;Check metadata for issues;bands;List bands with wavelengths;history;Show processing history
# %end

# %option
# % key: format
# % type: string
# % required: no
# % options: text,json,csv
# % answer: text
# % description: Output format for bands listing
# %end

# %option
# % key: wavelength_range
# % type: string
# % required: no
# % description: Filter bands by wavelength range (e.g., 400-700)
# %end

# %flag
# % key: g
# % description: Shell script style output (parseable)
# %end

import sys
import json
import grass.script as gs


def _is_component_metadata(meta):
    return (
        (meta.n_components is not None and meta.n_components > 0)
        or meta.explained_variance_ratio is not None
        or meta.component_labels is not None
    )


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


def view_metadata(meta, shell_style=False):
    """Print human-readable metadata summary."""
    is_components = _is_component_metadata(meta)
    if shell_style:
        # Parseable output
        print(f"schema_version={meta.schema_version}")
        print(f"data_type={'components' if is_components else 'spectral'}")
        if is_components:
            print(f"n_components={meta.n_components or 0}")
        else:
            print(f"sensor={meta.sensor or ''}")
            print(f"n_bands={meta.n_bands or 0}")
            print(f"wavelength_units={meta.wavelength_units}")
            print(f"radiometric_quantity={meta.radiometric_quantity or ''}")
            print(f"radiometric_units={meta.radiometric_units or ''}")
            if meta.wavelengths:
                wl = [w for w in meta.wavelengths if w is not None]
                if wl:
                    print(f"wavelength_min={min(wl):.2f}")
                    print(f"wavelength_max={max(wl):.2f}")
    else:
        # Human readable
        print("=" * 60)
        print("HYPERSPECTRAL METADATA")
        print("=" * 60)
        print(f"Schema version: {meta.schema_version}")
        print()
        
        if is_components:
            print("Type: Dimensionality Reduction Output")
            print(f"Components: {meta.n_components or 'Unknown'}")
            if meta.explained_variance_ratio:
                print("\nExplained variance:")
                cumulative = 0
                for i, var in enumerate(meta.explained_variance_ratio, 1):
                    cumulative += var
                    print(f"  Component {i}: {var*100:.2f}% (cumulative: {cumulative*100:.2f}%)")
        else:
            print("Type: Spectral Data")
            if meta.sensor:
                print(f"Sensor: {meta.sensor}")
            print(f"Bands: {meta.n_bands or 'Unknown'}")
            print(f"Wavelength units: {meta.wavelength_units}")
            
            if meta.radiometric_quantity:
                print(f"Radiometric quantity: {meta.radiometric_quantity}")
            if meta.radiometric_units:
                print(f"Radiometric units: {meta.radiometric_units}")
            
            if meta.wavelengths:
                wl = [w for w in meta.wavelengths if w is not None]
                if wl:
                    print(f"\nWavelength range: {min(wl):.2f} - {max(wl):.2f} {meta.wavelength_units}")
                    
                    # Count bad bands
                    if meta.bad_bands:
                        n_bad = sum(meta.bad_bands)
                        if n_bad > 0:
                            print(f"Bad bands flagged: {n_bad}")
        
        # Processing history
        if meta.processing_history:
            print(f"\nProcessing steps: {len(meta.processing_history)}")
        
        # Custom fields
        if meta.custom:
            print(f"\nCustom fields: {list(meta.custom.keys())}")


def print_json(meta, map_name=None, hyper_meta_class=None):
    """Print raw JSON metadata."""
    if hyper_meta_class is not None and map_name:
        try:
            json_path = hyper_meta_class._get_metadata_path(map_name)
            if json_path.exists():
                with open(json_path, "r") as f:
                    print(json.dumps(json.load(f), indent=2))
                return
        except Exception:
            pass

    # Fallback for in-memory metadata object representation
    data = {
        "schema_version": meta.schema_version,
        "dataset": {
            "sensor": meta.sensor,
            "wavelength_units": meta.wavelength_units,
            "radiometric_quantity": meta.radiometric_quantity,
            "radiometric_units": meta.radiometric_units,
            "region": meta.region,
        },
        "bands": {
            "count": meta.n_bands,
            "wavelength": meta.wavelengths,
            "fwhm": meta.fwhm,
            "bad_band": meta.bad_bands,
            "gain": meta.gain,
            "offset": meta.offset,
        },
        "components": {
            "count": meta.n_components,
            "explained_variance_ratio": meta.explained_variance_ratio,
            "labels": meta.component_labels,
        },
        "processing_history": meta.processing_history,
        "custom": meta.custom,
    }
    print(json.dumps(data, indent=2))


def list_bands(meta, output_format="text", wavelength_range=None):
    """List bands with their wavelengths."""
    if meta.wavelengths is None:
        gs.warning("No wavelength information available")
        return
    
    # Parse wavelength range filter
    wl_min, wl_max = None, None
    if wavelength_range:
        try:
            parts = wavelength_range.split("-")
            wl_min = float(parts[0]) if parts[0] else None
            wl_max = float(parts[1]) if len(parts) > 1 and parts[1] else None
        except ValueError:
            gs.fatal(f"Invalid wavelength range: {wavelength_range}")
    
    # Build band list
    bands = []
    for i, wl in enumerate(meta.wavelengths):
        if wl is None:
            continue
        if wl_min is not None and wl < wl_min:
            continue
        if wl_max is not None and wl > wl_max:
            continue
        
        fwhm = meta.fwhm[i] if meta.fwhm and i < len(meta.fwhm) else None
        bad = meta.bad_bands[i] if meta.bad_bands and i < len(meta.bad_bands) else False
        bands.append({
            "index": i + 1,  # 1-based for display
            "wavelength": wl,
            "fwhm": fwhm,
            "bad": bad,
        })
    
    if output_format == "json":
        print(json.dumps(bands, indent=2))
    elif output_format == "csv":
        print("index,wavelength,fwhm,bad")
        for b in bands:
            fwhm_str = f"{b['fwhm']:.4f}" if b['fwhm'] is not None else ""
            print(f"{b['index']},{b['wavelength']:.4f},{fwhm_str},{b['bad']}")
    else:
        # Text table
        print(f"{'Band':>5} {'Wavelength':>12} {'FWHM':>10} {'Status':>8}")
        print("-" * 40)
        for b in bands:
            fwhm_str = f"{b['fwhm']:.2f}" if b['fwhm'] is not None else "-"
            status = "BAD" if b['bad'] else "OK"
            print(f"{b['index']:>5} {b['wavelength']:>12.2f} {fwhm_str:>10} {status:>8}")
        print(f"\nTotal: {len(bands)} bands")


def show_history(meta):
    """Show processing history."""
    if not meta.processing_history:
        print("No processing history recorded.")
        return
    
    print("PROCESSING HISTORY")
    print("=" * 60)
    for i, step in enumerate(meta.processing_history, 1):
        print(f"\nStep {i}:")
        print(f"  Operation: {step.get('operation', 'Unknown')}")
        if step.get('module'):
            print(f"  Module: {step['module']}")
        if step.get('timestamp'):
            print(f"  Timestamp: {step['timestamp']}")
        if step.get('params'):
            print(f"  Parameters:")
            for k, v in step['params'].items():
                print(f"    {k}: {v}")


def validate_metadata(meta):
    """Check metadata for issues."""
    issues = meta.validate()
    
    if not issues:
        print("✓ Metadata validation passed")
        return 0
    
    print("Validation issues found:")
    for issue in issues:
        print(f"  ✗ {issue}")
    return 1


def main():
    options, flags = gs.parser()
    
    map_name = options["map"]
    operation = options["operation"]
    output_format = options["format"]
    wavelength_range = options.get("wavelength_range")
    shell_style = flags.get("g", False)
    
    # Import the metadata module
    hyper_meta = _import_hyper_meta()
    HyperMetadata = hyper_meta.HyperMetadata
    
    # Check map exists
    if not gs.find_file(map_name, element="grid3")["fullname"]:
        gs.fatal(f"3D raster map '{map_name}' not found")
    
    # Load metadata
    try:
        meta = HyperMetadata.load(map_name)
    except Exception as e:
        gs.fatal(f"Failed to load metadata: {e}")
    
    # Perform operation
    if operation == "view":
        view_metadata(meta, shell_style)
    elif operation == "json":
        print_json(meta, map_name=map_name, hyper_meta_class=HyperMetadata)
    elif operation == "bands":
        list_bands(meta, output_format, wavelength_range)
    elif operation == "history":
        show_history(meta)
    elif operation == "validate":
        return validate_metadata(meta)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
