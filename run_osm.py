# -*- coding: utf-8 -*-
# encoding: utf-8

import os, sys
from map_pub import BuildMapRes, PubMapWEB

if __name__ == "__main__":
    """
    script_name db_host map_name
    """
    mapjsonfile = "./maps/osm_utf8.json"
    fontsfile = "./maps/fonts/fonts.lst"
    db_host = sys.argv[1]
    map_name = sys.argv[2]
    #db_host = "localhost"
    debug_path = "{}/GIS/mapserver/debug".format(os.environ["HOME"])
    db_connection = "host={0} dbname={1} user=gis password=gis port=5432".format(
        db_host, 
        map_name
    )
    
    # build map
    builder = BuildMapRes()
    builder.load4file(mapjsonfile)
    #builder.debug = True
    builder.debug = '{}/build.log'.format(debug_path)
    builder.mapjson["VARS"]["db_connection"] = db_connection 
    builder.mapjson["VARS"]["name"] = "osm_{}".format(map_name) 
    builder.mapjson["VARS"]["wms_title"] = "Open Street Map {}".format(map_name) 
    builder.mapjson["VARS"]["fontset"] = fontsfile 
    builder.build()
    
    # run web
    pubmap = PubMapWEB(builder.mapdict)
    pubmap.debug_json_file(debug_path)
    pubmap.debug_python_mapscript(debug_path)
    pubmap.debug_map_file(debug_path)
    pubmap.wsgi()
