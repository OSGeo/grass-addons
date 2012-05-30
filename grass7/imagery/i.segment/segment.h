/****************************************************************************
 *
 * MODULE:       i.segment
 * AUTHOR(S):    Eric Momsen <eric.momsen at gmail com>
 * PURPOSE:      global variable and function listing
 * COPYRIGHT:    (C) 2012 by Eric Momsen, and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the COPYING file that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

extern struct GModule *module;
extern struct Option *input, *seeds, *output, *method, *threshold;

/* get_input.c */
int get_input(int, char *[]);
