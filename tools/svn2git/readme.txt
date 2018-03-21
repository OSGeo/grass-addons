Notes about Subversion2Git migration
------------------------------------

See also

* https://trac.osgeo.org/gdal/wiki/rfc71_github_migration
* https://trac.osgeo.org/gdal/wiki/UsingGitToMaintainGDALWorkflow

1. Generate authors file

$ echo "(no author) = unknown <unknown@unknown>" > authors.txt
$ svn log --xml --quiet | grep author | sort -u | perl -pe 's/.*>(.*?)<.*/$1 = /' >> authors.txt

2. Update authors file based on contributors.csv and contributors_extra.csv files

$ python3 svn-contributors-to-git.py
