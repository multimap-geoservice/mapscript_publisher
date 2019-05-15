
import mapscript
import os
import time
import ast
import json
from xml.etree import ElementTree
from multiprocessing import Process, Queue
from wsgiref.simple_server import make_server, WSGIServer
from SocketServer import ThreadingMixIn

from interface import pgsqldb
from mapublisher import PubMap


########################################################################
class PubMapWEB(PubMap):
    """
    Create wsgi socket for object PubMap
    Tiny map server
    """
    MAPSERV_ENV = [
        'CONTENT_LENGTH', 'CONTENT_TYPE', 'CURL_CA_BUNDLE', 'HTTP_COOKIE',
        'HTTP_HOST', 'HTTPS', 'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_PORT',
        'HTTP_X_FORWARDED_PROTO', 'MS_DEBUGLEVEL', 'MS_ENCRYPTION_KEY',
        'MS_ERRORFILE', 'MS_MAPFILE', 'MS_MAPFILE_PATTERN', 'MS_MAP_NO_PATH',
        'MS_MAP_PATTERN', 'MS_MODE', 'MS_OPENLAYERS_JS_URL', 'MS_TEMPPATH',
        'MS_XMLMAPFILE_XSLT', 'PROJ_LIB', 'QUERY_STRING', 'REMOTE_ADDR',
        'REQUEST_METHOD', 'SCRIPT_NAME', 'SERVER_NAME', 'SERVER_PORT'
    ]

    #----------------------------------------------------------------------
    def __init__(self, mapdict, port=3007, host='0.0.0.0'):
        self.wsgi_host = host
        self.wsgi_port = port
        self.mapdict = mapdict
        PubMap.__init__(self)
    
    def application(self, env, start_response):
        print "-" * 30
        for key in self.MAPSERV_ENV:
            if key in env:
                os.environ[key] = env[key]
                print "{0}='{1}'".format(key, env[key])
            else:
                os.unsetenv(key)
        print "-" * 30
    
        mapfile = self.get_mapobj()
        request = mapscript.OWSRequest()
        mapscript.msIO_installStdoutToBuffer()
        request.loadParamsFromURL(env['QUERY_STRING'])
    
        try:
            status = mapfile.OWSDispatch(request)
        except Exception as err:
            pass
    
        content_type = mapscript.msIO_stripStdoutBufferContentType()
        result = mapscript.msIO_getStdoutBufferBytes()
        start_response('200 OK', [('Content-type', content_type)])
        return [result]
    
    def wsgi(self):
        httpd = make_server(
            self.wsgi_host,
            self.wsgi_port,
            self.application
        )
        print('Serving on port %d...' % self.wsgi_port)
        httpd.serve_forever()
        
    def __call__(self):
        self.wsgi()


########################################################################
class ThreadingWSGIServer(ThreadingMixIn, WSGIServer): 
    daemon_threads = True


