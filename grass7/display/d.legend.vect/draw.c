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
#include <math.h>
#include <grass/display.h>
#include <grass/glocale.h>
#include <grass/colors.h>
#include "local_proto.h"

void draw(char *file_name, double LL, double LT, char *title, int cols, int bgcolor,
          int bcolor, int do_bg, char* tit_font, int tit_size, char *sub_font, int sub_size,
          char *font, int fontsize, int fontcolor, int symb_size)
{
    double db, dt, dl, dr;
    double bb, bt, bl, br;
    double x0, y0;
    double offs_y, row_ind, offs_x;
    double x, y;
    FILE *file_in;
    char buf[512];
    int got_new;
    SYMBOL *Symb;
    char *symb_name, *line_color_str, *fill_color_str, *label, *type_str;
    double size, line_width;
    double row_w, text_h, title_h, title_w;
    RGBA_Color *line_color, *fill_color;
    int ret, R, G, B;
    char *part, *sub_delim;
    double maxlblw, sym_lbl_space;
    double symb_h, symb_w, max_symb_w;
    int item_count, item;
    double it_per_col;
    double margin, bg_h, bg_w;
    char *sep;
    int type_count;


    D_get_src(&dt, &db, &dl, &dr);
    x0 = dl + (int)((dr - dl) * LL / 100.);
    y0 = dt + (int)((db - dt) * (100 - LT) / 100.);

    /* Draw title */
    title_h = 0;
    if (strlen(title) > 0) {
        D_font(tit_font);
        D_text_size(tit_size, tit_size);
        D_get_text_box(title, &bb, &bt, &bl, &br);
        margin = 10;
        title_h = bb - bt;
        title_w = br - bl;
        if (! do_bg) {
            x = x0;
            y = y0 + title_h;
            D_pos_abs(x, y);
            D_use_color(fontcolor);
            D_text(title);
        }
    }

    file_in = fopen(file_name, "r");
    sep = "|";
    if (!file_in)
        G_fatal_error(_("Unable to open input file <%s>"), file_name);

    /* Get number of legend row(item) and the biggest symbol*/
    item_count = 0;
    max_symb_w = 0;

    got_new = G_getl2(buf, sizeof(buf), file_in);
    G_strip(buf);
    while (got_new) {
        /* Get the maximum symbol size */
        label = G_malloc(strlen(buf) + 1);
        symb_name = G_malloc(strlen(buf) + 1);

        part = strtok(buf, sep);
        sscanf(part, "%s", label);
        part = strtok(NULL, sep);
        sscanf(part, "%s", symb_name);
        part = strtok(NULL, sep);
        sscanf(part, "%lf", &size);


        /* Symbol */
        if ((strcmp(symb_name,"legend/area")==0) || (strcmp(symb_name,"legend/line")==0))
            size = symb_size;
        Symb = S_read(symb_name);
        if (Symb == NULL)
            G_warning(_("Cannot read symbol"));
        else
            S_stroke(Symb, size, 0, 0);
        symb_w = Symb->xscale * size * 2;

        if (symb_w > max_symb_w)
                max_symb_w = symb_w;

        item_count++;
        got_new = G_getl2(buf, sizeof(buf), file_in);
        G_strip(buf);
    }
    rewind(file_in);
    it_per_col = ceil(item_count / (cols * 1.0));

    bg_h = 0;
    maxlblw = 0;
    offs_y = title_h;
    sym_lbl_space = 15;
    item = 0;
    offs_x = 0;
    margin = 10;
    sub_delim = G_malloc(strlen(buf)+1);
    snprintf(sub_delim, sizeof(strlen(buf)+1), "%s%s%s%s%s", sep, sep, sep, sep, sep);

    got_new = G_getl2(buf, sizeof(buf), file_in);
    G_strip(buf);

    while (got_new) {
        if (item < it_per_col){
            row_ind = 5;
            item++;
        }
        else {
            if (bg_h < offs_y)
                bg_h = offs_y + symb_h/2.;
            offs_x += maxlblw + margin;
            offs_y = title_h + row_ind;
            maxlblw = 0;
            item = 1;
            row_ind = 0;
        }
        if (strstr(buf, sub_delim) != NULL) {
            /* Group subtitle */
            label = G_malloc(strlen(buf)+1);
            part = strtok(buf, sep);
            sscanf(part, "%s", label);

            D_text_size(sub_size, sub_size);
            D_font(sub_font);
            D_get_text_box(label, &bb, &bt, &bl, &br);
            text_h = bb - bt;
            row_w = br - bl;
            offs_y += text_h + row_ind;
            if (bg_h < offs_y)
                bg_h = offs_y + symb_h/2.;
            if (row_w > maxlblw)
                maxlblw = row_w;

            if (! do_bg) {
                x = x0 + offs_x;
                y = y0 + offs_y;
                D_pos_abs(x, y);
                D_use_color(fontcolor);
                D_text(label);
            }
        }
        else {
            /* Map layers */
            symb_name = G_malloc(strlen(buf) + 1);
            type_str = G_malloc(strlen(buf) + 1);
            line_color_str = G_malloc(strlen(buf) + 1);
            fill_color_str = G_malloc(strlen(buf) + 1);
            label = G_malloc(strlen(buf)+1);
            line_color = G_malloc(sizeof(RGBA_Color));
            fill_color = G_malloc(sizeof(RGBA_Color));

            part = strtok(buf, sep);
            sscanf(part, "%s", label);
            part = strtok(NULL, sep);
            sscanf(part, "%s", symb_name);
            part = strtok(NULL, sep);
            sscanf(part, "%lf", &size);
            part = strtok(NULL, sep);
            sscanf(part, "%s", line_color_str);
            part = strtok(NULL, sep);
            sscanf(part, "%s", fill_color_str);
            part = strtok(NULL, sep);
            sscanf(part, "%lf", &line_width);
            part = strtok(NULL, sep);
            sscanf(part, "%s", type_str);
            part = strtok(NULL, sep);
            sscanf(part, "%d", &type_count);

            /* Symbol */
            if ((strcmp(symb_name,"legend/area")==0) || (strcmp(symb_name,"legend/line")==0))
                size = symb_size;
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

            symb_h = Symb->yscale * size * 2;
            text_h = bb - bt;
            row_w = max_symb_w + sym_lbl_space + br - bl;
            if (symb_h >= text_h)
                offs_y += symb_h + row_ind;
            else
                offs_y += text_h + row_ind;

            if (bg_h <= offs_y)
                bg_h = offs_y + symb_h/2.;
            if (row_w > maxlblw)
                maxlblw = row_w;

            if (! do_bg) {
                S_stroke(Symb, size, 0, 0);
                x = x0 + offs_x + max_symb_w/2.;
                y = y0 + offs_y - symb_h/2;
                D_symbol(Symb, x, y, line_color, fill_color);

                x = x0 + offs_x + max_symb_w + sym_lbl_space;
                y = y0 + offs_y - symb_h/2. + text_h/2.;
                D_pos_abs(x, y);
                D_use_color(fontcolor);
                D_text(label);
            }
        }

        got_new = G_getl2(buf, sizeof(buf), file_in);
        G_strip(buf);
    }

    fclose(file_in);

    /* Draw background */
    if (do_bg) {
        double x0bg, y0bg, x1bg, y1bg;
        if (title_w > offs_x + maxlblw)
            bg_w = title_w;
        else
            bg_w = offs_x + maxlblw;

        x0bg = x0 - margin;
        y0bg = y0 - margin;
        x1bg = x0 + bg_w + margin;
        y1bg = y0 + bg_h + margin;

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
