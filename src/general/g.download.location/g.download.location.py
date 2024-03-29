#!/usr/bin/env python
############################################################################
#
# MODULE:    g.download.location
# AUTHOR(S): Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:   Download and extract location from web
# COPYRIGHT: (C) 2017 by the GRASS Development Team
#
#    This program is free software under the GNU General
#    Public License (>=v2). Read the file COPYING that
#    comes with GRASS for details.
#
#############################################################################

# %module
# % label: Download GRASS Location from the web
# % description: Get GRASS Location from an URL or file path
# % keyword: general
# % keyword: data
# % keyword: download
# % keyword: import
# %end
# %option
# % key: url
# % multiple: no
# % type: string
# % label: URL of the archive with a location to be downloaded
# % description: URL of ZIP, TAR.GZ, or other similar archive
# % required: yes
# %end
# %option G_OPT_M_LOCATION
# % key: name
# % required: no
# % multiple: no
# % key_desc: name
# %end
# %option G_OPT_M_DBASE
# % key: path
# % required: no
# % multiple: no
# %end
# %option
# % key: dbase
# % multiple: no
# % type: string
# % label: Path to database, use path option instead
# % description: This option is obsolete and replaced by path
# % required: no
# %end
# %rules
# % exclusive: path,dbase
# %end

import os
import shutil
import tempfile
import atexit

try:
    from urllib2 import HTTPError, URLError
    from urllib import urlopen, urlretrieve
except ImportError:
    # there is also HTTPException, perhaps change to list
    from urllib.error import HTTPError, URLError
    from urllib.request import urlopen, urlretrieve

import grass.script as gs
from grass.script.utils import try_rmdir


class DownloadError(Exception):
    pass


# TODO: multiple functions copied or modified from g.extension and
# startup screen Download button
# all should go to "grass.scripts.tools"


# copy from g.extension
def move_extracted_files(extract_dir, target_dir, files):
    """Fix state of extracted file by moving them to different diretcory

    When extracting, it is not clear what will be the root directory
    or if there will be one at all. So this function moves the files to
    a different directory in the way that if there was one directory extracted,
    the contained files are moved.
    """
    gs.debug("move_extracted_files({0})".format(locals()))
    if len(files) == 1:
        actual_path = os.path.join(extract_dir, files[0])
        if os.path.isdir(actual_path):
            shutil.copytree(actual_path, target_dir)
        else:
            shutil.copy(actual_path, target_dir)
    else:
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        for file_name in files:
            actual_file = os.path.join(extract_dir, file_name)
            if os.path.isdir(actual_file):
                # shutil.copytree() replaced by copy_tree() because
                # shutil's copytree() fails when subdirectory exists
                shutil.copytree(actual_file, os.path.join(target_dir, file_name))
            else:
                shutil.copy(actual_file, os.path.join(target_dir, file_name))


# copy from g.extension
def extract_zip(name, directory, tmpdir):
    """Extract a ZIP file into a directory"""
    gs.debug(
        "extract_zip(name={name}, directory={directory},"
        " tmpdir={tmpdir})".format(name=name, directory=directory, tmpdir=tmpdir),
        3,
    )
    try:
        import zipfile

        zip_file = zipfile.ZipFile(name, mode="r")
        file_list = zip_file.namelist()
        # we suppose we can write to parent of the given dir
        # (supposing a tmp dir)
        extract_dir = os.path.join(tmpdir, "extract_dir")
        os.mkdir(extract_dir)
        for subfile in file_list:
            # this should be safe in Python 2.7.4
            zip_file.extract(subfile, extract_dir)
        files = os.listdir(extract_dir)
        move_extracted_files(extract_dir=extract_dir, target_dir=directory, files=files)
    except zipfile.BadZipfile as error:
        raise DownloadError(_("ZIP file is unreadable: {0}").format(error))


# copy from g.extension
def extract_tar(name, directory, tmpdir):
    """Extract a TAR or a similar file into a directory"""
    gs.debug(
        "extract_tar(name={name}, directory={directory},"
        " tmpdir={tmpdir})".format(name=name, directory=directory, tmpdir=tmpdir),
        3,
    )
    try:
        import tarfile  # we don't need it anywhere else

        tar = tarfile.open(name)
        extract_dir = os.path.join(tmpdir, "extract_dir")
        os.mkdir(extract_dir)
        tar.extractall(path=extract_dir)
        files = os.listdir(extract_dir)
        move_extracted_files(extract_dir=extract_dir, target_dir=directory, files=files)
    except tarfile.TarError as error:
        raise DownloadError(_("Archive file is unreadable: {0}").format(error))
    except EOFError as error:
        raise DownloadError(_("Archive file is incomplete: {0}").format(error))


extract_tar.supported_formats = ["tar.gz", "gz", "bz2", "tar", "gzip", "targz", "xz"]


