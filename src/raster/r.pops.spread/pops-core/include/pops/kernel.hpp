/*
 * PoPS model - main disperal kernel
 *
 * Copyright (C) 2019-2020 by the authors.
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

/*! \file kernel.hpp
 *
 * \brief Main entry point to dispersal kernel functionality
 *
 * This file contains convenient definitions or wrappers to be used
 * when using this library.
 *
 * ## Adding a new kernel
 *
 * To add new kernel, decide if it needs to be a separate class,
 * or if it is just a parameterization of the existing kernel.
 * Many kernels can be handled by the RadialDispersalKernel class.
 *
 * Generally, such class needs to provide contructor taking all required
 * parameters and a function call operator which takes a random number
 * generator object and returns a pair of coordinates as row and column.
 * The signature of the function template should be:
 *
 * ```
 * template<typename Generator>
 * std::tuple<int, int> operator() (Generator& generator)
 * ```
 *
 * Besides implementation in a class, enum for the different types
 * of kernels needs to be extented as well as function which transforms
 * strings into enum values, i.e., you need to add to the
 * `DispersalKernelType` enum and extend the kernel_type_from_string()
 * function in kernel_types.hpp.
 */

#ifndef POPS_KERNEL_HPP
#define POPS_KERNEL_HPP

#include "switch_kernel.hpp"
#include "natural_anthropogenic_kernel.hpp"

namespace pops {

/*! Dispersal kernel supporting all available kernels for natural and
 * anthropogenic distance spread.
 *
 * This is a typedef defining the main disperal kernel class in the PoPS
 * library. When you are using the library, this is default choice.
 *
 * The choices which are allowed by this class are:
 * ```
 *                     kernel type
 *                    /           \
 *                   /             \
 *              natural        anthropogenic
 *             /   |   \          /   |   \
 *        radial uniform ...   radial uniform ...
 *        /  | \_____                 |
 *       /   |       \                |
 * cauchy exponential ...            ...
 * ```
 * The ellipses represent whatever the SwitchDispersalKernel and
 * RadialDispersalKernel classes support.
 *
 * See NaturalAnthropogenicDispersalKernel and SwitchDispersalKernel for further
 * documentation.
 */
template <typename IntegerRaster>
using DispersalKernel =
    NaturalAnthropogenicDispersalKernel<SwitchDispersalKernel<IntegerRaster>,
                                        SwitchDispersalKernel<IntegerRaster>>;

} // namespace pops

#endif // POPS_KERNEL_HPP
