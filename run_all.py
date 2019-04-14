import os, sys
from map_pub import MapsAPI


if __name__ == "__main__":
    db_host = sys.argv[1]
    maps_path = "{}/GIS/mapserver/debug/all_maps".format(os.environ["HOME"])
    srcs = [
        {
            "type": "fs",
            "path": maps_path,
        }
    ]
    web = MapsAPI(srcs=srcs)
    #web.serial_src += srcs
    web.multi = True
    web.debug = 2
    #web.log = "{}/out.log".format(maps_path)
    web.full_serializer()
    web()
