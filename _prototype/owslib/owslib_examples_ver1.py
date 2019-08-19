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
    PropertyIsGreaterThanOrEqualTo,  # =>
    PropertyIsLessThan,  # <
    PropertyIsLessThanOrEqualTo,  # =<
    PropertyIsLike,  #как  * . ! 
    PropertyIsNotEqualTo,  # !=
    PropertyIsNull,  # =NULL
    BBox
)

wfs_ver = '1.1.0' 
wfs = WebFeatureService('http://localhost:3007', version=wfs_ver)


def get_info(echo=False):
    json_out = {}
    for layer_name in wfs.contents:
        wfs_response = wfs.getfeature(
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
        epsg_code = [my.code for my in wfs.contents[layer_name].crsOptions]
        wfs_opts = wfs.contents[layer_name].metadataUrls[0]
        wfs_opts["gml"] = wfs.contents[layer_name].outputFormats[0]
        json_out[layer_name] = {
            "wgs84_bbox": list(wfs.contents[layer_name].boundingBoxWGS84),
            "epsg_code": epsg_code, 
            "wfs_opts": wfs_opts, 
            "layer_property": layer_property,
        }
    
    if echo:
        print json.dumps(
            json_out,
            sort_keys=True,
            indent=4,
            separators=(',', ': '), 
            ensure_ascii=False, 
        )
    
    return json_out


def gml2json(gml, echo=False):
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
            json_out["features"].append(json_feature)
    if geom_crs:
        geom_crs = geom_crs.split(":")
        if len(geom_crs) == 2:
            print geom_crs
            if geom_crs[0].lower() == "epsg":
                json_out["crs"] = {
                    "type": "EPSG",
                    "properties": {
                            "code": geom_crs[-1],
                        },
                    }
    
    if echo:
        print json.dumps(
            json_out,
            sort_keys=True,
            indent=4,
            separators=(',', ': '), 
            ensure_ascii=False, 
        )
    
    return json_out



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

#out = wfs.getfeature(
    #typename='buildings', 
    #propertyname=['type', 'name'],
    ##propertyname=['msGeometry', 'osm_id', 'name'],
    #filter=filterxml, 
    #maxfeatures=10
#)

#print "*" * 30
#print "Metadata"
#print "*" * 30
#for lst in [my for my in out.read().split('\n')]:
    #print lst
#gml2json(out.read(), echo=True)


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

out = wfs.getfeature(
    # list typename - ????? (list2list propertyname)(list2filter)
    #typename=[
        #'buildings', 
        #'landuse', 
    #], 
    typename='landuse', 
    propertyname=[
        'msGeometry', 
        'osm_id', 
        'name', 
        'type'
    ],
    filter=filterxml, 
    maxfeatures=10
)

print "*" * 30
print "Bbox"
print "*" * 30
#for lst in [my for my in out.read().split('\n')]:
    #print lst
gml2json(out.read(), echo=True)


print "*" * 30
print "GetCapabilites"
print "*" * 30

print get_info(echo=True)
