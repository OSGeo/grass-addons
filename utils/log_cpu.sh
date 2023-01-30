#!/bin/sh
############################################################################
#
# TOOL:         log_cpu.sh
# AUTHOR:       Hamish Bowman, Dunedin, New Zealand
# PURPOSE:      Runs in the background on the server, collects load info
#               for later analysis
# COPYRIGHT:    (c) 2010 Hamish Bowman, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# script to log cpu use etc.

# log every 5 minutes
interval=300

outfile=~/"cpu_use.`hostname -s`.log"

#echo "Will consume about $((50 * 3600/$interval * 24 / 1024)) kb/day"

echo "#year/day hr:min TZ cpu_1min_avg cpu_5min_avg cpu_15min_avg cpu_hog hog_cpu% free_mem_mb" >> "$outfile"

while [ 1 -eq 1 ] ; do
   unset TIMESTAMP CPU_USAGE CPU_HOG FREE_MEM
   TIMESTAMP=`date -u '+%Y/%j %k:%M UTC'`
   CPU_USAGE=`uptime | sed -e 's/^.*average://' -e 's/,//g' -e 's/^ //'`
   CPU_HOG=`top -b -n 1 | sed -e '1,7d' | head -n 1 | awk '{print $12 " " $9}'`
   FREE_MEM=`free -m | grep 'buffers/cache' | awk '{print $4}'`
   sleep 1
   echo "$TIMESTAMP $CPU_USAGE $CPU_HOG $FREE_MEM" >> "$outfile"
   sleep `expr $interval - 1`
done



## top load times
#cat cpu_use.xblade14.log | sort -k4 -r | grep -v '^#' | head -n 20
## lowest RAM times
#cat cpu_use.xblade14.log | sort -k9 | grep -v '^#' | head -n 20


# #### plot using gnuplot
# # 5==1min avg, 6==5min avg, 7==15min avg
# data=7
#
# for server in xblade13 xblade14 ; do
#   file=cpu_use.$server
#   cat $file.log | sed -e 's/^#.*//' | cut -f2 -d/ | \
#     tr ':' ' ' | tr -s ' ' | cut -f1-3,$data -d' ' | awk \
#     '{ if(/./) {printf("%f %s\n", $1 + $2/24 + $3/(24*60), $4)} else {print} }' \
#     > $file.prn
# done
#
#
# ( cat << EOF
# set terminal svg size 800 480
# set output "cpuload.svg"
# set grid
# set xlabel 'Time (day of year, UTC)'
# set ylabel 'CPU load (15 minute average)'
# set title 'xblade loads, May/June 2010'
# #set label "httpd" at 147.332, 6.5
# #set label "rsync" at 147.278, 3.9
# set arrow from 146,1 to 160,1 nohead lt -1 lw 1.75
#
# plot "cpu_use.xblade14.prn" title 'xblade14' with lines lt 8, \
#      "cpu_use.xblade13.prn" title 'xblade13' with lines lt 3
# EOF
# ) | gnuplot
#
# inkscape --file=cpuload.svg --export-png=cpuload.png -b white


########
# Average load:
# set data=6 in above to look at 5 minute averages (since 5 minute sampling time)
#
echo "
xblade13 = load('cpu_use.xblade13.prn');
xblade14 = load('cpu_use.xblade14.prn');
xblade13_mean_load = mean(xblade13(:,2))
xblade14_mean_load = mean(xblade14(:,2))
x13_load_gt1 = length(find ( xblade13(:,2) > 1)) / length(xblade13(:,2))
x14_load_gt1 = length(find ( xblade14(:,2) > 1)) / length(xblade14(:,2))
" | octave
#
#
# 0.0998   1 %   (load is >1.0: 1.5% of the time )
# 0.5197   52 %  (load is >1.0: 10.1% of the time )
#
# Matlab plotting code:  (perhaps SciPy/NumPy/PyPlot?)
#
# clf
# set(gcf, 'color', 'w')
# colormap([.5 .5 .5])
#
# subplot(211)
# hist(xblade13(:,2),512)
# xlim([0 1])
# xlabel('CPU load (5 minute averages); tail cut off at 1.0')
# ylabel('number of samples')
# hT = title({'xblade13 loads, May-July 2010' '' ['Load > 1.0:  ' num2str(x13_load_gt1 * 100, '%.1f') '% of the time']});
# posn = get(hT, 'Position');
# posn(2) = posn(2) * 0.5;
# set(hT, 'Position', posn)
# hL = line([1 1], [0 5000], 'color', 'k', 'LineStyle', ':');
#
# subplot(212)
# hist(xblade14(:,2),255)
# xlim([0 4])
# xlabel('CPU load (5 minute averages); tail cut off at 4.0')
# ylabel('number of samples')
# hT = title({'xblade14 loads, May-July 2010' '' ['Load > 1.0:  ' num2str(x14_load_gt1 * 100, '%.1f') '% of the time']});
# posn = get(hT, 'Position');
# posn(2) = posn(2) * 0.5;
# set(hT, 'Position', posn)
# hL = line([1 1], [0 1500], 'color', 'k', 'LineStyle', ':');
#
