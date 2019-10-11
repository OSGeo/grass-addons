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
# References:
#Moreno-Seco, F. et al. (2006), Comparison of Classifier Fusion Methods for
#Classification in Pattern Recognition Tasks. In D.-Y. Yeung et al., eds.
#Structural, Syntactic, and Statistical Pattern Recognition. Lecture Notes in
#Computer Science. Springer Berlin Heidelberg, pp. 705-713,
#http://dx.doi.org/10.1007/11815921_77</a>.
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
#%option G_OPT_V_FIELD
#% key: segments_layer
#% label: Layer of the segments map where attributes are stored
#% required: no
#% answer: 1
#% guisection: Vector input
#%end
#%option G_OPT_V_INPUT
#% key: training_map
#% label: Vector map with training areas
#% description: Vector map with training areas and relevant attributes
#% required: no
#% guisection: Vector input
#%end
#%option G_OPT_V_FIELD
#% key: training_layer
#% label: Layer of the training map where attributes are stored
#% required: no
#% answer: 1
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
#%option G_OPT_F_SEP
#% description: Field separator in input text files
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
#% options: svmRadial,svmLinear,svmPoly,rf,rpart,C5.0,knn,knn1,xgbTree
#% answer: svmRadial,rf
#%end
#%option
#% key: folds
#% type: integer
#% description: Number of folds to use for cross-validation
#% required: yes
#% answer: 5
#% guisection: Cross-validation and voting
#%end
#%option
#% key: partitions
#% type: integer
#% description: Number of different partitions to use for cross-validation
#% required: yes
#% answer: 10
#% guisection: Cross-validation and voting
#%end
#%option
#% key: tunelength
#% type: integer
#% description: Number of levels to test for each tuning parameter
#% required: yes
#% answer: 10
#% guisection: Cross-validation and voting
#%end
#%option
#% key: tunegrids
#% type: string
#% description: Python dictionary of customized tunegrids
#% required: no
#% guisection: Cross-validation and voting
#%end
#%option
#% key: weighting_modes
#% type: string
#% description: Type of weighting to use
#% required: yes
#% multiple: yes
#% options: smv,swv,bwwv,qbwwv
#% answer: smv
#% guisection: Cross-validation and voting
#%end
#%option
#% key: weighting_metric
#% type: string
#% description: Metric to use for weighting
#% required: yes
#% options: accuracy,kappa
#% answer: accuracy
#% guisection: Cross-validation and voting
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
#% key: model_details
#% description: File for saving details about the classifier module runs
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
#%option
#% key: processes
#% type: integer
#% description: Number of processes to run in parallel
#% answer: 1
#%end
#%flag
#% key: f
#% description: Only write results to text file, do not update vector map
#% guisection: Optional output
#%end
#%flag
#% key: i
#% description: Include individual classifier results in output
#% guisection: Optional output
#%end
#
#%rules
#% required: segments_map,segments_file
#% exclusive: segments_map,segments_file
#% required: training_map,training_file
#% exclusive: training_map,training_file
#% requires: classified_map,raster_segments_map
#% requires: -f,classification_results
#%end

import atexit
import subprocess
import os, shutil
from ast import literal_eval
import grass.script as gscript

