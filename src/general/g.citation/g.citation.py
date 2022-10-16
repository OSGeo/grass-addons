#!/usr/bin/env python

############################################################################
#
# MODULE:       g.citation
#
# AUTHOR(S):    Vaclav Petras <wenzeslaus AT gmail DOT com> (ORCID: 0000-0001-5566-9236)
#               Peter Loewe <ploewe AT osgeo DOT org> (ORCID: 0000-0003-2257-0517)
#               Markus Neteler <neteler AT osgeo DOT org> (ORCID: 0000-0003-1916-1966)
#
# PURPOSE:      Provide scientific citation for GRASS modules and add-ons.
#
# COPYRIGHT:    (C) 2018 by Vaclav Petras and the GRASS Development team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Provide scientific citation for GRASS modules and add-ons.
# % keyword: general
# % keyword: metadata
# % keyword: citation
# %end

# %option
# % key: module
# % type: string
# % description: GRASS GIS module to be cited
# % multiple: no
# %end

# %option
# % key: format
# % type: string
# % description: Citation format or style
# % options: bibtex,cff,json,pretty-json,csl-json,citeproc,chicago-footnote,dict,plain
# % descriptions: bibtex;BibTeX;cff;Citation File Format;json;JSON;pretty-json;Pretty printed JSON;csl-json;Citation Style Language JSON (citeproc JSON) format;citeproc;Use the citeproc-py library to create the citation (CSL);chicago-footnote;Chicago style for footnotes;dict;Pretty printed Python dictionary;plain;Plain text
# % answer: bibtex
# % required: yes
# %end

# %option
# % key: style
# % type: string
# % description: Citation style for the citeproc formatter (CSL)
# % answer: harvard1
# %end

# %option
# % key: vertical_separator
# % type: string
# % label: Separator of individual citation records
# % description: Inserted before each item
# %end

# %option G_OPT_F_INPUT
# % key: output
# % type: string
# % description: Path of the output file
# % required: no
# %end

# %flag
# % key: a
# % description: Provide citations for all modules
# %end

# %flag
# % key: d
# % label: Add GRASS GIS as dependency to citation
# % description: Add GRASS GIS as dependency, reference, or additional citation to the citation of a module if applicable for the format (currently only CFF)
# %end

# %flag
# % key: s
# % description: Skip errors, provide warning only
# %end

# %rules
# % required: module,-a
# % exclusive: module,-a
# %end

# TODO: if output is provided, write to ascii file
# (otherwise print to command line)
# TODO: Find lhmpom-equivalent in GRASS repository

# x=$(wget -0 - 'http:/foo/g.region.html')

# Which GRASS version is currently used ?
# What Libraries, etc ?
# g.version -erg

from __future__ import print_function

import html
import sys
import os
import re
from collections import defaultdict
import json
from pathlib import Path
from datetime import datetime
from pprint import pprint

import grass.script as gs


def remove_empty_values_from_dict(d):
    """Removes empty entries from a nested dictionary

    Iterates and recurses over instances of dict or list and removes
    all empty entries. The emptiness is evaluated by conversion to bool
    in an if-statement. Values which are instances of bool are passed
    as is.

    Note that plain dict and list are returned, not the original types.
    What is not an instance of instances of dict or list is left
    untouched.
    """
    if isinstance(d, dict):
        return {
            k: remove_empty_values_from_dict(v)
            for k, v in d.items()
            if v or isinstance(v, bool)
        }
    elif isinstance(d, list):
        return [remove_empty_values_from_dict(i) for i in d if i or isinstance(v, bool)]
    else:
        return d


# TODO: copied from g.manual, possibly move to library
# (lib has also online ones)
def documentation_filename(entry):
    """Get the local path of HTML documentation

    Calls fatal when page is not found.
    """
    gisbase = os.environ["GISBASE"]
    path = os.path.join(gisbase, "docs", "html", entry + ".html")
    if not os.path.exists(path) and os.getenv("GRASS_ADDON_BASE"):
        path = os.path.join(
            os.getenv("GRASS_ADDON_BASE"), "docs", "html", entry + ".html"
        )

    if not os.path.exists(path):
        raise RuntimeError(_("No HTML manual page entry for '%s'") % entry)

    return path


