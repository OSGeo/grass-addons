Notes about Subversion2Git migration
------------------------------------

0. Go to SVN dir repo

1. Generate authors file

$ svn log --xml --quiet | grep author | sort -u | perl -pe 's/.*>(.*?)<.*/$1 = /' > authors.txt

2. Update authors file based on contributors.csv and contributors_extra.csv files

$ python3 svn-contributors-to-git.py

3. TBD
