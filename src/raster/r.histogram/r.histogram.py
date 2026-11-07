#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.histogram
# AUTHOR:       Paulo van Breugel
# PURPOSE:      Draws a histogram of raster values.
#
# SPDX-FileCopyrightText: 2026 Paulo van Breugel
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
#
#############################################################################

# %module
# % description: Draws a histogram of raster values.
# % keyword: display
# % keyword: raster
# % keyword: plot
# % keyword: histogram
# %end

# %option G_OPT_R_MAP
# % label: Input raster
# % description: Raster map whose non-NULL values are plotted.
# % guisection: Input
# %end

# %option
# % key: bins
# % type: integer
# % label: Number of bins
# % description: Number of equal-width histogram bins.
# % answer: 30
# % required: yes
# % guisection: Input
# %end

# %option
# % key: frequency
# % type: string
# % label: Frequency measure
# % description: Express histogram frequency as cell count or percentage of non-NULL cells.
# % options: count,percent
# % answer: count
# % required: yes
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % label: Name of output image file
# % required: no
# % guisection: Output
# %end

# %option
# % key: plot_dimensions
# % type: string
# % label: Plot dimensions (width,height)
# % description: Dimensions (width,height) of the figure in inches.
# % required: no
# % guisection: Output
# %end

# %option
# % key: fontsize
# % type: integer
# % label: Font size
# % description: Default font size.
# % required: no
# % guisection: Output
# %end

# %option
# % key: dpi
# % type: integer
# % label: DPI
# % description: Resolution of the plot in dots per inch.
# % required: no
# % guisection: Output
# %end

# %option
# % key: style
# % type: string
# % label: Matplotlib style
# % description: Name of a built-in Matplotlib style (see https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html), or the path to a custom .mplstyle file (see https://matplotlib.org/stable/tutorials/introductory/customizing.html#defining-your-own-style).
# % required: no
# % options: Solarize_Light2,_classic_test_patch, _mpl-gallery, _mpl-gallery-nogrid, bmh,classic, dark_background, fast, fivethirtyeight, ggplot, grayscale,petroff10, seaborn-v0_8, seaborn-v0_8-bright,seaborn-v0_8-colorblind, seaborn-v0_8-dark,seaborn-v0_8-dark-palette, seaborn-v0_8-darkgrid, seaborn-v0_8-deep,seaborn-v0_8-muted, seaborn-v0_8-notebook, seaborn-v0_8-paper,seaborn-v0_8-pastel, seaborn-v0_8-poster, seaborn-v0_8-talk,seaborn-v0_8-ticks, seaborn-v0_8-white, seaborn-v0_8-whitegrid,tableau-colorblind10
# % guisection: Plot format
# %end

# %option
# % key: title
# % type: string
# % label: Plot title
# % description: Optional title above the plot.
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: x_label
# % type: string
# % label: X-axis label
# % description: Label of the horizontal axis. Defaults to the raster name or cell count, depending on orientation.
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: y_label
# % type: string
# % label: Y-axis label
# % description: Label of the vertical axis. Defaults to the frequency measure or raster name, depending on orientation.
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: background_color
# % type: string
# % label: Background color
# % description: Color of the figure and plotting area. Use "transparent" for a transparent background.
# % required: no
# % guisection: Plot format
# %end

# %flag
# % key: h
# % label: Horizontal histogram
# % description: Draw the histogram horizontally.
# % guisection: Plot format
# %end

# %flag
# % key: g
# % label: Add grid lines
# % description: Add grid lines along the count axis.
# % guisection: Plot format
# %end

# %option
# % key: rotate_labels
# % type: double
# % options: -90-90
# % label: Rotate labels
# % description: Rotate value-axis labels (degrees).
# % required: no
# % guisection: Plot format
# %end

# %option
# % key: axis_limits
# % type: string
# % label: Limit value axis (min,max)
# % description: Minimum and maximum of the value axis.
# % required: no
# % guisection: Plot format
# %end

# %option G_OPT_CN
# % key: color
# % label: Color of the bars
# % description: Fill color of the histogram bars. Defaults to the style palette. See manual for color notation.
# % required: no
# % answer:
# % guisection: Histogram format
# %end

