#!/usr/bin/env python3
#
"""
# MODULE:       r.area.createweight
#
# AUTHOR(S):    Grippa Tais, Safa Fennia, Charlotte Flasse
#
# PURPOSE:      Create a weighting layer for dasymetric mapping,
#               using a random forest regression model.
#
# DATE:         2021/08/05
#
# COPYRIGHT:    (C) 2021 Grippa Tais, Safa Fennia, Charlotte Flasse
#               and by the GRASS Development Team
#
#               This program is free software under the
#               GNU General Public License (>=v2).
#               Read the file COPYING that comes with GRASS
#               for details.
"""

#%module
#% description: Create a dasymetric weighting layer with Random Forest
#% keyword:raster
#% keyword:statistics
#% keyword:density
#% keyword:dasymetry
#% keyword:resample
#%end
#%option G_OPT_V_MAP
#% key: vector
#% label: Vector with spatial units
#% description: Polygon vector containing unique ID and response variable in the attribute table
#% required : yes
#% guisection: Required inputs
#% guidependency:vector_layer,id,response_variable
#%end
#%option G_OPT_V_FIELD
#% key: vector_layer
#% label: Layer number or name
#% required : yes
#% guisection: Required inputs
#% answer:1
#% guidependency:id,response_variable
#%end
#%option G_OPT_DB_COLUMN
#% key: id
#% label: Name of the column containing unique ID of spatial units
#% required : yes
#% guisection: Required inputs
#%end
#%option G_OPT_DB_COLUMN
#% key: response_variable
#% label: Name of the column containing response variable
#% description: Format: All values must be >0
#% required : yes
#% guisection: Required inputs
#%end
#%option G_OPT_R_INPUT
#% key: basemap_a
#% type: string
#% label: Input raster 1
#% description: E.g. Land cover, Land use, morphological areas...
#% required : yes
#% guisection: Required inputs
#%end
#%option G_OPT_R_INPUT
#% key: basemap_b
#% type: string
#% label: Input raster 2 (optional)
#% description: E.g. Land cover, Land use, morphological areas...
#% required : no
#% guisection: Optional inputs
#%end
#%option G_OPT_R_INPUT
#% key: distance_to
#% type: string
#% label: Input distance raster (optional)
#% description: Distance to zones of interest
#% required : no
#% guisection: Optional inputs
#%end
#%option
#% key: tile_size
#% key_desc: value
#% type: Integer
#% label: Spatial resolution of output weighting layer
#% description: (in metres)
#% required : yes
#% guisection: Outputs
#%end
#%option G_OPT_R_OUTPUT
#% key: output_weight
#% description: Output weighting layer name
#% required: yes
#% guisection: Outputs
#% answer:weighted_layer
#%end
#%option G_OPT_V_OUTPUT
#% key: output_units
#% description: Name for output vector gridded spatial units
#% required: yes
#% guisection: Outputs
#% answer:gridded_spatial_units
#%end
#%option G_OPT_F_OUTPUT
#% key: plot
#% description: Name for output plot of model feature importances
#% required: yes
#% guisection: Outputs
#%end
#%option G_OPT_F_OUTPUT
#% key: log_file
#% description: Name for output file with log of the random forest run
#% required: yes
#% guisection: Outputs
#%end
#%option
#% key: basemap_a_list
#% type: string
#% label: Categories of basemap A to be used
#% description: Format: 1,2,3
#% required: no
#% guisection: Optional inputs
#%end
#%option
#% key: basemap_b_list
#% type: string
#% label: Categories of basemap B to be used
#% description: Format: 1,2,3
#% required: no
#% guisection: Optional inputs
#%end
#%flag
#% key: a
#% description: Use class names for basemap a
#% guisection: Optional inputs
#%end
#%flag
#% key: b
#% description: Use class names for basemap b
#% guisection: Optional inputs
#%end
#%option G_OPT_M_NPROCS
#% key: n_jobs
#% type: integer
#% description: Number of cores to be used for the parallel process
#% required : yes
#% guisection: Required inputs
#% answer: 1
#%end
#%flag
#% key: c
#% description: Keep all covariates in the final model
#% guisection: Feature selection and tuning
#%end
#%flag
#% key: f
#% description: Include detailed results of grid search cross-validation
#% guisection: Feature selection and tuning
#%end
#%option
#% key: kfold
#% type: integer
#% label: Number of k-fold cross-validation for grid search parameter optimization
#% description: Format: Must have a value > 2 and < N spatial units
#% required: no
#% guisection: Feature selection and tuning
#% answer: 5
#%end
#%option
#% key: param_grid
#% type: string
#% description: Python dictionary of customized tunegrid for sklearn RFregressor
#% required: no
#% guisection: Feature selection and tuning
#%end
# Import standard python libraries
import os
import sys
import time
import csv
import atexit

# Import GRASS GIS Python Scripting Library
import grass.script as gscript

# Import Shutil library
import shutil

# Import Numpy library
import numpy as np

# import math library
import math as ma

# Import pyplot library
import matplotlib
import matplotlib.pyplot as plt

# Import literal_eval
from ast import literal_eval
from copy import deepcopy

# Use a non-interactive backend: prevent the figure from popping up
matplotlib.use("Agg")


# For list of files to cleanup
TMP_MAPS = []  # Maps to cleanup
TMP_CSV = []  # Csv to cleanup
TMP_VECT = []  # Vector to cleanup


def lazy_import():
    """Lazy import py packages due compilation error on OS MS Windows
    (missing py packages)
    """
    # Import Pandas library (View and manipulation of tables)
    # Still required for selecting in dataframes based on column names
    global pd, RandomForestRegressor, SelectFromModel, GridSearchCV
    try:
        import pandas as pd
    except ModuleNotFoundError:
        gscript.fatal(_("Pandas is not installed"))

    # Import sklearn libraries
    try:
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.feature_selection import SelectFromModel
        from sklearn.model_selection import GridSearchCV
    except ModuleNotFoundError:
        gscript.fatal(
            _("Scikit-learn 0.24 or newer is not installed (python3-scikit-learn)")
        )


