# GRASS GIS Addons

This is the official GRASS GIS Addons git repository.
Head over to [GRASS GIS 7 Addons Manual
pages](https://grass.osgeo.org/grass78/manuals/addons/)
for an overview.

## Install AddOns

The simplest way to install GRASS GIS Addons is to use the `g.extension`
module which is part of any GRASS GIS installation:

<https://grass.osgeo.org/grass-stable/manuals/g.extension.html>

The same module can also remove installed addons.

## This repository

### Clone locally

Clone of the entire addons git repository:

```
git clone https://github.com/OSGeo/grass-addons.git grass_addons
```

### Write access

Read access is granted to the public, write access
must be requested, see here for details:
<https://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASSaddonsrepository>

However, it is also possible to fork this repository, insert your AddOn or fix
an existing one in a new branch and finally open
a [pull request](https://help.github.com/en/articles/about-pull-requests).

In either case, please read the submitting rules at the bottom of this page.

### Compile AddOns

#### With GRASS source code on your computer

Preparations (assuming the source code in $HOME/grass/):
(if you have already built GRASS from source you don't need to do this
again. If adding to a binary install, the versions must match exactly.
You need to git checkout the exact tag or commit used for the binary.)

```
./configure # [optionally flags]
make libs
```

The easiest way to compile GRASS AddOns modules into your GRASS code
is by setting MODULE_TOPDIR on the fly to tell 'make' where to
find the prepared GRASS source code:

```
make MODULE_TOPDIR=$HOME/grass/
```

(adapt to your /path/to/grass/). Each module/script in the GRASS
AddOns git repository should have a Makefile to support easy
installation.

Install then into your existing GRASS installation with

```
make MODULE_TOPDIR=$HOME/grass/ install
```

For system-wide installation this usually requires "root" privileges
(so, also 'sudo' may help).

#### With GRASS binaries on your computer

compile GRASS AddOns modules into your GRASS code by setting
MODULE_TOPDIR to where to the GRASS binaries are located:

```
make MODULE_TOPDIR=/usr/lib/grass/
```

### Contribute

To submit your GRASS GIS module here, please check

<https://grass.osgeo.org/development/>

The submission must be compliant with the GRASS
submission rules as found in the GRASS source code
and RFC2 (Legal aspects of submission):

<https://trac.osgeo.org/grass/wiki/RFC>

Also read submitting instructions before committing any changes!

<https://trac.osgeo.org/grass/wiki/Submitting>
