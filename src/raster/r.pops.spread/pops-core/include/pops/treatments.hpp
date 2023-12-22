/*
 * PoPS model - treatments
 *
 * Copyright (C) 2015-2020 by the authors.
 *
 * Authors: Anna Petrasova <akratoc gmail com>
 *          Vaclav Petras <wenzeslaus gmail com>
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef POPS_TREATMENTS_HPP
#define POPS_TREATMENTS_HPP

#include "raster.hpp"
#include "date.hpp"
#include "scheduling.hpp"

#include <map>
#include <vector>
#include <string>
#include <functional>
#include <stdexcept>

namespace pops {

/**
 * @brief The enum to decide how treatment is applied
 */
enum class TreatmentApplication {
    Ratio,            ///< A ratio is applied to all treated rasters
    AllInfectedInCell ///< All infected individuals are removed, rest by ratio
};

/**
 * @brief Get treatment application enum from string

 * Throws an std::invalid_argument exception if the value
 * is not supported.
 */
inline TreatmentApplication
treatment_app_enum_from_string(const std::string &text)
{
    std::map<std::string, TreatmentApplication> mapping{
        {"ratio_to_all", TreatmentApplication::Ratio},
        {"ratio", TreatmentApplication::Ratio},
        {"all_infected_in_cell", TreatmentApplication::AllInfectedInCell},
        {"all infected", TreatmentApplication::AllInfectedInCell}};
    try {
        return mapping.at(text);
    }
    catch (const std::out_of_range &) {
        throw std::invalid_argument("treatment_application_enum_from_string:"
                                    " Invalid value '" +
                                    text + "' provided");
    }
}

/*!
 * Abstract interface for treatment classes
 *
 * The class is meant for better internal code
 * layout and, at this point, it is not meant
 * as a universal matured interface for treatments.
 * Functions apply_treatment and end_treatment
 * are examples where we account for the current
 * concrete classes and will introduce more
 * general set of parameters only when
 * needed for additional classes.
 */
template <typename IntegerRaster, typename FloatRaster>
class AbstractTreatment {
public:
    virtual unsigned get_start() = 0;
    virtual unsigned get_end() = 0;
    virtual bool should_start(unsigned step) = 0;
    virtual bool should_end(unsigned step) = 0;
    virtual void apply_treatment(IntegerRaster &infected,
                                 std::vector<IntegerRaster> &exposed,
                                 IntegerRaster &susceptible,
                                 IntegerRaster &resistant) = 0;
    virtual void end_treatment(IntegerRaster &susceptible,
                               IntegerRaster &resistant) = 0;
    virtual void apply_treatment_mortality(IntegerRaster &infected) = 0;
    virtual ~AbstractTreatment() {}
};

/*!
 * Base treatment class.
 * Holds functions common between all treatment classes.
 */
template <typename IntegerRaster, typename FloatRaster>
class BaseTreatment : public AbstractTreatment<IntegerRaster, FloatRaster> {
protected:
    unsigned start_step_;
    unsigned end_step_;
    FloatRaster map_;
    TreatmentApplication application_;

public:
    BaseTreatment(const FloatRaster &map, unsigned start,
                  TreatmentApplication treatment_application)
        : start_step_(start), end_step_(start), map_(map),
          application_(treatment_application)
    {
    }
    unsigned get_start() override { return start_step_; }
    unsigned get_end() override { return end_step_; }
    void apply_treatment_mortality(IntegerRaster &infected) override
    {
        for (int i = 0; i < infected.rows(); i++)
            for (int j = 0; j < infected.cols(); j++) {
                if (application_ == TreatmentApplication::Ratio) {
                    infected(i, j) =
                        infected(i, j) - (infected(i, j) * map_(i, j));
                }
                else if (application_ ==
                         TreatmentApplication::AllInfectedInCell) {
                    infected(i, j) = map_(i, j) ? 0 : infected(i, j);
                }
            }
    }
};

/*!
 * Simple treatment class.
 * Removes percentage (given by treatment efficiency)
 * of infected and susceptible host (e.g. cut down trees).
 */
