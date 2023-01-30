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
#include <type_traits>

/** Convert pops::Date to GRASS GIS TimeStamp */
void date_to_grass(pops::Date date, struct TimeStamp *timestamp)
{
    struct DateTime date_time;
    datetime_set_type(&date_time, DATETIME_ABSOLUTE, DATETIME_YEAR,
                      DATETIME_DAY, 0);
    datetime_set_year(&date_time, date.year());
    datetime_set_month(&date_time, date.month());
    datetime_set_day(&date_time, date.day());
    G_init_timestamp(timestamp);
    G_set_timestamp(timestamp, &date_time);
}

// The right C function to call in function templates is picked using
// the following overloads based on the type of buffer.

/** Overload for get row function */
inline void grass_raster_get_row(int fd, DCELL *buffer, int row)
{
    Rast_get_d_row(fd, buffer, row);
}

/** Overload for get row function */
inline void grass_raster_get_row(int fd, FCELL *buffer, int row)
{
    Rast_get_f_row(fd, buffer, row);
}

/** Overload for get row function */
inline void grass_raster_get_row(int fd, CELL *buffer, int row)
{
    Rast_get_c_row(fd, buffer, row);
}

/** Overload for is null value function */
inline bool grass_raster_is_null_value(const DCELL *value)
{
    return Rast_is_d_null_value(value);
}

/** Overload for is null value function */
inline bool grass_raster_is_null_value(const FCELL *value)
{
    return Rast_is_f_null_value(value);
}

/** Overload for is null value function */
inline bool grass_raster_is_null_value(const CELL *value)
{
    return Rast_is_c_null_value(value);
}

/** Set a value to zero (0) if it is null (GRASS GIS NULL) */
template <typename Number>
inline void set_null_to_zero(Number *value)
{
    if (grass_raster_is_null_value(value))
        *value = 0;
}

/** Overload for put row function */
inline void grass_raster_put_row(int fd, DCELL *buffer)
{
    Rast_put_d_row(fd, buffer);
}

/** Overload for put row function */
inline void grass_raster_put_row(int fd, FCELL *buffer)
{
    Rast_put_f_row(fd, buffer);
}

/** Overload for put row function */
inline void grass_raster_put_row(int fd, CELL *buffer)
{
    Rast_put_c_row(fd, buffer);
}

/** Overload for set null value function */
inline void grass_raster_set_null(DCELL *buffer, int num_values = 1)
{
    Rast_set_d_null_value(buffer, num_values);
}

/** Overload for set null value function */
inline void grass_raster_set_null(FCELL *buffer, int num_values = 1)
{
    Rast_set_f_null_value(buffer, num_values);
}

/** Overload for set null value function */
inline void grass_raster_set_null(CELL *buffer, int num_values = 1)
{
    Rast_set_c_null_value(buffer, num_values);
}

/** Policy settings for handling null values in the input */
enum class NullInputPolicy {
    NullsAsZeros, ///< Convert null values to zeros
    NoConversions ///< Don't do any conversions
};

// Null values in all inputs we have mean 0 for the model, so using it
// as our default everywhere.
constexpr auto DefaultNullInputPolicy = NullInputPolicy::NullsAsZeros;

/** Policy settings for handling null values in the output */
enum class NullOutputPolicy {
    ZerosAsNulls, ///< Convert zeros to null values
    NoConversions ///< Don't do any conversions
};

// We are not producing any null values in the model, so there is no
// point in doing any conversions, so using it as default.
constexpr auto DefaultNullOutputPolicy = NullOutputPolicy::NoConversions;

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
template <typename Number>
inline pops::Raster<Number>
raster_from_grass(const char *name,
                  NullInputPolicy null_policy = DefaultNullInputPolicy)
{
    unsigned rows = Rast_window_rows();
    unsigned cols = Rast_window_cols();
    pops::Raster<Number> rast(rows, cols);
    Number *data = rast.data();

    int fd = Rast_open_old(name, "");
    for (unsigned row = 0; row < rows; row++) {
        auto row_pointer = data + (row * cols);
        grass_raster_get_row(fd, row_pointer, row);
        if (null_policy == NullInputPolicy::NullsAsZeros) {
            for (unsigned col = 0; col < cols; ++col) {
                set_null_to_zero(row_pointer + col);
            }
        }
    }
    Rast_close(fd);

    return rast;
}

