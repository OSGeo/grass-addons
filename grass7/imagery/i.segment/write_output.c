/* transfer the segmented regions from the segmented data file to a raster file */
/* put closing segment files here for now, OK to combine or better to put somewhere else? */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/segment.h> /* segmentation library */
#include "iseg.h"

int write_output(struct files *files)
{
	int out_fd, row, n;
	void *outbuf;
	outbuf = Rast_allocate_buf(files->data_type); 

	/* Todo: return codes are 1 for these, need to check and react to errors? programmer's manual didn't include it... */
	
	segment_flush(&files->out_seg); /* force all data to disk */
	
	
	/* open output raster map */
	out_fd = Rast_open_new(files->out_name, files->data_type); /* I assume even if it already exists, this will overwrite it... */
	
	/* transfer data row by row */
	for (row = 0; row < 100; row++) /* need to acces nrows, syntax?  files->out_seg::nrows  ??? */
	{
		segment_get_row (&files->out_seg, outbuf, row); //segment_get_row (SEGMENT *seg, char *buf, int row)
		Rast_put_row(out_fd, outbuf, files->data_type);
	}
	
	/* close segmentation files and output raster */
	
	for(n = 0; n < files->nbands; n++)
	{
		segment_release (&files->bands_seg[n]);
	}
	segment_release (&files->out_seg);
	close (out_fd);

/* TODO Note: The Segment Library does not know the name of the segment file. It does not attempt to remove the file. If the file is only temporary, the programmer should remove the file after closing it. */

/* anything else left to clean up? */

	return 0;
}
