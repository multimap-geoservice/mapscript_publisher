import os, sys
from multi_map import LightAPI


if __name__ == "__main__":
    db_host = sys.argv[1]
    maps_path = "{}/GIS/mapserver/debug/all_maps/fs".format(os.environ["HOME"])
    srcs = [
        {
            "type": "fs",
            "path": maps_path,
            "enable": True,
        }, 
        {
            "type": "pgsql", 
            "connect": {
                "host": db_host,
                "dbname": "maps",
                "user": "gis",
                "password": "gis",
            }, 
            "query": """
                select name as map_name,
                       cont as map_cont
                from maps
            """,
            "enable": True,
        }
    ]
    web = LightAPI(srcs=srcs)
    #web.serial_src += srcs
    web.multi = True
    web.debug = 2
    #web.log = "{}/out.log".format(maps_path)
    #web.full_serializer()
    web()
