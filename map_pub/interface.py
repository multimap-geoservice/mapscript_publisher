# -*- coding: utf-8 -*-
# encoding: utf-8

import psycopg2
from subprocess import Popen, PIPE

import config


class pgsqldb(object):
    
    pg_defaults = {
        'host': config.databaseHost,
        'port': config.databasePort,
        'dbname': config.databaseName,
        'user': config.databaseUser,
        'password': config.databasePass,
    }

    def __init__(self, **kwargs):
        self.connString = ''
        str_temp = '{0}{1}=\'{2}\' ' 
        for _key in self.pg_defaults:
            if kwargs.has_key(_key):
                self.connString= str_temp.format(
                    self.connString,
                    _key,
                    kwargs[_key]
                )
            elif self.pg_defaults[_key]:
                self.connString = str_temp.format(
                    self.connString,
                    _key,
                    self.pg_defaults[_key]
                )
        self.conn = psycopg2.connect(self.connString)
        self.cur = self.conn.cursor()

    def sql(self, _sql):
        self.cur.execute(_sql)

    def commit(self):
        self.conn.commit()

    def autocommit(self, _aut=False):
        self.conn.autocommit = _aut

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()

    def close(self):
        self.commit()
        self.cur.close()
        self.conn.close()

    def __call__(self):
        return self.cur

    # def __del__(self):
        # self.close()


class gdal2db(object):
    
    db_keys = {}
    nonstr_keys = [] 

    def __init__(self, **kwargs):
        self.update_db_keys(**kwargs)
   
    def update_db_keys(self, **kwargs):
        for _key in kwargs:
            self.db_keys[_key] = kwargs[_key]

    def create_conString(self):
        self.connString = 'PG:'
        str_temp = '{0}{1}=\'{2}\' ' 
        nonstr_temp = '{0}{1}={2} ' 
        for _key in self.db_keys:
            if _key in self.nonstr_keys:
                key_temp = nonstr_temp
            else:
                key_temp = str_temp
            if self.db_keys[_key]:
                self.connString = key_temp.format(
                    self.connString,
                    _key,
                    self.db_keys[_key]
                )
                
    def __call__(self):
        self.create_conString()
        return self.connString


class gdal2pg(gdal2db):
    
    db_keys = {
        'host': config.databaseHost,
        'port': config.databasePort,
        'dbname': config.databaseName,
        'user': config.databaseUser,
        'password': config.databasePass,
        'schema': 'public',
        'table': False,
        'column': False,
        'where': False,
        'mode': 2,
    }
    
    nonstr_keys = [
        'host', 
        'port', 
        'mode', 
    ] 
    def __init__(self, **kwargs):
        gdal2db.__init__(self, **kwargs)

    def __call__(self):
        return gdal2db.__call__(self)


class lst2str(object):
    """
    str construction(str|unicode):
    -----------------
    pre_str - start string
    meso_lst
    pre_lst
    lst[line] -list iteration
    post_lst
    mseo_lst
    pre_lst
    lst[line] -list iteration
    post_lst
    meso_lst
    post_str - end string
    
    hooks - list hook array [<hook>, <fix hook> ]
    idents - list idents 
    """
    pre_str = ""
    post_str = ""
    pre_lst = ""
    post_lst = ""
    meso_lst = " "
    hooks = [
        ["'", "\\'"], 
        ['"', '\\"']
    ]
    indents = [
        " ", 
    ]
    
    def __init__(self, *args):
        self.lst = args
        
    def create_str(self):
        all_str = "{0}{1}".format(self.post_str, self.meso_lst)
        for line in self.lst:
            if isinstance(line, (str, unicode, int, float)):
                if isinstance(line, (int, float)):
                    line = str(line)
                # fix hooks
                for hook_lst in self.hooks:
                    hook = hook_lst[0]
                    fix_hook = hook_lst[-1]
                    if line.find(hook) != -1 and line.find(fix_hook) == -1:
                        line = line.replace(hook, fix_hook)
                #fix indent
                start_indent = True
                end_indent = True
                while start_indent or end_indent:
                    if line[0] in self.indents:
                        line = line[1:]
                    else:
                        start_indent = False
                    if line[-1] in self.indents:
                        line = line[:-1]
                    else:
                        end_indent = False
                # create all line string        
                all_str = "{0}{1}{2}{3}{4}".format(
                    all_str, 
                    self.pre_lst, 
                    line, 
                    self.post_lst, 
                    self.meso_lst
                )
            else:
                raise Exception(
                    "lst2str PARSER\nFOR:\n{0}\nPOS:\n{1}\n\nERROR:\n{2}".format(
                        '\n'.join(self.lst),
                        "{%s}"%string[line], 
                        "not srr or unicode type"
                    )
                )
        all_str = "{0}{1}".format(all_str, self.post_str)
        return all_str
    
    def __call__(self):
        return self.create_str()


class proj2str(lst2str):
    """
    projs :int - list default projections
    """
    projs = [
        32638,
        4326,
        3857,
        2154,
        310642901,
        4171,
        310024802,
        310915814,
        310486805,
        310702807,
        310700806,
        310547809,
        310706808,
        310642810,
        310642801,
        310642812,
        310032811,
        310642813,
        2986
    ]
    def __init__(self, *args):
        self.pre_lst = "EPSG:" 
        if args is ():
            self.lst = args
        else:
            self.lst = self.projs
            
    def __call__(self):
        return lst2str.__call__(self)


class comstring(object):

    def __init__(self):
        self.stdout_echo = False
        self.stderr_echo = False

    def run(self, cmd):
        _proc = Popen(
            cmd,
            shell=True,
            stdout=PIPE,
            stderr=PIPE
        )
        _res = _proc.communicate()
        _proc.wait()
        if _proc.returncode:
            print "ERR"
            if self.stderr_echo:
                print _res[1]
            return False
        else:
            if self.stdout_echo:
                print _res[0]
            print "OK"
            return True