# %flag
# % key: c
# % label: Raster colors
# % description: Fill bars with the colors of the input raster color table.
# % guisection: Histogram format
# %end

# %option G_OPT_CN
# % key: border_color
# % label: Color of the bar borders
# % description: Color of the histogram bar borders. Defaults to the Matplotlib default.
# % required: no
# % answer:
# % guisection: Histogram format
# %end

# %option
# % key: border_width
# % type: double
# % label: Border line width
# % description: Line width of the bar borders. Defaults to the Matplotlib default.
# % required: no
# % guisection: Histogram format
# %end

# %option
# % key: rwidth
# % type: double
# % label: Relative bar width
# % description: Width of the bars as a fraction of the bin width (0,1].
# % options: 0-1
# % required: no
# % guisection: Histogram format
# %end

import atexit
import os
import sys
from subprocess import PIPE

import grass.script as gs

temporary_rasters = []


def create_temporary_raster(prefix):
    """Create a temporary raster name and register it for cleanup."""
    name = gs.append_node_pid(prefix)
    temporary_rasters.append(name)
    return name


def cleanup():
    """Remove temporary raster maps."""
    mapset = gs.gisenv()["MAPSET"]
    for name in reversed(temporary_rasters):
        found = gs.find_file(name=name, element="raster", mapset=mapset)
        if found["file"]:
            gs.run_command("g.remove", flags="f", type="raster", name=name, quiet=True)


def lazy_import_py_modules(to_file):
    """Import Matplotlib and select a backend suitable for the output."""
    global mpl
    global plt
    try:
        import matplotlib as mpl

        mpl.use("Agg" if to_file else "WXAgg")
        from matplotlib import pyplot as plt
    except ModuleNotFoundError:
        gs.fatal(_("Matplotlib is not installed. Please, install it."))


