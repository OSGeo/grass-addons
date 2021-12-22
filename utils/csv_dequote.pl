#!/usr/bin/perl
#
# csv_dequote.pl:
#
#  Take a .csv file with quoted strings, convert the real comma delims
#  to pipes (|) and strip away the double quote chars.
#
#  Author:   Hamish Bowman, Dunedin, New Zealand, June 2012
#            (c) 2012 M. Hamish Bowman, and the GRASS Development Team
#  License:  GNU GPL >=2. See the GPL.TXT file which comes with GRASS
#            for details.
#
# Requires:  Text::CSV   ('apt-get install libtext-csv-perl')
#
#  USAGE:  csv_dequote.pl infile.csv [outfile.psv]
#
#   if outfile is not given it will take the basename of the input
#   file and give it the .psv extension (".Pipe Sep Vars").
#

use strict;
use warnings;
use Text::CSV;
use File::Basename;


my $outsep = '|';

my $infile = shift
  or die "USAGE: csv_dequote.pl infile.csv [outfile.psv]\n";

my $outfile = shift || '';

unless($outfile) {
    my $file = '';
    my $dir = '';
    my $ext = '';
    ($file, $dir, $ext) = fileparse($infile, qr/\.[^.]*/);
    $outfile = "$file.psv";
}

if (-e $outfile) {
    die "ERROR: \"$outfile\" already exists.\
       Will not overwrite; aborting.\n";
}

my $csv = Text::CSV->new();

open (CSVin, "<", $infile) or die "$infile: $!";
open (CSVout, ">", $outfile) or die "$outfile: $!";


while (<CSVin>) {
    if ($csv->parse($_)) {
	my @columns = $csv->fields();
	print CSVout join("$outsep", @columns);
	print CSVout "\n";
    } else {
	my $bad = $csv->error_input;
	print "Unable to parse line: $bad";
    }
}


close CSVin or die "$infile: $!";
close CSVout or die "$outfile: $!";

