#!/usr/bin/env python3
############################################################################
#
# MODULE:       m.prism.download
# AUTHOR(S):    Huidae Cho <grass4u gmail.com>
# PURPOSE:      Downloads data from the PRISM Climate Group.
#
# COPYRIGHT:    (C) 2023 by Huidae Cho and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# %module
# % description: Downloads data from the PRISM Climate Group.
# % keyword: PRISM
# % keyword: Climate data
# %end
# %option
# % key: dataset
# % type: string
# % description: Dataset index or ID
# % multiple: yes
# %end
# %option
# % key: start_date
# % type: string
# % description: Start date for search in YYYY-MM-DD (today for today; first for first date of first data year)
# %end
# %option
# % key: end_date
# % type: string
# % description: End date for search in YYYY-MM-DD (today for today; first for last date of first data year)
# %end
# %option G_OPT_F_SEP
# %end
# %flag
# % key: d
# % label: List supported datasets and exit
# %end
# %flag
# % key: u
# % label: List URLs only without downloading
# %end
# %flag
# % key: f
# % label: List filenames only without downloading
# %end
# %rules
# % required: -d, dataset
# % exclusive: -d, -u, -f
# %end

import sys
import os
import ftplib
import re
import datetime
import grass.script as grass
from grass.script.utils import separator


main_url = "ftp.prism.oregonstate.edu"
supported_datasets = [
    "daily/ppt",
    "daily/tdmean",
    "daily/tmax",
    "daily/tmean",
    "daily/tmin",
    "daily/vpdmax",
    "daily/vpdmin",
    "monthly/ppt",
    "monthly/tdmean",
    "monthly/tmax",
    "monthly/tmean",
    "monthly/tmin",
    "monthly/vpdmax",
    "monthly/vpdmin",
    "normals_4km/dem",
    "normals_4km/ppt",
    "normals_4km/solclear",
    "normals_4km/solslope",
    "normals_4km/soltotal",
    "normals_4km/soltrans",
    "normals_4km/tdmean",
    "normals_4km/tmax",
    "normals_4km/tmean",
    "normals_4km/tmin",
    "normals_4km/vpdmax",
    "normals_4km/vpdmin",
    "normals_800m/dem",
    "normals_800m/ppt",
    "normals_800m/solclear",
    "normals_800m/solslope",
    "normals_800m/soltotal",
    "normals_800m/soltrans",
    "normals_800m/tdmean",
    "normals_800m/tmax",
    "normals_800m/tmean",
    "normals_800m/tmin",
    "normals_800m/vpdmax",
    "normals_800m/vpdmin",
    "data_archive/ppt/daily_D1_201506",
    "data_archive/ppt/monthly_M2_201506",
    "data_archive/tdmean/daily_D1_201910",
    "data_archive/tdmean/monthly_M1_201910",
    "data_archive/tmax/daily_D1_201910",
    "data_archive/tmax/monthly_M2_201910",
    "data_archive/tmean/daily_D1_201910",
    "data_archive/tmean/monthly_M2_201910",
    "data_archive/tmin/daily_D1_201910",
    "data_archive/tmin/monthly_M2_201910",
    "data_archive/vpdmax/daily_D1_201910",
    "data_archive/vpdmax/monthly_M1_201910",
    "data_archive/vpdmin/daily_D1_201910",
    "data_archive/vpdmin/monthly_M1_201910",
]
first_year = 1895
re_index = re.compile("^[0-9]+$")
re_year = re.compile("^[0-9]{4}$")
re_ymd = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
re_filename_ym = re.compile("_([0-9]{6})_")
re_filename_ymd = re.compile("_([0-9]{8})_")


