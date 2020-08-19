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

## Import global libraries
import mapscript
try:
    from osgeo import ogr,gdal,osr

except ImportError:
    import ogr,gdal,osr

## Import local libraries
from __config__ import *
import GdalOgr
import Mapserver
#sys.path.append(os.path.dirname(os.path.realpath(__file__).rstrip()))
import Sentinel2_functions



def BandsToIndeces(Bands):
    bandIndexes = ''
    allBands = ['B01','B02','B03','B04','B05','B06','B07','B08','B8A','B09','B10','B11','B12']
    for band in Bands.split(','):
        bandIndexes += str(allBands.index(band)+1)+','
    return bandIndexes.strip(',')





def SqliteQuickLooksLayer(mapObj, imageryShp, filters, layername):
    mapObj.shapepath = ''
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = 'raster_tindex'
    layerObj.status = mapscript.MS_OFF
    layerObj.type = mapscript.MS_LAYER_POLYGON
    layerObj.connectiontype = mapscript.MS_OGR
    layerObj.connection = imageryShp
    layerObj.data = 'select the_geom,locationQKL as location from sentinel2 where '+ filters +' GROUP BY MGRSID,Orbit HAVING MAX(RANK)'
    layerObj.metadata.set('wms_title','raster_tindex')
    layerObj.metadata.set('wms_enable_request','*')
    layerObj.metadata.set('wms_srs',"EPSG:3857")
    layerObj.metadata.set('wms_format','image/png')

    layerObj1 = mapscript.layerObj(mapObj)
    layerObj1.name = layername
    layerObj1.status = mapscript.MS_ON
    #layerObj1.debug = 1
    layerObj1.type = mapscript.MS_LAYER_RASTER
    layerObj1.tileindex = 'raster_tindex'
    layerObj1.tileitem = "location"
    layerObj1.offsite = mapscript.colorObj(0,0,0)
    layerObj1.metadata.set('wms_title','Image TOA Reflectance L1C')
    layerObj1.metadata.set('wms_enable_request','*')
    layerObj1.metadata.set('wms_srs',"EPSG:3857")
    layerObj1.metadata.set('wms_format','image/png')



def SqliteTileIndexLayer(mapObj, imageryShp, layername, filters, Bands, Scale1, Scale2, Scale3):
    mapObj.shapepath = ''
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = 'raster_tindex'
    layerObj.status = mapscript.MS_OFF
    layerObj.type = mapscript.MS_LAYER_POLYGON
    # layerObj.setProjection("AUTO")
    layerObj.connectiontype = mapscript.MS_OGR
    layerObj.connection = imageryShp
    layerObj.data = 'select the_geom,src_srs,locationVRT as location from sentinel2 where '+ filters +' GROUP BY MGRSID,Orbit HAVING MAX(RANK) '


    layerObj1 = mapscript.layerObj(mapObj)
    layerObj1.name = layername
    layerObj1.status = mapscript.MS_ON
    #layerObj1.debug = 1
    layerObj1.type = mapscript.MS_LAYER_RASTER
    layerObj1.setProjection("AUTO")
    layerObj1.tileindex = 'raster_tindex'
    layerObj1.tilesrs = "src_srs"
    layerObj1.tileitem = "location"
    layerObj1.setProcessingKey( "BANDS", BandsToIndeces(Bands) )
    layerObj1.setProcessingKey( "SCALE_1", Scale1 )
    layerObj1.setProcessingKey( "SCALE_2", Scale2 )
    layerObj1.setProcessingKey( "SCALE_3", Scale3 )
    layerObj1.offsite = mapscript.colorObj(0,0,0)
    layerObj1.metadata.set('wms_title','Sentinel2b')
    layerObj1.metadata.set('wms_enable_request','GetMap')
    layerObj1.metadata.set('wms_srs',"EPSG:3857")
    layerObj1.metadata.set('wms_format','image/png')


def ShapefileLayer(mapObj, imageryShp, filters, rgb):
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = "Sentinel2Shapefile"
    layerObj.status = mapscript.MS_ON
    layerObj.type = mapscript.MS_LAYER_POLYGON
    layerObj.setProjection("AUTO")
    layerObj.data = imageryShp
    layerObj.setFilter(filters)
    classObj = mapscript.classObj(layerObj)
    styleObj = mapscript.styleObj(classObj)
    styleObj.outlinecolor = mapscript.colorObj(rgb[0],rgb[1],rgb[2])

