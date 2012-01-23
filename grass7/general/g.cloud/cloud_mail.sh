#!/bin/sh

FROMMAIL="me@somewhere.com" # TO BE SET

echo "$1 The jobs that you submitted have finished" | mail -s "Jobs finished" $1
