# Unit Tests

In addition to the code of the module itself, it is important to include a suite of
tests. They guarantee that your add-on will remain functional when changes are
applied to the code on which it depends. Once committed to GitHub, the unit
tests are automatically run by the CI/CD pipeline every time the code in the
repository is modified. Notifications are issued if a modification somehow
affects your add-on.

## Requirements

The unit tests depend on the GRASS development package. It might already be
installed on your system, but make sure. On a packaged operating system like
Ubuntu or Debian Linux this can be achieved with:

```bash
sudo apt install grass-dev
```

If you have not done so yet, it is also helpful to install pre-commit. Follow
[the
instructions](https://github.com/OSGeo/grass/blob/main/doc/development/submitting/submitting.md#use-pre-commit)
in the main GRASS repository.

## Create a unit test

Unit tests must be stored in a subfolder named `testsuite` inside the add-on
folder. For example, if you contributed a raster module named `r.mymodule` you
would run:

```bash
cd src/raster/r.mymodule
mkdir testsuite
```

Then you can create a new Git branch and initiate a new unit test class:

```bash
git checkout new-branch
vim testsuite/test_mymodule.py
```

The [unit testing
documentation](https://grass.osgeo.org/grass-stable/manuals/libpython/gunittest_testing.html)
in the GRASS Reference Manual provides an overview on how to create unit tests
for C/C++ and Python code. Going through existing unit tests of a module
like
[r.sun](https://github.com/OSGeo/grass/blob/main/raster/r.sun/testsuite/test_rsun.py)
is also insightful.

## Run a unit test

In most circumstances you will wish to run the unit tests against a local
version of the add-on that you recently modified or created. To do so you need
to install this local version on your GRASS installation.

First start a new grass session. Does not matter on which location or mapset.

```bash
grass /home/user/GRASSDATA/location/mapset
```

Then use the flexibility of `g.extension` to install the add-on from the file
system.

```bash
g.extension r.mblend url=/home/user/git/grass-addons/src/raster/r.mymodule
```

You can now run the unit tests from the GRASS session, for example:

```bash
python testsuite/test_mymodule.py
```

## Submit a unit test

The [general contribution
guidelines](https://github.com/OSGeo/grass-addons/blob/master/CONTRIBUTING.md#changing-code-and-documentation)
apply to unit tests. In case you are submitting a new add-on, the unit tests
should feature in the pull request with the module itself. Otherwise submit the
unit tests in a dedicated pull request to facilitate the work of the reviewers.
