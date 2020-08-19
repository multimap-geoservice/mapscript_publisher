#!python
#
# Copyright (c) 2015, European Union
# All rights reserved.
# Authors: Simonetti Dario, Marelli Andrea
#
#

import sys,os,time,glob
import shutil
import zipfile
import time
from datetime import datetime
import fnmatch

import re

try:
    from osgeo import ogr,gdal,osr

except ImportError:
    import ogr,gdal,osr

sys.path.append(os.path.dirname(os.path.realpath(__file__).rstrip()))
import Sentinel2
from __config__ import *
import Terminal

# driver = gdal.GetDriverByName('JP2ECW')
# driver.Deregister()

def getYYYYMMDD_from_name(name):
    TMP = name.split('_')
    if len(TMP) == 7:
        ACQDATE = TMP[2][0:4]+'/'+TMP[2][4:6]+'/'+TMP[2][6:8]
    if len(TMP) == 9:
        ACQDATE = TMP[7][1:5]+'/'+TMP[7][5:7]+'/'+TMP[7][7:9]
    if len(TMP) == 11:
        if "S2A_OPER_MSI_L1C_" in name and "__" in name and "_N" in name:
            ACQDATE = TMP[7][0:4] + '/' + TMP[7][4:6] + '/' + TMP[7][6:8]
        else:
            ACQDATE = TMP[9][1:5]+'/'+TMP[9][5:7]+'/'+TMP[9][7:9]

    return ACQDATE

def traverseRecursively(path,extension):
    """ List all the files (full path) in the given directory (including all sub-directories) """
    extensions=[]
    if type(extension) == type(''):
        extensions.append(extension)
    else:
        extensions=extension

    fileList = []
    fileMatch = []

    for root, dirs, files in os.walk(path):
       for filename in files:
           fileList.append(os.path.join(root, filename))
    for ID in extensions:
        for img in fileList:
           if img.endswith(ID):
               fileMatch.append(img)
    return fileMatch


def remove_processed_directory(indir):
    print "Removing ...."
    print indir
    os.system("/bin/rm -r "+indir)
    '''
    tries = 1
    done = False
    while not done:
        if os.path.isdir(indir):
            os.system("/bin/rm -r "+indir)
            done = True 
        elif tries > 3:
            print "Waited for more than a half minute aborting remove" 
            print indir
            done = True
        else:
            print "There is no dir " + indir
            print "Sleeping for 10 for " + str(tries) + " time"
            time.sleep(10)
            tries += 1
    '''


def write_logfile(infile,message):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    f = open(infile, 'a')
    f.write(str(now)+' -> '+message+'\n')
    f.close()


def get_Sentinel_from_JeoDPP_API(DATE_Min,DATE_max,COUNTRY):
    import urllib2
    import json

    # QUERY = 'https://cidportal.jrc.ec.europa.eu/services/catalogue/dataset?platformFamilyName=SENTINEL-2&data=true'
    # QUERY+='&cloudCoverPercentage<='+str(CLOUD_Max)
    # QUERY+='&cloudCoverPercentage>='+str(CLOUD_Min)
    QUERY = 'https://cidportal.jrc.ec.europa.eu/services/catalogue/dataset?platformFamilyName=SENTINEL-2'

    QUERY += '&acquisitionStartTime=>='+str(DATE_Min)+'%'
    QUERY += '&acquisitionStopTime=<='+str(DATE_max)+'%'


    if COUNTRY == 'LAC':
        GEOM = '&footprint=POLYGON((-95 30,-30 30,-30 -36,-95 -36,-95 30))'.replace(' ','%20')
    if COUNTRY == 'AFR':

        GEOM = '&footprint=POLYGON((-23 38, 50 38, 50 -38, -23 -38, -23 38))'.replace(' ','%20')
        #GEOM = '&footprint=POLYGON((10 6, 20 6, 20 -6, 10 -6, 10 6))'.replace(' ','%20')  # Congo
        #GEOM = '&footprint=POLYGON((28 0, 43 0, 43 -13, 28 -13, 28 0))'.replace(' ','%20')  # TZ


    if COUNTRY == 'SEA':
        GEOM = '&footprint=POLYGON((91.5720213719568 19.5999465961424,94.0329588716148 28.0320289104471,98.4274901210028 29.189376704404,100.18530262076 27.4876063707585,100.800536995674 24.7256719835555,106.073974494936 24.0853802563049,108.271240119635 23.1189356761192,110.995849494252 21.0012347261195,115.302490118654 17.7683511205746,122.773193242614 20.919159907125,130.859130741489 11.220211273049,157.050536987844 -12.5129582466829,152.392333863488 -15.8358097830097,144.306396364613 -10.4459000761395,138.945068240364 -10.1864908362781,131.913818241345 -10.0134336863503,127.782958866917 -9.84028419392193,124.443115117385 -11.911649341377,104.579833870148 -13.5404881615098,89.6384276222268 8.53625572204067,91.5720213719568 19.5999465961424))'.replace(' ','%20')

    QUERY += GEOM
    QUERY += '&count=99999999999999&data=true&processingLevel=Level-1C'


    #print QUERY
    res = urllib2.urlopen(QUERY).read()
    content = json.loads(res)
    return content


