## DESCRIPTION

*g.citation* - creates citation or metadata based on documentation of a
given module.

### Formats

#### Citation File Format

[Citation File Format](https://citation-file-format.github.io/) (CFF) is
a YAML based format for citations, specifically CITATION files to be
included with software or code as `CITATION.cff`.

#### JSON

Currently, the keys and the overall structure are subject to change, but
the plan is to stabilize it or to provide existing metadata format in
JSON. Pretty-printed version is good, e.g., for saving into files, while
the other, compact version is good for further processing.

#### Pretty printed Python dictionary

This format is essentially a dump of the internal data structure holding
the citation entry. It should not be used in scripts, i.e. further
parsed, for that there are other formats such as JSON. When this is
advantageous is exploring what information the module was able to
acquire for the citation.

## NOTES

- Don't use the `format=dict` for further processing. It is meant for
    exploration of what information the module acquired.
- The structure of the JSON output is yet not guaranteed.

## EXAMPLES

```sh
g.citation module=v.select format=plain
```

```sh
g.citation f=pretty-json -a -s | grep '"name": ' | sort | uniq
```

```sh
g.citation -s format=citeproc vsep="< p>" -a > all.html
```

## KNOWN ISSUES

- More output formats or styles are needed. The following formats were
    suggested so far: `csl,datacite,dublincore,json-ld,narcxml`
- The structure of the JSON output is not guaranteed. It reflects the
    internal structure (only the empty entries are removed).
- Version and date in CFF output are incomplete.

## SEE ALSO

*[g.search.module](https://grass.osgeo.org/grass-stable/manuals/g.search.module.html)*

## AUTHORS

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/) (ORCID:
0000-0001-5566-9236)  
Peter Loewe (ORCID: 0000-0003-2257-0517)  
Markus Neteler, [mundialis](https://www.mundialis.de) (ORCID:
0000-0003-1916-1966)
