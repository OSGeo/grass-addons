#!/usr/bin/perl
#
# Author: Radim Blazek, ITC-irst, 2005 
#
# Converts GCM ascii format to 12 GRASS raster files (1 for each month)
# and changes longitude from 0-360
# http://www.ipcc-data.org/sres/gcm_data.html
#
# Reference:
#  M. Benito Garzón, R. Blazek, M. Neteler, R. Sanchez de Dios, H. Sainz
#  Ollero, and C. Furlanello, 2006: Predicting habitat suitability with
#  Machine Learning models: the potential area of Pinus sylvestris L. in
#  the Iberian Peninsula. Ecological Modelling,
#  197(3-4):383-393. doi:10.1016/j.ecolmodel.2006.03.015
#  http://www.uam.es/proyectosinv/Mclim/pdf/MBenito_EcoMod.pdf
#
##################

for($i=0; $i<=$#ARGV; $i++){
  if( $ARGV[$i] =~ /input=(.+)/){ $input = $1;  }
  elsif( $ARGV[$i] =~ /output=(.+)/){ $output = $1;  }
}

if ( length($input) == 0 || length($output) == 0 ) {
    die "File not specified\nParameters:\n    input=\n    output=\n";
}

open(IN, "<$input") or die "Cannot open input: $input";


while ( $r = <IN>){
    chomp $r;

    # Header 1
    $r = lc ($r);
    if ( !($r =~ /ipcc data distribution centre results/)  ) { die "Wrong input: $r\n"; }

    # Header 2
    $r = <IN>; chomp $r;
    $r = lc ($r);
    if ( !($r =~ /grid is/) ) { die "Wrong input: $r\n"; }
    ($t, $t, $cols, $t, $rows, $t, $t, $month ) = split / +/, $r;
    $month = lc ( $month );
    $rows = int ($rows);
    $cols = int($cols);
    print "Cols = $cols  Rows = $rows  Month = $month\n";

    # Header 3
    $r = <IN>; chomp $r;
    $r = lc ($r);
    if ( !($r =~ /mean change values/) ) { die "Wrong input: $r\n"; }

    # Header 4
    $r = <IN>; chomp $r;

    # Header 5
    $r = <IN>; chomp $r;

    # Header 6
    $r = <IN>; chomp $r;
    $r = lc ($r);
    if ( !($r =~ /missing/) ) { die "Wrong input: $r\n"; }
    $r =~ /.*  ([^ ]+)/;
    $null = $1;
    print "Null = $null\n";

$outfile = $output . $month;
    print "Output file = $outfile\n";
    open ( OUT, ">$outfile") or die "Cannot open $outfile";
    print OUT "north: 90N\n";
    print OUT "south: 90S\n";
    print OUT "west: 180W\n";
    print OUT "east: 180E\n";
    print OUT "rows: $rows\n";
    print OUT "cols: $cols\n";
    print OUT "null: $null\n";
    print OUT "type: float\n";

    $ncels = $cols * $rows;
    $nread = 0;

    $col = $row = 0;
    while ( $r = <IN> ){
        chomp $r;
        $r =~ s/^ +//;
        $r =~ s/ +/ /g;

        @value = split / /, $r;
        $n = $#value;
        $nread += $n + 1;

        #print OUT "$r\n";

        for ( $i = 0; $i <= $n; $i++ ) {
            #print "$row $col $value[$i]\n";
            $all[$row][$col] = $value[$i];
             
            $col++;
            if ( $col == $cols ) {
                $col = 0;
                $row++;
            }
        }

        if ( $nread >= $ncels ) {
            for ( $r = 0; $r < $rows; $r++ ) {
                $start = $cols/2;
                #print "start = $start\n";
                for ( $c = $start; $c < $cols; $c++ ) {
                    #print "$r $c $all[$r][$c]\n";
                    print OUT "$all[$r][$c] ";
                }
                for ( $c = 0; $c < $cols/2; $c++ ) {
                    #print "$r $c $all[$r][$c]\n";
                    print OUT "$all[$r][$c] ";
                }
                print OUT "\n";
            }
            close (OUT);
            last;
        }
    }

 print "\n";
}
close(IN);







