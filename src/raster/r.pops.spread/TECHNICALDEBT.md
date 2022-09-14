# Technical Debt

All issues and imperfections of the code should be documented in this
file.

The goal is to declare the technical debt as described by
[Easterbrook 2014](http://doi.org/10.1038/ngeo2283) or Wikipedia
contributors in
[Technical debt](https://en.wikipedia.org/wiki/Technical_debt).

The sections are based on sections in CHANGELOG. The version refers to
when the problem first occurred or was encountered. Entries are divided,
similarly to CHANGELOG, into what is missing and needs to be added (Add),
what requires a changes of the current code (Change) and what is an
issue which needs to be fixed (Fix).

Entries should be removed when resolved. Issue from tracker can be
optionally linked in an entry.

## 2018-06-20 - Critical Temperature

### Add

- Add (rigorous) tests for the Raster class.
- Add more tests for the Date class.
- Documentation of the C++ functions and classes (use Doxygen).

### Change

- Naming and descriptions of parameters related to weather
  (coefficients versus the actual values)
- Naming of critical and actual temperature in code

### Fix

- Even after the upgrade to Raster class, there are still some legacy
  method names and integers instead of doubles (but does not influence
  computations).
- Spelling in the code and comments.

## 2018-06-13 - Spotted Lanternfly

### Add

- Add SLF parameters to documentation.
- Update README.

## 2018-06-04 - Mortality Addition

### Add

- Add mortality to documentation.
- Update README.

### Change

- Mortality cohorts may require better name since the individual can be
  potentially also a cohort or stand.

### Fix

- Mortality-related infection cohort always updated in spore spread and
  need an additional parameter. However, the update is just a repeating
  previous line (perhaps some container optionally wrapping two images
  would be useful).

## 2017-09-05 - September 2017 Update

### Fix

- Dead code for the specific multiple host species.

## 2017-01-28 - January 2017 Status

### Add

- Image class is only for integers but the weather is floating point,
  so it needs a different treatment in code than other data.
- The date class needs abstraction for the leap years and days in month.
- Tests needed for the image class.

### Change

- Formatting of text and parameters for the date class (leading zeros).
- Create dedicated file for the direction enum and helper functions.
- Some of the Date class methods have still misleading names (e.g.,
  increased versus increase).
- Methods and functions should use underscores not camel case (using
  Python and GRASS GIS convention).
