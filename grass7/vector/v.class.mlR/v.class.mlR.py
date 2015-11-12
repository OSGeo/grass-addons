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
#% keyword: svm
#%end
#%option G_OPT_V_MAP
#% label: Vector map with areas to be classified
#% description: Vector map containing all areas and relevant attributes
#% required: yes
#%end
#%option G_OPT_V_INPUT
#% key: training
#% label: Vector map with training areas
#% description: Vector map with training areas and relevant attributes
#% required: yes
#%end
#%option
#% key: class_column
#% type: string
#% description: Name of attribute column containing training classification
#% required: yes
#%end
#%option
#% key: output_column
#% type: string
#% description: Name of column to create with final classification
#% required: yes
#%end
#%option
#% key: classifier
#% type: string
#% description: Classifier to use
#% required: yes
#% options: svm
#% answer: svm
#% end
#%option
#% key: kernel
#% type: string
#% description: Kernel to use
#% required: yes
#% options: linear,polynomial,radial,sigmoid
#% answer: linear
#% guisection: svm
#%end
#%option
#% key: cost
#% type: double
#% description: cost value
#% required: no
#% guisection: svm
#%end
#%option
#% key: degree
#% type: integer
#% description: degree value (for polynomial kernel)
#% required: no
#% guisection: svm
#%end
#%option
#% key: gamma
#% type: double
#% description: gamma value (for all kernels except linear)
#% required: no
#% guisection: svm
#%end
#%option
#% key: coeff0
#% type: double
#% description: coeff0 value (for polynomial and sigmoid kernels)
#% required: no
#% guisection: svm
#%end

import atexit
import subprocess
import os
import grass.script as grass

def cleanup():

    os.remove(feature_vars)
    os.remove(training_vars)
    os.remove(model_output)
    os.remove(model_output_desc)
    os.remove(r_commands)
    grass.run_command('db.droptable', table=temptable, flags='f', quiet=True)

