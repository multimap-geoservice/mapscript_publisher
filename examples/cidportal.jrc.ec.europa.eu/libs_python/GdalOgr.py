# Copyright (c) 2015, European Union
# All rights reserved.
# Authors: Simonetti Dario, Marelli Andrea
#
#
# This file is part of IMPACT toolbox.
#
# IMPACT toolbox is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# IMPACT toolbox is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with IMPACT toolbox.
# If not, see <http://www.gnu.org/licenses/>.


## import GDAL/OGR modules
try:
    from osgeo import ogr, gdal, osr
except ImportError:
    import ogr, gdal, osr

import json

def openShapeFile(shapefile):
    """ Open the given shapefile """
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(shapefile, 0)
    return dataSource

def getFeatureAttributes(layer, feature=None):
    """ Retrieve all attributes (dbf) from the given layer (feature) """
    if feature is None:
        feature = layer[0]
    layerDefinition = layer.GetLayerDefn()
    attributes = {}
    for i in range(layerDefinition.GetFieldCount()):
        attributes[layerDefinition.GetFieldDefn(i).GetName()] = str(feature.GetField(layerDefinition.GetFieldDefn(i).GetName()))
    return attributes

def queryByPoint(shapefile, lon, lat , filters=None, orderBy=None):
    """ query shapefile by point and retireve features (with all attributes) """
    dataSource = openShapeFile(shapefile)
    layer = dataSource.GetLayer(0)
    point=ogr.CreateGeometryFromWkt("POINT ("+str(lon)+" "+str(lat)+")")
    #layer.SetSpatialFilter(ogr.CreateGeometryFromWkt("POINT ("+str(lon)+" "+str(lat)+")"))
    #layer.SetSpatialFilterRect(float(lon), float(lat), float(lon), float(lat))
    layer.SetAttributeFilter(filters)
    records = []

    #for feature in layer:
    feature = layer.GetNextFeature()
    while feature:
        feat_geom=feature.GetGeometryRef()
        try:
            if feat_geom.Contains(point):
                attributes = getFeatureAttributes(layer, feature)
                records.append(attributes)
        except:
            pass
        feature = layer.GetNextFeature()

    if orderBy is not None:
        sorted_records = sorted(records, key=lambda k: k[orderBy], reverse=True)
    else:
        sorted_records = records
    return { "records": sorted_records }
