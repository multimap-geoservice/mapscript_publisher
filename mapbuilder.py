
#import mapscript
import json
from jinja2 import Environment, DictLoader
import ast
import inspect
import copy


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
    debug - False|True|filename - view debug build process
    mapjson - source json for building
    mapdict - output map dict for PubMap
    IMODS - list import modules
    VARS - dict variables
    TEMPS - dict templates
    MAP - TEMP|VAR|dict - mapfile
    """
    debug = False
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
        self.mapdict = self.MAP
    
    def load_mapjson(self, jsonfile):
        with open(jsonfile) as json_file:  
            self.mapjson = json.load(json_file)
            
    def debug_out(self, log, description, first=False):
        if isinstance(log, dict):
            log = json.dumps(
                log,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')
            )
        log = "\n{0}\nSTEP: {1}\n{0}\n{2}".format("-"*60, description, log)
        if isinstance(self.debug, (str, unicode)):
            if first:
                write_mode = 'w'
            else:
                write_mode = 'a'
            _file = open(self.debug, write_mode)
            _file.write(log)
            _file.close()
        else:
            print (log)
   
    def var_proc(self, data):
        """
        enter VAR:{} keys 
        """
        if self.VARS.has_key(data):
            if isinstance(data, (str, unicode)):
                return self.VARS[data]
            else:
                raise Exception('VAR:{} is not str or unicode'.format(data))
        else:
            raise Exception('VAR:{} not found'.format(data))

    def run_proc_item(self, item):
        if isinstance(item, (dict, str, unicode)):
            if isinstance(item, dict):
                if len(item) == 1:
                    # obj
                    obj = item.keys()[0]
                    # options
                    options = item[obj]
                    if isinstance(options, dict):
                        options = '(**{})'.format(options)
                    elif isinstance(options, (list, tuple)):
                        options = '(*{})'.format(options)
                    else:
                        options = '({})'.format(options)
                    # all
                    eval_item = '{0}{1}'.format(
                        obj, 
                        options 
                    )
                else:
                    raise Exception(
                        'All keys RUN:{} > 1, accesable 1 only'.format(item.keys())
                    )
            else:
                eval_item = item
            return eval_item
        else:
            raise Exception(
                'VAR:{} is not dict or str or unicode type'.format(item)
            )
        
    def run_proc(self, data):
        """
        enter RUN:[] keys
        variants: "":str
                  {}:dict
        """
        # import modules IMODS    
        for module in self.IMODS:
            exec('import {}'.format(module))
        # data is not list or tuple
        if not isinstance(data, (list, tuple)):
            if isinstance(data, dict):
                if inspect.isclass(eval(data.keys()[0])):
                    data = [data, "__call__()"]
                else:
                    data = [data]
            elif isinstance(data, (str, unicode)):
                data = [data]
            else:
                raise Exception('RUN data is not correct (dict or srt or unicode)')
        # RUN list
        separator = ''
        eval_data = ''
        for item in data:
            eval_data += '{0}{1}'.format(separator, self.run_proc_item(item))
            separator = '.'
        return eval(eval_data)

    def temp_proc(self, data):
        if isinstance(data, (list, tuple)):
            return {"TEMP":"\n".join(data)}
        else:
            return {"TEMP":data}
    
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
        # step 0: list temp to text
        for key in self.TEMPS:
            self.recurs_proc(self.TEMPS, key, 'TEMP')
        # step 1: temp to str to list
        for key in self.TEMPS:
            temp2json = json.dumps(
                    self.TEMPS[key],
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': ')
                ).split("\n")
            temp2text = []
            post_temp_cont = False
            temp_index = -1
            for string in temp2json:
                temp_index += 1
                if post_temp_cont:
                    post_temp_cont = False
                    continue
                temp_pos = string.find("TEMP") - 1
                if temp_pos != -2:
                    # find template
                    data = ast.literal_eval(
                        "{%s}"%string[temp_pos:]
                        )['TEMP'].split("\n")
                    # find pre template
                    pre_temp = temp2json[temp_index-1]
                    pre_pos = pre_temp.find("{")
                    if ": {" in pre_temp:
                        pre_temp = pre_temp[:pre_temp.find(": {")+2]
                    else:
                        pre_temp = " " * pre_pos
                    del temp2text[-1]
                    # find post template
                    post_temp = temp2json[temp_index+1]
                    if "}," in post_temp:
                        post_temp = ','
                    else:
                        post_temp = ''
                    post_temp_cont = True
                    # append template
                    first = 1
                    last = len(data)
                    index = 0
                    for pos in data:
                        index += 1
                        if index == first:
                            prefix = pre_temp
                        else:
                            prefix = " " * len(pre_temp)
                        if index == last:
                            postfix = post_temp
                        else:
                            postfix = ""
                        temp2text.append('{0}{1}{2}'.format(
                            prefix, 
                            pos, 
                            postfix
                        ))
                else:
                    temp2text.append(string)
            self.TEMPS[key] = "\n".join(temp2text)
            
    def build_map(self):
        """
        build map - step 3
            variants: MAP: TEMP
                      MAP: VAR
                      MAP: {}
        """
        if self.MAP.has_key('TEMP'):
            # MAP from section TEMPS
            maptemp = self.MAP['TEMP']
            if self.TEMPS.has_key(maptemp):
                env = Environment(
                    loader=DictLoader(self.TEMPS)
                )
                template = env.get_template(maptemp)
                map_txt = template.render(**self.VARS)
                self.MAP = ast.literal_eval(map_txt)
            else:
                raise Exception(
                    'TEMPS: "{}" for MAP not found'.format(maptemp)
                )
        elif self.MAP.has_key('VAR'):
            # MAP from section VAR
            mapvar = self.MAP['VAR']
            if self.TEMPS.has_key(mapvar):
                self.MAP = self.VARS[mapvar].copy()
            else:
                raise Exception(
                    'VARS: "{}" for MAP not found'.format(mapvar)
                )
        # init VAR
        for key in self.MAP:
            self.recurs_proc(self.MAP, key, 'VAR')
        # init RUN
        for key in self.MAP:
            self.recurs_proc(self.MAP, key, 'RUN')
            
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
        # trst load map json
        if self.mapjson:
            if self.debug:
                self.debug_out(self.mapjson, 'Load Map JSON file', first=True)
        else:
            raise Exception('Map JSON is not loaded')
        # init import modules  
        if self.mapjson.has_key('IMODS'):
            if isinstance(self.mapjson['IMODS'], list):
                self.IMODS = self.mapjson['IMODS'][:]
                if self.debug:
                    self.debug_out(self.IMODS, 'List import Modules')
        # VARS build - etap 1
        if self.mapjson.has_key('VARS'):
            if isinstance(self.mapjson['VARS'], dict):
                self.VARS = copy.deepcopy(self.mapjson['VARS'])
                if self.debug:
                    self.debug_out(self.VARS, 'Input VARS')
                self.build_vars()
                if self.debug:
                    self.debug_out(self.VARS, 'Output VARS')
        # TEMPS build - etap 2
        if self.mapjson.has_key('TEMPS'):
            if isinstance(self.mapjson['TEMPS'], dict):
                self.TEMPS = copy.deepcopy(self.mapjson['TEMPS'])
                if self.debug:
                    self.debug_out(self.TEMPS, 'Input TEMPS')
                self.build_temps()
                if self.debug:
                    for temp in self.TEMPS:
                        self.debug_out(self.TEMPS[temp], 'Output TEMP: {}'.format(temp))
        # MAP build - etap 3
        if self.mapjson.has_key('MAP'):
            if isinstance(self.mapjson['MAP'], dict):
                self.MAP = copy.deepcopy(self.mapjson['MAP'])
                if self.debug:
                    self.debug_out(self.MAP, 'Input MAP')
                self.build_map()
                if self.debug:
                    self.debug_out(self.MAP, 'Output MAP')
                self.mapdict = self.MAP
            else:
                raise Exception('Section MAP is not dict')
        else:
            raise Exception('Section MAP not found')
    
    def __call__(self):
        self.build()
        return self.mapdict