def cleanup():
    if TMP_MAPS != []:
        gscript.run_command(
            "g.remove",
            quiet=True,
            type="raster",
            name=",".join(TMP_MAPS),
            flags="fb",
        )
    if TMP_CSV != []:
        for tmp_csv in TMP_CSV:
            if os.path.isfile(tmp_csv):
                os.remove(tmp_csv)
    if TMP_VECT != []:
        gscript.run_command(
            "g.remove",
            quiet=True,
            type="vector",
            name=",".join(TMP_VECT),
            flags="fb",
        )


def check_no_missing_zones(vector_origin, vector_new):
    """
    Compare number of elements in 2 vector files

    Return True if equal
    Return N elements in each vector
    """

    origin_n = int(
        gscript.parse_command("v.db.univar", flags="g", map=vector_origin, column=id)[
            "n"
        ]
    )

    new_n = int(
        gscript.parse_command("v.db.univar", flags="g", map=vector_new, column=id)["n"]
    )

    difference = origin_n - new_n
    if origin_n != new_n:
        element_equal = False
    else:
        element_equal = True

    return element_equal, origin_n, new_n


def create_clumped_grid(tile_size):
    """
    Create empty raster grid with resolution <tile_size>

    Uses vector as a mask
    Used for computing raster class proportion at grid level.
    Also used at the end with r.reclass to allow random forest
        prediction to each grid.
    """

    gscript.run_command("g.region", vector=vector_map, res=tile_size)
    gscript.run_command("r.mask", quiet=True, vector=vector_map)
    # Creating a raster with random values
    gscript.mapcalc("empty_grid=rand(0 ,999999999)", seed="auto")
    # Assigning a unique value to each cell in contiguous zones
    gscript.run_command(
        "r.clump", quiet=True, input="empty_grid", output="clumped_grid"
    )

    gscript.run_command("r.mask", quiet=True, flags="r")
    TMP_MAPS.append("empty_grid")
    TMP_MAPS.append("clumped_grid")


def clip_basemaps(raster_list, rast_out_list, vector_map):
    """
    Clip all input rasters to the boundary of a vector

    Used to enables extraction of raster categories for only the zone
        covered by the spatial units, or to check user-given categories
        exist in zone covered by the spatial units.
    Original cell size & alignment of input rasters are kept.
    Input list of rasters to clip, and list of names for outputs
        (in same order as list of rasters)
    """

    # Mask area covered by the vector_map
    gscript.run_command("r.mask", quiet=True, vector=vector_map)

    # Clip rasters
    for inrast, outrast in zip(raster_list, rast_out_list):
        # Set region to vector & align to basemap
        # (to keep cell size & alignment)
        gscript.run_command("g.region", vector=vector_map, align=inrast)
        # Clip raster
        gscript.run_command("r.clip", quiet=True, input=inrast, output=outrast)
        TMP_MAPS.append(outrast)

    # Remove mask
    gscript.run_command("r.mask", quiet=True, flags="r")


def extract_raster_categories(categorical_raster):
    """Extract and return sorted list categorical raster classes"""

    L = []
    L = [
        cl.split(":")[0]
        for cl in gscript.parse_command(
            "r.category", map=categorical_raster, separator=":"
        )
    ]
    # UTF8 coding required for Linux
    if sys.platform == "linux":
        for i, x in enumerate(L):
            L[i] = x.encode("UTF8")
    L.sort(key=float)  # Sort the raster categories in ascending

    return L


def category_list_check(cat_list, raster_map):
    """
    Check if the categories in a list exist in a raster_map"""

    existing_cat = extract_raster_categories(raster_map.split("@")[0])
    existing_cat_string = deepcopy(existing_cat)

    # UTF8 coding required for Linux
    if sys.platform == "linux":
        for i, x in enumerate(cat_list):
            cat_list[i] = x.encode("UTF8")
        for j, z in enumerate(existing_cat_string):
            existing_cat_string[j] = z.decode("UTF8")

    for cat in cat_list:
        if cat not in existing_cat:
            message = (
                "Some categories provided do not exist in the "
                "parts of raster \n <%s>, that are covered by the "
                "spatial units. Please check. \n Valid categories "
                "are: " + ",".join(existing_cat_string)
            ) % raster_map
            gscript.fatal(_(message))
    gscript.verbose(_("All user-given categories exist in raster <%s>.") % raster_map)


def spatial_boundaries(vector, id):
    """
    Convert vector to raster, then raster to vector

    Boundaries will have a staircase appearance, so that each tile of
        the output weighted grid will be contained in only one spatial
        unit.
    Output gridded vector can be used as input for dasymetric mapping
        with v.area.weigh module.
    Creates error if number of polygons in initial and final vector are
        not equal as if the original vector contains small sized
        polygons (or very narrow) and desired 'tile_size' is too large,
        some polygons could disappear during the rasterization process
    """

    global gridded_vector

    current_mapset = gscript.gisenv()["MAPSET"]
    gridded_vector = (
        vector.split("@")[0] + "_" + str(tile_size) + "m_gridded@" + current_mapset
    )
    gscript.run_command("g.region", raster="clumped_grid")
    gscript.run_command(
        "v.to.rast",
        quiet=True,
        input=vector,
        type="area",
        output="gridded_spatial_units",
        use="attr",
        attribute_column=id,
    )
    gscript.run_command(
        "r.to.vect",
        quiet=True,
        input="gridded_spatial_units",
        output=gridded_vector,
        type="area",
        flags="v",
    )
    gscript.run_command(
        "v.db.dropcolumn", quiet=True, map=gridded_vector, column="label"
    )
    # Join the response variable count
    gscript.run_command(
        "v.db.join",
        quiet=True,
        map=gridded_vector,
        column="cat",
        other_table=vector,
        other_column=id,
        subset_columns=response_variable,
    )
    TMP_MAPS.append("gridded_spatial_units")
    TMP_VECT.append(gridded_vector)
    gscript.run_command("g.region", vector=gridded_vector, align="clumped_grid")

    # Check if loss of spatial units (polygons)
    element_equal, origin_n, gridded_n = check_no_missing_zones(vector, gridded_vector)
    if element_equal == False:
        gscript.run_command(
            "g.remove",
            quiet=True,
            type="vector",
            name=gridded_vector,
            flags="fb",
        )
        message = (
            "A tile size of %s m seems to large and produces "
            "loss of some spatial units when rasterizing them."
            "\n"
        ) % tile_size
        message += (
            "Try to reduce the 'tile_size' parameter or edit "
            "the <%s> vector to merge smallest spatial units with "
            "their neighboring units"
        ) % vector
        gscript.fatal(_(message))


