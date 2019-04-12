
import mapscript
import os
import time
import ast
from wsgiref.simple_server import make_server
from interface import psqldb

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
class MapsWEB(object):
    """
    Public more maps
    """
    debug = False 
    """
    Enviroments for request
    """
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
   
    """
    serial_src - [] list sources for serialization
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
        "query": "select name,file from table"
    }
    "content": content type for map
    "query": select two column: 1-name, 2-content
    """
    serial_tps = {
        "fs": {
            "subserial": _subserial_fs,
            "path": (str, unicode),
        }, 
        "pgsql": {
            "subserial": _subserial_pgsql,
            "connect": dict,
            "query": (str, unicode),
        }
    }
    serial_src = []
    
    """
    Options for serialization
    key: name
    get: method for get map
    request: method for request map
    """
    serial_ops = {
        "json": {
            "get": get_mapjson,
            "request": request_mapscript,
            },
        "map": {
            "get": get_mapfile,
            "request": request_mapscript,
            },
        "xml": {
            "get": get_mapnik,
            "request": request_mapnink,
            },
    }
    
    #----------------------------------------------------------------------
    def __init__(self, port=3007, host='0.0.0.0', base_url="http://localhost"):
        self.wsgi_host = host
        self.wsgi_port = port
        self.url = "{0}:{1}".format(base_url, port)
        self.maps = {}
 
    def _subserial_fs(self, map_name, **kwargs):
        """
        subserializator for fs
        """
        _dir = kwargs['path']
        for _file in os.listdir(_dir):
            for ext in self.serial_ops:
                if _file == "{0}.{1}".format(map_name, ext):
                    if self.debug:
                        print ("In Dir:{0}, load Map File {1}".format(_dir, _file))
                    with open("{0}/{1}".format(_dir, _file), "r") as _file:
                        content_file = _file.read()
                    return ext, content_file
  
    def _subserial_pgsql(self, map_name, **kwargs):
        """
        subserializator for pgsql
        """
        pass

    def serializer(self, map_name):
        """
        serialization map from name of self.serial_src
        """
        for src in self.serial_src:
            src_type = src['type']
            subserial = self.serial_tps[src_type]['subserial']
            valid = [
                isinstance(src[key], self.serial_tps[src_type][key]) 
                for key 
                in self.serial_tps[src_type] 
                if key != 'subserial'
            ]
            if False not in valid:
                out_subserial = subserial(self, map_name, **src)
                if out_subserial is not None:
                    ops, content = out_subserial
                    content = self.serial_ops[ops]['get'](self, map_name, content)
                    if content is not None:
                        self.maps[map_name] = {
                            "request": self.serial_ops[ops]['request'],
                            "content": content,
                            "timestamp": int(time.time()),
                        }
                        return True

    def get_mapnik(self, map_name, content):
        """
        get map on mapnik xml
        mapnik.load_map_from_string()
        """
        pass
    
    def get_mapfile(self, map_name, content):
        """
        get map on map file
        mapscript.mapObj() ?????
        """
        pass
    
    def get_mapjson(self, map_name, content):
        """
        get map on json template
        PubMap()
        """
        content = ast.literal_eval(content)
        pub_map = PubMap(content)
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
    
    def maps_cleaner(self):
        "cleaner maps as old timestamp"
        pass
    
    def application(self, env, start_response):
        # find query string value
        query_vals = {}
        for sval in env['QUERY_STRING'].split('&'):
            sval_div = sval.split('=')
            query_vals[sval_div[0]] = sval_div[-1]
        map_name = env['PATH_INFO'].split('/')[-1]
        # text debug
        if self.debug:
            print ("-" * 30)
            for key in self.MAPSERV_ENV:
                if key in env:
                    os.environ[key] = env[key]
                    print (
                        "{0}='{1}'".format(key, env[key])
                    )
                else:
                    os.unsetenv(key)
            print ("-" * 30)
            for key in query_vals:
                print ("{0}={1}".format(key, query_vals[key]))
            print ("-" * 30)
        
        # serializer or request 
        if not self.maps.has_key(map_name):
            out = self.serializer(map_name)
            if out:
                self.maps[map_name]['request'](self, self.maps[map_name]['content'])
            else:
                if self.debug:
                    print "ERROR: Map:{} is not serialized".format(map_name)
        else:
            self.maps[map_name]['request'](self, self.maps[map_name]['content'])
    
    def request_mapscript(self, mapdata):
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
        start_response('200 OK', [('Content-type', content_type)])
        return [result]
    
    def request_mapnik(self, mapdata):
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
            self.application
        )
        if self.debug:
            print('Serving on port %d...' % self.wsgi_port)
        httpd.serve_forever()
        
    def __call__(self):
        self.wsgi()
        
        
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

