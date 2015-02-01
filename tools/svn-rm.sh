#!/bin/sh

svn status | grep ^? | awk '{print $2}' | xargs rm -rfv

exit 0
