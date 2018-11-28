
import mapscript
import json
import inspect


def upd_temp(_super, _sub):
    """
    intheritance and update template dict
    _super - template dict or json ?
    _sub - modify template dict or json ?
    """
    _modify = _super.copy()
    _modify.update(_sub)
    return _modify



# Create mapscript mapfile Object

"""
OBJ = name of class for this dict
OBJ_VAR = class object for this class
SUB_OBJ = point transfer this object to another object
OBJS = all objects mapscript in list - map index 0
"""
OBJS = []

def line_processing(OBJ, method, value):
    #processing script line
    """
    test type
    
    import inspect
    a = mapscript.mapObj()
    
    type(a.name)
    <type 'str'>
    inspect.ismethod(a.name)
    False
    
    type(a.setSize)
    <type 'instancemethod'>
    inspect.ismethod(a.setSize)
    True
    """
    # tests value
    if isinstance(value, str):
        value = '\'{}\''.format(value)
    elif isinstance(value, dict):
        if value.has_key('OBJ'):
            value = 'eval(\'{}\')'.format(value['OBJ'])
    
    # test assigment
    if inspect.ismethod(eval('{0}.{1}'.format(OBJ, method))):
        if isinstance(value, dict):
            assigment = '(**{})'.format(value)
        elif isinstance(value, list):
            assigment = '(*{})'.format(value)
        else:
            assigment = '({})'.format(value)
    else:
        assigment = ' = {}'.format(value)
    
    # create script string
    script_str = '{0}.{1}{2}'.format(
        OBJ, 
        method, 
        assigment
    )
    print script_str
    exec(script_str)


def temp_engine(_dict, SUB_OBJ=''):
    if not _dict.has_key('OBJ_VAR'):
        # add OBJ Variable to OBJS list
        str_obj = '{0}({1})'.format(_dict['OBJ'], SUB_OBJ)
        OBJS.append(eval(str_obj))
        _dict['OBJ_VAR'] = 'OBJS[{}]'.format(len(OBJS) - 1)
    for line in _dict:
        if line == 'SUB_OBJ':
            # recursive function for Sub Objects
            for subline in _dict[line]:
                temp_engine(subline, _dict['OBJ_VAR'])
        elif line not in ['OBJ', 'OBJ_VAR']:
            # got to lines for processing
            if type(_dict[line]) == list:
                # loop in list
                for subline in _dict[line]:
                    line_processing(
                        _dict['OBJ_VAR'], 
                        line,
                        subline
                    )
            else:
                # one line
                line_processing(
                    _dict['OBJ_VAR'], 
                    line,
                    _dict[line]
                )

    
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

layer_obj = {
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

map_obj = {
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
            layer_obj,
            {
                'name': 'rst1',
                'data': 'PG: rst1',
                'metadata.set': [['wms_abstract',"Raster 1"]],  #two [[ = (
                
            }
        ), 
        upd_temp(
            layer_obj,
            {
                'name': 'rst2',
                'data': 'PG: rst2',
                'metadata.set': [['wms_abstract',"Raster 2"]], 
                
            }
        ), 
    ],
}    


    
if __name__ == '__main__':
    #print map_obj
    print json.dumps(map_obj, sort_keys=True, indent=4, separators=(',', ': '))
    temp_engine(map_obj)
    OBJS[0].save('templates/debug.map')
    

