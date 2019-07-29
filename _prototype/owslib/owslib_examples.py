# -*- coding: utf-8 -*-
# encoding: utf-8

from owslib.wfs import WebFeatureService

from owslib.etree import etree
from owslib.fes import PropertyIsLike
from owslib.fes import PropertyIsEqualTo

wfs_ver = '1.1.0' 

wfs = WebFeatureService('http://localhost:3007', version=wfs_ver)

#filter_ = PropertyIsEqualTo(propertyname="osm_id", literal="-8841754")
#filter_ = PropertyIsLike(propertyname="type", literal="yes", wildCard="*")
filter_ = PropertyIsLike(propertyname="name", literal=u"Санкт-Петербург", wildCard="*")
filterxml = u"<Filter>{}</Filter>".format(
    etree.tostring(filter_.toXML()).decode("utf-8")
)

out = wfs.getfeature(
    typename='buildings', 
    #propertyname='msGeometry',
    filter=filterxml, 
    maxfeatures=10
)

#out = wfs.getfeature(
    #typename='buildings',
    #propertyname='name', 
    #bbox=[
        #3364107.934602736961,
        #8393636.548086917028,
        #3364263.219452924561,
        #8393740.583811631426
        #]
    #,srsname="EPSG:3857"
#)

for lst in [my for my in out.read().split('\n')]:
    print lst
