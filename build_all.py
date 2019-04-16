import os, sys
from map_pub import BuildMapSave


def init_map(template, _map, db_host, maps_path):
    print ("BUILD: {}".format(_map))
    
    # init builder
    builder = BuildMapRes()
    builder.load_mapjson(template)
    
    # osm
    if builder.mapjson["VARS"].has_key('db_connection'):
        db_connection = "host={0} dbname={1} user=gis password=gis port=5432".format(
            db_host, 
            _map
        )
        builder.mapjson["VARS"]["db_connection"] = db_connection 
        builder.mapjson["VARS"]["name"] = "osm_{}".format(_map) 
        builder.mapjson["VARS"]["wms_title"] = "Open Street Map {}".format(_map) 
    
    # debug builder
    map_full_path = "{0}/{1}.json".format(maps_path, _map)
    
    # build map
    builder.save2file(path=map_full_path)


if __name__ == "__main__":
    db_host = sys.argv[1]
    maps_path = "{}/GIS/mapserver/debug/all_maps".format(os.environ["HOME"])
    template = "./maps/osm.json"
    maps = [
        "RU-SPE", 
        "RU-LEN", 
        "RU-KL", 
    ]
   
    for _map in maps:
        mapobj =  init_map(template, _map, db_host, maps_path)
