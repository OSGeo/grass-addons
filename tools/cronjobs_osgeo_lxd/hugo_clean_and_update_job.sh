#!/bin/sh

# 2020 Markus Neteler
# deploy updated web site from github repo

# 1. update local repo from github
# 2. rm previously built pages
# 3. built updated pages
# 4. rm deployed web pages while not deleting src code files in their separate directory (careful!)
# 5. copy over updated pages to web pages dir
# 6. copy over Google site ranking token
# 7. links src code dirs into deployed web pages dir
# 8. restore link timestamps from their original source time stamps

cd /home/neteler/grass-website/ && git pull origin master && rm -rf /home/neteler/grass-website/public/* && /usr/local/bin/hugo && rm -fr /var/www/html/* && \cp -rp /home/neteler/grass-website/public/* /var/www/html/ && cp -p /home/neteler/cronjobs/googleebda3c3d501e9945.html /var/www/html/ && ln -s /var/www/code_and_data/* /var/www/html/ && (cd /var/www/html/ ; /home/neteler/bin/fix_link_timestamp.sh .)

