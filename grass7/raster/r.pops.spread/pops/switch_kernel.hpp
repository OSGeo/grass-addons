/*
 * PoPS model - disperal kernels
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

#ifndef POPS_SWITCH_KERNEL_HPP
#define POPS_SWITCH_KERNEL_HPP

#include "radial_kernel.hpp"
#include "uniform_kernel.hpp"
#include "kernel_types.hpp"

namespace pops {

/*! Dispersal kernel providing all the radial kernels.
 *
 * We understand a radial kernel to be a kernel which has parameters
 * which translate into a distance and direction.
 *
 * To add new kernel, add new member, constructor parameter,
 * its call in the function call operator, and extend the
 * supports_kernel() function.
 */
class SwitchDispersalKernel
{
protected:
    DispersalKernelType dispersal_kernel_type_;
    RadialDispersalKernel radial_kernel_;
    UniformDispersalKernel uniform_kernel_;

public:
    SwitchDispersalKernel(const DispersalKernelType& dispersal_kernel_type,
                          const RadialDispersalKernel& radial_kernel,
                          const UniformDispersalKernel& uniform_kernel
                          )
        :
          dispersal_kernel_type_(dispersal_kernel_type),
          // Here we initialize all kernels,
          // although we won't use all of them.
          radial_kernel_(radial_kernel),
          uniform_kernel_(uniform_kernel)
    {}

    /*! \copydoc RadialDispersalKernel::operator()()
     */
    template<typename Generator>
    std::tuple<int, int> operator() (Generator& generator, int row, int col)
    {
        // switch in between the supported kernels
        if (dispersal_kernel_type_ == DispersalKernelType::Uniform) {
            return uniform_kernel_(generator, row, col);
        }
        else {
            return radial_kernel_(generator, row, col);
        }
    }

    /*! \copydoc RadialDispersalKernel::supports_kernel()
     */
    static bool supports_kernel(const DispersalKernelType type)
    {
        if (type == DispersalKernelType::Uniform)
            return true;
        else
            return RadialDispersalKernel::supports_kernel(type);
    }
};

} // namespace pops

#endif // POPS_SWITCH_KERNEL_HPP