def create_symlinks_to_cid(sourcePath, destPath):
    try:

        if "S2A_OPER_PRD_MSIL1C_PDMC" in sourcePath:
            # OLD SAFE, scan granules
            print 'OLD'
            #if not os.path.exists(os.path.join(cid_path,year,month,day,orbit,image_safe,'GRANULE')):
            #    print Terminal.printInColor("Error in creating symlink OLD NAMING (" + str(image_safe) + ")", 'red')

            # GRANULES = os.listdir(os.path.join(cid_path,year,month,day,orbit,image_safe,'GRANULE'))
            # for granule in GRANULES:
            #     symlink = os.path.join(symlinks_path,year, granule+".SAFE")
            #     try:
            #         if not os.path.islink(symlink):
            #             num_symlinks_created += 1
            #             #print os.path.join(cid_path, year, month, day, orbit, image_safe)
            #             #print symlink
            #             os.symlink(os.path.join(cid_path,year,month,day,orbit,image_safe,'GRANULE',granule), symlink)
            #     except Exception as e:
            #         print str(e)
            #         print Terminal.printInColor("Error 0 in creating symlink (" + str(symlink) + ")", 'red')

        else:
            try:
                if not os.path.islink(destPath):

                    #print os.path.join(cid_path,year,month,day,orbit,image_safe)
                    #print symlink
                    os.symlink(sourcePath, destPath)
            except Exception as e:
                print str(e)
                print Terminal.printInColor("Error 1 in creating symlink (" + str(destPath) + ")", 'red')



    except Exception as e:
        print Terminal.printInColor("Error in reading CID path ("+str(sourcePath)+")", 'red')
        print Terminal.printInColor(str(e), 'red')
    return True