def fetch_nonyear_dirs(ftp, path=""):
    dirs = []
    try:
        for line in sorted(ftp.mlsd(path), key=lambda x: x[0]):
            if line[1]["type"] == "dir":
                d = line[0]
                if re_year.match(d):
                    return dirs
                else:
                    subpath = f"{path}/{d}" if path else f"{d}"
                    subdirs = fetch_nonyear_dirs(ftp, subpath)
                    if subdirs:
                        dirs.extend(subdirs)
                    else:
                        dirs.append(subpath)
    except ftplib.error_reply as e:
        grass.fatal(_("Failed to fetch dataset list"))
    return dirs


# slower
def fetch_nonyear_dataset_list():
    datasets = []
    try:
        with ftplib.FTP(main_url) as ftp:
            ftp.login()
            datasets.extend(fetch_nonyear_dirs(ftp))
    except ftplib.error_reply as e:
        grass.fatal(_("Failed to fetch dataset list"))
    return datasets


def fetch_dirs(ftp, path, depth):
    depth -= 1
    dirs = []
    try:
        for line in sorted(ftp.mlsd(path), key=lambda x: x[0]):
            if line[1]["type"] == "dir":
                d = line[0]
                subpath = f"{path}/{d}" if path else f"{d}"
                if depth:
                    subdirs = fetch_dirs(ftp, subpath, depth)
                    if subdirs:
                        dirs.extend(subdirs)
                    else:
                        dirs.append(subpath)
                else:
                    dirs.append(subpath)
    except ftplib.error_reply as e:
        grass.fatal(_("Failed to fetch dataset list"))
    return dirs


# slow
def fetch_dataset_list():
    datasets = []
    try:
        with ftplib.FTP(main_url) as ftp:
            ftp.login()
            for line in sorted(ftp.mlsd(), key=lambda x: x[0]):
                if line[1]["type"] == "dir":
                    d = line[0]
                    if d == "data_archive":
                        subdirs = fetch_dirs(ftp, d, 2)
                    else:
                        subdirs = fetch_dirs(ftp, d, 1)
                    if subdirs:
                        datasets.extend(subdirs)
                    else:
                        datasets.append(subpath)
    except ftplib.error_reply as e:
        grass.fatal(_("Failed to fetch dataset list"))
    return datasets


def show_datasets(sep):
    print(f"index{sep}dataset")
    for i in range(len(supported_datasets)):
        ds = supported_datasets[i]
        print(f"{i}{sep}{ds}")


def parse_dates(start_date, end_date):
    today = datetime.date.today()
    today_y = today.year
    today_m = today.month
    today_d = today.day
    today = today_y, today_m, today_d

    if start_date == "today":
        start = today
    elif start_date == "first":
        start = first_year, 1, 1
    else:
        start = start_date.split("-") if start_date else []
    if end_date == "today":
        end = today
    elif end_date == "first":
        end = first_year, 12, 31
    else:
        end = end_date.split("-") if end_date else []

    start_y = first_year if len(start) == 0 else int(start[0])
    start_m = 1 if len(start) <= 1 else int(start[1])
    start_d = 1 if len(start) <= 2 else int(start[2])
    end_y = today_y if len(end) == 0 else int(end[0])
    end_m = 12 if len(end) <= 1 else int(end[1])
    end_d = 31 if len(end) <= 2 else int(end[2])

    start_ymd = f"{start_y}-{start_m:02d}-{start_d:02d}"
    end_ymd = f"{end_y}-{end_m:02d}-{end_d:02d}"
    today_ymd = f"{today_y}-{today_m:02d}-{today_d:02d}"
    first_ymd = f"{first_year}-01-01"

    if start_ymd > end_ymd:
        grass.fatal(
            _(
                "<start_date={start_date}> cannot be later than <end_date={end_date}>"
            ).format(start_date=start_ymd, end_date=end_ymd)
        )

    if start_ymd < first_ymd:
        start_y, start_m, start_d = first_year, 1, 1
        start_ymd = first_ymd

    if end_ymd < first_ymd:
        grass.fatal(
            _(
                "No data to download because <end_date={end_date}> is earlier than first data year {first_year}"
            ).format(end_date=end_ymd, first_year=first_year)
        )

    if start_ymd > today_ymd:
        grass.fatal(
            _(
                "No data to download because <start_date={start_date}> is later than today"
            ).format(start_date=start_ymd)
        )

    if end_ymd > today_ymd:
        end_y, end_m, end_d = today_y, today_m, today_m
        end_ymd = today_ymd

    return start_y, start_m, start_d, end_y, end_m, end_d


