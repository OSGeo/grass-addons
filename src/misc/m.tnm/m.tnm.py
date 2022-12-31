#!/usr/bin/env python3
############################################################################
#
# MODULE:       m.tnm
# AUTHOR(S):    Huidae Cho <grass4u gmail.com>
# PURPOSE:      Downloads data for specified polygon codes from The National
#               Map (TNM).
#
# COPYRIGHT:    (C) 2022 by Huidae Cho and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# %module
# % description: Downloads data for specified polygon codes from The National Map (TNM).
# % keyword: USGS
# % keyword: The National Map
# % keyword: TNM
# %end
# %option
# % key: dataset
# % type: string
# % description: Dataset index, ID, or tag
# % multiple: yes
# %end
# %option
# % key: type
# % type: string
# % description: Polygon type
# % options: state,huc2,huc4,huc8
# % answer: state
# %end
# %option
# % key: code
# % type: string
# % description: Polygon code (state name, USPS code, FIPS code, or HUC number)
# % multiple: yes
# %end
# %option
# % key: date_type
# % type: string
# % description: Date type for search
# % options: created,updated,published
# % answer: published
# %end
# %option
# % key: start_date
# % type: string
# % description: Start date for search in YYYY-MM-DD
# %end
# %option
# % key: end_date
# % type: string
# % description: End date for search in YYYY-MM-DD
# %end
# %option G_OPT_F_SEP
# %end
# %flag
# % key: d
# % label: List supported datasets and exit
# %end
# %flag
# % key: s
# % label: List supported states and exit
# %end
# %flag
# % key: f
# % label: List filenames only without downloading
# %end
# %rules
# % collective: dataset, code
# % collective: start_date, end_date
# % required: dataset, -d, -s
# %end

import sys
import os
import requests
import grass.script as grass
from grass.script.utils import separator