def main():

    allfeatures = options['map']
    training = options['training']
    classcol = options['class_column']
    output_classcol = options['output_column']
    kernel = options['kernel']
    cost = options['cost']
    gamma = options['gamma']
    degree = options['degree']
    coeff0 = options['coeff0']

    global feature_vars
    global training_vars
    global model_output
    global model_output_desc
    global temptable
    global r_commands
    feature_vars = grass.tempfile()
    training_vars = grass.tempfile()
    model_output = '.grass_tmp_model_output_%d.csv' % os.getpid()
    model_output_desc = model_output + 't'
    temptable = 'classif_tmp_table_%d' % os.getpid()

    feature_vars_file = open(feature_vars, 'w')
    training_vars_file = open(training_vars, 'w')

    grass.run_command('v.db.select', map_=allfeatures, file_=feature_vars,
            quiet=True, overwrite=True)
    grass.run_command('v.db.select', map_=training, file_=training_vars,
            quiet=True, overwrite=True)

    feature_vars_file.close()
    training_vars_file.close()

    r_commands = grass.tempfile()

    r_file = open(r_commands, 'w')

    install = "if(!is.element('e1071', installed.packages()[,1])) "
    install += "{cat('\n\nInstalling e1071 package from CRAN\n\n')\n"
    install += "install.packages('e1071', "
    install += "repos='https://mirror.ibcp.fr/pub/CRAN/')}"
    r_file.write(install)
    r_file.write("\n")
    r_file.write('library(e1071)')
    r_file.write("\n")
    r_file.write("cat('\nRunning R to tune and apply model...\n')")
    r_file.write("\n")
    r_file.write('features<-read.csv("%s", sep="|", header=TRUE)' % feature_vars)
    r_file.write("\n")
    r_file.write("features<-features[sapply(features, function(x) !any(is.na(x)))]") 
    r_file.write("\n")
    r_file.write('training<-read.csv("%s", sep="|", header=TRUE)' % training_vars)
    r_file.write("\n")
    data_string = "training = data.frame(training[names(training)[names(training)"
    data_string += "%%in%% names(features)]], classe=training$%s)" % classcol
    r_file.write(data_string)
    r_file.write("\n")
    r_file.write("training$%s <- as.factor(training$%s)" % (classcol, classcol))
    r_file.write("\n")
    tune = True
    if kernel == 'linear' and cost:
        model_string = "model=svm(%s~., data=training[-1])" % classcol
        tune = False
    if kernel == 'polynomial' and cost and degree and gamma and coeff0:
        model_string = "model=svm(%s~., data=training[-1], " % classcol
        model_string += "cost = %f, " % cost
        model_string += "degree = %d, " % degree
        model_string += "gamma = %f, " % gamma
        model_string += "coeff0 = %f)" % coeff0
        tune = False
    if kernel == 'radial' and cost and gamma:
        model_string = "model=svm(%s~., data=training[-1], " % classcol
        model_string += "cost = %f, " % cost
        model_string += "gamma = %f)" % gamma
        tune = False
    if kernel == 'sigmoid' and cost and gamma and coeff0:
        model_string = "model=svm(%s~., data=training[-1], " % classcol
        model_string += "cost = %f, " % cost
        model_string += "gamma = %f, " % gamma
        model_string += "coeff0 = %f)" % coeff0
        tune = False
    if tune:
        model_string = "model=tune(svm, %s~., data=training[-1], " % classcol
        model_string += "nrepeat=10, "
        model_string += "sampling='cross', cross=10"
        model_string += ", kernel='%s'" % kernel
        if cost:
            model_string += ", cost = %s, " % cost
        if gamma:
            model_string += ", gamma = %s, " % gamma
        if degree:
            model_string += ", degree = %s, " % degree
        if coeff0:
            model_string += ", coeff0 = %s, " % coeff0
        if not cost or not gamma or not degree or not coeff0:
            model_string += ", ranges=list("
            first = True

            if not cost:
                model_string += "cost=c(0.01, 0.1, 1, 5, 10)"
                first = False

            if not gamma and not kernel == 'linear':
                if first:
                    model_string += "gamma=seq(0,0.5,0.1)"
                    first = False
                else:
                    model_string += ", gamma=seq(0,0.5,0.1)"

            if not degree and kernel == 'polynomial':
                if first:
                    model_string += "degree=seq(2,4,1)"
                    first = False
                else:
                    model_string += ", degree=seq(2,4,1)"

            if not coeff0 and (kernel == 'polynomial' or kernel == 'sigmoid'):
                if first:
                    model_string += "coeff0=seq(0,0.5,0.1)"
                else:
                    model_string += ", coeff0=seq(0,0.5,0.1)"

            model_string += "))"

    r_file.write(model_string)
    r_file.write("\n")
    r_file.write("cat('\nTuning (or model) summary: ')")
    r_file.write("\n")
    r_file.write("summary(model)")
    r_file.write("\n")
    if tune:
        r_file.write("%s=predict(model$best.model, features[-1])" % output_classcol)
    else:
        r_file.write("%s=predict(model, features[-1])" % output_classcol)

    r_file.write("\n")
    write_string = "write.csv(data.frame(cat=features$cat, %s), " % output_classcol
    write_string += "'%s', row.names=FALSE, quote=FALSE)" % model_output
    r_file.write(write_string)
    r_file.write("\n")
    r_file.close()

    subprocess.call(['Rscript', r_commands])

    f = open(model_output_desc, 'w')
    f.write('"Integer","Integer"\n')
    f.close()

    grass.message("Loading results into attribute table")
    grass.run_command('db.in.ogr', input_=model_output, output=temptable,
            overwrite=True, quiet=True)
    grass.run_command('v.db.join', map_=allfeatures, column='cat',
                        otable=temptable, ocolumn='cat_', 
                        subset_columns=output_classcol, quiet=True)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
