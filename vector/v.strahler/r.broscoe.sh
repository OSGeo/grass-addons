#!/bin/sh
#
############################################################################
#
# MODULE:	r.broscoe
# AUTHOR(S):	Annalisa Minelli, Ivan Marchesini
#
# PURPOSE:	Calculates waerden test and t test statistics 
#		for some values of threshold, on a single basin 
#		according to A. J. Broscoe theory (1959) 
#
# COPYRIGHT:	(C) 2008 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
# REQUIREMENTS: you need R installed with "agricolae" package
#	You can install the package by starting R as root and typing
#	install.packages("agricolae")
#	This will install the package from a CRAN mirror on the internet.
#	For more information on R see the documentation available at
#	http://www.r-project.org/
#
# TODO: solve stability problems for low area threshold (cf. v.strahler) 
#############################################################################
#%Module
#%  description: Calculates waerden test and t test statistics for some values of threshold, on a single basin according to A. J. Broscoe theory (1959)
#%  keywords: waerden.test,t.test,mean stream drop
#%End
#%option
#% key: dem
#% type: string
#% key_desc: dem
#% gisprompt: old,cell,raster
#% description: Name of DEM raster map					
#% required : yes
#%END
#%option
#% key: thresholds
#% type: integer
#% description: Threshold values to calculate statistics on (separated by <space>)
#% required : yes
#%end
#%option
#% key: xcoor
#% type: double
#% description: x coord of outlet
#% required : yes
#%end
#%option
#% key: ycoor
#% type: double
#% description: y coord of outlet
#% required : yes
#%end
#%option
#% key: lt
#% type: integer
#% description: Lesser than (in meters), the program doesn't consider stream drops lesser than this
#% required : yes
#%END
#%option
#% key: result
#% type: string
#% gisprompt: new_file,file,output
#% key_desc: name
#% description: Resultant text file to write statistics into
#% required: yes
#%end

if  [ -z "$GISBASE" ] ; then
    echo "You must be in GRASS GIS to run this program." >&2
    exit 1
fi

if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi

dem=$GIS_OPT_DEM
thresholds=$GIS_OPT_THRESHOLDS
xcoor=$GIS_OPT_XCOOR
ycoor=$GIS_OPT_YCOOR
lt=$GIS_OPT_LT
result=$GIS_OPT_RESULT

### setup enviro vars ###
eval `g.gisenv`
: ${GISBASE?} ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}

echo $LOCATION_NAME

#g.region rast=$dem

res=`g.region -p | grep res | sed 1d | cut -f2 -d':' | tr -d ' ' `

#g.region vect=$input 

#g.region n=n+$res s=s-$res e=e+$res w=w-$res

for j in $thresholds
do

g.remove vect=ordered_$j
rm orderedtxt_$j

echo "initializing statistics for threshold value=$j"

r.strahler dem=$dem xcoor=$xcoor ycoor=$ycoor thr=$j output=ordered_$j textoutput=orderedtxt_$j --overwrite 

rm one
rm two
rm three
rm maxord

`cat orderedtxt_$j | sed 2d |sed 1d > one
sort -r -k 4,4 one > two
head -1 two > three
awk 'NR==1{print $4}' three > "maxord"`

maxord=`cat maxord`

rm thrVSmaxord_$j

