# GRASS Addons git repository

## How to get write access here?

Read access is granted to the public, write access
must be requested, see here for details: \
   https://trac.osgeo.org/grass/wiki/HowToContribute#WriteaccesstotheGRASSaddonsrepository

However, it is also possible to fork this repository, insert your AddOn or fix an existing one 
in a new branch and finally open a [pull request](https://help.github.com/en/articles/about-pull-requests).

In either case, please read the submitting rules at the bottom of this page.

## How to get the AddOn code?

Clone of the entire AddOns git repository:

    git clone https://github.com/OSGeo/grass-addons.git grass_addons

## How to install or remove AddOns in your GRASS installation

The simplest way to install GRASS GIS AddOns is to use the `g.extension` 
module: \
https://grass.osgeo.org/grass78/manuals/g.extension.html

##  How to compile AddOn code

### C code/Scripts, with GRASS source code on your computer:

  Preparations (assuming source code in $HOME/grass78/):
    (if you have already build GRASS from source you don't need to do this
    again. If adding to a binary install the versions must match exactly.
    For a git clone this means that the main GRASS binary and source
    code versions (GRASS GIS 6 or 7) must match.)
    
    ./configure # [opionally flags]
    make libs

  The easiest way to compile GRASS AddOns modules into your GRASS code 
  is by setting MODULE_TOPDIR on the fly to tell 'make' where to
  find the prepared GRASS source code:

    make MODULE_TOPDIR=$HOME/grass78/

  (adapt to your /path/to/grass78/). Each module/script in the GRASS
  AddOns git repository should have a Makefile to support easy
  installation.

  Install then into your existing GRASS installation with

    make MODULE_TOPDIR=$HOME/grass78/ install

  For system-wide installation this usually requires "root" priviledges 
  (so, also 'sudo' may help).

### C code/Scripts, with GRASS binaries on your computer:
  compile GRASS AddOns modules into your GRASS code by setting 
  MODULE_TOPDIR to where to the GRASS binaries are located:

    make MODULE_TOPDIR=/usr/lib/grass78/

## How to submitt contributions?

To submit your GRASS GIS module here, please check

   https://grass.osgeo.org/development/

The submmission must be compliant with the GRASS
submission rules as found in the GRASS source code
and RFC2 (Legal aspects of submission):

   https://trac.osgeo.org/grass/wiki/RFC

Also read submitting instructions before committing any changes!
   
   https://trac.osgeo.org/grass/wiki/Submitting
