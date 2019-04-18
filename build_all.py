import os, sys
from map_pub import BuildMapRes
import time


def init_map(template, _map, map_type, **kwargs):
    print ("BUILD: {}".format(_map))
    
    # init builder
    builder = BuildMapRes()
    builder.load4file(template)
    
    # osm
    if builder.mapjson["VARS"].has_key('db_connection'):
        db_connection = "host={0} dbname={1} user={2} password={3} port=5432".format(
            kwargs["host"], 
            _map, 
            kwargs["user"], 
            kwargs["password"], 
        )
        builder.mapjson["VARS"]["db_connection"] = db_connection 
        builder.mapjson["VARS"]["name"] = "osm_{}".format(_map) 
        builder.mapjson["VARS"]["wms_title"] = "Open Street Map {}".format(_map) 
        builder.mapjson["VARS"]["fontset"] = "{}/fonts/fonts.lst".format(_map)  #!!!!! 
    
    if map_type == "maps_path" or map_type == "maps_path_db":
        map_full_path = "{0}/{1}.json".format(kwargs['maps_path'], _map)
    
    if map_type == "maps_db" or map_type == "maps_path_db":
        db_connect = {
            "host": kwargs['host'], 
            "dbname": kwargs['dbname'],
            "user": kwargs['user'],
            "password": kwargs['password'],
        }
        if map_type == 'maps_path_db':
            db_connect['path'] = map_full_path

    # build map
    if map_type == "maps_path":
        builder.save2file(
            path=map_full_path
        )
    elif map_type == "maps_db" or map_type == "maps_path_db":
        builder.save2pgsql(
            table=kwargs['maps_table'], 
            name=_map, 
            col_name=kwargs['maps_col_name'], 
            col_cont=kwargs['maps_col_cont'],
            columns=kwargs['columns'], 
            **db_connect
        )


if __name__ == "__main__":
    db = {
        "host": sys.argv[1], 
        "dbname": "maps",
        "user": "gis",
        "password": "gis",
        "maps_table": "maps",
        "maps_col_name": "name",
        "maps_col_cont": "cont",
        "maps_path": "{}/GIS/mapserver/debug/all_maps".format(os.environ["HOME"]), 
        "columns": {
            "int_data": 1,
            "float_data": 0.5,
            "text_data": "text",
            "timestamp": "now::timestamp",
            }
    }
    template = "./maps/osm.json"
    maps = {
        "maps_path": [
            "RU-SPE", 
        ], 
        "maps_path_db": [
            "RU-KL", 
        ], 
        "maps_db": [
            "RU-LEN", 
        ], 
    }
    for map_type in maps:
        for _map in maps[map_type]: 
            init_map(template, _map, map_type, **db)
