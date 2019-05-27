
import os
import time
import ast
import copy
import json

from multi_web import MultiWEB


########################################################################
class LightAPI(MultiWEB):
    """
    Light API for MultiWEB
    """

    #----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
        Init MapsWEB constructor
        """
        MultiWEB.__init__(self, *args, **kwargs)
        """
        create map name 'api'
        """
        # invariable name for api
        self.invariable_name += ['api']
        self.api2maps = {
            'api': {
                "request": self.request_api,
                "content": 'api',
                "timestamp": 0,
                "multi": False
            }
        }
        self.maps.update(self.api2maps)
        """
        API schema dict
            'api key name':{
                    'obj': self.api_module_name,
                    'args': { # need args
                        'arg_name': [type1,type2] #types list in priotity
                    },
                    'opts': {} #optional args - type as 'args'
                }
            # int input for bool data type
        """
        self.api_args_keys = ["args"]
        self.api_opts_keys = ["opts"]
        self.api_schema = {
            "help": {
                "obj": self.api_help,
                "opts": {
                    "name": str,
                    },
                },
            "test": {
                "obj": self.api_test,
                "args": {
                    "data": [
                        int, 
                        float,
                        unicode, 
                        ],
                    },
                },
            "sources": {
                "obj": self.api_sources,
                "opts": {
                    "index": int,
                    "enable": bool,
                    },
                },
            "formats": {
                "obj": self.api_formats,
                "opts": {
                    "name": str,
                    "enable": bool,
                    },
                },
            "maps": {
                "obj": self.api_maps,
                "opts": {
                    "name": str,
                    "del": bool,
                    },
                },
            "serialize": {
                "obj": self.api_serialize,
                "opts": {
                    "name": str,
                    "replace": bool,
                    },
                },
            "timeout": {
                "obj": self.api_timeout,
                "args": {
                    "sec": int,
                    },
                "opts": {
                    "name": str,
                    },
                },
            }
    
    def api_help(self, **kwargs):
        """
        default api method:
            def method_name(self, **kwargs)
                return dict{} or tuple(result,content_type)
        """
        # find help for key 'name'
        if kwargs.has_key('name'):
            if self.api_schema.has_key(kwargs['name']):
                all_api_schema = {kwargs['name']: self.api_schema[kwargs['name']]}
            else:
                all_api_schema = {} 
        else:
            all_api_schema = self.api_schema
        # gen help dict    
        schema_help = {}
        for key in all_api_schema:
            schema_help[key] = {}
            for subkey in self.api_args_keys + self.api_opts_keys:
                if self.api_schema[key].has_key(subkey):
                    schema_help[key][subkey] = {}
                    args = self.api_schema[key][subkey]
                    for arg in args:
                        types = args[arg]
                        if not isinstance(types, list): types = [types]
                        schema_help[key][subkey][arg] = [my.__name__ for my in types]
        return {
            "api_keys": schema_help,
        }

    def api_test(self, **kwargs):
        return {
            "data_type": type(kwargs["data"]).__name__,
            "data_value": kwargs["data"],
        }
  
    def api_sources(self, **kwargs):
        if kwargs.has_key('index'):
            index = kwargs['index']
            if index + 1 <= len(self.serial_src):
                src_out = [self.serial_src[index]]
            else:
                return {
                    'result': False,
                    'error': 'Index too large',
                }
        else: 
            src_out = self.serial_src
        # test to found
        if len(src_out) == 0:
            return {
                "result": False,
                "error": "Sources not found",
            }
        else:
            # enable
            if kwargs.has_key('enable'):
                for src in src_out:
                    src['enable'] = kwargs['enable']
            #query to list
            out = copy.deepcopy(src_out)
            for src in out:
                if src.has_key('query'):
                    src['query'] = src['query'].split('\n')
        return {
            "sources": out,
        }
    
    def api_formats(self, **kwargs):
        # find format for key 'name'
        if kwargs.has_key('name'):
            if self.serial_formats.has_key(kwargs['name']):
                if kwargs.has_key('enable'):
                    self.serial_formats[kwargs['name']]['enable'] = kwargs['enable']
                all_formats = {kwargs['name']: self.serial_formats[kwargs['name']]}
            else:
                all_formats = {} 
        else:
            all_formats = self.serial_formats
        # create out
        out = {
            "formats": {},
        }
        for key in all_formats:
            out['formats'][key] = all_formats[key]['enable']
        return out
            
    def api_maps(self, **kwargs):
        out = {}
        # find map for key 'name'
        if kwargs.has_key('name'):
            if self.maps.has_key(kwargs['name']):
                all_maps = {kwargs['name']: self.maps[kwargs['name']]}
            else:
                all_maps = {} 
        else:
            all_maps = self.maps
        # gen maps dict    
        maps_out = {}
        for key in all_maps:
            if key not in self.invariable_name:
                # time
                if self.maps[key]['timestamp'] != 0:
                    data_time = time.ctime(int(self.maps[key]['timestamp']))
                else:
                    data_time = 'unlimited'
                # request & map data
                map_cont = self.maps[key]['content']
                map_format = self.maps[key]['format']
                metadata = self.serial_formats[map_format]['metadata'](map_cont)
                maps_out[key] = {
                    'format': map_format,
                    'metadata': metadata,
                    'multi': int(self.maps[key]['multi']),
                    'datatime': data_time,
                }
        # test to found
        if maps_out == {}:
            return {
                "result": False,
                "error": "Maps not found",
            }
        else:
            out['maps'] = maps_out
        # delete
        if kwargs.has_key('del') and kwargs.has_key('name'): 
            if kwargs['del']:
                del(self.maps[kwargs['name']])
                out['delete'] = True
        return out
    
    def api_serialize(self, **kwargs):
        if kwargs.has_key('replace'):
            replace = kwargs['replace']
        else:
            replace = True
        if kwargs.has_key('name'):
            map_name = kwargs['name']
            if self.maps.has_key(map_name) and not replace:
                return {
                    "serialize": map_name,
                    "error": "replace is not allow",
                    "result": False,
                }
            else:
                map_ = self.serializer(map_name)
                if map_ and map_name not in self.invariable_name:
                    self.maps[map_name] = map_
                    return {
                        "serialize": map_name, 
                        "result": True,
                    }
                else:
                    return {
                        "serialize": map_name,
                        "error": "Map is not found",
                        "result": False,
                    }
        else:
            self.full_serializer(replace=replace)
            return {
                "serialize": "full", 
                "result": True,
            }
    
    def api_timeout(self, **kwargs):
        # find map for key 'name'
        if kwargs.has_key('name'):
            if self.maps.has_key(kwargs['name']):
                all_map_nam = [kwargs['name']]
            else:
                all_map_nam = [] 
        else:
            all_map_nam = [my for my in self.maps]
        # cleant map for timeout
        clean_map_nam = []
        cur_time = time.time()
        for map_name in all_map_nam:
            map_time = self.maps[map_name]['timestamp']
            if cur_time - map_time > kwargs['sec'] and map_time != 0:
                del(self.maps[map_name])
                clean_map_nam.append(map_name)
        return {
            'clean': clean_map_nam,
        }
    
    def metadata4mapnik(self, map_cont):
        return {}
        
    def request_api(self, env, data):
        # find query string value
        query_string = env['QUERY_STRING'].split('&')
        query_method = query_string.pop(0)
        query_args = {}
        for sval in query_string:
            sval_div = sval.split('=')
            if len(sval_div) == 2:
                query_args[sval_div[0]] = sval_div[-1]
        
        # validization 
        valid = True
        if self.api_schema.has_key(query_method):
            for subkey in self.api_args_keys + self.api_opts_keys:
                if self.api_schema[query_method].has_key(subkey):
                    need = self.api_schema[query_method][subkey]
                else:
                    need = {}
                for arg in need:
                    if query_args.has_key(arg):
                        arg_data = query_args[arg]
                        if isinstance(need[arg], list):
                            arg_types = need[arg]
                        else:
                            arg_types = [need[arg]]
                        for arg_type in arg_types:
                            valid = False
                            try:
                                if arg_type is bool:
                                    query_args[arg] = arg_type(int(arg_data))
                                else:
                                    query_args[arg] = arg_type(arg_data)
                            except:
                                pass
                            else:
                                valid = True
                                break
                        if not valid:
                            err = "Argument '{0}' for API Key '{1}' wrong type".format(
                                arg, 
                                query_method
                            )
                            break
                    elif subkey in self.api_args_keys:
                        valid = False
                        err = "Argument '{0}' for API Key '{1}' not found".format(
                            arg, 
                            query_method
                        )
                        break
        elif query_method == '':
            query_method = 'help' 
        else:
            valid = False
            err = "API Key '{}' not found".format(query_method)

        # run api method
        if valid:
            out = self.api_schema[query_method]["obj"](**query_args)
        else:
            out = {
                "error": err,
                "result": False,
            }
            
        # init reslt and content type
        if isinstance(out, tuple):
            result, content_type = out
        elif isinstance(out, dict):
            content_type = 'application/json'
            if not out.has_key('result'):
                out['result'] = True
            result = b'{}'.format(json.dumps(out))
        else:
            out = {
                "error": "Not valid output for API Method {}".format(query_method),
                "result": False,
            }
            content_type = 'application/json'
            result = b'{}'.format(json.dumps(out))
            
        out_req = (content_type, result)
        return out_req