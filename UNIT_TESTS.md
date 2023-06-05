# Unit Tests

Besides the code of the module itself, it is important to submit in addition a
suite of tests. They guarantee your add-on remains functional when changes are
applied to the code on which it depends. Once committed to GitHub, the unit
tests are run automatically by the CI/CD pipeline every time the code in the
repository is modified. Notifications are issued if a modification somehow
impacts your add-on.

## Requirements

The unit tests depend on software that you must install in your system
beforehand: Subversion and the GRASS development package. On a packaged operating
system like Ubuntu or Debian Linux this can be achieved with:

```bash
sudo apt install subversion grass-dev
```

If you have not done so yet, it is also helpful to install pre-commit. Follow
[the
instructions](https://github.com/OSGeo/grass/blob/main/doc/development/submitting/submitting.md#use-pre-commit)
in the main GRASS repository.

## Create a unit test

Unit tests must be stored in a subfolder named `testsuite` inside the add-on
folder. For example, if you contributed a raster module named r.mymodule you
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
to install this local version on your GRASS installation, as in the example
below.

```bash
grass /home/user/GRASSDATA/location/mapset
g.extension r.mblend url=/home/user/git/grass-addons/src/raster/r.mymodule
```

You can then run the unit tests from the GRASS session, for example:

```bash
python3 testsuite/test_mymodule.py
```

## Submit a unit test

The [general contribution
guidelines](https://github.com/OSGeo/grass-addons/blob/master/CONTRIBUTING.md#changing-code-and-documentation)
apply to unit tests. To facilitate the work of reviewers it is better to
submit the unit tests in a dedicated pull request.
