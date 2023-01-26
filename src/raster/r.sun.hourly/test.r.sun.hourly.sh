#!/bin/sh

############################################################################
#
# TEST:      test.r.sun.hourly
# AUTHOR(S): Vaclav Petras, Anna Petrasova
# PURPOSE:   This is test for r.sun.hourly module
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

map_number_separator="_"
map_number_pattern="[0-9]{2}.[0-9]{2}"

map_basename=reflmap
decimal_map_basename=reflmap_decimal
temporal_map_basename=reflmap_temporal

map_names_file=`g.tempfile pid=$$`
created_map_names_file=`g.tempfile pid=$$`

decimal_map_names_file=`g.tempfile pid=$$`
decimal_created_map_names_file=`g.tempfile pid=$$`

temporal_dataset_file=`g.tempfile pid=$$`
temporal_map_names_file=`g.tempfile pid=$$`
temporal_created_dataset_file=`g.tempfile pid=$$`
temporal_created_map_names_file=`g.tempfile pid=$$`
year=2001

cat > "${map_names_file}" << EOF
${map_basename}_11.50
${map_basename}_14.50
${map_basename}_17.50
EOF

cat > "${decimal_map_names_file}" << EOF
${decimal_map_basename}_07.00
${decimal_map_basename}_08.33
${decimal_map_basename}_09.67
${decimal_map_basename}_11.00
EOF

cat > "${temporal_dataset_file}" << EOF
${temporal_map_basename}@`g.mapset -p`
EOF

cat > "${temporal_map_names_file}" << EOF
${temporal_map_basename}_11.50 landsat ${year}-04-10 11:30:00 None
${temporal_map_basename}_14.50 landsat ${year}-04-10 14:30:00 None
${temporal_map_basename}_17.50 landsat ${year}-04-10 17:30:00 None
EOF

# The @test

NAME="Missing ouput parameter test (module should fail)"
r.sun.hourly elevation=terrain start_time=11.50 end_time=18.20 time_step=3 day=80
echo "$NAME: r.sun.hourly returned: $? (expecting 1)"

NAME="Wrong start and end time parameter values test (module should fail)"
r.sun.hourly elevation=terrain start_time=11.50 end_time=9.00 time_step=3 day=80 reflrad_basename=${map_basename}
echo "$NAME: r.sun.hourly returned: $? (expecting 1)"

NAME="Wrong time step parameter value test (module should fail)"
r.sun.hourly elevation=terrain start_time=10.60 end_time=11.20 time_step=0.60 day=80 reflrad_basename=${map_basename}
echo "$NAME: r.sun.hourly returned: $? (expecting 1)"

NAME="Map creation test"
r.sun.hourly elevation=terrain start_time=11.50 end_time=20.00 time_step=3 day=80 reflrad_basename=${map_basename}

g.list -e type=rast pattern=${map_basename}${map_number_separator}${map_number_pattern} sep=newline > ${created_map_names_file}

diff ${map_names_file} ${created_map_names_file}
echo "$NAME: Diff returned $? (expecting 0)"

NAME="Map creation test with too much decimal places"
r.sun.hourly elevation=terrain start_time=7.0000 end_time=11.0000 time_step=1.3333 day=80 reflrad_basename=${decimal_map_basename}

g.list -e type=rast pattern=${decimal_map_basename}${map_number_separator}${map_number_pattern} sep=newline > ${decimal_created_map_names_file}

diff ${decimal_map_names_file} ${decimal_created_map_names_file}
echo "$NAME: Diff returned $? (expecting 0)"

NAME="Temporal dataset creation test"
r.sun.hourly -t elevation=terrain start_time=11.50 end_time=20.00 time_step=3 day=100 year=${year} reflrad_basename=${temporal_map_basename}

t.list type=strds > ${temporal_created_dataset_file}

t.rast.list input=${temporal_map_basename} method=col > ${temporal_created_map_names_file}

diff ${temporal_dataset_file} ${temporal_created_dataset_file}
echo "$NAME (maps temporal dataset subtest): Diff returned $? (expecting 0)"

diff --ignore-all-space ${temporal_map_names_file} ${temporal_created_map_names_file}
echo "$NAME (maps sub-test): Diff returned $? (expecting 0)"

NAME="Map already exists test (module should fail)"
r.sun.hourly elevation=terrain start_time=11.50 end_time=20.00 time_step=3 day=80 reflrad_basename=${map_basename}
echo "$NAME: r.sun.hourly returned: $? (expecting 1)"

# clean
rm ${map_names_file} ${created_map_names_file}
g.remove -ef type=rast pattern=${map_basename}${map_number_separator}${map_number_pattern}

rm ${decimal_map_names_file} ${decimal_created_map_names_file}
g.remove -ef type=rast pattern=${decimal_map_basename}${map_number_separator}${map_number_pattern}

rm ${temporal_map_names_file} ${temporal_dataset_file} ${temporal_created_dataset_file} ${temporal_created_map_names_file}
t.remove -rf inputs=${temporal_map_basename}
