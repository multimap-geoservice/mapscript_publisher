import os
import sys

import mapscript
from create_map import initMap

# List of all environment variable used by MapServer
MAPSERV_ENV = [
    'CONTENT_LENGTH', 'CONTENT_TYPE', 'CURL_CA_BUNDLE', 'HTTP_COOKIE',
    'HTTP_HOST', 'HTTPS', 'HTTP_X_FORWARDED_HOST', 'HTTP_X_FORWARDED_PORT',
    'HTTP_X_FORWARDED_PROTO', 'MS_DEBUGLEVEL', 'MS_ENCRYPTION_KEY',
    'MS_ERRORFILE', 'MS_MAPFILE', 'MS_MAPFILE_PATTERN', 'MS_MAP_NO_PATH',
    'MS_MAP_PATTERN', 'MS_MODE', 'MS_OPENLAYERS_JS_URL', 'MS_TEMPPATH',
    'MS_XMLMAPFILE_XSLT', 'PROJ_LIB', 'QUERY_STRING', 'REMOTE_ADDR',
    'REQUEST_METHOD', 'SCRIPT_NAME', 'SERVER_NAME', 'SERVER_PORT'
]


def application(env, start_response):
    print "-" * 30
    for key in MAPSERV_ENV:
        if key in env:
            os.environ[key] = env[key]
            print "{0}='{1}'".format(key, env[key])
        else:
            os.unsetenv(key)
    print "-" * 30

    #mapfile = '/home/oldbay/GIS/mapserver/basemaps/build/basemaps/osm-google-fix.map'
    #mapfile = 'temp_debug.map'
    #mapfile = mapscript.mapObj(mapfile)
    
    mapfile = initMap()

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

if __name__ == '__main__':  # run inline using WSGI reference implementation
    from wsgiref.simple_server import make_server
    port = 8002
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    httpd = make_server('', port, application)
    print('Serving on port %d...' % port)
    httpd.serve_forever()
