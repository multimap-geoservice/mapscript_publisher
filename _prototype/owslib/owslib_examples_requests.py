# -*- coding: utf-8 -*-
# encoding: utf-8

import json

def json_format(cont):
    print json.dumps(
        cont,
        sort_keys=True,
        indent=4,
        separators=(',', ': '), 
        ensure_ascii=False, 
    )

if __name__ == "__main__":
    request_ = {
        "epsg_code": 900913,
        "max_features": 1,
        "layer_property": [
            "type", 
            "name",
            "osm_id", 
            #"msGeometry", 
        ],
        "layers": {
            "buildings": None,
            "landuse": {
                "filter": {
                    "type": {
                        "=": "military",
                    },
                },
                "layer_property": [
                    #"type", 
                    "name",
                    #"osm_id", 
                    "msGeometry", 
                ],
            },
        },
        "filter": {
            "or": [
                {
                    #"and": {
                        "name": {
                            "like": "*Пет*",
                        },
                        "type": {
                            "=": "hotel",
                        },
                    #},
                }, 
                {
                    #"and": {
                        "name": {
                            "like": "*Бал*",
                        },
                        "type": {
                            "=": "hotel",
                        },
                    #},
                }, 
            ],
        }
    }
    
    json_format(request_)
    #print "*" * 30
    #print "Metadata"
    #print "*" * 30
    #json_format(gcoder.get_response(request_))
    
    request_ = {
        "epsg_code": 900913,
        #"epsg_code": 3857,
        "max_features": 1,
        "layer_property": [
            #"type", 
            "name",
            #"osm_id", 
            "msGeometry", 
        ],
        "layers": {
            "buildings": None,
            "landuse": None, 
        }, 
        "filter": {
            "name": {
                "null": None,
                "bbox": {
                    "coord": [
                        59.97111801186481728,
                        30.21720754623224181,
                        59.97569926211409097,
                        30.22404557000332304, 
                    ],
                    "epsg_code": 4326,
                    #"coord": [
                        #3364107.934602736961,
                        #8393636.548086917028,
                        #3364263.219452924561,
                        #8393740.583811631426
                    #],
                    #"epsg_code": 3857,
                },
            },
        }, 
    }
    
    json_format(request_)
    #print "*" * 30
    #print "Bbox"
    #print "*" * 30
    #json_format(gcoder.get_response(request_))
