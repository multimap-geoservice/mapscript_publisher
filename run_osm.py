import os, sys
from map_pub import BuildMapRes, PubMapWEB

if __name__ == "__main__":
    mapjsonfile = "./maps/osm.json"
    fontsfile = "./maps/fonts/fonts.lst"
    db_host = sys.argv[1]
    #db_host = "localhost"
    debug_path = "{}/GIS/mapserver/debug".format(os.environ["HOME"])
    db_connection = "host={} dbname=RU-SPE user=gis password=gis port=5432".format(
        db_host
    )
    
    # build map
    builder = BuildMapRes()
    builder.load4file(mapjsonfile)
    #builder.debug = True
    builder.debug = '{}/build.log'.format(debug_path)
    builder.mapjson["VARS"]["db_connection"] = db_connection 
    builder.mapjson["VARS"]["fontset"] = fontsfile 
    builder.build()
    
    # pub map
    pubmap = PubMapWEB(builder.mapdict)
    pubmap.debug_json_file(debug_path)
    pubmap.debug_python_mapscript(debug_path)
    pubmap.debug_map_file(debug_path)
    pubmap.wsgi()
