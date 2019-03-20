from mapbuilder import BuildMap
from mapweb import PubMapWEB
import json

if __name__ == "__main__":
    mapjsonfile = "./maps/osm.json"
    debug_path = '../debug'
    
    # build map
    builder = BuildMap()
    builder.load_mapjson(mapjsonfile)
    #builder.debug = True
    builder.debug = '{}/build.log'.format(debug_path)
    builder.build()
    
    # pub map
    pubmap = PubMapWEB(builder.mapdict)
    pubmap.debug_json_file(debug_path)
    pubmap.debug_python_mapscript(debug_path)
    pubmap.debug_map_file(debug_path)
    pubmap.wsgi()
