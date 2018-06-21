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


// define to support NetCDF format directly
// (requires linking to netcdf_c++)
// #define SOD_NETCDF_SUPPORT

#include "date.h"
#include "raster.h"
#include "Spore.h"

extern "C" {
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/vector.h>
#include <grass/raster.h>
}

#ifdef SOD_NETCDF_SUPPORT
#include <netcdfcpp.h>
#endif

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

// Initialize infected trees for each species
// needed unless empirical info is available
static Img initialize(Img& img1,Img& img2) {
    if (img1.getWidth() != img2.getWidth() ||
            img2.getHeight() != img2.getHeight()) {
        cerr << "The height or width of one image do not match with that of the other one!" << endl;
        return Img();
    }
    else {
        auto re_width = img1.getWidth();
        auto re_height = img1.getHeight();
        auto out = Img(re_width, re_height, img1.getWEResolution(), img1.getNSResolution());

        for (int i = 0; i < re_height; i++) {
            for (int j = 0; j < re_width; j++) {
                if (img2(i, j) > 0) {
                    if (img1(i, j) > img2(i, j))
                        out(i, j) =
                            img1(i, j) <
                            (img2(i, j) *
                             2) ? img1(i, j) : (img2(i, j) * 2);
                    else
                        out(i, j) = img1(i, j);
                }
                else {
                    out(i, j) = 0;
                }
            }
        }
        return out;
    }
}

