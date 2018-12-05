
import mapscript
import json
import inspect
import sys
from wsgiref.simple_server import make_server


class PubMap(object):
    """
    Publisher Engine
    
    dict keys:
    ----------
    OBJS = all objects mapscript in list - map index 0
    {'OBJ': str} = name of class for this dict
    {'OBJ_VAR': OBJS[int]} = index number for calss object OBJS
    {'SUB_OBJ': [{},{}]} = list subclss objects
    {'<key>: None'} - if key value = None to create exteption
    {'PRE_OBJ': str } - prestart script of create mapscript OBJ
    {'POST_OBJ': str } - poststart script of create mapscript OBJ
    {'MAP': str} - path to map file, for inhert mapscript.mapObj
    
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
        'PRE_OBJ',
        'POST_OBJ',
        'MAP', 
    ]
    mapdict = {'OBJ': 'mapscript.mapObj'}
    mapfile = ''
    debug_def_path = '.'
    OBJS = []
    textOBJS = 'self.OBJS'

    #----------------------------------------------------------------------
    def __init__(self):
        self.debug_mapscript = False
        
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
        # tests value
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
            elif isinstance(value, list):
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
    
    def engine(self, _dict=None, SUB_OBJ=None):
        if _dict is None:
            _dict = self.mapdict
        # inhert map file: _dict['MAP'] or self.mapfile    
        if SUB_OBJ is None:
            if _dict.has_key('MAP'):
                SUB_OBJ = _dict['MAP']
            else:
                SUB_OBJ = self.mapfile
        # prestart script operation
        if _dict.has_key('PRE_OBJ'):
            self.script_processing(_dict['PRE_OBJ'])
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
                    '{0}{1} = {2}\n'.format(
                        ' '*8,
                        _dict['OBJ_VAR'], 
                        str_obj
                    )
                )
        # loop objects method operations
        for line in _dict:
            if line == 'SUB_OBJ':
                # recursive function for Sub Objects
                for subline in _dict[line]:
                    self.engine(subline, _dict['OBJ_VAR'])
            elif line not in self.engine_keys:
                # got to lines for processing
                if type(_dict[line]) == list:
                    # loop in list
                    for subline in _dict[line]:
                        self.method_processing(
                            _dict['OBJ_VAR'], 
                            line,
                            subline
                        )
                else:
                    # one line
                    self.method_processing(
                        _dict['OBJ_VAR'], 
                        line,
                        _dict[line]
                    )
        # poststart script operation
        if _dict.has_key('POST_OBJ'):
            self.script_processing(_dict['POST_OBJ'])
                
    def get_json(self, path=debug_def_path, filename='debug.json'):
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
        
    def get_mapscript(self, path=debug_def_path, filename='debug.py'):
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
            '        return {}[0]\n'.format(self.textOBJS)
        ]
        if path:
            _file = open('{0}/{1}'.format(path, filename), 'w')
            _file.writelines(self.debug_mapscript)
            _file.close()
        else:
            for _line in self.debug_mapscript:
                print(_line)
         
    def get_mapobj(self):
        self.debug_mapscript = False
        self.engine()
        return self.OBJS[0]
                    
    def get_mapfile(self, path=debug_def_path, filename='debug.map'): 
        _map = self.get_mapobj()
        _map.save('{0}/{1}'.format(path, filename))

    def get_mapimg(self, path=debug_def_path, filename='debug.png'): 
        _map = self.get_mapobj()
        _map.write('{0}/{1}'.format(path, filename))


########################################################################
class PubMapWSGI(PubMap):
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
    class publish TMS Cache for objects PubMapWSGI
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
  
    def get_xml(self):
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
    class publish Vector Cache for objects PubMapWSGI
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
  
    def get_xml(self):
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

