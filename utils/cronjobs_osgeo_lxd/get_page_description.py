#!/usr/bin/env python

# PURPOSE: Extracts page one line descriptions for index.html of GRASS GIS Addons
#
# AUTHORS: Martin Landa (Bash version)
#          Vaclav Petras (Python version)

import os
import sys
import re


def get_desc_from_manual_page_line(text):
    """
    >>> get_desc_from_manual_page_line("r.example - This is a description<br>")
    'This is a description'
    """
    # this matches the dash at the beginning
    text = text.split(" - ", 1)[1]
    # this matches a tag at the end
    # (supposing no tags in the description and < represented as &lt;
    text = text.split("<", 1)[0]
    return text


def get_desc_from_comment_meta_line(text):
    """
    >>> get_desc_from_comment_meta_line("<!-- meta page description: Abc abc-->")
    'Abc abc'
    """
    text = text.split("<!-- meta page description:", 1)[1]
    text = text.split("-->", 1)[0]
    return text.strip()


def remove_unwanted_tags(text):
    r"""Remove HTML selected tags from text

    This is not an ideal example where the formatting is in fact wrong
    but let's fix it and use it so it at least looks good.

    >>> remove_unwanted_tags('module.name<br>\nDescription later')
    'module.name\nDescription later'

    Links to details are not ideal for index page. Links to the same page
    (the ones with #) would be even broken.

    >>> remove_unwanted_tags('uses <a href="http://example.com">Famous</a> lib')  # doctest: +NORMALIZE_WHITESPACE
    'uses Famous lib'

    However we save some links:

    >>> remove_unwanted_tags('abc <br> abc <em>abc</em>')  # doctest: +NORMALIZE_WHITESPACE
    'abc abc <em>abc</em>'
    """
    # ? is for non-greedy to not go to last tag but end the current first
    # new lines and paragraphs
    text = re.sub(r"<br.?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<p.*?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "", text, flags=re.IGNORECASE)
    # links and other anchors
    text = re.sub(r"<a.*?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</a>", "", text, flags=re.IGNORECASE)
    return text


def get_desc_from_desc_text(text):
    r"""Get description defined as first sentence in the given text.

    Sentence is defined as text which ends with dot and space.
    The string is expected to contain this. The other case not handled.

    >>> get_desc_from_desc_text("Abc abc.abc abc.")
    'Abc abc.abc abc.'
    >>> get_desc_from_desc_text("Abc abc.abc abc. ")
    'Abc abc.abc abc.'
    >>> get_desc_from_desc_text("Abc abc.abc\n abc.\n")
    'Abc abc.abc\n abc.'
    """
    # this matches the sentence but gives also whole string even if it
    # is not the sentence
    text = re.split(r"\.(\s|$)", text, 1)[0]
    text = remove_unwanted_tags(text)
    # strip spaces from the ends and add the stripped dot back
    # TODO: unify the behavior with dot, some modules have it, some don't
    return text.strip() + "."


def main(filename):
    with open(filename) as page_file:
        desc = None
        in_desc_block = False
        in_desc_section = False
        desc_section = ""
        desc_section_num_lines = 0
        # one empty after heading and then a longer sentence over two lines
        desc_section_max_lines = 3
        # we expect h2 level
        desc_block_start = re.compile(r"<h2.*>NAME.*/h.>", flags=re.IGNORECASE)
        # the incomplete manual pages have NAME followed by DESCRIPTION
        desc_block_end = re.compile(
            r"<h2.*>(KEYWORDS|DESCRIPTION).*/h.>", flags=re.IGNORECASE
        )
        desc_section_start = re.compile(r"<h2.*>DESCRIPTION.*/h.>", flags=re.IGNORECASE)
        # desc_section_end = re.compile(r'<h2.*>.*<.*/h.>', flags=re.IGNORECASE)
        desc_section_end = re.compile(r"<h2.*>.*/h.>", flags=re.IGNORECASE)
        desc_line = re.compile(r" - ")
        comment_meta_desc_line = re.compile(r"<!-- meta page description:.*-->")
        for line in page_file:
            line = line.rstrip()  # remove '\n' at end of line
            if desc_block_start.search(line):
                in_desc_block = True
            elif desc_block_end.search(line):
                in_desc_block = False
            if in_desc_block:
                if desc_line.search(line):
                    desc = get_desc_from_manual_page_line(line)
            # if there was nothing in the generated section of the page
            # try find manually added meta comments which are placed
            # at the beginning of the manually edited part of the page
            if not desc and comment_meta_desc_line.search(line):
                desc = get_desc_from_comment_meta_line(line)
            # if there was nothing else, last thing to try is get the first
            # sentence from the description section (which is also last
            # item in the file from all things we are trying
            if in_desc_section and desc_section_end.search(line):
                in_desc_section = False
            # we need to store line after we matched for start
            # and not store the line matched for end
            if in_desc_section:
                desc_section += line + "\n"
                desc_section_num_lines += 1
                if desc_section_num_lines > desc_section_max_lines:
                    in_desc_section = False
            if not desc and desc_section_start.search(line):
                in_desc_section = True
        if not desc and desc_section:
            desc = get_desc_from_desc_text(desc_section)
        if not desc:
            desc = "(incomplete manual page, please fix)"
        # the original script attempted to add also </li> but it as not working
        # now we leave up to the caller as well as whitespace around
        print(desc)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(
            "{name} takes exactly one argument (HTML manual page name)."
            " {argc} parameters were given.".format(
                name=os.path.basename(sys.argv[0]), argc=len(sys.argv) - 1
            )
        )
    sys.exit(main(sys.argv[1]))
