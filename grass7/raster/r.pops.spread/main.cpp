/*
 * SOD model
 *
 * Copyright (C) 2015-2017 by the authors.
 *
 * Authors: Zexi Chen (zchen22 ncsu edu)
 *          Vaclav Petras (wenzeslaus gmail com)
 *          Anna Petrasova (kratochanna gmail com)
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#include "graster.hpp"

#include "pops/date.hpp"
#include "pops/raster.hpp"
#include "pops/simulation.hpp"
#include "pops/kernel.hpp"
#include "pops/treatments.hpp"
#include "pops/spread_rate.hpp"
#include "pops/statistics.hpp"

extern "C" {
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/vector.h>
#include <grass/raster.h>
}

#include <map>
#include <tuple>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <string>
#include <cmath>

#include <sys/stat.h>

using std::string;
using std::cout;
using std::cerr;
using std::endl;
using std::round;
using std::isnan;

using namespace pops;

// TODO: for backwards compatibility, update eventually
typedef Simulation<Img, DImg> Sporulation;

#define DIM 1

// check if a file exists
inline bool file_exists(const char* name) {
  struct stat buffer;
  return (stat(name, &buffer) == 0);
}

inline void file_exists_or_fatal_error(struct Option* option) {
    if (option->answer && !file_exists(option->answer))
        G_fatal_error(_("Option %s: File %s does not exist"),
                      option->key, option->answer);
}

string generate_name(const string& basename, const Date& date)
{
    // counting on year being 4 digits
    auto year = G_double_to_basename_format(date.year(), 4, 0);
    auto month = G_double_to_basename_format(date.month(), 2, 0);
    auto day = G_double_to_basename_format(date.day(), 2, 0);
    auto sep = G_get_basename_separator();
    string name = basename + sep + year + "_" + month + "_" + day;
    return name;
}

void write_average_area(const std::vector<Img>& infected, const char* raster_name,
                        double ew_res, double ns_res)
{
    struct History hist;
    double avg = 0;
    for (unsigned i = 0; i < infected.size(); i++) {
        avg += area_of_infected(infected[i], ew_res, ns_res);
    }
    avg /= infected.size();
    string avg_string = "Average infected area: " + std::to_string(avg);
    Rast_read_history(raster_name, "", &hist);
    Rast_set_history(&hist, HIST_KEYWRD, avg_string.c_str());
    Rast_write_history(raster_name, &hist);
}

inline TreatmentApplication treatment_app_enum_from_string(const string& text)
{
    std::map<string, TreatmentApplication> mapping{
        {"ratio_to_all", TreatmentApplication::Ratio},
        {"all_infected_in_cell", TreatmentApplication::AllInfectedInCell}
    };
    try {
        return mapping.at(text);
    }
    catch (const std::out_of_range&) {
        throw std::invalid_argument("treatment_application_enum_from_string:"
                                    " Invalid value '" + text +"' provided");
    }
}

inline Date treatment_date_from_string(const string& text)
{
    Date d = Date(text);
    if (!(d.month() >= 1 && d.month() <= 12 && d.day() >=1 && d.day() <= 31))
        G_fatal_error(_("Date <%s> is invalid"), text.c_str());
    return d;
    
}

inline Season seasonality_from_option(const Option* opt)
{
    return {std::atoi(opt->answers[0]), std::atoi(opt->answers[1])};
}


unsigned int get_num_answers(struct Option *opt)
{
    unsigned int i = 0;
    if (opt->answers)
        for (i = 0; opt->answers[i]; i++);
    return i;
}

void read_names(std::vector<string>& names, const char* filename)
{
    std::ifstream file(filename);
    string line;
    while (std::getline(file, line)) {
        names.push_back(line);
    }
}

/*!
 * Warns about depreciated option value
 *
 * It uses the answer member. If the answer is not set,
 * nothing is tested.
 *
 * \param opt Pointer to a valid option structure
 * \param depreciated Value which is depreciated
 * \param current Value which should be used instead
 */
void warn_about_depreciated_option_value(const Option* opt,
                                         const string& depreciated,
                                         const string& current)
{
    if (opt->answer && opt->answer == depreciated) {
        G_warning(_("The value <%s> for option %s is depreciated."
                    " Use value <%s> instead."),
                  opt->answer, opt->key, current.c_str());
    }
}

std::vector<double> weather_file_to_list(const string& filename)
{
    std::ifstream input(filename);
    std::vector<double> output;
    string line;
    while (std::getline(input, line))
    {
        double m, c;
        std::istringstream stream(line);
        stream >> m >> c;
        output.push_back(m * c);
    }
    return output;
}

/** Checks if there are any susceptible hosts left */
bool all_infected(Img& susceptible)
{
    for (unsigned j = 0; j < susceptible.rows(); j++)
        for (unsigned k = 0; k < susceptible.cols(); k++)
            if (susceptible(j, k) > 0)
                return false;
    return true;
}

struct PoPSOptions
{
    struct Option *host, *total_plants, *infected, *outside_spores;
    struct Option *moisture_coefficient_file, *temperature_coefficient_file;
    struct Option *weather_coefficient_file;
    struct Option *lethal_temperature, *lethal_temperature_months;
    struct Option *temperature_file;
    struct Option *start_time, *end_time, *seasonality;
    struct Option *step;
    struct Option *treatments;
    struct Option *treatment_date, *treatment_length;
    struct Option *treatment_app;
    struct Option *reproductive_rate;
    struct Option *natural_kernel, *natural_scale;
    struct Option *natural_direction, *natural_kappa;
    struct Option *anthro_kernel, *anthro_scale;
    struct Option *anthro_direction, *anthro_kappa;
    struct Option *percent_natural_dispersal;
    struct Option *infected_to_dead_rate, *first_year_to_die;
    struct Option *dead_series;
    struct Option *seed, *runs, *threads;
    struct Option *single_series;
    struct Option *average, *average_series;
    struct Option *stddev, *stddev_series;
    struct Option *probability, *probability_series;
    struct Option *spread_rate_output;
};