def compute_proportion_csv(categorical_raster, zone_raster, prefix, outputfile):
    """Run module r.zonal.classes to calculate statistics"""

    gscript.run_command(
        "r.zonal.classes",
        quiet=True,
        zone_map=zone_raster,
        raster=categorical_raster,
        prefix=prefix,
        decimals="4",
        statistics="proportion",
        csvfile=outputfile,
        separator="comma",
        overwrite=True,
    )


def atoi(text):
    """
    Return integer if text is digit

    Used in 'natural_keys' function
    """

    return int(text) if text.isdigit() else text


def natural_keys(text):
    """Return key to sort a string containing numerical values"""

    import re  # Import needed library

    return [atoi(c) for c in re.split("(\d+)", text)]  # Split string


def join_2csv(file1, file2, separator=";", join="inner", fillempty="NULL"):
    """
    Join two csv files according to the first column (primary key)

    'file1' and 'file2' wait for complete path (strings) to the
        corresponding files. Please note that 'file1' is assumed to be
        the left-one in the join
    'separator' wait for the character to be considered as
        .csv delimiter (string)
    'join' parameter 'inner'
    'fillempty' wait for the string to be use to fill the blank when no
        occurrence is found for the join operation
    """

    header_list = []
    file1_values_dict = {}
    file2_values_dict = {}
    # Csv reader for file 1
    reader1 = csv.reader(open(file1), delimiter=separator)
    # Csv reader for file 2
    reader2 = csv.reader(open(file2), delimiter=separator)

    # Make a list of headers
    header_list1 = [x for x in reader1.__next__()]
    header_list2 = [x for x in reader2.__next__()]
    # Return a list of IDs matching in both the first and second table
    if join == "inner":
        id_list_1 = [row[0] for row in reader1]
        id_list_2 = [row[0] for row in reader2]
        id_list = list(set(id_list_1).intersection(id_list_2))
        id_list.sort(key=natural_keys)

    # Build dictionnary for values of file 1
    reader1 = csv.reader(open(file1), delimiter=separator)
    reader1.__next__()
    values_dict1 = {rows[0]: rows[1:] for rows in reader1}
    # Build dictionnary for values of file 2
    reader2 = csv.reader(open(file2), delimiter=separator)
    reader2.__next__()
    values_dict2 = {rows[0]: rows[1:] for rows in reader2}
    # Build new content
    new_content = []
    new_header = header_list1 + header_list2[1:]
    new_content.append(new_header)
    for key in id_list:
        new_row = [key]
        try:
            [new_row.append(value) for value in values_dict1[key]]
        except:
            [new_row.append("%s" % fillempty) for x in header_list1[1:]]
        try:
            [new_row.append(value) for value in values_dict2[key]]
        except:
            [new_row.append("%s" % fillempty) for x in header_list2[1:]]
        new_content.append(new_row)

    # Return the result
    outfile = gscript.tempfile()
    fout = open(outfile, "w")
    writer = csv.writer(fout, delimiter=separator, lineterminator="\n")
    writer.writerows(new_content)  # Write multiple rows in the file
    # Make sure file does not close too fast
    # (the content could be incompletely filled)
    time.sleep(0.5)
    fout.close()
    return outfile


def join_multiplecsv(
    fileList,
    outfile,
    separator=";",
    join="inner",
    fillempty="NULL",
    overwrite=False,
):
    """Join multiple csv files"""

    # Stop execution if outputfile exists and can not be overwritten
    if os.path.isfile(outfile) and overwrite == False:
        gscript.fatal(
            _(
                "File '%s' aleady exists and overwrite option is "
                "not enabled." % outfile
            )
        )
    else:
        nbfile = len(fileList)
        # Check if there are at least 2 files in the list
        if nbfile > 1:
            # Copy the list of file in a queue list
            queue_list = list(fileList)
            # Inner join on the two first files
            file1 = queue_list.pop(0)
            file2 = queue_list.pop(0)
            tmp_file = join_2csv(
                file1,
                file2,
                separator=separator,
                join=join,
                fillempty=fillempty,
            )
            # Inner join on the rest of the files in the list
            while len(queue_list) > 0:
                file2 = queue_list.pop(0)
                tmp_file = join_2csv(
                    tmp_file,
                    file2,
                    separator=separator,
                    join=join,
                    fillempty=fillempty,
                )
        else:  # in case there is only one file in the list
            tmp_file = fileList[0]
        if os.path.isfile(outfile) and overwrite == True:
            os.remove(outfile)
        # Copy the temporary file to the desired output path
        shutil.copy2(tmp_file, outfile)
        os.remove(tmp_file)


