#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include "convexhull.h"

#include <grass/imagery.h>
#include <grass/gis.h>
#include <string.h>

void add_file_to_group(const char *group, const char *raster, const char *mapset)
{
    struct Ref group_ref;
    int maxfiles;

    // Get current group reference
    if (I_get_group_ref(group, &group_ref) < 0) {
        G_fatal_error(_("Unable to read group <%s>"), group);
    }

    I_add_file_to_group_ref(raster, mapset, &group_ref);

    // Write back the updated group
    if (I_put_group_ref(group, &group_ref) < 0) {
        G_fatal_error(_("Unable to write group <%s>"), group);
    }
}

void create_group(const char *group_name)
{
    struct Ref group_ref;
    group_ref.nfiles = 0;
    group_ref.file = NULL; // No rasters initially

    // This creates the group (writes the REF file)
    if (I_put_group_ref(group_name, &group_ref) < 0) {
        G_fatal_error(_("Unable to create group <%s>"), group_name);
    }
}

int main(int argc, char *argv[]) {
    struct GModule *module;
    struct Option *input_group, *output_group, *output_basefilename;
    struct Ref ref;
    int i, row, col;
    int nrows, ncols;

    int infd[MAXFILES];
    int outfd[MAXFILES];
    void *inbuf[MAXFILES];
    void *outbuf[MAXFILES];
    char outname[MAXFILES][GNAME_MAX];

    double din[MAXFILES];    // Input spectrum for each pixel
    double dout[MAXFILES];   // Output spectrum for each pixel

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("spectral"));
    G_add_keyword(_("continuum removal"));
    module->description = _("Applies continuum removal to each band in an imagery group and outputs a new imagery group.");
    
    // Groups: Input and Output
    input_group = G_define_standard_option(G_OPT_I_GROUP);
    input_group->key = "input_group";
    output_group = G_define_standard_option(G_OPT_I_GROUP); 
    output_group->key = "output_group";

    // Define base filename for output rasters
    output_basefilename = G_define_option();
    output_basefilename->key = "outputbasename";
    output_basefilename->type = TYPE_STRING;
    output_basefilename->required = YES;
    output_basefilename->answer = "convexhull";
    output_basefilename->description = _("Base name for output files");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    // Read the input group
    I_get_group_ref(input_group->answer, &ref);
    if (ref.nfiles <= 0)
        G_fatal_error(_("No files in group <%s>"), input_group->answer);

    if (ref.nfiles > MAXFILES)
        G_fatal_error(_("Too many files in group (%d > %d)"), ref.nfiles, MAXFILES);


    // Open input rasters and allocate buffers
    for (i = 0; i < ref.nfiles; i++) {
        if ((infd[i] = Rast_open_old(ref.file[i].name, ref.file[i].mapset)) < 0)
            G_fatal_error(_("Unable to open raster map <%s>"), ref.file[i].name);
        if (!(inbuf[i] = Rast_allocate_buf(DCELL_TYPE)))
            G_fatal_error(_("Unable to allocate input buffer"));
        if (!(outbuf[i] = Rast_allocate_buf(DCELL_TYPE)))
            G_fatal_error(_("Unable to allocate output buffer"));
        snprintf(outname[i], GNAME_MAX, "%s_%s", output_group->answer, ref.file[i].name);
        if ((outfd[i] = Rast_open_new(outname[i], DCELL_TYPE)) < 0)
            G_fatal_error(_("Unable to create raster map <%s>"), outname[i]);
    }
    // Load nrows and ncols
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    
    // Process by row
    for (row = 0; row < nrows; row++) {
        // Read input rows
        for (i = 0; i < ref.nfiles; i++) {
            Rast_get_row(infd[i], inbuf[i], row, DCELL_TYPE);
        }
        // Process each column (pixel spectrum reconstitution)
	//#pragma omp parallel for private(i, din, dout)
        for (col = 0; col < ncols; col++) {
            // Gather spectrum for this pixel across all bands
            for (i = 0; i < ref.nfiles; i++) {
                din[i] = ((double *)inbuf[i])[col];
            }
            // Process convex hull per spectrum
            convexhull(din, dout, ref.nfiles);  

            // Write to pixel spectrum output buffer
            for (i = 0; i < ref.nfiles; i++) {
                ((DCELL *)outbuf[i])[col] = dout[i];
            }
        }
        // Write output rows
        for (i = 0; i < ref.nfiles; i++) {
            Rast_put_row(outfd[i], outbuf[i], DCELL_TYPE);
        }
    }

    // Clean the output_group from any pre-existing list
    if (I_find_group(output_group->answer)) {
        if (!G_check_overwrite(argc, argv)) {
            G_fatal_error(_("Group <%s> exists. Use --overwrite to replace."), output_group->answer);
        }
        // Proceed to overwrite
	create_group(output_group->answer);
    } else {
        // Proceed to create
	create_group(output_group->answer);
    }

    // Close files and add to group
    for (i = 0; i < ref.nfiles; i++) {
	add_file_to_group(output_group->answer, outname[i], G_mapset());
        G_free(inbuf[i]);
        G_free(outbuf[i]);
        if (infd[i] >= 0) Rast_close(infd[i]);
        if (outfd[i] >= 0) Rast_close(outfd[i]);
    }
    return EXIT_SUCCESS;
}
