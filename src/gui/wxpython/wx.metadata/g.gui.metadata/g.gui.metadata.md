## DESCRIPTION

*g.gui.metadata* supports advanced tools for metadata management
according to [ISO 19115](https://www.iso.org/standard/26020.html).

The metadata editor includes a graphical interface for converting
metadata from r.info and v.info into ISO based metadata, editing
metadata files and creating metadata templates. In addition, the
graphical module allows validating INSPIRE and GRASS Basic profile.

## NOTES

For dependencies and installation instructions see the dedicated [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

### Naming of metadata files and storage

Default location for exported metadata files is the *metadata* directory
in the map's mapset. For raster maps, the prefix derived from the
current nomenclature is *raster*, and for vector maps *vector*. The
files end with *.xml* extension.

For example, default metadata file name for the vector map "roads" is
*vector\_roads.xml*.

### Metadata profile

The *basic* profile is substituted from intersection between items
stored in GRASS native metadata format and INSPIRE profile. The
intersect (subset) includes all available GRASS metadata. Metadata which
cannot be assigned to ISO based attributes are stored in metadata
attribute *abstract*. The *inspire* profile fulfills the criteria of
INSPIRE profile. Values that cannot be read from native GRASS metadata
are filled by the text string `'$NULL'`. This rule applies for both
profiles.

#### Profile for temporal dataset

This function is based on t.info.iso which allows to create ISO based
metadata for temporal maps. Product of this function cannot be compiled
by INSPIRE profile because an additional attribute from ISO 19115
package have been added.

### Creation of metadata

The editor offers two editing modes. The first one allows to create
metadata from selected GRASS maps from an active location. The second
one allows editing of an external metadata file.

#### Metadata editor for spatial and temporal maps

The basis of this editor is similar to r|v.info.iso. After the selection
of the map, the editor converts native metadata of map to ISO based
metadata. By exported xml file is metadata editor initialized. There are
three options to select: **basic**, **inspire** or **load custom**. The
last one allows to load a metadata profile from a file, for example in
the case of using a predefined template. The intersection of GRASS Basic
profile (all the available metadata for the selected map) and loaded
custom profile will proceed with this selection.

#### External metadata editor

This editor mode allows to load user own templates and xml files for
editing. This option does not support any connection with GRASS maps
metadata.

### Defining templates

This function allows to create pattern of metadata profile. In other
words it supports defining fixed values to template. When using created
template, the editor does not initialize texts inputs of defined values.
These attributes are only visible in the Tree Browser in the editor.
Direct link on this function is multiple editing mode (see below).

If the check-box of metadata attribute is checked, the OWSLib object in
the template will be replaced by value. Unchecked attributes will not
change this 'part' of the template.

The yellow background of the text fields indicates metadata attributes
that cannot be read from GRASS map information.

### Editing metadata of multiple map selection

This option can be used by selecting multiple maps in the data catalog.
It is possible to use predifined templates with this editing mode.

### Validation of metadata profile

On the right side of editor there is a validator of metadata. Currently,
validator is able to validate two build-in profiles.

### Updating GRASS native metadata

The g.gui.metadata module allows to update native GRASS metadata with
the modules r.support and v.support. The intersection between ISO based
metadata and r|v.support is limited by the available parameters for
these modules.

### Creating reports for GRASS maps in PDF format

This function allows to automatically generate metadata reports as PDF
documents. Missing values are replaced by "Unknown" string.

## SEE ALSO

*[r.info](https://grass.osgeo.org/grass-stable/manuals/r.info.html),
[v.info.iso](v.info.iso.md), [g.gui.metadata](g.gui.metadata.md)
[db.csw.harvest](db.csw.harvest) [db.csw.admin](db.csw.admin)
[db.csw.run](db.csw.run)*

See also related [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

## AUTHORS

Matej Krejci, [OSGeoREL](https://geo.fsv.cvut.cz/gwiki/osgeorel) at the
Czech Technical University in Prague, developed during [Google Summer of
Code 2014](https://trac.osgeo.org/grass/wiki/GSoC/2014/MetadataForGRASS)
(mentors: Margherita Di Leo, Martin Landa)
