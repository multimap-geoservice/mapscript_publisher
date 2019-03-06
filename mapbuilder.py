
#import mapscript
import json
from jinja2 import Environment, DictLoader
import ast
import inspect


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
        if self.VARS.has_key(data):
            if isinstance(data, (str, unicode)):
                return self.VARS[data]
            else:
                raise Exception('VAR:{} is not str or unicode'.format(data))
        else:
            raise Exception('VAR:{} not found'.format(data))

    def run_proc(self, data):
        if isinstance(data, (dict, str, unicode)):
            # import modules IMODS    
            for module in self.IMODS:
                exec('import {}'.format(module))
            if isinstance(data, dict):
                if len(data) == 1:
                    # obj
                    obj = data.keys()[0]
                    # prefix (kostil!!!, add class.method to RUN in future)
                    if inspect.isclass(eval(obj)):
                        prefix = '()'
                    else:
                        prefix = ''
                    # options
                    options = data[obj]
                    if isinstance(options, dict):
                        options = '(**{})'.format(options)
                    elif isinstance(options, (list, tuple)):
                        options = '(*{})'.format(options)
                    else:
                        options = '({})'.format(options)
                    # all
                    eval_string = '{0}{1}{2}'.format(
                        obj, 
                        options, 
                        prefix
                    )
                else:
                    raise Exception(
                        'All keys RUN:{} > 1, accesable 1 only'.format(data.keys())
                    )
            else:
                eval_string = data
            return eval(eval_string)
        else:
            raise Exception(
                'VAR:{} is not dict or str or unicode type'.format(data)
            )

    def temp_proc(self, data):
        pass
    
    def recurs_proc(self, val, key, proc):
        if isinstance(val[key], list):
            for new_key in range(len(val[key])):
                self.recurs_proc(val[key], new_key, proc)
        elif isinstance(val[key], dict):
            if isinstance(proc, int) and val[key].has_key('VAR'):
                next_var = val[key]['VAR']
                if next_var == self.vars_queue[proc][0]:
                    # find copy VARS to sub-VARS
                    raise Exception(
                        'sub-VARS:{0} == VARS:{1}'.format(
                            next_var, 
                            self.vars_queue[proc][0]
                        )
                    )
                elif next_var not in self.vars_queue[proc]:
                    # find list var
                    self.vars_queue[proc].append(next_var)
            elif val[key].has_key(proc):
                # all key
                val[key] = self.procs[proc](val[key][proc])
            else: 
                for new_key in val[key]:
                    self.recurs_proc(val[key], new_key, proc)

    def build_vars(self):
        """
        if key "VARS" to step 1
        """
        # create list index
        index = 0
        self.vars_queue = []
        for key in self.VARS:
            self.vars_queue.append([key])
            self.recurs_proc(self.VARS, key, index)
            index += 1
        # sort and test variables
        sort = False
        while not sort:
            sort = True
            sort_queue = [my[0] for my in self.vars_queue]
            for var in self.vars_queue:
                var_index = self.vars_queue.index(var)
                for subvar in var[1:]:
                    # find subvar in VARS
                    if subvar not in sort_queue:
                        raise Exception(
                            'sub-VARS:{0} for VARS:{1} is not found'.format(
                                subvar, 
                                var[0]
                            )
                        )
                    else:
                        subvar_index = sort_queue.index(subvar)
                    # test fro cross depends in VARS
                    if var[0] in self.vars_queue[subvar_index]:
                        raise Exception(
                            'Found cross depends for sub-VARS:{0} to VARS:{1}'.format(
                                subvar, 
                                var[0]
                            )
                        )
                    # move VARS for next init as sub-VAR
                    if subvar_index > var_index:
                        mv_var = self.vars_queue.pop(subvar_index)
                        self.vars_queue.insert(var_index, mv_var)
                        sort = False
                        break
                if not sort:
                    break
        self.vars_queue = sort_queue
        # init VAR
        for key in self.vars_queue:
            self.recurs_proc(self.VARS, key, 'VAR')
        # init RUN
        for key in self.vars_queue:
            self.recurs_proc(self.VARS, key, 'RUN')
    
    def build_temps(self):
        """
        if key "TEMPS" to step 2
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