def SqliteLayer(mapObj, imageryShp, filters, rgb):
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = "Footprint"
    # layerObj.debug = 5
    layerObj.status = mapscript.MS_ON
    layerObj.type = mapscript.MS_LAYER_POLYGON
    #layerObj.setProjection("AUTO")
    # layerObj.setProjection("init=epsg:3857")
    layerObj.connectiontype = mapscript.MS_OGR
    layerObj.connection = imageryShp
    # layerObj.setGeomTransform("( generalize([shape],[map_cellsize]*10 ))")
    layerObj.data = 'select the_geom from sentinel2 where '+filters

    layerObj.metadata.set('wms_title','Footprint')
    layerObj.metadata.set('wms_enable_request','*')
    layerObj.metadata.set('wms_srs',"EPSG:3857")
    layerObj.metadata.set('wms_format','image/png')
    layerObj.metadata.set('wms_abstract',"Sentinel 2 Footprints")
    layerObj.metadata.set('wms_attribution_title',"JRC,JEODPP,ESA,COPERNICUS")

    classObj = mapscript.classObj(layerObj)
    styleObj = mapscript.styleObj(classObj)
    styleObj.outlinecolor = mapscript.colorObj(rgb[0],rgb[1],rgb[2])




def WMS_S2_Layers(mapObj, imageryShp):
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = "Imagery"
    layerObj.status = mapscript.MS_ON
    layerObj.type = mapscript.MS_LAYER_POLYGON
    layerObj.connectiontype = mapscript.MS_OGR
    layerObj.connection = imageryShp             # needed
    layerObj.metadata.set('wms_title','Imagery')
    layerObj.metadata.set('wms_enable_request','GetCapabilities')
    layerObj.metadata.set('wms_srs',"EPSG:3857")
    layerObj.metadata.set('wms_format','image/png')
    layerObj.metadata.set('wms_abstract',"Sentinel 2 Imagery")
    layerObj.metadata.set('wms_attribution_title',"JRC,JEODPP,ESA,COPERNICUS")

    layerObj1 = mapscript.layerObj(mapObj)
    layerObj1.name = "Footprint"
    # layerObj.debug = 5
    layerObj1.status = mapscript.MS_ON
    layerObj1.type = mapscript.MS_LAYER_POLYGON
    layerObj1.connectiontype = mapscript.MS_OGR
    layerObj1.connection = imageryShp              # needed
    layerObj1.metadata.set('wms_title','Footprint')
    layerObj1.metadata.set('wms_enable_request','GetCapabilities')
    layerObj1.metadata.set('wms_srs',"EPSG:3857")
    layerObj1.metadata.set('wms_format','image/png')
    layerObj1.metadata.set('wms_abstract',"Sentinel 2 Footprints")
    layerObj1.metadata.set('wms_attribution_title',"JRC,JEODPP,ESA,COPERNICUS")


def RasterLayer(mapObj, raster, layername, Bands, Scale1, Scale2, Scale3):
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = layername
    layerObj.status = mapscript.MS_ON
    #layerObj.debug = 1
    layerObj.type = mapscript.MS_LAYER_RASTER
    layerObj.setProjection("AUTO")
    layerObj.data = raster
    layerObj.setProcessingKey( "BANDS", BandsToIndeces(Bands))
    layerObj.setProcessingKey( "SCALE_1", Scale1 )
    layerObj.setProcessingKey( "SCALE_2", Scale2 )
    layerObj.setProcessingKey( "SCALE_3", Scale3 )
    layerObj.offsite = mapscript.colorObj(0,0,0)


def RasterClassLayer(mapObj, raster, layername):
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = layername
    layerObj.status = mapscript.MS_ON
    #layerObj.debug = 5
    layerObj.type = mapscript.MS_LAYER_RASTER
    layerObj.setProjection("AUTO")
    layerObj.data = raster
    layerObj.offsite = mapscript.colorObj(0,0,0)