def labels_from_csv(current_labels):
    """Extract class names for feature importances plot

    Extract class names for 'basemap_a' and 'basemap_b' and
        return a list of modified labels for the feature importances
        plot
    """

    new_label = []
    basemap_a_class_rename_dict = {}
    basemap_b_class_rename_dict = {}

    # If flag selected, extract class names from basemap_a
    if rasta_class_list == 1:
        ccode = [
            cl.split(":")[0]
            for cl in gscript.parse_command("r.category", map=basemap_a, separator=":")
        ]
        ccname = [
            cl.split(":")[1]
            for cl in gscript.parse_command("r.category", map=basemap_a, separator=":")
        ]
        for classcode, classname in zip(ccode, ccname):
            basemap_a_class_rename_dict[classcode] = classname
    # If flag selected, extract class names from basemap_b
    if rastb_class_list == 1:
        ccode = [
            cl.split(":")[0]
            for cl in gscript.parse_command("r.category", map=basemap_b, separator=":")
        ]
        ccname = [
            cl.split(":")[1]
            for cl in gscript.parse_command("r.category", map=basemap_b, separator=":")
        ]
        for classcode, classname in zip(ccode, ccname):
            basemap_b_class_rename_dict[classcode] = classname

    # Replace class value with class labels (if existing)
    #   else keep initial class value
    for l in current_labels:
        if l[:8] == "basemapA":
            classnum = l[l.index("_prop_") + len("_prop_") :]
            if (
                classnum in basemap_a_class_rename_dict.keys()
                and basemap_a_class_rename_dict[classnum] != ""
            ):
                new_label.append(
                    'Basemap A "%s"' % basemap_a_class_rename_dict[classnum]
                )
            else:
                new_label.append('Basemap A "%s"' % classnum)
        elif l[:8] == "basemapB":
            classnum = l[l.index("_prop_") + len("_prop_") :]
            if (
                classnum in basemap_b_class_rename_dict.keys()
                and basemap_b_class_rename_dict[classnum] != ""
            ):
                new_label.append(
                    'Basemap B "%s"' % basemap_b_class_rename_dict[classnum]
                )
            else:
                new_label.append('Basemap B "%s"' % classnum)
        elif l[-4:] == "mean":
            new_label.append(l[0].title() + l[1:-5].replace("_", " "))
        else:
            new_label.append(l)
    return new_label


