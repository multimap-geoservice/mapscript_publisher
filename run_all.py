import os, sys
from map_pub import MapsWEB


if __name__ == "__main__":
    db_host = sys.argv[1]
    maps_path = "{}/GIS/mapserver/debug/all_maps".format(os.environ["HOME"])
    srcs = [
        {
            "type": "fs",
            "path": maps_path,
        }
    ]
    web = MapsWEB(srcs=srcs)
    #web.serial_src += srcs
    web.multi = True
    web.debug = 2
    web()
