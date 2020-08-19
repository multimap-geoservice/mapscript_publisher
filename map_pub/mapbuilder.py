
import os
import json
from jinja2 import Environment, DictLoader
import ast
import inspect
import copy
import codecs

from .interface import pgsqldb


########################################################################
class BuildMap(object):
    """
    map builder from json file
    input = source json
    output = mapdict
    
    dict first keys:
    ----------
    {'IMODS': list} - list modules for import
    {'VARS': dict } - variables and values
    {'TEMPS': dict } - jinja2 templates
    {'MAP': dict } - start point map, permissio: dict or VAR or TEMP
    
    dict last keys for VARS, TEMPS or MAP:
    ----------
    {'VAR':str, 'arg1':'foo1', 'arg2':'foo2' }-variable in VARS declare(MAP|VARS|TEMPS): 
        VAR - variable name (in VARS)
        'arg' - argument for VARS[VAR] as var in format (var - arg:foo):
            str - '{}':str|list|dict text format, as: var.format(str|*list|**dict)
            int|float - '=':'str' math axpression as: '(1+{})/2'.format(var)
            dict - 'key':data - all data for dict, as: var['key'] = data
                   '-': key|[key] - delete key from dict as: del(var[key])
            list - for priority:
                int:data - data for index, as: var[index] = data
                '-':int|[int] - delete from index, as: del(var[index])
                   :data|[data] - delete from content, as: var.remove(data)
                '+':data|[data] - append data from list, as: var.append(data)
    {'RUN': any } - start module class or methos to MAP, VARS or TEMPS
    {'TEMP': } - jinja2 sintax template to TEMPS
    
    variables:
    ----------
    debug - False|True|filename - view debug build process
    mapjson - source json for building
    mapdict - output map dict for PubMap
    IMODS - list import modules
    VARS - dict variables
    TEMPS - dict templates
    MAP - TEMP|VAR|dict - mapfile
    """
    debug = False
    mapjson = False
    mapdict = {}
    IMODS = []
    VARS = {}
    TEMPS = {}
    MAP = {}
    
    #----------------------------------------------------------------------
    def __init__(self):
        self.procs = {
            "VAR": self.var_proc,
            "RUN": self.run_proc,
            "TEMP": self.temp_proc,
        }
        self.mapdict = self.MAP
    
    def debug_out(self, log, description, first=False):
        if isinstance(log, dict):
            log = json.dumps(
                log,
                sort_keys=True,
                indent=4,
                separators=(',', ': '), 
                ensure_ascii=False
            )
        log = "\n{0}\nSTEP: {1}\n{0}\n{2}".format(
            "-"*60, 
            description, 
            log
        )
        if isinstance(self.debug, str):
            if first:
                write_mode = 'w'
            else:
                write_mode = 'a'
            _file = codecs.open(self.debug, write_mode, encoding='utf-8')
            _file.write(log)
            _file.close()
        else:
            print (log)
    
    def var_proc(self, proc_data):
        """
        enter VAR:{} keys 
        """
        #init
        proc_nam = 'VAR'
        args = copy.deepcopy(proc_data)
        var = args.pop(proc_nam)
        if args == {}:
            args = None
        #proc
        if var in self.VARS.keys():
            if isinstance(var, str):
                var_data = copy.deepcopy(self.VARS[var])
                # init arguments
                if args is not None:
                    # pre-processing arguments in method recurs_proc
                    for argkey in args:
                        self.recurs_proc(args, argkey, 'VAR')
                        self.recurs_proc(args, argkey, 'RUN')
                    # string args processing
                    if isinstance(var_data, str):
                        args_key = '{}'
                        format_data = args[args_key]
                        try:
                            if isinstance(format_data, (str, int, float)):
                                var_data = var_data.format(format_data)
                            elif isinstance(format_data, list):
                                var_data = var_data.format(*format_data)
                            elif isinstance(format_data, dict):
                                var_data = var_data.format(**format_data)
                        except Exception as err:
                            raise Exception( 
                                "STR FORMAT\nFOR:\n{0}\nFORMAT:\n{1}\nERROR:\n{2}".format(
                                    var_data,
                                    format_data, 
                                    err
                                )
                            )
                    # numeric args processing (need TEST!!!)
                    elif isinstance(var_data, (int, float)):
                        args_key = '='
                        formula = args[args_key]
                        try:
                            formula = formula.format(var_data)
                        except Exception as err:
                            raise Exception( 
                                "STR FORMAT\nFOR:\n{0}\nFORMAT:\n{1}\nERROR:\n{2}".format(
                                    formula,
                                    var_data, 
                                    err
                                )
                            )
                        try:
                            var_data = eval(formula)
                        except Exception as err:
                            raise Exception( 
                                "MATH\nFORMULA:\n{0}\nERROR:\n{1}".format(
                                    formula,
                                    err
                                )
                            )
                    # dict pargs processing 
                    elif isinstance(var_data, dict):
                        # delete dict key
                        args_key = '-'
                        if args_key in args.keys():
                            keys_to_del = args[args_key]
                            if not isinstance(keys_to_del, list):
                                keys_to_del = [keys_to_del]
                            for del_key in keys_to_del:
                                if del_key in var_data.keys():
                                    del(var_data[del_key])
                                else:
                                    raise Exception( 
                                        "FOR DICT:\n{0}\nKEY:\n{1}\nnot found".format(
                                            var_data,
                                            del_key 
                                        )
                                    )
                            del(args[args_key])
                        # all dict procs 
                        try:
                            var_data.update(args)
                        except Exception as err:
                            raise Exception( 
                                "UPDATE\nDICT:\n{0}\nUPD DICT:\n{1}\nERROR:\n{2}".format(
                                    var_data,
                                    args, 
                                    err
                                )
                            )
                    # list args processing (need TEST!!!)
                    elif isinstance(var_data, list):
                        # int args_key
                        for args_key in [arg for arg in args if isinstance(arg, int)]:
                            try:
                                var_data[args_key] = args[args_key]
                            except Exception as err:
                                raise Exception( 
                                    "LIST\nLIST:\n{0}\nINDEX:\n{1}\nERROR:\n{2}".format(
                                        var_data,
                                        args_key, 
                                        err
                                    )
                                )
                        # '-' args_key
                        args_key = '-'
                        if args_key in args.keys():
                            list_data = args[args_key]
                            if not isinstance(list_data, list):
                                list_data = [list_data]
                            for next_data in list_data:
                                if isinstance(next_data, int):
                                    if next_data >= len(var_data) or next_data < 0:
                                        raise Exception( 
                                            "FOR:\n{0}\nINDEX:\n{1}\nout of range".format(
                                                var_data,
                                                next_data 
                                            )
                                        )
                                    else:
                                        del(var_data[next_data])
                                else:
                                    if next_data not in var_data:
                                        raise Exception( 
                                            "IN:\n{0}\nDATA:\n{1}\nnot found".format(
                                                var_data,
                                                next_data 
                                            )
                                        )
                                    else:
                                        var_data.remove(next_data)
                        # '+' args_key
                        args_key = '+'
                        if args_key in args.keys():
                            list_data = args[args_key]
                            if not isinstance(list_data, list):
                                list_data = [list_data]
                            for next_data in list_data:
                                try:
                                    var_data.append(next_data)
                                except Exception as err:
                                    raise Exception( 
                                        "APPEND\nLIST:\n{0}\nDATA:\n{1}\nERROR:\n{2}".format(
                                            var_data,
                                            next_data, 
                                            err
                                        )
                                    )
                # return var_data
                return var_data
            else:
                raise Exception('VAR:{} is not str'.format(var))
        else:
            raise Exception('VAR:{} not found'.format(var))

    def run_proc_item(self, item):
        if isinstance(item, (dict, str)):
            if isinstance(item, dict):
                if len(item) == 1:
                    # obj
                    obj = list(item.keys())[0]
                    # options
                    options = item[obj]
                    if isinstance(options, dict):
                        options = '(**{})'.format(options)
                    elif isinstance(options, (list, tuple)):
                        options = '(*{})'.format(options)
                    else:
                        options = '({})'.format(options)
                    # all
                    eval_item = '{0}{1}'.format(
                        obj, 
                        options 
                    )
                else:
                    raise Exception(
                        'All keys RUN:{} > 1, accesable 1 only'.format(item.keys())
                    )
            else:
                eval_item = item
            return eval_item
        else:
            raise Exception(
                'VAR:{} is not dict or str type'.format(item)
            )
        
    def run_proc(self, proc_data):
        """
        enter RUN:[] keys
        variants: "":str
                  {}:dict
        """
        #init
        proc_nam = 'RUN'
        data = proc_data[proc_nam]
        # import modules IMODS    
        for module in self.IMODS:
            try:
                exec('import {}'.format(module))
            except ImportError:
                exec('from . import {}'.format(module))
        # data is not list or tuple
        if not isinstance(data, (list, tuple)):
            if isinstance(data, dict):
                if inspect.isclass(eval(list(data.keys())[0])):
                    data = [data, "__call__()"]
                else:
                    data = [data]
            elif isinstance(data, str):
                data = [data]
            else:
                raise Exception('RUN data is not correct (dict or srt)')
        # RUN list
        separator = ''
        eval_data = ''
        for item in data:
            eval_data += '{0}{1}'.format(separator, self.run_proc_item(item))
            separator = '.'
        return eval(eval_data)

    def temp_proc(self, proc_data):
        #init
        proc_nam = 'TEMP'
        data = proc_data[proc_nam]
        #proc
        if isinstance(data, (list, tuple)):
            out_str = []
            for line in data:
                if isinstance(line, str):
                    out_str.append(line)
                elif isinstance(line, dict):
                    out_str.append(self.temp_str_parser(line))
                else:
                    out_str.append("{}".format(line))
            out_str='\n'.join(out_str)
        elif isinstance(data, dict):
            out_str = self.temp_str_parser(data)
        else:
            out_str = data
        return {"TEMP":out_str}
    
    def recurs_proc(self, val, key, proc):
        if isinstance(val[key], list):
            for new_key in range(len(val[key])):
                self.recurs_proc(val[key], new_key, proc)
        elif isinstance(val[key], dict):
            if isinstance(proc, int) and 'VAR' in val[key].keys():
                # create vars_queue
                next_var = val[key]['VAR']
                if next_var == self.vars_queue[proc][0]:
                    # find copy VARS to sub-VARS
                    raise Exception(
                        'sub-VARS:{0} == VARS:{1}'.format(
                            next_var, 
                            self.vars_queue[proc][0]
                        )
                    )
                elif next_var not in self.vars_queue[proc]:
                    # find list var
                    self.vars_queue[proc].append(next_var)
            elif proc in val[key].keys():
                # all key
                val[key] = self.procs[proc](val[key])
            else: 
                for new_key in val[key]:
                    self.recurs_proc(val[key], new_key, proc)

    def build_vars(self):
        """
        if key "VARS" to step 1
        """
        # create list index
        index = 0
        self.vars_queue = []
        for key in self.VARS:
            self.vars_queue.append([key])
            self.recurs_proc(self.VARS, key, index)
            index += 1
        # sort and test variables
        sort = False
        while not sort:
            sort = True
            sort_queue = [my[0] for my in self.vars_queue]
            for var in self.vars_queue:
                var_index = self.vars_queue.index(var)
                for subvar in var[1:]:
                    # find subvar in VARS
                    if subvar not in sort_queue:
                        raise Exception(
                            'sub-VARS:{0} for VARS:{1} is not found'.format(
                                subvar, 
                                var[0]
                            )
                        )
                    else:
                        subvar_index = sort_queue.index(subvar)
                    # test fro cross depends in VARS
                    if var[0] in self.vars_queue[subvar_index]:
                        raise Exception(
                            'Found cross depends for sub-VARS:{0} to VARS:{1}'.format(
                                subvar, 
                                var[0]
                            )
                        )
                    # move VARS for next init as sub-VAR
                    if subvar_index > var_index:
                        mv_var = self.vars_queue.pop(subvar_index)
                        self.vars_queue.insert(var_index, mv_var)
                        sort = False
                        break
                if not sort:
                    break
        self.vars_queue = sort_queue
        # init VAR
        for key in self.vars_queue:
            self.recurs_proc(self.VARS, key, 'VAR')
        # init RUN
        for key in self.vars_queue:
            self.recurs_proc(self.VARS, key, 'RUN')
            
    def temp_str_parser(self, in_dict):
        if not isinstance(in_dict, dict):
            raise Exception( 
                "TEMP PARSER\nFOR:\n{}\nERROR:\nis not dict".format(in_dict)
            )
        temp2json = json.dumps(
                in_dict,
                sort_keys=True,
                indent=4,
                separators=(',', ': '), 
                ensure_ascii=False
            ).split("\n")
        temp2text = []
        post_temp_cont = False
        temp_index = -1
        for string in temp2json:
            temp_index += 1
            if post_temp_cont:
                post_temp_cont = False
                continue
            temp_pos = string.find("TEMP") - 1
            if temp_pos != -2:
                # find template
                try:
                    data = json.loads(
                        json.dumps(
                            ast.literal_eval(
                                "{%s}"%string[temp_pos:]
                            )['TEMP'].split("\n"), 
                            ensure_ascii=False
                        )
                    )
                    data = ast.literal_eval(
                        "{%s}"%string[temp_pos:]
                        )['TEMP'].split("\n")
                except Exception as err:
                    raise Exception( 
                        "TEMP PARSER\nFOR:\n{0}\nPOS:\n{1}\n\nERROR:\n{2}".format(
                            '\n'.join(temp2json),
                            "{%s}"%string[temp_pos:], 
                            err
                        )
                    )
                # find pre template
                pre_temp = temp2json[temp_index-1]
                pre_pos = pre_temp.find("{")
                if ": {" in pre_temp:
                    pre_temp = pre_temp[:pre_temp.find(": {")+2]
                else:
                    pre_temp = " " * pre_pos
                del temp2text[-1]
                # find post template
                post_temp = temp2json[temp_index+1]
                if "}," in post_temp:
                    post_temp = ','
                else:
                    post_temp = ''
                post_temp_cont = True
                # append template
                first = 1
                last = len(data)
                index = 0
                for pos in data:
                    index += 1
                    if index == first:
                        prefix = pre_temp
                    else:
                        prefix = " " * len(pre_temp)
                    if index == last:
                        postfix = post_temp
                    else:
                        postfix = ""
                    temp2text.append('{0}{1}{2}'.format(
                        prefix, 
                        pos, 
                        postfix
                    ))
            else:
                temp2text.append(string)
        return "\n".join(temp2text)    
    
    def build_temps(self):
        """
        if key "TEMPS" to step 2
        """
        # init VAR
        for key in self.TEMPS:
            self.recurs_proc(self.TEMPS, key, 'VAR')
        # temp step: list temp to text
        for key in self.TEMPS:
            self.recurs_proc(self.TEMPS, key, 'TEMP')
        # temp step: temp to str to list
        for key in self.TEMPS:
            if isinstance(self.TEMPS[key], dict):
                temp2text = self.temp_str_parser(self.TEMPS[key])
                full_template = temp2text
            elif isinstance(self.TEMPS[key], list):
                full_template = ''
                for block in self.TEMPS[key]:
                    if isinstance(block, dict):
                        temp2text = self.temp_str_parser(block)
                    else:
                        temp2text = block
                    full_template = "{0}\n{1}".format(full_template, temp2text)
            self.TEMPS[key] = full_template
                    
            
    def build_map(self):
        """
        build map - step 3
            variants: MAP: TEMP
                      MAP: VAR
                      MAP: {}
        """
        if 'TEMP' in self.MAP.keys():
            # MAP from section TEMPS
            maptemp = self.MAP['TEMP']
            if maptemp in self.TEMPS.keys():
                env = Environment(
                    loader=DictLoader(self.TEMPS)
                )
                template = env.get_template(maptemp)
                map_txt = template.render(**self.VARS)
                #self.MAP = ast.literal_eval(map_txt)
                self.MAP = json.loads(
                    json.dumps(ast.literal_eval(map_txt), ensure_ascii=False)
                )
            else:
                raise Exception(
                    'TEMPS: "{}" for MAP not found'.format(maptemp)
                )
        elif 'VAR' in self.MAP.keys():
            # MAP from section VAR
            mapvar = self.MAP['VAR']
            if mapvar in self.TEMPS.keys():
                self.MAP = self.VARS[mapvar].copy()
            else:
                raise Exception(
                    'VARS: "{}" for MAP not found'.format(mapvar)
                )
        # init VAR
        for key in self.MAP:
            self.recurs_proc(self.MAP, key, 'VAR')
        # init RUN
        for key in self.MAP:
            self.recurs_proc(self.MAP, key, 'RUN')
            
    def build(self):
        """
        Build for key "MAP":
            * if {} to dict and VAR, RUN - TEMP ignore
            * if "VAR":"var_name" to {} frpm variable and VAR, RUN - TEMP ignore
            * if "TEMP":"temp_name" to
                1 step use VAR
                2 step use RUN
                3 render TEMP
        """
        # trst load map json
        if self.mapjson:
            if self.debug:
                self.debug_out(self.mapjson, 'Load Map JSON file', first=True)
        else:
            raise Exception('Map JSON is not loaded')
        # init import modules  
        if 'IMODS' in self.mapjson.keys():
            if isinstance(self.mapjson['IMODS'], list):
                self.IMODS = self.mapjson['IMODS'][:]
                if self.debug:
                    self.debug_out(self.IMODS, 'List import Modules')
        # VARS build - etap 1
        if 'VARS' in self.mapjson.keys():
            if isinstance(self.mapjson['VARS'], dict):
                self.VARS = copy.deepcopy(self.mapjson['VARS'])
                if self.debug:
                    self.debug_out(self.VARS, 'Input VARS')
                self.build_vars()
                if self.debug:
                    self.debug_out(self.VARS, 'Output VARS')
        # TEMPS build - etap 2
        if 'TEMPS'in self.mapjson.keys():
            if isinstance(self.mapjson['TEMPS'], dict):
                self.TEMPS = copy.deepcopy(self.mapjson['TEMPS'])
                if self.debug:
                    self.debug_out(self.TEMPS, 'Input TEMPS')
                self.build_temps()
                if self.debug:
                    for temp in self.TEMPS:
                        self.debug_out(self.TEMPS[temp], 'Output TEMP: {}'.format(temp))
        # MAP build - etap 3
        if 'MAP' in self.mapjson.keys():
            if isinstance(self.mapjson['MAP'], dict):
                self.MAP = copy.deepcopy(self.mapjson['MAP'])
                if self.debug:
                    self.debug_out(self.MAP, 'Input MAP')
                self.build_map()
                if self.debug:
                    self.debug_out(self.MAP, 'Output MAP')
                self.mapdict = self.MAP
            else:
                raise Exception('Section MAP is not dict')
        else:
            raise Exception('Section MAP not found')
    
    def get_json(self):
        self.build()
        return json.dumps(
            self.mapdict,
            sort_keys=True,
            indent=4,
            separators=(',', ': '), 
            ensure_ascii=False
        )
    
    def __call__(self):
        self.build()
        return self.mapdict