def ClassificationLayer(mapObj, imageryShp, layername, filters):
    layerObj = mapscript.layerObj(mapObj)
    layerObj.name = layername
    layerObj.status = mapscript.MS_ON
    #layerObj.debug = 5
    layerObj.type = mapscript.MS_LAYER_RASTER
    layerObj.setProjection("AUTO")
    layerObj.tileindex = imageryShp
    layerObj.tileitem = "LOCATION"
    layerObj.tilesrs = "src_srs"
    layerObj.setFilter(filters)
    layerObj.offsite = mapscript.colorObj(0,0,0)




def getBBoxByID(imageryShp, ID, targetEPSG):
    # open shapefile
    fileObj = GdalOgr.openShapeFile(imageryShp)
    layer = fileObj.GetLayer(0)
    # filter by ID
    layer.SetAttributeFilter("ID = '"+ID+"'")
    # get source projection from geometry
    feature = layer.GetNextFeature()
    geom = feature.GetGeometryRef()
    source = geom.GetSpatialReference()
    # transform to target projection
    target = osr.SpatialReference()
    target.ImportFromEPSG(int(targetEPSG))
    transform = osr.CoordinateTransformation(source, target)
    geom.Transform(transform)
    # get geometry envelop (Re-sorted for mapserver)
    env = geom.GetEnvelope()
    return  [env[0],env[2],env[1],env[3]]

def get_BBOX_fromXML(XML,FIELD):
    if os.path.exists(XML):
        from xml.etree import ElementTree
        with open(XML, 'rt') as f:
            tree = ElementTree.parse(f)
        for node in tree.iter(FIELD):
            BBOX=str(node.text).split()
        for index, item in enumerate(BBOX):
            BBOX[index]=float(item)
        return [min(BBOX[1::2]),min(BBOX[0::2]),max(BBOX[1::2]),max(BBOX[0::2])]
    else:
        print "WRONG XML"
        return


def get_BBOX_from_image(infile,out_srs=None):
    ds = gdal.Open(infile)
    geoTransform = ds.GetGeoTransform()
    minx = geoTransform[0]
    maxy = geoTransform[3]
    maxx = minx + geoTransform[1] * ds.RasterXSize
    miny = maxy + geoTransform[5] * ds.RasterYSize
   # print minx, miny , maxx, maxy
    if not out_srs == None:
        imgSR = osr.SpatialReference()
        imgSR.ImportFromWkt(ds.GetProjectionRef())

        outsrs = osr.SpatialReference()
        outsrs.ImportFromEPSG(int(out_srs))
        transformation = osr.CoordinateTransformation(imgSR, outsrs)
        (ulx, uly, holder) = transformation.TransformPoint(minx,maxy)
        (lrx, lry, holder) = transformation.TransformPoint(maxx, miny)

        #print ulx, lry , lrx, uly
        return [ulx, lry , lrx, uly ]

    return [ minx, miny , maxx, maxy ]


# works but does not add projections NOT USED
def SQLITEgenerateQuickLook(infileVRT, pixelSize, Bands, Scale1, Scale2, Scale3):

    quickLookPath = GLOBALS['S2']['qklooks_path']
    outname = os.path.basename(infileVRT.replace('.vrt','_test.tif'))
    bbox = get_BBOX_from_image(infileVRT,3857)
    print bbox
    epsg= Sentinel2_functions.get_EPSG_from_VRT(infileVRT).replace("EPSG:",'')
    print epsg
    mapSize = Mapserver.calculateImageSize(bbox, pixelSize)
    print mapSize
    # Create map object ##
    mapObj = Mapserver.initMap()
    mapObj.unit = mapscript.MS_METERS
    mapObj.setProjection("init=epsg:3857")
    # overwrite driver
    mapObj.outputformat=mapscript.outputFormatObj("GDAL/GTiff")
    mapObj.outputformat.name="GTif"
    mapObj.outputformat.mimetype="image/tiff"
    mapObj.outputformat.driver="GDAL/GTiff"
    mapObj.outputformat.extension="tif"
    mapObj.outputformat.setOption("COMPRESSION","LZW")


    mapObj.setSize(int(mapSize[0]),int(mapSize[1]))
    mapObj.setExtent(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))

    RasterLayer(mapObj, infileVRT, 'qkl', Bands, Scale1, Scale2, Scale3)

    ## Generate image file
    imgFilename = Mapserver.MapToFile(mapObj, quickLookPath, outname)
    Mapserver.WorldFile(mapObj, imgFilename)