#!/usr/bin/env python

import os
import grass.script as gscript
from PIL import Image
import argparse

# before the script runs, old maps and existing images must be removed
# g.remove type=raster name=slope,aspect,profile_curvature,shade -f
# rm *.png

# the size of images could be different between different dataset
DATASET = {"north_carolina": {"w": 600, "h": 600}, "piemonte": {"w": 600, "h": 800}}


def description_box(title):
    gscript.write_command(
        "d.graph",
        stdin="""
    color white
    polygon
        0 0
        0 16
        100 16
        100 0
    """,
    )
    gscript.run_command("d.text", text=title, at="2,11", size=5, color="black")


def legend_item(color, text, x, y):
    gscript.write_command(
        "d.graph",
        stdin="""
    color {color}
    polygon
        {x1} {y2}
        {x1} {y1}
        {x2} {y1}
        {x2} {y2}
    """.format(
            color=color, x1=x, y1=y, x2=x + 2, y2=y + 2
        ),
    )
    gscript.run_command("d.text", text=text, at=(x + 3, y + 0.5), size=2, color="black")


def d_rast_legend(raster, title):
    """Print raster and its legend
    :param str raster: the name of raster to print
    :param str title: the text to append to the legend
    """
    gscript.run_command("d.rast", map=raster)
    description_box(title)
    gscript.run_command("d.legend", raster=raster, at="6,9,6,50", flags="d")
    gscript.run_command(
        "d.barscale", style="classic", at="55,9", color="black", text_position="over"
    )


def join_output(inputs, output, width, height, resize=None):
    """Attach several  images in a collage
    :param list inputs: a list with the input images to attach together
    :param str output: the output name
    :param int width: the width of images
    :param int height: the height of images
    :param float resize: value between 0 and 1 to resize the final output
    """
    out = Image.new("RGB", (width * len(inputs), height), "white")
    x = 0
    for inp in inputs:
        out.paste(Image.open(inp), (x, 0))
        x += width
    if resize and resize < 1.0:
        out = out.resize(width * resize, height * resize)
    out.save(output)


def cleanup(maps):
    """Remove all the created maps"""
    gscript.run_command("g.remove", type="raster", name=",".join(maps), flags="f")


def get_parser():
    """Create the parser for running as script"""
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "dataset",
        type=str,
        metavar="DATASET",
        help="Name of dataset you are using, possible choices"
        " are: {va}".format(va=", ".join(DATASET.keys())),
        choices=DATASET.keys(),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="OUTPUT",
        help="Name of output collage",
        dest="output",
    )
    parser.add_argument(
        "-e",
        "--elevation",
        type=str,
        default="shaded_elevation.png",
        dest="ele",
        help="Name of shaded elevation output",
    )
    parser.add_argument(
        "-s",
        "--slope",
        type=str,
        default="slope.png",
        dest="slope",
        help="Name of slope output",
    )
    parser.add_argument(
        "-a",
        "--aspect",
        type=str,
        default="aspect.png",
        dest="aspect",
        help="Name of aspect output",
    )
    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        dest="profile",
        default="profile_curvature.png",
        help="Name of profile curvature output",
    )
    parser.add_argument(
        "-r",
        "--resize",
        type=float,
        default=1.0,
        dest="resize",
        help="Value to resize the final output",
    )
    parser.add_argument(
        "-c",
        "--cleanup",
        action="store_true",
        default=False,
        dest="cleanup",
        help="Remove the maps created by this" " script",
    )
    return parser


def main():
    """Main function to run the script"""
    parser = get_parser()
    args = parser.parse_args()
    # original maps
    elevation = "elevation"
    streams = "streams"
    roadsmajor = "roadsmajor"
    # color
    streams_color = "aqua"
    roads_color = "yellow"
    # created maps, to be removed
    slope = "slope"
    aspect = "aspect"
    profile_curvature = "profile_curvature"
    shade = "shade"
    # final png outfile
    ele_out = args.ele
    aspect_out = args.aspect
    slope_out = args.slope
    profile_out = args.profile

    data = DATASET[args.dataset]
    width = data["w"]
    height = data["h"]

    # we set region for the whole session (i.e. also outside the script)
    gscript.run_command("g.region", raster=elevation)

    gscript.run_command(
        "r.slope.aspect",
        elevation=elevation,
        slope=slope,
        aspect=aspect,
        pcurvature=profile_curvature,
    )

    gscript.run_command("r.relief", input=elevation, output=shade)

    # render maps
    # set variables for rendering into a file
    os.environ["GRASS_RENDER_IMMEDIATE"] = "cairo"
    os.environ["GRASS_RENDER_WIDTH"] = str(width)
    os.environ["GRASS_RENDER_HEIGHT"] = str(height)
    os.environ["GRASS_RENDER_FILE_READ"] = "TRUE"
    os.environ["GRASS_FONT"] = "sans"

    # shaded map with vectors
    os.environ["GRASS_RENDER_FILE"] = ele_out
    gscript.run_command("d.shade", shade=shade, color=elevation)
    gscript.run_command("d.vect", map=streams, width=1, color=streams_color)
    gscript.run_command("d.vect", map=roadsmajor, width=2, color=roads_color)
    description_box("Overview map")
    legend_item(streams_color, "Streams", 3, 3)
    legend_item(roads_color, "Major roads", 3, 6)
    gscript.run_command("d.legend", raster=elevation, at="3,6,30,50")
    gscript.run_command("d.text", text="Elevation", at="30,7", size=2, color="black")
    gscript.run_command(
        "d.barscale", style="classic", at="55,9", color="black", text_position="over"
    )

    # individual rasters
    os.environ["GRASS_RENDER_FILE"] = slope_out
    d_rast_legend(slope, "Slope")

    os.environ["GRASS_RENDER_FILE"] = aspect_out
    d_rast_legend(aspect, "Aspect")

    os.environ["GRASS_RENDER_FILE"] = profile_out
    d_rast_legend(profile_curvature, "Profile curvature")

    if args.output:
        join_inputs = [ele_out, aspect_out, slope_out, profile_out]
        join_output(join_inputs, args.output, width, height, args.resize)

    if args.cleanup:
        clean_maps = [slope, aspect, profile_curvature, shade]
        cleanup(clean_maps)


if __name__ == "__main__":
    main()