def OLD_create_symlinks_to_cid(filterId):
    symlinks_path = GLOBALS['S2']['unzip_path']
    cid_paths = GLOBALS['S2']['cid_paths']
    print ''
    print Terminal.printInColor('Searching for new images on CID repository...', 'blue')

    for cid_path in cid_paths:
        try:
            num_images = num_symlinks_created = 0
            years = ['2015','2016','2017','2018','2019','2020']
            if filterId and filterId != '' and len(filterId) == 4 :
                years = [str(filterId)]
            for year in years:
                for month in ['01','02','03','04','05','06','07','08','09','10','11','12']:
                    for day in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12','13','14','15',\
                                '16', '17', '18', '19', '20', '21', '22', '23', '24', '25','26','27','28','29','30','31']:

                        if not os.path.exists(os.path.join(symlinks_path,year)):
                            os.makedirs(os.path.join(symlinks_path,year))

                        if not os.path.exists(os.path.join(cid_path,year,month,day)):
                            #print "No images in "+ year+month+day
                            continue
                        for orbit in os.listdir(os.path.join(cid_path,year,month,day)):
                            print 'Reading '+os.path.join(cid_path,year,month,day,orbit)

                            for image_safe in os.listdir(os.path.join(cid_path,year,month,day,orbit)):
                                if image_safe.endswith('.SAFE'):
                                    #print image_safe
                                    num_images += 1

                                    if "S2A_OPER_PRD_MSIL1C_PDMC" in image_safe:
                                        # OLD SAFE, scan granules
                                        if not os.path.exists(os.path.join(cid_path,year,month,day,orbit,image_safe,'GRANULE')):
                                            print Terminal.printInColor("Error in creating symlink OLD NAMING (" + str(image_safe) + ")", 'red')
                                            continue
                                        GRANULES = os.listdir(os.path.join(cid_path,year,month,day,orbit,image_safe,'GRANULE'))
                                        for granule in GRANULES:
                                            symlink = os.path.join(symlinks_path,year, granule+".SAFE")
                                            try:
                                                if not os.path.islink(symlink):
                                                    num_symlinks_created += 1
                                                    #print os.path.join(cid_path, year, month, day, orbit, image_safe)
                                                    #print symlink
                                                    os.symlink(os.path.join(cid_path,year,month,day,orbit,image_safe,'GRANULE',granule), symlink)
                                            except Exception as e:
                                                print str(e)
                                                print Terminal.printInColor("Error 0 in creating symlink (" + str(symlink) + ")", 'red')

                                    else:
                                        symlink = os.path.join(symlinks_path,year, os.path.basename(image_safe))
                                        try:
                                            if not os.path.islink(symlink):
                                                num_symlinks_created += 1
                                                #print os.path.join(cid_path,year,month,day,orbit,image_safe)
                                                #print symlink
                                                os.symlink(os.path.join(cid_path,year,month,day,orbit,image_safe), symlink)
                                        except Exception as e:
                                            print str(e)
                                            print Terminal.printInColor("Error 1 in creating symlink (" + str(symlink) + ")", 'red')



            print Terminal.printInColor(str(num_images) + " images found in " + str(cid_path) + ". " +
                                        str(num_symlinks_created) + " symlinks created.", 'green')
        except Exception as e:
            print Terminal.printInColor("Error in reading CID path ("+str(cid_path)+")", 'red')
            print Terminal.printInColor(str(e), 'red')
    return True



def remove_broken_symlinks_to_cid():
    symlinks_path = GLOBALS['S2']['unzip_path']
    print ''
    print Terminal.printInColor('Searching broken symlinks to CID repository...', 'blue')
    broken_symlinks = 0
    for symlink in os.listdir(symlinks_path):
        if not os.path.exists(os.path.realpath(os.path.join(symlinks_path,symlink))):
            try:
                #os.unlink(os.path.join(symlinks_path, symlink))
                print symlink
                broken_symlinks += 1
            except:
                print Terminal.printInColor("Error removing broken symlink (" + str(symlink) + ")", 'red')
    print Terminal.printInColor(str(broken_symlinks)+" broken links found. "+str(broken_symlinks)+" removed.", 'green')


def test_S2_unzip(indir):
    print "Testing "+indir
    if os.path.exists(indir):
        return "OK"
    else:
        if os.path.exists(os.path.join(indir.replace('.SAFE',''),os.path.basename(indir))):
            print "Moving UP"
            os.system('mv '+os.path.join(indir.replace('.SAFE',''),os.path.basename(indir))+' '+indir)
            print "Del"
            os.system('/bin/rm -r '+indir.replace('.SAFE',''))

            return "RENAME"
        else :
            return "BAD"


#-----------------------------------------------------------------------------------------------------------------------
#------------------------------    NEW FUNCTION WITH SQLITE3 DB    -----------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------

def clelan_QKL_VRT_fromDisk():
    try:
        print "cleaning DISK from corrupted or missing QLK or VRT"
        print "Listing VRT files "
        vrts = glob.glob(os.path.join(GLOBALS['S2']['virtual_path'], GLOBALS['S2']['resolutions'][0], '*.vrt'))
        print "Looping "
        for vrt in vrts:
            qkl = os.path.join(GLOBALS['S2']['qklooks_path'], os.path.basename(vrt).replace('.vrt', '.tif'))
            if not os.path.exists(qkl):
                os.remove(vrt)
                print "del " + vrt

        print "Listing QKL files "
        qkls = glob.glob(GLOBALS['S2']['qklooks_path'] + '/*.tif')
        print "Looping "
        for qkl in qkls:
            vrt = os.path.join(GLOBALS['S2']['virtual_path'], GLOBALS['S2']['resolutions'][0],
                               os.path.basename(qkl).replace('.tif', '.vrt'))
            if not os.path.exists(vrt):
                os.remove(qkl)
                print "del " + qkl


    except Exception as e:
        print "Error cleaning FILE:" + str(e)


