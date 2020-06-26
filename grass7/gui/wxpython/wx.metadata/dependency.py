#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@module  dependency.py
@brief   Check wx.metadata py lib dependencies

(C) 2020 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

import importlib

URL = 'https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support'
MODULES = {
    'owslib': {
        'check_version': True,
        'package': 'owslib.iso',
        'method': 'MD_Metadata',
        'version': '>=0.9',
    },
    'pycsw': {
        'check_version': True,
        'package': 'pycsw.core',
        'submodule': 'admin',
        'version': '>=2.0',
    },
    'sqlalchemy': {
        'check_version': False,
    },
    'jinja2': {
        'check_version': False,
    },
    'reportlab': {
        'check_version': False,
    },
}

installed_vesion_message = 'Installed version of {} library is <{}>.'
req_vesion_message = '{name} {version} is required. Check requirements' \
    'on the manual page <{url}>'


def check_dependencies(module_name, check_version=False):
    module_cfg = MODULES[module_name]
    try:
        module = importlib.import_module(module_name)
        if module_cfg['check_version']:
            package = importlib.import_module(module_cfg['package'])

            if module_cfg.get('method'):
                if not hasattr(package, module_cfg.get('method')):
                    print(
                        installed_vesion_message.format(
                            module_name,
                            module.__version__,
                        ),
                    )
                    print(
                        req_vesion_message.format(
                            name=module_name,
                            version=module_cfg['version'],
                            url=URL,
                        ),
                    )
            elif module_cfg.get('module'):
                try:
                    importlib.import_module(module_cfg['submodule'])
                except ModuleNotFoundError:
                    print(
                        installed_vesion_message.format(
                            module_name,
                            module.__version__,
                        ),
                    )
                    print(
                        req_vesion_message.format(
                            name=module_name,
                            version=module_cfg['version'],
                            url=URL,
                        ),
                    )

        return True
    except ModuleNotFoundError:
        print(
            '{name} library is missing. Check requirements on the'
            ' manual page <{url}>'.format(
                name=module_name,
                url=URL,
            ),
        )


def main():
    for module in MODULES:
        if check_dependencies(module):
            print('{name} is installed.'.format(name=module))


if __name__ == "__main__":
    main()
