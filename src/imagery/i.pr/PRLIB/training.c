/*
   The following routines are written and tested by Stefano Merler

   for

   structure Training management
 */

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include "global.h"

void inizialize_training(Training *training)

/*
   alloc memory for training (see global.h for details)
 */
{
    int i;

    training->nexamples = 0;
    training->east = (double *)G_calloc(TRAINING_MAX_EXAMPLES, sizeof(double));
    training->north = (double *)G_calloc(TRAINING_MAX_EXAMPLES, sizeof(double));
    training->class = (int *)G_calloc(TRAINING_MAX_EXAMPLES, sizeof(int));
    training->mapnames =
        (char ***)G_calloc(TRAINING_MAX_EXAMPLES, sizeof(char **));
    for (i = 0; i < TRAINING_MAX_EXAMPLES; i++) {
        training->mapnames[i] =
            (char **)G_calloc(TRAINING_MAX_LAYERS, sizeof(char *));
    }
    training->data =
        (double **)G_calloc(TRAINING_MAX_EXAMPLES, sizeof(double *));
}

void read_training(char *file, Training *training)

/*
   read training structure from a file. Supported formats
   GRASS_data:list of labelled raster maps
   TABLE_data:list of labelled vecors
 */
{
    FILE *fp;
    char tempbuf[500];
    char *line = NULL;
    int i, j;
    int index;
    int tmprow, tmpcol;
    double tmpew, tmpns;
    int nlayers;
    int training_type = 0;
    int tmpc;

    fp = fopen(file, "r");
    if (fp == NULL) {
        sprintf(tempbuf, "read_training-> Can't open file %s for reading",
                file);
        G_fatal_error(tempbuf);
    }
    if (G_getl2(tempbuf, sizeof(tempbuf) - 1, fp) == 0) {
        G_fatal_error("read_training-> File %s is empty", file);
        fclose(fp);
    }

    training->file = file;

    line = GetLine(fp);

    /*line=GetLine(fp); */

    if (strcmp(line, "GrassTraining") == 0) {
        training_type = GRASS_data;
    }
    if (strcmp(line, "TableTraining") == 0) {
        training_type = TABLE_data;
    }

    switch (training_type) {
    case GRASS_data:
        training->data_type = training_type;
        if (training->nexamples == 0) {
            line = GetLine(fp);
            line = GetLine(fp);
            sscanf(line, "%d", &(training->nlayers));
            if (training->nlayers > TRAINING_MAX_LAYERS) {
                sprintf(tempbuf,
                        "read_training-> Maximum number of layers is %d",
                        TRAINING_MAX_LAYERS);
                G_fatal_error(tempbuf);
            }
            line = GetLine(fp);
            line = GetLine(fp);
            line = GetLine(fp);
            line = GetLine(fp);
        }
        else {
            line = GetLine(fp);
            line = GetLine(fp);
            sscanf(line, "%d", &nlayers);
            if (nlayers != training->nlayers) {
                sprintf(tempbuf, "read_training-> Training files must contain "
                                 "same number of layers");
                G_fatal_error(tempbuf);
            }
            line = GetLine(fp);
            line = GetLine(fp);
            line = GetLine(fp);
            line = GetLine(fp);
        }
        while ((line = GetLine(fp)) != NULL) {
            for (i = 0; i < training->nlayers; i++) {
                j = 0;
                training->mapnames[training->nexamples][i] =
                    (char *)G_calloc(strlen(line) - 1, sizeof(char));
                index = 0;
                while (line[j] > 44 && line[j] < 123)
                    training->mapnames[training->nexamples][i][index++] =
                        line[j++];
                training->mapnames[training->nexamples][i][strlen(
                    training->mapnames[training->nexamples][i])] = '\0';
                line = (char *)strchr(line, '\t');
                line++;
            }
            sscanf(line, "%d", &(training->class[training->nexamples]));

            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%lf", &(training->east[training->nexamples]));

            line = (char *)strchr(line, '\t');
            line++;
            sscanf(line, "%lf", &(training->north[training->nexamples]));

            line = (char *)strchr(line, '\t');
            line++;
            if (training->nexamples == 0) {
                sscanf(line, "%d", &(training->rows));
            }
            else {
                sscanf(line, "%d", &tmprow);
            }

            line = (char *)strchr(line, '\t');
            line++;
            if (training->nexamples == 0) {
                sscanf(line, "%d", &(training->cols));
            }
            else {
                sscanf(line, "%d", &tmpcol);
            }

            line = (char *)strchr(line, '\t');
            line++;
            if (training->nexamples == 0) {
                sscanf(line, "%lf", &(training->ew_res));
            }
            else {
                sscanf(line, "%lf", &tmpew);
            }

            line = (char *)strchr(line, '\t');
            line++;
            if (training->nexamples == 0) {
                sscanf(line, "%lf", &(training->ns_res));
            }
            else {
                sscanf(line, "%lf", &tmpns);
            }

            if (training->nexamples > 0) {
                if ((tmprow != training->rows) || (tmpcol != training->cols)) {
                    sprintf(tempbuf,
                            "read_training-> Example %d: different number of "
                            "rows or cols",
                            training->nexamples + 1);
                    G_fatal_error(tempbuf);
                }
                if (fabs((tmpew - training->ew_res) / training->ew_res) > 0.1) {
                    sprintf(tempbuf,
                            "read_training-> Example %d: EW-resolution differs "
                            "more than 10%%",
                            training->nexamples + 1);
                    G_warning(tempbuf);
                }
                if (fabs((tmpns - training->ns_res) / training->ns_res) > 0.1) {
                    sprintf(tempbuf,
                            "read_training-> Example %d: NS-resolution differs "
                            "more than 10%%",
                            training->nexamples + 1);
                    G_warning(tempbuf);
                }
            }
            training->nexamples += 1;
            if (training->nexamples == TRAINING_MAX_EXAMPLES) {
                sprintf(tempbuf,
                        "read_training-> Maximum number of training data is %d",
                        TRAINING_MAX_EXAMPLES);
                G_fatal_error(tempbuf);
            }
        }
        break;
    case TABLE_data:
        training->data_type = training_type;
        training->rows = 1;
        training->ew_res = 0.0;
        training->ns_res = 0.0;
        training->nlayers = 1;
        if (training->nexamples == 0) {
            line = GetLine(fp);
            line = GetLine(fp);
            sscanf(line, "%d", &(training->cols));
        }
        else {
            line = GetLine(fp);
            line = GetLine(fp);
            sscanf(line, "%d", &(tmpc));
            if (tmpc != training->cols) {
                sprintf(tempbuf, "read_training-> training data must have same "
                                 "number of columns");
                G_fatal_error(tempbuf);
            }
        }
        line = GetLine(fp);
        while ((line = GetLine(fp)) != NULL) {
            training->data[training->nexamples] =
                (double *)G_calloc(training->cols, sizeof(double));
            for (i = 0; i < training->cols; i++) {
                sscanf(line, "%lf", &(training->data[training->nexamples][i]));
                line = (char *)strchr(line, '\t');
                line++;
            }
            sscanf(line, "%d", &(training->class[training->nexamples]));
            training->nexamples += 1;
            if (training->nexamples == TRAINING_MAX_EXAMPLES) {
                sprintf(tempbuf,
                        "read_training-> Maximum number of training data is %d",
                        TRAINING_MAX_EXAMPLES);
                G_fatal_error(tempbuf);
            }
        }
        break;

    default:
        sprintf(tempbuf, "read_training-> Format not recognized");
        G_fatal_error(tempbuf);
        break;
    }
    fclose(fp);
}
