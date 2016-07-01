/* draw.c:
 *
 *    With do_bg=1 compute position of all legend graphic item and draw only background.
 *    Eith do_bg=0 compute position of all legend graphic item and draw all.
 *
 *    Copyright (C) 2016 by Adam Laza, GSoC 2016, and the GRASS Development Team*
 *    This program is free software under the GPL (>=v2)
 *    Read the COPYING file that comes with GRASS for details.
 */

#include <string.h>
#include <grass/display.h>
#include <grass/glocale.h>
#include <grass/colors.h>
#include "local_proto.h"

void draw(char *file_name, char *sep, double LL, double LT, char *title, int bgcolor, int bcolor,
          int do_bg, char* tit_font, int tit_size, char *sub_font, int sub_size, char *font,
          int fontsize, int fontcolor)
{
    double db, dt, dl, dr;
    double bb, bt, bl, br;
    double x0, y0;
    double offs_y, row_ind;
    FILE *file_in;
    char buf[512];
    int got_new;
    SYMBOL *Symb;
    char *symb_name, *line_color_str, *fill_color_str, *label;
    double size, line_width;
    double row_w, row_h;
    RGBA_Color *line_color, *fill_color;
    int ret, R, G, B;
    char *part, *sub_delim;
    double maxlblw, sym_lbl_space;



    D_get_src(&dt, &db, &dl, &dr);
    x0 = dl + (int)((dr - dl) * LL / 100.);
    y0 = dt + (int)((db - dt) * (100 - LT) / 100.);

    maxlblw = 0;
    offs_y = 0;

    /* Draw title */
    if (strlen(title) > 0) {
        D_text_size(tit_size, tit_size);
        D_font(tit_font);
        D_get_text_box(title, &bb, &bt, &bl, &br);
        row_h = bb - bt;
        offs_y += row_h;
        maxlblw = br - bl;
        if (! do_bg) {
            D_pos_abs(x0, y0 + offs_y);
            D_use_color(fontcolor);
            D_text(title);
        }
    }

    file_in = fopen(file_name, "r");
    if (!file_in)
        G_fatal_error(_("Unable to open input file <%s>"), file_name);

    row_ind = 5;
    sym_lbl_space = 5;
    sub_delim = G_malloc(strlen(buf)+1);
    snprintf(sub_delim, sizeof(sub_delim), "%s%s%s%s%s", sep, sep, sep, sep, sep);

    got_new = G_getl2(buf, sizeof(buf), file_in);
    G_strip(buf);
    while (got_new) {
        if (strstr(buf, sub_delim) != NULL) {
            label = G_malloc(strlen(buf)+1);
            part = strtok(buf, sep);
            sscanf(part, "%s", label);

            D_text_size(sub_size, sub_size);
            D_font(sub_font);
            D_get_text_box(label, &bb, &bt, &bl, &br);
            row_h = bb - bt;
            row_w = br - bb;
            offs_y += row_h + row_ind;
            if (row_w > maxlblw)
                maxlblw = row_w;

            if (! do_bg) {
                D_pos_abs(x0, y0 + offs_y);
                D_use_color(fontcolor);
                D_text(label);
            }
        }
        else {
            /* Parse the line */
            symb_name = G_malloc(strlen(buf) + 1);
            line_color_str = G_malloc(strlen(buf) + 1);
            fill_color_str = G_malloc(strlen(buf) + 1);
            label = G_malloc(strlen(buf)+1);
            line_color = G_malloc(sizeof(RGBA_Color));
            fill_color = G_malloc(sizeof(RGBA_Color));

            part = strtok(buf, sep);
            sscanf(part, "%s", symb_name);
            part = strtok(NULL, sep);
            sscanf(part, "%s", line_color_str);
            part = strtok(NULL, sep);
            sscanf(part, "%s", fill_color_str);
            part = strtok(NULL, sep);
            sscanf(part, "%lf", &size);
            part = strtok(NULL, sep);
            sscanf(part, "%lf", &line_width);
            part = strtok(NULL, sep);
            sscanf(part, "%s", label);

            /* Symbol */
            Symb = S_read(symb_name);
            if (Symb == NULL)
                G_warning(_("Cannot read symbol"));
            else
                S_stroke(Symb, size, 0, 0);
            /* parse line color */
            ret = G_str_to_color(line_color_str, &R, &G, &B);
            line_color->r = (unsigned char)R;
            line_color->g = (unsigned char)G;
            line_color->b = (unsigned char)B;
            if (ret == 1)
                /* here alpha is only used as an on/off switch, otherwise unused by the display drivers */
                line_color->a = RGBA_COLOR_OPAQUE;
            else if (ret == 2)
                line_color->a = RGBA_COLOR_NONE;
            else
                G_warning(_("[%s]: No such color"), line_color_str);
            /* parse fill color */
            ret = G_str_to_color(fill_color_str, &R, &G, &B);
            fill_color->r = (unsigned char)R;
            fill_color->g = (unsigned char)G;
            fill_color->b = (unsigned char)B;
            if (ret == 1)
                fill_color->a = RGBA_COLOR_OPAQUE;
            else if (ret == 2)
                fill_color->a = RGBA_COLOR_NONE;
            else
                G_warning(_("[%s]: No such color"), fill_color_str);

            /* Label */
            D_text_size(fontsize, fontsize);
            D_font(font);
            D_get_text_box(label, &bb, &bt, &bl, &br);
            row_h = bb - bt;
            row_w = row_h + sym_lbl_space + br - bb;
            offs_y += row_h + row_ind;
            if (row_w > maxlblw)
                maxlblw = row_w;

            if (! do_bg) {
                S_stroke(Symb, size, 0, 0);
                D_symbol(Symb, x0 + row_h/2, y0 + offs_y - row_h/2, line_color, fill_color);

                D_pos_abs(x0 + row_h + sym_lbl_space, y0 + offs_y);
                D_use_color(fontcolor);
                D_text(label);
            }
        } /* end of Parse the line */

        got_new = G_getl2(buf, sizeof(buf), file_in);
        G_strip(buf);
    }

    //            // Pomocny ctverec
    //            D_begin();
    //            D_move_abs(x0, y0 + offs_y);
    //            D_cont_abs(x0 + row_h, y0 + offs_y);
    //            D_cont_abs(x0 + row_h, y0 + offs_y - row_h);
    //            D_cont_abs(x0, y0 + offs_y - row_h);
    //            D_close();
    //            D_end();
    //            D_stroke();
    //            // Pomocny ctverec

    fclose(file_in);

    /* Draw background */
    if (do_bg) {
        double x0bg, y0bg, x1bg, y1bg, bg_margin;
        bg_margin = 10;
        x0bg = x0 - bg_margin;
        y0bg = y0 - bg_margin;
        x1bg = x0 + maxlblw + bg_margin;
        y1bg = y0 + offs_y + bg_margin;

        if (bgcolor) {
            D_use_color(bgcolor);
            D_box_abs(x0bg, y0bg, x1bg, y1bg);
        }

        D_use_color(bcolor);
        D_begin();
        D_move_abs(x0bg, y0bg);
        D_cont_abs(x0bg, y1bg);
        D_cont_abs(x1bg, y1bg);
        D_cont_abs(x1bg, y0bg);
        D_close();
        D_end();
        D_stroke();
    }

    D_save_command(G_recreate_command());
}
