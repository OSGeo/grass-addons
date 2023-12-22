#!/bin/sh
# a little script to track module memory use
#  Hamish Bowman, 31 Dec 2009   (released to the public domain)

FOLLOW=r.in.xyz
OUTFILE="$FOLLOW.memlog"
SLEEP=5

echo "date sec_since_1970 VirtMemSize   ResMemSize" > "$OUTFILE"

while [ "`ps -C $FOLLOW > /dev/null; echo $?`" -eq 0 ] ; do
   #Memory: VirtSize   ResSize
   MEMUSE=`ps rxl | grep "$FOLLOW" | awk '{print $7 "   " $8 }'`

   echo "`date`  `date +%s`  $MEMUSE" >> "$OUTFILE"

   sleep $SLEEP
done
