#!python
#
# Copyright (c) 2015, European Union
# All rights reserved.
# Authors: Simonetti Dario, Marelli Andrea
#

# Import global libraries
import os
import mapscript

# Import local libraries
from __config__ import *


def initMap():
    """ Initialize a generic mapObj item """
    #from datetime import datetime

    mapObj = mapscript.mapObj()
    # mapObj.debug = 5
    # mapObj.setConfigOption("MS_ERRORFILE", GLOBALS['S2']['root_path']+"S2_scripts/ms_error.txt")
    #mapObj.name = 'map_'+datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    mapObj.name = 'Sentinel2_map'
    mapObj.transparent = mapscript.MS_TRUE
    mapObj.imagecolor = mapscript.colorObj(0,0,0)
    mapObj.maxsize = 2500

    # mapObj.outputformat=mapscript.outputFormatObj("GD/JPEG")
    # mapObj.outputformat.mimetype="image/jpeg;"
    # mapObj.outputformat.name="JPEG"
    # mapObj.outputformat.driver="GD/JPEG"
    # mapObj.outputformat.extension="jpg"
    # mapObj.outputformat.setOption("QUALITY","90")
    # mapObj.outputformat.transparent = mapscript.MS_TRUE
    # mapObj.outputformat.imagemode= mapscript.MS_IMAGEMODE_RGBA

    mapObj.outputformat=mapscript.outputFormatObj("AGG/PNG")
    mapObj.outputformat.name="PNG"
    mapObj.outputformat.mimetype="image/png"
    mapObj.outputformat.driver="AGG/PNG"
    mapObj.outputformat.extension="png"
    mapObj.outputformat.setOption("COMPRESSION","7")
    mapObj.outputformat.setOption("QUANTIZE_FORCE","ON")
    mapObj.outputformat.transparent = mapscript.MS_TRUE
    mapObj.outputformat.imagemode= mapscript.MS_IMAGEMODE_RGBA

    # WMS

    mapObj.web.metadata.set('wms_title','Public API for Sentinel2 imagery')
    mapObj.web.metadata.set('wms_onlineresource',GLOBALS['mapserver_url']+"wms_sentinel2.py?")
    #mapObj.web.metadata.set("wms_feature_info_mime_type","text/html")
    #webObj.metadata.set('wms_onlineresource','http://cidportal.jrc.ec.europa.eu/forobsdev/cgi-bin/mapserv?')
    mapObj.web.metadata.set('wms_enable_request',"*")
    mapObj.web.metadata.set('wms_srs',"EPSG:3857")
    mapObj.web.metadata.set('wms_abstract',"WMS serving Sentinel 2 full resolution imagery")

    return mapObj


def MapToHTTP(mapObj):
    """ Generate map and sent as HTTP response """
    try:
        output = mapObj.draw().getBytes()
        print "Content-type:"+mapObj.outputformat.mimetype+ "\n"
        print output
    except Exception as err:
        if GLOBALS['debug'] == 'true':
            print "Content-type: text/plain;\n"
            print err

def MapToXML(mapObj):
    """ Generate map and sent as HTTP response """
    try:
        output = mapObj.draw().getBytes()
        #print "Content-type:"+mapObj.outputformat.mimetype+ "\n"
        print "Content-type: text/xml;\n"
        print output
    except Exception as err:
        if GLOBALS['debug'] == 'true':
            print "Content-type: text/xml;\n"
            print err

def MapToFile(mapObj, destinationPath, imgFilename=None, alsoMapfile=False):
    try:
        """ Generate map and save file """
        if imgFilename is None:
            from datetime import datetime
            imgFilename = 'map_'+datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        imgFilename = os.path.join(destinationPath, imgFilename+'.'+mapObj.outputformat.extension)
        if alsoMapfile:
            mapfileFilename = os.path.join(destinationPath, imgFilename+'.map')
            mapObj.save(mapfileFilename)
        image = mapObj.draw()
        image.save(imgFilename)
        return imgFilename
    except Exception as err:
        if GLOBALS['debug'] == 'true':
            print "Content-type: text/plain;\n"
            print err


def WorldFile(mapObj, imgFilename):
    """ Generate world file """
    mapExtent = mapObj.extent
    pixelSize = calculatePixelSize(mapExtent, [mapObj.width, mapObj.height])
    worldFileContent = str(pixelSize[0])+"\n"           # pixel size in the x-direction in map units/pixel
    worldFileContent += "0.0\n"                         # rotation about y-axis
    worldFileContent += "0.0\n"                         # rotation about x-axis
    worldFileContent += "-"+str(pixelSize[1])+"\n"      # pixel size in the y-direction
    worldFileContent += str(mapExtent.minx)+"\n"        # x-coordinate of the center of the upper left pixel
    worldFileContent += str(mapExtent.maxy)+"\n"        # y-coordinate of the center of the upper left pixel
    worldFilename = imgFilename.replace('.png', '.pgw')
    file = open(worldFilename, 'w')
    file.write(worldFileContent);
    file.close()
    return worldFileContent


def calculateImageSize(imageExtent, pixelSize):
    """ Calculate map size """
    mapWith = abs(float(imageExtent[2]) - float(imageExtent[0]))
    mapHeight = abs(float(imageExtent[3]) - float(imageExtent[1]))
    mapSizeX = mapWith/float(pixelSize)
    mapSizeY = mapHeight/float(pixelSize)
    return [mapSizeX, mapSizeY]


def calculatePixelSize(mapExtent, mapSize):
    """ Calculate map resolution """
    mapWith = abs((float(mapExtent.maxx)) - float(mapExtent.minx))
    mapHeight = abs((float(mapExtent.maxy)) - float(mapExtent.miny))
    pixelSizeX = mapWith/int(mapSize[0])
    pixelSizeY = mapHeight/int(mapSize[1])
    return [pixelSizeX, pixelSizeY]


def calculateScale(mapExtent, mapSize):
    """ Calculate map scale """
    mapWith = abs((float(mapExtent[2])) - float(mapExtent[0]))
    pixelSize = mapWith/int(mapSize[0])
    scale = pixelSize * 2 * 1000
    return scale