/** Overload of raster_from_grass(const char *) */
template <typename Number>
inline pops::Raster<Number>
raster_from_grass(const std::string &name,
                  NullInputPolicy null_policy = DefaultNullInputPolicy)
{
    return raster_from_grass<Number>(name.c_str(), null_policy);
}

/** Converts type to GRASS GIS raster map type identifier.
 *
 * Use `::value` to obtain the map type identifier.
 * When conversion is not possible, compile error about `value` not
 * being a member of this struct is issued.
 */
template <typename Number>
struct GrassRasterMapType {};

/** Specialization for GRASS GIS raster map type convertor */
template <>
struct GrassRasterMapType<CELL>
    : std::integral_constant<RASTER_MAP_TYPE, CELL_TYPE> {};

/** Specialization for GRASS GIS raster map type convertor */
template <>
struct GrassRasterMapType<FCELL>
    : std::integral_constant<RASTER_MAP_TYPE, FCELL_TYPE> {};

/** Specialization for GRASS GIS raster map type convertor */
template <>
struct GrassRasterMapType<DCELL>
    : std::integral_constant<RASTER_MAP_TYPE, DCELL_TYPE> {};

/** Write a Raster to a GRASS GIS raster map.
 *
 * When used, the template is resolved based on the parameter.
 */
template <typename Number>
void inline raster_to_grass(
    pops::Raster<Number> raster, const char *name,
    NullOutputPolicy null_policy = DefaultNullOutputPolicy,
    const char *title = nullptr, struct TimeStamp *timestamp = nullptr)
{
    Number *data = raster.data();
    unsigned rows = raster.rows();
    unsigned cols = raster.cols();

    int fd = Rast_open_new(name, GrassRasterMapType<Number>::value);
    for (unsigned i = 0; i < rows; i++) {
        auto row_pointer = data + (i * cols);
        if (null_policy == NullOutputPolicy::ZerosAsNulls) {
            for (unsigned j = 0; j < cols; ++j) {
                if (*(row_pointer + j) == 0)
                    grass_raster_set_null(row_pointer + j);
            }
        }
        grass_raster_put_row(fd, row_pointer);
    }
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
template <typename Number>
inline void
raster_to_grass(pops::Raster<Number> raster, const std::string &name,
                NullOutputPolicy null_policy = DefaultNullOutputPolicy)
{
    raster_to_grass<Number>(raster, name.c_str(), null_policy);
}

/** Overload of raster_to_grass() */
template <typename Number>
inline void
raster_to_grass(pops::Raster<Number> raster, const std::string &name,
                const std::string &title,
                NullOutputPolicy null_policy = DefaultNullOutputPolicy)
{
    raster_to_grass<Number>(raster, name.c_str(), null_policy, title.c_str());
}

/** Overload of raster_to_grass()
 *
 * Converts PoPS date to GRASS GIS timestamp.
 */
template <typename Number>
inline void
raster_to_grass(pops::Raster<Number> raster, const std::string &name,
                const std::string &title, const pops::Date &date,
                NullOutputPolicy null_policy = DefaultNullOutputPolicy)
{
    struct TimeStamp timestamp;
    date_to_grass(date, &timestamp);
    raster_to_grass<Number>(raster, name.c_str(), null_policy, title.c_str(),
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
template <typename String>
inline pops::Raster<Float>
raster_from_grass_float(String name,
                        NullInputPolicy null_policy = DefaultNullInputPolicy)
{
    return raster_from_grass<Float>(name, null_policy);
}

/** Wrapper to read GRASS GIS raster into integer type Raster */
template <typename String>
inline pops::Raster<Integer>
raster_from_grass_integer(String name,
                          NullInputPolicy null_policy = DefaultNullInputPolicy)
{
    return raster_from_grass<Integer>(name, null_policy);
}

// TODO: update names
// convenient definitions, names for backwards compatibility
typedef pops::Raster<Integer> Img;
typedef pops::Raster<Float> DImg;

#endif // GRASTER_HPP
