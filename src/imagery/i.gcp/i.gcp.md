## DESCRIPTION

*i.gcp* manages Ground Control Points (GCPs) non-interactively.

## NOTES

Unlike *g.gui.gcp*, *i.gcp* can be invoked from the command line or
scripts to manage GCPs. It is recommended to create a backup copy of the
original POINTS file using **-b** before making changes to the file. The
backup POINTS file (POINTS\_BAK) can be restored using **-r** or removed
later using **-B**. GCPs in the backup POINTS file can be listed using
**-L**.

## EXAMPLES

List all GCPs in group "sar":

```sh
i.gcp -l group=sar
```

Create a backup copy of the current POINTS file:

```sh
i.gcp -b group=sar
```

Clear all GCPs first by removing the POINTS file:

```sh
i.gcp -c group=sar
```

Add new GCPs at the bottom-left and top-right corners of the satellite
imagery:

```sh
i.gcp group=sar image_coordinates=0,0,31996,32239 target_coordinates=493920,3880490,529470,3916310
```

Add another GCP that will be ignored for now and list all GCPs:

```sh
i.gcp -l group=sar image_coordinates=100,100 target_coordinates=500000,4000000 status=ignore
```

Use the GCP just added and list all:

```sh
i.gcp -u -l group=sar point=3
```

Delete point 1:

```sh
i.gcp -d -l group=sar point=1
```

Ignore points 1-2:

```sh
i.gcp -i -l group=sar point=1-2
```

List GCPs in the backup POINTS file:

```sh
i.gcp -L group=sar
```

Restore the backup POINTS file:

```sh
i.gcp -r group=sar
```

Remove the backup POINTS file:

```sh
i.gcp -B group=sar
```

## SEE ALSO

The GRASS 4 *[Image Processing
manual](https://grass.osgeo.org/gdp/imagery/grass4_image_processing.pdf)*

*[i.group](https://grass.osgeo.org/grass-stable/manuals/i.group.html),
[i.target](https://grass.osgeo.org/grass-stable/manuals/i.target.html),
[i.rectify](https://grass.osgeo.org/grass-stable/manuals/i.rectify.html),
[i.points.auto](i.points.auto.md), [Ground Control Points
Manager](https://grass.osgeo.org/grass-stable/manuals/wxGUI.gcp.html)*

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com)