def clean_DB_DISK_from_corrupted_data(db_conn):
    try:

        print "cleaning BD from corrupted or missing QLK or VRT"

        db_conn.row_factory = lambda cursor, row: [row[0],row[1],row[2]]
        cursor = db_conn.cursor()
        rows = cursor.execute('SELECT ID, locationQKL, locationVRT FROM sentinel2').fetchall()
        listIDs=''
        for row in rows:
            if os.path.exists(row[1]) and os.path.exists(row[2]):
                #print row[0] + ' '+ row[1]+' '+row[2]
                continue
            else:
                listIDs = listIDs + '"'+row[0]+'",'
                print row[0]

        if listIDs != '':
            # DRY RUN
            print 'delete from sentinel2 where ID in (' + listIDs[:-1] + ')'
            #res = cursor.execute('delete from sentinel2 where ID in ('+listIDs[:-1]+')')
            #cursor.execute("VACUUM")
            #db_conn.commit()
        print "Done"

        print "Cleaning files that are not on DB"
        qkls = glob.glob(GLOBALS['S2']['qklooks_path']+'/*.tif')
        print "Looping "
        ct=0
        db_conn.row_factory = lambda cursor, row: row[0]
        cursor = db_conn.cursor()
        rows = cursor.execute('SELECT ID FROM sentinel2').fetchall()
        for qkl in qkls:
            ID = os.path.basename(qkl).replace('.tif','')
            if ID not in rows:

                ct+=1
                print ct
                vrt = os.path.join(GLOBALS['S2']['virtual_path'], GLOBALS['S2']['resolutions'][0],os.path.basename(qkl).replace('.tif', '.vrt'))
                os.remove(qkl)
                os.remove(vrt)

            else:
                rows.remove(ID)
                if len(rows) % 1000 == 0:
                    print len(rows)

        print "Removed "+str(ct)+' files'


    except Exception as e:
        print "Error cleaning DB:" + str(e)



def getAll_ID(db_conn):
    try:
        db_conn.row_factory = lambda cursor, row: row[0]
        cursor = db_conn.cursor()
        rows = cursor.execute('SELECT ID FROM sentinel2 order by ID').fetchall()
        return rows
    except:
        return []

def file_on_catalogue(db_conn, ID ):
    try:
        cursor = db_conn.cursor()
        cursor.execute('SELECT ID FROM sentinel2 WHERE ID = ?',(str(ID),))
        row = cursor.fetchone()
        if row:
          return True
        else:
          return False
    except:
        return False

def create_empty_catalogue(DB):
    if not os.path.exists(DB):
        import sqlite3

        conn = sqlite3.connect(DB)
        conn.enable_load_extension(True)
        conn.execute("SELECT load_extension('libspatialite.so')")
        conn.execute("SELECT InitSpatialMetaData()");
        cursor = conn.cursor()


        f1 = 'ID' # name of the column
        ft1 = 'TEXT'  # column data type
        f2 = 'Cloud' # name of the column
        ft2 = 'INTEGER'  # column data type
        f3 = 'Product' # name of the column
        ft3 = 'TEXT'  # column data type
        f4 = 'ACQTime' # name of the column
        ft4 = 'INTEGER'  # column data type
        f5 = 'Orbit' # name of the column
        ft5 = 'INTEGER'  # column data type
        f6 = 'MGRSID' # name of the column
        ft6 = 'TEXT'  # column data type
        f7 = 'locationQKL' # name of the column
        ft7 = 'TEXT'  # column data type
        f8 = 'locationVRT' # name of the column
        ft8 = 'TEXT'  # column data type
        f9 = 'src_srs' # name of the column
        ft9 = 'TEXT'  # column data type
        f10 = 'PROCTime' # name of the column
        ft10 = 'INTEGER'  # column data type
        f11 = 'RANK' # name of the column
        ft11 = 'INTEGER'  # column data type
        print "Creating a new SQLite table"
        cursor.execute("CREATE TABLE sentinel2 ({f1} {ft1} PRIMARY KEY, {f2} {ft2}, {f3} {ft3}, {f4} {ft4}, {f5} {ft5}, {f6} {ft6}, {f7} {ft7}, {f8} {ft8}, {f9} {ft9}, {f10} {ft10}, {f11} {ft11})"
                  .format( f1=f1, ft1=ft1, f2=f2, ft2=ft2, f3=f3,  ft3=ft3, f4=f4, ft4=ft4, f5=f5, ft5=ft5, f6=f6, ft6=ft6, f7=f7, ft7=ft7, f8=f8, ft8=ft8, f9=f9, ft9=ft9, f10=f10, ft10=ft10, f11=f11, ft11=ft11 ))
        conn.commit()
        cursor.execute("SELECT AddGeometryColumn('sentinel2', 'the_geom', 3857, 'POLYGON', 'XY', 1)")
        conn.close()
        print "done"

