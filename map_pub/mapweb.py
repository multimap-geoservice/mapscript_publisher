
import os
import copy
from wsgiref.simple_server import make_server

import mapscript

from .mapublisher import PubMap


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
        self.mapscript_obj = self.get_mapobj()
    
    def application(self, env, start_response):
        q_str = {
            my.split("=")[0].upper(): my.split("=")[1]
            for my 
            in env['QUERY_STRING'].split('&')
            if "=" in my
        }
        serv_ver = [q_str.get('SERVICE', False), q_str.get('VERSION', False)]
        
        print ("-" * 30)
        for key in self.MAPSERV_ENV:
            if key in env:
                os.environ[key] = env[key]
                print ("{0}='{1}'".format(key, env[key]))
            else:
                os.unsetenv(key)
        print ("QUERY_STRING=(")
        for key in q_str:
            print ("    {0}={1},".format(key, q_str[key]))
        print (")")
        print ("-" * 30)
    
        request = mapscript.OWSRequest()
        mapscript.msIO_installStdoutToBuffer()
        request.loadParamsFromURL(env['QUERY_STRING'])
        rec_obj = self.mapscript_obj.clone()
    
        try:
            status_id = rec_obj.OWSDispatch(request)
        except Exception as err:
            print ("OWSDispatch Error: {}".format(err))
            err_def = unicode(err).split(':')[0]
            status_id = None
        
        content_type = mapscript.msIO_stripStdoutBufferContentType()
        result = mapscript.msIO_getStdoutBufferBytes()
        mapscript.msIO_resetHandlers()

        # status:
        if status_id == mapscript.MS_SUCCESS:
            status = '200 OK'
        elif status_id == mapscript.MS_FAILURE:
            status = '400 Bad request'
            if serv_ver == ['WFS', '2.0.0']:
                result = '\n'.join(result.split('\n')[2:])
        elif status_id is None:
            if serv_ver[0] == "WMS" and err_def == "msPostGISLayerGetExtent()":
                status = '200 OK'
            elif serv_ver == ['WFS', '1.0.0'] and err_def == "msWFSGetFeature()":
                status = '400 Bad request'
            else:
                status = '500 Server Error'

        start_response(status, [('Content-type', str(content_type))])
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