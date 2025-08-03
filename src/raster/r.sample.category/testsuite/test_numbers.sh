#!/usr/bin/env sh

num_points_expected=42
num_cats_expected=7

g.region raster=landclass96
r.sample.category input=landclass96 output=landclass_points npoints=6 --o

num_points=$(v.db.select -c landclass_points | wc -l)

if [ $num_points -ne $num_points_expected ]; then
    >&2 echo "number of points ($num_points) != requested points per category times number of categories ($num_points_expected)"
    exit 1
fi

num_cats=$(v.db.select -c landclass_points | sed "s/.*|//g" | uniq | wc -l)

if [ $num_cats -ne $num_cats_expected ]; then
    >&2 echo "number of sampled categories ($num_cats) != number of categories in raster ($num_cats_expected)"
    exit 1
fi