def cleanup():

    if allmap:
        gscript.try_remove(feature_vars)
    if trainmap:
        gscript.try_remove(training_vars)
    if model_output_csv:
        gscript.try_remove(model_output_csv)
    if model_output_csvt:
        gscript.try_remove(model_output_csvt)
    if r_commands:
        gscript.try_remove(r_commands)
    if reclass_files:
        for reclass_file in reclass_files.values():
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
    global model_output_csv
    global model_output_csvt
    global temptable
    global r_commands
    global reclass_files

    allmap  =  trainmap  =  feature_vars  =  training_vars = None 
    model_output_csv = model_output_csvt  =  temptable  =  r_commands = None
    reclass_files = None

    voting_function = "voting <- function (x, w) {\n"
    voting_function += "res <- tapply(w, x, sum, simplify = TRUE)\n"
    voting_function += "maj_class <- as.numeric(names(res)[which.max(res)])\n"
    voting_function += "prob <- as.numeric(res[which.max(res)])\n"
    voting_function += "return(list(maj_class=maj_class, prob=prob))\n}"

    weighting_functions = {}
    weighting_functions['smv'] = "weights <- rep(1/length(weighting_base), length(weighting_base))"
    weighting_functions['swv'] = "weights <- weighting_base/sum(weighting_base)"
    weighting_functions['bwwv'] = "weights <- 1-(max(weighting_base) - weighting_base)/(max(weighting_base) - min(weighting_base))"
    weighting_functions['qbwwv'] = "weights <- ((min(weighting_base) - weighting_base)/(max(weighting_base) - min(weighting_base)))**2"

    packages = {'svmRadial': ['kernlab'], 'svmLinear': ['kernlab'], 'svmPoly': ['kernlab'], 'rf': ['randomForest'], 'rpart': ['rpart'], 'C5.0': ['C50'], 'xgbTree': ['xgboost', 'plyr']}

    install_package = "if(!is.element('%s', installed.packages()[,1])){\n"
    install_package += "cat('\\n\\nInstalling %s package from CRAN\n')\n"
    install_package += "if(!file.exists(Sys.getenv('R_LIBS_USER'))){\n"
    install_package += "dir.create(Sys.getenv('R_LIBS_USER'), recursive=TRUE)\n"
    install_package += ".libPaths(Sys.getenv('R_LIBS_USER'))}\n"
    install_package += "chooseCRANmirror(ind=1)\n"
    install_package += "install.packages('%s', dependencies=TRUE)}"

    if options['segments_map']:
        allfeatures = options['segments_map']
        segments_layer = options['segments_layer']
        allmap = True
    else:
        allfeatures = options['segments_file']
        allmap = False
    
    if options['training_map']:
        training = options['training_map']
        training_layer = options['training_layer']
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
    weighting_metric = options['weighting_metric']
    processes = int(options['processes'])
    folds = options['folds']
    partitions = options['partitions']
    tunelength = options['tunelength']
    separator = gscript.separator(options['separator'])
    tunegrids = literal_eval(options['tunegrids']) if options['tunegrids'] else {}

    classification_results = None
    if options['classification_results']:
        classification_results = options['classification_results'].replace("\\", "/")

    model_details = None
    if options['model_details']:
        model_details = options['model_details'].replace("\\", "/")

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
        accuracy_file = options['accuracy_file'].replace("\\", "/")

    bw_plot_file = None
    if options['bw_plot_file']:
        bw_plot_file = options['bw_plot_file'].replace("\\", "/")

    if allmap:
        feature_vars = gscript.tempfile().replace("\\", "/")
        gscript.run_command('v.db.select',
                            map_=allfeatures,
                            file_=feature_vars,
                            layer=segments_layer,
                            quiet=True,
                            overwrite=True)
    else:
        feature_vars = allfeatures.replace("\\", "/")

    if trainmap:
        training_vars = gscript.tempfile().replace("\\", "/")
        gscript.run_command('v.db.select',
                            map_=training,
                            file_=training_vars,
                            layer=training_layer,
                            quiet=True,
                            overwrite=True)
    else:
        training_vars = training.replace("\\", "/")

    r_commands = gscript.tempfile().replace("\\", "/")

    r_file = open(r_commands, 'w')

    if processes > 1:
        install = install_package % ('doParallel', 'doParallel', 'doParallel')
        r_file.write(install)
        r_file.write("\n")

    # automatic installation of missing R packages
    install = install_package % ('caret', 'caret', 'caret')
    r_file.write(install)
    r_file.write("\n")
    install = install_package % ('e1071', 'e1071', 'e1071')
    r_file.write(install)
    r_file.write("\n")
    for classifier in classifiers:
        # knn is included in caret
        if classifier == "knn" or classifier == "knn1":
            continue        
        for package in packages[classifier]:
            install = install_package % (package, package, package)
            r_file.write(install)
            r_file.write("\n")
    r_file.write("\n")
    r_file.write('require(caret)')
    r_file.write("\n")
    r_file.write('features <- read.csv("%s", sep="%s", header=TRUE, row.names=1)' % (feature_vars, separator))
    r_file.write("\n")
    r_file.write('training <- read.csv("%s", sep="%s", header=TRUE, row.names=1)' % (training_vars, separator))
    r_file.write("\n")
    r_file.write("training$%s <- as.factor(training$%s)" % (classcol, classcol))
    r_file.write("\n")
    if processes > 1:
        r_file.write("library(doParallel)")
        r_file.write("\n")
        r_file.write("registerDoParallel(cores = %d)" % processes)
        r_file.write("\n")
    r_file.write("MyFolds.cv <- createMultiFolds(training$%s, k=%s, times=%s)" %
            (classcol, folds, partitions))
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
            if classifier in tunegrids:
                r_file.write("Grid <- expand.grid(%s)" % tunegrids[classifier])
                r_file.write("\n")
                r_file.write("%sModel.cv <- train(fmla,training,method='%s', trControl=MyControl.cv, tuneGrid=Grid)" % (classifier,
                            classifier))
            else:
                r_file.write("%sModel.cv <- train(fmla,training,method='%s', trControl=MyControl.cv, tuneLength=%s)" % (classifier,
                            classifier, tunelength))
            r_file.write("\n")
            r_file.write("models.cv$%s <- %sModel.cv" % (classifier, classifier))
            r_file.write("\n")

    r_file.write("if (length(models.cv)>1) {")
    r_file.write("\n")
    r_file.write("resamps.cv <- resamples(models.cv)")
    r_file.write("\n")
    r_file.write("accuracy_means <- as.vector(apply(resamps.cv$values[seq(2,length(resamps.cv$values), by=2)], 2, mean))")
    r_file.write("\n")
    r_file.write("kappa_means <- as.vector(apply(resamps.cv$values[seq(3,length(resamps.cv$values), by=2)], 2, mean))")
    r_file.write("\n")
    r_file.write("} else {")
    r_file.write("\n")
    r_file.write("resamps.cv <- models.cv[[1]]$resample")
    r_file.write("\n")
    r_file.write("accuracy_means <- mean(resamps.cv$Accuracy)")
    r_file.write("\n")
    r_file.write("kappa_means <- mean(resamps.cv$Kappa)")
    r_file.write("\n")
    r_file.write("}")
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

    if weighting_metric == 'kappa':
        r_file.write("weighting_base <- kappa_means")
    else:
        r_file.write("weighting_base <- accuracy_means")
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
        if len(classifiers) > 1:
            r_file.write("resultsdf$%s_%s <- vote$V2" % (output_probcol, weighting_mode))
            r_file.write("\n")

    if allmap and not flags['f']:
        model_output = gscript.tempfile().replace("\\", "/")
        model_output_csv = model_output + '.csv'
        write_string = "write.csv(resultsdf, '%s'," % model_output_csv
        write_string += " row.names=FALSE, quote=FALSE)"
        r_file.write(write_string)
        r_file.write("\n")
    if classified_map:
        reclass_files = {}
        if flags['i']:
            for classifier in classifiers:
                tmpfilename = gscript.tempfile()
                reclass_files[classifier] = tmpfilename.replace("\\", "/")
                r_file.write("tempdf <- data.frame(resultsdf$id, resultsdf$%s)" % (classifier))
                r_file.write("\n")
                r_file.write("reclass <- data.frame(out=apply(tempdf, 1, function(x) paste(x[1],'=', x[2])))")
                r_file.write("\n")
                r_file.write("write.table(reclass$out, '%s', col.names=FALSE, row.names=FALSE, quote=FALSE)" % reclass_files[classifier])
                r_file.write("\n")
        for weighting_mode in weighting_modes:
            tmpfilename = gscript.tempfile()
            reclass_files[weighting_mode] = tmpfilename.replace("\\", "/")
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
        r_file.write("df_means <- data.frame(method=names(models.cv),accuracy=accuracy_means, kappa=kappa_means)")
        r_file.write("\n")
        r_file.write("write.csv(df_means, '%s', row.names=FALSE, quote=FALSE)" % accuracy_file)
        r_file.write("\n")
    if model_details:
        r_file.write("sink('%s')" % model_details)
        r_file.write("\n")
        r_file.write("cat('BEST TUNING VALUES\n')")
        r_file.write("\n")
        r_file.write("cat('******************************\n\n')")
        r_file.write("\n")
        r_file.write("lapply(models.cv, function(x) x$best)")
        r_file.write("\n")
        r_file.write("cat('\n')")
        r_file.write("\n")
        r_file.write("cat('\nSUMMARY OF RESAMPLING RESULTS\n')")
        r_file.write("\n")
        r_file.write("cat('******************************\n\n')")
        r_file.write("\n")
        r_file.write("summary(resamps.cv)")
        r_file.write("\n")
        r_file.write("cat('\n')")
        r_file.write("\n")
        r_file.write("cat('\nRESAMPLED CONFUSION MATRICES\n')")
        r_file.write("\n")
        r_file.write("cat('******************************\n\n')")
        r_file.write("\n")
        r_file.write("conf.mat.cv <- lapply(models.cv, function(x) confusionMatrix(x))")
        r_file.write("\n")
        r_file.write("print(conf.mat.cv)")
        r_file.write("\n")
        r_file.write("cat('\nDETAILED CV RESULTS\n')")
        r_file.write("\n")
        r_file.write("cat('******************************\n\n')")
        r_file.write("\n")
        r_file.write("lapply(models.cv, function(x) x$results)")
        r_file.write("\n")
        r_file.write("sink()")
        r_file.write("\n")

    if bw_plot_file and len(classifiers) > 1:
        r_file.write("png('%s.png')" % bw_plot_file)
        r_file.write("\n")
        r_file.write("print(bwplot(resamps.cv))")
        r_file.write("\n")
        r_file.write("dev.off()")
    r_file.close()

    if r_script_file:
        shutil.copy(r_commands, r_script_file)

    gscript.message("Running R now. Following output is R output.")
    try:
        subprocess.check_call(['Rscript', r_commands], stderr=subprocess.STDOUT, )
    except subprocess.CalledProcessError:
        gscript.fatal("There was an error in the execution of the R script.\nPlease check the R output.")

    gscript.message("Finished running R.")

    if allmap and not flags['f']:

        model_output_csvt = model_output + '.csvt'
        temptable = 'classif_tmp_table_%d' % os.getpid()

        f = open(model_output_csvt, 'w')
        header_string = '"Integer"'
        if flags['i']:
            for classifier in classifiers:
                header_string += ',"Integer"'
        if len(classifiers) > 1:
            for weighting_mode in weighting_modes:
                header_string += ',"Integer"'
                header_string += ',"Real"'
        else:
            header_string += ',"Integer"'

        f.write(header_string)
        f.close()

        gscript.message("Loading results into attribute table")
        gscript.run_command('db.in.ogr',
                            input_=model_output_csv,
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
        orig_cat = gscript.vector_db(allfeatures)[int(segments_layer)]['key']
        gscript.run_command('v.db.join',
                            map_=allfeatures,
                            column=orig_cat,
                            otable=temptable,
                            ocolumn='id', 
                            subset_columns=columns,
                            quiet=True)

    if classified_map:
        for classification, reclass_file in reclass_files.items():
            output_map = classified_map + '_' + classification
            gscript.run_command('r.reclass',
                                input=raster_segments_map,
                                output=output_map,
                                rules=reclass_file,
                                quiet=True)




if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
