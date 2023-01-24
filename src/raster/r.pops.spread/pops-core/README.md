# PoPS Core - Pest or Pathogen Spread Model Core

[![Build Status](https://travis-ci.org/ncsu-landscape-dynamics/pops-core.svg?branch=master)](https://travis-ci.org/ncsu-landscape-dynamics/pops-core)

PoPS Core is the core C++ library for the PoPS Model.

PoPS (Pest or Pathogen Spread) is a stochastic spread model of pests
and pathogens in forest and agricultural landscapes.
It is used for various pest, pathogens, and hosts.
It was originally developed for *Phytophthora ramorum* and the original
version of the model was written in R, later with Rcpp,
and was based on Meentemeyer (2011) paper.

PoPS Core is a header-only C++ library.
It is using templates for the main spatial data structures, i.e., rasters,
to be universal and it makes use of C++11 features, so C++11 is the minimal
required version.

## How to cite

If you use this software or code, please cite the following papers:

* Ross K. Meentemeyer, Nik J. Cunniffe, Alex R. Cook, Joao A. N. Filipe,
  Richard D. Hunter, David M. Rizzo, and Christopher A. Gilligan, 2011.
  Epidemiological modeling of invasion in heterogeneous landscapes:
  spread of sudden oak death in California (1990–2030).
  *Ecosphere* 2:art17.
  [DOI: 10.1890/ES10-00192.1](https://doi.org/10.1890/ES10-00192.1)

* Tonini, Francesco, Douglas Shoemaker, Anna Petrasova, Brendan Harmon,
  Vaclav Petras, Richard C. Cobb, Helena Mitasova,
  and Ross K. Meentemeyer, 2017.
  Tangible geospatial modeling for collaborative solutions
  to invasive species management.
  *Environmental Modelling & Software* 92: 176-188.
  [DOI: 10.1016/j.envsoft.2017.02.020](https://doi.org/10.1016/j.envsoft.2017.02.020)

In case you are using the automatic management feature in rpops or the
steering version of r.pops.spread (from the branch steering), please
cite also:

* Petrasova, A., Gaydos, D.A., Petras, V., Jones, C.M., Mitasova, H. and
  Meentemeyer, R.K., 2020.
  Geospatial simulation steering for adaptive management.
  *Environmental Modelling & Software* 133: 104801.
  [DOI: 10.1016/j.envsoft.2020.104801](https://doi.org/10.1016/j.envsoft.2020.104801)

In addition to citing the above paper, we also encourage you to
reference, link, and/or acknowledge specific version of the software
you are using for example:

* *We have used rpops R package version 1.0.0 from
  <https://github.com/ncsu-landscape-dynamics/rpops>*.

## Contributing

This section is designed to clarify the branch structure and versioning of
this repository (and interface repositories) and general naming of new
features and bug fix branches, especially those that are take longer to
develop.

### Branch Structure

1. **master** is the stable version of the model that is used for official
   releases.
2. **fix-issuenumber** or **fix-bugdescription** are branched off of master
   then merged back via a pull request once bug is fixed.
3. **new_feature** is where new features are developed before they are merged
   into Master via a pull request. For example, infect and vector are currently
   being developed and will be merged together prior to being merged to master
   for an official major version release.

### Bug Fixes

Most bugs/issues will be found in the **master** branch as it is the branch
being used in the R package and Grass module. Thus bug fixes should be merged
into **master** once tested on both R and Grass. Bug fixes should be released
as minor versions (e.g. if major release is 1.0 then the first bug fix would
be released as version 1.1 and both R and Grass would be updated to 1.1.0). If
a bug is found in one of the interfaces (R package or Grass module) that
doesn't require a change to PoPS Core then these repositories should be
updated indepentantly and maintain a patch release 1.0.x. For example, if the
current version of the R package is 1.1.0 and Grass module is 1.1.0 and a bug
is found in the R package then the R package version becomes 1.1.1 while the
Grass version is 1.1.0. However, the version number is still shared for all
the projects, so when a new version of the GRASS module is needed, it will
be 1.1.2.

### New Features

When creating new features create a branch from **master** using the following
syntax **new_feature**. For example, we want to add a transportation network
model for human assisted dispersal, the branch created would be named
`transportation_network_model` (or similar). New features will be merged into
**master** once tested based on the priorities of our stakeholders first. Once
new features are tested in R and Grass with the latest bug fixes and any other
new features being included in the next major release we will merge them into
**master** and create an official major release version (e.g. update from
version 1.1 to version 2.0 and the R package and Grass module are updated
to 2.0.0). When you are creating branches in your fork, we still recommend
choosing informative names such as the one suggested above.

If you are interested in contributing to PoPS and are not a core developer
on the model, please take a look at following documents to make the process
as seamless as possible.

1. [Contributor Code of Conduct](contributing_docs/CODE_OF_CONDUCT.md)
1. [PoPS Core Style Guide](contributing_docs/STYLE_GUIDE.md)
1. [Contributor Guide](contributing_docs/CONTRIBUTING.md)

## C++ API

The stable API to be used in other projects includes the `pops::Model`
and `pops::Config` classes and classes used in their API (for example,
`pops::SpreadRate`).
This API is changed only beween major versions or, if really needed,
to fix serious issues in the released major version.

Other classes and functions are part of the internal API and although
you can use them in your project, you will need to follow the changes
in the library more closely and update your code more often.

If you are using the C++ API, we invite you to open an issue in this
repository to tell us about it and we can both acknowledge you in this
repo or elsewhere and discuss planned changes with you.

## Core Functions

If you are interested in reviewing the code, you may want to focus at
the following core functions rather than the API.

simulation.remove : removes the pest or pathogen from the infested hosts
based on some environmental threshold (currently only temperature is
accounted for).

simulation.generate : generates dispersing indivduls from all infested
cells based as a function of local infected hosts and weather.

simulation.disperse : creates dispersal locations for the dispersing
individuals from the generate function.

simulation.mortality : causes mortality in infested/infected hosts based
on mortality rate

The custom date class is used to easily manage different time steps within
the model and account for differences in the way frequently used weather
data sets treat leap years (DAYMET drops December 31st from leap years,
PRISM keeps all days even for leap years)

## Using the model

The PoPS Core library can be used directly in a C++ program or through other
programs. It is used in R package called rpops and a GRASS GIS module
called r.pops.spread.

* <https://github.com/ncsu-landscape-dynamics/r.pops.spread>
* <https://github.com/ncsu-landscape-dynamics/rpops>

## Integrating the library into your own project

### As a Git submodule

This is a convenient way, if you are using Git and you can use the C++
header files directly.

Git supports inclusion of other repositories into your own code using
a mechanism called submodules. In your repository, run:

```bash
git submodule add https://github.com/ncsu-landscape-dynamics/pops-core
```

If you want a specific branch of PoPS Core, after adding the
PoPS submodule, run the following commands (with branch-name being
the branch of the PoPS library you want to use):

```bash
cd pops-core
git checkout origin/branch-name
```

The will create a directory called `pops-core` in your repository which
will now contain all the files from this repository. You can use the two
following commands to see the changes to your repository:

```bash
git status
git diff --cached
```

Git added a file called `.gitmodules` with the link to this repository
and linked a specific commit in this repository. The commit linked is
the currently latest commit to PoPS library.

You can now commit and push changes to your repository.

When someone else clones our project, they need to run the two following
commands to get the content of the `pops-core` directory:

```bash
git submodule init
git submodule update
```

Alternatively, the `pops-core` directory can be populated during cloning
when `git clone` is used with the `--recurse-submodules` parameter.

If you want to update the specific PoPS commit your repository is using
to the latest one, you the following command:

```bash
git submodule update --remote
```

## Compile and test

Here we are assuming that you use Linux command line or equivalent
and you have CMake and C++ compiler installed.
We are testing with GNU GCC with (`g++`) and GNU make (`make`),
but many of other tools supported by CMake should work too.
See CMake documentation for different ways of compiling.

First download the source code (as a ZIP file and unpack it or use Git
to get it from the Git repository).

Configure the project and use directory called `build` for configure and
build outputs:

```bash
cmake -S . -B build
```

Build the project:

```bash
cmake --build build
```

The library itself does not need compilation since it is header only
(it is compiled later with your project), but this compiled several
test programs.

To run these tests:

```bash
cmake --build build --target test
```

If something is wrong, this will generate error messages.
Note that not all tests are not fully automatic, so in couple cases
this only testing if the code is running and not crashing
(you will need to examine the source code to see the details).

Additionally, create documentation using the following (*Doxygen* required):

```bash
cmake --build build --target docs
```

The HTML documentation will appear in the `html` subdirectory of `build`
directory. Open the file called `index.html` to access it in a web browser.

Optionally, to remove the build directory when you are done, use:

```bash
rm -rf build
```

## Compiling as part of another project

Note that if you are not using CMake, you can just add the headers to
your project since this a header-only library. However,
if you are using CMake, you probably want to use the following approach.

Assuming you added the directory as a submodule or a plain subdirectory
called `pops-core` add these two following lines to your `CMakeLists.txt` file
(assuming you already have target called `your_target`):

```text
add_subdirectory(pops-core)
target_link_libraries(your_target PRIVATE pops-core)
```

## Authors and contributors

### Authors

*(alphabetical order)*:

* Chris Jones
* Margaret Lawrimore
* Vaclav Petras
* Anna Petrasova

### Previous contributors

*(alphabetical order)*:

* Zexi Chen
* Devon Gaydos
* Francesco Tonini

See Git commit history, GitHub insights, or CHANGELOG.md file (if present)
for details about contributions.

## License

Permission to use, copy, modify, and distribute this software and
its documentation under the terms of the GNU General Public License
is hereby granted. No representations are made about the suitability
of this software for any purpose. It is provided "as is" without express
or implied warranty. See the
[GNU General Public License](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
for more details.