def remove_non_author_lines(lines):
    """Remove lines which appear in the authors sec but are not authors

    >>> remove_non_author_lines(["Ann Doe", "&copy; 2012", "John Doe"])
    ['Ann Doe', 'John Doe']
    """
    out = []
    for line in lines:
        if "&copy;" in line:
            pass
        else:
            out.append(line)
    return out


def remove_html_tags(lines):
    out = []
    for line in lines:
        line = re.sub("<br.?>", "", line)
        line = re.sub("</?[a-z]+ ?[^>]*>", "", line)
        out.append(line)
    return out


def clean_line_item(text):
    """Clean (commas and spaces) from beginning and end of a text

    >>> print(clean_line_item(",Small University, "))
    Small University
    """
    text = text.strip()
    text = re.sub(r"^, *", "", text)
    text = re.sub(r",$", "", text)
    return text


def get_datetime_from_documentation(text):
    """Extract time of latest change from manual
    >>> text = "  Latest change: Monday Jun 28 11:54:09 2021 in commit: 1cfc0af029a35a5d6c7dae5ca7204d0eb85dbc55"
    >>> get_datetime_from_documentation(text)
    datetime.datetime(2022, 9, 18, 23, 55, 9)
    """
    date_format = "%A %b %d %H:%M:%S %Y"
    datetime_capture = r"^  (Latest change: )(.*)( in commit: ).*"
    match = re.search(datetime_capture, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not match:
        datetime_capture = r"^  (Accessed: )([a-z]{6,9} [a-z]{3} [0-9]{1,2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}).*"
        match = re.search(
            datetime_capture, text, re.MULTILINE | re.DOTALL | re.IGNORECASE
        )
    try:
        return datetime.strptime(match.group(2).replace("  ", " "), date_format)
    except ValueError:
        # TODO: raise or fatal? should be in library or module?
        raise RuntimeError(
            "Cannot extract the time of the latest change from the manual."
            "The respective entry does now seem to follow the expected standard."
        )


def get_email(text):
    """Get email from text

    Returns tuple (email, text_without_email)
    Returns (None, text) if not found.
    Any whitespace is stripped from the text.

    >>> print(get_email("<E. Jorge Tizado (ej.tizado@unileon.es)")[0])
    ej.tizado@unileon.es
    >>> print(get_email("<E. Jorge Tizado   (ej.tizado unileon es)")[0])
    ej.tizado@unileon.es
    >>> email, text = get_email("Andrea Aime (aaime libero it)")
    >>> print(text)
    Andrea Aime
    >>> print(email)
    aaime@libero.it
    >>> email, text = get_email("Maris Nartiss (maris.nartiss gmail.com)")
    >>> print(text)
    Maris Nartiss
    """
    email = None
    # ORCID as text
    email_re = re.compile(r"\(([^@]+@[^@]+\.[^@]+)\)", re.IGNORECASE)
    match = re.search(email_re, text)
    if match:
        email = match.group(1)
    else:
        for domain in ["com", "es", "it"]:
            email_re = re.compile(
                r"\(([^ ]+) ([^ ]+) ({})\)".format(domain), re.IGNORECASE
            )
            match = re.search(email_re, text)
            if match:
                email = "{name}@{service}.{domain}".format(
                    name=match.group(1), service=match.group(2), domain=match.group(3)
                )
                break
    text = re.sub(email_re, "", text).strip()
    return (email, text)


def get_orcid(text):
    """Get ORCID from text

    Returns tuple (orcid, text_without_orcid)
    Returns (None, text) if not found.
    Any whitespace is stripped from the text.

    >>> # URL style
    >>> print(get_orcid("http://orcid.org/0000-0000-0000-0000")[0])
    0000-0000-0000-0000
    >>> # ISBN style
    >>> print(get_orcid("ORCID 0000-0000-0000-0000")[0])
    0000-0000-0000-0000
    >>> # URI style
    >>> print(get_orcid("orcid:0000-0000-0000-0000")[0])
    0000-0000-0000-0000
    >>> # no ORCID
    >>> print(get_orcid("orcid: No ORCID here, no here: orcid.org.")[0])
    None
    """
    orcid = None
    # ORCID as text
    orcid_re = re.compile(r"\(?ORCID:? ?([0-9-]+)\)?", re.IGNORECASE)
    match = re.search(orcid_re, text)
    if match:
        orcid = match.group(1)
    else:
        # ORCID as URL
        orcid_re = re.compile(r"https?://orcid.org/([0-9-]+)", re.IGNORECASE)
        match = re.search(orcid_re, text)
        if match:
            orcid = match.group(1)
    text = re.sub(orcid_re, "", text).strip()
    return (orcid, text)


def get_authors_from_documentation(text):
    r"""Extract authors and associated info from documentation
    >>> text = '<h2><a name="author">AUTHOR</a></h2>\nPaul Kelly\n<br><h2>SOURCE CODE</h2>'
    >>> authors = get_authors_from_documentation(text)
    >>> print(authors[0]['name'])
    Paul Kelly
    """
    # Some section names are singular, some plural.
    # Additional tags can appear in the heading compiled documentation.
    # TODO: ...or attributes
    # HTML tags or section name can theoretically be different case.
    # The "last changed" part might be missing.
    # The i and em could be exchanged.
    author_section_capture = r"(<h2>.*AUTHOR.*</h2>)(.*)(<h2>.*SOURCE CODE.*</h2>)"
    match = re.search(
        author_section_capture, text, re.MULTILINE | re.DOTALL | re.IGNORECASE
    )

    if match:
        author_section = match.group(2)
    else:
        raise RuntimeError(_("Unable to find Authors section"))

    raw_author_lines = [
        line.strip()
        for line in author_section.strip()
        .replace("\n", " ")
        .replace("<p>", "<br>")
        .split("<br>")
        if line.strip()
    ]

    raw_author_lines = remove_non_author_lines(raw_author_lines)
    raw_author_lines = remove_html_tags(raw_author_lines)

    authors = []
    feature_heading = None
    for line in raw_author_lines:
        line = html.unescape(line.strip())  # strip after HTML tag strip
        if not line:
            continue
        institute = None
        feature = None

        if line.endswith(":"):
            feature_heading = line[:-1]
            continue

        email, text = get_email(text)
        orcid, text = get_orcid(text)
        ai = line.split(",", 1)
        name = clean_line_item(ai[0])
        if not email:
            email, name = get_email(name)
        if len(ai) == 2:
            institute = clean_line_item(ai[1])
        if " by " in name:
            feature, name = name.split(" by ", 1)
        elif ": " in name:
            feature, name = name.split(": ", 1)
        elif feature_heading:
            feature = feature_heading
        # assuming that names with "and" won't be at the same
        # line/record with author unique info like email or orcid
        if " and " in name:
            names = name.split(" and ", 1)
        elif " &amp; " in name:
            names = name.split(" &amp; ", 1)
        elif " & " in name:
            names = name.split(" & ", 1)
        else:
            names = [name]
        for name in names:
            # drop academic titles from name
            for title in ["Dr. ", "Prof. "]:
                if name.startswith(title):
                    name = name[len(title) :]
            authors.append(
                {
                    "name": name,
                    "institute": institute,
                    "feature": feature,
                    "email": email,
                    "orcid": orcid,
                }
            )
        # TODO: handle unknown/Unknown author
    return authors


def get_code_urls_from_documentation(text):
    """Extract URLs from text containing links to module source code

    Returns a tuple with URL of the source code and URL of history of
    the source code.

    >>> text = '<h2>SOURCE CODE</h2><a href="http://osgeo.org/r.spread">r.spread source code</a> (<a href="http://osgeo.org/log/r.spread">history</a>)'
    >>> get_code_urls_from_documentation(text)
    ('http://osgeo.org/r.spread', 'http://osgeo.org/log/r.spread')
    """
    capture = r'<h2>SOURCE CODE</h2>.*<a href="(.+)">[^<]*source code</a>\s+\(<a href="(.+)">history</a>\)'
    match = re.search(capture, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    else:
        # TODO: raise or fatal? should be in library or module?
        raise RuntimeError("The text does not contain source code URLs")


def remove_dots_from_module_name(name):
    # TODO: make this an option or perhaps a flag to replace with nothing
    # is sufficient to cover most needs
    return name.replace(".", "_")


def internal_to_csl_json(citation):
    """Returns the JSON structure as objects (not as one string)"""
    authors = []
    for author in citation["authors"]:
        name = author_name_to_cff(author["name"])
        authors.append({"family": name["family"], "given": name["given"]})
    return {
        "id": citation["module"],
        "issued": {"date-parts": [[citation["year"], "1", "1"]]},
        "title": "GRASS GIS: " + citation["module"] + " module",
        "type": "software",
        "author": authors,
    }


try:
    # can't be inside the function
    # (import * is not allowed in function)
    # but needed to make citeproc give results
    from citeproc.py2compat import *
except ImportError:
    pass


def print_using_citeproc(csl_json, keys, style):

    from citeproc import CitationStylesStyle, CitationStylesBibliography
    from citeproc import Citation, CitationItem
    from citeproc import formatter
    from citeproc.source.json import CiteProcJSON

    def warn(citation_item):
        raise RuntimeError(
            "Reference with key '{}' not found".format(citation_item.key)
        )

    bib_source = CiteProcJSON([csl_json])
    bib_style = CitationStylesStyle(style, validate=False)
    bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)
    citations = []
    # the following lines just do whatever example in citeproc repo does
    for key in keys:
        citation = Citation([CitationItem(key)])
        bibliography.register(citation)
        citations.append(citation)
    for citation in citations:
        # unused = bibliography.cite(citation, warn_missing_key)
        unused = bibliography.cite(citation, warn)
    for item in bibliography.bibliography():
        print(str(item))


# TODO: Jr. separated by comma
def author_name_to_cff(text):
    """

    Currently, we mostly intend this code to help getting legacy records
    from GRASS manual pages to a parseable format, so we really need to
    address only the national naming styles common for GRASS in 80s-10s.
    This practically means American (US) names and couple other styles.

    >>> d = author_name_to_cff("Richard G. Lathrop Jr.")
    >>> print(d['given'])
    Richard G.
    >>> print(d['family'])
    Lathrop
    >>> print(d['suffix'])
    Jr.
    >>> d = author_name_to_cff("Margherita Di Leo")
    >>> print(d['given'])
    Margherita
    >>> print(d['family'])
    Di Leo
    """
    particles = ["von", "van", "der", "di", "de"]
    suffixes = ["jr", "jnr", "sr", "snr", "junior", "senior"]
    roman = "IVX"  # if you are 40th, we will fix it for you

    def is_suffix(text):
        text = text.lower()
        for suffix in suffixes:
            if text == suffix:
                return True
            elif len(suffix) <= 3 and text == suffix + ".":
                return True
        if text.isupper():
            bool([char for char in text if char in roman])
        return False

    def is_middle_initial(text):
        if text.isupper():
            if len(text) == 2 and text.endswith("."):
                return True
            elif len(text) == 1:
                return True
        return False

    names = text.split(" ")
    # given and family required by CFF 1.0.3
    particle = None
    suffix = None
    if len(names) == 2:
        given = names[0]
        family = names[1]
    elif len(names) == 3:
        if is_middle_initial(names[1]):
            given = " ".join([names[0], names[1]])
            family = names[2]
        elif names[1] in particles:
            given = names[0]
            particle = names[1]
            family = names[2]
        elif names[1][0].isupper() and names[1].lower() in particles:
            # If particle starts with capital, it is often considered
            # to be part of family name.
            given = names[0]
            family = " ".join([names[1], names[2]])
        else:
            # TODO: since this is for legacy code, we could just
            # hardcode the "known" authors such as Maria Antonia Brovelli
            raise NotImplementedError(
                "Not sure if <{n}> is family or middle name in <{t}>".format(
                    n=names[1], t=text
                )
            )
    elif len(names) == 4:
        # assuming that if you have suffix, you have a middle name
        if is_suffix(names[3]):
            given = " ".join([names[0], names[1]])
            family = names[2]
            suffix = names[3]
        else:
            raise NotImplementedError("Not sure how to split <{}>".format(text))
    else:
        raise RuntimeError(_("Cannot split name <{}> correctly".format(text)))
    return {"given": given, "particle": particle, "family": family, "suffix": suffix}


def print_cff(citation):
    """Create Citation File Format file from citation dictionary

    >>> authors = [{'name': 'Joe Doe', 'orcid': '0000-0000-0000-0000'}]
    >>> cit = {'module': 'g.tst', 'authors': authors, 'year': 2011}
    >>> cit.update({'grass-version': '7.4.1'})
    >>> cit.update({'grass-build-date': '2018-06-07'})
    >>> print_cff(cit)
    cff-version: 1.0.3
    message: "If you use this software, please cite it as below."
    authors:
      - family-names: Doe
        given-names: Joe
        orcid: 0000-0000-0000-0000
    title: "GRASS GIS: g.tst module"
    version: 7.4.1
    date-released: 2018-06-07
    license: GPL-2.0-or-later
    """
    print("cff-version: 1.0.3")
    print('message: "If you use this software, please cite it as below."')
    print("authors:")
    for author in citation["authors"]:
        # note: CFF 1.0.3 specifies mandatory family, mandatory given,
        # optional particle (e.g. van), and optional suffix (e.g. III),
        # best shot should be taken for names which don't include family
        # or given or which have different order
        # here we just split based on first space into given and family
        name = author_name_to_cff(author["name"])
        print("  - family-names:", name["family"])
        print("    given-names:", name["given"])
        if author["orcid"]:
            print("    orcid:", author["orcid"])
    print('title: "GRASS GIS: ', citation["module"], ' module"', sep="")
    print("version:", citation["grass-version"])
    # CFF 1.0.3 does not say expplicitely except for Date (so not any
    # string), so assuming YAML timestamp
    # (http://yaml.org/type/timestamp.html)
    # now we have only the year, so using Jan 1
    print("date-released:", citation["grass-build-date"])
    # license string according to https://spdx.org/licenses/
    # we know license of GRASS modules should be GPL>=2
    print("license: GPL-2.0-or-later")
    if citation.get("keywords", None):
        print("keywords:")
        for keyword in citation["keywords"]:
            print("  -", keyword)
    if citation.get("references", None):
        print("references:")
        for reference in citation["references"]:
            # making sure scope, type, and title are first
            if reference.get("scope", None):
                print("  - scope:", reference["scope"])
                print("    type:", reference["type"])
            else:
                print("  - type:", reference["type"])
            print("    title:", reference["title"])
            for key, value in reference.items():
                if key in ["scope", "type", "title"]:
                    continue  # already handled
                # TODO: add general serialization to YAML
                elif key == "authors":
                    print("    authors:")
                    for author in value:
                        # special order for the name of entity
                        if "name" in author:
                            print("      - name: {name}".format(**author))
                        elif "family-names" in author:
                            print(
                                "      - family-names: {family-names}".format(**author)
                            )
                        for akey, avalue in author.items():
                            if akey == "name":
                                continue
                            print("        {akey}: {avalue}".format(**locals()))
                elif key == "keywords":
                    print("    keywords:")
                    for keyword in value:
                        print("      - {keyword}".format(**locals()))
                else:
                    print("    {key}: {value}".format(**locals()))


def print_bibtex(citation):
    """Create BibTeX entry from citation dictionary

    >>> print_bibtex({'module': 'g.tst', 'authors': [{'name': 'Joe Doe'}], 'year': 2011})
    @software{g.tst,
      title = {GRASS GIS: g.tst module},
      author = {Joe Doe},
      year = {2011}
    }
    """
    # TODO: make this an option to allow for software in case it is supported
    entry_type = "misc"
    key = remove_dots_from_module_name(citation["module"])
    print("@", entry_type, "{", key, ",", sep="")

    print("  title = {{", "GRASS GIS: ", citation["module"], " module}},", sep="")

    author_names = [author["name"] for author in citation["authors"]]
    print("  author = {", " and ".join(author_names), "},", sep="")
    print("  howpublished = {", citation["code-url"], "},", sep="")
    print("  year = {", citation["year"], "}", sep="")
    print("  note = {Accessed: ", citation["access"], "},", sep="")
    print("}")


def print_json(citation):
    """Create JSON dump from the citation dictionary"""
    cleaned = remove_empty_values_from_dict(citation)
    # since the format is already compact, let's make it even more
    # compact by omitting the spaces after separators
    print(json.dumps(cleaned, separators=(",", ":")))


def print_pretty_json(citation):
    """Create pretty-printed JSON dump from the citation dictionary"""
    cleaned = remove_empty_values_from_dict(citation)
    # the default separator for list items would leave space at the end
    # of each line, so providing a custom one
    # only small indent needed, so using 2
    # sorting keys because only that can provide consistent output
    print(json.dumps(cleaned, separators=(",", ": "), indent=2, sort_keys=True))


def print_csl_json(citation):
    """Create pretty-printed CSL JSON from the citation dictionary"""
    csl = internal_to_csl_json(citation)
    # the default separator for list items would leave space at the end
    # of each line, so providing a custom one
    # only small indent needed, so using 2
    # sorting keys because only that can provide consistent output
    print(json.dumps(csl, separators=(",", ": "), indent=2, sort_keys=True))


def print_chicago_footnote(citation):
    num_authors = len(citation["authors"])
    authors_text = ""
    for i, author in enumerate(citation["authors"]):
        authors_text += author["name"]
        if i < num_authors - 2:
            authors_text += ", "
        elif i < num_authors - 1:
            # likely with comma but unclear for footnote style
            authors_text += ", and "
    title = "GRASSS GIS module {}".format(citation["module"])
    print(
        "{authors_text}, {title} ({grass-version}), computer software"
        " ({year}).".format(authors_text=authors_text, title=title, **citation)
    )


def print_plain(citation):
    """Create citation from dictionary as plain text

    >>> print_plain({'module': 'g.tst', 'authors': [{'name': 'Joe Doe'}]})
    GRASS GIS module g.tst
    Joe Doe
    """
    print("GRASS GIS module", citation["module"])
    num_authors = len(citation["authors"])
    authors_text = ""
    for i, author in enumerate(citation["authors"]):
        authors_text += author["name"]
        # TODO: not defined if we need institute etc. or not, perhaps
        # use default dict
        if "institute" in author and author["institute"]:
            authors_text += ", {institute}".format(**author)
        if "feature" in author and author["feature"]:
            authors_text += " ({feature})".format(**author)
        if i < num_authors - 1:
            authors_text += "\n"
    print(authors_text)


# private dict for format name to function call
# use print_citation()
_FORMAT_FUNCTION = {
    "bibtex": print_bibtex,
    "cff": print_cff,
    "json": print_json,
    "pretty-json": print_pretty_json,
    "csl-json": print_csl_json,
    "chicago-footnote": print_chicago_footnote,
    "plain": print_plain,
    "dict": lambda d: pprint(dict(d)),  # only plain dict pretty prints
}


def print_citation(citation, format):
    """Create citation from dictionary in a given format"""
    # only catch the specific dict access, don't call the function

    # funs with special handling of parameters first
    # (alternatively all funs can have the most rich unified interface)
    if format == "citeproc":
        print_using_citeproc(
            internal_to_csl_json(citation), [citation["module"]], style="harvard1"
        )
        return
    try:
        function = _FORMAT_FUNCTION[format]
    except KeyError:
        raise RuntimeError(_("Unsupported format or style: %s" % format))
    function(citation)


def grass_cff_reference(grass_version, scope=None):
    """Reference/citation for GRASS GIS based on CFF (close to CFF)

    The parameter grass_version is a g.version dictionary or equivalent.

    Returns dictionary with keys of CFF reference (key).
    """
    citation = {}
    if scope:
        citation["scope"] = scope
    citation["type"] = "software"
    # the team as an entity
    citation["authors"] = [
        {"name": "The GRASS Development Team", "website": "http://grass.osgeo.org/"}
    ]
    citation["title"] = "GRASS GIS {version}".format(**grass_version)
    citation["version"] = grass_version["version"]
    # approximation
    citation["date-released"] = grass_version["build_date"]
    citation["year"] = grass_version["date"]
    citation["keywords"] = [
        "GIS",
        "geospatial analysis",
        "remote sensing",
        "image processing",
    ]
    citation["license"] = "GPL-2.0-or-later"
    return citation


def citation_for_module(name, add_grass=False):
    """Provide dictionary of citation values for a module"""
    path = documentation_filename(name)

    # derive core strings from lhmpom:
    # NAME / AUTHOR / LAST CHANGED / COPYRIGHT: Years + Entity

    text = open(path).read()

    g_version = gs.parse_command("g.version", flags="g")

    # using default empty value, this way we use just if d['k']
    # to check presence and non-emptiness at the same time
    citation = defaultdict(str)
    citation["module"] = name
    citation["grass-version"] = g_version["version"]
    citation["grass-build-date"] = g_version["build_date"]
    citation["authors"] = get_authors_from_documentation(text)
    citation["year"] = get_datetime_from_documentation(text).year
    citation["access"] = get_datetime_from_documentation(text).isoformat()
    code_url, code_history_url = get_code_urls_from_documentation(text)
    citation["code-url"] = code_url
    citation["url-code-history"] = code_history_url

    if add_grass:
        scope = "Use the following to cite the whole GRASS GIS"
        citation["references"] = [grass_cff_reference(g_version, scope=scope)]

    return citation


def get_core_modules():
    # test.r3flow manual is non-standard and breaks 'g.citation -a',
    # so here standard module prefixes are filtered
    # two characters are used, so db and r3 are not matched with a dot
    module_prefixes = ["d.", "db", "g.", "h.", "i.", "m.", "r.", "r3", "t.", "v."]
    # TODO: see what get_commands() does on MS Windows
    modules = sorted(
        [cmd for cmd in gs.get_commands()[0] if cmd[0:2] in module_prefixes]
    )
    return modules


def main(options, flags):
    """Main function to do the module's work

    Using minimal design, just getting the input and calling other
    functions.
    """

    if options["module"]:
        names = options["module"].split(",")
    if flags["a"]:
        names = get_core_modules()
    output_format = options["format"]
    if output_format == "citeproc":
        if not options["style"]:
            gs.fatal(
                _("Option format=citeproc requires also" " the option style to be set")
            )
    vertical_separator = options["vertical_separator"]

    error_count = 0
    for name in names:
        try:
            citation = citation_for_module(name, add_grass=flags["d"])
            if vertical_separator:
                # TODO: decide if we want the newline here or not
                print(vertical_separator)
            print_citation(citation, output_format)
        except RuntimeError as error:
            message = _("Module {name}: {error}".format(**locals()))
            if flags["s"]:
                gs.warning(message)
                error_count += 1
                continue
            else:
                gs.fatal(message)
    if flags["s"] and len(names) > 1:
        gs.warning(_("Errors in parsing {} modules").format(error_count))


# TODO: consider "Extended by" versus original authors

# LASTCHANGED, COPYRIGHT-YEARS, COPRIGHT-ENTITY

# LEFTOVERS:

# A BibTeX entry for LaTeX users is:
#
# @Manual{GRASS_GIS_software,
#  title = {Geographic Resources Analysis Support System (GRASS) Software},
#  author = {{GRASS Development Team}},
#  organization = {Open Source Geospatial Foundation},
#  address = {USA},
#  year = {YEAR},
#  url = {http://grass.osgeo.org},
# }


def doc_test():
    """Tests the module using doctest

    :return: a number of failed tests
    """
    import doctest
    from grass.gunittest.utils import do_doctest_gettext_workaround

    do_doctest_gettext_workaround()
    return doctest.testmod().failed


if __name__ == "__main__":
    if "--doctest" in sys.argv:
        sys.exit(doc_test())
    sys.exit(main(*gs.parser()))
