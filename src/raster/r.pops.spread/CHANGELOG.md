# Change Log

All notable changes to this project should be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).

## 2020-04-16 - SEI model

- Added
  - Add SEI modeling using model_type and latency_period parameters. (Vaclav Petras)
- Changed
  - Reduced scope of mortality_simulation_year variable. (Vaclav Petras)

## 2018-09-18 - July 2019 improvements

- Changed
  - The Raster class now allows access to internal structures which is
    now used for initialization and saving of raster maps. (Vaclav Petras)
    - The ability to change the raster types with one line is preserved.
    - FCELL (float) rasters are now (properly) supported.
  - Output rasters and vector now have metadata with the command used,
    simulation timestamp, and title. (Vaclav Petras)
  - The remaining susceptible hosts check is now faster. (Vaclav Petras)

## 2018-09-18 - Update to the next generation of PoPS library

- Changed
  - The direct support for reading NetCDF removed from the code (Vaclav Petras)
  - Weather coefficient value input removed (Vaclav Petras)
    - Not considered useful enough to keep around, can be replaced by
      constant rasters and series of one raster.
  - Using new names in PoPS API (Vaclav Petras)
  - Weather coefficient represented as Raster with doubles (Vaclav Petras)
    - This or one of the changes above or in the library changed result of
      one stochastic run slightly (reason unknown, similar change as when
      multiplying coefficient by 1.000001). The new result is considered to
      be "more" correct.

## 2018-09-10 - Seasonality Fixes

- Added
  - Save GRASS GIS history for all raster outputs (Vaclav Petras)
    - The executed command with all parameters is stored in the matadata.
- Changed
  - Seasonality parameter is checked for emptiness and empty string is
    not allowed (Vaclav Petras)
  - Seasonality is now mostly handled in a separate class.
- Fixed
  - Current month is now checked if it is in the season (Vaclav Petras)
    - Fixes #1 (Metadata - missing full command used).
  - GRASS GIS library function now used to generate random seed (Vaclav Petras)
    - Previous implementation didn't give non-deterministic outputs with
      the -s flag on MS Windows.
    - Fixes #2 (Stochastic runs with -s are always the same on Windows).

## 2018-06-21 - Critical Temperature

- Added
  - Critical temperature as the lowest temperature spores can survive
    in a provided month (Vaclav Petras)
    - Time-series of temperature raster maps specified as a text file.
    - Temperature rasters are used at a specified month to check against
      a provided critical temperature and if the condition is met,
      infected trees become susceptible again.
- Changed
  - Img was replaced by a generalized Raster template class which can
    handle both integers and floating point numbers. (Vaclav Petras)

## 2018-06-13 - Spotted Lanternfly

- Added
  - The date class now supports also month increments. (Vaclav Petras)
  - A new step option allows user to choose between weekly and monthly
    increments in simulation. (Vaclav Petras)
  - A custom season can now be selected by the user. (Vaclav Petras)
  - A new test executable for the date class added and available in an
    alternative Makefile. (Vaclav Petras)
- Changed
  - The season option is no longer yes or no but a range of months.
    (Vaclav Petras)
- Fixed
  - Avoid segmentation fault by using the weather coefficients only when
    available. (Vaclav Petras)
  - Make the NetCDF time-series input option always present regardless
    compilation settings which avoids use of uninitialized variable later
    (and thus undefined behavior). Modules now produces error with
    explanation when option is used but it was compiled without NetCDF
    support. (Vaclav Petras)

## 2018-06-04 - Mortality Addition

- Added
  - Mortality (Vaclav Petras)
    - Enabled by a flag, mandatory mortality rate, optional start time
    - Optional output series of accumulated dead tree counts per cell
  - Image class constructor taking another image using its dimensions
    and a provided value (Vaclav Petras)
  - Multiply for image class is commutative (Vaclav Petras)

## 2018-03-26 - March 2018 Update