# v.db.select map=tl_2022_us_state col=statefp,stusps,name
#   where="1 order by statefp" format=json |
#   sed 's/STATEFP/fips/; s/STUSPS/usps/; s/NAME/name/'
states = [
    {"fips": "01", "usps": "AL", "name": "Alabama"},
    {"fips": "02", "usps": "AK", "name": "Alaska"},
    {"fips": "04", "usps": "AZ", "name": "Arizona"},
    {"fips": "05", "usps": "AR", "name": "Arkansas"},
    {"fips": "06", "usps": "CA", "name": "California"},
    {"fips": "08", "usps": "CO", "name": "Colorado"},
    {"fips": "09", "usps": "CT", "name": "Connecticut"},
    {"fips": "10", "usps": "DE", "name": "Delaware"},
    {"fips": "11", "usps": "DC", "name": "District of Columbia"},
    {"fips": "12", "usps": "FL", "name": "Florida"},
    {"fips": "13", "usps": "GA", "name": "Georgia"},
    {"fips": "15", "usps": "HI", "name": "Hawaii"},
    {"fips": "16", "usps": "ID", "name": "Idaho"},
    {"fips": "17", "usps": "IL", "name": "Illinois"},
    {"fips": "18", "usps": "IN", "name": "Indiana"},
    {"fips": "19", "usps": "IA", "name": "Iowa"},
    {"fips": "20", "usps": "KS", "name": "Kansas"},
    {"fips": "21", "usps": "KY", "name": "Kentucky"},
    {"fips": "22", "usps": "LA", "name": "Louisiana"},
    {"fips": "23", "usps": "ME", "name": "Maine"},
    {"fips": "24", "usps": "MD", "name": "Maryland"},
    {"fips": "25", "usps": "MA", "name": "Massachusetts"},
    {"fips": "26", "usps": "MI", "name": "Michigan"},
    {"fips": "27", "usps": "MN", "name": "Minnesota"},
    {"fips": "28", "usps": "MS", "name": "Mississippi"},
    {"fips": "29", "usps": "MO", "name": "Missouri"},
    {"fips": "30", "usps": "MT", "name": "Montana"},
    {"fips": "31", "usps": "NE", "name": "Nebraska"},
    {"fips": "32", "usps": "NV", "name": "Nevada"},
    {"fips": "33", "usps": "NH", "name": "New Hampshire"},
    {"fips": "34", "usps": "NJ", "name": "New Jersey"},
    {"fips": "35", "usps": "NM", "name": "New Mexico"},
    {"fips": "36", "usps": "NY", "name": "New York"},
    {"fips": "37", "usps": "NC", "name": "North Carolina"},
    {"fips": "38", "usps": "ND", "name": "North Dakota"},
    {"fips": "39", "usps": "OH", "name": "Ohio"},
    {"fips": "40", "usps": "OK", "name": "Oklahoma"},
    {"fips": "41", "usps": "OR", "name": "Oregon"},
    {"fips": "42", "usps": "PA", "name": "Pennsylvania"},
    {"fips": "44", "usps": "RI", "name": "Rhode Island"},
    {"fips": "45", "usps": "SC", "name": "South Carolina"},
    {"fips": "46", "usps": "SD", "name": "South Dakota"},
    {"fips": "47", "usps": "TN", "name": "Tennessee"},
    {"fips": "48", "usps": "TX", "name": "Texas"},
    {"fips": "49", "usps": "UT", "name": "Utah"},
    {"fips": "50", "usps": "VT", "name": "Vermont"},
    {"fips": "51", "usps": "VA", "name": "Virginia"},
    {"fips": "53", "usps": "WA", "name": "Washington"},
    {"fips": "54", "usps": "WV", "name": "West Virginia"},
    {"fips": "55", "usps": "WI", "name": "Wisconsin"},
    {"fips": "56", "usps": "WY", "name": "Wyoming"},
    {"fips": "60", "usps": "AS", "name": "American Samoa"},
    {"fips": "66", "usps": "GU", "name": "Guam"},
    {
        "fips": "69",
        "usps": "MP",
        "name": "Commonwealth of the Northern Mariana Islands",
    },
    {"fips": "72", "usps": "PR", "name": "Puerto Rico"},
    {"fips": "78", "usps": "VI", "name": "United States Virgin Islands"},
]

api_url = "https://tnmaccess.nationalmap.gov/api/v1"
datasets_url = f"{api_url}/datasets"
products_url = (
    f"{api_url}/products?"
    + "datasets={datasets}&polyType={polyType}&polyCode={polyCode}&"
    + "offset={offset}"
)


def show_datasets(fs):
    datasets = query_datasets()
    print(f"INDEX{fs}ID{fs}TAG")
    for i in range(len(datasets)):
        dataset = datasets[i]
        print(f"{i}{fs}{dataset['id']}{fs}{dataset['sbDatasetTag']}")


def show_states(fs):
    print(f"FIPS{fs}USPS{fs}NAME")
    for state in states:
        print(f"{state['fips']}{fs}{state['usps']}{fs}{state['name']}")


def query_datasets():
    url = datasets_url
    res = requests.get(url)
    if res.status_code != 200:
        grass.fatal(_("Failed to fetch dataset metadata"))
    ret = res.json()

    datasets = []
    for item in ret:
        datasets.append({"id": item["id"], "sbDatasetTag": item["sbDatasetTag"]})
        for tag in item["tags"]:
            datasets.append({"id": tag["id"], "sbDatasetTag": tag["sbDatasetTag"]})

    if not datasets:
        grass.fatal(_("Failed to fetch dataset metadata"))
    return datasets


