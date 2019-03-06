# Change Log

All notable changes to this project should be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).

## 2018-11-17

- Added mortality function to simulation class

## 2018-10-31 - Minor Refactoring

### Added

- Added Season class to manage seasonality

### Changed

- Removed resolution from the Raster class

## 2018-09-20 - Variable Rename

### Added

- Created a style guide in a CONTRIBUTING file. (Vaclav Petras)

### Changed

- Renamed variables and functions to make the model more clear and easy
  to understand. (Chris Jones)
- Renaming and partial unification of styles across all files. (Vaclav Petras)
 - All is now in namespace called pops.
 - Private variables use trailing underscore if needed.
- Removed unused and legacy functions and types. (Vaclav Petras)

## 2018-08-02 - PoPS Model Separation

### Changed

- The general part of the simulation is now a separate library called
  PoPS. GRASS GIS module code was removed together with some parts of
  this file completely unrelated to the library. (Vaclav Petras)
- All files which were not supposed to be part of the repository
  were removed and purged from the history. However, all the relevant
  history is preserved. (Vaclav Petras)

## 2018-06-21 - Spotted Lanternfly

### Added

- The date class now supports also month increments. (Vaclav Petras)
- Critical temperature as the lowest temperature spores can survive
  in a provided month (Vaclav Petras)
 - Temperature rasters are used at a specified month to check against
   a provided critical temperature and if the condition is met,
   infected trees become susceptible again.

### Changed

- Img was replaced by a generalized Raster template class which can
  handle both integers and floating point numbers. (Vaclav Petras)

## 2018-06-04 - Mortality Addition

### Added

- Mortality (Vaclav Petras)
- Image class constructor taking another image using its dimensions
  and a provided value (Vaclav Petras)
- Multiply for image class is commutative (Vaclav Petras)

## 2018-03-26 - March 2018 Update

### Changed

- Explicitly include necessary standard C++ headers (Vaclav Petras)

## 2017-09-05 - September 2017 Update

### Added

- Long-range dispersal kernel (Anna Petrasova)
 - Events are recorded.
 - The affected points are exported as a vector map.
- Output probability of cell being infected (Vaclav Petras)
- Optionally output one run for series instead of an average (Vaclav Petras)

### Changed

- Spread of SOD based on a single species (Anna Petrasova)
 - Spread for UMCA and oak replaced by single species, assumed tanoak.

## 2017-01-28 - January 2017 Status

### Added

- Simplified weather inputs (Vaclav Petras)
 - Weather can be supplied as as a text file (spatially constant)
 - Weather can be supplied as one variable (non-spatial and non-temporal)

### Changed

- Efficiency improvements (Vaclav Petras)
 - Enable inlining of size getters of Img class which makes all_infected
   function much faster.
 - Move constructor and assignment operator added for cases when RVO
   is not applied.
 - Internal storage changed to one array (usually faster allocation).
- Code cleanup (Vaclav Petras)
 - Use same API style for Von Mises as for std lib distributions.
 - Creating data for Img outside of the object is avoided.
 - Indexing the Img done using operator ().
 - Using operators for all operations which fit semantically.
 - Remove unused variables from the code.
 - The 'using namespace' statement replaced by explicit use 'using' for
   string and other classes or objects.
- Date class API extended to provide readable comparison operators
  replacing usage of method with unclear name (Anna Petrasova)
- The cpl_string dependency was removed. (Vaclav Petras)
- The sporulation object is now seeded only once in the beginning.
  This changes the stochastic output of one run. (Anna Petrasova)

### Fixed

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