#-----------------------------------------------------------------------

def create_structure_and_catalogues():
    years = ['2015', '2016', '2017', '2018', '2019', '2020']
    months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12' ]
    days = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']
    for year in years:
        for month in months:
            for day in days:

                if not os.path.exists(os.path.join(GLOBALS['S2']['unzip_path'], year, month, day)):
                    os.makedirs(os.path.join(GLOBALS['S2']['unzip_path'], year, month, day))


                for res in GLOBALS['S2']['resolutions']:
                    if not os.path.exists(os.path.join(GLOBALS['S2']['virtual_path'], year, month, day, res)):
                        os.makedirs(os.path.join(GLOBALS['S2']['virtual_path'], year, month, day, res))


                if not os.path.exists(os.path.join(GLOBALS['S2']['qklooks_path'],year, month, day)):
                    os.makedirs(os.path.join(GLOBALS['S2']['qklooks_path'],year, month, day))

    if not os.path.exists(GLOBALS['S2']['sqlite_database']):
        create_empty_catalogue(GLOBALS['S2']['sqlite_database'])




#-----------------------------------------------------------------------

def make_virtual_qklooks(inSAFE, YYYY,MM,DD):
    try:
        granule = os.path.basename(inSAFE.replace('.SAFE',''))
        BANDS = GLOBALS['S2']['s2_bands']
        res = GLOBALS['S2']['resolutions'][0]
        qres = GLOBALS['S2']['qklooks_resolutions'][0]

        processing_list = traverseRecursively(inSAFE,BANDS)
        lista = ''
        for img in processing_list:
            lista = lista+img+' '
        if lista == '':
            return False

        VRTfile = os.path.join(GLOBALS['S2']['virtual_path'], YYYY, MM, DD, res, granule+'.vrt')
        TIFfile = os.path.join(GLOBALS['S2']['qklooks_path'], YYYY, MM, DD, granule+'.tif' )
        res1 = os.system("gdalbuildvrt -srcnodata 0 -hidenodata -vrtnodata 0 -separate -resolution user -tr "+res+" "+res+" "+VRTfile+' '+lista+' -q --config CPL_LOG '+os.path.join(GLOBALS['S2']['scripts_path'],'gdalerror.txt') )
        if os.path.exists(VRTfile):
            # mapserver creation of GTIF is equally fast but no projection in out
            #Sentinel2.SQLITEgenerateQuickLook(VRTfile, "500", "B11,B8A,B12", "1,4000", "1,4000", "1,4000")
            memout = gdal.Translate('mem', VRTfile, bandList = [12,9,13], format='MEM', xRes = qres, yRes = qres, outputType = gdal.GDT_Byte,scaleParams = [[0,4000,0,254],[0,4000,0,254],[0,4000,0,254]], noData = 0)
            dstout = gdal.Warp(TIFfile, memout, dstSRS = 'EPSG:3857')

            if os.path.exists(TIFfile):
                return [VRTfile, TIFfile]
            else:
                return False
        return False

    except Exception,e:
        print str(e)
        return False

