## DESCRIPTION

*v.in.redwg* imports DWG files into GRASS.

## EXAMPLE

```sh
v.in.redwg input=map.dwg output=map
```

## NOTES

v.in.redwg **does not require OpenDWG or any proprietary software**. It
requires [LibreDWG](https://www.gnu.org/software/libredwg), which is
released under the GNU GPLv3.****

You need to download, compile and install (check website) LibreDWG and
use the related `configure` options to tell GRASS about it (warning:
configure options not implemented yet)

```sh
   ./configure \
   ... \
   --with-libredwg \
   --with-libredwg-includes=/usr/include \
```

Then run *make* to compile this module.

Not all entity types are supported (warning printed).

## AUTHOR

Rodrigo Rodrigues da Silva (pitanga at members dot fsf dot org), São
Paulo, Brazil  
based on original code by Radim Blazek, ITC-Irst, Trento, Italy