echo "$j	$maxord" > thrVSmaxord_$j

   a=1
   until [ "$a" -gt "$maxord" ]
   do
      g.remove vect=ord1,ord1_pl,ord1_pl_3d
      g.remove vect=ord1_pl_3d_cat
      rm tmp
      rm ordcol
      rm textout

      v.extract input=ordered_$j output=ord1 type=line layer=1 new=-1 list=$a 

      v.build.polylines input=ord1 output=ord1_pl cats=no

      v.drape input=ord1_pl type=line rast=$dem method=nearest output=ord1_pl_3d

      v.category input=ord1_pl_3d output=ord1_pl_3d_cat type=line option=add cat=1 layer=1 step=1

      v.db.addtable map=ord1_pl_3d_cat table=ord1_pl_3d_cat layer=1 'columns=cat integer, sx double, sy double, sz double, ex double, ey double, ez double'

      v.to.db map=ord1_pl_3d_cat type=line layer=1 qlayer=1 option=start units=meters 'column=sx, sy, sz'

      v.to.db map=ord1_pl_3d_cat type=line layer=1 qlayer=1 option=end units=meters 'column=ex, ey, ez'

      v.rast.stats vector=ord1_pl_3d_cat raster=$dem colprefix=stats percentile=90 --verbose -c


     for i in `db.select table=ord1_pl_3d_cat database=$GISDBASE/$LOCATION_NAME/$MAPSET/dbf/ driver=dbf 'sql=select cat from ord1_pl_3d_cat' | sed 1d`
     do

         min=`echo "select stats_min from ord1_pl_3d_cat where cat=$i" | db.select | sed 1d`
         sz=`echo "select sz from ord1_pl_3d_cat where cat=$i" | db.select | sed 1d`
         ez=`echo "select ez from ord1_pl_3d_cat where cat=$i" | db.select | sed 1d`
	 if [  `echo "$ez - $min" | bc -l | cut -f1 -d'.'` -lt "$lt" ] || [ `echo "$sz - $min" | bc -l | cut -f1 -d'.'` -lt "$lt" ]
	   then
 	   if [ "$ez" -gt "$sz" ]
		then
		echo "$ez - $min" | bc -l | cut -f1 -d'.' >> tmp
		echo $a >> ordcol
	   else
		echo "$sz - $min" | bc -l | cut -f1 -d'.' >> tmp
		echo $a >> ordcol
	   fi
	 else 
	   echo "$ez - $min" | bc -l | cut -f1 -d'.' >> tmp
	   echo $a >> ordcol
	   echo "$sz - $min" | bc -l | cut -f1 -d'.' >> tmp
	   echo $a >> ordcol
	 fi
      done
   paste ordcol tmp > textout\_$a
   #read

   if [ "$a" -gt 1 ]
     then
     b=`echo "$a-1" | bc -l`
     cat textout\_$b textout\_$a > textout_temp
     rm textout\_$a textout\_$b
     mv textout_temp textout\_$a
   fi

   a=$(($a+1))
   done

   mv textout\_$maxord textout
   echo "plotting textout..."
   cat textout

   echo "
   imported=read.csv('textout', sep = '\t', dec='.', header = F)
   dframe=data.frame(imported)
   str(dframe)
   nrow_maxord=nrow(dframe[dframe\$V1==max(dframe\$V1),])
   maxord=max(dframe\$V1)
   ifelse(nrow_maxord==1, (dframe=na.omit(subset(dframe[dframe\$V1 < maxord,]))), (dframe))
   cat('plotted dframe \n')
   nord=c(1:max(dframe\$V1))
   #search for negative values of drop, replacing them with 0.1 values 
   dframe\$V2[(dframe\$V2 < 0)]<-0.1
   tmp<-dframe
   #search for zero values of drop, replacing them with 0.1 values
   tmp\$V2[dframe\$V2==0]<-0.1
   dframe<-tmp
   delta=c()
   for(i in nord)
	{
	offset=(qt(0.025,nrow(dframe[dframe\$V1==i,])-1,lower.tail=FALSE)*(sd(log(dframe\$V2[dframe\$V1==i])))/sqrt(nrow(dframe[dframe\$V1==i,])))/(mean	(log(dframe\$V2[dframe\$V1==i])))
	delta=c(delta,offset)

	}
   delta=delta[delta<0.5]
   delta<-data.frame(na.omit(delta))
   dframe<-data.frame(na.omit(dframe[dframe\$V1 <= (nrow(delta)),]))
   print(dframe)
   cat('plotted input dataframe \n')
   linear_regr=summary(lm(dframe\$V2~dframe\$V1))
   print(linear_regr)
   cat('plotted linear regression output \n')
   t=linear_regr\$coefficients[2,3]
   Pr=linear_regr\$coefficients[2,4]
   Radj=linear_regr\$adj.r.squared
   library(agricolae)
   wer_t=waerden.test(dframe\$V2,dframe\$V1,group=F)
   print(wer_t)
   cat('plotted Van der Waerden test output \n')
   sink(file=\"tmpfile\")
   waerden.test(dframe\$V2,dframe\$V1,group=F)
   sink()
   Pval=try(system(\"cat tmpfile | grep Pvalue | cut -f2 -d' '\", intern=TRUE))
   system(\"rm tmpfile\")
   Pval<-as.numeric(Pval)
   out_row<-as.numeric(c(\"$j\",t,Pr,Radj,Pval))
   cat('plotting values: threshold, t, Pr, Radj, Pval \n')
   print(out_row)
   write(out_row,file='results\_$j',ncolumns=5,sep='\t')
   " > R_temp

   echo 'source ("R_temp")' | R --vanilla --slave

   rm R_temp

done

rm $result
rm thrVSmaxord

echo "threshold	t	Pr	Radj	Pvalue">$result
echo "threshold	maxord">thrVSmaxord

for k in $thresholds
do
   cat results_$k >> $result
   rm results_$k

   cat thrVSmaxord_$k >> thrVSmaxord
   rm thrVSmaxord_$k
done

echo "plotting results..."
cat $result

echo "
thrVSmaxord=read.csv(\"thrVSmaxord\", sep = '\t', dec='.', header = F)
names(thrVSmaxord)[1]=\"Threshold\"
names(thrVSmaxord)[2]=\"Maxord\"
xgraph=read.csv(\"$result\", sep = '\t', dec='.', header = F)
names(xgraph)[1]=\"Threshold\"
names(xgraph)[2]=\"t_statistic\"
names(xgraph)[3]=\"Pr\"
names(xgraph)[4]=\"R_squared_adj\"
names(xgraph)[5]=\"Pvalue\"

pdf('waerden_test.pdf')
print(matplot(xgraph\$Threshold, xgraph[, c(\"Pvalue\")], type=\"l\", col=\"red\", lwd=3, lty=1, ylab=\"Pvalue\", pch=1))
dev.off()

pdf('linear_regression.pdf')
print(matplot(xgraph\$Threshold, xgraph[, c(\"Pr\")], type=\"l\", col=\"green\", lwd=3, lty=1, ylab=\"Pr\", pch=1))
dev.off()

pdf('all_tests.pdf')
print(matplot(xgraph\$Threshold, xgraph[, c(\"Pr\",\"Pvalue\")], type=\"b\", lwd=3, lty=1, ylab=\"(1)Pr, (2)Pvalue\"))
dev.off()

pdf('thrVSmaxord.pdf')
print(matplot(thrVSmaxord\$Threshold, thrVSmaxord[, c(\"Maxord\")], type=\"l\", col=\"blue\", lwd=3, lty=1, ylab=\"Maxord\", pch=1))
dev.off()

" > R_temp

echo 'source ("R_temp")' | R --vanilla --slave

rm R_temp


