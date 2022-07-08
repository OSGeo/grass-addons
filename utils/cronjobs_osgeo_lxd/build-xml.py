#!/usr/bin/env python

"""Creates the addons file module.xml required by the module g.extension
@Author: Martin Landa
"""

import os
import sys
import glob
import tempfile
import argparse
from datetime import datetime

import grass.script.task as gtask


def get_list(addons):
    mlist = [
        d
        for d in os.listdir(os.path.join(addons))
        if os.path.isdir(os.path.join(addons, d))
    ]
    if "logs" in mlist:
        mlist.remove("logs")
    mlist.sort()
    return mlist


class BuildXML:
    def __init__(self, build_path):
        self.build_path = build_path

    def run(self):
        with open(os.path.join(self.build_path, "modules.xml"), "w") as fd:
            self._header(fd)
            self._parse_modules(fd, get_list(self.build_path))
            self._footer(fd)

    def _parse_modules(self, fd, mlist):
        indent = 4
        blacklist = ["v.feature.algebra", "m.eigensystem"]
        for m in mlist:
            if m in blacklist:
                continue  # skip blacklisted modules
            print(f"Parsing <{m}>...", end="")
            desc, keyw = self._get_module_metadata(m)
            fd.write(f"{' ' * indent}<task name=\"{m}\">\n")
            indent += 4
            fd.write(f"{' ' * indent}<description>{desc}</description>\n")
            fd.write(f"{' ' * indent}<keywords>{','.join(keyw)}</keywords>\n")
            fd.write(f"{' ' * indent}<binary>\n")
            indent += 4
            for f in self._get_module_files(m):
                fd.write(f"{' ' * indent}<file>{f}</file>\n")
            indent -= 4
            fd.write(f"{' ' * indent}</binary>\n")
            indent -= 4
            fd.write(f"{' ' * indent}</task>\n")
            if desc:
                print(" SUCCESS")
            else:
                print(" FAILED")

    @staticmethod
    def parse_gui_modules(fd, mlist):
        indent = 4
        for m in mlist:
            print("Parsing <{}>...".format(m))
            fd.write('%s<task name="%s">\n' % (" " * indent, m))
            fd.write("%s</task>\n" % (" " * indent))

    def _scandirs(self, path):
        flist = list()
        for f in glob.glob(os.path.join(path, "*")):
            if os.path.isdir(f):
                flist += self._scandirs(f)
            else:
                flist.append(f)
        return flist

    def _get_module_files(self, name):
        cur_dir = os.getcwd()
        os.chdir(os.path.join(self.build_path, name))
        files = self._scandirs("*")
        os.chdir(cur_dir)  # prevent gtask.parse_interface() return None
        return files

    def _get_module_metadata(self, name):
        path = os.environ["PATH"]
        os.environ["PATH"] += (
            os.pathsep
            + os.path.join(self.build_path, name, "bin")
            + os.pathsep
            + os.path.join(self.build_path, name, "scripts")
        )
        try:
            task = gtask.parse_interface(name)
        except:
            task = None
        os.environ["PATH"] = path
        if not task:
            return "", ""

        return task.get_description(full=True), task.get_keywords()

    @staticmethod
    def _header(fd):
        import grass.script.core as grass

        fd.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fd.write('<!DOCTYPE task SYSTEM "grass-addons.dtd">\n')  # TODO
        vInfo = grass.parse_command("g.version", flags="g")
        fd.write(
            f"<addons version=\"{vInfo['version'].split('.')[0]}\""
            f" revision=\"{vInfo['revision']}\""
            f' date="{datetime.now()}">\n'
        )

    @staticmethod
    def _footer(fd):
        fd.write("</addons>\n")


def main(build_path):
    builder = BuildXML(build_path)
    builder.run()

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", help="Path to GRASS Addons build", required=True)
    args = parser.parse_args()

    sys.exit(main(args.build))