def download_end_extract(source):
    tmpdir = tempfile.mkdtemp()
    directory = os.path.join(tmpdir, "location")
    if source.endswith(".zip"):
        archive_name = os.path.join(tmpdir, "location.zip")
        # TODO: except IOError from urlretrieve
        f, h = urlretrieve(source, archive_name)
        if h.get("content-type", "") != "application/zip":
            raise DownloadError(
                _("Download of <%s> failed " "or file is not a ZIP file") % source
            )
        extract_zip(name=archive_name, directory=directory, tmpdir=tmpdir)
    elif "." in source and (
        source.endswith(".tar.gz")
        or source.rsplit(".", 1)[1] in extract_tar.supported_formats
    ):
        if source.endswith(".tar.gz"):
            ext = "tar.gz"
        else:
            ext = source.rsplit(".", 1)[1]
        archive_name = os.path.join(tmpdir, "extension." + ext)
        urlretrieve(source, archive_name)
        # TODO: error handling for urlretrieve
        extract_tar(name=archive_name, directory=directory, tmpdir=tmpdir)
    else:
        # probably programmer error
        # TODO: use GUI way
        raise DownloadError(_("Unknown format '{0}'.").format(source))
    if not os.path.isdir(directory):
        # If there is only one file ZIP and TAR extractions just
        # extract that file under the provided directory name.
        raise DownloadError(
            _("Archive contains only one file and no mapset directories")
        )
    return directory


# based on grass.py
def is_location_valid(location):
    """Return True if GRASS Location is valid

    :param location: path of a Location
    """
    # DEFAULT_WIND file should not be required until you do something
    # that actually uses them. The check is just a heuristic; a directory
    # containing a PERMANENT/DEFAULT_WIND file is probably a GRASS
    # location, while a directory lacking it probably isn't.
    # TODO: perhaps we can relax this and require only permanent
    return os.access(os.path.join(location, "PERMANENT", "DEFAULT_WIND"), os.F_OK)


def find_location_in_directory(path, recurse=0):
    """Return path to location in one of the subdirectories or None

    The first location found is returned. The expected usage is looking for one
    location somewhere nested in subdirectories.

    By default only the immediate subdirectories of the provided directory are
    tested, but with ``recurse >= 1`` additional levels of subdirectories
    are tested for being locations.

    Directory names are sorted to provide a stable result.

    :param path: Path to the directory to search
    :param recurse: How many additional levels of subdirectories to explore
    """
    assert recurse >= 0
    full_paths = [os.path.join(path, i) for i in os.listdir(path)]
    candidates = sorted([i for i in full_paths if os.path.isdir(i)])
    for candidate in candidates:
        if is_location_valid(candidate):
            return candidate
    if recurse:
        for candidate in candidates:
            result = find_location_in_directory(candidate, recurse - 1)
            if result:
                return result
    return None


def location_name_from_url(url):
    return url.rsplit("/", 1)[1].split(".", 1)[0].replace("-", "_").replace(" ", "_")


def main(options, flags):
    url = options["url"]
    name = options["name"]
    database = options["path"]
    if not database:
        database = options["dbase"]

    if not database:
        # use current
        database = gs.gisenv()["GISDBASE"]
    if not name:
        name = location_name_from_url(url)
    destination = os.path.join(database, name)

    if os.path.exists(destination):
        gs.fatal(_("Location named <%s> already exists," " download canceled") % name)
        return

    gs.message(_("Downloading and extracting..."))
    try:
        directory = download_end_extract(url)
        atexit.register(lambda: try_rmdir(directory))
    except DownloadError as error:
        gs.fatal(_("Unable to get the location: {error}").format(error=error))
    if not is_location_valid(directory):
        gs.verbose(_("Searching for valid location..."))
        # This in fact deal with location being on the third level of directories
        # thanks to how the extraction functions work (leaving out one level).
        result = find_location_in_directory(directory, recurse=1)
        if result:
            # We just want to show relative path in the message.
            # The relative path misses the root directory (name), because we
            # loose it on the way. (We should use parent directory to get the
            # full relative path, but the directory name is diffrent now.
            # This is the consequence of how the extract functions work.)
            relative = os.path.relpath(result, start=directory)
            gs.verbose(
                _("Location found in a nested directory '{directory}'").format(
                    directory=relative
                )
            )
            directory = result
        else:
            # The list is similarly misleading as the relative path above
            # as it misses the root directory, but it still should be useful.
            files_and_dirs = os.listdir(directory)
            gs.fatal(
                _(
                    "The dowloaded file is not a valid GRASS Location."
                    " The extracted file contains these files and directories:"
                    "\n{files_and_dirs}"
                ).format(files_and_dirs=" ".join(files_and_dirs))
            )
    gs.verbose(_("Copying to final destination..."))
    shutil.copytree(src=directory, dst=destination)
    gs.message(_("Path to the location now <{path}>").format(path=destination))


if __name__ == "__main__":
    main(*gs.parser())
