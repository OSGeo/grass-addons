"""
Name:       v.rast.bufferstats test
Purpose:    Tests v.rast.bufferstats with different input.
            Uses NC Basic data set.

Author:     Luca Delucchi
Copyright:  (C) 2017 by Luca Delucchi and the GRASS Development Team
Licence:    This program is free software under the GNU General Public
            License (>=v2). Read the file COPYING that comes with GRASS
            for details.
"""

import os

import grass.script as gscript
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestBufferstats(TestCase):
    inpoint = "firestations"
    inpoint_cats = "9,12,22,26,28"
    inpoint_tmp = "firestations_tmp"
    inline = "roadsmajor"
    inline_tmp = "roadsmajor_tmp"
    inline_cats = "227,231,271,272,273,277,302,316,319"
    inarea = "lakes"
    inarea_tmp = "lakes_tmp"
    inarea_cats = "6836,7283,8359,9240,10648,10809"
    inrast_label = "landclass96"
    inrast_no_label = "basin_50K"
    inrast_cont_1 = "elevation"
    inrast_cont_2 = "aspect"
    output = gscript.tempfile(create=False)
    # Output references
    points_cont = """cat|raster_map|buffer|statistic|value
9|elev|30|sum|3922.98136901855
9|elev|30|maximum|140.796890258789
9|elev|30|minimum|139.316741943359
9|elev|30|average|140.106477464948
9|aspect|30|sum|4153.37023925781
9|aspect|30|maximum|356.791687011719
9|aspect|30|minimum|75.3329010009766
9|aspect|30|average|148.334651402065
9|elev|50|sum|11058.9987792969
9|elev|50|maximum|142.220809936523
9|elev|50|minimum|136.571548461914
9|elev|50|average|139.987326320214
9|aspect|50|sum|11078.4593048096
9|aspect|50|maximum|356.791687011719
9|aspect|50|minimum|59.5261459350586
9|aspect|50|average|140.233662086197
12|elev|30|sum|3890.39111328125
12|elev|30|maximum|139.911636352539
12|elev|30|minimum|138.088180541992
12|elev|30|average|138.942539760045
12|aspect|30|sum|4192.51754665375
12|aspect|30|maximum|358.673522949219
12|aspect|30|minimum|3.08826923370361
12|aspect|30|average|149.732769523348
12|elev|50|sum|10986.4864196777
12|elev|50|maximum|140.922546386719
12|elev|50|minimum|136.884704589844
12|elev|50|average|139.069448350351
12|aspect|50|sum|11192.4951819777
12|aspect|50|maximum|359.847290039062
12|aspect|50|minimum|0.2237349152565
12|aspect|50|average|141.67715420225
22|elev|30|sum|2258.35559844971
22|elev|30|maximum|81.1031494140625
22|elev|30|minimum|79.6930313110352
22|elev|30|average|80.6555570874895
22|aspect|30|sum|4304.2073135376
22|aspect|30|maximum|228.845352172852
22|aspect|30|minimum|106.974494934082
22|aspect|30|average|153.7216897692
22|elev|50|sum|6365.45648193359
22|elev|50|maximum|81.6564407348633
22|elev|50|minimum|78.9974822998047
22|elev|50|average|80.5753985054885
22|aspect|50|sum|11882.7497787476
22|aspect|50|maximum|228.845352172852
22|aspect|50|minimum|106.974494934082
22|aspect|50|average|150.414554161362
26|elev|30|sum|3615.70491027832
26|elev|30|maximum|125.495140075684
26|elev|30|minimum|123.411689758301
26|elev|30|average|124.67947966477
26|aspect|30|sum|3512.48431944847
26|aspect|30|maximum|358.51025390625
26|aspect|30|minimum|2.05520701408386
26|aspect|30|average|121.120148946499
26|elev|50|sum|9709.70238494873
26|elev|50|maximum|126.604881286621
26|elev|50|minimum|122.212753295898
26|elev|50|average|124.483363909599
26|aspect|50|sum|8413.9311671257
26|aspect|50|maximum|358.51025390625
26|aspect|50|minimum|2.05520701408386
26|aspect|50|average|107.870912399047
28|elev|30|sum|2520.72622680664
28|elev|30|maximum|92.3031921386719
28|elev|30|minimum|89.0716400146484
28|elev|30|average|90.0259366716657
28|aspect|30|sum|2344.68381881714
28|aspect|30|maximum|140.575744628906
28|aspect|30|minimum|32.8917961120605
28|aspect|30|average|83.7387078148978
28|elev|50|sum|7220.3387298584
28|elev|50|maximum|93.5220108032227
28|elev|50|minimum|88.9108428955078
28|elev|50|average|90.25423412323
28|aspect|50|sum|7024.33261609077
28|aspect|50|maximum|358.419372558594
28|aspect|50|minimum|3.5048553943634
28|aspect|50|average|87.8041577011347
"""
    points_tab = """cat|raster_map|buffer|statistic|value
9|lc|30|ncats|1
9|lc|30|mode|4
9|lc|30|area shrubland|75.00%
9|basin|30|ncats|1
9|basin|30|mode|22
9|basin|30|area 22|75.00%
9|lc|50|ncats|3
9|lc|50|mode|4
9|lc|50|area shrubland|35.00%
9|lc|50|area herbaceous|5.00%
9|lc|50|area forest|5.00%
9|basin|50|ncats|1
9|basin|50|mode|22
9|basin|50|area 22|43.75%
12|lc|30|ncats|1
12|lc|30|mode|1
12|lc|30|area developed|75.00%
12|basin|30|ncats|1
12|basin|30|mode|12
12|basin|30|area 12|75.00%
12|lc|50|ncats|2
12|lc|50|mode|1
12|lc|50|area developed|46.67%
12|lc|50|area forest|13.33%
12|basin|50|ncats|1
12|basin|50|mode|12
12|basin|50|area 12|100.00%
22|lc|30|ncats|1
22|lc|30|mode|1
22|lc|30|area developed|66.67%
22|basin|30|ncats|1
22|basin|30|mode|16
22|basin|30|area 16|66.67%
22|lc|50|ncats|1
22|lc|50|mode|1
22|lc|50|area developed|125.00%
22|basin|50|ncats|1
22|basin|50|mode|16
22|basin|50|area 16|125.00%
26|lc|30|ncats|1
26|lc|30|mode|1
26|lc|30|area developed|66.67%
26|basin|30|ncats|1
26|basin|30|mode|2
26|basin|30|area 2|66.67%
26|lc|50|ncats|2
26|lc|50|mode|1
26|lc|50|area developed|53.33%
26|lc|50|area forest|13.33%
26|basin|50|ncats|1
26|basin|50|mode|2
26|basin|50|area 2|125.00%
28|lc|30|ncats|1
28|lc|30|mode|1
28|lc|30|area developed|25.00%
28|lc|50|ncats|2
28|lc|50|mode|1
28|lc|50|area developed|40.00%
28|lc|50|area forest|13.33%
"""
    lines_tab = """cat|raster_map|buffer|statistic|value
227|lc|30|ncats|5
227|lc|30|mode|1
227|lc|30|area no_data|3608014.500000
227|lc|30|area developed|138894.750000
227|lc|30|area shrubland|63355.500000
227|lc|30|area forest|46298.250000
227|lc|30|area herbaceous|21118.500000
227|lc|30|area total|3877681.5
227|basin|30|ncats|3
227|basin|30|mode|12
227|basin|30|area null|3791583.000000
227|basin|30|area 12|77163.750000
227|basin|30|area 8|8934.750000
227|basin|30|area total|86098.5
231|lc|30|ncats|4
231|lc|30|mode|1
231|lc|30|area no_data|2372582.250000
231|lc|30|area developed|114527.250000
231|lc|30|area herbaceous|25179.750000
231|lc|30|area forest|2436.750000
231|lc|30|area total|2514726.0
231|basin|30|ncats|3
231|basin|30|mode|12
231|basin|30|area null|2372582.250000
231|basin|30|area 12|127523.250000
231|basin|30|area 8|14620.500000
231|basin|30|area total|142143.75
271|lc|30|ncats|4
271|lc|30|mode|1
271|lc|30|area no_data|2409945.750000
271|lc|30|area developed|179507.250000
271|lc|30|area herbaceous|17869.500000
271|lc|30|area forest|8122.500000
271|lc|30|area total|2615445.0
271|basin|30|ncats|5
271|basin|30|mode|4
271|basin|30|area null|2465178.750000
271|basin|30|area 4|88535.250000
271|basin|30|area 16|47922.750000
271|basin|30|area 6|9747.000000
271|basin|30|area 10|4061.250000
271|basin|30|area total|150266.25
272|lc|30|ncats|4
272|lc|30|mode|1
272|lc|30|area no_data|3492675.000000
272|lc|30|area developed|100719.000000
272|lc|30|area forest|55233.000000
272|lc|30|area shrubland|10559.250000
272|lc|30|area total|3659186.25
272|basin|30|ncats|3
272|basin|30|mode|20
272|basin|30|area null|3492675.000000
272|basin|30|area 20|135645.750000
272|basin|30|area 12|30865.500000
272|basin|30|area total|166511.25
273|lc|30|ncats|5
273|lc|30|mode|1
273|lc|30|area no_data|2251557.000000
273|lc|30|area developed|220119.750000
273|lc|30|area forest|7310.250000
273|lc|30|area shrubland|4061.250000
273|lc|30|area herbaceous|1624.500000
273|lc|30|area total|2484672.75
273|basin|30|ncats|3
273|basin|30|mode|14
273|basin|30|area null|2251557.000000
273|basin|30|area 14|207936.000000
273|basin|30|area 12|25179.750000
273|basin|30|area total|233115.75
277|lc|30|ncats|3
277|lc|30|mode|1
277|lc|30|area no_data|4538040.750000
277|lc|30|area developed|200625.750000
277|lc|30|area forest|43861.500000
277|lc|30|area total|4782528.0
277|basin|30|ncats|3
277|basin|30|mode|12
277|basin|30|area null|4538040.750000
277|basin|30|area 12|229054.500000
277|basin|30|area 14|15432.750000
277|basin|30|area total|244487.25
302|lc|30|ncats|2
302|lc|30|mode|1
302|lc|30|area no_data|631930.500000
302|lc|30|area developed|164074.500000
302|lc|30|area total|796005.0
302|basin|30|ncats|2
302|basin|30|mode|16
302|basin|30|area null|631930.500000
302|basin|30|area 16|164074.500000
302|basin|30|area total|164074.5
316|lc|30|ncats|4
316|lc|30|mode|1
316|lc|30|area no_data|7676574.750000
316|lc|30|area developed|238801.500000
316|lc|30|area forest|7310.250000
316|lc|30|area herbaceous|3249.000000
316|lc|30|area total|7925935.5
316|basin|30|ncats|3
316|basin|30|mode|26
316|basin|30|area null|7812220.500000
316|basin|30|area 26|99906.750000
316|basin|30|area 16|13808.250000
316|basin|30|area total|113715.0
319|lc|30|ncats|4
319|lc|30|mode|1
319|lc|30|area no_data|7889384.250000
319|lc|30|area developed|214434.000000
319|lc|30|area forest|37363.500000
319|lc|30|area shrubland|8122.500000
319|lc|30|area total|8149304.25
319|basin|30|ncats|5
319|basin|30|mode|26
319|basin|30|area null|7889384.250000
319|basin|30|area 26|173821.500000
319|basin|30|area 30|45486.000000
319|basin|30|area 24|27616.500000
319|basin|30|area 16|12996.000000
319|basin|30|area total|259920.0
"""

    area_tab = """cat|raster_map|buffer|statistic|value
6836|lc|30|ncats|2
6836|lc|30|mode|1
6836|lc|30|area no_data|7310.250000
6836|lc|30|area developed|5685.750000
6836|lc|30|area total|12996.0
6836|basin|30|ncats|2
6836|basin|30|mode|2
6836|basin|30|area null|7310.250000
6836|basin|30|area 2|5685.750000
6836|basin|30|area total|5685.75
7283|lc|30|ncats|2
7283|lc|30|mode|5
7283|lc|30|area no_data|11371.500000
7283|lc|30|area forest|8934.750000
7283|lc|30|area total|20306.25
7283|basin|30|ncats|2
7283|basin|30|mode|12
7283|basin|30|area null|11371.500000
7283|basin|30|area 12|8934.750000
7283|basin|30|area total|8934.75
8359|lc|30|ncats|2
8359|lc|30|mode|5
8359|lc|30|area no_data|16245.000000
8359|lc|30|area forest|12996.000000
8359|lc|30|area total|29241.0
8359|basin|30|ncats|2
8359|basin|30|mode|20
8359|basin|30|area null|16245.000000
8359|basin|30|area 20|12996.000000
8359|basin|30|area total|12996.0
9240|lc|30|ncats|4
9240|lc|30|mode|6
9240|lc|30|area no_data|56857.500000
9240|lc|30|area water|31677.750000
9240|lc|30|area herbaceous|15432.750000
9240|lc|30|area forest|3249.000000
9240|lc|30|area total|107217.0
9240|basin|30|ncats|2
9240|basin|30|mode|30
9240|basin|30|area null|56857.500000
9240|basin|30|area 30|50359.500000
9240|basin|30|area total|50359.5
10648|lc|30|ncats|4
10648|lc|30|mode|5
10648|lc|30|area forest|16245.000000
10648|lc|30|area no_data|9747.000000
10648|lc|30|area shrubland|5685.750000
10648|lc|30|area herbaceous|812.250000
10648|lc|30|area total|32490.0
10648|basin|30|ncats|2
10648|basin|30|mode|22
10648|basin|30|area 22|22743.000000
10648|basin|30|area null|9747.000000
10648|basin|30|area total|22743.0
10809|lc|30|ncats|4
10809|lc|30|mode|1
10809|lc|30|area no_data|21930.750000
10809|lc|30|area developed|12183.750000
10809|lc|30|area water|10559.250000
10809|lc|30|area forest|812.250000
10809|lc|30|area total|45486.0
10809|basin|30|ncats|1
10809|basin|30|mode|NULL
10809|basin|30|area null|45486.000000
10809|basin|30|area total|0
"""

    point_attrs = """cat|ID|LABEL|LOCATION|CITY|MUN_COUNT|PUMPERS|PUMPER_TAN|TANKER|MINI_PUMPE|RESCUE_SER|AERIAL|BRUSH|OTHERS|WATER_RESC|MUNCOID|BLDGCODE|AGENCY|STATIONID|RECNO|CV_SID2|CVLAG|elev_sum_b30|elev_max_b30|elev_min_b30|elev_mean_b30|elev_sum_b50|elev_max_b50|elev_min_b50|elev_mean_b50|aspect_sum_b30|aspect_max_b30|aspect_min_b30|aspect_mean_b30|aspect_sum_b50|aspect_max_b50|aspect_min_b50|aspect_mean_b50|lc_ncats_b30|lc_mode_b30|lc_null_b30|lc_area_tot_b30|lc_1_b30|lc_2_b30|lc_3_b30|lc_4_b30|lc_5_b30|lc_6_b30|lc_7_b30|lc_ncats_b50|lc_mode_b50|lc_null_b50|lc_area_tot_b50|lc_1_b50|lc_2_b50|lc_3_b50|lc_4_b50|lc_5_b50|lc_6_b50|lc_7_b50|basin_ncats_b30|basin_mode_b30|basin_null_b30|basin_area_tot_b30|basin_2_b30|basin_4_b30|basin_6_b30|basin_8_b30|basin_10_b30|basin_12_b30|basin_14_b30|basin_16_b30|basin_18_b30|basin_20_b30|basin_22_b30|basin_24_b30|basin_26_b30|basin_28_b30|basin_30_b30|basin_ncats_b50|basin_mode_b50|basin_null_b50|basin_area_tot_b50|basin_2_b50|basin_4_b50|basin_6_b50|basin_8_b50|basin_10_b50|basin_12_b50|basin_14_b50|basin_16_b50|basin_18_b50|basin_20_b50|basin_22_b50|basin_24_b50|basin_26_b50|basin_28_b50|basin_30_b50|lc_developed_b30|lc_agriculture_b30|lc_herbaceous_b30|lc_shrubland_b30|lc_forest_b30|lc_water_b30|lc_sediment_b30|lc_developed_b50|lc_agriculture_b50|lc_herbaceous_b50|lc_shrubland_b50|lc_forest_b50|lc_water_b50|lc_sediment_b50
9|20|Fairview #1|4501 Ten-Ten Rd|Apex|C|1|1|3|0|1|0|0|1|0|2|162|FD|FF1A|11|FF1A|1.42|3922.98136901855|140.796890258789|139.316741943359|140.106477464948|11058.9987792969|142.220809936523|136.571548461914|139.987326320214|4153|356|75|148.334651402065|11078|356|59|140.233662086197|1|4||2436.75||||2436.75||||3|4||7310.25|||812.25|5685.75|812.25|||1|22||2436.75|||||||||||75|||||1|22||5685.75|||||||||||43.75||||||||75||||||5|35|5||
12|222|Cary #2|875 SE Maynard Rd|Cary|M|1|0|0|0|1|0|0|0|0|1|252|CF|CF2A|14|CF2A|1|3890.39111328125|139.911636352539|138.088180541992|138.942539760045|10986.4864196777|140.922546386719|136.884704589844|139.069448350351|4192|358|3|149.732769523348|11192|359|0|141.67715420225|1|1||2436.75|2436.75|||||||2|1||7310.25|5685.75||||1624.5|||1|12||2436.75||||||75||||||||||1|12||7310.25||||||100||||||||||75|||||||46.67||||13.33||
22|0|RFD #2|263 Pecan Rd|Raleigh|M|2|0|0|0|0|0|0|0|0|1|261|RF|RF02|24|RF02|0|2258.35559844971|81.1031494140625|79.6930313110352|80.6555570874895|6365.45648193359|81.6564407348633|78.9974822998047|80.5753985054885|4304|228|106|153.7216897692|11882|228|106|150.414554161362|1|1||3249|3249|||||||1|1||8122.5|8122.5|||||||1|16||3249||||||||66.67||||||||1|16||8122.5||||||||125||||||||66.67|||||||125||||||
26|0|RFD #5|300 Oberlin Rd|Raleigh|M|1|0|0|0|1|0|0|0|0|1|265|RF|RF05|28|RF05|0|3615.70491027832|125.495140075684|123.411689758301|124.67947966477|9709.70238494873|126.604881286621|122.212753295898|124.483363909599|3512|358|2|121.120148946499|8413|358|2|107.870912399047|1|1||3249|3249|||||||2|1||8122.5|6498||||1624.5|||1|2||3249|66.67|||||||||||||||1|2||8122.5|125|||||||||||||||66.67|||||||53.33||||13.33||
28|0|RFD #7|2100 Glascock St|Raleigh|M|2|0|0|0|0|0|0|0|0|1|267|RF|RF07|30|RF07|0|2520.72622680664|92.3031921386719|89.0716400146484|90.0259366716657|7220.3387298584|93.5220108032227|88.9108428955078|90.25423412323|2344|140|32|83.7387078148978|7024|358|3|87.8041577011347|1|1||1624.5|1624.5|||||||2|1||6498|4873.5||||1624.5|||1|||0||||||||||||||||1|||0||||||||||||||||25|||||||40||||13.33||
"""
    lines_attrs = """cat|MAJORRDS_|ROAD_NAME|MULTILANE|PROPYEAR|OBJECTID|SHAPE_LEN|elev_sum_b30|elev_max_b30|elev_min_b30|elev_mean_b30|aspect_sum_b30|aspect_max_b30|aspect_min_b30|aspect_mean_b30|lc_ncats_b30|lc_mode_b30|lc_null_b30|lc_area_tot_b30|lc_developed_b30|lc_agriculture_b30|lc_herbaceous_b30|lc_shrubland_b30|lc_forest_b30|lc_water_b30|lc_sediment_b30|basin_ncats_b30|basin_mode_b30|basin_null_b30|basin_area_tot_b30|basin_2_b30|basin_4_b30|basin_6_b30|basin_8_b30|basin_10_b30|basin_12_b30|basin_14_b30|basin_16_b30|basin_18_b30|basin_20_b30|basin_22_b30|basin_24_b30|basin_26_b30|basin_28_b30|basin_30_b30
227|229||no|0|227|14736.611903|390630.142501831|152.705459594727|128.046890258789|143.561243109824|543247|359|0|199.649794028233|5|1||269667|138894.75||21118.5|63355.5|46298.25|||3|12||86098.5||||8934.75||77163.75|||||||||
231|233|I-440|yes|2015|231|7616.150435|182309.024833679|146.155258178711|112.242462158203|128.386637206816|316358|359|0|222.787510772789|4|1||142143.75|114527.25||25179.75||2436.75|||3|12||142143.75||||14620.5||127523.25|||||||||
271|273||yes|0|271|13596.482653|160267.10295105|87.7338638305664|67.7318496704102|77.5360923807691|395548|358|0|191.920522822827|4|1||205499.25|179507.25||17869.5||8122.5|||5|4||150266.25||88535.25|9747||4061.25|||47922.75|||||||
272|274|US-1|yes|2005|272|8934.116302|220672.000610352|151.100128173828|113.639060974121|132.774970283003|366523|359|0|220.531536415596|4|1||166511.25|100719|||10559.25|55233|||3|20||166511.25||||||30865.5||||135645.75|||||
273|275|I-40|yes|0|273|12570.330141|222286.1352005|125.628257751465|76.1477203369141|95.606939871183|361544|359|0|155.503096504085|5|1||233115.75|220119.75||1624.5|4061.25|7310.25|||3|14||233115.75||||||25179.75|207936||||||||
277|279|I-40|yes|0|277|13067.640431|313902.62739563|141.195129394531|121.186614990234|129.872828876967|367211|359|0|151.928708516225|3|1||244487.25|200625.75||||43861.5|||3|12||244487.25||||||229054.5|15432.75||||||||
302|304|US-70|yes|0|302|8973.077064|159267.143463135|111.364028930664|72.6773834228516|95.369546983913|234950|359|0|140.689147761781|2|1||164074.5|164074.5|||||||2|16||164074.5||||||||164074.5|||||||
316|318|US-70|yes|0|316|13279.511648|259676.060325623|117.111793518066|97.6227798461914|105.817465495364|460401|359|0|187.612581782259|4|1||249360.75|238801.5||3249||7310.25|||3|26||113715||||||||13808.25|||||99906.75||
319|321|US-401|yes|0|319|14101.465844|259061.38193512|110.767074584961|76.8496322631836|99.6006850961629|559543|359|0|215.126274184826|4|1||259920|214434|||8122.5|37363.5|||5|26||259920||||||||12996||||27616.5|173821.5||45486
"""
    areas_attrs = """cat|AREA|PERIMETER|FULL_HYDRO|FULL_HYDR2|FTYPE|FCODE|NAME|elev_sum_b30|elev_max_b30|elev_min_b30|elev_mean_b30|aspect_sum_b30|aspect_max_b30|aspect_min_b30|aspect_mean_b30|lc_ncats_b30|lc_mode_b30|lc_null_b30|lc_area_tot_b30|lc_developed_b30|lc_agriculture_b30|lc_herbaceous_b30|lc_shrubland_b30|lc_forest_b30|lc_water_b30|lc_sediment_b30|basin_ncats_b30|basin_mode_b30|basin_null_b30|basin_area_tot_b30|basin_2_b30|basin_4_b30|basin_6_b30|basin_8_b30|basin_10_b30|basin_12_b30|basin_14_b30|basin_16_b30|basin_18_b30|basin_20_b30|basin_22_b30|basin_24_b30|basin_26_b30|basin_28_b30|basin_30_b30
6836|1452.65338|274.44519|6837|163418|TUNNEL/CULVERT|47800||3595.60639953613|70.0885620117188|66.9863739013672|69.1462769141564|8546|348|10|164.347192489184|2|1||5685.75|5685.75|||||||2|2||5685.75|5685.75||||||||||||||
7283|23839.00128|610.28163|7284|141156|LAKE/POND|39000||15205.8646240234|145.645538330078|137.747680664062|140.795042815032|21398|359|0|198.131774360038|2|5||8934.75|||||8934.75|||2|12||8934.75||||||8934.75|||||||||
8359|37572.83199|766.19885|8360|141094|RESERVOIR|43600||17046.3508224487|130.871307373047|124.45703125|127.211573301856|31418|328|47|234.469905767868|2|5||12996|||||12996|||2|20||12996||||||||||12996|||||
9240|310579.28177|2298.27976|9241|161228|LAKE/POND|39000||61970.4063644409|121.195388793945|112.610916137695|117.146325830701|86905|358|0|164.283076738027|4|6||50359.5|||15432.75||3249|31677.75||2|30||50359.5|||||||||||||||50359.5
10648|76841.82648|1172.32868|10649|147418|LAKE/POND|39000||24515.0629882812|119.485443115234|113.680084228516|116.738395182292|45729|359|0|217.760982579135|4|5||22743|||812.25|5685.75|16245|||2|22||22743|||||||||||22743||||
10809|116022.17309|1304.41571|10810|73768|LAKE/POND|39000||25037.8391799927|101.827484130859|96.5946502685547|99.3565046825106|60363|359|1|239.536427941114|4|1||23555.25|12183.75||||812.25|10559.25||1|||0|||||||||||||||
"""

    @classmethod
    def setUpClass(cls):
        """Ensures inputdata is present and writable"""
        cls.runModule(
            "v.extract",
            input=cls.inpoint,
            output=cls.inpoint_tmp,
            cats=cls.inpoint_cats,
            overwrite=True,
        )
        cls.runModule(
            "v.extract",
            input=cls.inarea,
            output=cls.inarea_tmp,
            cats=cls.inarea_cats,
            overwrite=True,
        )
        cls.runModule(
            "v.extract",
            input=cls.inline,
            output=cls.inline_tmp,
            cats=cls.inline_cats,
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region and generated data"""
        cls.runModule(
            "g.remove",
            flags="f",
            type="vector",
            name=(cls.inpoint_tmp, cls.inarea_tmp, cls.inline_tmp),
        )
        # use_temp_region() crashes the tests
        # cls.del_temp_region()

    def test_points(self):
        """Test buffering points and flags"""
        self.runModule("g.region", vector=self.inpoint_tmp, align=self.inrast_cont_1)
        self.assertModule(
            "v.rast.bufferstats",
            flags="u",
            input=self.inpoint_tmp,
            raster=[self.inrast_cont_1, self.inrast_cont_2],
            buffers=[30, 50],
            type="points",
            column_prefix=["elev", "aspect"],
            methods=["sum", "maximum", "minimum", "average"],
        )  # , percentile=10, [output=name] [separator=character] [--overwrite] [--help] [--verbose] [--quiet] [--ui]
        bufferstats = SimpleModule(
            "v.rast.bufferstats",
            flags="u",
            input=self.inpoint_tmp,
            raster=[self.inrast_cont_1, self.inrast_cont_2],
            buffers=[30, 50],
            type="points",
            column_prefix=["elev", "aspect"],
            methods=["sum", "maximum", "minimum", "average"],
            output="-",
        )
        bufferstats.run()
        self.assertLooksLike(bufferstats.outputs.stdout, self.points_cont)

        self.runModule("g.region", vector=self.inpoint_tmp, align=self.inrast_label)
        self.assertModule(
            "v.rast.bufferstats",
            flags="t",
            input=self.inpoint_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30, 50],
            type="points",
            column_prefix=["lc", "basin"],
        )
        self.assertModule(
            "v.rast.bufferstats",
            flags="ltu",
            input=self.inpoint_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30, 50],
            type="points",
            column_prefix=["lc", "basin"],
        )
        self.assertModuleFail(
            "v.rast.bufferstats",
            flags="ltpr",
            input=self.inpoint_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30, 50],
            type="points",
            column_prefix=["lc", "basin"],
        )
        self.assertModule(
            "v.rast.bufferstats",
            flags="ltupr",
            input=self.inpoint_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30, 50],
            type="points",
            column_prefix=["lc", "basin"],
        )
        self.assertModule(
            "v.rast.bufferstats",
            flags="ltup",
            input=self.inpoint_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30, 50],
            type="points",
            column_prefix=["lc", "basin"],
            output="{}_points".format(self.output),
        )
        self.assertFileExists("{}_points".format(self.output))

        bufferstats = SimpleModule(
            "v.rast.bufferstats",
            flags="tupl",
            input=self.inpoint_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30, 50],
            type="points",
            column_prefix=["lc", "basin"],
            output="-",
        )
        bufferstats.run()
        self.assertLooksLike(bufferstats.outputs.stdout, self.points_tab)

        bufferstats = SimpleModule("v.db.select", map=self.inpoint_tmp)
        bufferstats.run()
        self.assertLooksLike(bufferstats.outputs.stdout, self.point_attrs)

    def test_lines(self):
        """Test buffering lines"""
        self.runModule("g.region", vector=self.inline_tmp, align=self.inrast_cont_1)
        self.assertModule(
            "v.rast.bufferstats",
            flags="r",
            input=self.inline_tmp,
            raster=[self.inrast_cont_1, self.inrast_cont_2],
            buffers=[30],
            type="lines",
            methods=["sum", "maximum", "minimum", "average"],
            column_prefix=["elev", "aspect"],
        )
        self.assertModule(
            "v.rast.bufferstats",
            flags="u",
            input=self.inline_tmp,
            raster=[self.inrast_cont_1, self.inrast_cont_2],
            buffers=[30],
            type="lines",
            column_prefix=["elev", "aspect"],
            methods=["sum", "maximum", "minimum", "average"],
            output="{}_lines_cont".format(self.output),
        )
        self.assertFileExists("{}_lines_cont".format(self.output))

        self.runModule("g.region", vector=self.inline_tmp, align=self.inrast_label)
        self.assertModule(
            "v.rast.bufferstats",
            flags="tl",
            input=self.inline_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30],
            type="lines",
            column_prefix=["lc", "basin"],
        )

        self.assertModule(
            "v.rast.bufferstats",
            flags="tl",
            input=self.inline_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30],
            type="lines",
            column_prefix=["lc", "basin"],
            output="{}_lines_tab".format(self.output),
        )
        self.assertFileExists("{}_lines_tab".format(self.output))

        bufferstats = SimpleModule("v.db.select", map=self.inline_tmp)
        bufferstats.run()
        self.assertLooksLike(bufferstats.outputs.stdout, self.lines_attrs)

    def test_areas(self):
        """Test clipping point by region"""
        self.runModule("g.region", vector=self.inarea_tmp, align=self.inrast_cont_1)
        self.assertModule(
            "v.rast.bufferstats",
            flags="r",
            input=self.inarea_tmp,
            raster=[self.inrast_cont_1, self.inrast_cont_2],
            buffers=[30],
            type="areas",
            methods=["sum", "maximum", "minimum", "average"],
            column_prefix=["elev", "aspect"],
        )
        self.runModule("g.region", vector=self.inarea_tmp, align=self.inrast_label)
        self.assertModule(
            "v.rast.bufferstats",
            flags="tl",
            input=self.inarea_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30],
            type="areas",
            column_prefix=["lc", "basin"],
        )
        self.assertModule(
            "v.rast.bufferstats",
            flags="tl",
            input=self.inarea_tmp,
            raster=[self.inrast_label, self.inrast_no_label],
            buffers=[30],
            type="areas",
            column_prefix=["lc", "basin"],
            output="{}_area_tab".format(self.output),
        )
        self.assertFileExists("{}_area_tab".format(self.output))

        bufferstats = SimpleModule("v.db.select", map=self.inarea_tmp)
        bufferstats.run()
        self.assertLooksLike(bufferstats.outputs.stdout, self.areas_attrs)


if __name__ == "__main__":
    test()
