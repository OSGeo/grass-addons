#!/usr/bin/env python3

############################################################################
#
# TOOL:         windows_addons_latest.py
# AUTHOR(s):    Anna Petrasova
# PURPOSE:      Find the newest published Windows addon bundles
# COPYRIGHT:    (c) 2026 Anna Petrasova and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
#############################################################################

"""Print the newest Windows addon bundle for each platform and GRASS version

The CI of the grass-addons repository (.github/workflows/ci-windows.yml)
publishes the addons compiled for Windows as pre-releases tagged
windows-addons-<date>-<time>-<commit>. Each contains ZIP files with SHA256
checksum files named grass-<version>-addons-windows-<platform>.zip, where
the platform is the distribution and the CPU architecture the addons are
compiled for, e.g. osgeo4w-x86_64.

For each platform and GRASS version, one line is printed with the platform,
the version, the URL of the ZIP file and the URL of the checksum file,
separated by tabs. The ZIP file is the one from the newest pre-release
which has it, because a build does not publish the file for a GRASS version
whose compilation failed. Pre-releases and files which were not created by
the CI, e.g. by hand, are ignored. Only the Python standard library and no
GitHub token is needed.

Called from fetch_unpack_windows_addons.sh.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

API_URL = "https://api.github.com/repos/OSGeo/grass-addons/releases?per_page=30"
TAG_PREFIX = "windows-addons-"
# The account the CI creates the pre-releases and uploads the files with.
CI_ACCOUNT = "github-actions[bot]"
# The version (8.5.0, 8.6.0dev) and the platform (osgeo4w-x86_64) become
# parts of a path on the server.
BUNDLE = re.compile(
    r"grass-(?P<version>[0-9]+\.[0-9]+\.[0-9]+[0-9A-Za-z]*)"
    r"-addons-windows-(?P<platform>[0-9a-z]+-[0-9a-z_]+)\.zip"
)


def created_by_ci(item, key):
    """Return True if the release or file was created by the CI

    Anything else is reported and left out, so that a release created or
    a file uploaded by hand by mistake is not deployed.
    """
    login = (item.get(key) or {}).get("login")
    if login == CI_ACCOUNT:
        return True
    name = item.get("tag_name") or item.get("name")
    print(f"Ignoring {name} created by {login}, not by {CI_ACCOUNT}", file=sys.stderr)
    return False


def newest_bundles(releases):
    """Return (platform, version, ZIP URL, checksum URL) of the newest bundles

    The tags contain a timestamp, so a newer build has a higher tag.
    A bundle without its checksum file is left out.
    """
    builds = sorted(
        (
            release
            for release in releases
            if release["prerelease"]
            and release["tag_name"].startswith(TAG_PREFIX)
            and created_by_ci(release, "author")
        ),
        key=lambda release: release["tag_name"],
        reverse=True,
    )
    bundles = {}
    for build in builds:
        urls = {
            asset["name"]: asset["browser_download_url"]
            for asset in build["assets"]
            if created_by_ci(asset, "uploader")
        }
        for name, url in urls.items():
            match = BUNDLE.fullmatch(name)
            checksum = f"{name}.sha256"
            if match and checksum in urls:
                # Keeps the bundle from the newest build which has one.
                bundles.setdefault(
                    (match["platform"], match["version"]), (url, urls[checksum])
                )
    return [(*key, *urls) for key, urls in sorted(bundles.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--api-url", default=API_URL, help="URL of the list of releases (for testing)"
    )
    args = parser.parse_args()

    request = urllib.request.Request(
        args.api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "grass-addons-cronjob",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            releases = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        sys.exit(f"ERROR: Cannot get the list of releases: {error}")

    bundles = newest_bundles(releases)
    if not bundles:
        sys.exit(
            "ERROR: No file named grass-<version>-addons-windows-<platform>.zip"
            f" with a checksum in the {TAG_PREFIX}* pre-releases created by"
            f" {CI_ACCOUNT}"
        )
    for bundle in bundles:
        print("\t".join(bundle))


if __name__ == "__main__":
    main()