string generate_name(const string& basename, const Date& date)
{
    // counting on year being 4 digits
    auto year = G_double_to_basename_format(date.getYear(), 4, 0);
    auto month = G_double_to_basename_format(date.getMonth(), 2, 0);
    auto day = G_double_to_basename_format(date.getDay(), 2, 0);
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

Rtype radial_type_from_string(const string& text)
{
    if (text == "cauchy")
        return CAUCHY;
    else if (text == "cauchy_mix")
        return CAUCHY_MIX;
    else
        throw std::invalid_argument("radial_type_from_string: Invalid"
                                    " value '" + text +"' provided");
}

typedef std::pair<int, int> Season;

inline Season seasonality_from_option(const Option* opt)
{
    return {std::atoi(opt->answers[0]), std::atoi(opt->answers[1])};
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
    for (int j = 0; j < S_rast.getHeight(); j++) {
        for (int k = 0; k < S_rast.getWidth(); k++) {
            if (S_rast(j, k) > 0)
                allInfected = false;
        }
    }
    return allInfected;
}

#ifdef SOD_NETCDF_SUPPORT
void get_spatial_weather(NcVar *mcf_nc, NcVar *ccf_nc, double* mcf, double* ccf, double* weather, int width, int height, int step)
{
    // read the weather information
    if (!mcf_nc->set_cur(step, 0, 0)) {
        cerr << "Can not read the coefficients from the mcf_nc pointer to mcf array " << step << endl;
        exit(EXIT_FAILURE);
    }
    if (!ccf_nc->set_cur(step, 0, 0)) {
        cerr << "Can not read the coefficients from the ccf_nc pointer to ccf array "<< step << endl;
        exit(EXIT_FAILURE);
    }
    if (!mcf_nc->get(mcf, 1, height, width)) {
        cerr << "Can not get the record from mcf_nc " << step << endl;
        exit(EXIT_FAILURE);
    }
    if (!ccf_nc->get(ccf, 1, height, width)) {
        cerr << "Can not get the record from ccf_nc " << step << endl;
        exit(EXIT_FAILURE);
    }
    for (int j = 0; j < height; j++) {
        for (int k = 0; k < width; k++) {
            weather[j * width + k] = mcf[j * width + k] * ccf[j * width + k];
        }
    }
}
#endif

// TODO: create image which is float/double/template
void array_from_grass_raster(const char* name, double* array,
                             unsigned width, unsigned height)
{
    int fd = Rast_open_old(name, "");

    for (int row = 0; row < height; row++) {
        Rast_get_d_row(fd, array + (row * width), row);
    }

    Rast_close(fd);
}

void weather_rasters_to_array(const string& moisture_name,
                              const string& temperature_name,
                              double* mcf, double* ccf, double* weather,
                              unsigned width, unsigned height)
{
    // read the weather information
    array_from_grass_raster(moisture_name.c_str(), mcf, width, height);
    array_from_grass_raster(temperature_name.c_str(), ccf, width, height);
    for (unsigned j = 0; j < height; j++) {
        for (unsigned k = 0; k < width; k++) {
            weather[j * width + k] = mcf[j * width + k] * ccf[j * width + k];
        }
    }
}

struct SodOptions
{
    struct Option *species, *lvtree, *infected, *outside_spores;
    struct Option *nc_weather, *moisture_file, *temperature_file, *weather_value, *weather_file;
    struct Option *lethal_temperature_value, *lethal_temperature_months;
    struct Option *actual_temperature_file;
    struct Option *start_time, *end_time, *seasonality;
    struct Option *step;
    struct Option *spore_rate, *wind;
    struct Option *radial_type, *scale_1, *scale_2, *kappa, *gamma;
    struct Option *infected_to_dead_rate, *first_year_to_die;
    struct Option *dead_series;
    struct Option *seed, *runs, *threads;
    struct Option *output, *output_series;
    struct Option *stddev, *stddev_series;
    struct Option *output_probability;
};

struct SodFlags
{
    struct Flag *mortality;
    struct Flag *generate_seed;
    struct Flag *series_as_single_run;
};


int main(int argc, char *argv[])
{
    SodOptions opt;
    SodFlags flg;

    G_gisinit(argv[0]);

    struct GModule *module = G_define_module();

    G_add_keyword(_("raster"));
    G_add_keyword(_("spread"));
    G_add_keyword(_("model"));
    G_add_keyword(_("disease"));
    module->description = _("Stochastic landscape spread model of forest pathogen - Sudden Oak Death (SOD)");

    opt.species = G_define_standard_option(G_OPT_R_INPUT);
    opt.species->key = "species";
    opt.species->description = _("Input infected species raster map");
    opt.species->guisection = _("Input");

    opt.lvtree = G_define_standard_option(G_OPT_R_INPUT);
    opt.lvtree->key = "lvtree";
    opt.lvtree->description = _("Input live tree (all) raster map");
    opt.lvtree->guisection = _("Input");

    // TODO: is this oaks?
    opt.infected = G_define_standard_option(G_OPT_R_INPUT);
    opt.infected->key = "infected";
    opt.infected->description = _("Initial sources of infection raster map");
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
    opt.outside_spores->required = NO;
    opt.outside_spores->guisection = _("Output");

    opt.wind = G_define_option();
    opt.wind->type = TYPE_STRING;
    opt.wind->key = "wind";
    opt.wind->label = _("Prevailing wind direction");
    opt.wind->description = _("NONE means that there is no wind");
    opt.wind->options = "N,NE,E,SE,S,SW,W,NW,NONE";
    opt.wind->required = YES;
    opt.wind->guisection = _("Weather");

    opt.nc_weather = G_define_standard_option(G_OPT_F_BIN_INPUT);
    opt.nc_weather->key = "ncdf_weather";
    opt.nc_weather->description = _("Weather data");
    opt.nc_weather->required = NO;
    opt.nc_weather->guisection = _("Weather");

    opt.moisture_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.moisture_file->key = "moisture_file";
    opt.moisture_file->label =
        _("Input file with one moisture map name per line");
    opt.moisture_file->description =
        _("Moisture coefficient");
    opt.moisture_file->required = NO;
    opt.moisture_file->guisection = _("Weather");

    opt.temperature_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.temperature_file->key = "temperature_file";
    opt.temperature_file->label =
        _("Input file with one temperature map name per line");
    opt.temperature_file->description =
        _("Temperature coefficient");
    opt.temperature_file->required = NO;
    opt.temperature_file->guisection = _("Weather");

    opt.weather_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.weather_file->key = "weather_file";
    opt.weather_file->label = _("Text file with weather");
    opt.weather_file->description =
            _("Moisture and temperature");
    opt.weather_file->required = NO;
    opt.weather_file->guisection = _("Weather");

    opt.weather_value = G_define_option();
    opt.weather_value->type = TYPE_INTEGER;
    opt.weather_value->key = "weather_value";
    opt.weather_value->label = _("Value to be used as weather coeficient");
    opt.weather_value->description =
            _("Spatially and temporally constant weather coeficient"
              " (usually moisture times temperture)");
    opt.weather_value->required = NO;
    opt.weather_value->guisection = _("Weather");

    opt.lethal_temperature_value = G_define_option();
    opt.lethal_temperature_value->type = TYPE_DOUBLE;
    opt.lethal_temperature_value->key = "lethal_temperature";
    opt.lethal_temperature_value->label =
        _("Temperature when the pest or patogen dies");
    opt.lethal_temperature_value->description =
        _("The temerature unit must be the same as for the"
          "temerature raster map (typically degrees of Celsius)");
    opt.lethal_temperature_value->required = NO;
    opt.lethal_temperature_value->multiple = NO;
    opt.lethal_temperature_value->guisection = _("Weather");

    opt.lethal_temperature_months = G_define_option();
    opt.lethal_temperature_months->type = TYPE_INTEGER;
    opt.lethal_temperature_months->key = "lethal_month";
    opt.lethal_temperature_months->label =
        _("Month when the pest or patogen dies due to low temperature");
    opt.lethal_temperature_months->description =
        _("The temerature unit must be the same as for the"
          "temerature raster map (typically degrees of Celsius)");
    // TODO: implement this as multiple
    opt.lethal_temperature_months->required = NO;
    opt.lethal_temperature_months->guisection = _("Weather");

    // TODO: rename coefs in interface and improve their descs
    opt.actual_temperature_file = G_define_standard_option(G_OPT_F_INPUT);
    opt.actual_temperature_file->key = "actual_temperature_file";
    opt.actual_temperature_file->label =
        _("Input file with one temperature raster map name per line");
    opt.actual_temperature_file->description =
        _("The temperature should be in actual temperature units (typically degrees of Celsius)");
    opt.actual_temperature_file->required = NO;
    opt.actual_temperature_file->guisection = _("Weather");

    opt.start_time = G_define_option();
    opt.start_time->type = TYPE_INTEGER;
    opt.start_time->key = "start_time";
    opt.start_time->label = _("Start year for the simulation");
    opt.start_time->description = _("The first day of the year will be used");
    opt.start_time->required = YES;
    opt.start_time->guisection = _("Time");

    opt.end_time = G_define_option();
    opt.end_time->type = TYPE_INTEGER;
    opt.end_time->key = "end_time";
    opt.end_time->label = _("End year for the simulation");
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
    opt.seasonality->answer = "1,12";
    opt.seasonality->multiple = NO;
    opt.seasonality->guisection = _("Time");

    opt.step = G_define_option();
    opt.step->type = TYPE_STRING;
    opt.step->key = "step";
    opt.step->label = _("Step of simulation");
    opt.step->description = _("How often the simulation computes new step");
    opt.step->options = "week,month";
    opt.step->descriptions = _("week;Compute next simulation step each week;month;Compute next simulation step each month");
    opt.step->required = YES;
    opt.step->guisection = _("Time");

    opt.spore_rate = G_define_option();
    opt.spore_rate->type = TYPE_DOUBLE;
    opt.spore_rate->key = "spore_rate";
    opt.spore_rate->label = _("Spore production rate per week for each infected tree");
    opt.spore_rate->answer = "4.4";
    opt.spore_rate->guisection = _("Spores");

    opt.radial_type = G_define_option();
    opt.radial_type->type = TYPE_STRING;
    opt.radial_type->key = "radial_type";
    opt.radial_type->label = _("Radial distribution type");
    opt.radial_type->answer = "cauchy";
    opt.radial_type->options = "cauchy,cauchy_mix";
    opt.radial_type->guisection = _("Spores");

    opt.scale_1 = G_define_option();
    opt.scale_1->type = TYPE_DOUBLE;
    opt.scale_1->key = "scale_1";
    opt.scale_1->label = _("Scale parameter for the first Cauchy distribution");
    opt.scale_1->answer = "20.57";
    opt.scale_1->guisection = _("Spores");

    opt.scale_2 = G_define_option();
    opt.scale_2->type = TYPE_DOUBLE;
    opt.scale_2->key = "scale_2";
    opt.scale_2->label = _("Scale parameter for the second Cauchy distribution");
    opt.scale_2->guisection = _("Spores");

    opt.kappa = G_define_option();
    opt.kappa->type = TYPE_DOUBLE;
    opt.kappa->key = "kappa";
    opt.kappa->label = _("Concentration parameter for the von Mises distribution");
    opt.kappa->answer = "2";
    opt.kappa->guisection = _("Spores");

    opt.gamma = G_define_option();
    opt.gamma->type = TYPE_DOUBLE;
    opt.gamma->key = "gamma";
    opt.gamma->label = _("Gamma parameter for Bernoulli distribution");
    opt.gamma->description = _("Probability of using the first Cauchy distribution");
    opt.gamma->options = "0-1";
    opt.gamma->guisection = _("Spores");

    opt.infected_to_dead_rate = G_define_option();
    opt.infected_to_dead_rate->type = TYPE_DOUBLE;
    opt.infected_to_dead_rate->key = "mortality_rate";
    opt.infected_to_dead_rate->label =
        _("Mortality rate of infected trees");
    opt.infected_to_dead_rate->description =
        _("Percentage of infected trees that die in a given year"
          " (trees are removed from the infected pool)");
    opt.infected_to_dead_rate->options = "0-1";
    opt.infected_to_dead_rate->guisection = _("Mortality");

    opt.first_year_to_die = G_define_option();
    opt.first_year_to_die->type = TYPE_INTEGER;
    opt.first_year_to_die->key = "mortality_start";
    opt.first_year_to_die->label =
        _("Year of simulation when mortality is first applied");
    opt.first_year_to_die->description =
        _("How many years it takes for an infected tree to die"
          " (value 1 for trees dying at the end of the first year)");
    opt.first_year_to_die->guisection = _("Mortality");

    opt.dead_series = G_define_standard_option(G_OPT_R_BASENAME_OUTPUT);
    opt.dead_series->key = "dead_series";
    opt.dead_series->label =
        _("Basename for series of number of dead trees");
    opt.dead_series->description =
        _("Basename for output series of number of dead trees"
          " (requires mortality to be activated)");
    opt.dead_series->required = NO;
    opt.dead_series->guisection = _("Mortality");

    flg.mortality = G_define_flag();
    flg.mortality->key = 'm';
    flg.mortality->label =
        _("Apply mortality");
    flg.mortality->description =
        _("After a given amount of time, start removing dead trees"
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
          " and will be avaraged for the output");
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
    G_option_exclusive(opt.moisture_file, opt.nc_weather,
                       opt.weather_file, opt.weather_value, NULL);
    G_option_exclusive(opt.temperature_file, opt.nc_weather,
                       opt.weather_file, opt.weather_value, NULL);
    G_option_collective(opt.moisture_file, opt.temperature_file, NULL);

    // mortality
    // flag and rate required always
    // for simplicity of the code outputs allowed only with output
    // for single run (avgs from runs likely not needed)
    G_option_requires(flg.mortality, opt.infected_to_dead_rate, NULL);
    G_option_requires(opt.first_year_to_die, flg.mortality, NULL);
    G_option_requires_all(opt.dead_series, flg.mortality,
                          flg.series_as_single_run, NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

#ifndef SOD_NETCDF_SUPPORT
    if (opt.nc_weather->answer) {
        G_fatal_error(_("Direct NetCDF support is not available in this"
                        " installation, import the data instead"));
    }
#endif

    unsigned num_runs = 1;
    if (opt.runs->answer)
        num_runs = std::stoul(opt.runs->answer);

    unsigned threads = 1;
    if (opt.threads->answer)
        threads = std::stoul(opt.threads->answer);

    // check for file existence
    file_exists_or_fatal_error(opt.moisture_file);
    file_exists_or_fatal_error(opt.temperature_file);
    file_exists_or_fatal_error(opt.weather_file);

    // Seasonality: Do you want the spread to be limited to certain months?
    Season season = seasonality_from_option(opt.seasonality);

    Direction pwdir = direction_enum_from_string(opt.wind->answer);

    // set the spore rate
    double spore_rate = std::stod(opt.spore_rate->answer);
    Rtype rtype = radial_type_from_string(opt.radial_type->answer);
    double scale1 = std::stod(opt.scale_1->answer);
    double scale2 = 0;
    if (rtype == CAUCHY_MIX && !opt.scale_2->answer)
        G_fatal_error(_("The option %s is required for %s=%s"),
                      opt.scale_2->key, opt.radial_type->key,
                      opt.radial_type->answer);
    else if (opt.scale_2->answer)
        scale2 = std::stod(opt.scale_2->answer);
    double kappa = std::stod(opt.kappa->answer);
    double gamma = 0.0;
    if (rtype == CAUCHY_MIX && !opt.gamma->answer)
        G_fatal_error(_("The option %s is required for %s=%s"),
                      opt.gamma->key, opt.radial_type->key,
                      opt.radial_type->answer);
    else if (opt.gamma->answer)
        gamma = std::stod(opt.gamma->answer);

    // initialize the start Date and end Date object
    // options for times are required ints
    int start_time = std::stoi(opt.start_time->answer);
    int end_time = std::stoi(opt.end_time->answer);
    if (start_time > end_time) {
        cerr << "Start date must precede the end date!!!" << endl;
        exit(EXIT_FAILURE);
    }

    Date dd_start(start_time, 01, 01);
    Date dd_end(end_time, 12, 31);
    // difference in years (in dates) but including both years
    auto num_years = dd_end.getYear() - dd_start.getYear() + 1;

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
        // flag of option is required
        std::random_device rd;
        seed_value = rd();
        G_verbose_message(_("Generated random seed (-%c): %ud"),
                          flg.generate_seed->key, seed_value);
    }

    // read the suspectible UMCA raster image
    Img species_rast = Img::fromGrassRaster(opt.species->answer);

    // read the living trees raster image
    Img lvtree_rast = Img::fromGrassRaster(opt.lvtree->answer);

    // read the initial infected oaks image
    Img I_species_rast = Img::fromGrassRaster(opt.infected->answer);

    // create the initial suspectible oaks image
    Img S_species_rast = species_rast - I_species_rast;

    // SOD-immune trees image
    //Img SOD_rast = umca_rast + oaks_rast;
    //Img IMM_rast = lvtree_rast - SOD_rast;

    // retrieve the width and height of the images
    int width = species_rast.getWidth();
    int height = species_rast.getHeight();

#ifdef SOD_NETCDF_SUPPORT
    std::shared_ptr<NcFile> weather_coeff = nullptr;
#else
    bool weather_coeff = false;
#endif
    std::vector<string> moisture_names;
    std::vector<string> temperature_names;
    double weather_from_rasters = false;
    std::vector<double> weather_values;
    double weather_value = 0;

#ifdef SOD_NETCDF_SUPPORT
    if (opt.nc_weather->answer)
        weather_coeff = std::make_shared<NcFile>(opt.nc_weather->answer, NcFile::ReadOnly);
#else
    if (false)
        ;
    // TODO: switch order of ifs to avoid this
#endif
    else if (opt.moisture_file->answer && opt.temperature_file->answer) {
        read_names(moisture_names, opt.moisture_file->answer);
        read_names(temperature_names, opt.temperature_file->answer);
        weather_from_rasters = true;
    }
    else if (opt.weather_file->answer)
        weather_values = weather_file_to_list(opt.weather_file->answer);
    else if (opt.weather_value->answer)
        weather_value = std::stoi(opt.weather_value->answer);
    else
        weather_value = 1;  // no change (used in multiplication)

#ifdef SOD_NETCDF_SUPPORT
    if (weather_coeff && !weather_coeff->is_valid()) {
        cerr << "Can not open the weather coefficients file(.cn)!" << endl;
        exit(EXIT_FAILURE);
    }

    // TODO: do we need to free this? docs is 404
    NcVar *mcf_nc = nullptr;
    NcVar *ccf_nc = nullptr;

    if (weather_coeff && !(mcf_nc = weather_coeff->get_var("Mcoef"))) {
        cerr << "Can not read the moisture coefficients from the file!" <<
            endl;
        exit(EXIT_FAILURE);
    }

    if (weather_coeff && !(ccf_nc = weather_coeff->get_var("Ccoef"))) {
        cerr << "Can not read the temperature coefficients from the file!" <<
            endl;
        exit(EXIT_FAILURE);
    }
#endif

    double use_lethal_temperature = false;
    double lethal_temperature_value;
    int lethal_temperature_month = 0;  // invalid value for month
    std::vector<string> actual_temperature_names;
    std::vector<DImg> actual_temperatures;
    if (opt.lethal_temperature_value->answer)
        lethal_temperature_value = std::stod(opt.lethal_temperature_value->answer);
    if (opt.lethal_temperature_months->answer)
        lethal_temperature_month = std::stod(opt.lethal_temperature_months->answer);
    if (opt.actual_temperature_file->answer) {
        file_exists_or_fatal_error(opt.actual_temperature_file);
        read_names(actual_temperature_names, opt.actual_temperature_file->answer);
        for (string name : actual_temperature_names) {
            actual_temperatures.push_back(DImg::fromGrassRaster(name.c_str()));
        }
        use_lethal_temperature = true;
    }

    const unsigned max_weeks_in_year = 53;
    double *mcf = nullptr;
    double *ccf = nullptr;
    double *weather = nullptr;
    if (weather_coeff || weather_from_rasters) {
        mcf = new double[height * width];
        ccf = new double[height * width];
        weather = new double[max_weeks_in_year * height * width];
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
    for (unsigned i = 0; i < num_runs; ++i)
        sporulations.emplace_back(seed_value++, I_species_rast);
    std::vector<std::vector<std::tuple<int, int> > > outside_spores(num_runs);

    std::vector<unsigned> unresolved_weeks;
    unresolved_weeks.reserve(max_weeks_in_year);

    Date dd_current(dd_start);

    // main simulation loop (weekly steps)
    for (int current_week = 0; ; current_week++, step == "month" ? dd_current.increasedByMonth() : dd_current.increasedByWeek()) {
        if (dd_current < dd_end)
            if (season.first >= dd_current.getMonth() && dd_current.getMonth() <= season.second)
                unresolved_weeks.push_back(current_week);

        // removal is out of sync with the actual runs but it does
        // not matter as long as removal happends out of season
        if (use_lethal_temperature
                && dd_current.getMonth() == lethal_temperature_month
                && (dd_current.getYear() <= dd_end.getYear())) {
            // to avoid problem with Jan 1 of the following year
            // we explicitely check if we are in a valid year range
            unsigned simulation_year = dd_current.getYear() - dd_start.getYear();
            if (simulation_year >= actual_temperatures.size())
                G_fatal_error(_("Not enough temperatures"));
            #pragma omp parallel for num_threads(threads)
            for (unsigned run = 0; run < num_runs; run++) {
                sporulations[run].SporeRemove(inf_species_rasts[run],
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
        if ((step == "month" ? dd_current.isLastMonthOfYear() : dd_current.isYearEnd()) || dd_current >= dd_end) {
            if (!unresolved_weeks.empty()) {

                unsigned week_in_chunk = 0;
                // get weather for all the weeks
                for (auto week : unresolved_weeks) {
                    double *week_weather = weather + week_in_chunk * width * height;
#ifdef SOD_NETCDF_SUPPORT
                    if (weather_coeff) {
                        get_spatial_weather(mcf_nc, ccf_nc, mcf, ccf, week_weather, width, height, week);
                    }
#else
                    if (false)
                        ;
                    // TODO: switch order of ifs to avoid this
#endif
                    else if (weather_from_rasters) {
                        weather_rasters_to_array(moisture_names[week],
                                                 temperature_names[week],
                                                 mcf, ccf, week_weather,
                                                 width, height);
                    }
                    ++week_in_chunk;
                }

                // stochastic simulation runs
                #pragma omp parallel for num_threads(threads)
                for (unsigned run = 0; run < num_runs; run++) {
                    unsigned week_in_chunk = 0;
                    // actual runs of the simulation per week
                    for (auto week : unresolved_weeks) {
                        double *week_weather = 0;
                        if (weather) {
                            week_weather = weather + week_in_chunk * width * height;
                        }
                        if (!weather_coeff && !weather_values.empty()) {
                            weather_value = weather_values[week];
                        }
                        sporulations[run].SporeGen(inf_species_rasts[run], week_weather, weather_value, spore_rate);

                        auto current_age = dd_current.getYear() - dd_start.getYear();
                        sporulations[run].SporeSpreadDisp_singleSpecies(sus_species_rasts[run], inf_species_rasts[run],
                                                                        inf_species_cohort_rasts[run][current_age],
                                                                        lvtree_rast, outside_spores[run],
                                                                        rtype, week_weather,
                                                                        weather_value, scale1, kappa, pwdir, scale2,
                                                                        gamma);
                        ++week_in_chunk;
                    }
                }
                unresolved_weeks.clear();
            }
            if (mortality && (dd_current.getYear() <= dd_end.getYear())) {
                // to avoid problem with Jan 1 of the following year
                // we explicitely check if we are in a valid year range
                unsigned simulation_year = dd_current.getYear() - dd_start.getYear();
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
                        }
                        inf_species_rasts[run] -= dead_in_current_year[run];
                    }
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
                    inf_species_rasts[0].toGrassRaster(name.c_str());
                else
                    I_species_rast.toGrassRaster(name.c_str());
            }
            if (opt.stddev_series->answer) {
                Img stddev(I_species_rast.getWidth(), I_species_rast.getHeight(),
                           I_species_rast.getWEResolution(), I_species_rast.getNSResolution(), 0);
                for (unsigned i = 0; i < num_runs; i++) {
                    Img tmp = inf_species_rasts[i] - I_species_rast;
                    stddev += tmp * tmp;
                }
                stddev /= num_runs;
                stddev.for_each([](int& a){a = std::sqrt(a);});
                string name = generate_name(opt.stddev_series->answer, dd_current);
                stddev.toGrassRaster(name.c_str());
            }
            if (mortality && opt.dead_series->answer) {
                accumulated_dead += dead_in_current_year[0];
                if (opt.dead_series->answer) {
                    string name = generate_name(opt.dead_series->answer, dd_current);
                    accumulated_dead.toGrassRaster(name.c_str());
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
        I_species_rast.toGrassRaster(opt.output->answer);
    }
    if (opt.stddev->answer) {
        Img stddev(I_species_rast.getWidth(), I_species_rast.getHeight(),
                   I_species_rast.getWEResolution(), I_species_rast.getNSResolution(), 0);
        for (unsigned i = 0; i < num_runs; i++) {
            Img tmp = inf_species_rasts[i] - I_species_rast;
            stddev += tmp * tmp;
        }
        stddev /= num_runs;
        stddev.for_each([](int& a){a = std::sqrt(a);});
        stddev.toGrassRaster(opt.stddev->answer);
    }
    if (opt.output_probability->answer) {
        Img probability(I_species_rast.getWidth(), I_species_rast.getHeight(),
                        I_species_rast.getWEResolution(), I_species_rast.getNSResolution(), 0);
        for (unsigned i = 0; i < num_runs; i++) {
            Img tmp = inf_species_rasts[i];
            tmp.for_each([](int& a){a = bool(a);});
            probability += tmp;
        }
        probability *= 100;  // prob from 0 to 100 (using ints)
        probability /= num_runs;
        probability.toGrassRaster(opt.output_probability->answer);
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

    // clean the allocated memory
    if (weather) {
        delete[] mcf;
        delete[] ccf;
        delete[] weather;
    }

    return 0;
}
