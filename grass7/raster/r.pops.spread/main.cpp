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


// activate support for GRASS GIS in the PoPS library
#define POPS_RASTER_WITH_GRASS_GIS

#include "pops/date.hpp"
#include "pops/raster.hpp"
#include "pops/simulation.hpp"
#include "pops/treatments.hpp"

extern "C" {
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/vector.h>
#include <grass/raster.h>
}

#include <map>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <string>

#include <sys/stat.h>

using std::string;
using std::cout;
using std::cerr;
using std::endl;

using namespace pops;

// TODO: update names
// convenient definitions, names for backwards compatibility
typedef Raster<int> Img;
typedef Raster<double> DImg;
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

Direction direction_enum_from_string(const string& text)
{
    std::map<string, Direction> mapping{
        {"N", N}, {"NE", NE}, {"E", E}, {"SE", SE}, {"S", S},
        {"SW", SW}, {"W", W}, {"NW", NW}, {"NONE", NONE}
    };
    try {
        return mapping.at(text);
    }
    catch (const std::out_of_range&) {
        throw std::invalid_argument("direction_enum_from_string: Invalid"
                                    " value '" + text +"' provided");
    }
}

DispersalKernel radial_type_from_string(const string& text)
{
    if (text == "cauchy")
        return CAUCHY;
    else if (text == "cauchy_mix")
        return CAUCHY_DOUBLE_SCALE;
    else
        throw std::invalid_argument("radial_type_from_string: Invalid"
                                    " value '" + text +"' provided");
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

bool all_infected(Img& S_rast)
{
    bool allInfected = true;
    for (int j = 0; j < S_rast.rows(); j++) {
        for (int k = 0; k < S_rast.cols(); k++) {
            if (S_rast(j, k) > 0)
                allInfected = false;
        }
    }
    return allInfected;
}

struct PoPSOptions
{
    struct Option *host, *total_plants, *infected, *outside_spores;
    struct Option *moisture_coefficient_file, *temperature_coefficient_file;
    struct Option *lethal_temperature, *lethal_temperature_months;
    struct Option *temperature_file;
    struct Option *start_time, *end_time, *seasonality;
    struct Option *step;
    struct Option *treatments, *treatment_year;
    struct Option *reproductive_rate, *wind;
    struct Option *dispersal_kernel, *short_distance_scale, *long_distance_scale, *kappa, *percent_short_dispersal;
    struct Option *infected_to_dead_rate, *first_year_to_die;
    struct Option *dead_series;
    struct Option *seed, *runs, *threads;
    struct Option *output, *output_series;
    struct Option *stddev, *stddev_series;
    struct Option *output_probability;
};

struct PoPSFlags
{
    struct Flag *mortality;
    struct Flag *generate_seed;
    struct Flag *series_as_single_run;
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

    opt.output = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.output->guisection = _("Output");
    opt.output->required = NO;

    opt.output_series = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.output_series->key = "output_series";
    opt.output_series->description = _("Basename for output series");
    opt.output_series->required = NO;
    opt.output_series->guisection = _("Output");

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

    flg.series_as_single_run = G_define_flag();
    flg.series_as_single_run->key = 'l';
    flg.series_as_single_run->label =
        _("The output series as a single run only, not average");
    flg.series_as_single_run->description =
        _("The first run will be used for output instead of average");
    flg.series_as_single_run->guisection = _("Output");

    opt.output_probability = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.output_probability->key = "probability";
    opt.output_probability->description = _("Infection probability (in percent)");
    opt.output_probability->required = NO;
    opt.output_probability->guisection = _("Output");

    opt.outside_spores = G_define_standard_option(G_OPT_V_OUTPUT);
    opt.outside_spores->key = "outside_spores";
    opt.outside_spores->description = _("Output vector map of spores or pest units outside of modeled area");
    opt.outside_spores->required = NO;
    opt.outside_spores->guisection = _("Output");

    opt.treatments = G_define_standard_option(G_OPT_R_INPUT);
    opt.treatments->key = "treatments";
    opt.treatments->multiple = YES;
    opt.treatments->description = _("Raster map(s) of treatments (treated 1, otherwise 0)");
    opt.treatments->required = NO;
    opt.treatments->guisection = _("Treatments");

    opt.treatment_year = G_define_option();
    opt.treatment_year->key = "treatment_year";
    opt.treatment_year->type = TYPE_INTEGER;
    opt.treatment_year->multiple = YES;
    opt.treatment_year->description = _("Years when treatment rasters are applied");
    opt.treatment_year->required = NO;
    opt.treatment_year->guisection = _("Treatments");

    opt.wind = G_define_option();
    opt.wind->type = TYPE_STRING;
    opt.wind->key = "wind";
    opt.wind->label = _("Prevailing wind direction");
    opt.wind->description = _("NONE means that there is no wind");
    opt.wind->options = "N,NE,E,SE,S,SW,W,NW,NONE";
    opt.wind->required = YES;
    opt.wind->answer = const_cast<char*>("NONE");
    opt.wind->guisection = _("Weather");

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

    opt.dispersal_kernel = G_define_option();
    opt.dispersal_kernel->type = TYPE_STRING;
    opt.dispersal_kernel->key = "dispersal_kernel";
    opt.dispersal_kernel->label = _("Type of dispersal kernel");
    opt.dispersal_kernel->answer = const_cast<char*>("cauchy");
    opt.dispersal_kernel->options = "cauchy,cauchy_mix";
    opt.dispersal_kernel->guisection = _("Dispersal");

    opt.short_distance_scale = G_define_option();
    opt.short_distance_scale->type = TYPE_DOUBLE;
    opt.short_distance_scale->key = "short_distance_scale";
    opt.short_distance_scale->label = _("Distance scale parameter for short range dispersal kernel");
    opt.short_distance_scale->answer = const_cast<char*>("20.57");
    opt.short_distance_scale->guisection = _("Dispersal");

    opt.long_distance_scale = G_define_option();
    opt.long_distance_scale->type = TYPE_DOUBLE;
    opt.long_distance_scale->key = "long_distance_scale";
    opt.long_distance_scale->label = _("Distance scale parameter for long range dispersal kernel");
    opt.long_distance_scale->guisection = _("Dispersal");

    opt.kappa = G_define_option();
    opt.kappa->type = TYPE_DOUBLE;
    opt.kappa->key = "kappa";
    opt.kappa->label = _("Strength of the wind direction in the von-mises distribution");
    opt.kappa->answer = const_cast<char*>("2");
    opt.kappa->guisection = _("Dispersal");

    opt.percent_short_dispersal = G_define_option();
    opt.percent_short_dispersal->type = TYPE_DOUBLE;
    opt.percent_short_dispersal->key = "percent_short_dispersal";
    opt.percent_short_dispersal->label = _("Percentage of short range dispersal");
    opt.percent_short_dispersal->description = _("What percentage of dispersal is short range versus long range");
    opt.percent_short_dispersal->options = "0-1";
    opt.percent_short_dispersal->guisection = _("Dispersal");

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

    G_option_required(opt.output, opt.output_series, opt.output_probability,
                      opt.outside_spores, NULL);

    G_option_exclusive(opt.seed, flg.generate_seed, NULL);
    G_option_required(opt.seed, flg.generate_seed, NULL);

    // weather
    G_option_collective(opt.moisture_coefficient_file, opt.temperature_coefficient_file, NULL);

    // mortality
    // flag and rate required always
    // for simplicity of the code outputs allowed only with output
    // for single run (avgs from runs likely not needed)
    G_option_requires(flg.mortality, opt.infected_to_dead_rate, NULL);
    G_option_requires(opt.first_year_to_die, flg.mortality, NULL);
    G_option_requires_all(opt.dead_series, flg.mortality,
                          flg.series_as_single_run, NULL);
    G_option_requires(opt.treatments, opt.treatment_year, NULL);

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

    // Seasonality: Do you want the spread to be limited to certain months?
    if (!opt.seasonality->answer || opt.seasonality->answer[0] == '\0')
        G_fatal_error(_("The option %s cannot be empty"),
                      opt.seasonality->key);
    Season season = seasonality_from_option(opt.seasonality);

    Direction pwdir = direction_enum_from_string(opt.wind->answer);

    // set the spore rate
    double spore_rate = std::stod(opt.reproductive_rate->answer);
    DispersalKernel rtype = radial_type_from_string(opt.dispersal_kernel->answer);
    double scale1 = std::stod(opt.short_distance_scale->answer);
    double scale2 = 0;
    if (rtype == CAUCHY_DOUBLE_SCALE && !opt.long_distance_scale->answer)
        G_fatal_error(_("The option %s is required for %s=%s"),
                      opt.long_distance_scale->key, opt.dispersal_kernel->key,
                      opt.dispersal_kernel->answer);
    else if (opt.long_distance_scale->answer)
        scale2 = std::stod(opt.long_distance_scale->answer);
    double kappa = std::stod(opt.kappa->answer);
    double gamma = 0.0;
    if (rtype == CAUCHY_DOUBLE_SCALE && !opt.percent_short_dispersal->answer)
        G_fatal_error(_("The option %s is required for %s=%s"),
                      opt.percent_short_dispersal->key, opt.dispersal_kernel->key,
                      opt.dispersal_kernel->answer);
    else if (opt.percent_short_dispersal->answer)
        gamma = std::stod(opt.percent_short_dispersal->answer);

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

    string step = opt.step->answer;

    // mortality
    bool mortality = false;
    unsigned first_year_to_die = 1;  // starts at 1 (same as the opt)
    double infected_to_dead_rate = 0.0;
    if (flg.mortality->answer) {
        mortality = true;
        if (opt.first_year_to_die->answer) {
            first_year_to_die = std::stoi(opt.first_year_to_die->answer);
            if (first_year_to_die > num_years) {
                G_fatal_error(
                    _("%s is too large (%d). It must be smaller or "
                      " equal than number of simulation years (%d)."),
                    opt.first_year_to_die->key,
                    first_year_to_die, num_years);
            }
        }
        if (opt.infected_to_dead_rate->answer)
            infected_to_dead_rate = std::stod(opt.infected_to_dead_rate->answer);
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
    Img species_rast = Img::from_grass_raster(opt.host->answer);

    // read the living trees raster image
    Img lvtree_rast = Img::from_grass_raster(opt.total_plants->answer);

    // read the initial infected oaks image
    Img I_species_rast = Img::from_grass_raster(opt.infected->answer);

    // create the initial suspectible oaks image
    Img S_species_rast = species_rast - I_species_rast;

    // SOD-immune trees image
    //Img SOD_rast = umca_rast + oaks_rast;
    //Img IMM_rast = lvtree_rast - SOD_rast;

    std::vector<string> moisture_names;
    std::vector<string> temperature_names;
    double weather = false;

    if (opt.moisture_coefficient_file->answer && opt.temperature_coefficient_file->answer) {
        read_names(moisture_names, opt.moisture_coefficient_file->answer);
        read_names(temperature_names, opt.temperature_coefficient_file->answer);
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
            actual_temperatures.push_back(DImg::from_grass_raster(name.c_str()));
        }
        use_lethal_temperature = true;
    }

    const unsigned max_weeks_in_year = 53;
    std::vector<DImg> weather_coefficients;
    if (weather)
        weather_coefficients.resize(max_weeks_in_year);

    // treatments
    if (get_num_answers(opt.treatments) != get_num_answers(opt.treatment_year)){
        G_fatal_error(_("%s= and %s= must have the same number of values"), opt.treatments->key, opt.treatment_year->key);}
    Treatments<Img, DImg> treatments;
    bool use_treatments = false;
    if (opt.treatments->answers) {
        for (int i_t = 0; opt.treatment_year->answers[i_t]; i_t++) {
            DImg tr = DImg::from_grass_raster(opt.treatments->answers[i_t]);
            treatments.add_treatment(std::stoul(opt.treatment_year->answers[i_t]), tr);
            use_treatments = true;
        }
    }

    // build the Sporulation object
    std::vector<Sporulation> sporulations;
    std::vector<Img> sus_species_rasts(num_runs, S_species_rast);
    std::vector<Img> inf_species_rasts(num_runs, I_species_rast);

    // infected cohort for each year (index is cohort age)
    // age starts with 0 (in year 1), 0 is oldest
    std::vector<std::vector<Img> > inf_species_cohort_rasts(
        num_runs, std::vector<Img>(num_years, Img(S_species_rast, 0)));

    // we are using only the first dead img for visualization, but for
    // parallelization we need all allocated anyway
    std::vector<Img> dead_in_current_year(num_runs, Img(S_species_rast, 0));
    // dead trees accumulated over years
    // TODO: allow only when series as single run
    Img accumulated_dead(Img(S_species_rast, 0));

    sporulations.reserve(num_runs);
    struct Cell_head window;
    G_get_window(&window);
    for (unsigned i = 0; i < num_runs; ++i)
        sporulations.emplace_back(seed_value++, I_species_rast, window.ew_res, window.ns_res);
    std::vector<std::vector<std::tuple<int, int> > > outside_spores(num_runs);

    std::vector<unsigned> unresolved_weeks;
    unresolved_weeks.reserve(max_weeks_in_year);

    Date dd_current(dd_start);

    // main simulation loop (weekly steps)
    for (int current_week = 0; ; current_week++, step == "month" ? dd_current.increased_by_month() : dd_current.increased_by_week()) {
        if (dd_current < dd_end)
            if (season.month_in_season(dd_current.month()))
                unresolved_weeks.push_back(current_week);

        // removal is out of sync with the actual runs but it does
        // not matter as long as removal happends out of season
        if (use_lethal_temperature
                && dd_current.month() == lethal_temperature_month
                && (dd_current.year() <= dd_end.year())) {
            // to avoid problem with Jan 1 of the following year
            // we explicitely check if we are in a valid year range
            unsigned simulation_year = dd_current.year() - dd_start.year();
            if (simulation_year >= actual_temperatures.size())
                G_fatal_error(_("Not enough temperatures"));
            #pragma omp parallel for num_threads(threads)
            for (unsigned run = 0; run < num_runs; run++) {
                sporulations[run].remove(inf_species_rasts[run],
                                         sus_species_rasts[run],
                                         actual_temperatures[simulation_year],
                                         lethal_temperature_value);
            }
        }

        // if all the oaks are infected, then exit
        if (all_infected(S_species_rast)) {
            cerr << "In the " << dd_current << " all suspectible oaks are infected!" << endl;
            break;
        }

        // check whether the spore occurs in the month
        if ((step == "month" ? dd_current.is_last_month_of_year() : dd_current.is_last_week_of_year()) || dd_current >= dd_end) {
            if (!unresolved_weeks.empty()) {

                unsigned week_in_chunk = 0;
                // get weather for all the weeks
                for (auto week : unresolved_weeks) {
                    if (weather) {
                        DImg moisture(DImg::from_grass_raster(moisture_names[week].c_str()));
                        DImg temperature(DImg::from_grass_raster(temperature_names[week].c_str()));
                        weather_coefficients[week_in_chunk] = moisture * temperature;
                    }
                    ++week_in_chunk;
                }

                // stochastic simulation runs
                #pragma omp parallel for num_threads(threads)
                for (unsigned run = 0; run < num_runs; run++) {
                    unsigned week_in_chunk = 0;
                    // actual runs of the simulation per week
                    for (unsigned week : unresolved_weeks) {
                        sporulations[run].generate(inf_species_rasts[run],
                                                   weather,
                                                   weather_coefficients[week_in_chunk],
                                                   spore_rate);

                        auto current_age = dd_current.year() - dd_start.year();
                        sporulations[run].disperse(sus_species_rasts[run],
                                                   inf_species_rasts[run],
                                                   inf_species_cohort_rasts[run][current_age],
                                                   lvtree_rast,
                                                   outside_spores[run],
                                                   weather,
                                                   weather_coefficients[week_in_chunk],
                                                   rtype, scale1,
                                                   gamma, scale2,
                                                   pwdir, kappa);
                        ++week_in_chunk;
                    }
                }
                unresolved_weeks.clear();
            }
            if (mortality && (dd_current.year() <= dd_end.year())) {
                // to avoid problem with Jan 1 of the following year
                // we explicitely check if we are in a valid year range
                unsigned simulation_year = dd_current.year() - dd_start.year();
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
                if (simulation_year >= first_year_to_die - 1) {
                    auto max_index = simulation_year - (first_year_to_die - 1);
                    #pragma omp parallel for num_threads(threads)
                    for (unsigned run = 0; run < num_runs; run++) {
                        dead_in_current_year[run].zero();
                        for (unsigned age = 0; age <= max_index; age++) {
                            Img dead_in_cohort = infected_to_dead_rate * inf_species_cohort_rasts[run][age];
                            inf_species_cohort_rasts[run][age] -= dead_in_cohort;
                            dead_in_current_year[run] += dead_in_cohort;
                            if (use_treatments)
                                treatments.apply_treatment_infected(dd_current.year(), inf_species_cohort_rasts[run][age]);
                        }
                        inf_species_rasts[run] -= dead_in_current_year[run];
                    }
                }
            }
            if (use_treatments && (dd_current.year() <= dd_end.year())) {
                for (unsigned run = 0; run < num_runs; run++) {
                    treatments.apply_treatment_host(dd_current.year(), inf_species_rasts[run], sus_species_rasts[run]);
                }
            }
            if ((opt.output_series->answer && !flg.series_as_single_run->answer)
                     || opt.stddev_series->answer) {
                // aggregate in the series
                I_species_rast.zero();
                for (unsigned i = 0; i < num_runs; i++)
                    I_species_rast += inf_species_rasts[i];
                I_species_rast /= num_runs;
            }
            if (opt.output_series->answer) {
                // write result
                // date is always end of the year, even for seasonal spread
                string name = generate_name(opt.output_series->answer, dd_current);
                if (flg.series_as_single_run->answer)
                    inf_species_rasts[0].to_grass_raster(name.c_str());
                else
                    I_species_rast.to_grass_raster(name.c_str());
            }
            if (opt.stddev_series->answer) {
                Img stddev(I_species_rast, 0);
                for (unsigned i = 0; i < num_runs; i++) {
                    Img tmp = inf_species_rasts[i] - I_species_rast;
                    stddev += tmp * tmp;
                }
                stddev /= num_runs;
                stddev.for_each([](int& a){a = std::sqrt(a);});
                string name = generate_name(opt.stddev_series->answer, dd_current);
                stddev.to_grass_raster(name.c_str());
            }
            if (mortality && opt.dead_series->answer) {
                accumulated_dead += dead_in_current_year[0];
                if (opt.dead_series->answer) {
                    string name = generate_name(opt.dead_series->answer, dd_current);
                    accumulated_dead.to_grass_raster(name.c_str());
                }
            }
        }

        if (dd_current >= dd_end)
            break;
    }

    if (opt.output->answer || opt.stddev->answer) {
        // aggregate
        I_species_rast.zero();
        for (unsigned i = 0; i < num_runs; i++)
            I_species_rast += inf_species_rasts[i];
        I_species_rast /= num_runs;
    }
    if (opt.output->answer) {
        // write final result
        I_species_rast.to_grass_raster(opt.output->answer);
    }
    if (opt.stddev->answer) {
        Img stddev(I_species_rast, 0);
        for (unsigned i = 0; i < num_runs; i++) {
            Img tmp = inf_species_rasts[i] - I_species_rast;
            stddev += tmp * tmp;
        }
        stddev /= num_runs;
        stddev.for_each([](int& a){a = std::sqrt(a);});
        stddev.to_grass_raster(opt.stddev->answer);
    }
    if (opt.output_probability->answer) {
        Img probability(I_species_rast, 0);
        for (unsigned i = 0; i < num_runs; i++) {
            Img tmp = inf_species_rasts[i];
            tmp.for_each([](int& a){a = bool(a);});
            probability += tmp;
        }
        probability *= 100;  // prob from 0 to 100 (using ints)
        probability /= num_runs;
        probability.to_grass_raster(opt.output_probability->answer);
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
        Vect_build(&Map);
        Vect_close(&Map);
        Vect_destroy_line_struct(Points);
        Vect_destroy_cats_struct(Cats);
    }

    return 0;
}
