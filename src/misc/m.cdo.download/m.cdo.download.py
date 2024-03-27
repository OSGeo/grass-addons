#!/usr/bin/env python3
############################################################################
#
# MODULE:       m.cdo.download
# AUTHOR(S):    Huidae Cho <grass4u gmail.com>
# PURPOSE:      Downloads data from NCEI's Climate Data Online (CDO) using
#               their v2 API.
#
# COPYRIGHT:    (C) 2023 by Huidae Cho and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# %module
# % description: Downloads data from NCEI's Climate Data Online (CDO) using their v2 API.
# % keyword: NOAA
# % keyword: NCEI
# % keyword: Climate Data Online
# % keyword: CDO
# %end
# %option
# % key: fetch
# % type: string
# % description: Fetch available metadata or actual data for this specific item
# % options: datasets,datacategories,datatypes,locationcategories,locations,stations,data
# % answer: data
# % required: yes
# %end
# %option
# % key: datasetid
# % type: string
# % description: Dataset ID
# % multiple: yes
# %end
# %option
# % key: datacategoryid
# % type: string
# % description: Data category ID
# % multiple: yes
# %end
# %option
# % key: datatypeid
# % type: string
# % description: Data type ID
# % multiple: yes
# %end
# %option
# % key: locationcategoryid
# % type: string
# % description: Location category ID
# % multiple: yes
# %end
# %option
# % key: locationid
# % type: string
# % description: Location ID
# % multiple: yes
# %end
# %option
# % key: stationid
# % type: string
# % description: Station ID
# % multiple: yes
# %end
# %option
# % key: startdate
# % type: string
# % description: Start date in YYYY-MM-DD or date time in YYYY-MM-DDThh:mm:ss (for data only)
# %end
# %option
# % key: enddate
# % type: string
# % description: End date in YYYY-MM-DD or date time in YYYY-MM-DDThh:mm:ss (for data only)
# %end
# %option G_OPT_M_COORDS
# % key: extent
# % description: Extent in lower-left and upper-right coordinates in degrees
# % multiple: yes
# %end
# %option
# % key: units
# % type: string
# % description: Units for data (raw for no conversion)
# % options: raw,standard,metric
# % answer: metric
# %end
# %option
# % key: includemetadata
# % type: string
# % description: Include metadata when actually fetching data (slower)
# % options: true,false
# % answer: false
# %end
# %option
# % key: sortfield
# % type: string
# % description: Sort field
# % options: id,name,mindate,maxdate,datacoverage
# %end
# %option
# % key: sortorder
# % type: string
# % description: Sort order
# % options: asc,desc
# % answer: asc
# %end
# %option
# % key: limit
# % type: integer
# % description: Max number of results (0 for unlimited; can be > 1000)
# % answer: 0
# %end
# %option
# % key: offset
# % type: integer
# % description: 1-based offset for the first result
# % answer: 1
# %end
# %option
# % key: fields
# % type: string
# % description: Fields to print
# % multiple: yes
# %end
# %option G_OPT_F_SEP
# %end
# %option
# % key: indent
# % type: integer
# % description: Indent for JSON format (-1 for single line per record)
# % answer: 2
# %end
# %option G_OPT_F_OUTPUT
# % required: no
# %end
# %flag
# % key: c
# % label: Do not include column names in output
# %end
# %flag
# % key: j
# % label: Print output in JSON
# %end
# %flag
# % key: u
# % label: Print the request URL and exit
# %end

import sys
import os
import urllib.request
import urllib.error
import json
import grass.script as grass
from grass.script.utils import separator


api_url = "https://www.ncei.noaa.gov/cdo-web/api/v2"
datasets_url = f"{api_url}/datasets"
datacategories_url = f"{api_url}/datacategories"
datatypes_url = f"{api_url}/datatypes"
locationcategories_url = f"{api_url}/locationcategories"
locations_url = f"{api_url}/locations"
stations_url = f"{api_url}/stations"
data_url = f"{api_url}/data"
max_limit = 1000
# CDO API tokens
tokens_env_name = "CDO_API_TOKENS"


