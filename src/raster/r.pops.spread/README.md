# r.pops.spread

This is a GRASS GIS module _r.pops.spread_ for simulating spread of
pests and pathogens. The module is a GRASS GIS interface to the PoPS
(Pest or Pathogen Spread) model implemented in C++ library maintained
in the [PoPS Core repository](https://github.com/ncsu-landscape-dynamics/pops-core).

The purpose of the _r.pops.spread_ module is to provide easy way of
running the model in GRASS GIS environment once you have calibrated
the model for your purposes. You can obtain the calibration from a
colleague or published work or you can calibrate the model manually (in
GRASS GIS) or use the R interface to PoPS called
[rpops](https://github.com/ncsu-landscape-dynamics/rpops) to do that.

Note: Earlier versions of this module were called _r.spread.pest_ and
_r.spread.sod_.

## How to cite

If you use this software or code, please cite the following papers:

- Ross K. Meentemeyer, Nik J. Cunniffe, Alex R. Cook, Joao A. N. Filipe,
  Richard D. Hunter, David M. Rizzo, and Christopher A. Gilligan, 2011.
  Epidemiological modeling of invasion in heterogeneous landscapes:
  spread of sudden oak death in California (1990–2030).
  _Ecosphere_ 2:art17.
  [DOI: 10.1890/ES10-00192.1](https://doi.org/10.1890/ES10-00192.1)

- Tonini, Francesco, Douglas Shoemaker, Anna Petrasova, Brendan Harmon,
  Vaclav Petras, Richard C. Cobb, Helena Mitasova,
  and Ross K. Meentemeyer, 2017.
  Tangible geospatial modeling for collaborative solutions
  to invasive species management.
  _Environmental Modelling & Software_ 92: 176-188.
  [DOI: 10.1016/j.envsoft.2017.02.020](https://doi.org/10.1016/j.envsoft.2017.02.020)

In case you are using the automatic management feature in rpops or the
steering version of r.pops.spread (from the branch steering), please
cite also:

- Petrasova, A., Gaydos, D.A., Petras, V., Jones, C.M., Mitasova, H. and
  Meentemeyer, R.K., 2020.
  Geospatial simulation steering for adaptive management.
  _Environmental Modelling & Software_ 133: 104801.
  [DOI: 10.1016/j.envsoft.2020.104801](https://doi.org/10.1016/j.envsoft.2020.104801)

In addition to citing the above paper, we also encourage you to
reference, link, and/or acknowledge specific version of the software
you are using for example:

- _We have used rpops R package version 1.0.0 from
  <https://github.com/ncsu-landscape-dynamics/rpops>_.

## Download

### Download and install

The latest release of the _r.pops.spread_ module is available in GRASS GIS
Addons repository and can be installed directly in GRASS GIS through graphical
user interface or using the following command:

```bash
g.extension r.pops.spread
```

Alternatively, you can obtain latest source code here and install it
from this repository (see below).

### Source code download

Just use Git, but note that the
PoPS Core library is in a submodule, so use `--recursive` when cloning,
for example:

```bash
git clone --recursive git@github.com:ncsu-landscape-dynamics/r.pops.spread.git
```

If you have already cloned, you can obtain the submodules using:

```bash
git submodule update --init
```

Note that downloading as ZIP won't include the source code for the submodule,
so downloading as ZIP is not useful for this repo.

## Contributing

Please see the [pops-core](https://github.com/ncsu-landscape-dynamics/pops-core#readme)
repository for contributing best practices and release policies.
Other than that, just open pull requests against this repo.

### Updating submodule to latest version

To update the submodule, i.e. update submodule's commit used in this
repository, use:

```bash
git submodule update --remote
```

Note that this change is recorded in the repository. In other words,
the latest commit of a submodule is part of this repository.
The reason for this is that the code in this repository is linked to a
particular commit in the submodule repository (rather than the latest
version). Git works this way to avoid breaking things unexpectedly due
to changes in the submodule repository.

### Updating the code of the submodule

```bash
cd pops
git checkout master
git add file.hpp
git commit -m "this and that change"
git push
```

```bash
cd ..
git commit pops -m "update to latest pops commit"
git push
```

## The files

The `main.cpp` file contains the main program to run.
The model is in `pops-core/include/pops-core` directory.

## To run the model

You can use Linux to run the model in the following way.

Open an terminal and install dependencies:

```bash
sudo apt-get install grass grass-dev
```

Download this repo using Git (see above):

```bash
git clone ...
```

Change the current directory to the model directory:

```bash
cd ...
```

Compile:

```bash
grass --tmp-project XY --exec g.extension module=r.pops.spread url=.
```

Run (assuming you checked how to create a GRASS GIS mapset with our data):

```bash
grass .../modeling/scenario1 --exec r.pops.spread ...
```

## Authors and contributors

### Authors

_(alphabetical order)_:

- Chris Jones
- Margaret Lawrimore
- Vaclav Petras
- Anna Petrasova

### Previous contributors

_(alphabetical order)_:

- Zexi Chen
- Devon Gaydos
- Francesco Tonini

See Git commit history, GitHub insights, or CHANGELOG.md file (if present)
for details about contributions.

## License

Permission to use, copy, modify, and distribute this software and its documentation
under the terms of the GNU General Public License version 2 or higher is hereby
granted. No representations are made about the suitability of this software for any
purpose. It is provided "as is" without express or implied warranty.
See the GNU General Public License for more details.
