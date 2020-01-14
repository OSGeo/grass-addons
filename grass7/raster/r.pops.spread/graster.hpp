/*
 * PoPS model - Reading and writing GRASS GIS rasters as Raster
 *
 * Copyright (C) 2019 by the authors.
 *
 * Authors: Vaclav Petras (wenzeslaus gmail com)
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef GRASTER_HPP
#define GRASTER_HPP

#include "pops/raster.hpp"
#include "pops/date.hpp"

extern "C" {
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
}

#include <string>

void date_to_grass(pops::Date date, struct TimeStamp* timestamp)
{
    struct DateTime date_time;
    datetime_set_type(&date_time, DATETIME_ABSOLUTE,
                      DATETIME_YEAR, DATETIME_DAY, 0);
    datetime_set_year(&date_time, date.year());
    datetime_set_month(&date_time, date.month());
    datetime_set_day(&date_time, date.day());
    G_init_timestamp(timestamp);
    G_set_timestamp(timestamp, &date_time);
}

// The right C function to call in function templates is picked using
// the following overloads based on the type of buffer.

/** Overload for get row function */
inline void grass_raster_get_row(int fd, DCELL* buffer, int row)
{
    Rast_get_d_row(fd, buffer, row);
}

/** Overload for get row function */
inline void grass_raster_get_row(int fd, FCELL* buffer, int row)
{
    Rast_get_f_row(fd, buffer, row);
}

/** Overload for get row function */
inline void grass_raster_get_row(int fd, CELL* buffer, int row)
{
    Rast_get_c_row(fd, buffer, row);
}

/** Overload for put row function */
inline void grass_raster_put_row(int fd, DCELL* buffer)
{
    Rast_put_d_row(fd, buffer);
}

/** Overload for put row function */
inline void grass_raster_put_row(int fd, FCELL* buffer)
{
    Rast_put_f_row(fd, buffer);
}

/** Overload for put row function */
inline void grass_raster_put_row(int fd, CELL* buffer)
{
    Rast_put_c_row(fd, buffer);
}

/** Read a GRASS GIS raster map to the Raster
 *
 * The caller is required to specify the type of the raster as a
 * template parameter:
 *
 * ```
 * raster_from_grass<double>(name)
 * ````
 *
 * Given the types of GRASS GIS raster maps, it supports only
 * int, float, and double (CELL, FCELL, and DCELL).
 */
template<typename Number>
inline pops::Raster<Number> raster_from_grass(const char* name)
{
    unsigned rows = Rast_window_rows();
    unsigned cols = Rast_window_cols();
    pops::Raster<Number> rast(rows, cols);
    Number* data = rast.data();

    int fd = Rast_open_old(name, "");
    for (unsigned row = 0; row < rows; row++) {
        grass_raster_get_row(fd, data + (row * cols), row);
    }
    Rast_close(fd);

    return rast;
}

/** Overload of raster_from_grass(const char *) */
template<typename Number>
inline pops::Raster<Number> raster_from_grass(const std::string& name)
{
    return raster_from_grass<Number>(name.c_str());
}

/** Write a Raster to a GRASS GIS raster map.
 *
 * When used, the template is resolved based on the parameter.
 */
template<typename Number>
void inline raster_to_grass(pops::Raster<Number> raster,
                            const char* name,
                            const char* title = nullptr,
                            struct TimeStamp* timestamp = nullptr)
{
    Number* data = raster.data();
    unsigned rows = raster.rows();
    unsigned cols = raster.cols();

    int fd = Rast_open_new(name, DCELL_TYPE);
    for (unsigned i = 0; i < rows; i++)
        grass_raster_put_row(fd, data + (i * cols));
    Rast_close(fd);

    // writing map title and history
    if (title)
        Rast_put_cell_title(name, title);
    struct History history;
    Rast_short_history(name, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(name, &history);
    if (timestamp)
        G_write_raster_timestamp(name, timestamp);
    else
        G_remove_raster_timestamp(name);
    // we remove timestamp, because overwriting does not remove it
    // it is a no-op when it does not exist
}

/** Overload of raster_to_grass() */
template<typename Number>
inline void raster_to_grass(pops::Raster<Number> raster,
                            const std::string& name)
{
    raster_to_grass<Number>(raster, name.c_str());
}

/** Overload of raster_to_grass() */
template<typename Number>
inline void raster_to_grass(pops::Raster<Number> raster,
                            const std::string& name,
                            const std::string& title)
{
    raster_to_grass<Number>(raster, name.c_str(), title.c_str());
}

/** Overload of raster_to_grass()
 *
 * Converts PoPS date to GRASS GIS timestamp.
 */
template<typename Number>
inline void raster_to_grass(pops::Raster<Number> raster,
                            const std::string& name,
                            const std::string& title,
                            const pops::Date& date)
{
    struct TimeStamp timestamp;
    date_to_grass(date, &timestamp);
    raster_to_grass<Number>(raster, name.c_str(), title.c_str(),
                            &timestamp);
}

// these two determine the types of numbers used to represent the
// rasters (using terminology already used in the library)
typedef double Float;
typedef int Integer;

// The following wrappers are to avoid the need specify template
// parameters using the <> syntax and it is one place to change
// the types being read.
// The string parameter is a template parameter which in turn is used
// to find the right function template overload, so there is no extra
// cost when using const char* as it would be if we use
// const std::string& as parameter while supporting both.

/** Wrapper to read GRASS GIS raster into floating point Raster */
template<typename String>
inline pops::Raster<Float> raster_from_grass_float(String name)
{
    return raster_from_grass<Float>(name);
}

/** Wrapper to read GRASS GIS raster into integer type Raster */
template<typename String>
inline pops::Raster<Integer> raster_from_grass_integer(String name)
{
    return raster_from_grass<Integer>(name);
}

// TODO: update names
// convenient definitions, names for backwards compatibility
typedef pops::Raster<Integer> Img;
typedef pops::Raster<Float> DImg;

#endif // GRASTER_HPP
