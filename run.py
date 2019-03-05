from mapbuilder import BuildMap
from mapublisher import PubMap

if __name__ == "__main__":
    mapjsonfile = "./maps/raster.json"
    builder = BuildMap()
    builder.load_mapjson(mapjsonfile)
    builder.debug_mapjson()
    builder.build()
    print "IMODS"
    print builder.IMODS
    print "VARS"
    print builder.VARS
    print 'vars_queue'
    print builder.vars_queue
    print "TEMPS"
    print builder.TEMPS
    print "MAP"
    print builder.MAP