def retrieve_path(ftp, path, sep, action, start_ymd=None, end_ymd=None):
    if "daily" in path:
        ds_type = "daily"
        start, end = start_ymd, end_ymd
        re_date = re_filename_ymd
    elif "monthly" in path:
        ds_type = "monthly"
        start, end = start_ymd[0:6], end_ymd[0:6]
        re_date = re_filename_ym
    else:
        re_date = None

    list_items = []
    for line in sorted(ftp.mlsd(path), key=lambda x: x[0]):
        if line[1]["type"] == "file":
            filename = line[0]
            if re_date:
                m = re_date.search(filename)
                if m and (m.group(1) < start or m.group(1) > end):
                    continue

            filepath = f"{path}/{filename}"
            url = f"https://{main_url}/{filepath}"
            if action == "download":
                try:
                    grass.message(
                        _("Downloading {filename}...").format(filename=filename)
                    )
                    with open(filename, "wb") as f:
                        ftp.retrbinary(f"RETR {filepath}", f.write)
                except:
                    grass.warning(
                        _("Failed to download {filename}").format(filename=filename)
                    )
            elif action == "list_filenames":
                list_items.append(filename)
            else:
                list_items.append(url)
    return list_items


def retrieve_data(datasets, start_date, end_date, sep, action):
    start_y, start_m, start_d, end_y, end_m, end_d = parse_dates(start_date, end_date)
    start_ymd = f"{start_y}{start_m:02d}{start_d:02d}"
    end_ymd = f"{end_y}{end_m:02d}{end_d:02d}"
    list_items = []
    try:
        with ftplib.FTP(main_url) as ftp:
            ftp.login()
            for ds in datasets:
                if ds.startswith("normals_"):
                    list_items.extend(retrieve_path(ftp, ds, sep, action))
                else:
                    for y in range(start_y, end_y + 1):
                        path = f"{ds}/{y}"
                        try:
                            list_items.extend(
                                retrieve_path(
                                    ftp, path, sep, action, start_ymd, end_ymd
                                )
                            )
                        except ftplib.error_perm as e:
                            grass.warning(e)
    except ftplib.error_reply as e:
        grass.fatal(_("Failed to fetch dataset list"))

    if list_items:
        print(sep.join(list_items))


def main():
    dataset = options["dataset"].split(",")
    start_date = options["start_date"]
    end_date = options["end_date"]
    sep = separator(options["separator"])
    list_datasets = flags["d"]
    list_urls = flags["u"]
    list_filenames = flags["f"]

    if (
        start_date
        and start_date not in ("first", "today")
        and not re_ymd.match(start_date)
    ):
        grass.fatal(
            _("{start_date}: Invalid <start_date>").format(start_date=start_date)
        )

    if end_date and end_date not in ("first", "today") and not re_ymd.match(end_date):
        grass.fatal(_("{end_date}: Invalid <end_date>").format(end_date=end_date))

    if list_datasets:
        show_datasets(sep)
        return

    datasets = []
    for ds in dataset:
        if ds in supported_datasets:
            if ds not in datasets:
                datasets.append(ds)
        else:
            not_supported = True
            if re_index.match(ds):
                i = int(ds)
                if i >= 0 and i < len(supported_datasets):
                    ds = supported_datasets[i]
                    if ds not in datasets:
                        datasets.append(ds)
                    not_supported = False
            if not_supported:
                grass.fatal(_("{dataset}: Dataset not supported").format(dataset=ds))

    if list_urls:
        action = "list_urls"
    elif list_filenames:
        action = "list_filenames"
    else:
        action = "download"

    retrieve_data(datasets, start_date, end_date, sep, action)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
