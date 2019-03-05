
#import mapscript
import json
from jinja2 import Environment, DictLoader
import ast


########################################################################
class BuildMap(object):
    """
    map builder from json file
    input = source json
    output = mapdict
    
    dict first keys:
    ----------
    {'IMODS': list} - list modules for import
    {'VARS': dict } - variables and values
    {'TEMPS': dict } - jinja2 templates
    {'MAP': dict } - start point map, permissio: dict or VAR or TEMP
    
    dict last keys for VARS, TEMPS or MAP:
    ----------
    {'RUN': any } - start module class or methos to MAP, VARS or TEMPS
    {'VAR': str } - variable in VARS declare, to MAP, VARS or TEMPS
    {'TEMP': } - jinja2 sintaksis template to TEMPS
    
    variables:
    ----------
    mapjson - source json for building
    mapdict - output map dict for PubMap 
    """
    mapjson = False
    mapdict = {}
    IMODS = []
    VARS = {}
    TEMPS = {}
    MAP = {}
    
    #----------------------------------------------------------------------
    def __init__(self):
        self.procs = {
            "VAR": self.var_proc,
            "RUN": self.run_proc,
            "TEMP": self.temp_proc,
        }
    
    def load_mapjson(self, jsonfile):
        with open(jsonfile) as json_file:  
            self.mapjson = json.load(json_file)        
   
    def debug_mapjson(self):
        _debug = json.dumps(
            self.mapjson,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )
        print(_debug)
   
    def var_proc(self, data):
        return self.VARS[data]

    def run_proc(self, data):
        pass

    def temp_proc(self, data):
        pass
    
    def recurs_proc(self, val, key, proc):
        if isinstance(val[key], list):
            for new_key in range(len(val[key])):
                self.recurs_proc(val[key], new_key, proc)
        elif isinstance(val[key], dict):
            if isinstance(proc, int) and val[key].has_key('VAR'):
                # find list var
                next_var = val[key]['VAR']
                if next_var not in self.vars_queue[proc]:
                    self.vars_queue[proc].append(next_var)
            elif val[key].has_key(proc):
                # all key
                val[key] = self.procs[proc](val[key][proc])
            else: 
                for new_key in val[key]:
                    self.recurs_proc(val[key], new_key, proc)

    def build_imods(self):
        """
        if key "IMODS" step 1
        """
        for module in self.IMODS:
            exec('import {}'.format(module))
    
    def build_vars(self):
        """
        if key "VARS" to step 2
        """
        # create list index
        index = 0
        self.vars_queue = []
        for key in self.VARS:
            self.vars_queue.append([key])
            self.recurs_proc(self.VARS, key, index)
            index += 1
        # sort variables
        sort = False
        while not sort:
            sort = True
            sort_queue = [my[0] for my in self.vars_queue]
            for var in self.vars_queue:
                var_index = self.vars_queue.index(var)
                for subvar in var[1:]:
                    subvar_index = sort_queue.index(subvar)
                    if subvar_index > var_index:
                        mv_var = self.vars_queue.pop(subvar_index)
                        self.vars_queue.insert(var_index, mv_var)
                        sort = False
                        break
                if not sort:
                    break
        self.vars_queue = [my[0] for my in self.vars_queue]
        # create variables
        for key in self.vars_queue:
            self.recurs_proc(self.VARS, key, 'VAR')
    
    def build_temps(self):
        """
        if key "TEMPS" to step 3
        """
        pass
    
    def build(self):
        """
        Build for key "MAP":
            * if {} to dict and VAR, RUN - TEMP ignore
            * if "VAR":"var_name" to {} frpm variable and VAR, RUN - TEMP ignore
            * if "TEMP":"temp_name" to
                1 step use VAR
                2 step use RUN
                3 render TEMP
        """
        if self.mapjson.has_key('IMODS'):
            if isinstance(self.mapjson['IMODS'], list):
                self.IMODS = self.mapjson['IMODS'][:]
                self.build_imods()

        if self.mapjson.has_key('VARS'):
            if isinstance(self.mapjson['VARS'], dict):
                self.VARS = self.mapjson['VARS'].copy()
                self.build_vars()
   
        if self.mapjson.has_key('TEMPS'):
            if isinstance(self.mapjson['TEMPS'], dict):
                self.TEMPS = self.mapjson['TEMPS'].copy()
                self.build_temps()
                
        if self.mapjson.has_key('MAP'):
            if isinstance(self.mapjson['MAP'], dict):
                self.MAP = self.mapjson['MAP'].copy()
    
    def __call__(self):
        self.build()
        return self.mapdict

