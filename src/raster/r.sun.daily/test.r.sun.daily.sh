#!/bin/sh

############################################################################
#
# TEST:      test.r.sun.daily
# AUTHOR(S): Vaclav Petras, Anna Petrasova
# PURPOSE:   This is test for r.sun.daily module
# COPYRIGHT: (C) 2013 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# @preprocess step
# The region setting should work for UTM and LL test locations
# region could be set to some real values to avoid unable to read fp range warning

g.region s=30 n=40 w=40 e=60 res=10
r.mapcalc --o expr="building = 50"

g.region s=0 n=80 w=0 e=120 res=10
r.mapcalc --o expr="terrain = 10"

r.mapcalc --o expr="terrain = terrain + building"

map_basename=reflmap

map_names_file=`g.tempfile pid=$$`
created_map_names_file=`g.tempfile pid=$$`
should_not_be_created_map="test_r_sun_should_not_be_created_map"

cat > "${map_names_file}" << EOF
${map_basename}_026
${map_basename}_029
${map_basename}_032
${map_basename}_035
EOF

# The @test

NAME="Missing parameter test (module should fail)"
r.sun.daily elev=terrain start_day=26 end_day=37 day_step=3
echo "$NAME: r.sun.daily returned: $? (expecting 1)"

NAME="Wrong start and end day parameter values test (module should fail)"
r.sun.daily elevation=terrain start_day=82 end_day=37 day_step=3 reflrad_basename=${should_not_be_created_map}
echo "$NAME: r.sun.daily returned: $? (expecting 1)"

NAME="Wrong day step parameter values test (module should fail)"
r.sun.daily elevation=terrain start_day=82 end_day=85 day_step=9 reflrad_basename=${should_not_be_created_map}
echo "$NAME: r.sun.daily returned: $? (expecting 1)"

NAME="Wrong day step parameter and cumulative parameters values test (module should fail)"
r.sun.daily elevation=terrain start_day=1 end_day=85 day_step=9 refl_rad=${should_not_be_created_map}
echo "$NAME: r.sun.daily returned: $? (expecting 1)"

NAME="Map creation test"
r.sun.daily elevation=terrain start_day=26 end_day=37 day_step=3 reflrad_basename=${map_basename}

g.list -e type=rast pattern=${map_basename}_[0-9]{3} sep=newline > ${created_map_names_file}

diff ${map_names_file} ${created_map_names_file}
echo "$NAME: Diff returned $? (expecting 0)"

NAME="Overwrite flag test"
r.sun.daily elevation=terrain start_day=26 end_day=37 day_step=3 reflrad_basename=${map_basename} --overwrite
echo "$NAME: r.sun.daily returned: $? (expecting 0)"

NAME="Map already exists test (module should fail)"
r.sun.daily elevation=terrain start_day=26 end_day=37 day_step=3 reflrad_basename=${map_basename}
echo "$NAME: r.sun.daily returned: $? (expecting 1)"

# clean
rm ${map_names_file} ${created_map_names_file}
g.remove -ef type=rast pattern=${map_basename}_[0-9]{3}
