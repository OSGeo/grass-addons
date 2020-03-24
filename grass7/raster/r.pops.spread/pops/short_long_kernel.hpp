/*
 * PoPS model - disperal kernel combining short and long dispersals
 *
 * Copyright (C) 2015-2020 by the authors.
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

#ifndef POPS_SHORT_LONG_KERNEL_HPP
#define POPS_SHORT_LONG_KERNEL_HPP

#include "kernel_types.hpp"

#include <tuple>
#include <random>
#include <type_traits>

namespace pops {

/*! Dispersal kernel template for short and long distance dispersal
 *
 * This class template can be used for switching between two kernels
 * specified as template parameters where one kernel is assumed to
 * be used short distance distance dispersal and the other for long
 * distance one. The two disperal kernels can be the same or different.
 *
 * There are no assumptions for short or long kernels. We are using
 * these names for clarity since this is how we expect the template
 * to be used.
 *
 * Bernoulli distribution is used to decide between the short and
 * long distance kernel. The long distance dispersal can be also
 * competely disabled.
 */
template<typename ShortKernelType,
         typename LongKernelType>
class ShortLongDispersalKernel
{
protected:
    bool use_long_kernel_;
    ShortKernelType short_kernel_;
    LongKernelType long_kernel_;
    std::bernoulli_distribution bernoulli_distribution;

public:
    ShortLongDispersalKernel(const ShortKernelType& short_kernel,
                             const LongKernelType& long_kernel,
                             bool use_long_kernel,
                             double percent_short_dispersal
                             )
        :
          use_long_kernel_(use_long_kernel),
          // Here we initialize all distributions,
          // although we won't use all of them.
          short_kernel_(short_kernel),
          long_kernel_(long_kernel),
          // use bernoulli distribution to act as the sampling with prob(gamma,1-gamma)
          bernoulli_distribution(percent_short_dispersal)
    {}

    /*! \copydoc RadialDispersalKernel::operator()()
     */
    template<typename Generator>
    std::tuple<int, int> operator() (Generator& generator, int row, int col)
    {
        // switch in between the supported kernels
        if (!use_long_kernel_ || bernoulli_distribution(generator)) {
            return short_kernel_(generator, row, col);
        }
        else {
            return long_kernel_(generator, row, col);
        }
    }

    /*! \copydoc RadialDispersalKernel::supports_kernel()
     *
     * Returns true if at least one of the kernels (short or long)
     * supports the given kernel type.
     *
     * \note Note that if short and long kernels are different, this is
     * not generally usable because one kernel can support that and the
     * other not. However, there is not much room for accidental misuse
     * of this because this class does not use the type directly
     * (it is handled by the underlying kernels).
     */
    static bool supports_kernel(const DispersalKernelType type)
    {
        if (std::is_same<ShortKernelType, LongKernelType>::value) {
            return ShortKernelType::supports_kernel(type);
        }
        else {
            return ShortKernelType::supports_kernel(type) ||
                    LongKernelType::supports_kernel(type);
        }
    }
};

} // namespace pops

#endif // POPS_SHORT_LONG_KERNEL_HPP
