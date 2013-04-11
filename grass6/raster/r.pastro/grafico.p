set grid
set xlabel 'distanza'
set ylabel 'H'
set style line 2 lt 2 lw 2
set terminal gif notransparent size 1200,300
set nokey
set output 'immagini/profilo_altimetrico.gif'
plot 'per_plot3' using 1:2 with line ls 2
