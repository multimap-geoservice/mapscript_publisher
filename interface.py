#!/usr/bin/python2
# -*- coding: utf-8 -*-

import psycopg2
from subprocess import Popen, PIPE

import config


class psqldb(object):
    
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
        str_temp = '{0}{1}=\\\\\'{2}\\\\\' ' 
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


class proj2str(object):
    """
    projs - list default projections
    """
    projs = [
        'EPSG:32638', 
        'EPSG:4326',
        'EPSG:3857',
        'EPSG:2154',
        'EPSG:310642901',
        'EPSG:4171',
        'EPSG:310024802',
        'EPSG:310915814',
        'EPSG:310486805',
        'EPSG:310702807',
        'EPSG:310700806',
        'EPSG:310547809',
        'EPSG:310706808',
        'EPSG:310642810',
        'EPSG:310642801',
        'EPSG:310642812',
        'EPSG:310032811',
        'EPSG:310642813',
        'EPSG:2986'
    ]
    def __init__(self, _projs=None):
        if _projs is not None:
            self.projs = _projs
            
    def __call__(self):
        return ' '.join(self.projs)


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