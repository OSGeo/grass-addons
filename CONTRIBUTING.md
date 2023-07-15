# Contributing

## Contributions other than code

There is more than one way of contributing, see full list at
<https://grass.osgeo.org/get-involved/>.
In the rest of this document, we will focus on contributions centered
around the GRASS GIS Addons source code.

## Reporting issues and suggesting features

To report an issue or to suggest features or a change,
[open an issue](https://github.com/OSGeo/grass-addons/issues/new/choose)
on GitHub.

## Changing code and documentation

This guide covers contributing to the latest version of GRASS GIS Addons
source code which is stored in a branch called _grass8_.
It assumes that you have some very basic knowledge of Git and GitHub,
but if you don't just go through some tutorial online or ask on the
GRASS GIS developer mailing list.

### First time setup

* Create an account on GitHub.
* Install Git on your computer.
* Set up Git with your name and email.
* Fork the repository.
* Clone your fork (use SSH or HTTPS URL):

```bash
git clone git@github.com:your_GH_account/grass-addons.git
```

* Enter the directory

```bash
cd grass-addons/
```

* Add main GRASS GIS Addons repository as "upstream" (use HTTPS URL):

```bash
git remote add upstream https://github.com/OSGeo/grass-addons
```

* Your remotes now should be "origin" which is your fork and "upstream" which
  is this main GRASS GIS Addons repository. You can confirm that using:

```bash
git remote -v
```

* You should see something like:

```text
origin  git@github.com:your_GH_account/grass-addons.git (fetch)
origin  git@github.com:your_GH_account/grass-addons.git (push)
upstream        https://github.com/OSGeo/grass-addons.git (fetch)
upstream        https://github.com/OSGeo/grass-addons.git (push)
```

It is important that "origin" points to your fork.

### Update before creating a feature branch

* Make sure your are starting with the branch for the latest version, i.e., _grass8_:

```bash
git checkout grass8
```

* Download updates from all branches from the _upstream_ remote:

```bash
git fetch upstream
```

* Update your local branch to match the one in the upstream repository:

```bash
git rebase upstream/grass8
```

### Update if you have local branches

If `rebase` fails with "error: cannot rebase: You have unstaged changes...",
then move your uncommitted local changes to "stash" using:

```bash
git stash
```

* Now you can rebase:

```bash
git rebase upstream/grass8
```

* Apply your local changes on top:

```bash
git stash apply
```

* Remove the stash record (optional):

```bash
git stash pop
```

### Creating a new feature branch

Now you have updated your local branch, you can create a feature branch
based on it.

* Create a new feature branch and switch to it:

```bash
git checkout -b new-feature
```

### Making changes

You can use your favorite tools to change source code or other files
in the local copy of the code. When make changes, please follow the
[Submitting Guidelines](https://github.com/OSGeo/grass/blob/main/doc/development/submitting/submitting.md).

### Committing

* Add files to the commit (changed ones or new ones):

```bash
git add file1
git add file2
```

* Commit the change (first word is the module name):

```bash
git commit -m "module: added a new feature"
```

### Pushing changes to GitHub

* Push your local feature branch to your fork:

```bash
git push origin new-feature
```

### Pull request

When you push, GitHub will respond back in the command line to tell
you what URL to use to create a pull request. You can follow that URL
or you can go any time later to your fork on GitHub, display the
branch `new-feature`, and GitHub will show you button to create
a pull request.

### After creating a pull request

GRASS GIS maintainers or users will now review your pull request.
If needed, they will work with you to improve your changes.

Once the changes in the pull request are ready to be accepted,
the maintainers will usually squash all your commits into one commit and merge it
to the _grass8_ branch.

Once the pull request is merged, it is a good time to update your
local _grass8_ branch in order to get there the change you just contributed.

### Further notes

GRASS GIS maintainers use additional workflows besides the one described
above. These are detailed at <https://trac.osgeo.org/grass/wiki/HowToGit>

## Unit tests

Consider including a unit test suite with your addon. More details in [these
instructions](doc/development/submitting/UNIT_TESTS.md).
