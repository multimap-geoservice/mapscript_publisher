
import mapscript
import json
import inspect
import copy
import codecs


########################################################################
class PubMap(object):
    
    """
    Publisher Engine
    
    dict keys:
    ----------
    * OBJS = all objects mapscript in list - map index 0
    {'OBJ': str} = name of class for this dict
    {'OBJ_ARG': str|list|dict} - args for assigment constructor OBJ
    * {'OBJ_VAR': OBJS[int]} = index number for calss object OBJS
    {'SUB_OBJ': [{},{}]} - list subclss container or assigment objects
    {'<key>: None'} - if key value = None to create exteption
    {'MAP': str} - path to mapfile, for inhert mapscript.mapObj
    {'SCALES': list} - list for scale map
    
    * - use for engine only
    
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
        'OBJ_ARG', 
        'OBJ_VAR',
        'SUB_OBJ',
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
    scales list:
    [
    index 0 - all map scale
    index 1..n - scale number
    ]
    
    default(index =1)
    up_scale - scale first level
    """
    up_scale = 268435456

    """
    symplify geometry scale
    """
    #symplify_scale = [
        #220, 
        #200, 
        #180, 
        #160, 
        #140, 
        #120, 
        #100, 
        #80, 
        #60, 
        #40, 
        #20
    #]
    symplify_scale = []

    #----------------------------------------------------------------------
    def __init__(self, mapdict=None):
        self.debug_mapscript = False
        # init mapdict
        if isinstance(mapdict, dict):
            self.mapdict = mapdict
            
    def load_json(self, jsonfile):
        with open(jsonfile) as json_file:  
            self.mapdict = json.load(json_file, encoding='utf-8')

    def load_map(self, mapfile):
        mapdict = {
            'OBJ': 'mapscript.mapObj', 
            'OBJ_ARG': mapfile
        }

    def create_scales(self, up_scale=None):
        if not isinstance(up_scale, (int, float)):
            up_scale = self.up_scale
        # add scales 2 to down
        self.scales = [
            999999999,
            int(up_scale)
        ] 
        while not self.scales[-1] == 1:
            self.scales.append(self.scales[-1]/2)
        self.scales.append(0)

    def lst2str(self, lst):
        out = "["
        for dat in lst:
            if isinstance(dat, str):
                out = "{0}'{1}',".format(out, dat)
            else:
                out = "{0}{1},".format(out, dat)
        return "{}]".format(out) 

    def dct2str(self, dct):
        out = "{"
        for key in dct:
            dat = copy.deepcopy(dct[key])
            if isinstance(dat, str):
                out = "{0}{1}:'{2}',".format(out, key, dat)
            else:
                out = "{0}{1}:{2},".format(out, key, dat)
        return "{}}".format(out)
                
        
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
                        value = copy.deepcopy(_value)
                        value = value.popitem()[-1]
                        if _level: 
                            if minlevel <= _level <= maxlevel:
                                return value
                            else:
                                return None
                        else:
                            return minlevel, maxlevel, value
        return _value
        
        
    def method_processing(self, OBJ, method, value, _level):
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
            hook = "'"
            fix_hook = "\\'"
            if value.find(hook) != -1 and value.find(fix_hook) == -1:
                value = value.replace(hook, fix_hook)
            value = '\'{}\''.format(value)
        elif isinstance(value, dict):
            if value.has_key('OBJ'):
                value = 'eval(\'{}\')'.format(value['OBJ'])
            elif value.has_key('SUB_OBJ'):
                if isinstance(value['SUB_OBJ'], dict):
                    if not value['SUB_OBJ'].has_key('OBJ'):
                        raise Exception(
                            'in {} OBJ: not found'.format(value['SUB_OBJ'])
                        )
                    elif value['SUB_OBJ'].has_key('OBJ_ARG'):
                        OBJ_ARG = value['SUB_OBJ']['OBJ_ARG'] 
                        if isinstance(OBJ_ARG, dict):
                            OBJ_ARG = '**{}'.format(self.dct2str(OBJ_ARG))
                        elif isinstance(OBJ_ARG, (list, tuple)):
                            OBJ_ARG = '*{}'.format(self.lst2str(OBJ_ARG))
                        else:
                            OBJ_ARG = '{}'.format(OBJ_ARG)
                    else:
                        OBJ_ARG = ''
                    OBJ_VAR = self.engine(value['SUB_OBJ'], OBJ_ARG, _level)
                    value = OBJ_VAR
                else:
                    raise Exception(
                        'SUB_OBJ: {} is not dict'.format(value['SUB_OBJ'])
                    )
        elif value == None:
            raise Exception('None value in Template')

        # test syntax assigment method        
        try:
            test_assigment = eval('{0}.{1}'.format(OBJ, method))
        except Exception as err:
            raise Exception( 
                "ASSIGMENT METHOD\nFOR:\n{0}\nIN:\n{1}\nERROR:\n{2}".format(
                    '{0}.{1}'.format(OBJ, method), 
                    "type({0}) = {1}".format(
                        OBJ, 
                        eval("type({})".format(OBJ))
                        ), 
                    err
                )
            )
        # test assigment
        if inspect.ismethod(test_assigment):
            if isinstance(value, dict):
                assigment = '(**{})'.format(self.dct2str(value))
            elif isinstance(value, (list, tuple)):
                assigment = '(*{})'.format(self.lst2str(value))
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
            # run method processing and tracking exeptions
            try:
                exec(script_str)
            except Exception as err:
                raise Exception( 
                    "SINTAX\nFOR:\n{0}\nIN:\n{1}\nERROR:\n{2}".format(
                        script_str, 
                        "type({0}) = {1}".format(
                            OBJ, 
                            eval("type({})".format(OBJ))
                            ), 
                        err
                    )
                )
            
        return True
            
    def engine(self, _dict=None, SUB_OBJ=None, _level=False):
        """
        recursive engine for dict
        _dict - working dict
        SUB_OBJ - object for constructor _dict['OBJ'](SUB_OBJ):
            None - first start SUB_OBJ in MAP
            '' - first start SUB_OBJ in assigment
            self.OBJS[] - recursive start over self.engine
        _level - loop level for this _dict
        """
        if _dict is None:
            # insert dase value for mapdict
            _dict = copy.deepcopy(self.mapdict)
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
                if isinstance(_dict['SCALES'], list):
                    self.scales = _dict['SCALES']
                if isinstance(_dict['SCALES'], (int, float)):
                    self.create_scales(_dict['SCALES'])
                    _dict['SCALES'] = copy.deepcopy(self.scales)
                else:
                    self.create_scales()
                    _dict['SCALES'] = copy.deepcopy(self.scales)
            else:
                self.create_scales()
                _dict['SCALES'] = copy.deepcopy(self.scales)
        elif self.textOBJS not in SUB_OBJ:
                _dict['SCALES'] = self.scales
        # object operation
        if not _dict.has_key('OBJ_VAR'):
            # add OBJ Variable to OBJS list
            str_obj = '{0}({1})'.format(_dict['OBJ'], SUB_OBJ)
            try:
                eval_str_obj = eval(str_obj)
            except Exception as err:
                raise Exception( 
                    "SYNTAX\nIN:\n{0}\nFOR:\n{1}\nERROR:\n{2}".format(
                        json.dumps(
                            _dict,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '), 
                            ensure_ascii=False
                        ), 
                        str_obj, 
                        err
                    )
                )
            try:
                self.OBJS.append(eval_str_obj)
            except Exception as err:
                raise Exception( 
                    "STRUCTURE\nFOR:\n{0}\nIN:\n{1}\nASSIGMENT:\n{2}\nERROR:\n{3}".format(
                        json.dumps(
                            _dict,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '), 
                            ensure_ascii=False
                        ), 
                        "type({0}) = {1}".format(
                            SUB_OBJ, 
                            eval("type({})".format(SUB_OBJ))
                            ), 
                        str_obj, 
                        err
                    )
                )
            _dict['OBJ_VAR'] = '{0}[{1}]'.format(
                self.textOBJS, 
                len(self.OBJS) - 1
            )
            # create script debug
            if self.debug_mapscript:
                append_index = len(self.OBJS) - 1
                self.debug_mapscript.append(
                    '{0}{1}.append({2}) #create {1}[{3}]\n'.format(
                        ' '*8,
                        self.textOBJS, 
                        str_obj,
                        append_index
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
                                # scale
                                loopline = copy.deepcopy(levelline)
                                # test scale name
                                scale_test = True
                                if not loopline.has_key('name'):
                                    scale_test = False
                                elif loopline['name'] is None or loopline['name'] == '':
                                    scale_test = False
                                if not scale_test:
                                    raise Exception( 
                                        "STRUCTURE\nIN:\n{}\nKEY:'name' not found".format(
                                            json.dumps(
                                                loopline,
                                                sort_keys=True,
                                                indent=4,
                                                separators=(',', ': '), 
                                                ensure_ascii=False
                                        ), 
                                        )
                                    )
                                # name layer for scale level
                                loopline['name'] = '{0}{1}'.format(
                                    loopline['name'],
                                    numlevel
                                )
                                # add scale denoms
                                loopline['maxscaledenom'] = self.scales[
                                    numlevel
                                ]
                                loopline['minscaledenom'] = self.scales[
                                    numlevel + 1
                                ]
                                # simplify
                                if len(self.symplify_scale) > numlevel:
                                    simplify_text = 'simplifypt([shape],{})'.format(
                                        self.symplify_scale[numlevel]
                                    )
                                    loopline['setGeomTransform'] = simplify_text
                                # recursive engine
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
                line_tests = []
                line_tests.append(line_scale is not None)
                line_tests.append(line_scale is not False)
                line_tests.append(not isinstance(line_scale, tuple))
                if False not in line_tests:
                    # got to lines for processing
                    if isinstance(line_scale, list):
                        # loop in list
                        for subline in line_scale:
                            loop_scale = self.find_level_scale(subline, _level)
                            loop_tests = []
                            loop_tests.append(loop_scale is not None)
                            loop_tests.append(loop_scale is not False)
                            loop_tests.append(not isinstance(loop_scale, tuple))
                            if False not in loop_tests:
                                self.method_processing(
                                    _dict['OBJ_VAR'], 
                                    line,
                                    loop_scale,
                                    _level
                                )
                    else:
                        # one line
                        self.method_processing(
                            _dict['OBJ_VAR'], 
                            line,
                            line_scale,
                            _level
                        )
        return _dict['OBJ_VAR']
         
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
            separators=(',', ': '),
            ensure_ascii=False
        )
        if path:
            _file = codecs.open('{0}/{1}'.format(path, filename), 'w', encoding='utf-8')
            _file.write(_json)
            _file.close()
        else:
            print(_json)
        
    def debug_python_mapscript(self, path=debug_def_path, filename='debug.py'):
        """
        if path = False to output to stdout
        """
        self.debug_mapscript = [
            '#!/usr/bin/python3\n', 
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
            _file = codecs.open('{0}/{1}'.format(path, filename), 'w', encoding='utf-8')
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
