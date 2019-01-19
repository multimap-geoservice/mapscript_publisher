
#import mapscript
import json
from jinja2 import Environment, DictLoader
import ast

from interface import gdal2pg
from mapublisher import PubMap


########################################################################
class MapTools:
    """
    convert mapdict to json file
    and operation from this file
    mapdict - input map dict format variable
    mapjson - output map json format variable
    """

    #----------------------------------------------------------------------
    def __init__(self, mapdict):
        self.mapdict = mapdict
    
    def gen_mapjson(self):
        self.mapjson = json.dumps(
            self.mapdict,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )
        
