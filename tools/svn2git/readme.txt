Notes about Subversion2Git migration
------------------------------------

See also

* https://trac.osgeo.org/gdal/wiki/rfc71_github_migration
* https://trac.osgeo.org/gdal/wiki/UsingGitToMaintainGDALWorkflow

Recipe how to build authors file from contributors.csv & contributors_extra.csv files:

$ echo "(no author) = unknown <unknown@unknown>" > authors.txt
$ svn log --xml --quiet | grep author | sort -u | perl -pe 's/.*>(.*?)<.*/$1 = /' >> authors.txt
$ python3 svn-contributors-to-git.py

Run migrate.sh script...
