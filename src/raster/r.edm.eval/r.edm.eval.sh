#!/bin/sh
#
#set -x
########################################################################
#
# MODULE:       r.model.eval
# AUTHOR(S):    Paulo van Breugel <paulo AT ecodiv.org>
# PURPOSE:      To evaluate how well a modeled distribution predicts an
#               observed distribution.
#
# NOTES:        The observed distribution of e.g., a species, land
#               cover unit or vegetation unit should be a binary map
#               with 1 (present) and 0 (absent). The values of the
#               modeled distribution can be any map that represents a
#               probability distribution in space. This could be based
#               on X, but it doesn't need to be. You can also, for example,
#               evaluate how well the modeled distribution of a species X
#               predicts the distribution of species Y or of land cover
#               type Y.
#
# Disclaimer:   Only limited testing has been done. Use at own risk
#
# COPYRIGHT: (C) 2014 Paulo van Breugel
#            http://ecodiv.org
#            http://pvanb.wordpress.com/
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Computes evaluation statistics of an environmental distribution model, based on a layer with observed and a layer with predicted values
# %End

# %option
# % key: obs
# % type: string
# % gisprompt: old,cell,raster
# % description: Observed distribution
# % key_desc: Raster name
# % required: yes
# % multiple: no
# %end

# %option
# % key: mod
# % type: string
# % gisprompt: old,cell,raster
# % description: Modeled distribution
# % key_desc: Raster name
# % required: yes
# % multiple: no
# %end

# %flag
# % key: b
# % description: add presence to background?
# %end

# %option
# % key: fstats
# % type: string
# % description: Name of output files (without extension)
# % key_desc: File name
# % required: yes
# % multiple: no
# %end

# %option
# % key: n_bins
# % type: integer
# % description: Number of bins in which to divide the modeled distribution scores
# % key_desc: integer
# % answer: 200
# % required: no
# %end

# %flag
# % key: l
# % description: print log file to file?
# %end

# %option
# % key: buffer_abs
# % type: integer
# % description: Restrict absence area to x km buffer
# % key_desc: buffer zone (km)
# % answer: 0
# % required: no
# % guisection: evaluation area
# %end

# %option
# % key: buffer_pres
# % type: integer
# % description: Restrict presence area to x km buffer
# % key_desc: buffer zone (km)
# % answer: 0
# % required: no
# % guisection: evaluation area
# %end

# %option
# % key: preval
# % type: string
# % description: Prevalence of presence points
# % key_desc: <0-1>
# % answer: 0
# % required: no
# % guisection: evaluation area
# %end

# %option
# % key: num_pres
# % type: integer
# % description: number of presence points (this will not work if preval > 0)
# % key_desc: integer
# % answer: 0
# % required: no
# % guisection: evaluation area
# %end

# %option
# % key: num_abs
# % type: integer
# % description: number of absence points (this will not work if preval > 0)
# % key_desc: integer
# % answer: 0
# % required: no
# % guisection: evaluation area
# %end

#=======================================================================
## GRASS team recommendations
#=======================================================================

## Check if in GRASS
if  [ -z "$GISBASE" ] ; then
    echo "You must be in GRASS GIS to run this program." 1>&2
    exit 1
fi

## check for awk
if [ ! -x "$(which awk)" ] ; then
    g.message -e "<awk> required, please install <awk> or <gawk> first"
    exit 1
fi

## To parse the code into interactive menu
if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi

## set environment so that awk works properly in all languages ##
unset LC_ALL
export LC_NUMERIC=C


## what to do in case of user break:
exitprocedure()
{
    echo "User break!"
    cleanup
    exit 1
}

## shell check for user break (signal list: trap -l)
trap "exitprocedure" 2 3 15

#=======================================================================
## Config and general procedures
#=======================================================================

##fix this path
if [ -z "$PROCESSDIR" ] ; then
	PROCESSDIR="$HOME"
fi

#=======================================================================
# test for missing input raster maps
#=======================================================================

oIFS=$IFS
IFS=,
arrIN=${GIS_OPT_OBS} `echo $nvar | awk 'BEGIN{FS="@"}{print $1}'`
g.findfile element=cell file=${arrIN} > /dev/null
if [ $? -gt 0 ] ; then
    g.message -e 'The output map '${arrIN}' does not exists'
exit 1
fi
unset arrIN

