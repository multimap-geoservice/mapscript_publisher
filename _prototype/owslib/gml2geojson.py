
import ogr,os,osr


def main(inputGMLfn,inputEPSG,outputGeoJSONfn,outputEPSG):
    inputDs = ogr.Open(inputGMLfn)
    inLayer = inputDs.GetLayer() 
    
    outDriver = ogr.GetDriverByName('GeoJSON')
    
    if os.path.exists(outputGeoJSONfn):
        outDriver.DeleteDataSource(outputGeoJSONfn)
    
    outputDs = outDriver.CreateDataSource(outputGeoJSONfn)
    outLayer = outputDs.CreateLayer(outputGeoJSONfn, geom_type=ogr.wkbLineString )
    
    # create the input SpatialReference
    sourceSR = osr.SpatialReference()
    sourceSR.ImportFromEPSG(inputEPSG)  
    
    # create the output SpatialReference
    targetSR = osr.SpatialReference()
    targetSR.ImportFromEPSG(outputEPSG)
    
    # create transform    
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
    
    # Get the output Layer's Feature Definition
    featureDefn = outLayer.GetLayerDefn()
    
    # loop through the input features
    inFeature = inLayer.GetNextFeature()
    while inFeature:
    
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coordTrans)
    
        outFeature = ogr.Feature(featureDefn)
    
        # set new geometry
        outFeature.SetGeometry(geom)
        # Add new feature to output Layer
        outLayer.CreateFeature(outFeature)
    
        # Get the next input feature
        inFeature = inLayer.GetNextFeature()

    
if __name__ == "__main__":
    inputEPSG = 2964
    outputEPSG = 4326
    inputGMLfn = 'test.gml'
    outputGeoJSONfn = 'test.geojson'
    
    main(inputGMLfn,inputEPSG,outputGeoJSONfn,outputEPSG)