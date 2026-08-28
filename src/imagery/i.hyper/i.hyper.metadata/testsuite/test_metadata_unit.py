#!/usr/bin/env python3

"""Focused unit tests for generic hyperspectral metadata operations."""

import importlib.util
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
HYPER_META_PATH = HERE.parent.parent / "i_hyper_lib" / "hyper_meta.py"
METADATA_MODULE_PATH = HERE.parent / "i.hyper.metadata.py"


def _install_grass_stub():
    try:
        import grass.script as gs  # noqa: F401
    except ImportError:
        grass = types.ModuleType("grass")
        script = types.ModuleType("grass.script")
        script.message = lambda *args, **kwargs: None
        script.warning = lambda *args, **kwargs: None
        script.fatal = lambda message: (_ for _ in ()).throw(RuntimeError(message))
        grass.script = script
        sys.modules.setdefault("grass", grass)
        sys.modules.setdefault("grass.script", script)


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_install_grass_stub()
hyper_meta = _load_module("hyper_meta_unit_test", HYPER_META_PATH)
metadata_module = _load_module("i_hyper_metadata_unit_test", METADATA_MODULE_PATH)


class HyperMetadataSaveTest(unittest.TestCase):
    def _metadata_path(self, directory):
        map_directory = Path(directory) / "grid3" / "cube"
        map_directory.mkdir(parents=True)
        return map_directory / "hyper.json"

    def test_save_is_atomic_when_serialization_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._metadata_path(directory)
            original = '{"existing": true}'
            path.write_text(original)
            metadata = hyper_meta.HyperMetadata.for_spectral_data([450.0])

            def interrupted_dump(data, stream, indent):
                stream.write('{"partial":')
                raise OSError("interrupted")

            with patch.object(metadata, "_get_metadata_path", return_value=path):
                with patch.object(
                    hyper_meta.json, "dump", side_effect=interrupted_dump
                ):
                    with self.assertRaises(OSError):
                        metadata.save("cube")

            self.assertEqual(path.read_text(), original)
            self.assertEqual(list(path.parent.glob(".hyper.json.*.tmp")), [])

    def test_save_preserves_json_format_order_and_escaping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._metadata_path(directory)
            long_value = 'quote=" slash=\\ newline=\n cafe=caf\u00e9 ' + "x" * 10000
            metadata = hyper_meta.HyperMetadata.for_spectral_data(
                [450.0], sensor="sensor"
            )
            metadata.extended_metadata = {"text": long_value}

            with patch.object(metadata, "_get_metadata_path", return_value=path):
                metadata.save("cube")

            text = path.read_text()
            self.assertTrue(text.startswith('{\n  "schema_version": "1.0",'))
            self.assertIn("caf\\u00e9", text)
            self.assertNotIn("caf\u00e9", text)
            self.assertFalse(text.endswith("\n"))
            self.assertEqual(json.loads(text)["extended_metadata"]["text"], long_value)

    def test_atomic_save_preserves_existing_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._metadata_path(directory)
            path.write_text('{"existing": true}')
            path.chmod(0o600)
            metadata = hyper_meta.HyperMetadata.for_spectral_data([450.0])

            with patch.object(metadata, "_get_metadata_path", return_value=path):
                metadata.save("cube")

            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_public_save_and_load_signatures_are_compatible(self):
        self.assertEqual(
            str(inspect.signature(hyper_meta.HyperMetadata.load)),
            "(map_name: 'str', mapset: 'str | None' = None) -> 'HyperMetadata'",
        )
        self.assertEqual(
            str(inspect.signature(hyper_meta.HyperMetadata.save)),
            "(self, map_name: 'str', mapset: 'str | None' = None, *, save_region: 'bool' = False) -> 'None'",
        )

    def test_save_preserves_embedded_ancestor_snapshots(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._metadata_path(directory)
            metadata = hyper_meta.HyperMetadata.for_spectral_data([450.0])
            metadata.dataset_id = "derived-id"
            metadata.derived = True
            metadata.processing_history = [
                {
                    "command": "derive",
                    "inputs": [{"id": "source-id"}],
                    "outputs": [{"id": "derived-id"}],
                }
            ]
            ancestor_data = {
                "dataset_id": "ancestor-id",
                "processing_history": [],
                "bands": {"count": 1, "wavelength": [450.0]},
            }
            source_data = {
                "dataset_id": "source-id",
                "processing_history": [
                    {
                        "command": "source-step",
                        "inputs": [{"id": "ancestor-id"}],
                        "outputs": [{"id": "source-id"}],
                    }
                ],
                "input_datasets_metadata": {"ancestor-id": ancestor_data},
                "bands": {"count": 1, "wavelength": [450.0]},
            }
            metadata.input_datasets_metadata = {"source-id": source_data}
            dataset_index = {
                "source-id": {
                    "data": {
                        "dataset_id": "source-id",
                        "processing_history": [],
                        "sensor": "wrong-duplicate",
                    }
                }
            }

            with patch.object(metadata, "_get_metadata_path", return_value=path):
                with patch.object(
                    metadata,
                    "discover_dataset_index",
                    return_value=(dataset_index, {}),
                ):
                    metadata.save("cube")

            snapshots = json.loads(path.read_text())["input_datasets_metadata"]
            self.assertEqual(set(snapshots), {"source-id", "ancestor-id"})
            self.assertNotIn("input_datasets_metadata", snapshots["source-id"])
            self.assertEqual(snapshots["source-id"]["bands"]["wavelength"], [450.0])

    def test_save_keeps_existing_snapshots_when_discovery_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self._metadata_path(directory)
            metadata = hyper_meta.HyperMetadata.for_spectral_data([450.0])
            metadata.dataset_id = "derived-id"
            metadata.derived = True
            metadata.processing_history = [
                {
                    "command": "derive",
                    "inputs": [{"id": "source-id"}],
                    "outputs": [{"id": "derived-id"}],
                }
            ]
            metadata.input_datasets_metadata = {
                "source-id": {
                    "dataset_id": "source-id",
                    "processing_history": [],
                    "bands": {"count": 1, "wavelength": [450.0]},
                }
            }

            with patch.object(metadata, "_get_metadata_path", return_value=path):
                with patch.object(
                    metadata,
                    "discover_dataset_index",
                    side_effect=OSError("unreadable mapset"),
                ):
                    metadata.save("cube")

            snapshots = json.loads(path.read_text())["input_datasets_metadata"]
            self.assertEqual(set(snapshots), {"source-id"})


class DeriveMetadataTest(unittest.TestCase):
    def test_derive_requires_overwrite_for_existing_metadata(self):
        class FakeHyperMetadata:
            @staticmethod
            def exists(_map_name):
                return True

        with self.assertRaisesRegex(RuntimeError, "--overwrite"):
            metadata_module._derive_metadata(
                FakeHyperMetadata,
                "source@mapset",
                "output@mapset",
                command="generic.module",
            )

    def test_derive_creates_new_id_and_one_local_lineage_entry(self):
        class FakeMetadata:
            dataset_id = "source-id"
            derived = False
            processing_history = [{"command": "old"}]
            extended_metadata = {"existing": {"value": 1}}
            n_bands_valid = 2
            wavelengths = [450.0, 550.0]
            fwhm = [10.0, 10.0]
            validity = [True, True]
            component_labels = None
            save_calls = []

            def merge_extended_metadata(self, payload):
                hyper_meta.HyperMetadata._deep_merge_dict(
                    self.extended_metadata, payload
                )

            def add_history_entry(self, command, inputs, outputs):
                self.processing_history.append(
                    {"command": command, "inputs": inputs, "outputs": outputs}
                )

            def save(self, map_name, *, save_region=False):
                self.save_calls.append((map_name, save_region))

        source = FakeMetadata()

        class FakeHyperMetadata:
            @staticmethod
            def exists(_map_name):
                return False

            @staticmethod
            def load(_map_name):
                return source

            @staticmethod
            def load_raw(_map_name):
                return {"dataset_id": "source-id"}

            @staticmethod
            def new_dataset_id():
                return "derived-id"

        with patch.object(metadata_module, "_get_raster_depth", return_value=2):
            metadata_module._derive_metadata(
                FakeHyperMetadata,
                "source@mapset",
                "output@mapset",
                command='generic.module input="a b" note="' + "z" * 5000 + '"',
                overrides={
                    "radiometric_quantity": "surface_reflectance",
                    "region": {"north": 10},
                    "bands": {"count": 2, "validity": [True, False]},
                    "extended_metadata": {"generic": {"text": "line1\nline2"}},
                },
            )

        self.assertEqual(source.dataset_id, "derived-id")
        self.assertTrue(source.derived)
        self.assertEqual(source.radiometric_quantity, "surface_reflectance")
        self.assertEqual(source.region, {"north": 10})
        self.assertEqual(source.n_bands_source, 2)
        self.assertEqual(source.validity, [True, False])
        self.assertEqual(source.extended_metadata["generic"]["text"], "line1\nline2")
        self.assertEqual(len(source.processing_history), 1)
        entry = source.processing_history[0]
        self.assertEqual(
            entry["inputs"], [{"id": "source-id", "map_name": "source@mapset"}]
        )
        self.assertEqual(
            entry["outputs"], [{"id": "derived-id", "map_name": "output@mapset"}]
        )
        self.assertEqual(source.save_calls, [("output@mapset", False)])

    def test_derive_rejects_source_without_persisted_dataset_id(self):
        class FakeHyperMetadata:
            @staticmethod
            def exists(_map_name):
                return False

            @staticmethod
            def load_raw(_map_name):
                return {"bands": {"count": 2}}

            @staticmethod
            def load(_map_name):
                return object()

        with self.assertRaisesRegex(RuntimeError, "persisted dataset_id"):
            metadata_module._derive_metadata(
                FakeHyperMetadata,
                "source@mapset",
                "output@mapset",
                command="generic.module",
            )

    def test_derive_rejects_band_array_length_mismatch(self):
        class FakeMetadata:
            dataset_id = "source-id"
            n_bands_source = 2
            n_bands_valid = 2
            wavelengths = [450.0, 550.0]
            fwhm = [10.0, 10.0]
            validity = [True, True]
            component_labels = None
            processing_history = []
            dimensionality_reduction = None
            derived = False

        class FakeHyperMetadata:
            @staticmethod
            def exists(_map_name):
                return False

            @staticmethod
            def load_raw(_map_name):
                return {"dataset_id": "source-id"}

            @staticmethod
            def load(_map_name):
                return FakeMetadata()

            @staticmethod
            def new_dataset_id():
                return "derived-id"

        with patch.object(metadata_module, "_get_raster_depth", return_value=2):
            with self.assertRaisesRegex(RuntimeError, "bands.fwhm length"):
                metadata_module._derive_metadata(
                    FakeHyperMetadata,
                    "source@mapset",
                    "output@mapset",
                    command="generic.module",
                    overrides={"bands": {"fwhm": [10.0]}},
                )

    def test_component_derive_clears_inherited_spectral_axes(self):
        metadata = types.SimpleNamespace(
            data_type="spectral",
            wavelengths=[450.0, 550.0],
            fwhm=[10.0, 10.0],
            n_bands_source=2,
            n_components=None,
        )

        metadata_module._apply_derive_overrides(
            metadata,
            {"data_type": "component", "bands": {"count": 2}},
        )

        self.assertEqual(metadata.data_type, "component")
        self.assertIsNone(metadata.wavelengths)
        self.assertIsNone(metadata.fwhm)
        self.assertEqual(metadata.n_components, 2)
        self.assertEqual(metadata.validity, [True, True])
        self.assertEqual(metadata.n_bands_valid, 2)

    def test_overrides_file_stdin_accepts_escaped_and_long_values(self):
        value = 'a="b"\\c\n' + "q" * 10000
        stream = io.StringIO(json.dumps({"extended_metadata": {"text": value}}))
        with patch.object(metadata_module.sys, "stdin", stream):
            overrides = metadata_module._load_overrides(None, "-")
        self.assertEqual(overrides["extended_metadata"]["text"], value)


if __name__ == "__main__":
    unittest.main()
