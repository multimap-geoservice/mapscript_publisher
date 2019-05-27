
import os
import time
from multiprocessing import Process, Queue
from wsgiref.simple_server import make_server, WSGIServer
from SocketServer import ThreadingMixIn

from interface import pgsqldb
from requests import (
    request_mapscript, 
    request_mapnik
) 

########################################################################
class ThreadingWSGIServer(ThreadingMixIn, WSGIServer): 
    daemon_threads = True


########################################################################
class MultiWEB(object):
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
                "enable": bool,
            }, 
            "pgsql": {
                "preserial": self._preserial_pgsql,
                "subserial": self._subserial_pgsql,
                "connect": dict,
                "query": (str, unicode),
                "enable": bool,
            }
        }
        """
        Mpa Formats for serialization:
        key: name
        "test": test to find format
        "get": method for get map
        "request": method for request map
        "metadata": return matadata dict
        "enable": bool flag for use in serialize
        """
        self.serial_formats = {}
       
        # default web params
        self.wsgi_host = host
        self.wsgi_port = port
        self.url = "{0}:{1}".format(base_url, port)
        self.maps = {}

        # add map requests 
        self.map_requests = [
            request_mapscript, 
            request_mapnik
        ]
        self.init_map_requests() 

        if self.fullserial:
            self.full_serializer()
            
    def logging(self, debug_layer, outdata):
        if self.debug >= debug_layer:
            if self.log:
                with open(self.log, mode='a') as logfile:
                    logfile.write("{}\n".format(outdata))
            else:
                print(outdata)

    def init_map_requests(self):
        self.map_req_objs = []
        for map_req in self.map_requests:
            protcol = map_req.Protocol(self.url, self.logging)
            self.serial_formats.update(protcol.proto_schema)
            self.map_req_objs.append(protcol)
             
    def _detect_cont_format(self, cont):
        """
        Detect content format as self.serial_formats
        """
        for cont_format in self.serial_formats:
            if self.serial_formats[cont_format]["enable"]:
                if self.serial_formats[cont_format]["test"](cont):
                    return cont_format
        
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
            exts = self.serial_formats
        names = []
        for _file in os.listdir(_dir):
            file_name = _file.split('.')[0]
            file_ext = _file.split('.')[-1]
            if file_ext in exts:
                self.logging(
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
            exts = self.serial_formats
        for _file in os.listdir(_dir):
            for ext in exts:
                if _file == "{0}.{1}".format(map_name, ext):
                    content = "{0}/{1}".format(_dir, _file)
                    cont_format = self._detect_cont_format(content)
                    if cont_format is not None:
                        self.logging(
                            2,
                            "INFO: In Dir:{0}, load Map File {1}".format(_dir, _file)
                        )
                        return cont_format, content
                
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
            self.logging(
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
            cont_format = self._detect_cont_format(content)
            if cont_format is not None:
                self.logging(
                    2,
                    "INFO: From Database:{0}, load Map {1}".format(
                        kwargs['connect']['dbname'],
                        map_name
                    )
                )
                return cont_format, content
    
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
            valid.append(src['enable'])
            if False not in valid:
                preserial = self.serial_tps[src_type]['preserial']
                all_map_names += preserial(**src)
                
        # find dublicates + replaces
        nam_count = {my: all_map_names.count(my) for my in all_map_names}
        nam_uniq = [my for my in nam_count if nam_count[my] == 1]
        nam_dubl = [my for my in nam_count if nam_count[my] > 1]
        if len(nam_dubl) > 0: 
            self.logging(
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
            valid.append(src['enable'])
            if False not in valid:
                subserial = self.serial_tps[src_type]['subserial']
                out_subserial = subserial(map_name, **src)
                if out_subserial is not None:
                    cont_format, content = out_subserial
                    content = self.serial_formats[cont_format]['get'](map_name, content)
                    if content is not None:
                        return {
                            "format": cont_format,
                            "request": self.serial_formats[cont_format]['request'],
                            "content": content,
                            "timestamp": int(time.time()),
                            "multi": True,
                        }

    def application(self, env, start_response):
        
        # find map name
        map_name = env['PATH_INFO'].split('/')[-1]
        
        # text debug
        if self.debug >= 1:
            self.logging(1, "-" * 30)
            for key in self.MAPSERV_ENV:
                if key in env:
                    os.environ[key] = env[key]
                    self.logging(
                        1, 
                        "{0}='{1}'".format(key, env[key])
                    )
                else:
                    os.unsetenv(key)
            if self.debug >= 2:
                self.logging(2, "QUERY_STRING=(")
                for q_str in env['QUERY_STRING'].split('&'):
                    self.logging(2, "    {},".format(q_str))
                self.logging(2, ")")
            self.logging(1, "-" * 30)
        
        # serialization & response  
        while True:
            if not self.maps.has_key(map_name):
                # serialization
                map_ = self.serializer(map_name)
                if map_ and map_name not in self.invariable_name:
                    self.maps[map_name] = map_
                else:
                    self.logging(
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
                    if self.maps[map_name]['timestamp'] != 0:
                        self.maps[map_name]['timestamp'] = int(time.time())
                    resp_status = '200 OK'
                    resp_type = [('Content-type', response[0])]
                    start_response(resp_status, resp_type)
                    return [response[1]]
                else:
                    self.logging(
                        0,
                        "ERROR: Resource:{} error".format(map_name)
                    )
                    resp_status = '500 Server Error'
                    resp_type = [('Content-type', 'text/plain')]
                    start_response(resp_status, resp_type)
                    return [b'Resource:{} error'.format(map_name)]

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
        self.logging(0, 'Serving on port %d...' % self.wsgi_port)
        httpd.serve_forever()
    
    def __call__(self):
        self.wsgi()