## DESCRIPTION

*m.csw.update* updates the CSW connections resource XML file (required
by the *g.gui.cswbrowser* and *g.gui.metadata* modules). If the **-p**
flag is used only printing instead of writing is done.

The module also allows validate the connections resources XML file
against XSD schema, remove invalid and not active CSW connections
resources candidates.

## NOTES

For dependencies and installation instructions see the [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

Stored new connections resources candidates are only those being active
and valid.

### Writing new connections resources candidates

Default source of the new candidates is a spreadsheet file (\*.ods),
which is to be stored in the module's *config/* directory. It is
possible to use the updated document directly from the web address, see
**-w** flag.

## EXAMPLES

Import and store new resources connections candidates (default):

```sh
m.csw.update url=API-cases.ods
```

Store new resources connections candidates along with printing a summary
info:

```sh
m.csw.update -s
```

Print only all new connections resources candidates (with following
format *'{Country}, {Governmental level}, {API provider}: {URL}'*) with
summary info:

```sh
m.csw.update -ps
```

Print only active new connections resources candidates with summary
info:

```sh
m.csw.update -pas
```

Validate the default connections resources XML file against XSD schema
plus validate individual CSW connection resources (remove and print non
active CSWs):

```sh
m.csw.update -xc
```

## SEE ALSO

*[g.gui.cswbrowser](g.gui.cswbrowser.md),
[g.gui.metadata](g.gui.metadata.md)*

See also related [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

## AUTHOR

Tomas Zigo
