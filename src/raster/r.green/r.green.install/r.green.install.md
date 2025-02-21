[![image-alt](grass_logo.png)](https://grass.osgeo.org/grass-stable/manuals/index.html)

-----

## NAME

*r.green.install* - Toolset to check that all the necessary Python
libraries like scipy and numexpr are present in the python path. The
module also check post-installation troubles that sometimes may occur.

## KEYWORDS

[raster](https://grass.osgeo.org/grass-stable/manuals/raster.html),
[biomass
topic](https://grass.osgeo.org/grass-stable/manuals/topic_biomass.html)

## DESCRIPTION

The module installs the missing Python libraries for different operating
systems and provide a general menu in the GRASS GUI.

## NOTES

*r.green.install* checks that all the necessary Python libraries like
scipy and numexpr are present in the python path. The module also check
post-installation troubles that sometimes may occur.

### Installation on Microsoft Windows

You should install [GRASS
GIS](https://grass.osgeo.org/download/windows/) with administrator
rights; either the stand-alone installer or via OSGeo4W package, in a
directory with full control of permissions, to be able to intall the
*r.green* modules.

![image-alt](r_green_install_permissions.png)  
Microsoft Windows Permissions

The *r.green* modules are based on Python libraries. The module
*r.green.install -i* is able to download and install them. However, some
troubles can raise due to new links or versions. In this case, you can
manually download the following libraries in your GRASS installation
directory from
[https://www.lfd.uci.edu/\~gohlke/pythonlibs/](https://web.archive.org/web/20231011171244/https://www.lfd.uci.edu/~gohlke/pythonlibs/)
according with your GRASS download (32bit or 64bit):

| 32bit                                   | 64bit                                        |
| --------------------------------------- | -------------------------------------------- |
| numpy-1.11.0b3+mkl-cp27-cp27m-win32.whl | numpy-1.11.0b3+mkl-cp27-cp27m-win\_amd64.whl |
| scipy-0.17.0-cp27-none-win32.whl        | scipy-0.17.0-cp27-none-win\_amd64.whl        |
| numexpr-2.5-cp27-cp27m-win32.whl        | numexpr-2.5-cp27-cp27m-win\_amd64.whl        |

After the downloading, in the grass Command Console use the following
code to install libraries and the *r.green* menu:

```sh
r.green.install -i
```

Check the list of suggested libraries with the previous table. If they
agree, you can proceed with the installation. If you install the Energy
menu, use the following command:

```sh
r.green.install -x
```

Close GRASS and restart the programm to have in the the menu the session
energy with all the *r.green* modules.

## SEE ALSO

*[r.green](r.green.md) - overview page*

## AUTHOR

Pietro Zambelli (Eurac Research, Bolzano, Italy)
