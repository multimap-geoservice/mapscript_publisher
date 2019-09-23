# -*- coding: utf-8 -*-
# encoding: utf-8

import os, sys
from map_pub import BuildMapRes, PubMapWEB

if __name__ == "__main__":
    """
    script_name db_host
    """
    mapjsonfile = "./maps/geodb_sxf.json"
    db_host = sys.argv[1]
    #db_host = "localhost"
    db_data = '(9511,9512,9513,9514,9515,9516,9517,9518,9519,9520,9521,9522,9523,9524,9525,9526,9527,9528,9529,9530)'
    debug_path = "{}/GIS/mapserver/debug".format(os.environ["HOME"])
    db_connection = "host={0} dbname=sxf user=innouser password=innopass port=5432".format(
        db_host 
    )
    
    # build map
    builder = BuildMapRes()
    builder.load4file(mapjsonfile)
    #builder.debug = True
    builder.debug = '{}/build.log'.format(debug_path)
    builder.mapjson["VARS"]["db_connection"] = db_connection 
    builder.mapjson["VARS"]["data"] = db_data 
    builder.mapjson["VARS"]["name"] = u"SXF" 
    builder.mapjson["VARS"]["title"] = u"SXF of GeoDB" 
    builder.build()
    
    # run web
    pubmap = PubMapWEB(builder.mapdict)
    pubmap.debug_json_file(debug_path)
    pubmap.debug_python_mapscript(debug_path)
    pubmap.debug_map_file(debug_path)
    pubmap.wsgi()