def RandomForest(weighting_layer_name, vector, id):
    """
    Create, train and run a random forest model

    Trained at the spatial units level to generate gridded prediction.
    Covariates are proportion of each basemap class.
    """

    global log_text, log_text_extend
    # ------------------------------------------------------------------
    # Data preparation for spatial units
    # ------------------------------------------------------------------
    gscript.info(_("Data preparation for spatial units..."))
    # Compute area of the gridded spatial unit (vector) layer
    gscript.run_command(
        "v.to.db",
        quiet=True,
        map=gridded_vector,
        option="area",
        columns="area",
        units="meters",
    )
    # Export desired columns from the attribute table as CSV
    area_table = gscript.tempfile()  # Define the path to the .csv

    query = "SELECT cat,%s,area FROM %s" % (
        response_variable,
        gridded_vector.split("@")[0],
    )
    gscript.run_command(
        "db.select", quiet=True, sql=query, output=area_table, overwrite=True
    )
    TMP_CSV.append(area_table)
    # Copy gridded vector to be an output with user-defined name
    gscript.run_command(
        "g.copy",
        quiet=True,
        vector="%s,%s" % (gridded_vector, output_units_layer),
    )

    # Compute log of density in a new .csv file
    reader = csv.reader(open(area_table, "r"), delimiter="|")
    # Define the path to the .csv containing the log of density
    log_density_csv = gscript.tempfile()

    fout = open(log_density_csv, "w")
    writer = csv.writer(fout, delimiter=",", lineterminator="\n")
    new_content = []
    new_header = ["cat", "log_" + response_variable + "_density"]
    new_content.append(new_header)
    reader.__next__()
    # Compute log (ln) of the density
    [
        new_content.append([row[0], ma.log(int(row[1]) / float(row[2]))])
        for row in reader
    ]
    writer.writerows(new_content)
    # Make sure file does not close too fast
    #   (the content could be incompletely filled)
    time.sleep(0.5)
    fout.close()

    ## Define the path to the file with all co-variates
    # For grid level
    all_stats_grid = allstatfile["grid"]
    # For spatial unit level
    all_stats_spatial_unit = allstatfile["unit"]
    # For spatial unit level : join all co-variates with the log of
    #   density (response variable of the model)
    units_attribute_table = join_2csv(
        log_density_csv,
        all_stats_spatial_unit,
        separator=",",
        join="inner",
        fillempty="NULL",
    )
    TMP_CSV.append(units_attribute_table)

    # ------------------------------------------------------------------
    # Creating and applying RF model
    # ------------------------------------------------------------------
    gscript.info(_("Creating RF model..."))
    ## Prepare inputs
    # Reading the csv files as dataframes
    df_unit = pd.read_csv(units_attribute_table)
    df_grid = pd.read_csv(all_stats_grid)

    # Make a list with names of covariables columns
    list_covar = []
    for cl in basemap_a_category_list:
        list_covar.append("basemapA_prop_%s" % cl)
    if basemap_b != "":
        for cl in basemap_b_category_list:
            list_covar.append("basemapB_prop_%s" % cl)
    if distance_to != "":
        list_covar.append(distance_to.split("@")[0] + "_mean")

    # Saving variable to predict
    y = df_unit["log_" + response_variable + "_density"]

    # Saving covariable for prediction
    # Get a dataframe with independent variables for spatial units
    x = df_unit[list_covar]

    ## Remove features whose importance is less than a threshold
    ##  (Feature selection)
    gscript.verbose(
        _(
            "Removing features whose importance is "
            "less than a threshold (Feature selection)..."
        )
    )
    # Run RF with default parameters, and 500 trees
    rfmodel = RandomForestRegressor(
        n_estimators=500, oob_score=True, max_features="auto", n_jobs=-1
    )
    # Select features
    a = SelectFromModel(rfmodel, threshold=min_fimportance)
    fitted = a.fit(x, y)
    # Get list of True/False values according to the fact the OOB score
    #   of the covariate is upper the threshold
    feature_idx = fitted.get_support()
    # Update list of covariates with the selected features
    list_covar = list(x.columns[feature_idx])
    # Replace the dataframe with the selected features
    x = fitted.transform(x)
    # Save the selected covariates for the model in message for logfile
    message = (
        "Selected covariates for the random forest model (with "
        "feature importance upper than {value} %) : \n\
        ".format(
            value=min_fimportance * 100
        )
    )
    message += "\n".join(list_covar)
    log_text += message + "\n\n"

    ## Tuning of hyperparameters for the Random Forest regressor using
    ##      "Grid search"
    gscript.verbose(_("Tuning of hyperparameters for the RF regressor..."))
    # Instantiate the grid search model
    grid_search = GridSearchCV(
        estimator=RandomForestRegressor(),
        param_grid=param_grid,
        cv=kfold,
        n_jobs=n_jobs,
        verbose=0,
    )
    grid_search.fit(x, y)  # Fit the grid search to the data
    regressor = grid_search.best_estimator_  # Save the best regressor
    regressor.fit(x, y)  # Fit the best regressor with the data

    ## Save RF infos in message for logile
    gscript.verbose(_("Saving information into logfile..."))
    # Save info for logfile - Parameter grid
    message = "Parameter grid for Random Forest tuning :\n"
    for key in param_grid.keys():
        message += "    %s : %s \n" % (
            key,
            ", ".join([str(i) for i in list(param_grid[key])]),
        )
    log_text += message + "\n"
    # Save info for logfile - Tuned parameters
    message = (
        "Optimized parameters for Random Forest after grid "
        "search %s-fold cross-validation tuning :\n" % kfold
    )
    for key in grid_search.best_params_.keys():
        message += " %s : %s \n" % (key, grid_search.best_params_[key])
    log_text += message + "\n"
    # Save info for logfile - Mean cross-validated estimator
    #    score (R2) and stddev of the best_estimator
    best_score = grid_search.cv_results_["mean_test_score"][grid_search.best_index_]
    best_std = grid_search.cv_results_["std_test_score"][grid_search.best_index_]
    message = (
        "Mean cross-validated estimator score (R2) and stddev "
        "of the best estimator : %0.3f (+/-%0.3f) \n" % (best_score, best_std)
    )
    log_text += message + "\n"
    # Save info for logfile: Mean R2 + sddev for each set of parameters
    means = grid_search.cv_results_["mean_test_score"]
    stds = grid_search.cv_results_["std_test_score"]
    message = (
        "Mean cross-validated estimator score (R2) and stddev"
        " for every tested set of parameter :\n"
    )
    for mean, std, params in zip(means, stds, grid_search.cv_results_["params"]):
        message += "%0.3f (+/-%0.03f) for %r \n" % (mean, std, params)
    log_text_extend += message

    ## Applying the RF model
    gscript.info(_("Applying the RF model..."))
    # Predict on grids
    gscript.verbose(_("Predict on grids..."))
    # Get a dataframe with independent variables for grids
    #   (remaining after feature selection)
    x_grid = df_grid[list_covar]
    # Apply the model on grid values
    prediction = regressor.predict(x_grid)

    # Save the prediction
    gscript.verbose(_("Saving the prediction..."))
    df1 = df_grid["cat"]
    df2 = pd.DataFrame(prediction, columns=["log"])
    df_weight = pd.concat((df1, df2), axis=1)
    col = df_weight.apply(lambda row: np.exp(row["log"]), axis=1)
    df_weight["weight_after_log"] = col

    ## Reclassify output weighted grid
    # Define a reclassification rule
    gscript.info(_("Preparing weighted layer..."))
    cat_list = df_weight["cat"].tolist()
    weight_list = df_weight["weight_after_log"].tolist()
    rule = ""
    for i, cat in enumerate(cat_list):
        rule += str(cat)
        rule += "="
        # Reclass rule of r.reclass requires INTEGER but random forest
        #   prediction could have very low values.
        rule += str(int(round(weight_list[i] * 1000000000, 0)))
        rule += "\n"
    rule += "*"
    rule += "="
    rule += "NULL"

    # Create a temporary 'weight_reclass_rules.csv' file for r.reclass
    outputcsv = gscript.tempfile()
    TMP_CSV.append(outputcsv)
    f = open(outputcsv, "w")
    f.write(rule)
    f.close()

    # Reclass segments raster layer
    gscript.run_command("g.region", raster="clumped_grid")
    gscript.run_command(
        "r.reclass",
        quiet=True,
        input="clumped_grid",
        output="weight_int",
        rules=outputcsv,
    )
    # Get back to the original 'float' prediction of response variable
    #   density of random forest
    gscript.run_command(
        "r.mapcalc",
        expression="%s=float(weight_int)/float(1000000000)" % weighting_layer_name,
        quiet=True,
    )
    gscript.run_command(
        "g.remove", quiet=True, type="raster", name="weight_int", flags="fb"
    )

    # ------------------------------------------------------------------
    # Saving and creating plot of feature importances
    # ------------------------------------------------------------------
    gscript.info(_("Saving feature importances..."))
    # Save feature importances from the model
    importances = regressor.feature_importances_
    indices = np.argsort(importances)[::-1]
    x_axis = importances[indices][::-1]
    idx = indices[::-1]
    y_axis = range(x.shape[1])
    # Set the size of the plot according to the number of features
    plt.figure(figsize=(5, (len(y_axis) + 1) * 0.23))
    plt.scatter(x_axis, y_axis)
    Labels = []
    for i in range(x.shape[1]):
        Labels.append(x_grid.columns[idx[i]])
    # Change the labels of the feature if raster class labels specified
    Labels = labels_from_csv(Labels)
    plt.yticks(y_axis, Labels)
    plt.ylim([-1, len(y_axis)])  # Ajust ylim
    plt.xlim([-0.04, max(x_axis) + 0.04])  # Ajust xlim
    plt.title("Feature importances")

    # Export in .png file (image)
    plt.savefig(plot + ".png", bbox_inches="tight", dpi=400)
    # Export in .svg file (vectorial)
    plt.savefig(plot + ".svg", bbox_inches="tight", dpi=400)
    message = (
        "Final Random Forest model run - internal Out-of-bag "
        "score (OOB) : %0.3f" % regressor.oob_score
    )
    log_text += message + "\n"
    gscript.info(_(message))


