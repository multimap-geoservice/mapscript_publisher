# -*- coding: utf-8 -*-
# encoding: utf-8

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

########################################################################
class WfsFilter(object):
    """
    create filter for wfs
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
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
        
    def filter_create(self, content):
        pass
    
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
                            f_arg = []
                        elif not isinstance(f_arg, list):
                            f_arg = [f_arg]
                        f_arg.insert(0, key)
                        all_filter = "{0}{1}".format(
                            all_filter, 
                            self.filter_opts[f_opt](*f_arg)
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
                raise Exception("Filter error")
        return wrapper
    
    @dec_filters_literal_opts 
    def filter_opt_equal_to(self, **kwargs):
        return PropertyIsEqualTo(**kwargs)

    @dec_filters_literal_opts 
    def filter_opt_not_equal_to(self, **kwargs):
        return PropertyIsNotEqualTo(**kwargs)

    @dec_filters_literal_opts 
    def filter_opt_greater_than(self, **kwargs):
        return PropertyIsGreaterThan(**kwargs)

    @dec_filters_literal_opts 
    def filter_opt_graater_than_or_equal_to(self, **kwargs):
        return PropertyIsGreaterThanOrEqualTo(**kwargs)

    @dec_filters_literal_opts 
    def filter_opt_less_than(self, **kwargs):
        return PropertyIsLessThan(**kwargs)

    @dec_filters_literal_opts 
    def filter_opt_less_than_or_equal_to(self, **kwargs):
        return PropertyIsLessThanOrEqualTo(**kwargs)

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

    def filter_opt_null(self, propertyname=None):
        if propertyname:
            tag = PropertyIsNull(
                propertyname=self.data2literal(propertyname), 
            )
            return etree.tostring(tag.toXML()).decode("utf-8")
        else:
            return None

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

    def filter_opt_bbox(self, propertyname=None, bbox=None, epsg_code=None):
        if propertyname and bbox and epsg_code:
            tag = BBox(
                propertyname=self.data2literal(propertyname), 
                bbox=bbox, 
                crs="EPSG:{}".foramt(epsg_code), 
            )
            return etree.tostring(tag.toXML()).decode("utf-8")
        elif not propertyname and not bbox and not epsg_code:
            return {
                "bbox": [
                    "Upper Left Coord", 
                    "Lower Left Coord", 
                    "Upper Right Coord", 
                    "Lower Right Coord", 
                    ],
                "crs": "epsg code projection",
            }
        else:
            raise Exception("Filter error")


########################################################################
class GeoCoder(WfsFilter):
    """"""
    wfs_ver = '1.1.0'
    

    #----------------------------------------------------------------------
    def __init__(self, wfs_url='http://localhost:3007', debug=False):
        WfsFilter.__init__(self)
        self.debug = debug
        self.wfs = WebFeatureService(wfs_url, version=self.wfs_ver)
        self.capabilities = self.get_capabilities()
        
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
        filter_opts = {
            my: self.filter_opts[my]()
            for my
            in self.filter_opts
        }
        json_out = {
            "filter":{
                "tags": filter_tags,
                "opts": filter_opts,
                "example": {
                    "tag": {
                        "property 1": {
                            "opt": "value",
                            },
                        "property 2": {
                            "opt 1": "value",
                            "opt 2": ["value 1", "value 2"],
                        },
                    },
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

    def get_feature(self, layer_name, filter_json, **kwargs):
        feature_args = [
            "propertyname", 
            "maxfeatures", 
            "srsname"
        ]
        out_args = {
            "typename": layer_name,
            "filter": self.filter_engine(filter_json),
        }
        for arg in feature_args:
            if kwargs.get(arg, None):
                out_args[arg] = kwargs[arg]
                
        return self.gml2json(
            self.wfs.getfeature(**out_args).read()
        )
    
    def get_response(self, request_):
        def_com_opts = {
            "layer_name": [u"{}", "layer"],
            "filter_json": [{}, "filter"],
            "propertyname": [[], "layer_property"],
            "maxfeatures": [u"{}", "max_features"],
            "srsname": [u"EPSG:{}", "epsg_code"],
        }
        response = []
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
            response.append(
                self.get_feature(**com_opts)
            )
        return response

if __name__ == "__main__":
    gcoder = GeoCoder(debug=True)
    
    filter1 = PropertyIsEqualTo(propertyname="type", literal=u"hotel")
    filter2 = PropertyIsLike(
        propertyname="name", 
        literal=u"*Пет*",
        wildCard="*", 
        singleChar=".", 
        escapeChar="!"
    )
    filter3 = PropertyIsLike(
        propertyname="name", 
        literal=u"Бал*", 
        wildCard="*", 
        singleChar=".", 
        escapeChar="!"
    )
    filterxml = u"<Filter><OR><AND>{0}{1}</AND><AND>{0}{2}</AND></OR></Filter>".format(
        etree.tostring(filter1.toXML()).decode("utf-8"), 
        etree.tostring(filter2.toXML()).decode("utf-8"), 
        etree.tostring(filter3.toXML()).decode("utf-8"), 
    )
    
    #print "*" * 30
    #print "Metadata"
    #print "*" * 30

    #print gcoder.get_feature(
        #layer_name='buildings', 
        #propertyname=['type', 'name'],
        ##propertyname=['msGeometry', 'osm_id', 'name'],
        #filter_xml=filterxml, 
        #maxfeatures=10
    #)
    
    
    filter1 = BBox(
        bbox=[
                59.97111801186481728,
                30.21720754623224181,
                59.97569926211409097,
                30.22404557000332304, 
            ], 
        #bbox=[
                #59.94617,
                #30.23334, 
                #59.94618,
                #30.23335, 
            #], 
        #crs="urn:ogc:def:crs:EPSG::4326",
        crs="EPSG:4326"
    )
    #filter1 = BBox(
        #bbox=[
                #3364107.934602736961,
                #8393636.548086917028,
                #3364263.219452924561,
                #8393740.583811631426
            #], 
        ##crs="urn:ogc:def:crs:EPSG::3857",
        #crs="EPSG:3857"
    #)
    filterxml = u"<Filter>{}</Filter>".format(
        etree.tostring(filter1.toXML()).decode("utf-8") 
    )
    
    #print "*" * 30
    #print "Bbox"
    #print "*" * 30
    #print gcoder.get_feature(
        #layer_name='landuse', 
        #propertyname=[
            #'msGeometry', 
            #'osm_id', 
            #'name', 
            #'type'
        #],
        #filter_xml=filterxml, 
        #maxfeatures=10
    #)
    
    print "*" * 30
    print "GetCapabilites"
    print "*" * 30
    
    print gcoder.get_capabilities()

    print "*" * 30
    print "GetInfo"
    print "*" * 30
    
    print gcoder.get_info()

    #print "*" * 30
    #print "GetHelp"
    #print "*" * 30
    
    #print gcoder.get_help()

    print "*" * 30
    print "filter"
    print "*" * 30
    
    request_ = {
        "epsg_code": 900913,
        "max_features": 1,
        #"layer_property": [
            #"type", 
            #"name",
            #"osm_id", 
            #"msGeometry", 
        #],
        "layers": {
            "buildings": None,
            "landuse": {
                "filter": {
                    "type": {
                        "null": None,
                    },
                },
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
    print gcoder.get_response(request_)