template <typename IntegerRaster, typename FloatRaster>
class SimpleTreatment : public BaseTreatment<IntegerRaster, FloatRaster> {
public:
    SimpleTreatment(const FloatRaster &map, unsigned start,
                    TreatmentApplication treatment_application)
        : BaseTreatment<IntegerRaster, FloatRaster>(map, start,
                                                    treatment_application)
    {
    }
    bool should_start(unsigned step) override
    {
        if (this->start_step_ == step)
            return true;
        return false;
    }
    bool should_end(unsigned) override { return false; }
    void apply_treatment(IntegerRaster &infected,
                         std::vector<IntegerRaster> &exposed,
                         IntegerRaster &susceptible, IntegerRaster &) override
    {
        for (int i = 0; i < infected.rows(); i++)
            for (int j = 0; j < infected.cols(); j++) {
                if (this->application_ == TreatmentApplication::Ratio) {
                    infected(i, j) =
                        infected(i, j) - (infected(i, j) * this->map_(i, j));
                }
                else if (this->application_ ==
                         TreatmentApplication::AllInfectedInCell) {
                    infected(i, j) = this->map_(i, j) ? 0 : infected(i, j);
                }
                for (auto &raster : exposed) {
                    if (this->application_ == TreatmentApplication::Ratio) {
                        raster(i, j) =
                            raster(i, j) - (raster(i, j) * this->map_(i, j));
                    }
                    else if (this->application_ ==
                             TreatmentApplication::AllInfectedInCell) {
                        raster(i, j) = this->map_(i, j) ? 0 : raster(i, j);
                    }
                }
                susceptible(i, j) =
                    susceptible(i, j) - (susceptible(i, j) * this->map_(i, j));
            }
    }
    void end_treatment(IntegerRaster &, IntegerRaster &) override { return; }
};

/*!
 * Pesticide treatment class.
 * Removes percentage (given by treatment efficiency)
 * of infected and susceptible to resistant pool
 * and after certain number of days back to susceptible.
 */
template <typename IntegerRaster, typename FloatRaster>
class PesticideTreatment : public BaseTreatment<IntegerRaster, FloatRaster> {
public:
    PesticideTreatment(const FloatRaster &map, unsigned start, unsigned end,
                       TreatmentApplication treatment_application)
        : BaseTreatment<IntegerRaster, FloatRaster>(map, start,
                                                    treatment_application)
    {
        this->end_step_ = end;
    }
    bool should_start(unsigned step) override
    {
        if (this->start_step_ == step)
            return true;
        return false;
    }
    bool should_end(unsigned step) override
    {
        if (this->end_step_ == step)
            return true;
        return false;
    }

    void apply_treatment(IntegerRaster &infected,
                         std::vector<IntegerRaster> &exposed_vector,
                         IntegerRaster &susceptible,
                         IntegerRaster &resistant) override
    {
        for (int i = 0; i < infected.rows(); i++)
            for (int j = 0; j < infected.cols(); j++) {
                int infected_resistant = 0;
                int exposed_resistant_sum = 0;
                int susceptible_resistant =
                    susceptible(i, j) * this->map_(i, j);
                int current_resistant = resistant(i, j);
                if (this->application_ == TreatmentApplication::Ratio) {
                    infected_resistant = infected(i, j) * this->map_(i, j);
                }
                else if (this->application_ ==
                         TreatmentApplication::AllInfectedInCell) {
                    infected_resistant = this->map_(i, j) ? infected(i, j) : 0;
                }
                infected(i, j) -= infected_resistant;
                for (auto &exposed : exposed_vector) {
                    int exposed_resistant = 0;
                    if (this->application_ == TreatmentApplication::Ratio) {
                        exposed_resistant = exposed(i, j) * this->map_(i, j);
                    }
                    else if (this->application_ ==
                             TreatmentApplication::AllInfectedInCell) {
                        exposed_resistant =
                            this->map_(i, j) ? exposed(i, j) : 0;
                    }
                    exposed(i, j) -= exposed_resistant;
                    exposed_resistant_sum += exposed_resistant;
                }
                resistant(i, j) = infected_resistant + exposed_resistant_sum +
                                  susceptible_resistant + current_resistant;
                susceptible(i, j) -= susceptible_resistant;
            }
    }
    void end_treatment(IntegerRaster &susceptible,
                       IntegerRaster &resistant) override
    {
        for (int i = 0; i < resistant.rows(); i++)
            for (int j = 0; j < resistant.cols(); j++) {
                if (this->map_(i, j) > 0) {
                    susceptible(i, j) += resistant(i, j);
                    resistant(i, j) = 0;
                }
            }
    }
};

