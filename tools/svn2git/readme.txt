Notes about Subversion2Git migration
------------------------------------

See also

* https://trac.osgeo.org/gdal/wiki/rfc71_github_migration
* https://trac.osgeo.org/gdal/wiki/UsingGitToMaintainGDALWorkflow

Recipe how to build authors file from contributors.csv & contributors_extra.csv files:

$ echo "(no author) = unknown <unknown@unknown>" > authors.txt
$ svn log --xml --quiet | grep author | sort -u | perl -pe 's/.*>(.*?)<.*/$1 = /' >> authors.txt
$ python3 svn-contributors-to-git.py

Run migrate scripts:

$ 0-migrate-fetch.sh
$ 1-migrate-core.sh
$ 2-migrate-addons-promo.sh
$ 3-rewrite-messages.sh

Push to github for review:

$ cd grass-rewrite
$ git remote add github https://github.com/grass-svn2git/grass.git
$ git push github --all
$ git push github --tags

Similarly for `grass-legacy-rewrite`, `grass-addons-rewrite`, `grass-promo-rewrite`.