# ----------------------------------------------------------------------------------------------------------------------
def get_footprint_geom_from_qklooks(tiffile):
    src_ds = gdal.Open( tiffile )
    src_band = src_ds.GetRasterBand(1)
    mem_drv = ogr.GetDriverByName( 'Memory' )
    mem_ds = mem_drv.CreateDataSource( 'out' )
    mem_layer = mem_ds.CreateLayer( 'poly', None, ogr.wkbPolygon )
    fd = ogr.FieldDefn( 'DN', ogr.OFTInteger )
    mem_layer.CreateField( fd )
    result = gdal.Polygonize( src_band, src_band.GetMaskBand(), mem_layer, 0 )
    geomcol = ogr.Geometry(ogr.wkbGeometryCollection)
    for feature in mem_layer:
        geomcol.AddGeometry(feature.GetGeometryRef())
    # Calculate convex hull
    convexhull = geomcol.ConvexHull()
    buffer=100
    simplify=500
    bufferGeom = convexhull.Buffer(buffer)
    bufferGeom = bufferGeom.Simplify(simplify)
    return bufferGeom



#-----------------------------------------------------------------------------------------------------------------------
def get_metadata_info_from_SAFE(inSAFE):
    import re
    from xml.etree import ElementTree
    GENERATION_TIME = False

    XML=os.path.join(GLOBALS['S2']['unzip_path'],inSAFE,'MTD_MSIL1C.xml')
    if os.path.exists(XML):
        with open(XML, 'rt') as f:
            tree = ElementTree.parse(f)
        for node in tree.iter('PRODUCT_TYPE'):
            PRODUCT=str(node.text)
        for node in tree.iter('Cloud_Coverage_Assessment'):
            CLOUDS=float(node.text)
        for node in tree.iter('DATATAKE_SENSING_START'):
            ACQTime=str(node.text)[:10].replace('-','')
        for node in tree.iter('SENSING_ORBIT_NUMBER'):
            ORBIT=str(node.text)
        for node in tree.iter('GENERATION_TIME'):
            GENERATION_TIME=str(node.text)[:10].replace('-','')
        try:
            for node in tree.iter('PRODUCT_URI'):
                MGRS=str(node.text.split('_')[-2])   # '-' is in the old file format
                if re.search('^T[0-9][0-9][A-Z][A-Z][A-Z]$', MGRS) is None:
                    print "--------------- MGRS NOT CORRECT ---------------"
                    print MGRS
                    MGRS = '0'
        except:
            MGRS = '1'

    # ----------  OLD FILE FORMAT pseudo tiles ---------
    else:
        print "OLD XML"

        newXML=(os.path.basename(inSAFE)[:-12]+'.xml').replace('S2A_OPER_MSI_L1C','S2A_OPER_MTD_L1C')
        print newXML
        XML=os.path.join(GLOBALS['S2']['unzip_path'],inSAFE,newXML)
        print XML

        if not os.path.exists(XML):
            return [False,False,False,False,False,False]
        ACQdate=os.path.basename(inSAFE).split('_')[7]

        ORBIT = re.search('_R[0-9][0-9][0-9]_', os.path.realpath(inSAFE))

        if ORBIT is None:
            print "ORBIT ERROR"
            ORBIT= 0
        ORBIT = int(ORBIT.group(0).replace('_','').replace('R',''))


        PRODUCT='S2MSI1C'

        with open(XML, 'rt') as f:
            tree = ElementTree.parse(f)
        for node in tree.iter('CLOUDY_PIXEL_PERCENTAGE'):
            CLOUDS=float(node.text)
        for node in tree.iter('SENSING_TIME'):
            ACQTime=str(node.text)[:10].replace('-','')
        for node in tree.iter('ARCHIVING_TIME'):  # NOT CORRECT BUT WILL BE REPLACED BY NEW FILES SOON
            GENERATION_TIME=str(node.text)[:10].replace('-','')
        try:

            MGRS=str(XML.split('_')[-1]).replace('.xml','')   # '-' is in the old file format

            if re.search('^T[0-9][0-9][A-Z][A-Z][A-Z]$', MGRS) is None:
                print "--------------- MGRS NOT CORRECT2 ---------------"
                print MGRS
                MGRS = '0'
        except:
            MGRS = '1'

    return [PRODUCT,CLOUDS,ACQTime,ORBIT,MGRS,GENERATION_TIME]

