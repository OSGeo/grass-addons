
/**
   \file ls.c

   \brief Functions to list the files in a directory.

   \author Paul Kelly, Huidae Cho
   
   (C) 2007, 2008 by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the file COPYING that comes with GRASS
   for details.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <dirent.h>
#include <unistd.h>
#include <regex.h>

#include <grass/gis.h>
#include <grass/config.h>
#include <grass/glocale.h>

#ifdef HAVE_SYS_IOCTL_H
#  include <sys/ioctl.h>
#endif


#define LS_FILTER_FLAGS REG_EXTENDED|REG_NOSUB
static char *ls_filter = NULL;

static int cmp_names(const void *aa, const void *bb)
{
    char *const *a = (char *const *)aa;
    char *const *b = (char *const *)bb;

    return strcmp(*a, *b);
}

/**
 * \brief Sets a filter for G__ls using POSIX Extended Regular Expressions.
 * 
 * Defines the pattern that allows G__ls to filter out unwanted file names.
 * Call this function before G__ls.
 *
 * \param pattern   POSIX Extended Regular Expressions
 * 		    (if NULL, no filter will be used)
 **/
void G_set_ls_filter(const char *pattern)
{
    regex_t reg;

    if (ls_filter)
	G_free(ls_filter);
    if (pattern) {
	ls_filter = G_strdup(pattern);
	if (regcomp(&reg, ls_filter, LS_FILTER_FLAGS) != 0)
	    G_fatal_error(_("Unable to compile regular expression %s"),
			  ls_filter);
	regfree(&reg);
    }
    else
	ls_filter = NULL;

    return;
}

/**
 * \brief Gets a filter string for G__ls.
 * 
 * Returns the filter pattern defined by G_set_ls_filter.
 *
 * \return          Filter pattern
 **/
const char *G_get_ls_filter(void)
{
    return ls_filter;
}

/**
 * \brief Stores a sorted directory listing in an array
 * 
 * The filenames in the specified directory are stored in an array of
 * strings, then sorted alphabetically. Each filename has space allocated
 * using G_store(), which can be freed using G_free() if necessary. The
 * same goes for the array itself.
 * 
 * 
 * \param dir       Directory to list
 * \param num_files Pointer to an integer in which the total number of
 *                  files listed will be stored
 * 
 * \return          Pointer to array of strings containing the listing
 **/

const char **G__ls(const char *dir, int *num_files)
{
    struct dirent *dp;
    DIR *dfd;
    const char **dir_listing = NULL;
    int n = 0;
    regex_t reg;

    if ((dfd = opendir(dir)) == NULL)
	G_fatal_error(_("Unable to open directory %s"), dir);

    if (ls_filter && regcomp(&reg, ls_filter, LS_FILTER_FLAGS) != 0)
	G_fatal_error(_("Unable to compile regular expression %s"),
		      ls_filter);

    while ((dp = readdir(dfd)) != NULL) {
	if (dp->d_name[0] != '.' &&	/* Don't list hidden files */
	    (ls_filter == NULL || regexec(&reg, dp->d_name, 0, NULL, 0) == 0)) {
	    dir_listing = (const char **)G_realloc(dir_listing,
						   (1 + n) * sizeof(char *));
	    dir_listing[n] = G_store(dp->d_name);
	    n++;
	}
    }

    if (ls_filter)
	regfree(&reg);

    /* Sort list of filenames alphabetically */
    qsort(dir_listing, n, sizeof(char *), cmp_names);

    *num_files = n;
    return dir_listing;
}
