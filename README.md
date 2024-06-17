# GRASS GIS Addons Code Repository

## How to get the addon code

Clone of the entire repository:

```bash
git clone https://github.com/OSGeo/grass-addons.git grass-addons
```

## How to install or remove addons in your GRASS installation

The simplest way to install GRASS GIS Addons is to use the `g.extension`
module:
<https://grass.osgeo.org/grass-stable/manuals/g.extension.html>

`g.extension` can install from the online repository (the default) or from
local source code (not available on Windows).

## How to compile addon code

### Compilation with GRASS GIS binaries on your computer

In this case, compile GRASS addon modules into your installed GRASS code
by setting `MODULE_TOPDIR` to where to the GRASS binaries are located:

```bash
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

The easiest way to compile GRASS addons modules into your GRASS code
is by setting `MODULE_TOPDIR` on the fly to tell `make` where to
find the prepared GRASS source code:

```bash
make MODULE_TOPDIR=$HOME/grass/
```

(adapt as needed to your `/path/to/grass/`). Each module in the GRASS
Addons repository should have a Makefile to support easy
installation.

Install then into your existing GRASS installation with

```bash
make MODULE_TOPDIR=$HOME/grass/ install
```

For system-wide installation the install step usually requires "root" privileges
(so, also `sudo` may help).

## How to submit your contributions

While read access is granted to the public, for submissions you best fork
this repository, insert your addon or fix an existing one in a new branch
and finally open a [pull request](https://help.github.com/en/articles/about-pull-requests).

Please note the following submitting rules: To successfully
submit your GRASS GIS Addon module here, please check

<https://grass.osgeo.org/development/>

Your submission must be compliant with the GRASS
submission rules as found in the GRASS source code
and [RFC2 (Legal aspects of submission)](https://github.com/OSGeo/grass/blob/main/doc/development/rfc/legal_aspects_of_code_contributions.md).

Also, please read the general GRASS contributing instructions before creating a pull request:
<https://github.com/OSGeo/grass/?tab=readme-ov-file#contributing>

If you aim at becoming code maintainer with full write access, this must be
formally requested, see here for details:
<https://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASSaddonsrepository>
