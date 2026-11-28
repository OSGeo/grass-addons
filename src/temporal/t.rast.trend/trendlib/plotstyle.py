############################################################################
#
# MODULE:       t.rast.trend / trendlib (library)
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Plot helpers shared by the t.rast.trend tools: the style=
#               option and the vlines=/vlines_labels= options.
#
# COPYRIGHT:    (c) 2026 Paulo van Breugel and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""Plot helpers shared by t.rast.stl, t.rast.stl2ca and t.rast.breakpoint.

pd/plt are set by each driver script's lazy_import_py_modules() -- after
GRASS parses the command line -- rather than imported here, so a plain
module scan (--help, g.extension) never needs pandas/matplotlib installed.
"""

import os

import grass.script as gs

if not callable(globals().get("_")):
    from gettext import gettext as _

# Set by the driver script's lazy_import_py_modules() before any function
# below runs.
pd = None
plt = None


def apply_style(style):
    """Apply a Matplotlib style sheet: either a built-in style name, or the
    path to a custom .mplstyle file (e.g. to set 'axes.linewidth' thinner
    than any built-in style does).

    :param str style: name of a built-in Matplotlib style, or a path to a
        custom style file
    """
    if not style:
        return
    if style not in plt.style.available and not os.path.isfile(style):
        gs.fatal(
            _(
                "'{}' is neither a built-in style ({}) nor an existing "
                "file. A custom style is given as the path to a "
                ".mplstyle file."
            ).format(style, ", ".join(plt.style.available))
        )
    plt.style.use(style)


def parse_vlines(vlines_opt, labels_opt, temporal_type):
    """Parse the vlines/vlines_labels options into plot-ready positions.

    :param str vlines_opt: comma separated dates (absolute time) or integer
        time steps (relative time); may be empty
    :param str labels_opt: comma separated labels, in the same order and
        count as vlines_opt; may be empty (no labels)
    :param str temporal_type: 'absolute' or 'relative'
    :return list: list of (position, label|None) tuples, position being a
        pandas.Timestamp (absolute) or int (relative)
    """
    if not vlines_opt:
        return []
    raw_values = [v.strip() for v in vlines_opt.split(",") if v.strip()]
    positions = []
    for value in raw_values:
        if temporal_type == "relative":
            try:
                positions.append(int(value))
            except ValueError:
                gs.fatal(
                    _(
                        "Could not parse 'vlines' value '{}' as an integer time step."
                    ).format(value)
                )
        else:
            try:
                positions.append(pd.to_datetime(value))
            except (ValueError, TypeError):
                gs.fatal(
                    _("Could not parse 'vlines' value '{}' as a date.").format(value)
                )

    labels = [label.strip() for label in labels_opt.split(",")] if labels_opt else []
    if labels and len(labels) != len(positions):
        gs.fatal(
            _(
                "'vlines_labels' must have the same number of values as "
                "'vlines' ({labels} vs {vlines})."
            ).format(labels=len(labels), vlines=len(positions))
        )
    if not labels:
        labels = [None] * len(positions)
    return list(zip(positions, labels))


def check_plot_numbers(options):
    """Fail early when a plot size option is zero or negative.

    Checks 'dpi', 'fontsize' and 'line_width', those of them that the tool
    has and that are set.

    :param dict options: parsed module options
    """
    for key in ("dpi", "fontsize", "line_width"):
        if options.get(key) and float(options[key]) <= 0:
            gs.fatal(_("'{}' must be a positive number.").format(key))


def parse_plot_dimensions(value):
    """Parse the plot_dimensions= option.

    :param str value: the option value, 'width,height' in inches, or empty
    :return list|None: [width, height], or None when value is empty
    """
    if not value:
        return None
    try:
        dimensions = [float(v) for v in value.split(",")]
    except ValueError:
        dimensions = []
    if len(dimensions) != 2 or min(dimensions) <= 0:
        gs.fatal(_("'plot_dimensions' must be two positive numbers: width,height."))
    return dimensions


def check_output_format(output):
    """Fail early when Matplotlib cannot save to the output file's format.

    Needs Matplotlib, so it runs after the driver's lazy imports.

    :param str output: the output= option value (a file name)
    """
    from matplotlib.backend_bases import FigureCanvasBase

    supported = FigureCanvasBase.get_supported_filetypes()
    extension = os.path.splitext(output)[1].lstrip(".").lower()
    if extension not in supported:
        gs.fatal(
            _(
                "Cannot save the plot as '{f}': the file extension must be one of {e}."
            ).format(f=output, e=", ".join(sorted(supported)))
        )
