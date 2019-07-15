# -*- coding: utf-8 -*-
# encoding: utf-8

import os
from wsgiref.simple_server import make_server

import mapscript

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