/*!
 * Treatments class manages all treatments.
 * Treatments can be simple (host removal)
 * and using pesticide (temporarily removed).
 * Each treatment can have unique date, type (simple, pesticide),
 * length (in case of pesticide), and treatment application.
 *
 * Pesticide treatments should not overlap spatially AND temporally
 * because of single resistance raster. In that case all resistant
 * populations that overlap both spatially and temporally
 * are returned to the susceptible pool when the first treatment ends.
 */
template <typename IntegerRaster, typename FloatRaster>
class Treatments {
private:
    std::vector<AbstractTreatment<IntegerRaster, FloatRaster> *> treatments;
    Scheduler scheduler_;

public:
    Treatments(const Scheduler &scheduler) : scheduler_(scheduler) {}
    ~Treatments()
    {
        for (auto item : treatments) {
            delete item;
        }
    }
    /*!
     * \brief Add treatment, based on parameters it is distinguished
     * which treatment it will be.
     *
     * This works internally like a factory function
     * separating the user from all treatment classes.
     *
     * \param map treatment raster
     * \param start_date date when treatment is applied
     * \param num_days for simple treatments should be 0, otherwise number of
     * days host is resistant \param treatment_application if efficiency < 100%
     * how should it be applied to infected/susceptible \param increase_by_step
     * function to increase simulation step
     */
    void add_treatment(const FloatRaster &map, const Date &start_date,
                       int num_days, TreatmentApplication treatment_application)
    {
        unsigned start = scheduler_.schedule_action_date(start_date);
        if (num_days == 0)
            treatments.push_back(
                new SimpleTreatment<IntegerRaster, FloatRaster>(
                    map, start, treatment_application));
        else {
            Date end_date(start_date);
            end_date.add_days(num_days);
            unsigned end = scheduler_.schedule_action_date(end_date);
            treatments.push_back(
                new PesticideTreatment<IntegerRaster, FloatRaster>(
                    map, start, end, treatment_application));
        }
    }
    /*!
     * \brief Do management if needed.
     * Should be called before every simulation step.
     * Decides internally whether any treatment needs to be
     * activated/deactivated.
     *
     * \param current simulation step
     * \param infected raster of infected host
     * \param susceptible raster of susceptible host
     * \param resistant raster of resistant host
     * \return true if any management action was necessary
     */
    bool manage(unsigned current, IntegerRaster &infected,
                std::vector<IntegerRaster> &exposed, IntegerRaster &susceptible,
                IntegerRaster &resistant)
    {
        bool changed = false;
        for (unsigned i = 0; i < treatments.size(); i++) {
            if (treatments[i]->should_start(current)) {
                treatments[i]->apply_treatment(infected, exposed, susceptible,
                                               resistant);
                changed = true;
            }
            else if (treatments[i]->should_end(current)) {
                treatments[i]->end_treatment(susceptible, resistant);
                changed = true;
            }
        }
        return changed;
    }
    /*!
     * \brief Separately manage mortality infected cohorts
     * \param current simulation step
     * \param infected raster of infected host
     * \return true if any management action was necessary
     */
    bool manage_mortality(unsigned current, IntegerRaster &infected)
    {
        bool applied = false;
        for (unsigned i = 0; i < treatments.size(); i++)
            if (treatments[i]->should_start(current)) {
                treatments[i]->apply_treatment_mortality(infected);
                applied = true;
            }
        return applied;
    }
    /*!
     * \brief Used to remove treatments after certain step.
     * Needed for computational steering.
     * \param step simulation step
     */
    void clear_after_step(unsigned step)
    {
        for (auto &treatment : treatments) {
            if (treatment->get_start() > step) {
                delete treatment;
                treatment = nullptr;
            }
        }
        treatments.erase(
            std::remove(treatments.begin(), treatments.end(), nullptr),
            treatments.end());
    }
};

} // namespace pops
#endif // POPS_TREATMENTS_HPP
