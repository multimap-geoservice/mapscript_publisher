# -*- coding: utf-8 -*-
# encoding: utf-8

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

#filter_ = PropertyIsEqualTo(propertyname="osm_id", literal="-8841754")
#filter_ = PropertyIsLike(propertyname="type", literal="yes", wildCard="*")
#filter_ = PropertyIsLike(propertyname="name", literal=u"Санкт-Петербург", wildCard="*")
#filterxml = u"<Filter>{}</Filter>".format(
    #etree.tostring(filter_.toXML()).decode("utf-8")
#)


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

out = wfs.getfeature(
    typename='buildings', 
    #propertyname=['msGeometry', 'osm_id'],
    filter=filterxml, 
    maxfeatures=10
)

print "*" * 30
print "Metadata"
print "*" * 30
tree = etree.fromstring(out.read())
nsmap = tree.nsmap
for feature in tree.getiterator("{%s}featureMember" % nsmap["gml"]):
    for layer in feature.iterfind('{%s}*' % nsmap["ms"]):
        print "-" * 30
        for meta in layer.iterfind('{%s}*' % nsmap["ms"]):
            meta_name = meta.tag.split("{%s}" % nsmap[meta.prefix])[-1]
            for geom in meta.iterfind("{%s}*" % nsmap["gml"]):
                geom_type = geom.tag.split("{%s}" % nsmap[geom.prefix])[-1]
                geom_srs = geom.get("srsName", None)
                for ex in geom.iterfind("{%s}exterior" % nsmap["gml"]):
                    for lr in ex.iterfind("{%s}LinearRing" % nsmap["gml"]):
                        for ps in lr.iterfind("{%s}posList" % nsmap["gml"]):
                            geom_data = [float(my) for my in ps.text.split(" ")[:-1]]
                print geom_type
                print geom_srs
                print geom_data
            else:
                print u"{0}={1}".format(meta_name, meta.text)


filter1 = BBox(
    #bbox=[
            #59.97242505986301353,
            #30.21999842282087911,
            #59.9735703724253284,
            #30.22170792876364942,
        #], 
    bbox=[
            59.98198,
            30.21001, 
            59.98198,
            30.21001, 
        ], 
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
    typename='buildings', 
    propertyname=['msGeometry', 'osm_id', 'name', 'type'],
    filter=filterxml, 
    maxfeatures=10
)

#print "*" * 30
#print "Bbox"
#print "*" * 30
#for lst in [my for my in out.read().split('\n')]:
    #print lst


print "*" * 30
print "Attributes List"
print "*" * 30

for layer_name in wfs.contents:
    print "*" * 5
    print layer_name
    print "*" * 5
    #print wfs.contents[layer_name].abstract
    print wfs.contents[layer_name].boundingBoxWGS84
    print wfs.contents[layer_name].crsOptions
    #print wfs.contents[layer_name].defaulttimeposition
    #print wfs.contents[layer_name].id
    #print wfs.contents[layer_name].keywords
    print wfs.contents[layer_name].metadataUrls
    print wfs.contents[layer_name].outputFormats
    #print wfs.contents[layer_name].styles
    #print wfs.contents[layer_name].timepositions
    #print wfs.contents[layer_name].title
    #print wfs.contents[layer_name].verbOptions
    print "*" * 5
    print "Metadata List for {}".format(layer_name)
    print "*" * 5
    out = wfs.getfeature(
        typename=layer_name, 
        maxfeatures=1
    )
    tree = etree.fromstring(out.read())
    nsmap = tree.nsmap
    for feature in tree.getiterator("{%s}featureMember" % nsmap["gml"]):
        for layer in feature.iterfind('{%s}*' % nsmap["ms"]):
            for meta in layer.iterfind('{%s}*' % nsmap["ms"]):
                meta_name = meta.tag.split("{%s}" % nsmap[meta.prefix])[-1]
                print meta_name