def get_metadata_info_from_XML(XML):
    import re
    from xml.etree import ElementTree

    PRODUCT = False
    CLOUDS = False
    ACQTime = False
    ORBIT = False
    MGRS = False
    GENERATION_TIME = False
    #XML=os.path.join(GLOBALS['S2']['unzip_path'],inSAFE,'MTD_MSIL1C.xml')
    try:

        with open(XML, 'rt') as f:
            tree = ElementTree.parse(f)
        for node in tree.iter('PRODUCT_TYPE'):
            PRODUCT=str(node.text)
        for node in tree.iter('Cloud_Coverage_Assessment'):
            CLOUDS=float(node.text)
        for node in tree.iter('DATATAKE_SENSING_START'):
            ACQTime=str(node.text)[:10].replace('-','')
        for node in tree.iter('SENSING_ORBIT_NUMBER'):
            ORBIT=str(node.text)
        for node in tree.iter('GENERATION_TIME'):
            GENERATION_TIME=str(node.text)[:10].replace('-','')
        try:
            for node in tree.iter('PRODUCT_URI'):
                MGRS=str(node.text.split('_')[-2])   # '-' is in the old file format

                print "MGRS from MET"
                print MGRS

                if re.search('^T[0-9][0-9][A-Z][A-Z][A-Z]$', MGRS) is None:

                    print "--------------- MGRS NOT CORRECT1 ---------------"
                    print MGRS
                    MGRS = '0'

                    MGRS = (XML.split('_')[-1]).replace('.xml','')  # '-' is in the old file format
                    if re.search('^T[0-9][0-9][A-Z][A-Z][A-Z]$', MGRS) is None:
                        print "--------------- MGRS NOT CORRECT2 ---------------"
                        print MGRS
                        MGRS = '0'
                    # try:
                    #     for node in tree.iter('Granule_List'):
                    #         print 'NODE:'
                    #         print str(node[0][0])
                    #         print str(node[0][0].text)
                    #         # MGRS = str(node.text.split('_')[-2])  # '-' is in the old file format
                    #         # if re.search('^T[0-9][0-9][A-Z][A-Z][A-Z]$', MGRS) is None:
                    #         #     print "--------------- MGRS NOT CORRECT ---------------"
                    #         #     print MGRS
                    #         #     MGRS = '0'
                    # except Exception as e:
                    #     print "Retry error " + str(e)
        except:
            MGRS = '1'

        if MGRS in (False, 0, 1):
            #try to extract from Name again
            MGRS = (XML.split('_')[-1]).replace('.xml', '')  # '-' is in the old file format
            if re.search('^T[0-9][0-9][A-Z][A-Z][A-Z]$', MGRS) is None:
                print "--------------- MGRS NOT CORRECT3 ---------------"
                print MGRS
                MGRS = False

        if PRODUCT == False:
            PRODUCT = 'S2MSI1C'

        if ORBIT == False:
            ORBIT = re.search('_R[0-9][0-9][0-9]_', os.path.realpath(XML))
            if ORBIT is None:
                print "ORBIT ERROR"
                ORBIT = 0
            ORBIT = int(ORBIT.group(0).replace('_', '').replace('R', ''))

        if CLOUDS == False:
            for node in tree.iter('CLOUDY_PIXEL_PERCENTAGE'):
                CLOUDS = float(node.text)
        if ACQTime == False:
            for node in tree.iter('SENSING_TIME'):
                ACQTime = str(node.text)[:10].replace('-', '')
        if GENERATION_TIME == False:
            for node in tree.iter('ARCHIVING_TIME'):  # NOT CORRECT BUT WILL BE REPLACED BY NEW FILES SOON
                GENERATION_TIME = str(node.text)[:10].replace('-', '')

    # ----------  OLD FILE FORMAT pseudo tiles ---------
    except Exception as e:
        print 'ERROR ' + str(e)

    return [PRODUCT,CLOUDS,ACQTime,ORBIT,MGRS,GENERATION_TIME]
#-----------------------------------------------------------------------------------------------------------------------
def get_EPSG_from_VRT(vrt):
    data_source = gdal.Open(vrt)
    srs = "EPSG:"+str(osr.SpatialReference(data_source.GetProjection()).GetAttrValue("AUTHORITY", 1))
    return srs



#-----------------------------------------------------------------------
# REMOVE S2 from disk
#-----------------------------------------------------------------------

