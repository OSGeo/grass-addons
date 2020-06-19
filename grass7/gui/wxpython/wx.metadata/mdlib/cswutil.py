#!/usr/bin/env python
"""
@module  utility for g.gui.cswbrowser
@brief   GUI csw browser


(C) 2015 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
"""
from gettext import gettext, ngettext
import os
import webbrowser
from xml.dom.minidom import parseString
import xml.etree.ElementTree as etree

from jinja2 import Environment, FileSystemLoader
from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import HtmlFormatter

def get_connections_from_file( filename):
    """load connections from connection file"""

    error = 0
    try:
        doc = etree.parse(filename).getroot()
        if doc.tag != 'qgsCSWConnections':
            error = 1
            msg = 'Invalid CSW connections XML.'
    except etree.ParseError as err:
        error = 1
        msg = ('Cannot parse XML file: %s' % err)
    except IOError as err:
        error = 1
        msg = ('Cannot open file: %s' % err)

    if error == 1:
        return False,msg
    return True,doc


def render_template(language, context, data, template):
    """Renders HTML display of metadata XML"""

    env = Environment(extensions=['jinja2.ext.i18n'],
                      loader=FileSystemLoader(context.confDirPath))
    env.globals.update(zip=zip)

    env.install_gettext_callables(gettext, ngettext, newstyle=True)

    template_file = template
    template = env.get_template(template_file)
    return template.render(language=language, obj=data)


def prettify_xml(xml):
    """convenience function to prettify XML"""
    if xml.count('\n') > 5:  # likely already pretty printed
        return xml
    else:
        # check if it's a GET request
        if xml.startswith('http'):
            return xml
        else:
            return parseString(xml).toprettyxml()


def encodeString(str):
    return str.encode('ascii', 'ignore')


def highlight_xml(context, xml):
    """render XML as highlighted HTML"""

    hformat = HtmlFormatter()
    css = hformat.get_style_defs('.highlight')
    body = highlight(prettify_xml(xml), XmlLexer(), hformat)

    env = Environment(loader=FileSystemLoader(context.confDirPath))

    template_file = 'xml_highlight.html'
    template = env.get_template(template_file)
    return template.render(css=css, body=body)


def renderXML(context, xml):
    hformat = HtmlFormatter()
    body = highlight(prettify_xml(xml), XmlLexer(), hformat)
    env = Environment(loader=FileSystemLoader(context.confDirPath))

    template_file = 'xml_render.html'
    template = env.get_template(template_file)
    return template.render(body=body)


def open_url(url):
    """open URL in web browser"""

    webbrowser.open(url)


def normalize_text(text):
    """tidy up string"""
    return text.replace('\n', '')


def serialize_string(input_string):
    """apply a serial counter to a string"""

    s = input_string.strip().split()

    last_token = s[-1]
    all_other_tokens_as_string = input_string.replace(last_token, '')

    if last_token.isdigit():
        value = '%s%s' % (all_other_tokens_as_string, int(last_token) + 1)
    else:
        value = '%s 1' % input_string

    return value
