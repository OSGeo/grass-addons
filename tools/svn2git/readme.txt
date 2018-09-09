Notes about Subversion2Git migration
------------------------------------

See also

* https://trac.osgeo.org/gdal/wiki/rfc71_github_migration
* https://trac.osgeo.org/gdal/wiki/UsingGitToMaintainGDALWorkflow

Recipe how to build authors file from contributors.csv & contributors_extra.csv files:

$ echo "(no author) = unknown <unknown@unknown>" > authors.txt
$ svn log --xml --quiet | grep author | sort -u | perl -pe 's/.*>(.*?)<.*/$1 = /' >> authors.txt
$ python3 svn-contributors-to-git.py

1. Initialize git repo (preferably use AUTHORS.txt from SVN)

$ mkdir grass-gis-git ; cd grass-gis-git
$ git svn init --stdlayout https://svn.osgeo.org/grass/grass
$ git svn --authors-file=path/to/grass_addons/tools/svn2git/AUTHORS.txt
