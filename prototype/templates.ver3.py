
#import mapscript
from mapublisher import PubMap
import json


def upd_temp(_super, _sub):
    """
    intheritance and update template dict
    _super - template dict or json ?
    _sub - modify template dict or json ?
    """
    _modify = _super.copy()
    _modify.update(_sub)
    return _modify

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

layer_dict = {
    'OBJ': 'mapscript.layerObj',  #name object of mapscript
    'name': None,  # if data is None to return Exeption Template Error
    'status': {'OBJ': 'mapscript.MS_ON'}, 
    'type': {'OBJ': 'mapscript.MS_LAYER_RASTER'}, 
    'data': None, 
    'units': {'OBJ': 'mapscript.MS_METERS'}, 
    'tileitem': 'location', 
    'setProcessing': [
        'NODATA=-999', 
        'SCALE=AUTO',
    ] 
}

map_dict = {
    'OBJ': 'mapscript.mapObj', #name object of mapscript
    'name': 'Rasters',  # if variable to key_name = data
    'setSize': [[932, 870]],  # if function and data len > 1 to key_name(*data)
    'setExtent': [[630027.311698621,5328559.3147829,657977.792312785,5354655.55868648]], 
    'units': {'OBJ': 'mapscript.MS_DD'},  #-> exec("a.units = eval('mapscript.MS_DD')")
    'imagecolor.setRGB': [[255,255,255]], 
    'setProjection': ('init=epsg:32638'), # if function and data len = 1 to key_name(*data)
    'web.metadata.set': [  # first [ to loop data -> key_name
        ['ows_enable_request', '*'],
        ['labelcache_map_edge_buffer', '-10'], 
        ['wms_srs', ' '.join(wms_projs)], 
        ['wms_title', 'Rasters'], 
        ['wms_enable_request', '*'],
    ], 
    'SUB_OBJ': [  # this(self) MS_OBJ to next MS_OBJ ex: layerObj(mapObj)
        upd_temp(
            layer_dict,
            {
                'name': 'rst1',
                'data': 'PG: rst1',
                'metadata.set': [['wms_abstract',"Raster 1"]],  #two [[ = (
                
            }
        ), 
        upd_temp(
            layer_dict,
            {
                'name': 'rst2',
                'data': 'PG: rst2',
                'metadata.set': [['wms_abstract',"Raster 2"]], 
                
            }
        ), 
    ],
}    

    
if __name__ == '__main__':
    #_json = json.dumps(map_dict, sort_keys=True, indent=4, separators=(',', ': '))
    #print _json
    debug_path = '/home/oldbay/GIS/mapserver/debug'
    _map = PubMap()
    _map.mapdict = map_dict
    _map.get_json(debug_path)
    _map.get_mapscript(debug_path)
    _map.get_mapfile(debug_path)
    

