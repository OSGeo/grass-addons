BARREN_LAND_CLASS_STRING = 'Barren_Land'
DUMMY_MAPCALC_STRING_RADIANCE = 'Radiance'
DUMMY_MAPCALC_STRING_DN = 'DigitalNumber'
DUMMY_MAPCALC_STRING_T10 = 'Input_T10'
DUMMY_MAPCALC_STRING_T11 = 'Input_T11'
DUMMY_MAPCALC_STRING_AVG_LSE = 'Input_AVG_LSE'
DUMMY_MAPCALC_STRING_DELTA_LSE = 'Input_DELTA_LSE'
DUMMY_MAPCALC_STRING_FROM_GLC = 'Input_FROMGLC'
DUMMY_MAPCALC_STRING_CWV = 'Input_CWV'
DUMMY_Ti_MEAN = 'Mean_Ti'
DUMMY_Tj_MEAN = 'Mean_Tj'
DUMMY_Rji = 'Ratio_ji'
EQUATION = "{result} = {expression}"
FROM_GLC_CODES = [10, 11, 12, 13,
                  20, 21, 22, 23, 24,
                  30, 31, 32,
                  51, 72,
                  40, 71,
                  60, 61, 62, 63,
                  80, 81, 82,
                  90, 52, 91, 92, 93, 94, 95, 96,
                  100, 101, 102]
FROM_GLC_LEGEND = {'Cropland': (10, 11, 12, 13),
                   'Forest': (20, 21, 22, 23, 24),
                   'Grasslands': (30, 31, 32, 51, 72),
                   'Shrublands': (40, 71),
                   'Waterbodies': (60, 61, 62, 63),
                   'Tundra': (70,),
                   'Impervious': (80, 81, 82),
                   'Barren_Land': (90, 52, 91, 92, 93, 94, 95, 96),
                   'Snow_and_ice': (100, 101, 102),
                   'Cloud': (120,)}
# LST_FORMULA = ('{b0} + '
#                '({b1} + '
#                '({b2}) * ((1 - {ae}) / {ae}^2) + '
#                '({b3}) * ({de}/{ae}^2)) * (({DUMMY_T10}+{DUMMY_T11})/2) + '
#                '({b4} + '
#                '({b5}) * ((1 - {ae}) / {ae}) + '
#                '({b6}) * ({de}/{ae}^2)) * (({DUMMY_T10}-{DUMMY_T11})/2)')
# LST_FORMULA_BARREN_LAND = 
LST_FORMULA = ('{b0} + '
               '({b1} + '
               '({b2}) * ((1 - {ae}) / {ae}^2) + '
               '({b3}) * ({de}/{ae}^2)) * (({DUMMY_T10}+{DUMMY_T11})/2) + '
               '({b4} + '
               '({b5}) * ((1 - {ae}) / {ae}) + '
               '({b6}) * ({de}/{ae}^2)) * (({DUMMY_T10}-{DUMMY_T11})/2) + '
               '({b7}) * ({DUMMY_T10} - {DUMMY_T11})^2')
