#define GLOBAL

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"
#include "globals.h"
#include "func.h"
#include "loc_func.h"

int main(int argc, char **argv)
{
    struct GModule *module;
    struct Option *opt1;
    struct Option *opt2;
    struct Option *opt3;
    struct Option *opt4;
    struct Option *opt5;
    struct Option *opt6;
    struct Option *opt7;
    struct Cell_head cellhd, zoomed_cellhd, map_cellhd;
    char *mapset[TRAINING_MAX_LAYERS];
    char *name[TRAINING_MAX_LAYERS];
    int nmaps;
    char buf[256];
    int window_rows, window_cols;
    FILE *fp;
    int num_class;
    int i, j;
    Training training;
    int X1, X2, Y1, Y2;
    int x_screen1, y_screen1, button1;
    int x_screen2, y_screen2, button2;
    int other = TRUE;
    double east, north, west, south;
    double tempeast1, tempnorth1;
    double tempeast2, tempnorth2;
    char out_map[100];
    int orig_nexamples;
    char opt1desc[500];
    char *vis_map;
    char *vis_mapset;

    char gisrc[500];

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to generate the training samples for use in i.pr.* modules. "
          "i.pr: Pattern Recognition environment for image processing. "
          "Includes kNN, "
          "Decision Tree and SVM classification techniques. Also includes "
          "cross-validation and bagging methods for model validation.");

    sprintf(opt1desc,
            "Input raster maps (max %d) for extracting the training "
            "examples.\n\t\tThe first one will be used for graphical output in "
            "case vis_map option not set",
            TRAINING_MAX_LAYERS);
    /* set up command line */
    opt1 = G_define_option();
    opt1->key = "map";
    opt1->type = TYPE_STRING;
    opt1->required = YES;
    opt1->gisprompt = "old,cell,raster";
    opt1->description = opt1desc;
    opt1->multiple = YES;

    opt7 = G_define_option();
    opt7->key = "vis_map";
    opt7->type = TYPE_STRING;
    opt7->required = NO;
    opt7->gisprompt = "old,cell,raster";
    opt7->description = "Raster map for visualization.";

    opt4 = G_define_option();
    opt4->key = "training";
    opt4->type = TYPE_STRING;
    opt4->required = YES;
    opt4->description =
        "Name of the output file containing the training raster maps.\n\t\tIf "
        "this file already exists, the new data will be appended\n\t\tto the "
        "end of the file.";

    opt6 = G_define_option();
    opt6->key = "vector";
    opt6->type = TYPE_STRING;
    opt6->required = NO;
    opt6->description = "Name of the vector points map containing labelled "
                        "location.\n\t\tSubstitutes the interactive procedure "
                        "of point selection.";

    opt2 = G_define_option();
    opt2->key = "rows";
    opt2->type = TYPE_INTEGER;
    opt2->required = YES;
    opt2->description =
        "Number of rows (required odd) of the training samples.";

    opt3 = G_define_option();
    opt3->key = "cols";
    opt3->type = TYPE_INTEGER;
    opt3->required = YES;
    opt3->description =
        "Number of columns (required odd) of the training samples.";

    opt5 = G_define_option();
    opt5->key = "class";
    opt5->type = TYPE_INTEGER;
    opt5->required = NO;
    opt5->description =
        "Numerical label to be attached to the training examples.\n\t\tOption "
        "not required with the vector option.";

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* informations from command line */
    nmaps = 0;
    for (i = 0; name[nmaps] = opt1->answers[i]; i++) {
        mapset[i] = (char *)G_find_raster2(name[i], "");
        if (mapset[i] == NULL) {
            sprintf(buf, "Can't find raster map <%s>", name[i]);
            G_fatal_error(buf);
        }
        nmaps += 1;
        if (nmaps > TRAINING_MAX_LAYERS) {
            sprintf(buf, "Too many raster maps\nMaximum number allowed = %d",
                    TRAINING_MAX_LAYERS);
            G_fatal_error(buf);
        }
    }

    if (opt7->answer) {
        vis_map = opt7->answer;
        vis_mapset = (char *)G_find_raster2(vis_map, "");
        if (vis_mapset == NULL) {
            sprintf(buf, "Can't find raster map <%s>", vis_map);
            G_fatal_error(buf);
        }
    }
    else {
        vis_map = name[0];
        vis_mapset = mapset[0];
    }

    if (!opt6->answer && !opt5->answer) {
        sprintf(buf, "Please select a class for the examples\n");
        G_fatal_error(buf);
    }
    if (!opt6->answer) {
        sscanf(opt5->answer, "%d", &num_class);
    }
    if (opt6->answer && opt5->answer) {
        sprintf(buf, "Option class ignored\nLabels will be directlly read from "
                     "site file\n");
        G_warning(buf);
    }
    sscanf(opt2->answer, "%d", &window_rows);
    sscanf(opt3->answer, "%d", &window_cols);
    if (window_rows % 2 == 0 || window_cols % 2 == 0) {
        sprintf(buf, "Number of rows and columns must be odd\n");
        G_fatal_error(buf);
    }

    /*open output file and read/initialize training */
    inizialize_training(&training);
    if (fopen(opt4->answer, "r") == NULL) {
        if ((fp = fopen(opt4->answer, "w")) == NULL) {
            sprintf(buf, "Can't open file %s for writing\n", opt4->answer);
            G_fatal_error(buf);
        }
        fprintf(fp, "Data type:\n");
        fprintf(fp, "GrassTraining\n");
        fprintf(fp, "Number of layers:\n");
        fprintf(fp, "%d\n", nmaps);
        fprintf(fp, "Label:\n");
        fprintf(fp, "%s\n", opt4->answer);
        fprintf(fp, "Data:\n");
        for (i = 0; i < nmaps; i++) {
            fprintf(fp, "Layer_%d\t", i + 1);
        }
        fprintf(fp, "Class\tEast\tNorth\tRows\tCols\tEW-res\tNS-res\n");
    }
    else {
        if ((fp = fopen(opt4->answer, "a")) == NULL) {
            sprintf(buf, "Can't open file %s for appending\n", opt4->answer);
            G_fatal_error(buf);
        }
        read_training(opt4->answer, &training);
    }

    if (!opt6->answer) {
        /* must have a graphics terminal selected */
        if (R_open_driver() != 0)
            G_fatal_error(_("No graphics device selected."));

        /*inizialize monitor */
        Init_graphics();
        exit_button();
        info_button();

        /*get current region */
        G_get_window(&cellhd);

        /*plot map */
        display_map(&cellhd, VIEW_MAP1, vis_map, vis_mapset);
        R_standard_color(RED);
        for (i = 0; i < training.nexamples; i++) {
            display_one_point(VIEW_MAP1, training.east[i], training.north[i]);
        }
        R_flush();

        X1 = X2 = Y1 = Y2 = 0;
        while (other == TRUE) {
            Mouse_pointer(&x_screen1, &y_screen1, &button1);
            if (In_view(VIEW_MAP1, x_screen1, y_screen1) && button1 == 1) {
                R_standard_color(GREEN);
                point(x_screen1, y_screen1);
                R_flush();
            }
            if (In_view(VIEW_EXIT, x_screen1, y_screen1)) {
                R_close_driver();
                fclose(fp);
                return 0;
            }
            Mouse_pointer(&x_screen2, &y_screen2, &button2);
            if (In_view(VIEW_EXIT, x_screen2, y_screen2)) {
                R_close_driver();
                fclose(fp);
                return 0;
            }
            if (In_view(VIEW_MAP1, x_screen1, y_screen1) &&
                In_view(VIEW_MAP1, x_screen2, y_screen2) && button1 == 1 &&
                button2 == 1) {
                R_standard_color(GREEN);
                rectangle(x_screen1, y_screen1, x_screen2, y_screen2);
                R_standard_color(GREY);
                point(X1, Y1);
                rectangle(X1, Y1, X2, Y2);
                R_flush();
                X1 = x_screen1;
                X2 = x_screen2;
                Y1 = y_screen1;
                Y2 = y_screen2;

                from_screen_to_geo(VIEW_MAP1, x_screen1, y_screen1, &tempeast1,
                                   &tempnorth1);
                from_screen_to_geo(VIEW_MAP1, x_screen2, y_screen2, &tempeast2,
                                   &tempnorth2);
                if (tempeast1 > tempeast2) {
                    east = tempeast1;
                    west = tempeast2;
                }
                else {
                    east = tempeast2;
                    west = tempeast1;
                }
                if (tempnorth1 > tempnorth2) {
                    north = tempnorth1;
                    south = tempnorth2;
                }
                else {
                    north = tempnorth2;
                    south = tempnorth1;
                }
                compute_temp_region(&zoomed_cellhd, &cellhd, east, west, north,
                                    south);
                Erase_view(VIEW_MAP1_ZOOM);
                display_map(&zoomed_cellhd, VIEW_MAP1_ZOOM, vis_map,
                            vis_mapset);
                R_standard_color(RED);
                for (i = 0; i < training.nexamples; i++) {
                    display_one_point(VIEW_MAP1_ZOOM, training.east[i],
                                      training.north[i]);
                }
                R_flush();
            }
            if (In_view(VIEW_MAP1_ZOOM, x_screen1, y_screen1) &&
                In_view(VIEW_MAP1_ZOOM, x_screen2, y_screen2) && button1 == 1 &&
                button2 == 1) {
                if (VIEW_MAP1_ZOOM->cell.configured) {
                    from_screen_to_geo(VIEW_MAP1_ZOOM, x_screen2, y_screen2,
                                       &east, &north);
                    compute_temp_region2(&map_cellhd, &zoomed_cellhd, east,
                                         north, window_rows, window_cols);
                    R_standard_color(BLUE);
                    display_one_point(VIEW_MAP1, east, north);
                    display_one_point(VIEW_MAP1_ZOOM, east, north);
                    display_map(&map_cellhd, VIEW_IMAGE, vis_map, vis_mapset);
                    R_flush();
                }
            }

            if (In_view(VIEW_IMAGE, x_screen1, y_screen1) &&
                In_view(VIEW_IMAGE, x_screen2, y_screen2)) {
                if (button1 == 3 && button2 == 3) {
                    if (VIEW_IMAGE->cell.configured) {
                        training.nexamples += 1;
                        training.east[training.nexamples] = east;
                        training.north[training.nexamples] = north;

                        R_standard_color(RED);

                        display_one_point(VIEW_MAP1,
                                          training.east[training.nexamples],
                                          training.north[training.nexamples]);
                        display_one_point(VIEW_MAP1_ZOOM,
                                          training.east[training.nexamples],
                                          training.north[training.nexamples]);
                        R_flush();
                        for (i = 0; i < nmaps; i++) {
                            sprintf(out_map, "%s_%s.%d", opt4->answer, name[i],
                                    training.nexamples);
                            write_map(&map_cellhd, name[i], mapset[i], out_map);
                            fprintf(fp, "%s\t", out_map);
                        }
                        fprintf(fp, "%d\t%f\t%f\t%d\t%d\t%f\t%f\n", num_class,
                                training.east[training.nexamples],
                                training.north[training.nexamples], window_rows,
                                window_cols, cellhd.ew_res, cellhd.ns_res);
                    }
                }
            }
        }
    }
    else {
        G_get_window(&cellhd);
        if (R_open_driver() != 0)
            G_fatal_error(_("No graphics device selected."));
        Init_graphics2();
        display_map(&cellhd, VIEW_MAP1, vis_map, vis_mapset);

        R_flush();
        orig_nexamples = training.nexamples;
        if (read_points_from_file(&training, opt6->answer) == 0) {
            sprintf(buf, "Error readining site file <%s>", opt6->answer);
            G_fatal_error(buf);
        }
        R_standard_color(BLUE);
        for (i = 0; i < orig_nexamples; i++) {
            display_one_point(VIEW_MAP1, training.east[i], training.north[i]);
        }
        R_standard_color(RED);
        for (i = orig_nexamples; i < training.nexamples; i++) {
            display_one_point(VIEW_MAP1, training.east[i], training.north[i]);
            R_flush();
            compute_temp_region2(&map_cellhd, &cellhd, training.east[i],
                                 training.north[i], window_rows, window_cols);
            for (j = 0; j < nmaps; j++) {
                sprintf(out_map, "%s_%s.%d", opt4->answer, name[j], i + 1);
                write_map(&map_cellhd, name[j], mapset[j], out_map);
                fprintf(fp, "%s\t", out_map);
            }
            fprintf(fp, "%d\t%f\t%f\t%d\t%d\t%f\t%f\n", training.class[i],
                    training.east[i], training.north[i], window_rows,
                    window_cols, cellhd.ew_res, cellhd.ns_res);
        }
        fclose(fp);
        R_close_driver();
        return 0;
    }
    return 0;
}
