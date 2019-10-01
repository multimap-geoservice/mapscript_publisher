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
    #db_data = '9511,9512,9513,9514,9515,9516,9517,9518,9519,9520,9521,9522,9523,9524,9525,9526,9527,9528,9529,9530'
    #db_data = '10667,10668,10669,10670,10671,10672,10673,10674,10675,10676,10677,10678,10679,10680,10681,10682,10683,10684,10685,10686,10687,10688,10689,10690,10691,10692,10693,10694,10695,10696,10697,10698,10699,10700,10701,10702,10703,10704,10705,10706,10707,10708'
    #db_data = '10971,10972,10973,10974,10975,10976,10977,10978,10979,10980,10981,10982,10983,10984,10985,10986,10987,10988,10989,10990,10991,10992,10993,10875,10876,10877,10878,10879,10880,10881,10882,10883,10884,10885,10886,10887,10888,10889,10890,10891,10892,10893'
    db_data = '10739,10740,10741,10742,10743,10744,10745,10746,10747,10748,10749,10750,10751,10752,10753,10754,10755,10756,10757,10758,10759,10760,10761,10762,10763,10764,10765,10766,10767,10768,10769,10770,10771,10772,10773,10774,10775,10776,10777,10778,10779,10780'
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