def removeS2fromDISK(file):
    try:
        VRT=os.path.join(GLOBALS['S2']['virtual_path'][0],file+'.vrt')
        TIF=os.path.join(GLOBALS['S2']['qklooks_path'],file+'.tif')

        if os.path.exists(VRT):
            os.remove(VRT)
        if os.path.exists(TIF):
            os.remove(TIF)
    except Exception as e:
        print "Error removing file " + file + ' :' + str(e)



#-----------------------------------------------------------------------
# REMOVE S2  from catalogues
#-----------------------------------------------------------------------

def removeS2fromDB(file):
    try:
        DB = GLOBALS['S2']['sqlite_database']

        # -- initialize DB connection --
        db_conn = sqlite3.connect(DB)
        db_conn.enable_load_extension(True)
        print "enabling extension"
        db_conn.execute("SELECT load_extension('libspatialite.so')")
        cursor = db_conn.cursor()
        cursor.execute("DELETE from sentinel2 where ID = "+file.replace('.SAFE',''))
        cursor.execute("VACUUM")
        db_conn.close()
        print "File removed from DB"
    except Exception as e:
        print "Error removing file "+file+' :'+str(e)





# ----------------------------------------------------------------------------------------------------------------
#            TEST IMG SHP OVERLAPS
# ----------------------------------------------------------------------------------------------------------------

def test_overlapping(shp_img,img):

    if shp_img.endswith('.shp'):

        # --------------  IN SHP  -------------------
        #print "Shapefile vs raster <br>"
        shp_ds = ogr.Open(shp_img)
        layer = shp_ds.GetLayer(0)
        INSR = layer.GetSpatialRef()
        INextent = layer.GetExtent()
        shp_ds=None

    if shp_img.endswith('.tif') or shp_img.endswith('.vrt'):

        # --------------  IN IMG  -------------------
        #print "Raster vs raster <br>"
        in_ds = gdal.Open(shp_img)
        INSR = osr.SpatialReference()
        INSR.ImportFromWkt(in_ds.GetProjectionRef())

        geoTransform = in_ds.GetGeoTransform()
        minx = geoTransform[0]
        maxy = geoTransform[3]
        maxx = minx + geoTransform[1]*in_ds.RasterXSize
        miny = maxy + geoTransform[5]*in_ds.RasterYSize
        INextent=[minx,maxx,miny,maxy]
        in_ds=None

    print INextent

    # --------------  IN IMG  -------------------

    img_ds = gdal.Open(img)
    imgGeo = img_ds.GetGeoTransform()

    cols = img_ds.RasterXSize
    rows = img_ds.RasterYSize

    imgSR = osr.SpatialReference()
    imgSR.ImportFromWkt(img_ds.GetProjectionRef())
    img_ds=None
    transform  = osr.CoordinateTransformation(imgSR,INSR)
    (ulx, uly,holder) = transform.TransformPoint(imgGeo[0],imgGeo[3])
    (lrx, lry,holder) = transform.TransformPoint(imgGeo[0]+cols*imgGeo[1],imgGeo[3]+rows*imgGeo[5])

    wkt1 = "POLYGON (("+str(INextent[0])+" "+str(INextent[2])+","+str(INextent[1])+" "+str(INextent[2])+","+str(INextent[1])+" "+str(INextent[3])+","+str(INextent[0])+" "+str(INextent[3])+","+str(INextent[0])+" "+str(INextent[2])+"))"
    wkt2 = "POLYGON (("+str(ulx)+" "+str(uly)+","+str(lrx)+" "+str(uly)+","+str(lrx)+" "+str(lry)+","+str(ulx)+" "+str(lry)+","+str(ulx)+" "+str(uly)+"))"

    poly1 = ogr.CreateGeometryFromWkt(wkt1)
    poly2 = ogr.CreateGeometryFromWkt(wkt2)

    intersection = poly1.Intersection(poly2)
    #print intersection.ExportToWkt()
    return (intersection.ExportToWkt() != 'GEOMETRYCOLLECTION EMPTY')

# ----------------------------------------------------------------------------------------------------------------
#            TEST IMG SHP OVERLAPS
# ----------------------------------------------------------------------------------------------------------------

def valid_user_key(user_key):
    # test if is a valid MD5
    return re.findall(r'(?i)(?<![a-z0-9])[a-f0-9]{32}(?![a-z0-9])', user_key)

