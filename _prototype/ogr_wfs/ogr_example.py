# -*- coding: utf-8 -*-
# encoding: utf-8

import ogr

driver = ogr.GetDriverByName('WFS')
wfs = driver.Open('WFS:http://localhost:3007')
print dir(wfs)
layer = wfs.GetLayerByName('buildings')
#layer.SetAttributeFilter("hz")
print dir(layer)