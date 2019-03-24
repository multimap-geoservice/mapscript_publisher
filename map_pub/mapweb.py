
import mapscript
import os
from wsgiref.simple_server import make_server

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

    #----------------------------------------------------------------------
    def __init__(self, port=3007, host='0.0.0.0', base_url="http://localhost", *args):
        self.wsgi_host = host
        self.wsgi_port = port
        self.url = "{0}:{1}".format(base_url, port)
        self.maps = {}
        if args != ():
            for map_obj in args:
                self.get_map(map_obj)
    
    def get_map(self, map_obj):
        if isinstance(map_obj, mapscript.mapObj):
            map_name = map_obj.name
            if map_name != "":
                map_url = "{0}/{1}".format(self.url, map_name)
                if "wms_enable_request" in map_obj.web.metadata.keys():
                    map_obj.web.metadata.set("wms_onlineresource", map_url)
                if "wfs_enable_request" in map_obj.web.metadata.keys():
                    map_obj.web.metadata.set("wfs_onlineresource", map_url)
                self.maps[map_name] = map_obj
    
    def application(self, env, start_response):
        # find query string value
        query_vals = {}
        for sval in env['QUERY_STRING'].split('&'):
            sval_div = sval.split('=')
            query_vals[sval_div[0]] = sval_div[-1]
        map_name = env['PATH_INFO'].split('/')[-1]
        # text debug
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
    
        mapfile = self.maps[map_name]
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

