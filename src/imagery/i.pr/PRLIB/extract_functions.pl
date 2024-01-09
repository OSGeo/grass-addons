#!/usr/local/bin/perl

use strict;
require getopts;

&Getopts('f');


opendir DIR, "./";
@files=readdir DIR;
closedir DIR;
$nfiles=$#files;
$done = 0;

if(!$opt_f){
    while($nfiles>=0){
	($name,$extension)= split(/\./,$files[$nfiles]);
	if($extension eq "c" || $extension eq "h"){
	    if(!$done){
		print "#########################\n$files[$nfiles]\n#########################\n\n";} else {
		    print "\n#########################\n$files[$nfiles]\n#########################\n\n";
		}
	    $done = 1;
	    open(my $FILE,"<",$files[$nfiles]);
	    while(<$FILE>){
		if(!/\#/){
		    print $_;
		}else{
		    goto START;
		}
	    }
	  START:
	    while(<$FILE>){
	      NEWfun:
		if(!/;/ && !/static/){
		    if(/void /){
			print $_;
			while(<$FILE>){
			    if(!/\{/){
				print $_;
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/double /){
			print $_;
			while(<$FILE>){
			    if(!/\{/){
				print $_;
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/float /){
			print $_;
			while(<FILE>){
			    if(!/\{/){
				print $_;
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/int /){
			print $_;
			while(<$FILE>){
			    if(!/\{/){
				print $_;
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/char /){
			print $_;
			while(<$FILE>){
			    if(!/\{/){
				print $_;
			    }else{
				goto NEWfun;
			    }
			}
		    }
		}
	    }
	    close($FILE);

	}
	$nfiles = $nfiles - 1;
    }
} else{
    while($nfiles>=0){
	($name,$extension)= split(/\./,$files[$nfiles]);
	if($extension eq "c"){
	    if(!$done){
		print "/*\n$files[$nfiles]\n*/\n\n";} else {
		    print "\n/*\n$files[$nfiles]\n*/\n\n";
		}
	    $done = 1;
	    open(my $FILE,"<",$files[$nfiles]);
	    while(<$FILE>){
	      NEWfun:
		if(!/;/ && !/static/){
		    if(/void /){
			($func,$param)=split(/\(/,$_);
			print $func,"();\n";
			while(<$FILE>){
			    if(!/\{/){
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/double /){
			($func,$param)=split(/\(/,$_);
			print $func,"();\n";
			while(<$FILE>){
			    if(!/\{/){
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/float /){
			($func,$param)=split(/\(/,$_);
			print $func,"();\n";
			while(<$FILE>){
			    if(!/\{/){
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/int /){
			($func,$param)=split(/\(/,$_);
			print $func,"();\n";
			while(<$FILE>){
			    if(!/\{/){
			    }else{
				goto NEWfun;
			    }
			}
		    }
		    if(/char /){
			($func,$param)=split(/\(/,$_);
			print $func,"();\n";
			while(<$FILE>){
			    if(!/\{/){
			    }else{
				goto NEWfun;
			    }
			}
		    }
		}
	    }
	    close($FILE);

	}
	$nfiles = $nfiles - 1;
    }
}
