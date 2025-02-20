#!/bin/sh

# 2020-2024, Markus Neteler
# deploy updated web site from github repo

# preparations:
#  sudo chown -R neteler.users /var/www
# get grass-website repo
#  cd ~/
#  git clone https://github.com/OSGeo/grass-website.git
####

# 1. change into local git repo copy
# 2. update local repo from github
# 3. build updated pages with hugo into clean directory
# 4. rsync over updated pages to target web directory, deleting leftover files
# 5. generate links from src code directory content into web directory
# 6. restore timestamps of links from their original time stamps in src directory

cd /home/neteler/grass-website/ && \
   git pull origin master && \
   rm -rf /home/neteler/grass-website/public/* && \
   nice /home/neteler/go/bin/hugo && \
   rsync -a --delete /home/neteler/grass-website/public/ /var/www/html/ && \
   ln -s /var/www/code_and_data/* /var/www/html/ && \
   (cd /var/www/html/ ; /home/neteler/bin/fix_link_timestamp.sh .)