arrIN=${GIS_OPT_MOD} `echo $nvar | awk 'BEGIN{FS="@"}{print $1}'`
g.findfile element=cell file=${arrIN} > /dev/null
if [ $? -gt 0 ] ; then
    g.message -e 'The output map '${arrIN}' does not exists'
exit 1
fi
IFS=$oIFS
unset arrIN

#=======================================================================
## Creating the R script
#=======================================================================

writeScript(){
cat > $1 << "EOF"

options(echo = TRUE)
library(rgrass7)
library(reshape)
library(caTools)

# Define required functions
get_output.GRASS <- function(x, separator=",", h=FALSE){
      con <- textConnection(x)
      MyVar <- read.table(con, header=h, sep=separator, comment.char="")
      close(con)
      return(MyVar)
}

rand.name <- function(base="tmp", l=6){
    paste(base,paste(sample(c(0:9, letters, LETTERS), l, replace=TRUE), collapse=""), sep="_")
}

copy_rast.GRASS <- function(rast, remove.orig=FALSE){
    mpst <- gmeta()$MAPSET
    fft <- execGRASS("g.findfile", flags="quiet", element="cell", file=rast, mapset=mpst, Sys_ignore.stdout=TRUE)
    if(fft==0){
        rname <- rand.name()
        execGRASS("g.copy", raster=paste(rast, rname, sep=","))
        if(remove.orig){execGRASS("g.remove", flags="f", type="raster", name=rast)}
        return(rname)
    }else{
        print("the selected file does not exist")
    }
}

## Get vector with variables
obsmap <- Sys.getenv("GIS_OPT_OBS")
distmod <- Sys.getenv("GIS_OPT_MOD")
n.bins <- as.numeric(Sys.getenv("GIS_OPT_N_BINS"))
bufabs <- as.numeric(Sys.getenv("GIS_OPT_BUFFER_ABS"))
bufpres <- as.numeric(Sys.getenv("GIS_OPT_BUFFER_PRES"))
fnames <- Sys.getenv("GIS_OPT_FSTATS")
num.pres <- Sys.getenv("GIS_OPT_NUM_PRES")
num.abs <- Sys.getenv("GIS_OPT_NUM_ABS")
preval <- as.numeric(Sys.getenv("GIS_OPT_PREVAL"))
print.log <- as.numeric(Sys.getenv("GIS_FLAG_L"))
backgr <- as.numeric(Sys.getenv("GIS_FLAG_B"))

# Create buffer map with buffer width of bufabs (outside) or bufpres (inside)
if(bufabs>0){
    tmp.a <- "tmp_r_model_evaluation_0987654321a"
    tmp.b <- "tmp_r_model_evaluation_0987654321b"
	execGRASS("r.mapcalc", flags="overwrite", expression=paste(tmp.a, obsmap, sep=" = "))
	execGRASS("r.null", map=tmp.a, setnull="0")
	execGRASS("r.buffer", input=tmp.a, output=tmp.b, distances=bufabs, units="kilometers")
	sink("reclass.rules"); cat("1:1:1:1"); cat("\n"); cat("2:2:0:0"); cat("\n"); sink()
    execGRASS("r.recode", flags="overwrite", input=tmp.b, output=tmp.a, rules="reclass.rules")
	obsmap <- tmp.a
	execGRASS("g.remove", flags="f", type="raster", name=tmp.b); unlink("reclass.rules")
}

if(bufpres>0){
    tmp.b <- "tmp_r_model_evaluation_0987654321b"
    tmp.c <- "tmp_r_model_evaluation_0987654321c"
    execGRASS("r.mapcalc", flags="overwrite", expression=paste(tmp.b," = if(", obsmap,"==1,0,null())", sep=""))
    execGRASS("r.buffer", flags=c("z","overwrite"), input=tmp.b, output=tmp.c, distances=bufpres, units="kilometers")
    execGRASS("r.mapcalc", flags="overwrite", expression=paste(tmp.b, " = if(", tmp.c, "==2,1,", obsmap, ")", sep=""))
    obsmap <- tmp.b
    execGRASS("g.remove", flags="f", type="raster", name=tmp.c)
}

# Prevalence
if(preval>0 & preval < 1){
    tmp.e <- "tmp_r_model_evaluation_0987654321e"
    tmp.f <- "tmp_r_model_evaluation_0987654321f"
    tmp.g <- "tmp_r_model_evaluation_0987654321g"
    tmp.h <- "tmp_r_model_evaluation_0987654321h"
    tmp.i <- "tmp_r_model_evaluation_0987654321i"
    pa_cnt <- execGRASS("r.univar", flags=c("t","g"), map=obsmap, zones=obsmap, intern=TRUE)
    pa_cnt <- get_output.GRASS(pa_cnt, separator="|", h=TRUE)[,c(1,3)]
    pres.req <- ceiling((pa_cnt[1,2] + pa_cnt[2,2]) * preval)
    abs.req <- ceiling((pa_cnt[1,2] + pa_cnt[2,2]) - pres.req)
    if(pres.req > pa_cnt[2,2]){
        pres.req <- pa_cnt[2,2]
        abs.req <- ceiling((pa_cnt[2,2] / preval) - pa_cnt[2,2])
    }
    if(abs.req > pa_cnt[1,2]){
        pres.req <- ceiling(pa_cnt[1,2]/abs.req*pres.req)
        abs.req <- pa_cnt[1,2]
    }
    execGRASS("r.mapcalc", expression=paste(tmp.e, " = if(", obsmap, "== 1,1, null())", sep=""), Sys_wait=TRUE)
    execGRASS("r.random", input=tmp.e, n=as.character(pres.req), raster_output=tmp.f, Sys_wait=TRUE)
    execGRASS("r.mapcalc", flags="overwrite", expression=paste(tmp.g, " = if(", obsmap, "==0,0,null())", sep=""), Sys_wait=TRUE)
    execGRASS("r.random", input=tmp.g, n=as.character(abs.req), raster_output=tmp.h, Sys_wait=TRUE)
    execGRASS("r.patch", input=paste(tmp.f, tmp.h, sep=","), output=tmp.i, flags="overwrite", Sys_wait=TRUE)
    obsmap <- tmp.i
    execGRASS("g.remove", flags="f", type="raster", name=paste(tmp.f, tmp.g, tmp.h, tmp.e, sep=","), Sys_wait=TRUE)
}else{
    # Set number of presence and absence points
    if(num.pres > 0 | num.abs > 0){
        pa_cnt <- execGRASS("r.univar", flags=c("t","g"), map=obsmap, zones=obsmap, intern=TRUE)
        pa_cnt <- get_output.GRASS(pa_cnt, separator="|", h=TRUE)[,c(1,3)]
        num.pres <- ifelse(num.pres >= pa_cnt[2,2], 0, num.pres)
        num.abs  <- ifelse(num.abs >= pa_cnt[1,2], 0, num.abs)
    }
    if(num.pres > 0){
        tmp.e <- "tmp_r_model_evaluation_0987654321e"
        tmp.f <- "tmp_r_model_evaluation_0987654321f"
        execGRASS("r.mapcalc", expression=paste(tmp.e, obsmap, sep=" = "), Sys_wait=TRUE)
        execGRASS("r.null", map=tmp.e, setnull="0", Sys_wait=TRUE)
        execGRASS("r.random", input=tmp.e, raster_output=tmp.f, n=as.character(num.pres), Sys_wait=TRUE)
    }
    if(num.abs > 0){
        tmp.g <- "tmp_r_model_evaluation_0987654321g"
        tmp.h <- "tmp_r_model_evaluation_0987654321h"
        execGRASS("r.mapcalc", expression=paste(tmp.g, obsmap, sep=" = "), Sys_wait=TRUE)
        execGRASS("r.null", map=tmp.g, setnull="1", Sys_wait=TRUE)
        execGRASS("r.random", input=tmp.g, raster_output=tmp.h, n=as.character(num.pres), Sys_wait=TRUE)
    }
    if(num.pres > 0 & num.abs == 0){
        tmp.h <- "tmp_r_model_evaluation_0987654321h"
        execGRASS("r.mapcalc", expression=paste(tmp.h, obsmap, sep=" = "), Sys_wait=TRUE)
        execGRASS("r.null", map=tmp.h, setnull="1", Sys_wait=TRUE)
    }
    if(num.abs > 0 & num.pres ==0){
        tmp.f <- "tmp_r_model_evaluation_0987654321f"
        execGRASS("r.mapcalc", expression=paste(tmp.f, obsmap, sep=" = "), Sys_wait=TRUE)
        execGRASS("r.null", map=tmp.f, setnull="0", Sys_wait=TRUE)
    }
    if(num.abs > 0 | num.pres > 0){
        tmp.j <- "tmp_r_model_evaluation_0987654321j"
        execGRASS("r.patch", input=paste(tmp.f, tmp.h, sep=","), output=tmp.j, flags="overwrite", Sys_wait=TRUE)
        obsmap <- tmp.j
        execGRASS("g.remove", flags="f", type="raster", name=paste(tmp.f, tmp.g, tmp.h, tmp.e, sep=","), Sys_wait=TRUE)
    }
}

# Create map with probability scores grouped in n.bins bins
a <- execGRASS("r.univar", flags="g", map=distmod, intern=TRUE)
maxmin <- get_output.GRASS(a, separator="=")
stps <- (maxmin[5,2] - maxmin[4,2])/n.bins
roc.st <- seq(maxmin[4,2], maxmin[5,2], by=stps)
x1 <- c(0,roc.st[-length(roc.st)])
x2 <- c(roc.st[1],roc.st[-1])
y1 <- seq(length(roc.st)-1,0,-1)
xy1 <- format(cbind(x1,x2,y1), scientific=F, trim=T, nsmall=12)
xy2 <- apply(xy1, 1, function(x){paste(x, collapse=":")})
tmp.rule <- tempfile(pattern = "file", tmpdir = tempdir(), fileext = ".rules")
write.table(xy2, file=tmp.rule, quote=F, row.names=F, col.names=F)
tmp.d <- "tmp_r_model_evaluation_0987654321d"
execGRASS("r.recode", flags="overwrite", input=distmod, output=tmp.d, rules=tmp.rule)
unlink(tmp.rule)

# Zonal stats
if(backgr == 0){
    # Based on presence / absence
    a <- execGRASS("r.stats", flags=c("c","n"), input=paste(obsmap, tmp.d, sep=","), intern=TRUE)
    a <- get_output.GRASS(a, separator=" ")
    execGRASS("g.remove", flags="f", type="raster", name=tmp.d)
}else{
    # Based on presence / background
    tmp.k <- "tmp_r_model_evaluation_0987654321k"
    execGRASS("r.mapcalc", flags="overwrite", expression=paste(tmp.k, obsmap, sep=" = "), Sys_wait=TRUE)
    execGRASS("r.null", map=tmp.k, setnull="0", Sys_wait=TRUE)
    a1 <- execGRASS("r.stats", flags=c("c","n"), input=paste(tmp.k, tmp.d, sep=","), intern=TRUE)
    a1 <- get_output.GRASS(a1, separator=" ")

    tmp.m <- "tmp_r_model_evaluation_0987654321m"
    execGRASS("r.mapcalc", flags="overwrite", expression=paste(tmp.m, obsmap, sep=" = "), Sys_wait=TRUE)
    execGRASS("r.null", map=tmp.m, setnull="1", Sys_wait=TRUE)
    a2 <- execGRASS("r.stats", flags=c("c","n"), input=paste(tmp.m, tmp.d, sep=","), intern=TRUE)
    a2 <- get_output.GRASS(a2, separator=" ")
    a3 <- cbind(a2[,-3],a1[,3] + a2[,3])
    names(a3) <- names(a1)
    a <- rbind(a1, a3)

    # Clean up
    execGRASS("g.remove", flags="f", type="raster", name=paste(tmp.k, tmp.m, sep=","))
}

# Clean up
execGRASS("g.remove", flags="f", type="raster", name=tmp.d)
if(bufabs>0){execGRASS("g.remove", flags="f", type="raster", name=tmp.a)}
if(bufabs>0){execGRASS("g.remove", flags="f", type="raster", name=tmp.b)}
if(preval>0){execGRASS("g.remove", flags="f", type="raster", name=tmp.i)}
if(num.abs > 0 | num.pres > 0){execGRASS("g.remove", flags="f", type="raster", name=tmp.j)}

# the temporary files do not always get cleaned up, need to check why
# this is a temporary fix!
aa <- execGRASS("g.list", type="raster", pattern="tmp_r_model_evaluation_*", intern=TRUE)
if(length(aa)>0){
    execGRASS("g.remove", type="raster", pattern="tmp_r_model_evaluation_*", flags="f")
}

# Calculate evaluation stats
a.cast <- cast(a, V2 ~ V1)
a.cast[] <- sapply(a.cast, function(x) replace(x,is.na(x),0))
a.sum <- apply(a.cast,2,sum)
a.stats <- cbind(a.cast,cumsum(a.cast[,2]),cumsum(a.cast[,3]))[,-c(2,3)]
names(a.stats) <- c("bin", "FP", "TP")
a.stats$TN <- a.sum[1]-a.stats$FP
a.stats$FN <- a.sum[2]-a.stats$TP
a.stats$TPR <- apply(a.stats,1,function(x){x[3]/(x[3]+x[5])})
a.stats$FPR <- apply(a.stats,1,function(x){x[2]/(x[2]+x[4])})
a.stats$TNR <- apply(a.stats,1,function(x){x[4]/(x[2]+x[4])})
a.stats$TSS <- apply(a.stats,1,function(x){x[6]+x[8]-1})
PRa <- apply(a.stats,1,function(x){(x[3]+x[4])/sum(x)})
Yobs <- apply(a.stats,1,function(x){(x[3]+x[5])/sum(x)})
Ymod <- apply(a.stats,1,function(x){(x[3]+x[2])/sum(x)})
PRe <- Yobs*Ymod + (1-Yobs)*(1-Ymod)
a.stats$kappa <- (PRa - PRe) / (1 - PRe)
n.presence <- a.stats$TP[2] + a.stats$FN[2]
n.absence <- a.stats$TN[2] + a.stats$FP[2]
prevalence <- n.presence / (n.presence + n.absence)

# Calculate threshold values
a.auc <- trapz(a.stats$FPR, a.stats$TPR)
a.TSS <- max(a.stats$TSS)
threshold.bin <- n.bins - a.stats[which.max(a.stats$TSS),1]
a.TSS_threshold <- x2[threshold.bin]
a.kappa_max  <- max(a.stats$kappa)
threshold.bin <- n.bins - a.stats[which.max(a.stats$kappa),1]
a.kappa_threshold <- x2[threshold.bin]

sink(paste(fnames, "summary.txt", sep="_"))
cat(paste("AUC", as.character(a.auc), sep=" = ")); cat("\n")
cat(paste("maximum TSS", a.TSS, sep=" = ")); cat("\n")
cat(paste("maximum TSS threshold", a.TSS_threshold, sep=" = ")); cat("\n")
cat(paste("maximum kappa", a.kappa_max, sep=" = ")); cat("\n")
cat(paste("maximum kappa threshold", a.kappa_threshold, sep=" = ")); cat("\n")
cat(paste("prevalence", prevalence, sep=" = ")); cat("\n")
cat(paste("presence points", n.presence, sep=" = ")); cat("\n")
cat(paste("absence points", n.absence, sep=" = ")); cat("\n")
cat(paste("stats txt file =", paste(fnames, "summary.txt", sep="_"))); cat("\n")
cat(paste("stats txt file =", paste(fnames, "stats.csv", sep="_"))); cat("\n")
if(print.log==1){
    cat(paste("log file =", paste(fnames, "log.txt", sep="_"))); cat("\n")
}
sink()
b.stats <- cbind(sort(x2[-length(x2)], decreasing=TRUE), a.stats)
names(b.stats) <- c("threshold", names(a.stats))
write.table(b.stats, file=paste(fnames, "stats.csv", sep="_"), append=TRUE, sep=";", row.names=FALSE)

EOF
}

# RGrass script generation
# --------------------------
RGRASSSCRIPT="`g.tempfile pid=$$`"
if [ $? -ne 0 ] || [ -z "$RGRASSSCRIPT" ] ; then
	g.message -e 'ERROR: unable to create temporary file for RGrass script' 1>&2
    exit 1
fi
writeScript "$RGRASSSCRIPT"


#=======================================================================
## RGrass call
#=======================================================================

# Message
g.message message='Working on it...'
g.message message='-----'
g.message message=''

#using R to create MESS layers
R CMD BATCH --slave "$RGRASSSCRIPT" ${GIS_OPT_FSTATS}_log.txt;

if  [ "$GIS_FLAG_L" -eq 0 ] ; then
    rm ${GIS_OPT_FSTATS}_log.txt
fi

head -11 ${GIS_OPT_FSTATS}_summary.txt

g.message message='-----'
g.message "Don't forget to check out the output files"

#=======================================================================