########################################################################
class MapsWEB(object):
    """
    Class for serialization & render more maps
    """
    # full serialization sources
    fullserial = False
    # multiprocessing
    multi = False
    # debug -1-response only, 0-error, 1-warning, 2-full
    debug = 0
    # log - False or path
    log = False
    # Enviroments for request
    MAPSERV_ENV = [
        'CONTENT_LENGTH',
        'CONTENT_TYPE',
        'CURL_CA_BUNDLE',
        'HTTP_COOKIE',
        'HTTP_HOST',
        'HTTPS',
        'HTTP_X_FORWARDED_HOST',
        'HTTP_X_FORWARDED_PORT',
        'HTTP_X_FORWARDED_PROTO',
        'MS_DEBUGLEVEL',
        'MS_ENCRYPTION_KEY',
        'MS_ERRORFILE',
        'MS_MAPFILE',
        'MS_MAPFILE_PATTERN',
        'MS_MAP_NO_PATH',
        'MS_MAP_PATTERN',
        'MS_MODE',
        'MS_OPENLAYERS_JS_URL',
        'MS_TEMPPATH',
        'MS_XMLMAPFILE_XSLT',
        'PATH_INFO',
        'PROJ_LIB',
        'QUERY_STRING',
        'REMOTE_ADDR',
        'REQUEST_METHOD',
        'SCRIPT_NAME',
        'SERVER_NAME',
        'SERVER_PORT'
    ]
    # invariable map name list
    invariable_name = []
    
    #----------------------------------------------------------------------
    def __init__(self, port=3007, host='0.0.0.0', base_url="http://localhost", srcs = []):
        """
        serial_src - [] list sources for serialization
        """
        self.serial_src = srcs
        """
        serial_tps - {} dict of tipes serialization data
        ------------------------------
        source format:
        {
            "type": self.serial_type
        }
        Next keys is optionls for type
        ------------------------------
        example file system:
        {
            "type": "fs"
            "ext": [] json|xml|map|or any|or not
            "path": "/path/to/maps"
        }
        ------------------------------
        example database:
        {
            "type": "pgsql"(while only)
            "connect": {
                "host": localhost,
                "port": 5432,
                "dbname": "name",
                "user": "user",
                "password": "pass",
            }
            "query": "select name as map_name, content as map_cont from table"
        }
        "query": select two column as: map_name, map_cont
        """
        self.serial_tps = {
            "fs": {
                "preserial": self._preserial_fs,
                "subserial": self._subserial_fs,
                "path": (str, unicode),
            }, 
            "pgsql": {
                "preserial": self._preserial_pgsql,
                "subserial": self._subserial_pgsql,
                "connect": dict,
                "query": (str, unicode),
            }
        }
        """
        Options for serialization
        key: name
        get: method for get map
        request: method for request map
        """
        self.serial_ops = {
            "json": {
                "get": self.get_mapjson,
                "request": self.request_mapscript,
                },
            "map": {
                "get": self.get_mapfile,
                "request": self.request_mapscript,
                },
            "xml": {
                "get": self.get_mapnik,
                "request": self.request_mapnik,
                },
        }
        self.wsgi_host = host
        self.wsgi_port = port
        self.url = "{0}:{1}".format(base_url, port)
        self.maps = {}
        if self.fullserial:
            self.full_serializer()
            
    def _logging(self, debug_layer, outdata):
        if self.debug >= debug_layer:
            if self.log:
                with open(self.log, mode='a') as logfile:
                    logfile.write("{}\n".format(outdata))
            else:
                print(outdata)
             
    def _is_json(self, test_cont):
        try:
            _ = json.loads(test_cont)
        except:
            return False
        else:
            return True    

    def _is_xml(self, test_cont):
        try:
            _ = ElementTree.fromstring(test_cont)
        except:
            return False
        else:
            return True
        
    def _is_map(self, test_cont):
        if "MAP" in test_cont and "EXTENT" in test_cont:
            return True
        else:
            return False
        
    def _detect_cont_ops(self, cont):
        """
        Detect content options as self.serial_ops
        """
        # init test_cont
        if os.path.isfile(cont):
            with open(cont, 'r') as file_:
                test_cont = file_.read()
        else:
            test_cont = cont
        # detect
        if self._is_json(test_cont):
            return "json"
        elif self._is_xml(test_cont):
            return "xml"
        elif self._is_map(test_cont):
            return "map"
        
    def _preserial_fs(self, **kwargs):
        """
        Find names for serialization all fs sources
        """
        _dir = kwargs['path']
        if kwargs.has_key('ext'):
            if isinstance(kwargs['ext'], (list, tuple)):
                exts = kwargs['ext']
            else:
                exts = [kwargs['ext']]
        else:
            exts = self.serial_ops
        names = []
        for _file in os.listdir(_dir):
            file_name = _file.split('.')[0]
            file_ext = _file.split('.')[-1]
            if file_ext in exts:
                self._logging(
                    2,
                    "INFO: In Dir:{0}, add Map name {1}".format(_dir, file_name)
                )
                names.append(file_name)
        return names

    def _subserial_fs(self, map_name, **kwargs):
        """
        subserializator for fs
        """
        _dir = kwargs['path']
        if kwargs.has_key('ext'):
            if isinstance(kwargs['ext'], (list, tuple)):
                exts = kwargs['ext']
            else:
                exts = [kwargs['ext']]
        else:
            exts = self.serial_ops
        for _file in os.listdir(_dir):
            for ext in exts:
                if _file == "{0}.{1}".format(map_name, ext):
                    content = "{0}/{1}".format(_dir, _file)
                    ops = self._detect_cont_ops(content)
                    if ops is not None:
                        self._logging(
                            2,
                            "INFO: In Dir:{0}, load Map File {1}".format(_dir, _file)
                        )
                        return ops, content
                
    def _preserial_pgsql(self, **kwargs):
        """
        Find names for serialization all pgsql sources
        """
        SQL = """
        select query.map_name
        from (
        {}
        ) as query
        """.format(kwargs['query'])
        
        psql = pgsqldb(**kwargs['connect'])
        psql.sql(SQL)
        names = psql.fetchall()
        psql.close()
        if names is not None:
            names = [my[0] for my in names]
            self._logging(
                2,
                "INFO: In Database:{0}, add Map name(s) {1}".format(
                    kwargs['connect']['dbname'],
                    names
                )
            )
            return names
  
    def _subserial_pgsql(self, map_name, **kwargs):
        """
        subserializator for pgsql
        """
        
        SQL = """
        select query.map_cont
        from (
        {0}
        ) as query
        where query.map_name = '{1}'
        limit 1
        """.format(kwargs['query'], map_name)
        
        psql = pgsqldb(**kwargs['connect'])
        psql.sql(SQL)
        content = psql.fetchone()
        psql.close()
        if content is not None:
            content = content[0]
            ops = self._detect_cont_ops(content)
            if ops is not None:
                self._logging(
                    2,
                    "INFO: From Database:{0}, load Map {1}".format(
                        kwargs['connect']['dbname'],
                        map_name
                    )
                )
                return ops, content
    
    def full_serializer(self, replace=True):
        """
        Full serialization all sources map
        replase - replace maps if the names match
        """
        # map names
        all_map_names = []
        for src in self.serial_src:
            src_type = src['type']
            valid = [
                isinstance(src[key], self.serial_tps[src_type][key]) 
                for key 
                in self.serial_tps[src_type] 
                if key not in ('subserial', 'preserial')
            ]
            if False not in valid:
                preserial = self.serial_tps[src_type]['preserial']
                all_map_names += preserial(**src)
                
        # find dublicates + replaces
        nam_count = {my: all_map_names.count(my) for my in all_map_names}
        nam_uniq = [my for my in nam_count if nam_count[my] == 1]
        nam_dubl = [my for my in nam_count if nam_count[my] > 1]
        if len(nam_dubl) > 0: 
            self._logging(
                1,
                "WARINIG: Found dublicate Map Names:{}".format(nam_dubl)
            )
        if replace:
            all_map_names = nam_uniq + nam_dubl
        else:
            all_map_names = nam_uniq
        # load all names
        for map_name in all_map_names:
            if not self.maps.has_key(map_name):
                map_ = self.serializer(map_name)
                if map_ and map_name not in self.invariable_name:
                    self.maps[map_name] = map_

    def serializer(self, map_name):
        """
        serialization map from name of self.serial_src
        """
        for src in self.serial_src:
            src_type = src['type']
            valid = [
                isinstance(src[key], self.serial_tps[src_type][key]) 
                for key 
                in self.serial_tps[src_type] 
                if key not in ('subserial', 'preserial')
            ]
            if False not in valid:
                subserial = self.serial_tps[src_type]['subserial']
                out_subserial = subserial(map_name, **src)
                if out_subserial is not None:
                    ops, content = out_subserial
                    content = self.serial_ops[ops]['get'](map_name, content)
                    if content is not None:
                        return {
                            "request": self.serial_ops[ops]['request'],
                            "content": content,
                            "timestamp": int(time.time()),
                            "multi": True,
                        }

    def get_mapnik(self, map_name, content):
        """
        get map on mapnik xml
        mapnik.load_map_from_string()
        """
        pass
    
    def get_mapfile(self, map_name, content):
        """
        get map on map file
        PubMap()
        """
        try:
            if os.path.isfile(content):
                pub_map = PubMap()
                pub_map.load_map(content)
            else:
                raise  # to do
        except:
            self._logging(
                0, 
                "ERROR: Content {} not init as Map FILE".format(content)
            )
        else:
            return self.edit_mapscript(map_name, pub_map())
    
    def get_mapjson(self, map_name, content):
        """
        get map on json template
        PubMap()
        """
        try:
            if os.path.isfile(content):
                pub_map = PubMap()
                pub_map.load_json(content)
            else:
                content = ast.literal_eval(content)
                pub_map = PubMap(content)
        except:
            self._logging(
                0, 
                "ERROR: Content {} not init as Map JSON".format(content)
            )
        else:
            return self.edit_mapscript(map_name, pub_map())
     
    def edit_mapscript(self, map_name, content):
        """
        edit requests resources in mapscript object
        """
        if isinstance(content, mapscript.mapObj):
            if map_name != "":
                map_url = "{0}/{1}".format(self.url, map_name)
                if "wms_enable_request" in content.web.metadata.keys():
                    content.web.metadata.set("wms_onlineresource", map_url)
                if "wfs_enable_request" in content.web.metadata.keys():
                    content.web.metadata.set("wfs_onlineresource", map_url)
                return content
    
    def application(self, env, start_response):
        
        # find map name
        map_name = env['PATH_INFO'].split('/')[-1]
        
        # text debug
        if self.debug >= 1:
            self._logging(1, "-" * 30)
            for key in self.MAPSERV_ENV:
                if key in env:
                    os.environ[key] = env[key]
                    self._logging(
                        1, 
                        "{0}='{1}'".format(key, env[key])
                    )
                else:
                    os.unsetenv(key)
            if self.debug >= 2:
                self._logging(2, "QUERY_STRING=(")
                for q_str in env['QUERY_STRING'].split('&'):
                    self._logging(2, "    {},".format(q_str))
                self._logging(2, ")")
            self._logging(1, "-" * 30)
        
        # serialization & response  
        while True:
            if not self.maps.has_key(map_name):
                # serialization
                map_ = self.serializer(map_name)
                if map_ and map_name not in self.invariable_name:
                    self.maps[map_name] = map_
                else:
                    self._logging(
                        0,
                        "ERROR: Map:'{}' is not serialized".format(map_name)
                    )
                    resp_status = '404 Not Found'
                    resp_type = [('Content-type', 'text/plain')]
                    start_response(resp_status, resp_type)
                    return [b'MAP:\'{}\' not found'.format(map_name)]
            else:
                # response (mono or multi)
                if self.multi and self.maps[map_name]['multi']:
                    que = Queue()
                    proc = Process(
                        target=self.maps[map_name]['request'],
                        name='response',
                        args=(
                            env,
                            self.maps[map_name]['content'],
                            que
                        )
                    )
                    proc.start()
                    response = que.get()
                    proc.join()
                else:
                    response = self.maps[map_name]['request'](
                        env,
                        self.maps[map_name]['content']
                    )
                # fin response
                if response:
                    resp_status = '200 OK'
                    resp_type = [('Content-type', response[0])]
                    start_response(resp_status, resp_type)
                    return [response[1]]
                else:
                    self._logging(
                        0,
                        "ERROR: Resource:{} error".format(map_name)
                    )
                    resp_status = '500 Server Error'
                    resp_type = [('Content-type', 'text/plain')]
                    start_response(resp_status, resp_type)
                    return [b'Resource:{} error'.format(map_name)]
    
    def request_mapscript(self, env, mapdata, que=None):
        """
        render on mapserver mapscript request
        """
        request = mapscript.OWSRequest()
        mapscript.msIO_installStdoutToBuffer()
        request.loadParamsFromURL(env['QUERY_STRING'])
    
        try:
            status = mapdata.OWSDispatch(request)
        except Exception as err:
            pass
    
        content_type = mapscript.msIO_stripStdoutBufferContentType()
        result = mapscript.msIO_getStdoutBufferBytes()
        out_req = (content_type, result)
        if que is None:
            return out_req
        else:
            que.put(out_req)
    
    def request_mapnik(self, env, mapdata, que=None):
        """
        render on mapnik request
        """
        pass
    
    def wsgi(self):
        """
        simple wsgi server
        """
        httpd = make_server(
            self.wsgi_host,
            self.wsgi_port,
            self.application,
            ThreadingWSGIServer
        )
        self._logging(0, 'Serving on port %d...' % self.wsgi_port)
        httpd.serve_forever()
        
    def __call__(self):
        self.wsgi()
        

