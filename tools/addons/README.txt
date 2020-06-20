## WORKFLOW

(updated in 6/2020)

Cronjobs are run on the `grasslxd` container (on Server `osgeo7`).
For details, see:
https://github.com/OSGeo/grass-addons/blob/master/tools/cronjobs_osgeo_lxd/README.md


## Old WORKFLOW

These scripts are used for building addons modules (on build server,
currently at the CTU in Prague) and publishing their manual pages on
publishing server (grass.osgeo.org).

On building server (geo102.fsv.cvut.cz) two scripts are
running (see file crontab.build):

1) compile-grass.sh to recompile GRASS on it (daily or so);

2) grass-addons-build.sh to create addons packages, the script
   provides tarballs with created addons manual pages and logs for
   publication on the publishing server.

   On publishing server (grass.osgeo.org) one script is running (see
   file crontab.publish):

3) grass-addons-publish.sh downloads provided tarballs (2) from
   building server and creates index.html page on publishing server at
   https://grass.osgeo.org/grass7/manuals/addons/index.html


SCRIPTS OVERVIEW

* build-xml.py - support Python script called by compile-xml.sh
* compile.sh   - support script to compile GRASS Addons modules called by compile-xml.sh
* compile-xml.sh - creates XML file for each addons module (used by g.extension)
* grass-addons-index.sh - creates ovewview index page, called by grass-addons-publish.sh
* grass-addons-build.sh - called on Building server (2)
* grass-addons-publish.sh - called on Publishing server (1)
* compile-addons.sh - compiles GRASS Addons, called by grass-addons-build.sh
* compile-grass.sh - compiles GRASS
* update_manual.py - support Python script which modifies addons
  manual pages for Publishing server (called by grass-addons-build.sh)

RESULTS

* manual pages at: http://grass.osgeo.org/grass7/manuals/addons/
* XMLs file at: https://grass.osgeo.org/addons/
* winGRASS binary files at: http://wingrass.fsv.cvut.cz/grass78/x86/addons/

SEE ALSO

https://trac.osgeo.org/grass/wiki/AddOnsManagement

