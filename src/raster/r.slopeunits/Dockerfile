FROM osgeo/grass-gis:releasebranch_8_4-alpine

RUN apk add coreutils gawk

COPY . /workdir/r.slopeunits

# RUN grass --tmp-location EPSG:4326 --exec g.extension extension=r.slopeunits url=/workdir/r.slopeunits

RUN grass --tmp-project EPSG:4326 --exec g.extension extension=r.slopeunits.create url=/workdir/r.slopeunits/r.slopeunits.create
RUN grass --tmp-project EPSG:4326 --exec g.extension extension=r.slopeunits.clean url=/workdir/r.slopeunits/r.slopeunits.clean
RUN grass --tmp-project EPSG:4326 --exec g.extension extension=r.slopeunits.metrics url=/workdir/r.slopeunits/r.slopeunits.metrics
RUN grass --tmp-project EPSG:4326 --exec g.extension extension=r.slopeunits.optimize url=/workdir/r.slopeunits/r.slopeunits.optimize
