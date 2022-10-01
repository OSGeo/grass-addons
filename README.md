# GRASS Addons git repository

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

### Compilation with GRASS GIS binaries on your computer

In this case, compile GRASS AddOns modules into your installed GRASS code
by setting `MODULE_TOPDIR` to where to the GRASS binaries are located:

```
make MODULE_TOPDIR=/usr/lib/grass/
```

### Compilation with GRASS GIS core source code locally compiled

Preparations (assuming the [GRASS GIS core source code](https://github.com/OSGeo/grass)
being stored in `$HOME/grass/` - if you have already built GRASS GIS core from
source code you don't need to do this again. If adding to a binary install,
the versions must match exactly. You need to `git checkout` the exact tag
or commit used for the binary.)

```bash
# GRASS GIS core source code
./configure # [optionally flags]
make
```

The easiest way to compile GRASS AddOns modules into your GRASS code
is by setting `MODULE_TOPDIR` on the fly to tell `make` where to
find the prepared GRASS source code:

```
make MODULE_TOPDIR=$HOME/grass/
```

(adapt as needed to your `/path/to/grass/`). Each module/script in the GRASS
AddOns git repository should have a Makefile to support easy
installation.

Install then into your existing GRASS installation with

```
make MODULE_TOPDIR=$HOME/grass/ install
```

For system-wide installation this usually requires "root" privileges
(so, also `sudo` may help).

## How to submit your contributions

While read access is granted to the public, for submissions you best fork
this repository, insert your AddOn or fix an existing one in a new branch
and finally open a [pull request](https://help.github.com/en/articles/about-pull-requests).

If you aim at full write access, this must be formally requested, see here for details:
<https://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASSaddonsrepository>

In either case, please note the folloing submitting rules: To successfully submit your
GRASS GIS AddOn module here, please check

<https://grass.osgeo.org/development/>

Your submission must be compliant with the GRASS
submission rules as found in the GRASS source code
and RFC2 (Legal aspects of submission):

<https://trac.osgeo.org/grass/wiki/RFC>

Also read submitting instructions before committing any changes!

<https://trac.osgeo.org/grass/wiki/Submitting>
