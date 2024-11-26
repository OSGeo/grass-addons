#!/bin/sh

# 2020-2024, Markus Neteler
# deploy updated web site from github repo

# preparation
#  sudo chown -R neteler.users /var/www

# 0.  change into local git repo copy
#     cd ~ ; git clone https://github.com/OSGeo/grass-website.git
#     cd grass-website
# 1.  update local repo from github
# 2.  rm previously built pages in local git repo copy
# 3.  build updated pages with hugo
# 4.  create tmp target web directory
# 5.  copy over updated pages to tmp target web directory
# 6.  rm previously deployed web pages while not deleting src code files in their adjacent directory (careful!)
# 7.  copy over updated pages from tmp target web directory to server target web directory
# 8.  links src code dir content into now deployed web directory
# 9.  rm tmp target web directory
# 10. restore linked src file timestamps from their original source time stamps

cd /home/neteler/grass-website/ && \
   git pull origin master && \
   rm -rf /home/neteler/grass-website/public/* && \
   nice /home/neteler/go/bin/hugo && \
   mkdir /var/www/html_new && \
   \cp -rp /home/neteler/grass-website/public/* /var/www/html_new/ && \
   rm -fr /var/www/html/* && \
   \mv /var/www/html_new/* /var/www/html/ && \
   ln -s /var/www/code_and_data/* /var/www/html/ && \
   rmdir /var/www/html_new && \
   (cd /var/www/html/ ; /home/neteler/bin/fix_link_timestamp.sh .)
