import functools
import py
import pytest
from ruamel.yaml import YAML

from .runner import estimap_test_runner


yaml=YAML(typ="safe", pure=True)


def pytest_collect_file(parent, path):
    if path.ext in (".yml", ".yaml") and path.basename.startswith("test"):
        return YamlFile(path, parent)


class YamlFile(pytest.File):

    def collect(self):
        test_cases = yaml.load(self.fspath.open())
        for case in test_cases:
            module = py.path.local(str(self.fspath).replace(".yml", ".py"))
            yield pytest.Function(
                name=case['mapset'],
                # parent=pytest.Module(fspath=os.path.abspath(__file__), parent=self),
                parent=pytest.Module(fspath=module, parent=self),
                callobj=functools.partial(estimap_test_runner, case)
            )