- Changed
  - Changes for automatic compilation in GRASS GIS Addons (Vaclav Petras)
    - GDAL support optional using ifdef
    - NetCDF support optional using ifdef
    - Explicitly include necessary standard C++ headers
    - Add formalities: basic documentation and a proper GRASS module name

## 2017-09-05 - September 2017 Update

- Added
  - Long-range dispersal kernel (Anna Petrasova)
    - Events are recorded.
    - The affected points are exported as a vector map.
  - Weather coefficients as GRASS GIS raster maps (Vaclav Petras)
    - Input weather coefficients are obtained from a file with list of map
      names (ordering and naming is resolved separately, e.g. same raster
      can be used multiple times, i.e. temporal oversampling is possible).
    - Weather rasters are now automatically resampled on the fly to the
      raster grid based the computational region.
  - Output probability of cell being infected (Vaclav Petras)
  - Optionally output one run for series instead of an average (Vaclav Petras)
- Changed
  - Spread of SOD based on a single species (Anna Petrasova)
    - Spread for UMCA and oak replaced by single species, assumed tanoak.
  - Final infected trees output is now optional (Vaclav Petras)
- Fixed
  - Interface now checks if only one way of providing weather coefficients
    was used. (Vaclav Petras)

## 2017-01-28 - January 2017 Status

- Added
  - GRASS GIS interface added (Vaclav Petras)
    - Main spatial inputs handled through GRASS GIS libraries so that
      different extents and resolutions can be used. (Not implemented for
      the weather time series.)
    - Text and numerical inputs hardcoded in defines replaced by
      description using GRASS GIS library. Command line parameters are now
      parsed, checked including dependencies, and it is possible to open
      GUI.
    - All hardcoded parameters replaced by command line parameters.
    - Basic descriptions for all parameters.
    - GDAL input and output is in the code.
  - Multiple stochastic runs and parallelization (Vaclav Petras)
    - Optionally outputs also stdandard deviation.
    - Aggregates series output from runs.
    - Creates OpenMP threads for chunks of weeks.
    - User can set number of threads from command line (or GUI).
  - Simplified weather inputs (Vaclav Petras)
    - Weather can be supplied as as a text file (spatially constant)
    - Weather can be supplied as one variable (non-spatial and non-temporal)
- Changed
  - Efficiency improvements (Vaclav Petras)
    - Enable inlining of size getters of Img class which makes all_infected
      function much faster.
    - Move constructor and assignment operator added for cases when RVO
      is not applied.
    - Internal storage changed to one array (usually faster allocation).
    - Use the interal data directly to write using GDAL output.
  - Code cleanup (Vaclav Petras)
    - Time measurement code removed (use external tool such as time instead).
    - Commented-out code for seeding by time removed.
    - Use same API style for Von Mises as for std lib distributions.
    - Creating data for Img outside of the object is avoided.
    - Indexing the Img done using operator ().
    - Using operators for all operations which fit semantically.
    - Remove unused variables from the code.
    - The 'using namespace' statement replaced by explicit use 'using' for
      string and other classes or objects.
  - Date class API extended to provide readable comparison operators
    replacing usage of method with unclear name (Anna Petrasova)
  - Random seed for generators is required or must be explicitly generated.
  - The cpl_string dependency was removed. (Vaclav Petras)
  - The sporulation object is now seeded only once in the beginning.
    This changes the stochastic output of one run. (Anna Petrasova)
- Fixed
  - Initialize memory for the sporulation object for the cases when it is
    zero cases to fix conditional jump which depends on uninitialised
    value. (Vaclav Petras)
  - Memory allocation and deallocation is done by the right pair of
    malloc-free or new-delete. (Vaclav Petras)
  - Compilation output and other non-repository files removed from the
    repository. (Vaclav Petras)
  - Von Mises distribution concentration parameter is float not integer.
    (Vaclav Petras)
  - Copy of GDAL code was removed from the repository, using system GDAL
    includes now. (Vaclav Petras)
