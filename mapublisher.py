
import mapscript
import json
import inspect
import sys
from wsgiref.simple_server import make_server

#from tools import MapTools

########################################################################
class PubMap(object):
    
    """
    Publisher Engine
    
    dict keys:
    ----------
    * OBJS = all objects mapscript in list - map index 0
    {'OBJ': str} = name of class for this dict
    * {'OBJ_VAR': OBJS[int]} = index number for calss object OBJS
    {'SUB_OBJ': [{},{}]} = list subclss objects
    {'<key>: None'} - if key value = None to create exteption
    ** {'PRE_OBJ': str } - prestart script of create mapscript OBJ
    ** {'POST_OBJ': str } - poststart script of create mapscript OBJ
    {'MAP': str} - path to mapfile, for inhert mapscript.mapObj
    {'SCALES': list} - list for scale map
    
    * - use for engine only
    ** - deprecated
    
    variables:
    ----------
    engine_keys = technikal key(see up) for mapdict
    mapdict = mapscript dict
    mapfile = path template mapfile for mapOBJ (default '')
    debug_def_path = default path for debug file
    OBJS = list mapscript objects
    textOBJS = text name list mapscript objects
    """
    
    engine_keys = [
        'OBJ',
        'OBJ_VAR',
        'SUB_OBJ',
        #'PRE_OBJ',
        #'POST_OBJ',
        'MAP',
        'SCALES', 
    ]
    mapdict = {'OBJ': 'mapscript.mapObj'}
    mapfile = ''
    debug_def_path = '.'
    textOBJS = 'self.OBJS'
    
    # layer scale division symbol
    lsd = '-'

    """
    scales default (0)1-16
    [
    index 0 - all map scale
    index 1..n - scale number
    ]
    """
    scales = [
        999999999, 
        268435456, 
        134217728, 
        67108864, 
        33554432, 
        16777216, 
        8388608, 
        4194304, 
        2097152, 
        1048576, 
        524288, 
        262144, 
        131072, 
        65536, 
        32768, 
        16384, 
        8192, 
    ]

    #----------------------------------------------------------------------
    def __init__(self):
        self.debug_mapscript = False
        
    def find_level_scale(self, _value, _level=False):
        """
        _value - value for method object mapscript, for level: {"1-2": value}
        return:
        type.tuple = for loop layers (minscale, maxscale, list layer data)
        false = error data for layer
        other = all correct data
        """
        
        # test level for value operations
        if isinstance(_value, dict):
            if len(_value.keys()) == 1 and isinstance(_value.keys()[0], str):
                if len(_value.keys()[0].split(self.lsd)) == 2:
                    try:
                        minlevel = int(_value.keys()[0].split(self.lsd)[0]) 
                        maxlevel = int(_value.keys()[0].split(self.lsd)[-1])
                    except:
                        pass
                    else:
                        value = _value.copy()
                        value = value.popitem()[-1]
                        if _level: 
                            if minlevel <= _level <= maxlevel:
                                return value
                            else:
                                return False
                        else:
                            return minlevel, maxlevel, value
        return _value
        
        
    def method_processing(self, OBJ, method, value):
        """
        processing script line:
        
        OBJ - mapscript object name
        method - method for object mapscript
        value - value for method object mapscript
        
        
        example processing:
        
        import inspect
        a = mapscript.mapObj()
        
        type(a.name)
        <type 'str'>
        inspect.ismethod(a.name)
        False
        
        type(a.setSize)
        <type 'instancemethod'>
        inspect.ismethod(a.setSize)
        True
        """

        # tests value as type
        if isinstance(value, str):
            value = '\'{}\''.format(value)
        elif isinstance(value, dict):
            if value.has_key('OBJ'):
                value = 'eval(\'{}\')'.format(value['OBJ'])
        elif value == None:
            raise Exception('None value in Template')
        
        # test assigment
        if inspect.ismethod(eval('{0}.{1}'.format(OBJ, method))):
            if isinstance(value, dict):
                assigment = '(**{})'.format(value)
            elif isinstance(value, (list, tuple)):
                assigment = '(*{})'.format(value)
            else:
                assigment = '({})'.format(value)
        else:
            assigment = ' = {}'.format(value)
        
        # create script string
        script_str = '{0}.{1}{2}'.format(
            OBJ, 
            method, 
            assigment
        )
        
        # line script debug or run line
        if self.debug_mapscript:
            self.debug_mapscript.append(
                '{0}{1}\n'.format(' '*8, script_str)
            )
        else:
            exec(script_str)
            
        return True
            
    def script_processing(self, script):
        if type(script) is str:
            script = script.split('\n')
        if type(script) is not list:
            raise Exception('Failed tipe from script')
        for line in script:
            exec('{}\n'.format(line), globals())
            # create scrip debug
            if self.debug_mapscript:
                self.debug_mapscript.append(
                    '{0}{1}\n'.format(
                        ' '*8,
                        line
                    )
                )
    
    def engine(self, _dict=None, SUB_OBJ=None, _level=False):
        if _dict is None:
            # insert dase value for mapdict
            _dict = self.mapdict.copy()
            self.OBJS = []
        # inhert map file: _dict['MAP'] or self.mapfile    
        if SUB_OBJ is None:
            # find base obj for map
            if _dict.has_key('MAP'):
                SUB_OBJ = _dict['MAP']
            else:
                SUB_OBJ = self.mapfile
            # find scale list
            if _dict.has_key('SCALES'):
                self.scales = _dict['SCALES']
            else:
                _dict['SCALES'] = self.scales
        # prestart script operation
        #if _dict.has_key('PRE_OBJ'):
            #self.script_processing(_dict['PRE_OBJ'])
        # object operation
        if not _dict.has_key('OBJ_VAR'):
            # add OBJ Variable to OBJS list
            str_obj = '{0}({1})'.format(_dict['OBJ'], SUB_OBJ)
            self.OBJS.append(eval(str_obj))
            _dict['OBJ_VAR'] = '{0}[{1}]'.format(
                self.textOBJS, 
                len(self.OBJS) - 1
            )
            # create scrip debug
            if self.debug_mapscript:
                self.debug_mapscript.append(
                    '{0}{1}.append({2})\n'.format(
                        ' '*8,
                        self.textOBJS, 
                        str_obj
                    )
                )
        # loop objects method operations
        for line in _dict:
            if line == 'SUB_OBJ':
                # recursive function for Sub Objects
                for subline in _dict[line]:
                    # levels procedure
                    obj_scale = self.find_level_scale(subline, _level)
                    if isinstance(obj_scale, tuple):
                        minlevel = obj_scale[0]
                        maxlevel = obj_scale[1]
                        levelline = obj_scale[-1]
                        # layer level scale objects
                        if levelline['OBJ'] == "mapscript.layerObj":
                            for numlevel in range(minlevel, maxlevel+1):
                                loopline = levelline.copy()
                                loopline['name'] = '{0}{1}'.format(
                                    loopline['name'],
                                    numlevel
                                )
                                loopline['maxscaledenom'] = self.scales[
                                    numlevel-1
                                ]
                                loopline['minscaledenom'] = self.scales[
                                    numlevel
                                ]
                                self.engine(
                                    loopline, 
                                    _dict['OBJ_VAR'],
                                    numlevel
                                )
                    # other objects 
                    elif obj_scale:
                        self.engine(
                            obj_scale,
                            _dict['OBJ_VAR'], 
                            _level
                        )
            elif line not in self.engine_keys:
                line_scale = self.find_level_scale(_dict[line], _level)
                if line_scale and not isinstance(line_scale, tuple):
                    # got to lines for processing
                    if isinstance(line_scale, list):
                        # loop in list
                        for subline in line_scale:
                            loop_scale = self.find_level_scale(subline, _level)
                            if loop_scale and not isinstance(loop_scale, tuple):
                                self.method_processing(
                                    _dict['OBJ_VAR'], 
                                    line,
                                    loop_scale
                                )
                    else:
                        # one line
                        self.method_processing(
                            _dict['OBJ_VAR'], 
                            line,
                            line_scale
                        )
        # poststart script operation
        #if _dict.has_key('POST_OBJ'):
            #self.script_processing(_dict['POST_OBJ'])
         
    def get_mapobj(self):
        self.debug_mapscript = False
        self.engine()
        return self.OBJS[0]
                
    def debug_json_file(self, path=debug_def_path, filename='debug.json'):
        """
        if path = False to output to stdout
        """
        _json = json.dumps(
            self.mapdict,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )
        if path:
            _file = open('{0}/{1}'.format(path, filename), 'w')
            _file.write(_json)
            _file.close()
        else:
            print(_json)
        
    def debug_python_mapscript(self, path=debug_def_path, filename='debug.py'):
        """
        if path = False to output to stdout
        """
        self.debug_mapscript = [
            '#!/usr/bin/python2\n', 
            '# -*- coding: utf-8 -*-\n', 
            '\n', 
            'import mapscript\n',
            '\n',
            'class script(object):\n',
            '\n', 
            '    def __init__(self):\n', 
            '        {} = []\n'.format(self.textOBJS),
        ]
        self.engine()
        self.debug_mapscript += [
            '\n', 
            '    def __call__(self):\n', 
            '        return {}[0]\n'.format(self.textOBJS), 
            '\n', 
            '\n', 
            'if __name__ =="__main__":\n', 
            '    test = script()\n'
            '    test().save("./debug.script.map")\n', 
        ]
        if path:
            _file = open('{0}/{1}'.format(path, filename), 'w')
            _file.writelines(self.debug_mapscript)
            _file.close()
        else:
            for _line in self.debug_mapscript:
                print(_line)
                    
    def debug_map_file(self, path=debug_def_path, filename='debug.map'): 
        _map = self.get_mapobj()
        _map.save('{0}/{1}'.format(path, filename))

    def debug_map_img(self, path=debug_def_path, filename='debug.png'): 
        _map = self.get_mapobj()
        _map.write('{0}/{1}'.format(path, filename))
    
    def __call__(self):
        return self.get_mapobj()


########################################################################
class PubMapWEB(PubMap):
    """
    Create wsgi socket for object PubMap
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
    def __init__(self, mapdict, port, host='0.0.0.0'):
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
    
    def response(self):
        """
        for imput response an all protocols
        """
        pass
    
    def wsgi(self):
        if len(sys.argv) > 1:
            port = int(sys.argv[1])
        httpd = make_server(
            self.wsgi_host,
            self.wsgi_port,
            self.application
        )
        print('Serving on port %d...' % port)
        httpd.serve_forever()
        
        
########################################################################
class PubMapCache(object):
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
class PubTinyOWS(object):
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
class MapGraphQl(object):
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

