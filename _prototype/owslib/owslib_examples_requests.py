# -*- coding: utf-8 -*-
# encoding: utf-8

import json
import requests

def json_format(cont):
    print json.dumps(
        cont,
        sort_keys=True,
        indent=4,
        separators=(',', ': '), 
        ensure_ascii=False, 
    )


def get_response(request_):
    if isinstance(request_, dict):
        request_ = json.dumps(
            request_, 
            ensure_ascii=False
        )
    json_format(
        requests.get(
            "http://localhost:3008/?{}".format(
                request_
            )
        ).json()
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
    
    #print "*" * 30
    #print "Metadata"
    #print "*" * 30
    #json_format(
        #requests.get(
            #"http://localhost:3008/?{}".format(
                #json.dumps(
                    #request_, 
                    #ensure_ascii=False
                #)
            #)
        #).json()
    #)
    
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
        
    #print "*" * 30
    #print "Bbox"
    #print "*" * 30
    #get_response(request_)

    request_ = {
        "epsg_code": 900913,
        "layer_property": [
            "name",
            "msGeometry"
        ],
        "max_features": 10,
        "layers": {
            "buildings": None,
            },
        "filter": {
            "coord1": {
                "buffer": {
                    #"coord": [
                        #59.93903,
                        #30.31589,
                    #],
                    "coord": [
                        8386175.766,
                        3374749.506,
                    ],
                    "radius": 105,
                    #"epsg_code": 4326, 
                    #"epsg_code_measure": 900913, 
                    #"epsg_code_measure": 4326, 
                    "epsg_code": 3857, 
                },
            }, 
        }, 
    }
    
    request_ = {
        "max_features": 10,
        "filter": {
            #"and": {
                "name": {
                    #"like": "*Сев*", 
                    "bbox": {
                        "coord": [
                            59.97,
                            30.21,
                            59.98,
                            30.22
                        ],
                        "epsg_code": 4326
                    },
                    "buffer": {
                        "radius": 2000.0,
                        "epsg_code": 4326,
                        "coord": [
                            59.97,
                            30.21
                        ],
                        "epsg_code_measure": 3857
                    }
                #}
            }
        },
        #"layer_property": [
            #"name"
        #]
    }    

    print "*" * 30
    print "HZ"
    print "*" * 30
    get_response(request_)
    
    #print "*" * 30
    #print "GetCapabilites"
    #print "*" * 30
    #get_response("GetCapabilites")

    #print "*" * 30
    #print "GetInfo"
    #print "*" * 30
    #get_response("GetInfo")

    #print "*" * 30
    #print "GetHelp"
    #print "*" * 30
    #get_response("GetHelp")
    
    #print "*" * 30
    #print "GetPropperties"
    #print "*" * 30
    #get_response("GetPropperties")
