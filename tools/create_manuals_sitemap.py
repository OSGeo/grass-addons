#!/usr/bin/env python3

"""
Created on Thu Nov 19 10:42:17 2020

@author: lucadelu
"""
import os
import argparse
import glob
import xml.etree.cElementTree as ET
from xml.dom import minidom
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description="Create XML sitemap for GRASS GIS manual"
    )
    parser.add_argument(
        "--dir",
        type=str,
        required=True,
        help="The directory containing the HTML GRASS manuals page",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="The main url to GRASS manual, (default: %(default)s)",
        default="https://grass.osgeo.org/grass-stable/manuals/",
    )
    parser.add_argument(
        "--sitemap",
        type=str,
        default="sitemap_manuals.xml",
        help="The sitemap name, (default: %(default)s)",
    )
    parser.add_argument("-o", "--overwrite", dest="overwrite", action="store_true")
    args = parser.parse_args()
    output = os.path.join(args.dir, args.sitemap)
    if os.path.exists(output) and not args.overwrite:
        print(
            "{} already exists. If you want overwrite please use '-o' "
            "parameter".format(output)
        )
        return False
    url = args.url.rstrip("/")
    root = ET.Element("urlset")
    root.attrib["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
    root.attrib[
        "xsi:schemaLocation"
    ] = "http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
    root.attrib["xmlns"] = "http://www.sitemaps.org/schemas/sitemap/0.9"

    htmls = glob.glob1(args.dir, "*.html")
    for html in sorted(htmls):
        htmlstat = os.stat(os.path.join(args.dir, html))
        htmldate = str(datetime.fromtimestamp(htmlstat.st_mtime).date())
        doc = ET.SubElement(root, "url")
        ET.SubElement(doc, "loc").text = "{ur}/{ht}".format(ur=url, ht=html)
        ET.SubElement(doc, "lastmod").text = htmldate
        ET.SubElement(doc, "changefreq").text = "monthly"
        ET.SubElement(doc, "priority").text = "1.0"

    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    with open(output, "w") as f:
        f.write(xmlstr)


if __name__ == "__main__":
    main()
