#!/usr/bin/python

# Support Python scripts which modifies Addons manual pages for
# publishing server

import os
import sys
import re


def get_addons(path):
    """Get list of addons

    Goes two levels deep to get directory names which are assumed
    to be addon names.
    """
    top_dirs = os.walk(path).next()[1]
    addons = []
    for d in top_dirs:
        a.extend(os.walk(d).next()[1])
    addons.extend(top_dirs)
    return addons


def main(htmlfile, prefix):
    try:
        f = open(htmlfile)
        shtml = f.read()
    except IOError as e:
        sys.exit("Unable to read manual page: %s" % e)
    else:
        f.close()

    pos = []

    # find URIs
    pattern = r'''<a href="([^"]+)">([^>]+)</a>'''
    # TODO: replace the magic 4 by passing the base addons dir as parameter
    addons = get_addons(os.sep.join(htmlfile.split(os.sep)[:4]))
    for match in re.finditer(pattern, shtml):
        # most common URLs
        if match.group(1).startswith('http://'):
            continue
        if match.group(1).startswith('https://'):
            continue
        # protocol-relative URL
        if match.group(1).startswith('//'):
            continue
        # TODO: perhaps we could match any *://
        # link to other addon
        if match.group(1).replace('.html', '') in addons:
            continue
        pos.append(match.start(1))

    if not pos:
        return  # no match

    # replace file URIs
    ohtml = shtml[:pos[0]]
    for i in range(1, len(pos)):
        ohtml += prefix + '/' + shtml[pos[i-1]:pos[i]]
    ohtml += prefix + '/' + shtml[pos[-1]:]

    # write updated html file
    try:
        f = open(htmlfile, 'w')
        f.write(ohtml)
    except IOError as e:
        sys.exit("Unable for write manual page: %s" % e)
    else:
        f.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("provide file and url")
    main(sys.argv[1], sys.argv[2])
