#!/bin/sh

FROMMAIL="me@example.com" # TO BE SET

echo "$1 The jobs that you submitted have finished" | mail -s "Jobs finished" $1
