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


import sys
import os


try:
    from osgeo import ogr,gdal,osr

except ImportError:
    import ogr,gdal,osr

try:
    import simplejson as json
except (ImportError,):
    import json

   
## Import local libraries
def smart_filter_catalogue(shp,bbox,filters,returnAll=False):

    shpname=os.path.basename(shp)
    shpbasename=shpname.replace(".shp","")

    # ---------- OPEN SHP -----------
    shp_ds = ogr.Open(shp)

    layer = shp_ds.GetLayer(0)
    wkt = "POLYGON (("+str(bbox[0])+" "+str(bbox[1])+","+str(bbox[0])+" "+str(bbox[3])+","+str(bbox[2])+" "+str(bbox[3])+","+str(bbox[2])+" "+str(bbox[1])+","+str(bbox[0])+" "+str(bbox[1])+"))"
    extent=ogr.CreateGeometryFromWkt(wkt)
    extentheight=abs(float(bbox[3])-float(bbox[1]))
    #uncoveredbuffer=-extentheight/10
    #extent=extent.Buffer(uncoveredbuffer)
    
    source = osr.SpatialReference()
    source.ImportFromEPSG(3857)

    # transform to target projection
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(source, target)
    extent.Transform(transform)

    # ADD AREA SORT 
    layer=shp_ds.ExecuteSQL('select * from "{}" order by  Cloud ASC, ACQTime DESC '.format(shpbasename),extent,"")
    
    layer.SetAttributeFilter(filters)
    diff_extent=extent
    #res=save_geom2file(extent.ExportToWkt(),'extent')

    # if mapextent is big then use the fully within option otherwise intersects

    IDs=""
    feature = layer.GetNextFeature()
    ct=0
    #file = open('/eos/jeodpp/htcondor/scases/forobs/S2_repository/S2_scripts/www/temp/filter.txt', "w")
    while feature:
            ID = str(feature.GetFieldAsString('ID'))
            feat_geom=feature.GetGeometryRef()
            # print diff_extent.GetArea()
            # print feat_geom.GetArea()
            # print extent.GetArea() <= feat_geom.GetArea()
            # IDs=IDs+"'[ID]' = '"+ID+"'"
            # feature = layer.GetNextFeature()
            # continue

            # if extent.GetArea() <= feat_geom.GetArea() :
            #     IDs=IDs+"'[ID]' = '"+ID+"'"
            #     shp_ds.ReleaseResultSet(layer)
            #     shp_ds=None
            #     print 'below'
            #     return "("+(".zip' or ".join(IDs.split(".zip'"))[:-4])+")"


            # negative buffer to avoid centroid overlaps
            #print diff_extent.GetArea()
            try:
                if returnAll :
                    IDs="'[ID]' = '"+ID+"'"+IDs
                    #file.write(ID+'\n')


                elif diff_extent.GetGeometryName() in  ["POLYGON","MULTIPOLYGON"] and feat_geom.GetGeometryName() == "POLYGON" and diff_extent.GetArea() > 0:
                    #if diff_extent.Intersects(feat_geom):
                    if extentheight > 3000000:
                        if feat_geom.Centroid().Buffer(0.1).Within(diff_extent):
                            IDs="'[ID]' = '"+ID+"'"+IDs
                            #file.write(ID+'\n')
                            #res=save_geom2file(feat_geom.ExportToWkt(),'GEOM'+str(ct))
                            diff_extent = diff_extent.Difference(feat_geom.Buffer(0.05))
                            #res=save_geom2file(diff_extent.ExportToWkt(),str(ct))
                            #ct+=1
                    elif feat_geom.Intersects(diff_extent):

                        IDs="'[ID]' = '"+ID+"'"+IDs
                        #file.write(ID+'\n')
                        #res=save_geom2file(feat_geom.ExportToWkt(),'GEOM'+str(ct))
                        diff_extent = diff_extent.Difference(feat_geom.Buffer(0.05))
                        #res=save_geom2file(diff_extent.ExportToWkt(),str(ct))
                        #ct+=1
            except:
                #IDs="'[ID]' = '"+ID+"'"+IDs
                pass

            feature = layer.GetNextFeature()



    #shp_ds.ReleaseResultSet(layer)
    shp_ds=None
    #return IDs
    

    #file.close()
    
    return "("+(".zip' or ".join(IDs.split(".zip'"))[:-4])+")"
    #return "('[ID]'='S2A_OPER_PRD_MSIL1C_PDMC_20160812T002511_R051_V20160809T105032_20160809T105851.zip')"
    #return "([Product]='S2MSI1C')"
    #return "([Cloud]<2)"








if __name__ == "__main__":
     #shp_names,bbox,filters=getArgs(sys.argv)
     shp_name='/eos/jeodpp/htcondor/scases/forobs/S2_Repository/S2_virtual/Sentinel2_catalogue1.shp'
   
     #bbox= {'LLX': -11300450.260108 , 'LLY':-5031770.2502371, 'URX': 16818592.205302, 'URY': 4287432.2369944}
     #world
     
     #bbox=[-59952720.84939,-7470417.7787459,13518143.081428,8585027.195717]
     #bbox=[1137410.1583349,106938.28660345,4652290.4665111,1271838.5975073]
     #Lac
     bbox= [ -8147675.260108 , 455328.2502371,  -8037835.205302, 491731.2369944]
     # AFR 10 mt res 
     #bbox=[2263786.2069889,704443.65257813,2302921.9654655,743579.41105469]
     #AFR tile 21 4 tiles
     #bbox=[1252371.4488599,290387.15446232,4767251.7570361,1455287.4653662]
     #bbox=[4771482.9712011,-2802388.7743248,4991162.9904621,-2729582.5048932]
     #bbox=[0,0,100,-80]
     filters = "Cloud <= 100 and ACQTime >= 20160801"
          
     res= smart_filter_catalogue(shp_name,bbox,filters).split('or')
     
    
     for x in res:
        print x