def main():
    start_time = time.ctime()
    options, flags = gscript.parser()
    lazy_import()
    gscript.use_temp_region()  # define use of temporary regions

    ## Create global variables
    global TMP_MAPS, TMP_CSV, TMP_VECT, vector_map, allstatfile, min_fimportance, param_grid, kfold, basemap_a, basemap_b, distance_to, tile_size, n_jobs, id, response_variable, plot, log_f, log_text, log_text_extend, basemap_a_category_list, basemap_b_category_list, rasta_class_list, rastb_class_list, output_units_layer

    ## Create empty variables
    raster_list = []  # List of the input rasters
    raster_list_prep = []  # List to rename rasters after pre-processing
    log_text = ""  # Log for random forest
    log_text_extend = ""  # Extended log (flag -f) for random forest

    # ------------------------------------------------------------------
    # Check installation of necessary modules
    # ------------------------------------------------------------------
    gscript.verbose(_("Checking installation of necessary modules..."))
    # Check if i.segment.stats is well installed
    if not gscript.find_program("i.segment.stats", "--help"):
        message = "You first need to install the addon " "i.segment.stats.\n"
        message += "You can install the addon with 'g.extension " "i.segment.stats'"
        gscript.fatal(_(message))
    # Check if r.zonal.classes is well installed
    if not gscript.find_program("r.zonal.classes", "--help"):
        message = _("You first need to install the addon " "r.zonal.classes.\n")
        message += _("You can install the addon with 'g.extension " "r.zonal.classes'")
        gscript.fatal(_(message))
    # Check if r.clip is well installed
    if not gscript.find_program("r.clip", "--help"):
        message = _("You first need to install the addon " "r.clip.\n")
        message += _("You can install the addon with 'g.extension " "r.clip.'")
        gscript.fatal(_(message))
    # ------------------------------------------------------------------
    # Define variables from user's values
    # ------------------------------------------------------------------
    gscript.message(_("Preparing and checking input data..."))
    gscript.verbose(_("Preparing variables from user options flags..."))
    vector_map = options["vector"]
    basemap_a_user = options["basemap_a"]
    basemap_b_user = options["basemap_b"] if options["basemap_b"] else ""
    distance_to = options["distance_to"] if options["distance_to"] else ""
    tile_size = options["tile_size"]
    id = options["id"]
    response_variable = options["response_variable"]
    output_weighting_layer = options["output_weight"]
    output_units_layer = options["output_units"]
    plot = options["plot"]
    log_file = options["log_file"]
    basemap_a_list = (
        options["basemap_a_list"].split(",") if options["basemap_a_list"] else ""
    )
    basemap_b_list = (
        options["basemap_b_list"].split(",") if options["basemap_b_list"] else ""
    )
    n_jobs = int(options["n_jobs"])
    rasta_class_list = 1 if flags["a"] else 0
    rastb_class_list = 1 if flags["b"] else 0
    # Default value = 0.005 i.e. covariates with less than 0.5% of
    #   importance will be removed. If flag active, all covariates
    #   are kept
    min_fimportance = 0.00 if flags["c"] else 0.005
    # Default value is 5-fold cross validation
    kfold = int(options["kfold"]) if options["kfold"] else 5
    if options["param_grid"]:
        try:
            literal_eval(options["param_grid"])
        except:
            gscript.fatal(
                _(
                    "The syntax of the Python dictionary with "
                    "model parameter is not as expected. \nPlease refer "
                    "to the manual"
                )
            )
    param_grid = (
        literal_eval(options["param_grid"])
        if options["param_grid"]
        else {
            "oob_score": [True],
            "bootstrap": [True],
            "max_features": ["sqrt", 0.1, 0.3, 0.5, 0.7, 1],
            "n_estimators": [500, 1000],
        }
    )

    # ------------------------------------------------------------------
    # Check existance & validity of user files and values
    # ------------------------------------------------------------------
    gscript.verbose(_("Checking vaidity of data (existence, type...)..."))
    # basemap_a exists?
    result = gscript.find_file(basemap_a_user, element="cell")
    if not result["file"]:
        gscript.fatal(_("Raster map <%s> not found" % basemap_a_user))
    raster_list.append(basemap_a_user)
    basemap_a = "basemap_a"
    raster_list_prep.append(basemap_a)
    # vector exists?
    result = gscript.find_file(vector_map, element="vector")
    if not result["file"]:
        gscript.fatal(_("Vector map <%s> not found" % vector_map))

    # id column exists?
    if id not in gscript.vector_columns(vector_map).keys():
        gscript.fatal(_("Column '%s' not found in vector <%s>") % (id, vector_map))
    # is id column numeric?
    coltype = gscript.vector_columns(vector_map)[id]["type"]
    if coltype not in ("INTEGER", "DOUBLE PRECISION"):
        gscript.fatal(_("Column <%s> must be integer") % id)
    # response variable column exists?
    if response_variable not in gscript.vector_columns(vector_map).keys():
        gscript.fatal(
            _("Column <%s> not found in vector <%s>") % (response_variable, vector_map)
        )
    # is response variable column numeric?
    coltype = gscript.vector_columns(vector_map)[response_variable]["type"]
    if coltype not in ("INTEGER", "DOUBLE PRECISION"):
        gscript.fatal(_("Column <%s> must be numeric") % (response_variable))
    # response variable column contains values <=0 or NULL?
    for x in gscript.parse_command(
        "v.db.select",
        map=vector_map,
        columns=response_variable,
        null_value="0",
        flags="c",
    ):
        if float(x) <= 0:
            gscript.fatal(
                _(
                    "Response values contained in column <%s> "
                    "cannot be smaller than 1 or have NULL values. \n"
                    "Check manual page for more information."
                )
                % (response_variable)
            )
    # is tile_size different from null?
    if int(tile_size) <= gscript.raster_info(basemap_a_user).nsres:
        gscript.fatal(
            _(
                "Invalid tile size. Tile size must be greater "
                "than basemap_a's resolution. \n"
                "Make sure the resolution of basemap_a is smaller than "
                "the tile size."
            )
        )
    # basemap_b exists
    if basemap_b_user != "":
        result = gscript.find_file(basemap_b_user, element="cell")
        if not result["file"]:
            gscript.fatal(_("Raster map <%s> not found") % basemap_b_user)
        raster_list.append(basemap_b_user)
        basemap_b = "basemap_b"
        raster_list_prep.append(basemap_b)
    else:
        basemap_b = ""
    # basemap_b_list only exists if basemap_b exists?
    if basemap_b_list != "":
        if basemap_b_user == "":
            gscript.warning(
                (
                    "Category list for basemap_b will be "
                    "ignored as basemap_b has not been provided."
                )
            )
    # distance_to exists?
    if distance_to != "":
        result = gscript.find_file(distance_to, element="cell")
        if not result["file"]:
            gscript.fatal(_("Raster map <%s> not found") % distance_to)
    # rastb_class_list only exists if basemap_b exists?
    if rastb_class_list == 1:
        if basemap_b == "":
            rastb_class_list = 0
            gscript.warning(
                _(
                    "Class names for basemap_b will be "
                    "ignored as basemap_b has not been provided."
                )
            )

    gscript.verbose(_("Checking RF parameters..."))
    # 'oob_score' parameter in the dictionary for grid search is True?
    if "oob_score" not in param_grid.keys():
        param_grid["oob_score"] = [True]
    elif param_grid["oob_score"] != [True]:
        param_grid["oob_score"] = [True]
    # Is kfold valid?
    # Corresponds to leave-one-out cross-validation
    maxfold = int(
        gscript.parse_command("v.db.univar", flags="g", map=vector_map, column="cat")[
            "n"
        ]
    )
    if kfold > maxfold:
        gscript.fatal(
            _(
                "<kfold> parameter must be lower than %s "
                "(number of spatial units)" % maxfold
            )
        )
    if kfold < 2:
        gscript.fatal(_("<kfold> parameter must be higher than 2"))
    # Directory for output plot of model's feature importances valid?
    if not os.path.exists(os.path.split(plot)[0]):
        gscript.fatal(
            _(
                "Directory '%s' for output plot of model's "
                "feature importances does not exist. \nPlease specify an "
                "existing directory" % os.path.split(plot)[0]
            )
        )
    # Directory for output file with logging of RF run valid?
    if not os.path.exists(os.path.split(log_file)[0]):
        gscript.fatal(
            _(
                "Directory '%s' for output file with logging "
                "of RF run does not exist. \nPlease specify an existing "
                "directory" % os.path.split(log_file)[0]
            )
        )

    # ------------------------------------------------------------------
    # Create dictionaries and grids
    # ------------------------------------------------------------------
    gscript.verbose(_("Creating empty dictionaries..."))
    # Create a dictionary that will contain the paths of intermediate
    #   files with statistics
    tmp_stat_files = {}
    # Create a dictionary that will contain the paths of files resulting
    #   of the join of intermediates files
    allstatfile = {}
    # Creating a empty grid raster: each grid has a size corresponding
    #   to the "tile_size" parameter
    gscript.verbose(_("Creating empty grid raster..."))
    create_clumped_grid(tile_size)

    # ------------------------------------------------------------------
    # Prepare basemaps & distance map and check raster category lists
    # ------------------------------------------------------------------
    gscript.verbose(_("Preparing input rasters and defining raster categories..."))
    ## Prepare basemaps (clip to zone covered by the vector_map)
    # Ensure extraction of raster categories only within area covered
    #   by spatial units
    clip_basemaps(raster_list, raster_list_prep, vector_map)

    ## Extract list of raster categories for each basemap OR check that
    ##   user provided category list is valid
    if basemap_a_list == "":
        gscript.verbose(_("Classes list will be extracted from <%s>.") % basemap_a)
        # Get a sorted list with values of category in this raster
        basemap_a_category_list = extract_raster_categories(basemap_a)
    else:
        gscript.verbose(
            _("Checking if user provided classes exist in raster <%s>...") % basemap_a
        )
        category_list_check(basemap_a_list, basemap_a)
        basemap_a_category_list = basemap_a_list
        # Make sure the list provided by the user is well sorted
        basemap_a_category_list.sort(key=float)
    # UTF8 coding required for Linux
    if sys.platform == "linux":
        for i, x in enumerate(basemap_a_category_list):
            basemap_a_category_list[i] = x.decode("UTF8")
    message = (
        "Classes of raster '"
        + str(basemap_a_user)
        + "' used: "
        + ",".join(basemap_a_category_list)
    )
    log_text += message + "\n"

    if basemap_b_user != "":
        if basemap_b_list == "":
            gscript.verbose(_("Classes list will be extracted from <%s>.") % basemap_b)
            # Get a sorted list with values of category in this raster
            basemap_b_category_list = extract_raster_categories(basemap_b)
        else:
            gscript.verbose(
                _("Checking if user provided classes exist in raster <%s>...")
                % basemap_b
            )
            category_list_check(basemap_b_list, basemap_b)
            basemap_b_category_list = basemap_b_list
            # Make sure the list provided by the user is well sorted
            basemap_b_category_list.sort(key=float)
        # UTF8 coding required for Linux
        if sys.platform == "linux":
            for i, x in enumerate(basemap_b_category_list):
                basemap_b_category_list[i] = x.decode("UTF8")
        message = (
            "Classes of raster '"
            + str(basemap_b_user)
            + "' used: "
            + ",".join(basemap_b_category_list)
        )
        log_text += message + "\n"

    # ------------------------------------------------------------------
    # Preparing spatial units
    # ------------------------------------------------------------------
    # Rasterize spatial units (so that the resolution corresponds to
    #   the output weighted grid)
    # Then re-vectorise
    gscript.verbose(_("Preparing spatial units..."))
    spatial_boundaries(vector_map.split("@")[0], id)

    # ------------------------------------------------------------------
    # Compute statistics per grid and per spatial unit
    # ------------------------------------------------------------------
    gscript.info(_("Extracting statistics..."))
    gscript.verbose(_("Extracting statistics per grid and spatial unit..."))
    ## Calculate proportion of each class for categorical rasters
    # Categorical raster A
    gscript.run_command("g.region", raster=basemap_a.split("@")[0])
    tmp_stat_files["grid_A"] = gscript.tempfile()
    TMP_CSV.append(tmp_stat_files["grid_A"])
    compute_proportion_csv(
        basemap_a.split("@")[0],
        "clumped_grid",
        "basemapA",
        tmp_stat_files["grid_A"],
    )
    tmp_stat_files["unit_A"] = gscript.tempfile()
    TMP_CSV.append(tmp_stat_files["unit_A"])
    compute_proportion_csv(
        basemap_a.split("@")[0],
        "gridded_spatial_units",
        "basemapA",
        tmp_stat_files["unit_A"],
    )

    # Categorical raster B
    if basemap_b != "":
        # Set the region to match the extent of the raster
        gscript.run_command("g.region", raster=basemap_b.split("@")[0])
        tmp_stat_files["grid_B"] = gscript.tempfile()
        TMP_CSV.append(tmp_stat_files["grid_B"])
        compute_proportion_csv(
            basemap_b.split("@")[0],
            "clumped_grid",
            "basemapB",
            tmp_stat_files["grid_B"],
        )
        tmp_stat_files["unit_B"] = gscript.tempfile()
        TMP_CSV.append(tmp_stat_files["unit_B"])
        compute_proportion_csv(
            basemap_b.split("@")[0],
            "gridded_spatial_units",
            "basemapB",
            tmp_stat_files["unit_B"],
        )

    ## Compute mean value for quantitative raster
    if distance_to != "":
        ## For grids
        tmp_stat_files["grid_C"] = gscript.tempfile()
        TMP_CSV.append(tmp_stat_files["grid_C"])
        gscript.run_command(
            "i.segment.stats",
            quiet=True,
            flags="sc",
            map="clumped_grid",
            rasters=distance_to.split("@")[0],
            raster_statistics="mean",
            csvfile=tmp_stat_files["grid_C"],
            separator="comma",
            overwrite=True,
        )

        ## Use pandas dataframe to remove any rows containing null value
        # Reading the csv file as dataframe
        df = pd.read_csv(tmp_stat_files["grid_C"])
        # Drop rows
        df.dropna(axis=0, how="any", inplace=True)
        # Replace csv
        df.to_csv(tmp_stat_files["grid_C"], index=False)

        ## For spatial units
        tmp_stat_files["unit_C"] = gscript.tempfile()
        TMP_CSV.append(tmp_stat_files["unit_C"])
        gscript.run_command(
            "i.segment.stats",
            quiet=True,
            flags="sc",
            map="gridded_spatial_units",
            rasters=distance_to.split("@")[0],
            raster_statistics="mean",
            csvfile=tmp_stat_files["unit_C"],
            separator="comma",
            overwrite=True,
        )

        ## Use pandas dataframe to remove any rows containing null value
        # Reading the csv file as dataframe
        df = pd.read_csv(tmp_stat_files["unit_C"])
        # Drop rows
        df.dropna(axis=0, how="any", inplace=True)
        # Replace csv
        df.to_csv(tmp_stat_files["unit_C"], index=False)

        # Save log
        log_text += "Distance raster used: " + str(distance_to) + "\n\n"

    # ------------------------------------------------------------------
    # Join .csv files of statistics
    # ------------------------------------------------------------------
    gscript.verbose(_("Join .csv files of statistics..."))
    for zone in ["grid", "unit"]:
        # Create list of .csv files to join
        allstatfile[zone] = gscript.tempfile()
        TMP_CSV.append(allstatfile[zone])
        list_paths = [
            tmp_stat_files["%s_A" % zone],
        ]
        # Add all csv with proportions of classesfrom basemap_b
        if basemap_b != "":
            list_paths.append(tmp_stat_files["%s_B" % zone])
        if distance_to != "":  # Add mean distance
            list_paths.append(tmp_stat_files["%s_C" % zone])
        # Join .csv files
        join_multiplecsv(
            list_paths,
            allstatfile[zone],
            separator=",",
            join="inner",
            fillempty="0.000",
            overwrite=True,
        )

    # ------------------------------------------------------------------
    # Run random forest
    # ------------------------------------------------------------------
    gscript.info(
        _("Random forest model training and prediction. " "This may take some time...")
    )
    RandomForest(output_weighting_layer, vector_map.split("@")[0], id)

    # ------------------------------------------------------------------
    # Export log file
    # ------------------------------------------------------------------
    gscript.info(_("Exporting log file"))
    end_time = time.ctime()
    path, ext = os.path.splitext(log_file)
    if ext != ".txt":
        log_file = log_file + ".txt"
    logging = open(log_file, "w")
    logging.write("Log file of r.area.createweight\n")
    logging.write(
        "Run started on "
        + str(start_time)
        + " and finished "
        + "on "
        + str(end_time)
        + "\n"
    )
    logging.write(
        "Selected spatial resolution for weightarea_tableing layer : "
        + tile_size
        + " meters\n"
    )
    logging.write("Spatial units layer used : %s \n" % vector_map)
    logging.write(log_text)
    if flags["f"]:
        logging.write("\n")
        logging.write(log_text_extend)
    logging.close()

    gscript.del_temp_region()  # Remove temporary region
    gscript.message(
        _(
            "Run started on "
            + str(start_time)
            + " and "
            + "finished on "
            + str(end_time)
            + "\n"
        )
    )


if __name__ == "__main__":

    atexit.register(cleanup)
    sys.exit(main())
