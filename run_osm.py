
import sys
from map_pub import BuildMapRes, PubMapWEB

if __name__ == "__main__":
    """
    script_name db_host map_name
    """
    mapjsonfile = "./maps/osm.json"
    #mapjsonfile = "./maps/osm_utf8.json"
    fontsfile = "./maps/fonts/fonts.lst"
    db_host = sys.argv[1]
    db_port = sys.argv[2]
    map_name = sys.argv[3]
    debug_path = "./debug"
    db_connection = "host={host} dbname={name} user=gis password=gis port={port}".format(
        host=db_host,
        port=db_port, 
        name=map_name, 
    )
    
    # build map
    builder = BuildMapRes()
    builder.load4file(mapjsonfile)
    #builder.debug = True
    builder.debug = '{}/build.log'.format(debug_path)
    builder.mapjson["VARS"]["db_connection"] = db_connection 
    builder.mapjson["VARS"]["name"] = "ОСМ_{}".format(map_name) 
    builder.mapjson["VARS"]["wms_title"] = "Open Street Map {}".format(map_name) 
    builder.mapjson["VARS"]["fontset"] = fontsfile 
    builder.build()
    
    # run web
    pubmap = PubMapWEB(builder.mapdict)
    pubmap.debug_json_file(debug_path)
    pubmap.debug_python_mapscript(debug_path)
    pubmap.debug_map_file(debug_path)
    pubmap.wsgi()
