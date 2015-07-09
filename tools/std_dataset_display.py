#!/usr/bin/env python

import os
import grass.script as gscript

# before the script runs, old maps and existing images must be removed
# g.remove type=raster name=slope,aspect,profile_curvature,shade -f
# rm *.png


def description_box(title):
    gscript.write_command('d.graph', stdin="""
    color white
    polygon
        0 0
        0 16
        100 16
        100 0
    """)
    gscript.run_command('d.text', text=title, at='2,11', size=5, color='black')


def legend_item(color, text, x, y):
    gscript.write_command('d.graph', stdin="""
    color {color}
    polygon
        {x1} {y2}
        {x1} {y1}
        {x2} {y1}
        {x2} {y2}
    """.format(color=color, x1=x, y1=y, x2=x + 2, y2=y + 2))
    gscript.run_command('d.text', text=text, at=(x + 3, y + 0.5), size=2, color='black')


def d_rast_legend(raster, title):
    gscript.run_command('d.rast', map=raster)
    description_box(title)
    gscript.run_command('d.legend', raster=raster, at='6,9,6,50')
    gscript.run_command('d.barscale', style='classic', at='55,9', color='black', text_position='over')


def main():
    elevation = 'elevation'
    slope = 'slope'
    aspect = 'aspect'
    profile_curvature = 'profile_curvature'
    shade = 'shade'
    streams = 'streams'
    streams_color = 'aqua'
    roadsmajor = 'roadsmajor'
    roads_color = 'yellow'

    # we set region for the whole session (i.e. also outside the script)
    gscript.run_command('g.region', raster=elevation)

    gscript.run_command('r.slope.aspect', elevation=elevation,
                        slope=slope, aspect=aspect, pcurvature=profile_curvature)

    gscript.run_command('r.relief', input=elevation, output=shade)

    # render maps
    # set variables for rendering into a file
    os.environ['GRASS_RENDER_IMMEDIATE'] = 'cairo'
    os.environ['GRASS_RENDER_WIDTH'] = '600'
    os.environ['GRASS_RENDER_HEIGHT'] = '600'
    os.environ['GRASS_RENDER_FILE_READ'] = 'TRUE'
    os.environ['GRASS_FONT'] = 'sans'

    # shaded map with vectors
    os.environ['GRASS_RENDER_FILE'] = 'shaded_elevation.png'
    gscript.run_command('d.shade', shade=shade, color=elevation)
    gscript.run_command('d.vect', map=streams, width=1, color=streams_color)
    gscript.run_command('d.vect', map=roadsmajor, width=2, color=roads_color)
    description_box('Overview map')
    legend_item(streams_color, 'Streams', 3, 3)
    legend_item(roads_color, 'Major roads', 3, 6)
    gscript.run_command('d.legend', raster=elevation, at='3,6,30,50')
    gscript.run_command('d.text', text='Elevation', at='30,7', size=2, color='black')
    gscript.run_command('d.barscale', style='classic', at='55,9', color='black', text_position='over')

    # individual rasters
    os.environ['GRASS_RENDER_FILE'] = 'slope.png'
    d_rast_legend(slope, 'Slope')

    os.environ['GRASS_RENDER_FILE'] = 'aspect.png'
    d_rast_legend(aspect, 'Aspect')

    os.environ['GRASS_RENDER_FILE'] = 'profile_curvature.png'
    d_rast_legend(profile_curvature, 'Profile curvature')

    # post processing
    # convert shaded_elevation.png slope.png aspect.png profile_curvature.png +append stripe.png
    # mogrify -resize 60%x60% stripe.png
    # optipng stripe.png

if __name__ == "__main__":
    main()