def append_url_params(url, params):
    return f"{url}{'&' if '?' in url else '?'}{params}"


def fetch_once(endpoint, offset, limit):
    request_url = append_url_params(
        f"{api_url}/{endpoint}", f"limit={limit}&offset={offset}"
    )

    response = None

    for token in tokens:
        try:
            request = urllib.request.Request(request_url, headers={"token": token})
            with urllib.request.urlopen(request) as f:
                response = json.load(f)
        except:
            continue
        if "message" in response:
            if token != tokens[len(tokens) - 1] and (
                "per day" in response["message"] or "per second" in response["message"]
            ):
                continue
            else:
                raise Exception(response["message"])
        break

    if response is None:
        grass.fatal(_("Failed to fetch data"))

    return response


def fetch_many(endpoint, offset, limit):
    lim = min(limit, max_limit)
    grass.message(_("Fetching %d-%d...") % (offset, offset + lim - 1))
    response = fetch_once(endpoint, offset, lim)

    records = response["results"] if "results" in response else [response]

    if "metadata" in response:
        count = response["metadata"]["resultset"]["count"]

        offset += lim
        limit -= lim

        while offset <= count and offset <= limit:
            lim = min(limit, max_limit)
            grass.message(
                _("Fetching %d-%d of %d...") % (offset, offset + lim - 1, count)
            )
            response = fetch_once(endpoint, offset, lim)

            if "results" not in response:
                response["results"] = []

            for record in response["results"]:
                records.append(record)
            offset += lim
            limit -= lim

    return records


def fetch_all(endpoint, offset=1):
    limit = max_limit

    grass.message(_("Fetching %d-%d...") % (offset, limit))
    response = fetch_once(endpoint, offset, limit)

    records = response["results"] if "results" in response else [response]

    if "metadata" in response:
        count = response["metadata"]["resultset"]["count"]

        offset += limit

        while offset <= count:
            grass.message(
                _("Fetching %d-%d of %d...") % (offset, offset + limit - 1, count)
            )
            response = fetch_once(endpoint, offset, limit)

            if "results" not in response:
                response["results"] = []

            for record in response["results"]:
                records.append(record)
            offset += limit

    return records


def find_keys(records, fields):
    keys = []
    for record in records:
        if fields:
            for key in fields:
                if key not in keys and key in record:
                    keys.append(key)
        else:
            for key in record:
                if key not in keys:
                    keys.append(key)
    return keys


def print_json(outf, records, fields, indent):
    if fields:
        keys = find_keys(records, fields)
        recs = []
        for record in records:
            rec = {}
            for key in keys:
                if key in record:
                    rec[key] = record[key]
            recs.append(rec)
        records = recs

    if indent < 0:
        print("[\n" + ",\n".join(json.dumps(rec) for rec in records) + "\n]", file=outf)
    else:
        print(json.dumps(records, indent=indent), file=outf)


def print_table(outf, records, fields, fs, exclude_colnames):
    if len(records) > 0:
        keys = find_keys(records, fields)
        if not exclude_colnames:
            print(fs.join(keys), file=outf)
        for record in records:
            cols = []
            for key in keys:
                cols.append(record[key] if key in record else "")
            print(fs.join(map(str, cols)), file=outf)


