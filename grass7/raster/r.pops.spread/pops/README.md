# PoPS (Pest or Pathogen Spread) Model

[![Build Status](https://travis-ci.org/ncsu-landscape-dynamics/PoPS.svg?branch=master)](https://travis-ci.org/ncsu-landscape-dynamics/PoPS)

PoPS library

PoPS (Pest or Pathogen Spread) is a C++ library for a stochastic spread model of pests and pathogens in forest and agricultural landscapes. It has been generalized and new features added but was originally developed for *Phytophthora ramorum* and the original version of the model was based on this reference paper: Ross K. Meentemeyer, Nik J. Cunniffe, Alex R. Cook, Joao A. N. Filipe, Richard D. Hunter, David M. Rizzo, and Christopher A. Gilligan 2011. Epidemiological modeling of invasion in heterogeneous landscapes: spread of sudden oak death in California (1990–2030). *Ecosphere* 2:art17. [http://dx.doi.org/10.1890/ES10-00192.1] (http://www.esajournals.org/doi/abs/10.1890/ES10-00192.1) 

PoPS is a header-only C++ library. It is using templates to be universal and it makes use of C++11 features, so C++11 is the minimal
required version.

## Contributing

This section is designed to clarify the branch structure of this repository and where new features and bug fixes should go.

### Branch Structure

1. **master** is the stable version of the model that is used for official releases. 
2. **bugfix/thingnotworking** are branched off of master then merged back via a pull request once bug is fixed.
3. **feature/new_feature** is where new features are developed before they are merged into Master via a pull request. For example, infect and vector are currently being developed and will be merged together prior to being merged to master for an official major version release.

### Bug Fixes

Most bugs/issues will be found in the **master** branch as it is the branch being used in the R package and Grass Module. Thus bug fixes should be merged into **master** once tested on both R and Grass. Bug fixes should be released as minor versions (e.g. if major release is 1.0 then the first bug fix would be released as version 1.1).

### New Features

When creating new features create a branch from **master** using the following syntax **feature/new_feature**. For example, we want to add a transportation network model for human assisted dispersal, the branch created would be named feature/transportation_network_model (or similar). New features will be merged into **master** once tested based on the priorities of our stakeholders first. Once new features are tested in R and Grass with the latest bug fixes and any other new features being included in the next major release we will merge them into **master** and create an official major release version (e.g. update from version 1.1 to version 2.0). 

If you are interested in contributing to PoPS development and are not a core developer on the model, please take a look at following
documents to make the process as seamless as possible.

1. [Contributor Code of Conduct](contributing_docs/CODE_OF_CONDUCT.md)
1. [PoPS Style Guide](contributing_docs/STYLE_GUIDE.md)
1. [Contributor Guide](contributing_docs/CONTRIBUTING.md)

## Main Functions

simulation.remove : removes the pest or pathogen from the infested hosts based on some environmental threshold (currently only temperature is accounted for).

simulation.generate : generates dispersing indivduls from all infested cells based as a function of local infected hosts and weather.

simulation.disperse : creates dispersal locations for the dispersing individuals from the generate function.

simulation.mortality : causes mortality in infested/infected hosts based on mortality rate

The custom date class is used to easily manage different time steps within the model and account for differences in the way frequently used weather data sets treat leap years (DAYMET drops December 31st from leap years, PRISM keeps all days even for leap years)

## Using the model

The PoPS library can be used directly in a C++ program or through other
programs. It is used in an experimental version of a GRASS GIS module
called r.spread.pest.

* https://github.com/ncsu-landscape-dynamics/r.pops.spread

It is also used in the pops_model function in R.

* https://github.com/ncsu-landscape-dynamics/rpops

## Integrating the library into your own project

### As a Git submodule

This is a convenient way, if you are using Git and you can use the C++
header files directly.

Git supports inclusion of other repositories into your own code using
a mechanism called submodules. In your repository, run:

```
git submodule add https://github.com/ncsu-landscape-dynamics/PoPS pops
```

If you want a specific branch of the PoPS library. After adding the 
PoPS submodule, run the following commands (with branch-name being
the branch of the PoPS library you want to use):

```
cd pops
git checkout origin/branch-name
```

The will create a directory called `pops` in your repository which will
now contain all the files from this repository. You can use the two
following commands to see the changes to your repository:

```
git status
git diff --cached
```

Git added a file called `.gitmodules` with the link to this repository
and linked a specific commit in this repository. The commit linked is
the currently latest commit to PoPS library.

You can now commit and push changes to your repository.

When someone else clones our project, they need to run the two following
commands to get the content of the `pops` directory:

```
git submodule init
git submodule update
```

Alternatively, the `pops` directory can be populated during cloning
when `git clone` is used with the `--recurse-submodules` parameter.

If you want to update the specific PoPS commit your repository is using
to the latest one, you the following command:

```
git submodule update --remote
```

## Testing the model in this repository

Here we are assuming that you use Linux command line or equivalent,
i.e., you have `make` (e.g. GNU make) and GNU GCC with `g++`
(or something compatible with the same command line interface).
If you don't have it, you may need to modify the `Makefile` or configure
your system.

First download the source code (as a ZIP file and unpack it or use Git
to get it from the Git repository).

Then compile the code:

    make

The library itself does not need compilation since it is header only
(it is compiled later with your project), but this compiles several
test programs.

Finally, run the tests:

    make test

This will generate some test output, to see if all was right, you will
need to examine the source code. The tests are not fully automatic
and currently cover only the bare minimum.

Additionally, if you have Doxygen, to generate documentation run:

    make doc

The HTML documentation will appear in the `html` directory. Open the
file called `index.html` to access it in a web browser.

## Authors

* Vaclav Petras (raster handling, critical temperature, library, ...)
* Anna Petrasova (single species simulation)
* Chris Jones (rename, SEID, ...)

## Previous Contributors

* Francesco Tonini (original R version)
* Zexi Chen (initial C++ version)

## License

Permission to use, copy, modify, and distribute this software and
its documentation under the terms of the GNU General Public License
is hereby granted. No representations are made about the suitability
of this software for any purpose. It is provided "as is" without express
or implied warranty. See the
[GNU General Public License](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
for more details.
