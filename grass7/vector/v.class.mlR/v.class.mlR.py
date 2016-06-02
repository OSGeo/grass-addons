#!/usr/bin/env python
############################################################################
#
# MODULE:       v.class.mlR
# AUTHOR:       Moritz Lennert
# PURPOSE:      Provides supervised machine learning based classification
#               (using support vector machine from R package e1071)
#
# COPYRIGHT:    (c) 2015 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Provides supervised support vector machine classification
#% keyword: classification
#% keyword: machine learning
#% keyword: R
#% keyword: classifiers
#%end
#%option G_OPT_V_MAP
#% key: segments_map
#% label: Vector map with areas to be classified
#% description: Vector map containing all areas and relevant attributes
#% required: no
#% guisection: Vector input
#%end
#%option G_OPT_V_INPUT
#% key: training_map
#% label: Vector map with training areas
#% description: Vector map with training areas and relevant attributes
#% required: no
#% guisection: Vector input
#%end
#%option G_OPT_F_INPUT
#% key: segments_file
#% label: File containing statistics of all segments
#% description: File containing relevant attributes for all areas
#% required: no
#% guisection: Text input
#%end
#%option G_OPT_F_INPUT
#% key: training_file
#% label: File containing statistics of training segments
#% description: File containing relevant attributes for training areas
#% required: no
#% guisection: Text input
#%end
#%option G_OPT_R_INPUT
#% key: raster_segments_map
#% label: Raster map with segments
#% description: Input raster map containing all segments
#% required: no
#% guisection: Raster maps
#%end
#%option G_OPT_R_OUTPUT
#% key: classified_map
#% label: Prefix for raster maps (one per weighting mode) with classes attributed to pixels
#% description: Output raster maps (one per weighting mode) in which all pixels are reclassed to the class attributed to the segment they belong to
#% required: no
#% guisection: Raster maps
#%end
#%option
#% key: train_class_column
#% type: string
#% description: Name of attribute column containing training classification
#% required: yes
#%end
#%option
#% key: output_class_column
#% type: string
#% description: Prefix of column with final classification
#% required: yes
#% answer: vote
#%end
#%option
#% key: output_prob_column
#% type: string
#% description: Prefix of column with probability of classification
#% required: yes
#% answer: prob
#%end
#%option
#% key: classifiers
#% type: string
#% description: Classifiers to use
#% required: yes
#% multiple: yes
#% options: svmRadial,rf,rpart,knn,knn1
#% answer: svmRadial,rf,rpart,knn,knn1
#%end
#%option
#% key: weighting_modes
#% type: string
#% description: Type of weighting to use
#% required: yes
#% multiple: yes
#% options: smv,swv,bwwv,qbwwv
#% answer: smv
#%end
#%option G_OPT_F_OUTPUT
#% key: classification_results
#% description: File for saving results of all classifiers
#% required: no
#% guisection: Optional output
#%end
#%option G_OPT_F_OUTPUT
#% key: accuracy_file
#% description: File for saving accuracy measures of classifiers
#% required: no
#% guisection: Optional output
#%end
#%option G_OPT_F_OUTPUT
#% key: bw_plot_file
#% description: PNG file for saving box-whisker plot of classifier performance
#% required: no
#% guisection: Optional output
#%end
#%option G_OPT_F_OUTPUT
#% key: r_script_file
#% description: File containing R script
#% required: no
#% guisection: Optional output
#%end
#%flag
#% key: f
#% description: Only write results to text file, do not update vector map
#%end
#%flag
#% key: i
#% description: Include individual classifier results in output
#%end
#
#%rules
#% required: segments_map,segments_file
#% required: training_map,training_file
#% requires: classified_map,raster_segments_map
#%end

import atexit
import subprocess
import os, shutil
import grass.script as gscript

def cleanup():

    if allmap:
        gscript.try_remove(feature_vars)
    if trainmap:
        gscript.try_remove(training_vars)
    gscript.try_remove(model_output)
    gscript.try_remove(model_output_desc)
    gscript.try_remove(r_commands)
    if reclass_files:
        for reclass_file in reclass_files.itervalues():
            gscript.try_remove(reclass_file)
    if temptable:
        gscript.run_command('db.droptable',
                            table=temptable,
                            flags='f',
                            quiet=True)

