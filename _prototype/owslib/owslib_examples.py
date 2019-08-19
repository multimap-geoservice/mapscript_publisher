# -*- coding: utf-8 -*-
# encoding: utf-8

import ogr
import json

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
        self.tags = {
            "and": None,
            "or": None,
            "not": None,
        } 
        self.ops = {
            "between": PropertyIsBetween,
            "=": PropertyIsEqualTo,
            ">": PropertyIsGreaterThan,
            ">=": PropertyIsGreaterThanOrEqualTo,
            "<": PropertyIsLessThan,
            "<=": PropertyIsLessThanOrEqualTo,
            "!=": PropertyIsNotEqualTo,
            "like": PropertyIsLike,
            "null": PropertyIsNull,
            "bbox": BBox,
        }
    

########################################################################
class GeoCoder(WfsFilter):
    """"""
    wfs_ver = '1.1.0'
    

    #----------------------------------------------------------------------
    def __init__(self, wfs_url='http://localhost:3007', debug=False):
        WfsFilter.__init__(self)
        self.debug = debug
        self.wfs = WebFeatureService(wfs_url, version=self.wfs_ver)
        
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
                "layer": None,
                "properties": None,
                "geometry": None,
            }
            for layer in feature.iterfind('{%s}*' % nsmap["ms"]):
                json_feature["id"] = layer.get("{%s}id" % nsmap["gml"], None)
                json_feature["layer"] = tag_name(layer)
                for prop in layer.iterfind('{%s}*' % nsmap["ms"]):
                    get_prop = True
                    geom_crs = None
                    for geom in prop.iterfind("{%s}*" % nsmap["gml"]):
                        get_prop = False
                        geom_crs = geom.get("srsName", None)
                        ogr_geom = ogr.CreateGeometryFromGML(etree.tostring(geom))
                        if isinstance(ogr_geom, ogr.Geometry):
                            json_feature["geometry"] = json.loads(
                                ogr_geom.ExportToJson()
                            )
                    if get_prop:
                        if not json_feature["properties"]:
                            json_feature["properties"] = {}
                        json_feature["properties"][tag_name(prop)] = prop.text
                    if geom_crs:
                        geom_crs = geom_crs.split(":")
                        if len(geom_crs) == 2:
                            if geom_crs[0].lower() == "epsg":
                                json_feature["crs"] = {
                                    "type": "EPSG",
                                    "properties": {
                                            "code": geom_crs[-1],
                                        },
                                    }
                json_out["features"].append(json_feature)
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
        json_out = {}
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
            json_out[layer_name] = {
                "epsg_code": epsg_code, 
                "layer_property": layer_property,
                "max_features": 0,
                "filter": None,
            }
        if self.debug:
            self.echo2json(json_out)
        return json_out

    def get_feature(self, layer_name, filter_xml, **kwargs):
        feature_args = [
            "propertyname", 
            "maxfeatures"
        ]
        out_args = {
            "typename": layer_name,
            "filter": filter_xml,
        }
        for arg in feature_args:
            if kwargs.get(arg, False):
                out_args[arg] = kwargs[arg]
                
        return self.gml2json(
            self.wfs.getfeature(**out_args).read()
        )
    

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
    
    print "*" * 30
    print "Metadata"
    print "*" * 30

    print gcoder.get_feature(
        layer_name='buildings', 
        propertyname=['type', 'name'],
        #propertyname=['msGeometry', 'osm_id', 'name'],
        filter_xml=filterxml, 
        maxfeatures=10
    )
    
    
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
    
    
    print "*" * 30
    print "Bbox"
    print "*" * 30
    print gcoder.get_feature(
        layer_name='landuse', 
        propertyname=[
            'msGeometry', 
            'osm_id', 
            'name', 
            'type'
        ],
        filter_xml=filterxml, 
        maxfeatures=10
    )
    
    print "*" * 30
    print "GetCapabilites"
    print "*" * 30
    
    print gcoder.get_capabilities()

    print "*" * 30
    print "GetInfo"
    print "*" * 30
    
    print gcoder.get_info()
