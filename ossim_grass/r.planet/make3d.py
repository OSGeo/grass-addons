def make3d(tile, elev, outdir):
    makedir(outdir)
    kwl = 'elev.kwl'
    template = 'igen.slave_tile_buffers: 5 \n'
    template += 'igen.tiling.type: ossimTiling \n'
    template += 'igen.tiling.tiling_distance: 1 1 \n'
    template += 'igen.tiling.tiling_distance_type: degrees \n'
    template += 'igen.tiling.delta: %s %s \n' % (tile,tile)
    template += 'igen.tiling.delta_type: total_pixels \n'
    template += 'igen.tiling.padding_size_in_pixels: 0 0 \n'
    template += 'object1.description: \n'
    template += 'object1.enabled:  1 \n'
    template += 'object1.id:  1 \n'
    template += 'object1.object1.description: \n'  
    template += 'object1.object1.enabled:  1 \n'
    template += 'object1.object1.id:  2 \n'
    template += 'object1.object1.resampler.magnify_type:  bilinear \n'
    template += 'object1.object1.resampler.minify_type:  bilinear \n'
    template += 'object1.object1.type:  ossimImageRenderer \n'
    template += 'object1.object2.type:  ossimCastTileSourceFilter \n'
    template += 'object1.object2.scalar_type: ossim_sint16 \n'
    template += 'object1.type:  ossimImageChain \n'
    template += 'object2.type: ossimGeneralRasterWriter \n'
    template += 'object2.byte_order: big_endian \n'
    template += 'object2.create_overview: false \n'
    template += 'object2.create_histogram: false \n'
    template += 'object2.create_external_geometry: false \n'
    template += 'product.projection.type: ossimEquDistCylProjection \n'
    open(kwl,'w').write(template)
    instr = 'ossim-orthoigen'
    instr += ' --tiling-template '
    instr += kwl
    instr +=' --view-template '
    instr += kwl
    instr +=' --writer-template '
    instr += kwl
    instr +=' --chain-template '
    instr += kwl
    instr += ' %s ' % elev 
    instr += '%s' % outdir
    instr +='/%SRTM%'
    return instr

# os.system(instr)

