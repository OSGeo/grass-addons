#!/usr/bin/python

# Support Python scripts which modifies Addons manual pages for
# publishing server

import os
import sys
import re


def get_pages(path):
    """Get list of HTML pages in the given directory and its subdirectories

    Only filenames are returned, not the paths.
    """
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".html"):
                matches.append(filename)
    return matches


def main(htmlfile, prefix, html_directory):
    try:
        f = open(htmlfile)
        shtml = f.read()
    except IOError as e:
        sys.exit("Unable to read manual page: %s" % e)
    else:
        f.close()

    pos = []

    # find URIs
    pattern = r"""<a href="([^"]+)">([^>]+)</a>"""
    addon_pages = get_pages(html_directory)
    for match in re.finditer(pattern, shtml):
        # most common URLs
        if match.group(1).startswith("http://"):
            continue
        if match.group(1).startswith("https://"):
            continue
        # protocol-relative URL
        if match.group(1).startswith("//"):
            continue
        # TODO: perhaps we could match any *://
        # link to other addon
        if match.group(1) in addon_pages:
            continue
        pos.append(match.start(1))

    if not pos:
        return  # no match

    # replace file URIs
    ohtml = shtml[: pos[0]]
    for i in range(1, len(pos)):
        ohtml += prefix + "/" + shtml[pos[i - 1] : pos[i]]
    ohtml += prefix + "/" + shtml[pos[-1] :]

    # write updated html file
    try:
        f = open(htmlfile, "w")
        f.write(ohtml)
    except IOError as e:
        sys.exit("Unable for write manual page: %s" % e)
    else:
        f.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Provide file, URL and directory with other HTML files")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