########################################################################
class BuildMapRes(BuildMap):
    """
    BuildMap and Save/Load operations
    """
    #create resource for save
    create_res = False

    #----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """
        Init Constructor of BuildMap
        """
        BuildMap.__init__(self, *args, **kwargs)

    def load4file(self, path):
        """
        Load json template from file

        path - path for load json template
        """
        with open(path) as _file:  
            self.mapjson = json.load(_file)
     
    def load4pgsql(self, query, **kwargs):
        """
        Load json template map from postgresql database
        
        query - SQL query one data to json
        **kwargs - connect **dict as interface.pgsqldb.pg_defaults
        """
        #psql = pgsqldb(**kwargs)
        pass

    def save2file(self, path=None):
        """
        save json build map to file
        
        path - path to save json file
        """
        json_ = self.get_json()
        if path:
            dir_ = os.path.dirname(path)
            if self.create_res:
                if not os.path.isdir(dir_):
                    os.makedirs(dir_)
            if os.path.isdir(dir_):
                with codecs.open(path, 'w', encoding='utf-8') as file_:
                    file_.write(json_)
            else:
                raise Exception('Dir {} not found'.format(dir_))
        else:
            print(json_)
        
    def save2pgsql(self, table, name, col_name, col_cont, **kwargs):
        """
        save json build map to postgresql database
        
        table - table name
        name - map name
        col_name - column for map name
        col_cont - column for filename or content:
            if not kwargs['path'] - to col_name save content
            if kwargs['path']= hibrid data db/path:
                path - to col_name save filename, content save to file path
        kwargs['path'] - path for hibrid data db/path
        kwargs['columns'] - additional column for database, Dict format: 
            {
                "cilumn_name": "column_data(::column_type)"
            }
            column_type - if str to type
        kwargs[all next keys] - connect **dict as interface.pgsqldb.pg_defaults
        """

        # kwargs
        if 'path' in kwargs.keys():
            cont = kwargs.pop('path')
            cont_type = 'text'
            self.save2file(path=cont)
        else:
            cont = self.get_json()
            cont = cont.replace("'", "''")
            cont_type = 'json'
        
        # SQL data
        SQL = {
            'create_table': """
                create table if not exists "{0}" (
                    "id" serial primary key,
                    "{1}" text unique,
                    "{2}" text
                )
                """,
            'find_name': """
                select *
                from "{0}"
                where "{1}" = '{2}'; 
                """,
            'insert_all': """
                insert into "{0}" 
                (
                    "{1}",
                    "{2}"{6}
                )
                values
                (
                    '{3}',
                    '{4}'::{5}{7}
                );
                """,
            'update_all': """
                update "{0}"
                set "{2}" = '{4}'::{5}{6}
                where "{1}" = '{3}';            
                """,
            'find_extra': """
                select *
                from information_schema.columns
                where table_name = '{0}'
                and column_name = '{1}' 
                """,
            'alter_extra': """
                alter table "{0}"
                add column "{1}" {2};
                """,
        }
        # init db
        psql = pgsqldb(**kwargs)

        # create table
        if self.create_res:
            psql.sql(
                SQL['create_table'].format(
                    table, 
                    col_name, 
                    col_cont
                )
            )
            psql.commit()
        
        # extra columns
        ins_ex_cols = ""
        ins_ex_vals = ""
        upd_ex_sets = ""
        if 'columns' in kwargs.keys():
            for col_extra in kwargs['columns']:
                cont_extra = kwargs['columns'][col_extra]
                if isinstance(cont_extra, int):
                    type_extra = 'int'
                elif isinstance(cont_extra, float):
                    type_extra = 'float'
                elif isinstance(cont_extra, (dict, list, tuple)):
                    type_extra = 'text'
                elif isinstance(cont_extra, str):
                    if "::" in cont_extra:
                        type_extra = cont_extra.split("::")[-1]
                        cont_extra = cont_extra.split("::")[0]
                    else:
                        type_extra = 'text'
                # find & alter extra columns
                if self.create_res:
                    psql.sql(SQL['find_extra'].format(table, col_extra))
                    if psql.fetchone() is None:
                        psql.sql(
                            SQL['alter_extra'].format(
                                table, 
                                col_extra, 
                                type_extra 
                            )
                        )
                        psql.commit()
                # text data for extra columns
                ins_ex_cols = '{0},\n{1}"{2}"'.format(
                    ins_ex_cols, 
                    " "*20, 
                    col_extra
                )
                ins_ex_vals = "{0},\n{1}'{2}'".format(
                    ins_ex_vals, 
                    " "*20, 
                    cont_extra
                )
                upd_ex_sets = '{0},\n{1}"{2}" = \'{3}\''.format(
                    upd_ex_sets, 
                    " "*20, 
                    col_extra, 
                    cont_extra
                )
                
        # query map name and insert/update all
        psql.sql(
            SQL['find_name'].format(
                table, 
                col_name, 
                name
            )
        )
        if psql.fetchone() is None:
            psql.sql(
                SQL['insert_all'].format(
                    table, 
                    col_name, 
                    col_cont, 
                    name, 
                    cont, 
                    cont_type, 
                    ins_ex_cols, 
                    ins_ex_vals
                )
            )
        else:
            psql.sql(
                SQL['update_all'].format(
                    table, 
                    col_name, 
                    col_cont, 
                    name, 
                    cont, 
                    cont_type, 
                    upd_ex_sets
                )
            )

        # end db work
        psql.commit()
        psql.close()