struct PoPSFlags
{
    struct Flag *mortality;
    struct Flag *generate_seed;
};


int main(int argc, char *argv[])
{
    PoPSOptions opt;
    PoPSFlags flg;

    G_gisinit(argv[0]);

    struct GModule *module = G_define_module();

    G_add_keyword(_("raster"));
    G_add_keyword(_("spread"));
    G_add_keyword(_("model"));
    G_add_keyword(_("disease"));
    G_add_keyword(_("pest"));
    module->description = _("A dynamic species distribution model for pest or "
                            "pathogen spread in forest or agricultural ecosystems");

    opt.host = G_define_standard_option(G_OPT_R_INPUT);
    opt.host->key = "host";
    opt.host->label = _("Input host raster map");
    opt.host->description = _("Number of hosts per cell.");
    opt.host->guisection = _("Input");

    opt.total_plants = G_define_standard_option(G_OPT_R_INPUT);
    opt.total_plants->key = "total_plants";
    opt.total_plants->label = _("Input raster map of total plants");
    opt.total_plants->description = _("Number of all plants per cell");
    opt.total_plants->guisection = _("Input");

    opt.infected = G_define_standard_option(G_OPT_R_INPUT);
    opt.infected->key = "infected";
    opt.infected->label = _("Input raster map of initial infection");
    opt.infected->description = _("Number of infected hosts per cell");
    opt.infected->guisection = _("Input");

    opt.average = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.average->key = "average";
    opt.average->description = _("Average infected across multiple runs");
    opt.average->guisection = _("Output");
    opt.average->required = NO;

    opt.average_series = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.average_series->key = "average_series";
    opt.average_series->description = _("Basename for output series of average infected across multiple runs");
    opt.average_series->required = NO;
    opt.average_series->guisection = _("Output");

    opt.single_series = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.single_series->key = "single_series";
    opt.single_series->description = _("Basename for output series of infected as single stochastic run");
    opt.single_series->required = NO;
    opt.single_series->guisection = _("Output");

    opt.stddev = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.stddev->key = "stddev";
    opt.stddev->description = _("Standard deviations");
    opt.stddev->required = NO;
    opt.stddev->guisection = _("Output");

    opt.stddev_series = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.stddev_series->key = "stddev_series";
    opt.stddev_series->description
            = _("Basename for output series of standard deviations");
    opt.stddev_series->required = NO;
    opt.stddev_series->guisection = _("Output");

    opt.probability = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.probability->key = "probability";
    opt.probability->description = _("Infection probability (in percent)");
    opt.probability->required = NO;
    opt.probability->guisection = _("Output");

    opt.probability_series = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.probability_series->key = "probability_series";
    opt.probability_series->description = _("Basename for output series of probabilities");
    opt.probability_series->required = NO;
    opt.probability_series->guisection = _("Output");

    opt.outside_spores = G_define_standard_option(G_OPT_V_OUTPUT);
    opt.outside_spores->key = "outside_spores";
    opt.outside_spores->description = _("Output vector map of spores or pest units outside of modeled area");
    opt.outside_spores->required = NO;
    opt.outside_spores->guisection = _("Output");

    opt.spread_rate_output = G_define_standard_option(G_OPT_F_OUTPUT);
    opt.spread_rate_output->key = "spread_rate_output";
    opt.spread_rate_output->description =
        _("Output CSV file containg yearly spread rate in N, S, E, W directions");
    opt.spread_rate_output->required = NO;
    opt.spread_rate_output->guisection = _("Output");

    opt.treatments = G_define_standard_option(G_OPT_R_INPUT);
    opt.treatments->key = "treatments";
    opt.treatments->multiple = YES;
    opt.treatments->description = _("Raster map(s) of treatments (treated 1, otherwise 0)");
    opt.treatments->required = NO;
    opt.treatments->guisection = _("Treatments");

    opt.treatment_date = G_define_option();
    opt.treatment_date->key = "treatment_date";
    opt.treatment_date->type = TYPE_STRING;
    opt.treatment_date->multiple = YES;
    opt.treatment_date->description = _("Dates when treatments are applied (e.g. 2020-01-15)");
    opt.treatment_date->required = NO;
    opt.treatment_date->guisection = _("Treatments");

    opt.treatment_length = G_define_option();
    opt.treatment_length->type = TYPE_INTEGER;
    opt.treatment_length->key = "treatment_length";
    opt.treatment_length->multiple = YES;
    opt.treatment_length->label =
        _("Treatment length in days");
    opt.treatment_length->description =
        _("Treatment length 0 results in simple removal of host, length > 0 makes"
          " host resistant for certain number of days");
    opt.treatment_length->required = NO;
    opt.treatment_length->guisection = _("Treatments");

    opt.treatment_app = G_define_option();
    opt.treatment_app->key = "treatment_application";
    opt.treatment_app->type = TYPE_STRING;
    opt.treatment_app->multiple = NO;
    opt.treatment_app->description = _("Type of treatmet application");
    opt.treatment_app->options = "ratio_to_all,all_infected_in_cell";
    opt.treatment_app->required = NO;
    opt.treatment_app->answer = const_cast<char*>("ratio_to_all");
    opt.treatment_app->guisection = _("Treatments");

    opt.moisture_coefficient_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.moisture_coefficient_file->key = "moisture_coefficient_file";
    opt.moisture_coefficient_file->label =
        _("Input file with one moisture coefficient map name per line");
    opt.moisture_coefficient_file->description =
        _("Moisture coefficient");
    opt.moisture_coefficient_file->required = NO;
    opt.moisture_coefficient_file->guisection = _("Weather");

    opt.temperature_coefficient_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.temperature_coefficient_file->key = "temperature_coefficient_file";
    opt.temperature_coefficient_file->label =
        _("Input file with one temperature coefficient map name per line");
    opt.temperature_coefficient_file->description =
        _("Temperature coefficient");
    opt.temperature_coefficient_file->required = NO;
    opt.temperature_coefficient_file->guisection = _("Weather");

    opt.weather_coefficient_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.weather_coefficient_file->key = "weather_coefficient_file";
    opt.weather_coefficient_file->label =
        _("Input file with one weather coefficient map name per line");
    opt.weather_coefficient_file->description =
        _("Weather coefficient");
    opt.weather_coefficient_file->required = NO;
    opt.weather_coefficient_file->guisection = _("Weather");

    opt.lethal_temperature = G_define_option();
    opt.lethal_temperature->type = TYPE_DOUBLE;
    opt.lethal_temperature->key = "lethal_temperature";
    opt.lethal_temperature->label =
        _("Temperature at which the pest or pathogen dies");
    opt.lethal_temperature->description =
        _("The temerature unit must be the same as for the"
          "temerature raster map (typically degrees of Celsius)");
    opt.lethal_temperature->required = NO;
    opt.lethal_temperature->multiple = NO;
    opt.lethal_temperature->guisection = _("Weather");

    opt.lethal_temperature_months = G_define_option();
    opt.lethal_temperature_months->type = TYPE_INTEGER;
    opt.lethal_temperature_months->key = "lethal_month";
    opt.lethal_temperature_months->label =
        _("Month when the pest or patogen dies due to low temperature");
    opt.lethal_temperature_months->description =
        _("The temperature unit must be the same as for the"
          "temperature raster map (typically degrees of Celsius)");
    // TODO: implement this as multiple
    opt.lethal_temperature_months->required = NO;
    opt.lethal_temperature_months->guisection = _("Weather");

    // TODO: rename coefs in interface and improve their descs
    opt.temperature_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.temperature_file->key = "temperature_file";
    opt.temperature_file->label =
        _("Input file with one temperature raster map name per line");
    opt.temperature_file->description =
        _("The temperature should be in actual temperature units (typically degrees of Celsius)");
    opt.temperature_file->required = NO;
    opt.temperature_file->guisection = _("Weather");

    opt.start_time = G_define_option();
    opt.start_time->type = TYPE_INTEGER;
    opt.start_time->key = "start_time";
    opt.start_time->label = _("Start year of the simulation");
    opt.start_time->description = _("The first day of the year will be used");
    opt.start_time->required = YES;
    opt.start_time->guisection = _("Time");

    opt.end_time = G_define_option();
    opt.end_time->type = TYPE_INTEGER;
    opt.end_time->key = "end_time";
    opt.end_time->label = _("End year of the simulation");
    opt.end_time->description = _("The last day of the year will be used");
    opt.end_time->required = YES;
    opt.end_time->guisection = _("Time");

    opt.seasonality = G_define_option();
    opt.seasonality->type = TYPE_STRING;
    opt.seasonality->key = "seasonality";
    opt.seasonality->label = _("Seasonal spread (from,to)");
    opt.seasonality->description =
            _("Spread limited to certain months (season), for example"
              " 5,9 for spread starting at the beginning of May and"
              " ending at the end of September");
    opt.seasonality->key_desc = "from,to";
    //opt.seasonality->options = "1-12";
    opt.seasonality->answer = const_cast<char*>("1,12");
    opt.seasonality->required = YES;
    opt.seasonality->multiple = NO;
    opt.seasonality->guisection = _("Time");

    opt.step = G_define_option();
    opt.step->type = TYPE_STRING;
    opt.step->key = "step";
    opt.step->label = _("Simulation step");
    opt.step->description = _("How often the simulation computes new step");
    opt.step->options = "week,month";
    opt.step->descriptions = _("week;Compute next simulation step each week;month;Compute next simulation step each month");
    opt.step->required = YES;
    opt.step->guisection = _("Time");

    opt.reproductive_rate = G_define_option();
    opt.reproductive_rate->type = TYPE_DOUBLE;
    opt.reproductive_rate->key = "reproductive_rate";
    opt.reproductive_rate->label = _("Number of spores or pest units produced by a single host");
    opt.reproductive_rate->description = _("Number of spores or pest units produced by a single host under optimal weather conditions");
    opt.reproductive_rate->answer = const_cast<char*>("4.4");
    opt.reproductive_rate->guisection = _("Dispersal");

    opt.natural_kernel = G_define_option();
    opt.natural_kernel->type = TYPE_STRING;
    opt.natural_kernel->key = "natural_dispersal_kernel";
    opt.natural_kernel->label = _("Natural dispersal kernel type");
    opt.natural_kernel->answer = const_cast<char*>("cauchy");
    opt.natural_kernel->options = "cauchy,exponential";
    opt.natural_kernel->guisection = _("Dispersal");

    opt.natural_scale = G_define_option();
    opt.natural_scale->type = TYPE_DOUBLE;
    opt.natural_scale->key = "natural_distance";
    opt.natural_scale->label =
            _("Distance parameter for natural dispersal kernel");
    opt.natural_scale->guisection = _("Dispersal");

    opt.natural_direction = G_define_option();
    opt.natural_direction->type = TYPE_STRING;
    opt.natural_direction->key = "natural_direction";
    opt.natural_direction->label =
            _("Direction of natural dispersal kernel");
    opt.natural_direction->description =
            _("Typically prevailing wind direction;"
              " none means that there is no directionality or no wind");
    opt.natural_direction->options = "N,NE,E,SE,S,SW,W,NW,NONE,none";
    opt.natural_direction->required = YES;
    opt.natural_direction->answer = const_cast<char*>("none");
    opt.natural_direction->guisection = _("Dispersal");

    opt.natural_kappa = G_define_option();
    opt.natural_kappa->type = TYPE_DOUBLE;
    opt.natural_kappa->key = "natural_direction_strength";
    opt.natural_kappa->label =
            _("Strength of direction of natural dispersal kernel");
    opt.natural_kappa->description =
            _("The kappa parameter of von Mises distribution"
              " (concentration);"
              " typically the strength of the wind direction");
    opt.natural_kappa->required = YES;
    opt.natural_kappa->guisection = _("Dispersal");

    opt.anthro_kernel = G_define_option();
    opt.anthro_kernel->type = TYPE_STRING;
    opt.anthro_kernel->key = "anthropogenic_dispersal_kernel";
    opt.anthro_kernel->label = _("Anthropogenic dispersal kernel type");
    opt.anthro_kernel->options = "cauchy,exponential";
    opt.anthro_kernel->guisection = _("Dispersal");

    opt.anthro_scale = G_define_option();
    opt.anthro_scale->type = TYPE_DOUBLE;
    opt.anthro_scale->key = "anthropogenic_distance";
    opt.anthro_scale->label =
            _("Distance parameter for anthropogenic dispersal kernel");
    opt.anthro_scale->guisection = _("Dispersal");

    opt.anthro_direction = G_define_option();
    opt.anthro_direction->type = TYPE_STRING;
    opt.anthro_direction->key = "anthropogenic_direction";
    opt.anthro_direction->label =
            _("Direction of anthropogenic dispersal kernel");
    opt.anthro_direction->description =
            _("Value none means that there is no directionality");
    opt.anthro_direction->options = "N,NE,E,SE,S,SW,W,NW,NONE,none";
    opt.anthro_direction->required = YES;
    opt.anthro_direction->answer = const_cast<char*>("none");
    opt.anthro_direction->guisection = _("Dispersal");

    opt.anthro_kappa = G_define_option();
    opt.anthro_kappa->type = TYPE_DOUBLE;
    opt.anthro_kappa->key = "anthropogenic_direction_strength";
    opt.anthro_kappa->label =
            _("Strength of direction of anthropogenic dispersal kernel");
    opt.anthro_kappa->description =
            _("The kappa parameter of von Mises distribution"
              " (concentration);"
              " typically the strength of the wind direction");
    opt.anthro_kappa->guisection = _("Dispersal");

    opt.percent_natural_dispersal = G_define_option();
    opt.percent_natural_dispersal->type = TYPE_DOUBLE;
    opt.percent_natural_dispersal->key = "percent_natural_dispersal";
    opt.percent_natural_dispersal->label =
            _("Percentage of natural dispersal");
    opt.percent_natural_dispersal->description =
            _("How often is the natural dispersal kernel used versus"
              " the anthropogenic dispersal kernel");
    opt.percent_natural_dispersal->options = "0-1";
    opt.percent_natural_dispersal->guisection = _("Dispersal");

    opt.infected_to_dead_rate = G_define_option();
    opt.infected_to_dead_rate->type = TYPE_DOUBLE;
    opt.infected_to_dead_rate->key = "mortality_rate";
    opt.infected_to_dead_rate->label =
        _("Mortality rate of infected hosts");
    opt.infected_to_dead_rate->description =
        _("Percentage of infected hosts that die in a given year"
          " (hosts are removed from the infected pool)");
    opt.infected_to_dead_rate->options = "0-1";
    opt.infected_to_dead_rate->guisection = _("Mortality");

    opt.first_year_to_die = G_define_option();
    opt.first_year_to_die->type = TYPE_INTEGER;
    opt.first_year_to_die->key = "mortality_time_lag";
    opt.first_year_to_die->label =
        _("Time lag from infection until mortality can occur in years");
    opt.first_year_to_die->description =
        _("How many years it takes for an infected host to die"
          " (value 1 for hosts dying at the end of the first year)");
    opt.first_year_to_die->guisection = _("Mortality");

    opt.dead_series = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.dead_series->key = "mortality_series";
    opt.dead_series->label =
        _("Basename for series of number of dead hosts");
    opt.dead_series->description =
        _("Basename for output series of number of dead hosts"
          " (requires mortality to be activated)");
    opt.dead_series->required = NO;
    opt.dead_series->guisection = _("Mortality");

    flg.mortality = G_define_flag();
    flg.mortality->key = 'm';
    flg.mortality->label =
        _("Apply mortality");
    flg.mortality->description =
        _("After certain number of years, start removing dead hosts"
          " from the infected pool with a given rate");
    flg.mortality->guisection = _("Mortality");

    opt.seed = G_define_option();
    opt.seed->key = "random_seed";
    opt.seed->type = TYPE_INTEGER;
    opt.seed->required = NO;
    opt.seed->label = _("Seed for random number generator");
    opt.seed->description =
        _("The same seed can be used to obtain same results"
          " or random seed can be generated by other means.");
    opt.seed->guisection = _("Randomness");

    flg.generate_seed = G_define_flag();
    flg.generate_seed->key = 's';
    flg.generate_seed->label =
        _("Generate random seed (result is non-deterministic)");
    flg.generate_seed->description =
        _("Automatically generates random seed for random number"
          " generator (use when you don't want to provide the seed option)");
    flg.generate_seed->guisection = _("Randomness");

    opt.runs = G_define_option();
    opt.runs->key = "runs";
    opt.runs->type = TYPE_INTEGER;
    opt.runs->required = NO;
    opt.runs->label = _("Number of simulation runs");
    opt.runs->description =
        _("The individual runs will obtain different seeds"
          " and will be averaged for the output");
    opt.runs->guisection = _("Randomness");

    opt.threads = G_define_option();
    opt.threads->key = "nprocs";
    opt.threads->type = TYPE_INTEGER;
    opt.threads->required = NO;
    opt.threads->description =
        _("Number of threads for parallel computing");
    opt.threads->options = "1-";
    opt.threads->guisection = _("Randomness");

    G_option_required(opt.average, opt.average_series, opt.single_series, opt.probability, opt.probability_series,
                      opt.outside_spores, NULL);

    G_option_exclusive(opt.seed, flg.generate_seed, NULL);
    G_option_required(opt.seed, flg.generate_seed, NULL);

    // weather
    G_option_collective(opt.moisture_coefficient_file, opt.temperature_coefficient_file, NULL);
    G_option_exclusive(opt.moisture_coefficient_file, opt.weather_coefficient_file, NULL);
    G_option_exclusive(opt.temperature_coefficient_file, opt.weather_coefficient_file, NULL);

    // mortality
    // flag and rate required always
    // for simplicity of the code outputs allowed only with output
    // for single run (avgs from runs likely not needed)
    G_option_requires(flg.mortality, opt.infected_to_dead_rate, NULL);
    G_option_requires(opt.first_year_to_die, flg.mortality, NULL);
    G_option_requires_all(opt.dead_series, flg.mortality,
                          opt.single_series, NULL);
    // TODO: requires_all does not understand the default?
    // treatment_app needs to be removed from here and check separately
    G_option_requires_all(opt.treatments,
                          opt.treatment_length,
                          opt.treatment_date,
                          opt.treatment_app,
                          NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    unsigned num_runs = 1;
    if (opt.runs->answer)
        num_runs = std::stoul(opt.runs->answer);

    unsigned threads = 1;
    if (opt.threads->answer)
        threads = std::stoul(opt.threads->answer);

    // check for file existence
    file_exists_or_fatal_error(opt.moisture_coefficient_file);
    file_exists_or_fatal_error(opt.temperature_coefficient_file);
    file_exists_or_fatal_error(opt.weather_coefficient_file);

    // get current computational region (for rows, cols and resolution)
    struct Cell_head window;
    G_get_window(&window);

    // Seasonality: Do you want the spread to be limited to certain months?
    if (!opt.seasonality->answer || opt.seasonality->answer[0] == '\0')
        G_fatal_error(_("The option %s cannot be empty"),
                      opt.seasonality->key);
    Season season = seasonality_from_option(opt.seasonality);

    // set the spore rate
    double spore_rate = std::stod(opt.reproductive_rate->answer);

    // TODO: how to support DispersalKernelType::None for natural_kernel?
    // perhaps the long-short should take the type instead of bool,
    // then T is anything else than None
    // TODO: should all kernels support None?
    DispersalKernelType natural_kernel_type =
            kernel_type_from_string(opt.natural_kernel->answer);
    double natural_scale = std::stod(opt.natural_scale->answer);
    Direction natural_direction = direction_from_string(opt.natural_direction->answer);
    double natural_kappa = std::stod(opt.natural_kappa->answer);

    DispersalKernelType anthro_kernel_type =
            kernel_type_from_string(opt.anthro_kernel->answer);
    bool use_long_kernel = false;
    if (anthro_kernel_type != DispersalKernelType::None)
        use_long_kernel = true;

    double anthro_scale = 0;
    if (use_long_kernel && !opt.anthro_scale->answer)
        G_fatal_error(_("The option %s is required for %s=%s"),
                      opt.anthro_scale->key, opt.anthro_kernel->key,
                      opt.anthro_kernel->answer);
    else if (opt.anthro_scale->answer)
        anthro_scale = std::stod(opt.anthro_scale->answer);

    // we allow none and an empty string
    Direction anthro_direction = direction_from_string(opt.anthro_direction->answer);

    double anthro_kappa = 0;
    if (use_long_kernel && !opt.anthro_kappa->answer)
        G_fatal_error(_("The option %s is required for %s=%s"),
                      opt.anthro_kappa->key, opt.anthro_kernel->key,
                      opt.anthro_kernel->answer);
    else if (opt.anthro_kappa->answer)
        anthro_kappa= std::stod(opt.anthro_kappa->answer);

    double gamma = 0.0;
    if (use_long_kernel &&
            !opt.percent_natural_dispersal->answer)
        G_fatal_error(_("The option %s is required for %s=%s"),
                      opt.percent_natural_dispersal->key, opt.natural_kernel->key,
                      opt.natural_kernel->answer);
    else if (opt.percent_natural_dispersal->answer)
        gamma = std::stod(opt.percent_natural_dispersal->answer);

    // warn about limits to backwards compatibility
    // "none" is consistent with other GRASS GIS modules
    warn_about_depreciated_option_value(
                opt.natural_direction, "NONE", "none");
    warn_about_depreciated_option_value(
                opt.anthro_kernel, "NONE", "none");
    warn_about_depreciated_option_value(
                opt.anthro_direction, "NONE", "none");

    RadialDispersalKernel short_radial_kernel(
                window.ew_res, window.ns_res, natural_kernel_type,
                natural_scale, natural_direction, natural_kappa);
    RadialDispersalKernel long_radial_kernel(
                window.ew_res, window.ns_res, anthro_kernel_type,
                anthro_scale, anthro_direction, anthro_kappa);
    UniformDispersalKernel uniform_kernel(window.rows, window.cols);
    SwitchDispersalKernel short_selectable_kernel(
                natural_kernel_type,
                short_radial_kernel, uniform_kernel);
    SwitchDispersalKernel long_selectable_kernel(
                natural_kernel_type,
                long_radial_kernel, uniform_kernel);
    // each run has its own copy, so a kernel can have a state
    std::vector<DispersalKernel> kernels;
    kernels.reserve(num_runs);
    for (unsigned i = 0; i < num_runs; ++i) {
        // each (sub)kernel is copied to the main kernel
        kernels.emplace_back(short_selectable_kernel,
                             long_selectable_kernel,
                             use_long_kernel,
                             gamma);
    }

    // initialize the start Date and end Date object
    // options for times are required ints
    int start_time = std::stoi(opt.start_time->answer);
    int end_time = std::stoi(opt.end_time->answer);
    if (start_time > end_time) {
        G_fatal_error(_("Start date must precede the end date"));
    }

    Date dd_start(start_time, 01, 01);
    Date dd_end(end_time, 12, 31);
    // difference in years (in dates) but including both years
    unsigned num_years = dd_end.year() - dd_start.year() + 1;

    string step_type = opt.step->answer;

    // mortality
    bool use_mortality = false;
    unsigned first_mortality_year = 1;  // starts at 1 (same as the opt)
    double mortality_rate = 0.0;
    if (flg.mortality->answer) {
        use_mortality = true;
        if (opt.first_year_to_die->answer) {
            first_mortality_year = std::stoi(opt.first_year_to_die->answer);
            if (first_mortality_year > num_years) {
                G_fatal_error(
                    _("%s is too large (%d). It must be smaller or "
                      " equal than number of simulation years (%d)."),
                    opt.first_year_to_die->key,
                    first_mortality_year, num_years);
            }
        }
        if (opt.infected_to_dead_rate->answer)
            mortality_rate = std::stod(opt.infected_to_dead_rate->answer);
    }

    unsigned seed_value;
    if (opt.seed->answer) {
        seed_value = std::stoul(opt.seed->answer);
        G_verbose_message(_("Read random seed from %s option: %ud"),
                          opt.seed->key, seed_value);
    } else {
        // flag or option is required, so no check needed
        // getting random seed using GRASS library
        // std::random_device is deterministic in MinGW (#338)
        seed_value = G_srand48_auto();
        G_verbose_message(_("Generated random seed (-%c): %ud"),
                          flg.generate_seed->key, seed_value);
    }

    // read the suspectible UMCA raster image
    Img species_rast = raster_from_grass_integer(opt.host->answer);

    // read the living trees raster image
    Img lvtree_rast = raster_from_grass_integer(opt.total_plants->answer);

    // read the initial infected oaks image
    Img I_species_rast = raster_from_grass_integer(opt.infected->answer);

    // create the initial suspectible oaks image
    Img S_species_rast = species_rast - I_species_rast;

    // SOD-immune trees image
    //Img SOD_rast = umca_rast + oaks_rast;
    //Img IMM_rast = lvtree_rast - SOD_rast;

    std::vector<string> moisture_names;
    std::vector<string> temperature_names;
    std::vector<string> weather_names;
    bool weather = false;
    bool moisture_temperature = false;

    if (opt.moisture_coefficient_file->answer && opt.temperature_coefficient_file->answer) {
        read_names(moisture_names, opt.moisture_coefficient_file->answer);
        read_names(temperature_names, opt.temperature_coefficient_file->answer);
        moisture_temperature = true;
    }
    if (opt.weather_coefficient_file->answer) {
        read_names(weather_names, opt.weather_coefficient_file->answer);
        weather = true;
    }

    double use_lethal_temperature = false;
    double lethal_temperature_value;
    int lethal_temperature_month = 0;  // invalid value for month
    std::vector<string> actual_temperature_names;
    std::vector<DImg> actual_temperatures;
    if (opt.lethal_temperature->answer)
        lethal_temperature_value = std::stod(opt.lethal_temperature->answer);
    if (opt.lethal_temperature_months->answer)
        lethal_temperature_month = std::stod(opt.lethal_temperature_months->answer);
    if (opt.temperature_file->answer) {
        file_exists_or_fatal_error(opt.temperature_file);
        read_names(actual_temperature_names, opt.temperature_file->answer);
        for (string name : actual_temperature_names) {
            actual_temperatures.push_back(raster_from_grass_float(name));
        }
        use_lethal_temperature = true;
    }

    // TODO: limit this by the actual max steps
    // weeks are currently the worst case
    const unsigned max_weeks_in_year = 53;
    std::vector<DImg> weather_coefficients;
    if (weather || moisture_temperature)
        weather_coefficients.resize(max_weeks_in_year);

    // treatments
    if (get_num_answers(opt.treatments) != get_num_answers(opt.treatment_date) &&
            get_num_answers(opt.treatment_date) != get_num_answers(opt.treatment_length)){
        G_fatal_error(_("%s=, %s= and %s= must have the same number of values"),
                      opt.treatments->key, opt.treatment_date->key, opt.treatment_length->key);}
    // the default here should be never used
    TreatmentApplication treatment_app = TreatmentApplication::Ratio;
    if (opt.treatment_app->answer)
        treatment_app = treatment_app_enum_from_string(opt.treatment_app->answer);
    Treatments<Img, DImg> treatments;
    bool use_treatments = false;
    if (opt.treatments->answers) {
        auto increase_by_step = step_type == "month" ? &Date::increased_by_month : &Date::increased_by_week;
        for (int i_t = 0; opt.treatment_date->answers[i_t]; i_t++) {
            DImg tr = raster_from_grass_float(opt.treatments->answers[i_t]);
            treatments.add_treatment(tr, treatment_date_from_string(opt.treatment_date->answers[i_t]),
                                     std::stoul(opt.treatment_length->answers[i_t]), treatment_app, increase_by_step);
            use_treatments = true;
        }
    }

    // build the Sporulation object
    std::vector<Sporulation> sporulations;
    std::vector<Img> sus_species_rasts(num_runs, S_species_rast);
    std::vector<Img> inf_species_rasts(num_runs, I_species_rast);
    std::vector<Img> resistant_rasts(num_runs, Img(S_species_rast, 0));

    // infected cohort for each year (index is cohort age)
    // age starts with 0 (in year 1), 0 is oldest
    std::vector<std::vector<Img> > mortality_tracker_vector(
        num_runs, std::vector<Img>(num_years, Img(S_species_rast, 0)));

    // we are using only the first dead img for visualization, but for
    // parallelization we need all allocated anyway
    std::vector<Img> dead_in_current_year(num_runs, Img(S_species_rast, 0));
    // dead trees accumulated over years
    // TODO: allow only when series as single run
    Img accumulated_dead(Img(S_species_rast, 0));

    sporulations.reserve(num_runs);
    for (unsigned i = 0; i < num_runs; ++i)
        sporulations.emplace_back(seed_value++, I_species_rast);
    std::vector<std::vector<std::tuple<int, int> > > outside_spores(num_runs);

    // spread rate initialization
    std::vector<SpreadRate<Img>> spread_rates(num_runs,
                                              SpreadRate<Img>(I_species_rast, window.ew_res, window.ns_res, num_years));

    std::vector<unsigned> unresolved_steps;
    std::vector<Date> unresolved_dates;
    unresolved_steps.reserve(max_weeks_in_year);
    unresolved_dates.reserve(max_weeks_in_year);

    Date dd_current(dd_start);
    Date dd_current_last_day = step_type == "month" ? dd_current.get_last_day_of_month() : dd_current.get_last_day_of_week();

    // main simulation loop (weekly or monthly steps)
    for (int current_step = 0; dd_current < dd_end; current_step++, step_type == "month" ? dd_current.increased_by_month() : dd_current.increased_by_week()) {
        unresolved_steps.push_back(current_step);
        unresolved_dates.push_back(dd_current);
        dd_current_last_day = step_type == "month" ? dd_current.get_last_day_of_month() : dd_current.get_last_day_of_week();

        // if all the oaks are infected, then exit
        if (all_infected(S_species_rast)) {
            cerr << "In the " << dd_current << " all suspectible oaks are infected!" << endl;
            break;
        }

        // check whether the spore occurs in the month
        // At the end of the year, run simulation for all unresolved
        // steps in one chunk.
        if ((step_type == "month" ? dd_current.is_last_month_of_year() : dd_current.is_last_week_of_year())) {
            unsigned simulation_year = dd_current.year() - dd_start.year();
            if (!unresolved_steps.empty()) {

                // to avoid problem with Jan 1 of the following year
                // we explicitely check if we are in a valid year range
                // TODO: will this ever happen here?
                if (use_lethal_temperature
                        && simulation_year >= actual_temperatures.size())
                    G_fatal_error(_("Not enough temperatures"));

                unsigned step_in_chunk = 0;
                // get weather for all the steps in chunk
                for (auto step : unresolved_steps) {
                    if (moisture_temperature) {
                        DImg moisture(raster_from_grass_float(moisture_names[step]));
                        DImg temperature(raster_from_grass_float(temperature_names[step]));
                        weather_coefficients[step_in_chunk] = moisture * temperature;
                    } else if (weather)
                        weather_coefficients[step_in_chunk] = raster_from_grass_float(weather_names[step]);
                    ++step_in_chunk;
                }

                // stochastic simulation runs
                #pragma omp parallel for num_threads(threads)
                for (unsigned run = 0; run < num_runs; run++) {
                    bool lethality_done_this_year = false;
                    // actual runs of the simulation for each step
                    for (unsigned step = 0; step < unresolved_steps.size(); ++step) {
                        Date date = unresolved_dates[step];
                        // removal of dispersers
                        if (use_lethal_temperature && !lethality_done_this_year
                                && date.month() == lethal_temperature_month) {
                            sporulations[run].remove(inf_species_rasts[run],
                                                     sus_species_rasts[run],
                                                     actual_temperatures[simulation_year],
                                                     lethal_temperature_value);
                            lethality_done_this_year = true;
                        }
                        if (use_treatments) {
                            bool managed = treatments.manage(date, inf_species_rasts[run],
                                                             sus_species_rasts[run], resistant_rasts[run]);
                            if (managed && use_mortality) {
                                // same conditions as the mortality code below
                                // TODO: make the mortality timing available as a separate function in the library
                                // or simply go over all valid cohorts
                                if (simulation_year >= first_mortality_year - 1) {
                                    auto max_index = simulation_year - (first_mortality_year - 1);
                                    for (unsigned age = 0; age <= max_index; age++) {
                                        treatments.manage_mortality(date, 
                                                                    mortality_tracker_vector[run][age]);
                                    }
                                }
                            }
                        }
                        if (!season.month_in_season(date.month()))
                            continue;
                        sporulations[run].generate(inf_species_rasts[run],
                                                   weather || moisture_temperature,
                                                   weather_coefficients[step],
                                                   spore_rate);

                        sporulations[run].disperse(sus_species_rasts[run],
                                                   inf_species_rasts[run],
                                                   mortality_tracker_vector[run][simulation_year],
                                                   lvtree_rast,
                                                   outside_spores[run],
                                                   weather || moisture_temperature,
                                                   weather_coefficients[step],
                                                   kernels[run]);
                    }
                }
                unresolved_steps.clear();
                unresolved_dates.clear();
            }
            if (use_mortality) {
                // only run to the current year of simulation
                // (first year is 0):
                //   max index == sim year
                // reduced by first time when trees start dying
                // (counted from 1: first year == 1)
                // e.g. for sim year 3, year dying 4, max index is 0
                //   max index = sim year - (dying year - 1)
                // index is negative before we reach the year
                // (so we can skip these years)
                // sim year - (dying year - 1) < 0
                // sim year < dying year - 1
                #pragma omp parallel for num_threads(threads)
                for (unsigned run = 0; run < num_runs; run++) {
                    dead_in_current_year[run].zero();
                    sporulations[run].mortality(inf_species_rasts[run], mortality_rate, simulation_year,
                                                first_mortality_year - 1, dead_in_current_year[run],
                                                mortality_tracker_vector[run]);
                }
            }
            // compute spread rate
            #pragma omp parallel for num_threads(threads)
            for (unsigned i = 0; i < num_runs; i++) {
                spread_rates[i].compute_yearly_spread_rate(inf_species_rasts[i], simulation_year);
            }
            if (opt.single_series->answer) {
                string name = generate_name(opt.single_series->answer, dd_current_last_day);
                raster_to_grass(inf_species_rasts[0], name,
                        "Occurrence from a single stochastic run",
                        dd_current_last_day);
            }
            if ((opt.average_series->answer) || opt.stddev_series->answer) {
                // aggregate in the series
                DImg average_raster(I_species_rast.rows(), I_species_rast.cols(), 0);
                average_raster.zero();
                for (unsigned i = 0; i < num_runs; i++)
                    average_raster += inf_species_rasts[i];
                average_raster /= num_runs;
                if (opt.average_series->answer) {
                    // write result
                    // date is always end of the year, even for seasonal spread
                    string name = generate_name(opt.average_series->answer, dd_current_last_day);
                    raster_to_grass(average_raster, name,
                                    "Average occurrence from a all stochastic runs",
                                    dd_current_last_day);
                    write_average_area(inf_species_rasts, name.c_str(),
                                       window.ew_res, window.ns_res);
                }
                if (opt.stddev_series->answer) {
                    DImg stddev(I_species_rast.rows(), I_species_rast.cols(), 0);
                    for (unsigned i = 0; i < num_runs; i++) {
                        auto tmp = inf_species_rasts[i] - average_raster;
                        stddev += tmp * tmp;
                    }
                    stddev /= num_runs;
                    stddev.for_each([](Float& a){a = std::sqrt(a);});
                    string name = generate_name(opt.stddev_series->answer, dd_current_last_day);
                    string title = "Standard deviation of average"
                                   " occurrence from a all stochastic runs";
                    raster_to_grass(stddev, name, title, dd_current_last_day);
                }
            }
            if (opt.probability_series->answer) {
                DImg probability(I_species_rast.rows(), I_species_rast.cols(), 0);
                for (unsigned i = 0; i < num_runs; i++) {
                    Img tmp = inf_species_rasts[i];
                    tmp.for_each([](Integer& a){a = bool(a);});
                    probability += tmp;
                }
                probability *= 100;  // prob from 0 to 100
                probability /= num_runs;
                string name = generate_name(opt.probability_series->answer, dd_current_last_day);
                string title = "Probability of occurrence";
                raster_to_grass(probability, name, title, dd_current_last_day);
            }
            if (use_mortality && opt.dead_series->answer) {
                accumulated_dead += dead_in_current_year[0];
                if (opt.dead_series->answer) {
                    string name = generate_name(opt.dead_series->answer, dd_current_last_day);
                    raster_to_grass(accumulated_dead, name,
                                    "Number of dead hosts to date",
                                    dd_current_last_day);
                }
            }
        }
    }

    if (opt.average->answer || opt.stddev->answer) {
        // aggregate
        DImg average_raster(I_species_rast.rows(), I_species_rast.cols(), 0);
        for (unsigned i = 0; i < num_runs; i++)
            average_raster += inf_species_rasts[i];
        average_raster /= num_runs;
        if (opt.average->answer) {
            // write final result
            raster_to_grass(average_raster, opt.average->answer,
                            "Average occurrence from all stochastic runs",
                            dd_current_last_day);
            write_average_area(inf_species_rasts, opt.average->answer,
                               window.ew_res, window.ns_res);
        }
        if (opt.stddev->answer) {
            DImg stddev(average_raster.rows(), average_raster.cols(), 0);
            for (unsigned i = 0; i < num_runs; i++) {
                auto tmp = inf_species_rasts[i] - average_raster;
                stddev += tmp * tmp;
            }
            stddev /= num_runs;
            stddev.for_each([](Float& a){a = std::sqrt(a);});
            raster_to_grass(stddev, opt.stddev->answer,
                            opt.stddev->description, dd_current_last_day);
        }
    }
    if (opt.probability->answer) {
        DImg probability(I_species_rast.rows(), I_species_rast.cols(), 0);
        for (unsigned i = 0; i < num_runs; i++) {
            Img tmp = inf_species_rasts[i];
            tmp.for_each([](Integer& a){a = bool(a);});
            probability += tmp;
        }
        probability *= 100;  // prob from 0 to 100
        probability /= num_runs;
        raster_to_grass(probability, opt.probability->answer,
                        "Probability of occurrence", dd_current_last_day);
    }
    if (opt.outside_spores->answer) {
        Cell_head region;
        Rast_get_window(&region);
        struct Map_info Map;
        struct line_pnts *Points;
        struct line_cats *Cats;
        if (Vect_open_new(&Map, opt.outside_spores->answer, WITHOUT_Z) < 0)
            G_fatal_error(_("Unable to create vector map <%s>"), opt.outside_spores->answer);

        Points = Vect_new_line_struct();
        Cats = Vect_new_cats_struct();

        for (unsigned i = 0; i < num_runs; i++) {
            for (unsigned j = 0; j < outside_spores[i].size(); j++) {
                int row = std::get<0>(outside_spores[i][j]);
                int col = std::get<1>(outside_spores[i][j]);
                double n = Rast_row_to_northing(row, &region);
                double e = Rast_col_to_easting(col, &region);
                Vect_reset_line(Points);
                Vect_reset_cats(Cats);
                Vect_append_point(Points, e, n, 0);
                Vect_cat_set(Cats, 1, i + 1);
                Vect_write_line(&Map, GV_POINT, Points, Cats);
            }
        }
        Vect_hist_command(&Map);
        Vect_set_map_name(
                    &Map,
                    "Dispersers escaped outside computational region");
        Vect_write_header(&Map);
        Vect_build(&Map);
        Vect_close(&Map);
        struct TimeStamp timestamp;
        date_to_grass(dd_current_last_day, &timestamp);
        G_write_vector_timestamp(opt.outside_spores->answer,
                                 NULL, &timestamp);
        Vect_destroy_line_struct(Points);
        Vect_destroy_cats_struct(Cats);
    }
    if (opt.spread_rate_output->answer) {
        FILE *fp = G_open_option_file(opt.spread_rate_output);
        fprintf(fp, "year,N,S,E,W\n");
        for (unsigned i = 0; i < num_years; i++) {
            double n, s, e, w;
            std::tie(n, s, e, w) = average_spread_rate(spread_rates, i);
            fprintf(fp, "%d,%.0f,%.0f,%.0f,%.0f\n", start_time + i,
                    isnan(n) ? n : round(n), isnan(s) ? s : round(s),
                    isnan(e) ? e : round(e), isnan(w) ? w : round(w));
        }
        G_close_option_file(fp);
    }

    return 0;
}
