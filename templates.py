
#import mapscript
import json
from jinja2 import Environment, DictLoader
import ast

from interface import gdal2pg
from mapublisher import PubMap

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
wms_srs = ' '.join(wms_projs)

layer_dict = """
{
    "OBJ": "mapscript.layerObj",
    "name": "{{layer_vars['name']}}",
    "status": {"OBJ": "mapscript.MS_ON"}, 
    "type": {"OBJ": "mapscript.MS_LAYER_RASTER"}, 
    "data": "{{layer_vars['data']}}",
    "units": {"OBJ": "mapscript.MS_METERS"},
    "tileitem": "location",
    "setProcessing": [
        "NODATA=-999", 
        "SCALE=AUTO",
    ], 
    "metadata.set": [
        [
            "wms_abstract",
            "{{layer_vars['wms_abstract']}}"
        ]
    ],
}
"""

map_dict = """
{
    "OBJ": "mapscript.mapObj",
    "name": "{{name}}",
    "imagecolor.setRGB": [{{imagecolor}}],
    "setExtent": [{{extent}}],
    "setProjection": "init=epsg:{{epsg_id}}",
    "setSize": [{{size}}],
    "units": {
        "OBJ": "mapscript.MS_DD"
    },
    "web.metadata.set": [
        [
            "ows_enable_request",
            "*"
        ],
        [
            "labelcache_map_edge_buffer",
            "-10"
        ],
        [
            "wms_srs", "{{wms_srs}}"
        ],
        [
            "wms_title",
            "Rasters"
        ],
        [
            "wms_enable_request",
            "*"
        ]
    ],
    "SUB_OBJ": [
        {% for layer_vars in layer_dicts %}
            {% include layer_vars['TEMP'] %},
        {% endfor %}
    ],
}
"""

    
if __name__ == '__main__':
    
    name = 'rasters'
    imagecolor = [255, 255, 255] 
    extent = [
        630027.311698621,
        5328559.3147829,
        657977.792312785,
        5354655.55868648
    ]
    size = [932, 870]
    epsg_id = 32638
    gdal_pgdata_str = gdal2pg(
        #host = 'localhost', 
        #port = 5432, 
        #base = 'dinamo', 
        #user = 'gis', 
        #password='gis', 
        #shema = 'public', 
        table = 'rasters', 
        column = 'geom', 
        #where = 'rid=%s', 
        mode = 2
    )
    gdal_pgdata_str.db_keys['where'] = 'rid=%s'
    layer_dicts = [
        {
            'TEMP': 'raster_layer.json',
            'name': 'rst1',
            'data': gdal_pgdata_str() % str(1),
            'wms_abstract': 'raster1',
        }, 
        {
            'TEMP': 'raster_layer.json',
            'name': 'rst2',
            'data': gdal_pgdata_str() % str(2),
            'wms_abstract': 'raster2',
        }, 
    ]
    
    env = Environment(
        loader=DictLoader(
            {
                'map.json': map_dict, 
                'raster_layer.json': layer_dict, 
            }
        )
    )
    template = env.get_template('map.json')
    map_txt = template.render(
        name=name,
        imagecolor=imagecolor, 
        extent=extent, 
        size=size,
        epsg_id=epsg_id, 
        wms_srs=wms_srs, 
        layer_dicts=layer_dicts
    )
    #print map_txt
    #map_dict.replace('\n', '')
    map_dict = ast.literal_eval(map_txt)

    _json = json.dumps(map_dict, sort_keys=True, indent=4, separators=(',', ': '))
    print _json
    
    debug_path = '/home/oldbay/GIS/mapserver/debug'
    _map = PubMap()
    _map.mapdict = map_dict
    _map.debug_json_file(debug_path)
    _map.debug_python_mapscript(debug_path)
    _map.debug_map_file(debug_path)
    

