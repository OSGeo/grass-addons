#!/usr/bin/env python

# PURPOSE: Extracts page one line descriptions for index.html of GRASS GIS Addons

# AUTHORS: Martin Landa (Bash version)
#          Vaclav Petras (Python version)

import os
import sys
import re


def get_desc_from_manual_page_line(text):
    """
    >>> get_desc_from_manual_page_line("r.example - This is a description<br>")
    'This is a description'
    """
    # this matches the dash at the beginning
    text = text.split(" - ", 1)[1]
    # this matches a tag at the end
    # (supposing no tags in the description and < represented as &lt;
    text = text.split("<", 1)[0]
    return text


def main(filename):
    with open(filename) as page_file:
        desc = None
        in_desc_block = False
        desc_block_start = re.compile(r'NAME')
        desc_block_end = re.compile(r'KEYWORDS')
        desc_line = re.compile(r' - ')
        for line in page_file:
            line = line.rstrip()  # remove '\n' at end of line
            if desc_block_start.search(line):
                in_desc_block = True
            elif desc_block_end.search(line):
                in_desc_block = False
            if in_desc_block:
                if desc_line.search(line):
                    desc = get_desc_from_manual_page_line(line)
        if not desc:
            desc = "(incomplete manual page, please fix)"
        # the original script attempted to add also </li> but it as not working
        # now we leave up to the caller as well as whitespace around
        print desc


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("{name} takes exactly one argument (HTML manual page name)."
                 " {argc} parameters were given."
                 .format(name=os.path.basename(sys.argv[0]),
                                               argc=len(sys.argv) - 1))
    sys.exit(main(sys.argv[1]))
