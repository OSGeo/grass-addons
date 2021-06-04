# GRASS GIS 6 Addons legacy repository

This is legacy code used with GRASS GIS 6.
It is useful for finding code for that old addon module which was not
ported to GRASS GIS 7 or for comparing the current version with the
old one which is possibly written in a different language or with
a very different API. Most addon modules, especially the most useful
ones were ported to GRASS GIS 7, so you should use the current version.

What follows are usage and contributing instruction written for
GRASS GIS 7 rather than 6. New contributions should go to the
current version.

The repository was restructured for archival, i.e., it is not meant
to be consumed by GRASS GIS 6 in any way except for manual compilation.

## How to get write access here

Read access is granted to the public, write access
must be requested, see here for details:
<https://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASSaddonsrepository>

However, it is also possible to fork this repository, insert your AddOn or fix
an existing one in a new branch and finally open
a [pull request](https://help.github.com/en/articles/about-pull-requests).

In either case, please read the submitting rules at the bottom of this page.

## How to get the AddOn code

Clone of the entire AddOns git repository:

```
git clone https://github.com/OSGeo/grass-addons.git grass_addons
```

## How to install or remove AddOns in your GRASS installation

The simplest way to install GRASS GIS AddOns is to use the `g.extension`
module:
<https://grass.osgeo.org/grass-stable/manuals/g.extension.html>

## How to compile AddOn code

### C code/Scripts, with GRASS source code on your computer

Preparations (assuming the source code in $HOME/grass64/):
(if you have already built GRASS from source you don't need to do this
again. If adding to a binary install the versions must match exactly.
For a git clone this means that the main GRASS binary and source
code versions (GRASS GIS 6 or 7) must match.)

```
./configure # [optionally flags]
make libs
```

The easiest way to compile GRASS AddOns modules into your GRASS code
is by setting MODULE_TOPDIR on the fly to tell 'make' where to
find the prepared GRASS source code:

```
make MODULE_TOPDIR=$HOME/grass64/
```

(adapt to your /path/to/grass64/). Each module/script in the GRASS
AddOns git repository should have a Makefile to support easy
installation.

Install then into your existing GRASS installation with

```
make MODULE_TOPDIR=$HOME/grass64/ install
```

For system-wide installation this usually requires "root" privileges
(so, also 'sudo' may help).

### C code/Scripts, with GRASS binaries on your computer

compile GRASS AddOns modules into your GRASS code by setting
MODULE_TOPDIR to where to the GRASS binaries are located:

```
make MODULE_TOPDIR=/usr/lib/grass64/
```

## How to submit contributions

To submit your GRASS GIS module here, please check

<https://grass.osgeo.org/development/>

The submission must be compliant with the GRASS
submission rules as found in the GRASS source code
and RFC2 (Legal aspects of submission):

<https://trac.osgeo.org/grass/wiki/RFC>

Also read submitting instructions before committing any changes!

<https://trac.osgeo.org/grass/wiki/Submitting>

## License

The code is under GNU General Public License v2.0 or later (GPL-2.0-or-later).
