#ifndef POPS_UTILS_HPP
#define POPS_UTILS_HPP

/*
 * PoPS model - general utility functions (unrelated to the model)
 *
 * Copyright (C) 2020 by the authors.
 *
 * Authors: Vaclav Petras <wenzeslaus gmail com>
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

/*!
 * Macro to mark unused variables (including paramters) and silence the warning
 * while documenting that it is intentionally unused.
 *
 * It is recommended to also document why the variable is unused, but left in
 * the code.
 *
 * Usage:
 *
 * ```
 * UNUSED(variable_name);  // Parameter needed for backwards compatibility.
 * ```
 *
 * To be replaced by `[[maybe_unused]]` once we migrate to C++17 or higher.
 */
#define UNUSED(expr) (void)(expr)

#endif // POPS_UTILS_HPP
