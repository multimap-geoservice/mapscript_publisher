import os, sys
from map_pub import BuildMap, PubMap, MapsWEB

debug_path = "{}/GIS/mapserver/debug".format(os.environ["HOME"])
db_host = sys.argv[1]
#db_host = "localhost"

def init_map(mapjsonfile):
    print ("LOAD: {}".format(mapjsonfile))
    
    # init builder
    builder = BuildMap()
    builder.load_mapjson(mapjsonfile)
    
    # osm
    if builder.mapjson["VARS"].has_key('db_connection'):
        db_connection = "host={} dbname=RU-SPE user=gis password=gis port=5432".format(
            db_host
        )
        builder.mapjson["VARS"]["db_connection"] = db_connection 
    # rasters
    if builder.mapjson["VARS"].has_key('db_host'):
        builder.mapjson["VARS"]["db_host"] = db_host 
    
    # debug builder
    name = mapjsonfile.split("/")[-1].split(".")[0]
    debug_all_path = "{0}/{1}".format(debug_path, name)
    #builder.debug = True
    builder.debug = '{}/build.log'.format(debug_all_path)
    
    # build map
    builder.build()
    
    # pub map
    pubmap = PubMap(builder.mapdict)
    pubmap.debug_json_file(debug_all_path)
    pubmap.debug_python_mapscript(debug_all_path)
    pubmap.debug_map_file(debug_all_path)
    
    return pubmap


if __name__ == "__main__":
    maps = [
        "./maps/osm.json",
        "./maps/raster.json", 
    ]
   
    web = MapsWEB()
    for mapjson in maps:
        mapobj =  init_map(mapjson)
        web.get_map(mapobj())
    web()