def main():

    global allmap
    global trainmap
    global feature_vars
    global training_vars
    global model_output
    global model_output_desc
    global temptable
    global r_commands
    global reclass_files

    allmap  =  trainmap  =  feature_vars  =  training_vars = None 
    model_output = model_output_desc  =  temptable  =  r_commands = None
    reclass_files = None

    voting_function = "voting <- function (x, w) {\n"
    voting_function += "res <- tapply(w, x, sum, simplify = TRUE)\n"
    voting_function += "maj_class <- as.numeric(names(res)[which.max(res)])\n"
    voting_function += "prob <- as.numeric(res[which.max(res)])\n"
    voting_function += "return(list(maj_class=maj_class, prob=prob))\n}"

    weighting_functions = {}
    weighting_functions['smv'] = "weights <- rep(1/length(accuracy_means), length(accuracy_means))"
    weighting_functions['swv'] = "weights <- accuracy_means/sum(accuracy_means)"
    weighting_functions['bwwv'] = "weights <- 1-(max(accuracy_means) - accuracy_means)/(max(accuracy_means) - min(accuracy_means))"
    weighting_functions['qbwwv'] = "weights <- ((min(accuracy_means) - accuracy_means)/(max(accuracy_means) - min(accuracy_means)))**2"

    if options['segments_map']:
        allfeatures = options['segments_map']
        allmap = True
    else:
        allfeatures = options['segments_file']
        allmap = False
    
    if options['training_map']:
        training = options['training_map']
        trainmap = True
    else:
        training = options['training_file']
        trainmap = False
    
    classcol = options['train_class_column']
    output_classcol = options['output_class_column']
    output_probcol = None
    if options['output_prob_column']:
        output_probcol = options['output_prob_column']
    classifiers = options['classifiers'].split(',')
    weighting_modes = options['weighting_modes'].split(',')

    classification_results = None
    if options['classification_results']:
        classification_results = options['classification_results']
    if flags['f'] and not classification_results:
        gscript.fatal("A classification_results file is necessary for flag 'f'")

    raster_segments_map = None
    if options['raster_segments_map']:
        raster_segments_map = options['raster_segments_map']

    classified_map = None
    if options['classified_map']:
        classified_map = options['classified_map']

    r_script_file = None
    if options['r_script_file']:
        r_script_file = options['r_script_file']

    accuracy_file = None
    if options['accuracy_file']:
        accuracy_file = options['accuracy_file']

    bw_plot_file = None
    if options['bw_plot_file']:
        bw_plot_file = options['bw_plot_file']

    if allmap:
        feature_vars = gscript.tempfile()
        gscript.run_command('v.db.select',
                            map_=allfeatures,
                            file_=feature_vars,
                            quiet=True,
                            overwrite=True)
    else:
        feature_vars = allfeatures

    if trainmap:
        training_vars = gscript.tempfile()
        gscript.run_command('v.db.select',
                            map_=training,
                            file_=training_vars,
                            quiet=True,
                            overwrite=True)
    else:
        training_vars = training

    r_commands = gscript.tempfile()

    r_file = open(r_commands, 'w')

    install = "if(!is.element('caret', installed.packages()[,1])){\n"
    install += "cat('\\n\\nInstalling caret package from CRAN\n')\n"
    install += "if(!file.exists(Sys.getenv('R_LIBS_USER'))){\n"
    install += "dir.create(Sys.getenv('R_LIBS_USER'), recursive=TRUE)\n"
    install += ".libPaths(Sys.getenv('R_LIBS_USER'))}\n"
    install += "chooseCRANmirror(ind=1)\n"
    install += "install.packages('caret')}"
    r_file.write(install)
    r_file.write("\n")
    r_file.write("\n")
    r_file.write('require(caret)')
    r_file.write("\n")
    r_file.write("cat('\\nRunning R...\\n')")
    r_file.write("\n")
    r_file.write('features <- read.csv("%s", sep="|", header=TRUE, row.names=1)' % feature_vars)
    r_file.write("\n")
    r_file.write('training <- read.csv("%s", sep="|", header=TRUE, row.names=1)' % training_vars)
    r_file.write("\n")
    r_file.write("training$%s <- as.factor(training$%s)" % (classcol, classcol))
    r_file.write("\n")
    r_file.write("MyFolds.cv <- createMultiFolds(training$%s, k=5, times=10)" % classcol)
    r_file.write("\n")
    r_file.write("MyControl.cv <- trainControl(method='repeatedCV', index=MyFolds.cv)")
    r_file.write("\n")
    r_file.write("fmla <- %s ~ ." % classcol)
    r_file.write("\n")
    r_file.write("models.cv <- list()")
    r_file.write("\n")
    for classifier in classifiers:
        if classifier == 'knn1':
            r_file.write("Grid <- expand.grid(k=1)")
            r_file.write("\n")
            r_file.write("knn1Model.cv <- train(fmla, training, method='knn', trControl=MyControl.cv, tuneGrid=Grid)")
            r_file.write("\n")
            r_file.write("models.cv$knn1 <- knn1Model.cv")
            r_file.write("\n")
        else:
            r_file.write("%sModel.cv <- train(fmla,training,method='%s', trControl=MyControl.cv,tuneLength=10)" % (classifier, classifier))
            r_file.write("\n")
            r_file.write("models.cv$%s <- %sModel.cv" % (classifier, classifier))
            r_file.write("\n")

    r_file.write("resamps.cv <- resamples(models.cv)")
    r_file.write("\n")
    r_file.write("accuracy_means <- as.vector(apply(resamps.cv$values[seq(2,length(resamps.cv$values), by=2)], 2, mean))")
    r_file.write("\n")
    r_file.write("kappa_means <- as.vector(apply(resamps.cv$values[seq(3,length(resamps.cv$values), by=2)], 2, mean))")
    r_file.write("\n")
    r_file.write("predicted <- data.frame(predict(models.cv, features))")
    r_file.write("\n")
    if flags['i']:
        r_file.write("resultsdf <- data.frame(id=rownames(features), predicted)")
    else:
        r_file.write("resultsdf <- data.frame(id=rownames(features))")
    r_file.write("\n")
    r_file.write(voting_function)
    r_file.write("\n")

    for weighting_mode in weighting_modes:
        r_file.write(weighting_functions[weighting_mode])
        r_file.write("\n")
        r_file.write("weights <- weights / sum(weights)")
        r_file.write("\n")
        r_file.write("vote <- apply(predicted, 1, voting, w=weights)")
        r_file.write("\n")
        r_file.write("vote <- as.data.frame(matrix(unlist(vote), ncol=2, byrow=TRUE))")
        r_file.write("\n")
        r_file.write("resultsdf$%s_%s <- vote$V1" % (output_classcol, weighting_mode))
        r_file.write("\n")
        r_file.write("resultsdf$%s_%s <- vote$V2" % (output_probcol, weighting_mode))
        r_file.write("\n")

    if allmap and not flags['f']:
        model_output = '.gscript_tmp_model_output_%d.csv' % os.getpid()
        write_string = "write.csv(resultsdf, '%s'," % model_output
        write_string += " row.names=FALSE, quote=FALSE)"
        r_file.write(write_string)
        r_file.write("\n")
    if classified_map:
        reclass_files = {}
        for weighting_mode in weighting_modes:
            reclass_files[weighting_mode] = gscript.tempfile()
            r_file.write("tempdf <- data.frame(resultsdf$id, resultsdf$%s_%s)" % (output_classcol, weighting_mode))
            r_file.write("\n")
            r_file.write("reclass <- data.frame(out=apply(tempdf, 1, function(x) paste(x[1],'=', x[2])))")
            r_file.write("\n")
            r_file.write("write.table(reclass$out, '%s', col.names=FALSE, row.names=FALSE, quote=FALSE)" % reclass_files[weighting_mode])
            r_file.write("\n")

    if classification_results:
        r_file.write("write.csv(resultsdf, '%s', row.names=FALSE, quote=FALSE)" % classification_results)
        r_file.write("\n")
    if accuracy_file:
        r_file.write("df_means <- data.frame(method=names(resamps.cv$methods),accuracy=accuracy_means, kappa=kappa_means)")
        r_file.write("\n")
        r_file.write("write.csv(df_means, '%s', row.names=FALSE, quote=FALSE)" % accuracy_file)
        r_file.write("\n")
    if bw_plot_file:
        r_file.write("png('%s.png')" % bw_plot_file)
        r_file.write("\n")
        r_file.write("print(bwplot(resamps.cv))")
        r_file.write("\n")
        r_file.write("dev.off()")
    r_file.close()

    if r_script_file:
        shutil.copy(r_commands, r_script_file)

    subprocess.call(['Rscript', r_commands], stdout=open(os.devnull, 'wb'))

    if allmap and not flags['f']:

        model_output_desc = model_output + 't'
        temptable = 'classif_tmp_table_%d' % os.getpid()

        f = open(model_output_desc, 'w')
        header_string = '"Integer"'
        if flags['i']:
            for model in classifiers:
                header_string += ',"Integer"'
        for weighting_mode in weighting_modes:
            header_string += ',"Integer"'
            header_string += ',"Real"'
        f.write(header_string)
        f.close()

    	gscript.message("Loading results into attribute table")
	gscript.run_command('db.in.ogr',
                            input_=model_output,
                            output=temptable,
                            overwrite=True,
                            quiet=True)
        index_creation = "CREATE INDEX idx_%s_cat" % temptable
        index_creation += " ON %s (id)" % temptable
        gscript.run_command('db.execute',
                            sql=index_creation,
                            quiet=True)
        columns = gscript.read_command('db.columns',
                                       table=temptable).splitlines()[1:]
	gscript.run_command('v.db.join',
                            map_=allfeatures,
                            column='cat',
			    otable=temptable,
                            ocolumn='id', 
			    subset_columns=columns,
                            quiet=True)

    if classified_map:
        for weighting_mode, reclass_file in reclass_files.iteritems():
            output_map = classified_map + '_' + weighting_mode
            gscript.run_command('r.reclass',
                                input=raster_segments_map,
                                output=output_map,
                                rules=reclass_file,
                                quiet=True)




if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
