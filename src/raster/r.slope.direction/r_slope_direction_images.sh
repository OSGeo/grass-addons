#########################################
# r.slope.direction
#########################################
# Set the computational region
g.region -p raster=elevation

# Convert street network to raster and assign pixels direction value
r.watershed elevation=elevation accumulation=faccum drainage=fdir

v.to.rast input=streets_wake type=line output=streets_wake use=dir

in_dir=streets_wake
tmp_dir=streets_wake_dir
out_dir=streets_wake_dir8

r.mapcalc --o expression="${tmp_dir}=if(int(round(${in_dir}/45.0))==0,8, \
int(round(${in_dir}/45.0)))"
r.mapcalc --o expression="${out_dir}=if(${tmp_dir}==8,if(isnull(${tmp_dir}[0,1]), \
if(isnull(${tmp_dir}[-1,1]), \
if(isnull(${tmp_dir}[1,1]), \
if(isnull(${tmp_dir}[-1,0]), \
if(isnull(${tmp_dir}[1,0]),8,6),2),7),1),8) \
,if(${tmp_dir}==7,if(isnull(${tmp_dir}[1,1]), \
if(isnull(${tmp_dir}[0,1]), \
if(isnull(${tmp_dir}[1,0]), \
if(isnull(${tmp_dir}[-1,1]), \
if(isnull(${tmp_dir}[1,-1]),7,5),1),6),8),7) \
,if(${tmp_dir}==6,if(isnull(${tmp_dir}[1,0]), \
if(isnull(${tmp_dir}[1,1]), \
if(isnull(${tmp_dir}[1,-1]), \
if(isnull(${tmp_dir}[0,1]), \
if(isnull(${tmp_dir}[0,-1]),6,4),8),5),7),6) \
,if(${tmp_dir}==5,if(isnull(${tmp_dir}[1,-1]), \
if(isnull(${tmp_dir}[1,0]), \
if(isnull(${tmp_dir}[0,-1]), \
if(isnull(${tmp_dir}[1,1]), \
if(isnull(${tmp_dir}[-1,-1]),5,4),7),4),6),5) \
,if(${tmp_dir}==4,if(isnull(${tmp_dir}[0,-1]), \
if(isnull(${tmp_dir}[1,-1]), \
if(isnull(${tmp_dir}[-1,-1]), \
if(isnull(${tmp_dir}[1,0]), \
if(isnull(${tmp_dir}[-1,0]),4,3),6),3),5),4) \
,if(${tmp_dir}==3,if(isnull(${tmp_dir}[-1,-1]), \
if(isnull(${tmp_dir}[0,-1]), \
if(isnull(${tmp_dir}[-1,0]), \
if(isnull(${tmp_dir}[1,-1]), \
if(isnull(${tmp_dir}[-1,-1]),1,3),5),2),4),3) \
,if(${tmp_dir}==2,if(isnull(${tmp_dir}[-1,0]), \
if(isnull(${tmp_dir}[-1,-1]), \
if(isnull(${tmp_dir}[-1,1]), \
if(isnull(${tmp_dir}[0,-1]), \
if(isnull(${tmp_dir}[0,1]),2,8),4),1),3),2) \
,if(${tmp_dir}==1,if(isnull(${tmp_dir}[-1,1]), \
if(isnull(${tmp_dir}[-1,0]), \
if(isnull(${tmp_dir}[0,1]), \
if(isnull(${tmp_dir}[-1,-1]), \
if(isnull(${tmp_dir}[1,1]),1,7),3),8),2),1) \
,null()))))))))"

# Compute slope of the streets for three different step-size (neighborhood)
r.slope.direction -a elevation=elevation direction=streets_wake_dir8 steps=1,5,13 output=streets_wake_slope_1,streets_wake_slope_5,streets_wake_slope_13


# Generate image
#d.mon wx0
for out in streets_wake_slope_1 streets_wake_slope_5 streets_wake_slope_13
do
output=r_slope_direction_${out}.png

d.mon --o start=cairo width=600  height=600 bgcolor=white output=$output
d.rast ${out}
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim $output
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../../utils/svn-image.sh $output
done

# Compute slope of the streets for three different step-size (neighborhood)
r.slope.direction -a elevation=elevation direction=fdir steps=1,5,13 output=fdir_slope_1,fdir_slope_5,fdir_slope_13

# Compute hillshade as background
r.relief --o input=elevation output=hillshade

# Generate image
g.region -p n=225230 s=221050 w=633990 e=639570

#d.mon wx0
for out in fdir_slope_1 fdir_slope_5 fdir_slope_13
do
output=r_slope_direction_${out}.png

d.mon --o start=cairo width=600  height=600 bgcolor=none output=$output
d.rast hillshade
d.rast ${out}
d.mon stop=cairo
# save image to files (manually)
# crop the background using Gimp or ImageMagic
mogrify -trim $output
# some bounding box problems noticed when opening mogrify result in Gimp

# Optimize for SVN
../../../../utils/svn-image.sh $output
done