def main():
    global tokens

    if tokens_env_name not in os.environ or not os.environ[tokens_env_name]:
        grass.fatal(
            _(
                "Please define an environment variable %s with CDO API tokens separated by a comma"
            )
            % tokens_env_name
        )
    tokens = os.environ[tokens_env_name].split(",")

    fetch = options["fetch"]
    datasetid = options["datasetid"]
    datacategoryid = options["datacategoryid"]
    datatypeid = options["datatypeid"]
    locationcategoryid = options["locationcategoryid"]
    locationid = options["locationid"]
    stationid = options["stationid"]
    startdate = options["startdate"]
    enddate = options["enddate"]
    extent = options["extent"]
    units = options["units"]
    includemetadata = options["includemetadata"]
    sortfield = options["sortfield"]
    sortorder = options["sortorder"]
    limit = int(options["limit"])
    offset = int(options["offset"])
    fields = options["fields"]
    fields = fields.split(",") if fields else []
    fs = separator(options["separator"])
    indent = int(options["indent"])
    output = options["output"]
    exclude_colnames = flags["c"]
    json_format = flags["j"]
    print_url = flags["u"]

    if datacategoryid and fetch not in (
        "datacategories",
        "datatypes",
        "locations",
        "stations",
    ):
        grass.fatal(
            _(
                "<datacategoryid> supported only for fetching datacategories, datatypes, locations, or stations"
            )
        )

    if datatypeid and fetch not in ("datasets", "datatypes", "stations", "data"):
        grass.fatal(
            _(
                "<datatypeid> supported only for fetching datasets, datatypes, stations, or data"
            )
        )

    if locationcategoryid and fetch not in ("locationcategories", "locations"):
        grass.fatal(
            _(
                "<locationcategoryid> supported only for fetching locationcategories or locations"
            )
        )

    if locationid and fetch not in (
        "datasets",
        "datacategories",
        "datatypes",
        "locations",
        "stations",
        "data",
    ):
        grass.fatal(
            _(
                "<locationid> supported only for fetching datasets, datacategories, datatypes, locations, stations, or data"
            )
        )

    if stationid and fetch not in (
        "datasets",
        "datacategories",
        "datatypes",
        "stations",
        "data",
    ):
        grass.fatal(
            _(
                "<stationid> supported only for fetching datasets, datacategories, datatypes, stations, or data"
            )
        )

    if extent:
        if fetch == "stations":
            extent = extent.split(",")
            if len(extent) != 4:
                grass.fatal(
                    _("<extent> must have lower-left and upper-right coordinates")
                )
        else:
            grass.fatal(_("<extent> supported only for fetching stations"))

    if fetch == "data" and (not datasetid or not startdate or not enddate):
        grass.fatal(
            _("<fetch=data> requires all of <datasetid>, <startdate>, and <enddate>")
        )

    if limit < 0:
        grass.fatal(_("<limit> must be >= 0"))

    if offset <= 0:
        grass.fatal(_("<offset> must be >= 1"))

    if indent < -1:
        grass.fatal(_("<indent> must be >= -1"))

    endpoint = fetch
    if fetch.endswith("ies"):
        itemid = fetch[: len(fetch) - 3] + "yid"
    else:
        itemid = fetch[: len(fetch) - 1] + "id"
    if itemid in options:
        endpoint += f"/{options[itemid]}"

    for key in (
        "datasetid",
        "datacategoryid",
        "datatypeid",
        "locationcategoryid",
        "locationid",
        "stationid",
        "startdate",
        "enddate",
        "extent",
        "units",
        "includemetadata",
        "sortfield",
        "sortorder",
    ):
        if options[key] and (
            key not in ("units", "includemetadata") or fetch == "data"
        ):
            endpoint = append_url_params(endpoint, f"{key}={options[key]}")

    if output in ("", "-", "/dev/stdout"):
        outf = sys.stdout
    else:
        outf = open(output, "w")

    try:
        if print_url:
            if limit > 0:
                endpoint = append_url_params(endpoint, f"limit={limit}")
            if offset > 1:
                endpoint = append_url_params(endpoint, f"offset={offset}")
            url = f"{api_url}/{endpoint}"
            print(url, file=outf)
        else:
            if limit > 0:
                records = fetch_many(endpoint, offset, limit)
            else:
                records = fetch_all(endpoint, offset)

            if json_format:
                print_json(outf, records, fields, indent)
            else:
                print_table(outf, records, fields, fs, exclude_colnames)
    finally:
        if outf is not sys.stdout:
            outf.close()


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
