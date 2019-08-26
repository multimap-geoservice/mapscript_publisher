# -*- coding: utf-8 -*-
# encoding: utf-8

import os
import ogr
import json
import copy

from owslib.wfs import WebFeatureService

from owslib.etree import etree
from owslib.fes import (
    PropertyIsBetween,  # между
    PropertyIsEqualTo,  # =
    PropertyIsGreaterThan,  # >
    PropertyIsGreaterThanOrEqualTo,  # >=
    PropertyIsLessThan,  # <
    PropertyIsLessThanOrEqualTo,  # <=
    PropertyIsLike,  #как  * . ! 
    PropertyIsNotEqualTo,  # !=
    PropertyIsNull,  # =NULL
    BBox
)
import urllib
from wsgiref.simple_server import make_server

########################################################################
class WfsFilter(object):
    """
    create filter for wfs
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.epsg_code_cap = None
        self.epsg_code_use = None
        self.layer_property_cap = None
        self.layer_property_use = None
        self.filter_tags = {
            "and": self.filter_tag_and,
            "or": self.filter_tag_or,
            "not": self.filter_tag_not,
            "filter": self.filter_tag_filter,
        } 
        self.filter_opts = {
            "=": self.filter_opt_equal_to,
            "!=": self.filter_opt_not_equal_to,
            ">": self.filter_opt_greater_than,
            ">=": self.filter_opt_graater_than_or_equal_to,
            "<": self.filter_opt_less_than,
            "<=": self.filter_opt_less_than_or_equal_to,
            "between": self.filter_opt_beetwen,
            "null": self.filter_opt_null,
            "like": self.filter_opt_like,
            "bbox": self.filter_opt_bbox,
        }
        
    def filter_engine(self, content, bool_tag=True, filter_tag=True):
        all_filter = u""
        for key in content:
            cont_key = copy.deepcopy(content[key])
            if self.filter_tags.has_key(key):
                if isinstance(cont_key, dict):
                    cont = self.filter_engine(
                                cont_key, 
                                bool_tag=False, 
                                filter_tag=False
                            )
                    all_filter = "{0}{1}".format(
                        all_filter,
                        self.filter_tags[key](cont)
                    )
                elif isinstance(cont_key, list):
                    cont_arr = []
                    for cont_next in cont_key:
                        cont_arr.append(
                            self.filter_engine(
                                cont_next, 
                                bool_tag=True, 
                                filter_tag=False
                            )
                        )
                    all_filter = "{0}{1}".format(
                        all_filter,
                        self.filter_tags[key](*cont_arr)
                    )
            else:
                for f_opt in cont_key:
                    if self.filter_opts.has_key(f_opt):
                        f_arg = cont_key[f_opt]
                        if not f_arg:
                            f_kwarg = {}
                            f_arg = []
                        elif isinstance(f_arg, dict):
                            f_kwarg = copy.deepcopy(f_arg)
                            f_arg = []
                        elif isinstance(f_arg, list):
                            f_kwarg = {}
                        else:
                            f_kwarg = {}
                            f_arg = [f_arg] 
                        f_arg.insert(0, key)
                        all_filter = "{0}{1}".format(
                            all_filter, 
                            self.filter_opts[f_opt](*f_arg, **f_kwarg)
                        )
                    else:
                        raise Exception(
                            "Error: filter option '{}' not found".format(f_opt)
                        )
        if bool_tag:
            if len(content) != 1:
                all_filter = self.filter_tags['and'](all_filter)
        if filter_tag:
            all_filter = self.filter_tags['filter'](all_filter)
        return all_filter
   
    def dec_filters_tags(method):
        def wrapper(self, *args):
            if args:
                all_args = []
                for arg in args:
                    all_args.append(arg)
                return method(self).format("".join(all_args))
            else:
                return ["filter opts"]
        return wrapper
   
    @dec_filters_tags
    def filter_tag_and(self):
        return "<AND>{}</AND>"
    
    @dec_filters_tags
    def filter_tag_or(self):
        return "<OR>{}</OR>"
   
    @dec_filters_tags
    def filter_tag_not(self):
        return "<NOT>{}</NOT>"
    
    @dec_filters_tags
    def filter_tag_filter(self):
        return "<Filter>{}</Filter>"

    def data2literal(self, data):
        if isinstance(data, (int, float)):
            data = str(data)
        return u"{}".format(data.decode('utf-8'))

    def dec_filters_literal_opts(method):
        def wrapper(self, propertyname=None, literal=None):
            if propertyname and literal:
                tag = method(
                    self, 
                    propertyname=self.data2literal(propertyname), 
                    literal=self.data2literal(literal), 
                )
                return etree.tostring(tag.toXML()).decode("utf-8")
            elif not propertyname and not literal:
                return "value"
            else:
                raise Exception("Filter literal error")
        return wrapper
    
    def dec_test_propertiname(method):
        def wrapper(self, propertyname=None, *args, **kwargs):
            if propertyname: 
                layer_property_cap = [
                    self.data2literal(my) 
                    for my 
                    in self.layer_property_cap
                ] 
                if self.data2literal(propertyname) not in layer_property_cap:
                    raise Exception(
                        "Filter: error 'layer_property'='{}' not in capabilites".format(
                            propertyname
                        )
                    )
            return method(self, propertyname, *args, **kwargs)
        return wrapper
    
    @dec_test_propertiname
    @dec_filters_literal_opts 
    def filter_opt_equal_to(self, **kwargs):
        return PropertyIsEqualTo(**kwargs)

    @dec_test_propertiname
    @dec_filters_literal_opts 
    def filter_opt_not_equal_to(self, **kwargs):
        return PropertyIsNotEqualTo(**kwargs)

    @dec_test_propertiname
    @dec_filters_literal_opts 
    def filter_opt_greater_than(self, **kwargs):
        return PropertyIsGreaterThan(**kwargs)

    @dec_test_propertiname
    @dec_filters_literal_opts 
    def filter_opt_graater_than_or_equal_to(self, **kwargs):
        return PropertyIsGreaterThanOrEqualTo(**kwargs)

    @dec_test_propertiname
    @dec_filters_literal_opts 
    def filter_opt_less_than(self, **kwargs):
        return PropertyIsLessThan(**kwargs)

    @dec_test_propertiname
    @dec_filters_literal_opts 
    def filter_opt_less_than_or_equal_to(self, **kwargs):
        return PropertyIsLessThanOrEqualTo(**kwargs)

    @dec_test_propertiname
    def filter_opt_beetwen(self, propertyname=None, lower=None, upper=None):
        if propertyname and lower and upper:
            tag = PropertyIsBetween(
                propertyname=self.data2literal(propertyname), 
                lower=self.data2literal(lower), 
                upper=self.data2literal(upper), 
            )
            return etree.tostring(tag.toXML()).decode("utf-8")
        elif not propertyname and not lower and not upper:
            return [
                "lower value", 
                "upper value", 
            ]
        else:
            raise Exception("Filter error")

    @dec_test_propertiname
    def filter_opt_null(self, propertyname=None):
        if propertyname:
            tag = PropertyIsNull(
                propertyname=self.data2literal(propertyname), 
            )
            return etree.tostring(tag.toXML()).decode("utf-8")
        else:
            return None

    @dec_test_propertiname
    def filter_opt_like(self, propertyname=None, literal=None):
        if propertyname and literal:
            tag = PropertyIsLike(
                propertyname=self.data2literal(propertyname), 
                literal=self.data2literal(literal), 
                wildCard="*", 
                singleChar=".", 
                escapeChar="!", 
            )
            return etree.tostring(tag.toXML()).decode("utf-8")
        elif not propertyname and not literal:
            return "value"
        else:
            raise Exception("Filter error")
        
    def dec_test_epsg_code(method):
        def wrapper(self, propertyname=None, **kwargs):
            if kwargs.get("epsg_code", False):
                epsg_code_cap = [self.data2literal(my) for my in self.epsg_code_cap] 
                if self.data2literal(kwargs["epsg_code"]) not in epsg_code_cap:
                    raise Exception(
                        "Filter: error 'epsg_code'='{}' not in capabilites".format(
                            kwargs["epsg_code"]
                        )
                    )
            else:
                kwargs["epsg_code"] = self.epsg_code_use
            return method(self, propertyname=None, **kwargs)
        return wrapper

    @dec_test_epsg_code
    def filter_opt_bbox(self, propertyname=None, coord=None, epsg_code=None):
        if coord:
            tag = BBox(
                bbox=coord, 
                crs="EPSG:{}".format(epsg_code), 
            )
            return etree.tostring(tag.toXML()).decode("utf-8")
        elif not propertyname and not coord:
            return {
                "coord": [
                    "Upper Left Coord", 
                    "Lower Left Coord", 
                    "Upper Right Coord", 
                    "Lower Right Coord", 
                    ],
                "epsg_code": "epsg code projection",
            }
        else:
            raise Exception("Filter bbox: error")


########################################################################
class GeoCoder(WfsFilter):
    """
    geocoder
    """
    wfs_ver = '1.1.0'
    

    #----------------------------------------------------------------------
    def __init__(self, wfs_url='http://localhost:3007', debug=False):
        WfsFilter.__init__(self)
        self.debug = debug
        self.wfs = WebFeatureService(wfs_url, version=self.wfs_ver)
        self.capabilities = self.get_capabilities()
        self._set_def_resp_params()
        
    def _set_def_resp_params(self):
        self.epsg_code_cap = self.capabilities["epsg_code"]
        self.epsg_code_use = self.capabilities["epsg_code"][0]
        self.layer_property_cap = self.capabilities["layer_property"]
        self.layer_property_use = self.capabilities["layer_property"]
        self.response = []
        
    def echo2json(self, dict_):
        print json.dumps(
            dict_,
            sort_keys=True,
            indent=4,
            separators=(',', ': '), 
            ensure_ascii=False, 
        )
 
    def gml2json(self, gml):
        json_out = {
            "type": "FeatureCollection",
            "features": [],
        }
        geom_crs = None
        tree = etree.fromstring(gml)
        nsmap = tree.nsmap
        tag_name = lambda t: t.tag.split("{%s}" % nsmap[t.prefix])[-1]
        for feature in tree.getiterator("{%s}featureMember" % nsmap["gml"]):
            json_feature = {
                "type": "Feature",
                "id": None,
                "properties": {},
                "geometry": None,
            }
            for layer in feature.iterfind('{%s}*' % nsmap["ms"]):
                json_feature["id"] = layer.get("{%s}id" % nsmap["gml"], None)
                json_feature["properties"]["layer"] = tag_name(layer)
                for prop in layer.iterfind('{%s}*' % nsmap["ms"]):
                    get_prop = True
                    for geom in prop.iterfind("{%s}*" % nsmap["gml"]):
                        get_prop = False
                        geom_crs = geom.get("srsName", None)
                        ogr_geom = ogr.CreateGeometryFromGML(etree.tostring(geom))
                        if isinstance(ogr_geom, ogr.Geometry):
                            json_feature["geometry"] = json.loads(
                                ogr_geom.ExportToJson()
                            )
                    if get_prop:
                        json_feature["properties"][tag_name(prop)] = prop.text
                json_out["features"].append(json_feature)
        if geom_crs:
            geom_crs = geom_crs.split(":")
            if len(geom_crs) == 2:
                if geom_crs[0].lower() == "epsg":
                    json_out["crs"] = {
                        "type": "EPSG",
                        "properties": {
                                "code": geom_crs[-1],
                            },
                        }
        if self.debug:
            self.echo2json(json_out)
        return json_out
   
    def get_help(self):
        filter_tags = {
            my: self.filter_tags[my]()
            for my
            in self.filter_tags
        }
        comparsion_opts = {
            my: self.filter_opts[my]()
            for my
            in self.filter_opts
            if isinstance(self.filter_opts[my](),(str, unicode, list))
        }
        spatial_opts = {
            my: self.filter_opts[my]()
            for my
            in self.filter_opts
            if isinstance(self.filter_opts[my](),dict)
        }
        json_out = {
            "filter":{
                "tags": filter_tags,
                "comparsion opts": comparsion_opts,
                "spatial opts": spatial_opts,
                "example": {
                    "tag": [
                        {
                            "tag": {
                                "property 1": {
                                    "comparsion opt": "value",
                                },
                                "property 2": {
                                    "comparsion opt 1": "value",
                                    "comparsion opt 2": ["value 1", "value 2"],
                                },
                            }, 
                        },
                        {
                            "property 3": {
                                "comparsion opt": "value",
                                "spatial opt": {
                                    "opt key 1": "value", 
                                    "opt key 2": "value",
                                },
                            },
                        }, 
                    ],
                },
            }, 
        }
        if self.debug:
            self.echo2json(json_out)
        return json_out
    
    def get_info(self):
        json_out = {}
        for layer_name in self.wfs.contents:
            wfs_opts = self.wfs.contents[layer_name].metadataUrls[0]
            wfs_opts["gml"] = self.wfs.contents[layer_name].outputFormats[0]
            json_out[layer_name] = {
                "wgs84_bbox": list(self.wfs.contents[layer_name].boundingBoxWGS84),
                "wfs_opts": wfs_opts, 
            }
        if self.debug:
            self.echo2json(json_out)
        return json_out
    
    def get_capabilities(self):
        json_out = {
            "max_features": None,
            "filter": None,
            "layers": {},
        }
        all_epsg_code = None
        all_layer_property = None
        for layer_name in self.wfs.contents:
            wfs_response = self.wfs.getfeature(
                typename=layer_name, 
                maxfeatures=1
            )
            tree = etree.fromstring(wfs_response.read())
            nsmap = tree.nsmap
            layer_property = []
            for feature in tree.getiterator("{%s}featureMember" % nsmap["gml"]):
                for layer in feature.iterfind('{%s}*' % nsmap["ms"]):
                    for meta in layer.iterfind('{%s}*' % nsmap["ms"]):
                        meta_name = meta.tag.split("{%s}" % nsmap[meta.prefix])[-1]
                        layer_property.append(meta_name)
            epsg_code = [my.code for my in self.wfs.contents[layer_name].crsOptions]
            json_out['layers'][layer_name] = {
                "epsg_code": epsg_code, 
                "layer_property": layer_property,
                "max_features": None,
                "filter": None,
            }
            if not all_layer_property:
                all_layer_property = layer_property
            else:
                all_layer_property = list(
                    set(all_layer_property).intersection(set(layer_property))
                )
            if not all_epsg_code:
                all_epsg_code = epsg_code
            else:
                all_epsg_code = list(
                    set(all_epsg_code).intersection(set(epsg_code))
                )
        json_out.update({
            "epsg_code": all_epsg_code,
            "layer_property": all_layer_property,
        })
        if self.debug:
            self.echo2json(json_out)
        return json_out

    def get_feature(self, layer_name, filter_json=None, **kwargs):
        feature_args = [
            "propertyname", 
            "maxfeatures", 
            "srsname"
        ]
        out_args = {
            "typename": layer_name,
        }
        if isinstance(filter_json, dict):
            out_args["filter"] = self.filter_engine(filter_json)

        for arg in feature_args:
            if kwargs.get(arg, None):
                out_args[arg] = kwargs[arg]
                
        return self.gml2json(
            self.wfs.getfeature(**out_args).read()
        )
    
    def merge_gjson(self, gjson):
        if not isinstance(self.response, list) or not isinstance(gjson, dict):
            return
        elif not gjson['features']:
            return
        elif not self.response:
            self.response = [gjson]
        else:
            gj = {}
            gj_test_fea = copy.deepcopy(gjson['features'][0])
            gj['props'] = set(gj_test_fea['properties'].keys())
            if isinstance(gj_test_fea['geometry'], dict):
                gj['crs'] = copy.deepcopy(gjson['crs'])
                gj['geom'] = gj_test_fea['geometry']['type']
            else:
                gj['crs'] = None
                gj['geom'] = None
            merge = False
            for lst_element in self.response:
                if isinstance(lst_element, dict):
                    lst = {}
                    lst_test_fea = copy.deepcopy(lst_element['features'][0])
                    lst['props'] = set(lst_test_fea['properties'].keys())
                    if isinstance(lst_test_fea['geometry'], dict):
                        lst['crs'] = copy.deepcopy(lst_element['crs'])
                        lst['geom'] = lst_test_fea['geometry']['type']
                    else:
                        lst['crs'] = None
                        lst['geom'] = None
                    if gj == lst:
                        index = self.response.index(lst_element)
                        self.response[index]['features'].extend(gjson['features'])
                        merge = True
                        break
            if not merge:
                self.response.append(gjson)
    
    def get_response(self, request_):
        def_com_opts = {
            "layer_name": [u"{}", "layer"],
            "filter_json": [{}, "filter"],
            "propertyname": [[], "layer_property"],
            "maxfeatures": [u"{}", "max_features"],
            "srsname": [u"EPSG:{}", "epsg_code"],
        }
        self._set_def_resp_params()  # start response
        capabilities = copy.deepcopy(self.capabilities)
        cap_layers = {my:{} for my in capabilities["layers"]}
        req_layers = {
            my:request_.get("layers", cap_layers)[my] 
            for my 
            in request_.get("layers", cap_layers)
            if cap_layers.has_key(my)
        }
        req_opts = copy.deepcopy(request_)
        if req_opts.has_key("layers"):
            del(req_opts["layers"])
        for layer in req_layers:
            capabilities['layers'][layer]["layer"] = None
            layer_opts = {"layer": layer}
            layer_opts.update(req_opts)
            if isinstance(req_layers[layer], dict):
                layer_opts.update(req_layers[layer])
            com_opts = copy.deepcopy(def_com_opts)
            for opt in com_opts:
                cap_param = capabilities['layers'][layer][def_com_opts[opt][1]]
                param = layer_opts.get(com_opts[opt][1], None)
                if cap_param:
                    # test param from capabilites
                    cap_param = [self.data2literal(my) for my in cap_param]
                    if isinstance(param, list):
                        param = [self.data2literal(my) for my in param]
                        param = list(set(param).intersection(set(cap_param)))
                    elif isinstance(param, (str, unicode, int, float)):
                        param = self.data2literal(param)
                        if param not in cap_param:
                            param = None
                if param:
                    if isinstance(com_opts[opt][0], unicode):
                        if isinstance(param, (str, unicode, int, float)):
                            com_opts[opt] = com_opts[opt][0].format(param)
                    elif isinstance(com_opts[opt][0], (dict)):
                        if isinstance(param, dict):
                            com_opts[opt] = copy.deepcopy(param)
                    elif isinstance(com_opts[opt][0], list):
                        if isinstance(param, list):
                            com_opts[opt] = copy.deepcopy(param)
                    else:
                        com_opts[opt] = None
                else:
                    com_opts[opt] = None
            # data for use in filter
            self.epsg_code_cap = capabilities["layers"][layer]["epsg_code"]
            self.epsg_code_use = layer_opts.get(
                "epsg_code", 
                capabilities["layers"][layer]["epsg_code"][0]
            )
            self.layer_property_cap = capabilities["layers"][layer]["layer_property"]
            self.layer_property_use = layer_opts.get(
                "layer_property", 
                capabilities["layers"][layer]["layer_property"]
            )
            # return gjson & merge
            self.merge_gjson(
                self.get_feature(**com_opts)
            )
        
        resp_out = copy.deepcopy(self.response)
        self._set_def_resp_params()  # end response
        if len(resp_out) == 0:
            return {}
        elif len(resp_out) == 1:
            return resp_out[0]
        else:
            return resp_out
        
    def get_properties(self):
        disable_prop = [
            "layer", 
            "id", 
            "osm_id"
        ]
        out = {}
        layers = self.capabilities["layers"].keys()
        for layer in layers:
            out[layer] = {}
            req = {
                "layers": {
                    layer: None,
                    },
            }
            resp = self.get_response(req)
            prop_list = resp["features"][0]["properties"].keys()
            for prop in prop_list:
                if prop not in disable_prop:
                    out[layer][prop] = list(set([
                        my["properties"][prop]
                        for
                        my
                        in
                        resp["features"]
                    ]))
        return out
        
    def __call__(self, *args, **kwargs):
        return self.get_response(*args, **kwargs)


########################################################################
class MapGK(GeoCoder):
    """
    Tiny gcoder server
    """
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
        'PROJ_LIB', 
        'QUERY_STRING', 
        'REMOTE_ADDR',
        'REQUEST_METHOD', 
        'SCRIPT_NAME', 
        'SERVER_NAME', 
        'SERVER_PORT'
    ]

    #----------------------------------------------------------------------
    def __init__(self, port=3008, host='0.0.0.0'):
        self.wsgi_host = host
        self.wsgi_port = port
        GeoCoder.__init__(self)
    
    def application(self, env, start_response):
        print "-" * 30
        for key in self.MAPSERV_ENV:
            if key in env:
                os.environ[key] = env[key]
                print "{0}='{1}'".format(key, env[key])
            else:
                os.unsetenv(key)
        print "-" * 30
    
        # status:
        status = '200 OK'
        req = json.loads(urllib.unquote(env["QUERY_STRING"]))
        resp = json.dumps(self.get_response(req), ensure_ascii=False)
        result = b'{}'.format(resp.encode('utf-8'))
        #status = '500 Server Error'

        start_response(status, [('Content-type', 'application/json')])
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


def json_format(cont):
    print json.dumps(
        cont,
        sort_keys=True,
        indent=4,
        separators=(',', ': '), 
        ensure_ascii=False, 
    )


if __name__ == "__main__":
    gk = MapGK()
    gk()
    
    
    #gcoder = GeoCoder(debug=True)
    gcoder = GeoCoder()

    request_ = {
        "epsg_code": 900913,
        "max_features": 1,
        #"layer_property": [
            #"type", 
            #"name",
            #"osm_id", 
            ##"msGeometry", 
        #],
        "layers": {
            "buildings": None,
            "landuse": {
                "filter": {
                    "type": {
                        "=": "military",
                    },
                },
                #"layer_property": [
                    #"type", 
                    #"name",
                    #"osm_id", 
                    #"msGeometry", 
                #],
            },
        },
        "filter": {
            "or": [
                {
                    #"and": {
                        "name": {
                            "like": "*Пет*",
                        },
                        "type": {
                            "=": "hotel",
                        },
                    #},
                }, 
                {
                    #"and": {
                        "name": {
                            "like": "*Бал*",
                        },
                        "type": {
                            "=": "hotel",
                        },
                    #},
                }, 
            ],
        }
    }
    
    #print "*" * 30
    #print "Metadata"
    #print "*" * 30
    #json_format(gcoder.get_response(request_))
    
    request_ = {
        "epsg_code": 900913,
        #"epsg_code": 3857,
        "max_features": 1,
        "layer_property": [
            #"type", 
            "name",
            #"osm_id", 
            "msGeometry", 
        ],
        "layers": {
            "buildings": None,
            "landuse": None, 
        }, 
        "filter": {
            "name": {
                "null": None,
                "bbox": {
                    "coord": [
                        59.97111801186481728,
                        30.21720754623224181,
                        59.97569926211409097,
                        30.22404557000332304, 
                    ],
                    "epsg_code": 4326,
                    #"coord": [
                        #3364107.934602736961,
                        #8393636.548086917028,
                        #3364263.219452924561,
                        #8393740.583811631426
                    #],
                    #"epsg_code": 3857,
                },
            },
        }, 
    }
    
    #print "*" * 30
    #print "Bbox"
    #print "*" * 30
    #json_format(gcoder.get_response(request_))
    
    #print "*" * 30
    #print "GetCapabilites"
    #print "*" * 30
    #json_format(gcoder.get_capabilities())

    #print "*" * 30
    #print "GetInfo"
    #print "*" * 30
    
    #json_format(gcoder.get_info())

    #print "*" * 30
    #print "GetHelp"
    #print "*" * 30
    
    #json_format(gcoder.get_help())
    

    #request_ = {
        #"layer_property": [
            #"type", 
            #"name",
            #"osm_id", 
        #],
    #}

    #print "*" * 30
    #print "HZ"
    #print "*" * 30
    #json_format(gcoder.get_response(request_))

    #print "*" * 30
    #print "GetPropperties"
    #print "*" * 30
    #json_format(gcoder.get_properties())