def download_file(item, code):
    url = item["downloadURL"]
    size = item["sizeInBytes"]
    name = code["name"]
    res = requests.get(url, stream=True)
    if res.status_code != 200:
        grass.warning(
            _("Failed to download %s with status code %d") % (name, res.status_code)
        )
        return

    filename = url.split("/")[-1]
    if os.path.exists(filename) and not grass.overwrite():
        file_size = os.path.getsize(filename)
        if file_size == size:
            grass.message(_("Skipping existing file %s for %s") % (filename, name))
            return
        grass.warning(
            _("File size (%d) mismatch with metadata (%d)") % (file_size, size)
        )

    grass.message(_("Downloading %s for %s...") % (filename, name))
    with open(filename, "wb") as f:
        for chunk in res.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


def main():
    dataset = options["dataset"].split(",")
    type_ = options["type"]
    code = options["code"].split(",")
    date_type = options["date_type"]
    start_date = options["start_date"]
    end_date = options["end_date"]
    fs = separator(options["separator"])
    list_datasets = flags["d"]
    list_states = flags["s"]
    list_filenames = flags["f"]

    if list_datasets:
        show_datasets(fs)
        return

    if list_states:
        show_states(fs)
        return

    datasets = query_datasets()
    n = len(datasets)
    ids = [d["id"] for d in datasets]
    sbDatasetTags = [d["sbDatasetTag"] for d in datasets]

    sel_datasets = []
    for d in dataset:
        if d in ids:
            i = ids.index(d)
        elif d in sbDatasetTags:
            d = sbDatasetTags.index(d)
        else:
            try:
                i = int(d)
                if i >= n:
                    raise
            except:
                grass.fatal(_("Unsupported dataset: %s") % d)
        sel_datasets.append(sbDatasetTags[i])
    datasets = ",".join(sel_datasets)

    sel_codes = []
    if type_ == "state":
        fips = [s["fips"] for s in states]
        usps = [s["usps"] for s in states]
        name = [s["name"] for s in states]
        for s in code:
            if s in fips:
                i = fips.index(s)
            elif s in usps:
                i = usps.index(s)
            elif s in name:
                i = name.index(s)
            else:
                grass.fatal(_("Invalid state: %s") % s)
            sel_codes.append({"polyCode": fips[i], "name": name[i]})
    else:
        n = int(type_[-1])
        for h in code:
            try:
                x = int(h)
                if len(h) != n:
                    raise
            except:
                grass.fatal(_("Invalid HUC%d: %s") % (n, h))
            sel_codes.append({"polyCode": h, "name": f"{type_.upper()} {h}"})

    if start_date or end_date:
        date_params = "&dateType="
        if date_type == "created":
            date_params += "dateCreated"
        elif date_type == "updated":
            date_params += "lastUpdated"
        else:
            date_params += "Publication"
        if start_date:
            date_params += f"&start={start_date}"
        if end_date:
            date_params += f"&end={end_date}"
    else:
        date_params = ""

    for code in sel_codes:
        offset = 0
        total = None
        filenames = []
        while not total or offset < total:
            if total:
                grass.message(
                    _("Fetching product metadata for %s (offset %d of %d)...")
                    % (code["name"], offset, total)
                )
            else:
                grass.message(
                    _("Fetching product metadata for %s (offset %d)...")
                    % (code["name"], offset)
                )
            url = (
                products_url.format(
                    datasets=datasets,
                    polyType=type_,
                    polyCode=code["polyCode"],
                    offset=offset,
                )
                + date_params
            )
            res = requests.get(url)
            if res.status_code != 200:
                if total:
                    grass.fatal(
                        _("Failed to fetch product metadata for %s (offset %d of %d)")
                        % (code["name"], offset, total)
                    )
                else:
                    grass.fatal(
                        _("Failed to fetch product metadata for %s (offset %d)")
                        % (code["name"], offset)
                    )
            ret = res.json()
            if not total:
                total = ret["total"]
                grass.message(_("Number of files to download: %d") % total)

            items = ret["items"]
            for item in items:
                if list_filenames:
                    filenames.append(item["downloadURL"].split("/")[-1])
                else:
                    download_file(item, code)
            offset += len(items)
        if filenames:
            print(fs.join(filenames))


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
