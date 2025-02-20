## DESCRIPTION

The *r.maxent.setup* addon provides a helper function to install Maxent
and ensures that GRASS GIS can locate the Java executable, a
prerequisite for running Maxent.

### Maxent

The *r.maxent.train* and *r.maxent.predict* modules require the Maxent
software, which can be downloaded from the [Maxent
website](https://biodiversityinformatics.amnh.org/open_source/maxent).
The *r.maxent.setup* installs this to the GRASS GIS addon directory. If
you want to update the Maxent.jar file, use the **-u** flag.

### Java

Maxent requires Java to be installed, and it should be accessible from
the GRASS GIS environment. You can check this by running the
*r.maxent.setup* with the **-j** flag.

On Windows, even if JAVA is installed and on the PATH, GRASS GIS may
still not be able to find it. The reason is that OSGeo4W environment
used by GRASS GIS on Windows has its own shell environment, which may
not automatically inherit the system-wide PATH or environment variables
from Windows. As a result, even if Java is correctly installed and
accessible from a regular Command Prompt or PowerShell, it might not be
visible to GRASS GIS within the OSGeo4W shell.

To enable GRASS GIS to find the path to the Java executable, you can set
the path to the executable using the **java** parameter. The path will
be written to a text file in the GRASS GIS addon directory, which can be
used by the *r.maxent.train* and *r.maxent.predict* modules.

An arguably better but more involved way is to add the Java directory to
the OSGeo4W PATH. See the NOTES for a short 'how to'.

## NOTES

Instead of using this addon to set the path to the java executable, you
can add the Java directory to the OSGeo4W PATH temporarily. Open the
Open the OSGeo4W shell and run the following:

```sh
set PATH=C:\Program Files\Java\jdk-XX.X.X\bin;%PATH%
```

Replace C:\\Program Files\\Java\\jdk-XX.X.X\\bin with your Java
installation path. To make this change persistent, you need to edit the
*osgeo4w.bat* file. This file can be found in the OSGeo4W installation
folder. Locate the file, and find the line that starts with *set PATH=*.

At the end of that line, add a semi-colun and the path to the Java
installation path. For example:

```sh
set PATH=%PATH%;C:\Program Files\Java\jdk-XX.X.X\bin;
```

Replace C:\\Program Files\\Java\\jdk-XX.X.X\\bin with your Java
installation path. Save the file and restart the OSGeo4W shell. Note
that you may need administrator rightrs to edit the osgeo4w.bat file.

## SEE ALSO

  - [v.maxent.train](v.maxent.train.md)
  - [v.maxent.predict](v.maxent.predict.md)

## AUTHOR

[Paulo van Breugel](https:ecodiv.earth), [HAS green
academy](https://has.nl), [Innovative Biomonitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/),
[Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
