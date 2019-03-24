
import mapscript

def initMap():
    # create a new mapfile from scratch
    mymap = mapscript.mapObj()
    mymap.name = 'Rasters'
    mymap.setSize(932, 870)
    mymap.setExtent(630027.311698621,5328559.3147829,657977.792312785,5354655.55868648)
    mymap.units = mapscript.MS_DD
    mymap.imagecolor.setRGB(255,255,255)
    mymap.setProjection('init=epsg:32638')
    
    #all web metadata
    mymap.web.metadata.set('ows_enable_request', '*')
    mymap.web.metadata.set('labelcache_map_edge_buffer', '-10')
    
    #wms web metadata
    wms_projs = [
        'EPSG:32638', 
        'EPSG:4326',
        'EPSG:3857',
        'EPSG:2154',
        'EPSG:310642901',
        'EPSG:4171',
        'EPSG:310024802',
        'EPSG:310915814',
        'EPSG:310486805',
        'EPSG:310702807',
        'EPSG:310700806',
        'EPSG:310547809',
        'EPSG:310706808',
        'EPSG:310642810',
        'EPSG:310642801',
        'EPSG:310642812',
        'EPSG:310032811',
        'EPSG:310642813',
        'EPSG:2986'
    ]
    mymap.web.metadata.set('wms_srs', ' '.join(wms_projs))
    mymap.web.metadata.set('wms_title', 'Rasters')
    mymap.web.metadata.set('wms_enable_request', '*')
    
    
    # create connect data
    pg_host = 'host={}'.format('localhost')
    pg_port = 'port={}'.format(5432)
    pg_base = 'dbname=\'{}\''.format('dinamo')
    pg_user = 'user=\'{}\''.format('gis')
    pg_pass = 'password=\'{}\''.format('gis')
    pg_shema = 'schema=\'{}\''.format('public')
    pg_table = 'table=\'{}\''.format('rasters')
    pg_column = 'column=\'{}\''.format('geom')
    pg_where = 'where=\'{}\''.format('rid=1')
    pg_mode = 'mode=\'{}\''.format(2)
    pg_data_str = 'PG:{0} {1} {2} {3} {4} {5} {6} {7} {8} {9}'.format(
        pg_host, 
        pg_port,
        pg_base,
        pg_user,
        pg_pass,
        pg_shema,
        pg_table,
        pg_column,
        pg_where,
        pg_mode
    )
    
    # create a layer for the raster
    layer1 = mapscript.layerObj(mymap)
    layer1.name = 'rst1'
    layer1.status = mapscript.MS_ON
    layer1.type = mapscript.MS_LAYER_RASTER
    layer1.data = pg_data_str
    layer1.units = mapscript.MS_METERS
    layer1.tileitem = 'location'
    #layer1.setProjection('init=epsg:32638')

    # layer wms metadata
    #layer1.metadata.set('wms_title', 'rst1')
    layer1.metadata.set('wms_abstract',"Raster 1")
    #layer1.metadata.set('ows_enable_request', '*')
    #layer1.metadata.set('wms_format','image/png')
    #layer1.metadata.set('wms_srs', ' '.join(wms_projs))
    #layer1.metadata.set('wms_srs',"EPSG:32638")
      
    # group
    #layer1.metadata.set('wms_group_title','frames')  #group title one layer
    #layer1.metadata.set('wms_layer_group','/frames/rst1')
    #layer1.group = 'frames'

    # layer processing
    layer1.setProcessing('NODATA=-999')
    layer1.setProcessing('SCALE=AUTO')
   
    #""" 
    #Layer2 
    
    pg_where = 'where=\'{}\''.format('rid=2')
    pg_data_str = 'PG:{0} {1} {2} {3} {4} {5} {6} {7} {8} {9}'.format(
        pg_host, 
        pg_port,
        pg_base,
        pg_user,
        pg_pass,
        pg_shema,
        pg_table,
        pg_column,
        pg_where,
        pg_mode
    )
    # create a layer for the raster
    layer2 = mapscript.layerObj(mymap)
    layer2.name = 'rst2'
    layer2.status = mapscript.MS_ON
    layer2.type = mapscript.MS_LAYER_RASTER
    layer2.data = pg_data_str
    layer2.units = mapscript.MS_METERS
    layer2.tileitem = 'location'
    #layer2.setProjection('init=epsg:32638')

    # layer wms metadata
    #layer2.metadata.set('wms_title', 'rst2')
    layer2.metadata.set('wms_abstract',"Raster 2")
    #layer2.metadata.set('wms_enable_request','*')
    #layer2.metadata.set('wms_format','image/png')
    #layer2.metadata.set('wms_srs', ' '.join(wms_projs))
    #layer2.metadata.set('wms_srs',"EPSG:32638")
    
    # group
    #layer2.metadata.set('wms_layer_group','/frames/rst2')
    #layer2.group = 'frames'

    # layer processing
    layer2.setProcessing('NODATA=-999')
    layer2.setProcessing('SCALE=AUTO')
    #"""
   
    return mymap
    
if __name__ == '__main__':
    mapfile = initMap()
    mapfile.save('debug.map')