########################################################################
class MapsAPI(MapsWEB):
    """
    Light API for MapsWEB
    """

    #----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
        Init MapsWEB constructor
        """
        MapsWEB.__init__(self, *args, **kwargs)
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
                },
            "serialize": {
                "obj": self.api_serialize,
                "opts": {
                    "map": str,
                    "replace": int,
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
        return {
            "sources": self.serial_src,
        }
    
    def api_serialize(self, **kwargs):
        if kwargs.has_key('replace'):
            replace = bool(kwargs['replace'])
        else:
            replace = True
        if kwargs.has_key('map'):
            map_name = kwargs['map']
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
            result = b'{}'.format(out)
        else:
            out = {
                "error": "Not valid output for API Method {}".format(query_method),
                "result": False,
            }
            content_type = 'application/json'
            result = b'{}'.format(out)
            
        out_req = (content_type, result)
        return out_req
     
    def maps_cleaner(self):
        "cleaner maps as old timestamp"
        pass
    
   
########################################################################
class MapsCache(object):
    """
    class publish TMS Cache for objects PubMapWEB
    """
    
    #----------------------------------------------------------------------
    def __init__(self, pud_maps_wsgi):
        """
        pud_maps_wsgi - [
            {
                'OBJ': <PubMapWSGI object>,
                'type': <cache type>
                'bla1': <>,
                'bla2': <>,
                'bla3': <>
            }
        ]
        """
        pass
  
    def debug_xml(self):
        """
        return xml config MapCache
        """
        pass
   
    def wsgi(self):
        """
        return wsgi socket for TMS
        """
        pass

    
########################################################################
class MapsTinyOWS(object):
    """
    class publish Vector Cache for objects PubMapWEB
    """
    
    #----------------------------------------------------------------------
    def __init__(self, pud_maps_wsgi):
        """
        pud_maps_wsgi - [
            {
                'OBJ': <PubMapWSGI object>,
                'type': <cache type>
                'bla1': <>,
                'bla2': <>,
                'bla3': <>
            }
        ]
        """
        pass
  
    def debug_xml(self):
        """
        return xml config TinyOWS
        """
        pass
   
    def wsgi(self):
        """
        return wsgi socket for Vector
        """
        pass


########################################################################
class MapsGraphQl(object):
    """
    class for publish every GIS protocol from GraphQl
    """
    
    #----------------------------------------------------------------------
    def __init__(self, port, host):
        """
        port - port GraphQl
        host - port GraphQl
        pub_list = [] list objects: PubMapWSGI, PubMapCache, PubTinyOWS
        """
        self.pub_list = []
        pass
    
    def run(self):
        for pub in self.pub_list:
            pub.wsgi()  #start object from method wsgi
            
    def debug(self):
        """
        return json log GraphQl
        """
        pass

