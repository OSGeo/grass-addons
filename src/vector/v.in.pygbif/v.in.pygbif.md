## DESCRIPTION

The module *v.in.pygbif* is a wrapper around the
[pygbif](https://pygbif.readthedocs.io/en/latest/index.html) package.  
Thus, *pygbif* is a dependency of v.in.pygbif. pygbif can be installed
like this:

```sh
pip install pygbif [--user]
```

Through *pygbif*, the module allows to download data from the Global
Biodiversity Information Facility ([GBIF](https://www.gbif.org)) using
different search/filter criteria.

Since some of the Darwin Core attribute columns represent SQL key-words,
the prefix "g\_" was added to all attribute columns. The names of taxa
provided at input to the search are written to the column "g\_search".

The point data is downloaded and projected into the current location. By
default import is limited to the current computational region in order
to avoid possible projection errors, e.g. when projecting global data
into UTM locations. However, in lat⁄lon location this limitation can be
skiped using the ***-r*** flag.  
Providing a mask automatically overrides the limitation of the search to
the current computational region.

Terminology in **v.in.pygbif** is oriented on the *Darwin Core*
standard: <https://rs.tdwg.org/dwc>.

Please note that the GBIF Search API has a hard limit of 200,000
occurrences per request. If you want to fetch more records, either
subivide your area of interest or split up your search by using
different search criteria.  
When a list of taxa is given as input, **v.in.pygbif** issues a search
for each taxon individually. Thus, in order to split up a search it is
recommended to either use different filters on time or space.

## EXAMPLES

```sh
# Check matching taxon names and alternatives in GBIF:
v.in.pygbif taxa="Poa,Plantago" rank=genus  -p

# Check matching taxon names and alternatives in GBIF and print output in table:
v.in.pygbif taxa="Poa pratensis,Plantago media,Acer negundo" rank=species -t

# Get number of occurrences for two geni:
v.in.pygbif taxa="Poa,Plantago" rank=genus  -o

# Get number of occurrences for two species:
v.in.pygbif taxa="Poa pratensis,Plantago media" rank=species  -o

# Fetch occurrences for two species into a map for each species:
v.in.pygbif taxa="Poa pratensis,Plantago media" rank=species output=gbif -i

```

## SEE ALSO:

[v.in.gbif](v.in.gbif.md)

## REFERENCES

<https://pygbif.readthedocs.io/en/latest/index.html>  
<https://www.gbif.org>  
<https://techdocs.gbif.org/en/openapi>

## AUTHORS

Stefan Blumentrath, Norwegian Institute for Nature Research, Oslo,
Norway  
Helmut Kudrnovsky