def apply_style(style):
    """Apply a Matplotlib style sheet: either a built-in style name, or the
    path to a custom .mplstyle file.
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


def strip_mapset(name, join_char="@"):
    """Strip the mapset suffix from a map name."""
    return name.split(join_char)[0] if join_char in name else name


def get_valid_color(color):
    """Return a Matplotlib-compatible color from GRASS color notation."""
    if ":" in color:
        try:
            color = [int(value) / 255 for value in color.split(":")]
        except ValueError:
            gs.fatal(_("{} is not a valid color.").format(color))
    if not mpl.colors.is_color_like(color):
        gs.fatal(_("{} is not a valid color.").format(color))
    return color


def check_region_raster_match(raster):
    """Return whether the current region matches the raster's native grid.

    Both sides are queried through g.region (the current region, and the
    region g.region would set for this raster) and compared.
    """
    keys = ["n", "s", "e", "w", "nsres", "ewres", "rows", "cols"]
    current = gs.parse_command("g.region", flags="up", format="shell")
    native = gs.parse_command("g.region", flags="up", format="shell", raster=raster)
    return all(current[key] == native[key] for key in keys)


def mask_is_active():
    """Return whether a raster MASK is active in the current mapset."""
    mapset = gs.gisenv()["MAPSET"]
    return bool(gs.find_file(name="MASK", element="cell", mapset=mapset)["file"])


def prepare_histogram_raster(raster):
    """Return a floating-point raster suitable for equal-width binning.

    Floating-point category ranges used by r.stats come from the raster's
    stored range. A temporary raster is therefore needed when a mask or a
    different computational region changes the observed range. Integer maps
    are converted because r.stats otherwise reports their categories rather
    than grouping them into the requested number of bins.
    """
    info = gs.raster_info(raster)
    needs_copy = (
        info["datatype"] == "CELL"
        or mask_is_active()
        or not check_region_raster_match(raster)
    )
    if not needs_copy:
        return raster
    temporary = create_temporary_raster("r_histogram")
    gs.mapcalc(f"{temporary} = double({raster})", quiet=True)
    return temporary


def histogram_data(raster, bins):
    """Compute equal-width histogram counts with GRASS raster modules.

    Only the per-bin counts are returned to Python, so memory use does not
    depend on the number of raster cells.

    :param str raster: input raster map
    :param int bins: requested number of bins

    :return tuple: counts, bin edges, and bin centers
    """
    working_raster = prepare_histogram_raster(raster)
    info = gs.raster_info(working_raster)
    minimum = info["min"]
    maximum = info["max"]
    if minimum is None or maximum is None:
        gs.fatal(_("Raster map <{}> contains only NULL cells.").format(raster))

    rows = gs.read_command(
        "r.stats",
        flags="cnr",
        input=working_raster,
        nsteps=bins,
        separator="pipe",
        quiet=True,
    ).splitlines()

    counts = [0] * bins
    for row in rows:
        if not row:
            continue
        raw_index, count = row.split("|", maxsplit=1)
        index = int(raw_index) - 1
        if index < 0 or index >= bins:
            gs.fatal(_("Unexpected histogram bin index <{}>.").format(raw_index))
        counts[index] = int(count)

    total = sum(counts)
    if not total:
        gs.fatal(_("Raster map <{}> contains only NULL cells.").format(raster))

    minimum = float(minimum)
    maximum = float(maximum)
    if minimum == maximum:
        half_width = max(abs(minimum) * 0.01, 0.5)
        return [total], [minimum - half_width, maximum + half_width], [minimum]

    step = (maximum - minimum) / bins
    edges = [minimum + step * index for index in range(bins + 1)]
    centers = [(edges[index] + edges[index + 1]) / 2 for index in range(bins)]
    return counts, edges, centers


def raster_colors(raster, values):
    """Return normalized RGB colors for raster values from its color table."""
    text = "\n".join(format(value, ".17g") for value in values) + "\n"
    process = gs.pipe_command(
        "r.what.color", flags="i", input=raster, stdin=PIPE, stderr=PIPE
    )
    process_input = (
        text if getattr(process.stdin, "encoding", None) else gs.encode(text)
    )
    stdout, stderr = process.communicate(input=process_input)
    stdout = gs.decode(stdout) if isinstance(stdout, bytes) else stdout
    stderr = gs.decode(stderr) if isinstance(stderr, bytes) else stderr
    if process.returncode:
        message = stderr.strip()
        gs.fatal(
            _("Unable to read the color table of raster map <{name}>: {error}").format(
                name=raster, error=message
            )
        )

    rows = stdout.splitlines()
    if len(rows) != len(values):
        gs.fatal(_("The raster color table did not return all requested colors."))

    colors = []
    for row in rows:
        _value, separator, color = row.partition(":")
        if not separator or color.strip() == "*":
            gs.fatal(_("The input raster does not have a usable color table."))
        try:
            channels = [int(channel.strip()) for channel in color.split(":")]
        except ValueError:
            gs.fatal(_("Invalid color table entry <{}>.").format(color.strip()))
        if len(channels) != 3 or any(
            channel < 0 or channel > 255 for channel in channels
        ):
            gs.fatal(_("Invalid color table entry <{}>.").format(color.strip()))
        colors.append([channel / 255 for channel in channels])
    return colors


def parse_dimensions(value):
    """Parse and validate plot dimensions."""
    if not value:
        return [6, 4]
    try:
        dimensions = [float(item) for item in value.split(",")]
    except ValueError:
        gs.fatal(_("Plot dimensions must be two numbers separated by a comma."))
    if len(dimensions) != 2 or any(item <= 0 for item in dimensions):
        gs.fatal(_("Plot dimensions must contain two values larger than zero."))
    return dimensions


def parse_axis_limits(value):
    """Parse and validate optional value-axis limits."""
    if not value:
        return None
    try:
        limits = [float(item) for item in value.split(",")]
    except ValueError:
        gs.fatal(_("Axis limits must be two numbers separated by a comma."))
    if len(limits) != 2 or limits[0] >= limits[1]:
        gs.fatal(_("Axis limits must be two increasing values."))
    return limits


def scale_frequencies(counts, frequency):
    """Return histogram frequencies as counts or percentages."""
    if frequency == "percent":
        total = sum(counts)
        return [100 * count / total for count in counts]
    return counts


def get_background_color(value):
    """Return a background color and whether it is transparent."""
    if not value:
        return None, False
    if value.lower() == "transparent":
        return "none", True
    return get_valid_color(value), False


def draw_histogram(options, flags, counts, edges, centers):
    """Draw and display or save the histogram."""
    horizontal = flags["h"]
    dimensions = parse_dimensions(options["plot_dimensions"])
    axis_limits = parse_axis_limits(options["axis_limits"])

    if options["fontsize"]:
        fontsize = int(options["fontsize"])
        if fontsize <= 0:
            gs.fatal(_("Font size must be larger than zero."))
        plt.rcParams["font.size"] = fontsize

    dpi = float(options["dpi"]) if options["dpi"] else 300
    if dpi <= 0:
        gs.fatal(_("DPI must be larger than zero."))

    relative_width = float(options["rwidth"]) if options["rwidth"] else 1.0
    if relative_width <= 0 or relative_width > 1:
        gs.fatal(_("Relative bar width must be larger than 0 and at most 1."))

    if flags["c"]:
        colors = raster_colors(options["map"], centers)
    elif options["color"]:
        colors = get_valid_color(options["color"])
    else:
        colors = None

    bar_kwargs = {}
    if colors is not None:
        bar_kwargs["color"] = colors
    if options["border_color"]:
        bar_kwargs["edgecolor"] = get_valid_color(options["border_color"])
    if options["border_width"]:
        border_width = float(options["border_width"])
        if border_width < 0:
            gs.fatal(_("Border width cannot be negative."))
        bar_kwargs["linewidth"] = border_width

    widths = [edges[index + 1] - edges[index] for index in range(len(counts))]
    bar_sizes = [width * relative_width for width in widths]
    positions = [
        edge + (width - size) / 2
        for edge, width, size in zip(edges[:-1], widths, bar_sizes)
    ]
    frequencies = scale_frequencies(counts, options["frequency"])
    frequency_label = (
        _("Percentage of cells (%)")
        if options["frequency"] == "percent"
        else _("Cell count")
    )

    background_color, transparent = get_background_color(options["background_color"])
    figure, axis = plt.subplots(figsize=dimensions)
    if background_color is not None:
        figure.patch.set_facecolor(background_color)
        axis.set_facecolor(background_color)
    if horizontal:
        axis.barh(positions, frequencies, height=bar_sizes, align="edge", **bar_kwargs)
        axis.set_xlabel(options["x_label"] or frequency_label)
        axis.set_ylabel(options["y_label"] or strip_mapset(options["map"]))
        if axis_limits:
            axis.set_ylim(axis_limits)
        if flags["g"]:
            axis.xaxis.grid(True, alpha=0.5)
    else:
        axis.bar(positions, frequencies, width=bar_sizes, align="edge", **bar_kwargs)
        axis.set_xlabel(options["x_label"] or strip_mapset(options["map"]))
        axis.set_ylabel(options["y_label"] or frequency_label)
        if axis_limits:
            axis.set_xlim(axis_limits)
        if flags["g"]:
            axis.yaxis.grid(True, alpha=0.5)

    if options["rotate_labels"]:
        axis.tick_params(
            axis="y" if horizontal else "x",
            labelrotation=float(options["rotate_labels"]),
        )
    if options["title"]:
        axis.set_title(options["title"])

    output = options["output"]
    if output:
        plt.savefig(
            output,
            bbox_inches="tight",
            dpi=dpi,
            transparent=transparent,
        )
        plt.close()
        gs.message(_("Histogram written to <{}>.").format(os.path.abspath(output)))
    else:
        gs.message(_("\n> Close the figure window to finish the script.\n"))
        plt.tight_layout()
        plt.show()
        plt.close()


def main(options, flags):
    """Draw a histogram of the non-NULL values in a raster map."""
    bins = int(options["bins"])
    if bins <= 0:
        gs.fatal(_("The number of bins must be larger than zero."))

    output = options["output"] if options["output"] else None
    lazy_import_py_modules(bool(output))
    apply_style(options["style"])

    counts, edges, centers = histogram_data(options["map"], bins)
    draw_histogram(options, flags, counts, edges, centers)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
