
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

#include <grass/gis.h>
#include <grass/config.h>
#include <grass/glocale.h>

#ifdef HAVE_SYS_IOCTL_H
#  include <sys/ioctl.h>
#endif

typedef int ls_filter_func(const char * /*filename */ , void * /*closure */ );
static ls_filter_func *ls_filter = NULL;
static void *ls_closure = NULL;

static int cmp_names(const void *aa, const void *bb)
{
    char *const *a = (char *const *)aa;
    char *const *b = (char *const *)bb;

    return strcmp(*a, *b);
}

/**
 * \brief Sets a function and its complementary data for G__ls filtering.
 *
 * Defines a filter function and its rule data that allow G__ls to filter out
 * unwanted file names.  Call this function before G__ls.
 *
 * \param func      Filter callback function to compare a file name and closure
 * 		    pattern (if NULL, no filter will be used).
 * 		    func(filename, closure) should return 1 on success, 0 on
 * 		    failure.
 * \param closure   Data used to determine if a file name matches the rule.
 **/

void G_set_ls_filter(ls_filter_func * func, void *closure)
{
    ls_filter = func;
    ls_closure = closure;
    return;
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

char **G__ls(const char *dir, int *num_files)
{
    struct dirent *dp;
    DIR *dfd;
    char **dir_listing = NULL;
    int n = 0;

    if ((dfd = opendir(dir)) == NULL)
	G_fatal_error(_("Unable to open directory %s"), dir);

    while ((dp = readdir(dfd)) != NULL) {
	if ((dp->d_name[0] == '.' && dp->d_name[1] == 0) ||
	    (dp->d_name[0] == '.' && dp->d_name[1] == '.' &&
	     dp->d_name[2] == 0) || (ls_filter &&
				     !(*ls_filter) (dp->d_name, ls_closure)))
	    continue;
	dir_listing = (char **)G_realloc(dir_listing, (1 + n) * sizeof(char *));
	dir_listing[n] = G_store(dp->d_name);
	n++;
    }

    /* Sort list of filenames alphabetically */
    qsort(dir_listing, n, sizeof(char *), cmp_names);

    *num_files = n;
    return dir_listing;
}
