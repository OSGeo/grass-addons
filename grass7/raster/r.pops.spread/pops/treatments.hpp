/*
 * PoPS model - treatments
 *
 * Copyright (C) 2015-2019 by the authors.
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

#include <map>
#include <vector>
#include <functional>

namespace pops {


/**
 * @brief The enum to decide how treatment is applied
 */
enum class TreatmentApplication {
    Ratio,  ///< A ratio is applied to all treated rasters
    AllInfectedInCell  ///< All infected individuals are removed, rest by ratio
};

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
template<typename IntegerRaster, typename FloatRaster>
class AbstractTreatment
{
public:
    virtual Date get_start() = 0;
    virtual Date get_end() = 0;
    virtual bool should_start(const Date& date) = 0;
    virtual bool should_end(const Date& date) = 0;
    virtual void apply_treatment(IntegerRaster& infected, IntegerRaster& susceptible, IntegerRaster& resistant) = 0;
    virtual void end_treatment(IntegerRaster& susceptible, IntegerRaster& resistant) = 0;
    virtual void apply_treatment_mortality(IntegerRaster& infected) = 0;
    virtual ~AbstractTreatment() {}
};

/*!
 * Base treatment class.
 * Holds functions common between all treatment classes.
 */
template<typename IntegerRaster, typename FloatRaster>
class BaseTreatment : public AbstractTreatment<IntegerRaster, FloatRaster>
{
protected:
    Date start_;
    Date end_;
    FloatRaster map_;
    TreatmentApplication application_;
    std::function<void (Date&)> increase_by_step_;
public:
    BaseTreatment(const FloatRaster& map, const Date& start,
                  TreatmentApplication treatment_application,
                  std::function<void (Date&)> increase_by_step):
        start_(start), end_(start), map_(map),
        application_(treatment_application), increase_by_step_(increase_by_step)
    {}
    Date get_start() {return start_;}
    Date get_end() {return end_;}
    void apply_treatment_mortality(IntegerRaster& infected) override
    {
        for(unsigned i = 0; i < infected.rows(); i++)
            for(unsigned j = 0; j < infected.cols(); j++) {
                if (application_ == TreatmentApplication::Ratio) {
                    infected(i, j) = infected(i, j) - (infected(i, j) * map_(i, j));
                }
                else if (application_ == TreatmentApplication::AllInfectedInCell) {
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
template<typename IntegerRaster, typename FloatRaster>
class SimpleTreatment : public BaseTreatment<IntegerRaster, FloatRaster>
{
public:
    SimpleTreatment(const FloatRaster& map, const Date& start,
                    TreatmentApplication treatment_application,
                    std::function<void (Date&)> increase_by_step):
        BaseTreatment<IntegerRaster, FloatRaster>(map, start, treatment_application, increase_by_step)
    {}
    bool should_start(const Date& date) override
    {
        Date st = Date(this->start_);
        this->increase_by_step_(st);
        if (date >= this->start_ && date < st)
            return true;
        return false;
    }
    bool should_end(const Date&) override
    {
        return false;
    }
    void apply_treatment(IntegerRaster& infected, IntegerRaster& susceptible, IntegerRaster& ) override
    {
        for(unsigned i = 0; i < infected.rows(); i++)
            for(unsigned j = 0; j < infected.cols(); j++) {
                if (this->application_ == TreatmentApplication::Ratio) {
                    infected(i, j) = infected(i, j) - (infected(i, j) * this->map_(i, j));
                }
                else if (this->application_ == TreatmentApplication::AllInfectedInCell) {
                    infected(i, j) = this->map_(i, j) ? 0 : infected(i, j);
                }
                susceptible(i, j) = susceptible(i, j) - (susceptible(i, j) * this->map_(i, j));
            }
    }
    void end_treatment(IntegerRaster&, IntegerRaster&) override
    {
        return;
    }
};

/*!
 * Pesticide treatment class.
 * Removes percentage (given by treatment efficiency)
 * of infected and susceptible to resistant pool
 * and after certain number of days back to susceptible.
 */
template<typename IntegerRaster, typename FloatRaster>
class PesticideTreatment : public BaseTreatment<IntegerRaster, FloatRaster>
{
public:
    PesticideTreatment(const FloatRaster& map, const Date& start, int num_days,
                       TreatmentApplication treatment_application,
                       std::function<void (Date&)> increase_by_step):
        BaseTreatment<IntegerRaster, FloatRaster>(map, start, treatment_application, increase_by_step)
    {
        this->end_.add_days(num_days);
    }
    bool should_start(const Date& date) override
    {
        Date st = Date(this->start_);
        this->increase_by_step_(st);
        if (date >= this->start_ && date < st)
            return true;
        return false;
    }
    bool should_end(const Date& date) override
    {
        Date end = Date(this->end_);
        this->increase_by_step_(end);
        if (date >= this->end_ && date < end)
            return true;
        return false;
    }

    void apply_treatment(IntegerRaster& infected, IntegerRaster& susceptible, IntegerRaster& resistant) override
    {
        for(unsigned i = 0; i < infected.rows(); i++)
            for(unsigned j = 0; j < infected.cols(); j++) {
                int infected_resistant;
                int susceptible_resistant = susceptible(i, j) * this->map_(i, j);
                int current_resistant = resistant(i, j); 
                if (this->application_ == TreatmentApplication::Ratio) {
                    infected_resistant = infected(i, j) * this->map_(i, j);
                }
                else if (this->application_ == TreatmentApplication::AllInfectedInCell) {
                    infected_resistant = this->map_(i, j) ? infected(i, j): 0;
                }
                infected(i, j) -= infected_resistant;
                resistant(i, j) = infected_resistant + susceptible_resistant + current_resistant;
                susceptible(i, j) -= susceptible_resistant;
            }
    }
    void end_treatment(IntegerRaster& susceptible, IntegerRaster& resistant) override
    {
        for(unsigned i = 0; i < resistant.rows(); i++)
            for(unsigned j = 0; j < resistant.cols(); j++) {
                if (this->map_(i, j) > 0){
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
template<typename IntegerRaster, typename FloatRaster>
class Treatments
{
private:
    std::vector<AbstractTreatment<IntegerRaster, FloatRaster>*> treatments;
public:
    ~Treatments()
    {
        for (auto item : treatments)
        {
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
     * \param num_days for simple treatments should be 0, otherwise number of days host is resistant
     * \param treatment_application if efficiency < 100% how should it be applied to infected/susceptible
     * \param increase_by_step function to increase simulation step
     */
    void add_treatment(const FloatRaster& map, const Date& start_date, int num_days, TreatmentApplication treatment_application,
                       std::function<void (Date&)> increase_by_step)
    {
        if (num_days == 0)
            treatments.push_back(new SimpleTreatment<IntegerRaster, FloatRaster>(map, start_date, treatment_application, increase_by_step));
        else
            treatments.push_back(new PesticideTreatment<IntegerRaster, FloatRaster>(map, start_date, num_days, treatment_application, increase_by_step));
    }
    /*!
     * \brief Do management if needed.
     * Should be called before every simulation step.
     * Decides internally whether any treatment needs to be
     * activated/deactivated.
     *
     * \param current simulation date
     * \param infected raster of infected host
     * \param susceptible raster of susceptible host
     * \param resistant raster of resistant host
     * \return true if any management action was necessary
     */
    bool manage(const Date& current, IntegerRaster& infected,
                IntegerRaster& susceptible, IntegerRaster& resistant)
    {
        bool changed = false;
        for (unsigned i = 0; i < treatments.size(); i++) {
            if (treatments[i]->should_start(current)) {
                treatments[i]->apply_treatment(infected, susceptible, resistant);
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
     * \param current simulation date
     * \param infected raster of infected host
     * \return true if any management action was necessary
     */
    bool manage_mortality(const Date& current, IntegerRaster& infected)
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
     * \brief Used to remove treatments after certain date.
     * Needed for computational steering.
     * \param date simulation date
     */
    void clear_after_date(const Date& date)
    {
        for(auto& treatment : treatments)
        {
            if (treatment->get_start() > date)
            {
                delete treatment;
                treatment = nullptr;
            }
        }
        treatments.erase(std::remove(treatments.begin(), treatments.end(), nullptr),
                         treatments.end());
    }
};

}
#endif // POPS_TREATMENTS_HPP

