#!/usr/bin/env python3
"""csv_dequote.py.

Take a .csv file with quoted strings, convert the real comma delimiters
to pipes (|) and strip away the double quote chars.

Author:   Hamish Bowman, Dunedin, New Zealand, June 2012 (original Perl)
          Python port: 2026
          (c) 2012 M. Hamish Bowman, and the GRASS Development Team
License:  GNU GPL >=2. See the GPL.TXT file which comes with GRASS
          for details.

USAGE:  csv_dequote.py infile.csv [outfile.psv]

  if outfile is not given it will take the basename of the input
  file and give it the .psv extension ('Pipe Sep Vars').
"""

import csv
import os
import sys

OUTSEP = "|"


def main(argv):
    if len(argv) < 2 or len(argv) > 3:
        sys.stderr.write("USAGE: csv_dequote.py infile.csv [outfile.psv]\n")
        return 1

    infile = argv[1]
    outfile = argv[2] if len(argv) == 3 else None

    if outfile is None:
        # Match the Perl behavior: File::Basename::fileparse + "$file.psv"
        # drops the directory component.
        base = os.path.basename(infile)
        base_no_ext, _ = os.path.splitext(base)
        outfile = base_no_ext + ".psv"

    try:
        fin = open(infile, newline="")
    except OSError as exc:
        sys.stderr.write("{}: {}\n".format(infile, exc.strerror))
        return 1

    try:
        # "x" creates the file atomically and fails if it already exists,
        # so we never overwrite an existing file (no check-then-open race).
        fout = open(outfile, "x", newline="")
    except FileExistsError:
        fin.close()
        sys.stderr.write(
            'ERROR: "{}" already exists.\n'
            "       Will not overwrite; aborting.\n".format(outfile)
        )
        return 1
    except OSError as exc:
        fin.close()
        sys.stderr.write("{}: {}\n".format(outfile, exc.strerror))
        return 1

    had_parse_error = False
    try:
        reader = csv.reader(fin)
        # csv.Error is raised by next() on parse failures, not by the writes.
        # Drive the reader explicitly so we can catch and continue per row.
        while True:
            try:
                row = next(reader)
            except StopIteration:
                break
            except csv.Error as exc:
                sys.stderr.write(
                    "Unable to parse CSV at line {} in {}: {}\n".format(
                        reader.line_num, infile, exc
                    )
                )
                had_parse_error = True
                continue
            fout.write(OUTSEP.join(row))
            fout.write("\n")
    finally:
        fin.close()
        fout.close()

    return 1 if had_parse_error else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
