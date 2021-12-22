#!/bin/bash

# test get_page_description.py
# must be executed in the directory where it is paced in the source code

python -m doctest ../get_page_description.py
../get_page_description.py data/r.standard.example.html
../get_page_description.py data/r.group.page.html
../get_page_description.py data/r.group.page.with.toc.html
../get_page_description.py data/wxGUI.example.html
../get_page_description.py data/g.broken.example.html
../get_page_description.py data/g.no.keywords.html
../get_page_description.py data/g.almost.empty.html
