#!/usr/local/bin/perl

opendir DIR, "./";
@files=readdir DIR;
closedir DIR;
$nfiles=$#files;


while($nfiles>=0){
    ($name,$extension)= split(/\./,$files[$nfiles]);
    if($extension eq "c" || $extension eq "h"){
	$out = join(".",$name,"ps");
	system("a2ps $files[$nfiles] -o $out");
	system("lpr -PNE.PP.Sud $out");
    }
    $nfiles = $nfiles - 1;
}
