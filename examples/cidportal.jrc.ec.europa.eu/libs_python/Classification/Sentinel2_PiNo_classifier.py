#!/bin python

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
import string
import shutil 
import platform 
import glob
import time
import numpy
from stat import *
import ctypes
#from pymorph import mmorph 

import gdal 

try:
    import simplejson as json
except (ImportError,):
    import json

#from PiNo_classifier import *

numpy.seterr(divide='ignore', invalid='ignore')
Memory_Buffer=3  # 2b on the safe side - other user app running etc etc - , when using tiling mode use only 1/Memory_Buffer memory amount to prevent mem error

  
def usage():
	print
	print 'Author: Simonetti Dario for European Commission  2015'
	print 'Wrapper for Satellite data classifier ---> Pixel Image 2 Natural Objects'
	print 'RUN_PiNo_classifier.py overwrite apply_fores_normalization images'
	print
	sys.exit(0)

  
def getArgs(args):
    
    infiles = None
   
    if (len(sys.argv) < 5):
        usage()
    else: 
	
        	overwrite=sys.argv[1]
		apply_fnorm=sys.argv[2]
		infile=sys.argv[3]
		outfile=sys.argv[4]
		if ( infiles is None ):
			usage()
				
		else:
			 return overwrite,apply_fnorm,infile,outfile
    



class Metadata:
	def __init__(self):
		self.sensor = ""
		self.gain = [] 
		self.bias = [] 
		self.sunel=0.
		self.sunazi=0.
		self.ESdistance=0.
		self.clouds=-1
	def __str__(self):
		return self


def UnixMemory():
    """
    Get node total memory and memory usage
    """
    with open('/proc/meminfo', 'r') as mem:
        ret = {}
        tmp = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) == 'MemTotal:':
                ret['total'] = int(sline[1])
            elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                tmp += int(sline[1])
        ret['free'] = tmp
        ret['used'] = int(ret['total']) - int(ret['free'])
    return ret



class SysInfo:

    def __init__(self):

        self.totalRam, self.availRam = self.ram()
        self.totalRam = self.totalRam / (1048576)
        self.availRam = self.availRam / (1048576)



    def ram(self):
     try:
        kernel32 = ctypes.windll.kernel32
        c_ulong = ctypes.c_ulong
        class MEMORYSTATUS(ctypes.Structure):
            _fields_ = [
                ('dwLength', c_ulong),
                ('dwMemoryLoad', c_ulong),
                ('dwTotalPhys', c_ulong),
                ('dwAvailPhys', c_ulong),
                ('dwTotalPageFile', c_ulong),
                ('dwAvailPageFile', c_ulong),
                ('dwTotalVirtual', c_ulong),
                ('dwAvailVirtual', c_ulong)
            ]

        memoryStatus = MEMORYSTATUS()
        memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUS)
        kernel32.GlobalMemoryStatus(ctypes.byref(memoryStatus))
        return (memoryStatus.dwTotalPhys, memoryStatus.dwAvailPhys)
     except:
        print "No ram "




# ----------------------------------------------------------------------------------------------------------------	
def classify_tile(src_ds,MinX,MinY,MaxX,MaxY,sat,fnorm_delta_val,DataType):
		th_NDVI_MAX_WATER=0.0
		th_NDVI_SATURATION=0.0037
		th_NDVI_MIN_CLOUD_BARE=0.35
		th_NDVI_MIN_VEGE=0.45

		th_SHALLOW_WATER=-0.1

		th_RANGELAND=0.50
		th_GRASS=0.55
		th_SHRUB=0.65
		th_TREES=0.78 
		
		
				
		if (sat == "S2A_L1C"):
			sat = "oli"

			#print "------ Processing ------",MinX,MinY,MaxX,MaxY+"<br>"
			band = src_ds.GetRasterBand(2) ; BAND1 = band.ReadAsArray(MinX,MinY,MaxX-MinX,MaxY-MinY).astype(numpy.float);band=None;del band
			band = src_ds.GetRasterBand(3) ; BAND2 = band.ReadAsArray(MinX,MinY,MaxX-MinX,MaxY-MinY).astype(numpy.float);band=None;del band
			band = src_ds.GetRasterBand(4) ; BAND3 = band.ReadAsArray(MinX,MinY,MaxX-MinX,MaxY-MinY).astype(numpy.float);band=None;del band
			band = src_ds.GetRasterBand(8) ; BAND4 = band.ReadAsArray(MinX,MinY,MaxX-MinX,MaxY-MinY).astype(numpy.float);band=None;del band
			band = src_ds.GetRasterBand(12) ; BAND5 = band.ReadAsArray(MinX,MinY,MaxX-MinX,MaxY-MinY).astype(numpy.float);band=None;del band
			band = src_ds.GetRasterBand(13) ; BAND7 = band.ReadAsArray(MinX,MinY,MaxX-MinX,MaxY-MinY).astype(numpy.float);band=None;del band


			# sentinel2
			if DataType =="Byte":
				FACTOR=255.
			elif DataType == "Uint16":
				FACTOR=10000.0
			else:
				FACTOR = 1.0

			numpy.divide(BAND1,FACTOR,BAND1)
			numpy.divide(BAND2,FACTOR,BAND2)
			numpy.divide(BAND3,FACTOR,BAND3)
			numpy.divide(BAND4,FACTOR,BAND4)
			numpy.divide(BAND5,FACTOR,BAND5)
			numpy.divide(BAND7,FACTOR,BAND7)


			if (len(fnorm_delta_val) > 1):
				MASK=((BAND2 ==0) * (BAND3 ==0) * (BAND4 == 0)).astype(bool)

				numpy.add(BAND1,fnorm_delta_val[0],BAND1)
				numpy.add(BAND2,fnorm_delta_val[1],BAND2)
				numpy.add(BAND3,fnorm_delta_val[2],BAND3)
				numpy.add(BAND4,fnorm_delta_val[3],BAND4)
				numpy.add(BAND5,fnorm_delta_val[4],BAND5)
				numpy.add(BAND7,fnorm_delta_val[5],BAND7)

				BAND1[MASK]=0
				BAND1[BAND1 > 1]=1
				BAND2[MASK]=0
				BAND2[BAND2 > 1]=1
				BAND3[MASK]=0
				BAND3[BAND3 > 1]=1
				BAND4[MASK]=0
				BAND4[BAND4 > 1]=1
				BAND5[MASK]=0
				BAND5[BAND5 > 1]=1
				BAND7[MASK]=0
				BAND7[BAND7 > 1]=1

				
		#TMP_BOOL_MATRIX=(BAND1*0).astype(bool)
		#TMP_MATRIX=(BAND1*0.)
		
		min123=(BAND1*0.)
		numpy.minimum(BAND1,BAND2,min123)
		numpy.minimum(min123,BAND3,min123)
		
		min1234=(BAND1*0.)
		numpy.minimum(min123,BAND4,min1234)
		
		min234=(BAND1*0.)
		numpy.minimum(BAND2,BAND3,min234)
		numpy.minimum(min234,BAND4,min234)
		
		max234=(BAND1*0.)
		numpy.maximum(BAND2,BAND3,max234)
		numpy.maximum(max234,BAND4,max234)
		
		max1234=(BAND1*0.)
		numpy.maximum(BAND1,max234,max1234)
		
		max57=(BAND1*0.)
		numpy.maximum(BAND5,BAND7,max57)
		
		max457=(BAND1*0.)
		numpy.maximum(BAND4,max57,max457)
		
		max123457=(BAND1*0.)
		numpy.maximum(max1234,max57,max123457)
		
		Saturation=(max234-min234)/max234
		
		NDVI = (BAND4 - BAND3) / (BAND4 + BAND3 + 0.00001);
		
		#TMP_MATRIX=None
		#del TMP_MATRIX
		CLASS=(BAND1*0).astype('B')
		
		
		# -----------------------------------------------------------------------
		# --------------  SENSOR DEPENDENT CONDITION ----------------------------
		# -----------------------------------------------------------------------
		
		
		if (sat == "oli" or sat == "tm" or sat == "etm" ):

			growing14=(BAND1*0).astype(bool)
			numpy.logical_and(BAND1 <= BAND2, BAND2 <= BAND3,growing14)
			numpy.logical_and(growing14, BAND3 <= BAND4,growing14)
			numpy.logical_and(growing14, BAND5 <= BAND4,growing14)
			numpy.logical_and(growing14, BAND7 <= BAND5,growing14)


			growing15=(BAND1*0).astype(bool)
			numpy.logical_and(BAND1 <= BAND2, BAND2 <= BAND3,growing15)
			numpy.logical_and(growing15, BAND3 <= BAND4,growing15)
			numpy.logical_and(growing15, BAND4 <= BAND5,growing15)


			NDSI=(BAND1 - BAND5) / (BAND2 + BAND5 + 0.000001);
			WETNESS=0.2626*BAND1*255 + 0.21*BAND2*255 + 0.0926*BAND3*255 + 0.0656*BAND4*255 - 0.7629*BAND5*255 - 0.5388*BAND7*255

			Bright_soil= (numpy.logical_or((BAND1 < 0.27) * growing15,(BAND1 < 0.27) * growing14 *((BAND4-BAND5) > 0.038))).astype(bool)

			Watershape=(((BAND1-BAND2) > -0.2) * (BAND2 >= BAND3) * (BAND3 >= BAND4) *  (BAND4 >= BAND5) * (WETNESS > 0)).astype(bool)

			OtherWaterShape=((BAND1 >= BAND2) * (BAND2 >= BAND3) * (BAND4 >= BAND3) * (BAND5 < BAND4) * (BAND7 <= BAND5) * (BAND4 < BAND3*1.3) * (BAND4 < 0.12) * (BAND5 < BAND3) * (BAND4 <= BAND2) * (BAND4 > 0.039) * (WETNESS > 0 )).astype(bool)

			snowshape= ((min1234 > 0.30 ) * (NDSI > 0.65)).astype(bool)

			corecloudshape=((max123457 > 0.47) * (min1234 > 0.37) * (snowshape == 0) * (Bright_soil == 0)).astype(bool)

			corecloudshape1=((min123 > 0.21) * (BAND5 > min123) * (Saturation >= 0.2) * (Saturation <= 0.4) * (max234 >= 0.35) * (snowshape == 0) * (NDSI > -0.3 ) * (corecloudshape == 0) * (Bright_soil == 0)).astype(bool)

			cloudshape=    ( (min123 > 0.17) * (BAND5 > min123) * (NDSI < 0.65) * (max1234 > 0.30) * ((BAND4/BAND3) >= 1.3) * ((BAND4/BAND2) >= 1.3) * ((BAND4/BAND5) >= 0.95) * (corecloudshape == 0) * (corecloudshape1 == 0) * (Bright_soil == 0) ).astype(bool)

		

		ndvi_1=((NDVI <= th_NDVI_MAX_WATER)).astype(bool)
		ndvi_2=((NDVI < th_NDVI_MIN_VEGE)*(ndvi_1 == 0)).astype(bool)
		ndvi_3=((NDVI >= th_NDVI_MIN_VEGE)).astype(bool)
		
		

		#-------------------------------------------------------------------------------------------------------------
		#----------------------  SECTION 1 : WATER  ---------------------------------------------------------
		#-------------------------------------------------------------------------------------------------------------
		
		CLASS[ndvi_1*(snowshape == 1)]=3
		#     condition to simulate if then else cascade 
		
		if (sat == "oli" or sat == "tm" or sat == "etm" ):
			CLASS[(CLASS ==0 )*ndvi_1* Watershape * (BAND1 > 0.078) * (BAND2 > 0.04) * (BAND2 <= 0.12 ) * (max57 < 0.04)]=5;
			CLASS[(CLASS ==0 )*ndvi_1* (BAND3 >= max457) * (BAND3 <= 0.19) * (BAND3 > 0.04) * (BAND1 > 0.078) * (max57 < 0.04)]=6
				
		

		CLASS[(CLASS == 0 )*ndvi_1*( BAND1 > 0.94) *( BAND2 > 0.94)*( BAND3 > 0.94)* ( BAND4 > 0.94)]=1  # NEW TEST 2014 for L8 saturation on clouds 
		CLASS[(CLASS == 0 )*ndvi_1*(WETNESS > 5)]=8
		CLASS[(CLASS == 0 )*ndvi_1]=41
		
		
		#-------------------------------------------------------------------------------------------------------------
		#----------------------  SECTION 2 : CLOUDS or SOIL  ---------------------------------------------------------
		#-------------------------------------------------------------------------------------------------------------
		
		CLASS[(CLASS == 0 )*ndvi_2*(snowshape ==1)]=3
		
		
		CLASS[(CLASS == 0 )*ndvi_2*( BAND1 > 0.94) *( BAND2 > 0.94)*( BAND3 > 0.94)* ( BAND4 > 0.94)]=1 # NEW TEST 2014 for L8 saturation on clouds 
		
		CLASS[(CLASS == 0 )*ndvi_2*OtherWaterShape*(BAND1 > 0.078) * (max57 < 0.058 )]=7
		CLASS[(CLASS == 0 )*ndvi_2*cloudshape]=1
		CLASS[(CLASS == 0 )*ndvi_2*corecloudshape]=1
		CLASS[(CLASS == 0 )*ndvi_2*corecloudshape1]=2
		
		if not(sat  == "DMC"):
			CLASS[(CLASS == 0 )*ndvi_2* (BAND1 > BAND2) * (BAND2 > BAND3) * (BAND4 > 0.254) * (BAND1 > 0.165) * (NDVI < 0.40)]=2
					
		CLASS[(CLASS == 0 )*ndvi_2* (BAND1 > BAND2) * (BAND1 > 0.27 ) *  (BAND2 > 0.21) * (numpy.absolute(BAND3-BAND2) <= 0.1) * (BAND4 > 0.35 )]=2
		CLASS[(CLASS == 0 )*ndvi_2* (BAND1 < 0.13) * (BAND1 > BAND2) * (BAND2 > BAND3) * (BAND3 < 0.05) * ((BAND1-BAND4) < -0.04 )]=40
		CLASS[(CLASS == 0 )*ndvi_2* (WETNESS > 5)]=8 #only at this point to avoid confusion with shadows
		CLASS[(CLASS == 0 )*ndvi_2* (BAND1 < 0.13 ) * (BAND1 > BAND2) * (BAND2 > BAND3 ) * (BAND3 < 0.05) * ((BAND1-BAND4) < 0.04)]=42
		
		CLASS[(CLASS == 0 )*ndvi_2* (BAND1 < 0.14) * (BAND1 > 0.10) * (BAND1 > BAND2) * (BAND2 > BAND3) * (BAND3 < 0.06) * (BAND4 < 0.14) * ((BAND4-BAND1) < 0.02)]=41
		
		MyCOND=(numpy.absolute(BAND4-BAND2) <= 0.01)+(BAND1-BAND4 >= 0.01)
		CLASS[(CLASS == 0 )*ndvi_2* (BAND1 > BAND2) * (BAND2 > BAND3) * MyCOND * (BAND4 >= 0.06)]=41
		MyCOND=None
		del MyCOND
		
		CLASS[(CLASS == 0 )*ndvi_2* (NDVI <= 0.09) * (BAND4 < 0.4) * (BAND2 <= BAND3) * (BAND3 <= BAND4)]=35
		
		CLASS[(CLASS == 0 )*ndvi_2* (NDVI <= 0.20) * (BAND4 > 0.3) * (BAND1 <= BAND2) * (BAND2 <= BAND3) * (BAND3 <= BAND4)]=34
		CLASS[(CLASS == 0 )*ndvi_2* (NDVI >= 0.35) * (BAND1 >= BAND2) * (numpy.absolute(BAND3-BAND2) < 0.04)]=21
		CLASS[(CLASS == 0 )*ndvi_2* (NDVI >= 0.20) * (numpy.absolute(BAND3-BAND2) < 0.05)]=30
		CLASS[(CLASS == 0 )*ndvi_2]=31
		
		
		#-------------------------------------------------------------------------------------------------------------
		#----------------------  SECTION 3 : VEGETATION  -------------------------------------------------------------
		#-------------------------------------------------------------------------------------------------------------
		
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_RANGELAND) * (BAND4 >= 0.15 )]=21
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_RANGELAND) * (BAND4 < 0.15)]=40
		
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_GRASS ) * (BAND1 <= BAND4) * (BAND4 < 0.15)]=40
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_GRASS ) * (BAND1 <= BAND4)]=16
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_GRASS ) * (BAND1 > BAND4)]=40
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_SHRUB ) * (BAND4 > 0.22)]=14
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_SHRUB ) * (BAND4 >= 0.165)]=12
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_SHRUB ) * (BAND4 < 0.165)]=10
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI < th_TREES ) * (BAND4 < 0.30)]=11
		CLASS[(CLASS == 0 )*ndvi_3* (NDVI > th_TREES)]=9
		CLASS[(CLASS == 0 )*ndvi_3]=13
		
		
		CLASS[(BAND2 ==0) * (BAND3 ==0) * (BAND4 == 0)]=0
		return CLASS
		
		

def getend(start, angle, distance):
	while angle>=360:
		angle-=360
	while angle<0:
		angle+=360
	if angle>270:
		angle-=270
		x=start[0]+math.cos(angle*math.pi/180)*distance*-1
		y=start[1]+math.sin(angle*math.pi/180)*distance*-1
	elif angle==270:
		x=start[0]-distance
		y=start[1]
	elif angle>180:
		angle-=180
		x=start[0]+math.sin(angle*math.pi/180)*distance*-1
		y=start[1]+math.cos(angle*math.pi/180)*distance
	elif angle==180:
		x=start[0]
		y=start[1]+distance
	elif angle>90:
		angle-=90
		x=start[0]+math.cos(angle*math.pi/180)*distance
		y=start[1]+math.sin(angle*math.pi/180)*distance
	elif angle==90:
		x=start[0]+distance
		y=start[1]
	elif angle>0:
		x=start[0]+math.sin(angle*math.pi/180)*distance
		y=start[1]+math.cos(angle*math.pi/180)*distance*-1
	elif angle==0:
		x=start[0]
		y=start[1]-distance
	return (x, y)		
		
		
	
	

def PiNo_classifier(infile,outfile,sat,detect_clouds,sun_azi,fnorm_delta_val):
	try:
		print "INTO pino classifier"
		start = time.time()
		print infile
		src_ds = gdal.Open(infile)
		num_bands=src_ds.RasterCount

		print infile
		print "Bands:"
		print num_bands


		if (sat == "S2A_L1C" and (not num_bands == 13 ) ):
			src_ds = None
			print "Input image does not have 13 bands"+"<br>"
			return(-1)

		DataType = src_ds.GetRasterBand(1).DataType
		DataType = gdal.GetDataTypeName(DataType)
		print "Type: "+DataType

		if (DataType =="Byte"):
			TOTmem=   src_ds.RasterXSize*src_ds.RasterYSize * 8/1024*6*20

		elif (DataType =="UInt16"):
			TOTmem= src_ds.RasterXSize*src_ds.RasterYSize * 16/1024*6*20

		else :
			TOTmem= src_ds.RasterXSize*src_ds.RasterYSize * 32/1024*6*20
			print TOTmem

		res=UnixMemory()
		FREEmem=res['free']
		print FREEmem

		if (FREEmem < TOTmem + (TOTmem/100*20)):
			print "Processing using tiling ..... "+"<br>"
			ratio=int(round(TOTmem*Memory_Buffer/FREEmem*1.,))
		else:
			ratio=1

		print "Ratio: "+str(ratio)+"<br>"





		MaxX=src_ds.RasterXSize
		MaxY=src_ds.RasterYSize

		LenX=int(src_ds.RasterXSize/ratio)
		LenY=int(src_ds.RasterYSize/ratio)

		#print MaxX,MaxY
		#print LenX,LenY

		Xval=[]
		Yval=[]

		for x in range(1,ratio):
			Xval.append(LenX*x)

		Xval.append(MaxX)

		for x in range(1,ratio):
			Yval.append(LenY*x)

		Yval.append(MaxY)

		#print Xval
		#print Yval


		driver = gdal.GetDriverByName("GTiff")
		print outfile

		dst_ds = driver.Create( outfile,src_ds.RasterXSize,src_ds.RasterYSize,1,gdal.GDT_Byte,options=['COMPRESS=LZW'])
		dst_ds.GetRasterBand(1).SetRasterColorInterpretation(gdal.GCI_PaletteIndex)
		c = gdal.ColorTable()
		ctable=[[0,(0,0,0)],[1,(255,255,255)],[2,(192,242,255)],[3,(1,255,255)],[4,(0,0,0)],[5,(1,1,255)],[6,(1,123,255)],[7,(110,150,255)],[8,(168,180,255)],[9,(160,255,90)],[10,(1,80,1)],[11,(12,113,1)],[12,(1,155,1)],[13,(100,190,90)],[14,(146,255,165)],[15,(0,0,0)],[16,(210,255,153)],[17,(0,0,0)],[18,(0,0,0)],[19,(0,0,0)],[20,(0,0,0)],[21,(237,255,193)],[22,(200,230,200)],[23,(0,0,0)],[24,(0,0,0)],[25,(0,0,0)],[26,(0,0,0)],[27,(0,0,0)],[28,(0,0,0)],[29,(0,0,0)],[30,(200,200,150)],[31,(227,225,170)],[32,(0,0,0)],[33,(0,0,0)],[34,(255,225,255)],[35,(140,5,190)],[36,(255,1,1)],[37,(0,0,0)],[38,(0,0,0)],[39,(0,0,0)],[40,(20,40,10)],[41,(145,1,110)],[42,(100,100,100)]]
		for cid in range(0,43):
			c.SetColorEntry(cid,ctable[cid][1])

		dst_ds.GetRasterBand(1).SetColorTable(c)
		dst_ds.SetGeoTransform( src_ds.GetGeoTransform())
		dst_ds.SetProjection( src_ds.GetProjectionRef())

		print 'Setting out file ....'
		OUTCLASS=dst_ds.GetRasterBand(1).ReadAsArray(0,0,dst_ds.RasterXSize,dst_ds.RasterYSize)
		print 'Processing <br>'
		mytry=0

		#try:
		if (1==1):
			MinX=0
			MinY=0
			for x in range(0,len(Xval)):
				for y in range(0,len(Yval)):

					MaxX=Xval[x]
					MaxY=Yval[y]
					OUTCLASS[MinY:MaxY,MinX:MaxX]=classify_tile(src_ds,MinX,MinY,MaxX,MaxY,sat,fnorm_delta_val,DataType)
					MinY=MaxY
				MinX=MaxX
				MinY=0

			dst_ds.GetRasterBand(1).WriteArray(OUTCLASS)

			if (detect_clouds==0):
				OUTCLASS[(OUTCLASS==1)]=34
				OUTCLASS[(OUTCLASS==2)]=34

			else:
				try:
					dst_ds.GetRasterBand(1).WriteArray(OUTCLASS)  # save temporary out so class is saved even on mask failure

					filter=numpy.ndarray(shape=(17,17), dtype=bool)
					filter[:]=False
					filter[0,8]=True
					filter[1,7:9]=True
					filter[2,6:9]=True
					filter[3,5:10]=True
					filter[4,4:11]=True
					filter[5,3:12]=True
					filter[6,2:14]=True
					filter[7,2:14]=True
					filter[8,0:16]=True
					filter[9,2:14]=True
					filter[10,2:14]=True
					filter[11,3:12]=True
					filter[12,4:11]=True
					filter[13,5:10]=True
					filter[14,6:9]=True
					filter[15,7:9]=True
					filter[16,8]=True

					BOOL_MATRIX=numpy.zeros((dst_ds.RasterXSize,dst_ds.RasterYSize)).astype(bool)
					BOOL_MATRIX=(OUTCLASS==1)+(OUTCLASS==2)
					#OUTCLASS[mmorph.close(BOOL_MATRIX,filter)]=1  # 3x3

					#------------------------------------------------------------------------------------------
					#-------------------------USE 3D filter for CL - SH detection -----------------------------
					#------------------------------------------------------------------------------------------
					if (int(sun_azi) > 0 ):

						sft=getend([100,100],270-int(sun_azi),20)
						shiftX=100-int(sft[0])
						shiftY=100-int(sft[1])

						BOOL_MATRIX=numpy.roll(BOOL_MATRIX,shiftX,axis=0)
						BOOL_MATRIX=numpy.roll(BOOL_MATRIX,shiftY,axis=1)
						print "Cloud masking step 1"+"<br>"
						SHDW_MATRIX=((OUTCLASS==10)+(OUTCLASS==40)+(OUTCLASS==41)+(OUTCLASS==42)+(OUTCLASS==34)+(OUTCLASS==35)+(OUTCLASS==36)+(OUTCLASS==4)+(OUTCLASS==5)+(OUTCLASS==6)+(OUTCLASS==7)+(OUTCLASS==8)).astype(bool)

						SHDW_MATRIX*=BOOL_MATRIX
						print "Cloud masking step 2"+"<br>"

						#OUTCLASS[mmorph.close(SHDW_MATRIX,filter)]=42
						print "Cloud masking step 3"+"<br>"
				except:
					print "Image is TOO BIG for morphological filters <br>"


			dst_ds.GetRasterBand(1).WriteArray(OUTCLASS)


			#close roperly the dataset
			dst_ds = None
			src_ds = None

			print "Execution time: "+str(time.time()-start)+"<br>"


			return 'Complete'+"<br>"

	except Exception,e:
		print "Error  :"
		print str(e)


# ----------------------------------------------------------------------------------------------------------------	
# ----------------------------------------------------------------------------------------------------------------
#
#            LOOP input DIR and process file according to flags (2 implement)
#
# ----------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------


def run_PiNo_classifier(overwrite,apply_fnorm,IN,OUT):
	try:
		if (IN  == '' ):
			return " No images ...."



		#-----------------------------------------------------------------------------------------
		#------------------------add better test to determine image type -------------------------
		#-----------------------------------------------------------------------------------------
		#MTL_met=None
		#MET_met=None
		#XML_met=None
		MetOBJ=Metadata()

		#MetOBJ=get_Landsat_metadata_info('')  # create empty METOBJ


		if (('S2A' in IN) and ("_MSI"  in IN) and ("L1C_" in IN)) :
			tmp=os.path.basename(IN.replace('.vrt','_class.tif'))

			MetOBJ.sensor='S2A_L1C'

			fnorm_median_reference=[0.086,0.062,0.043,0.247,0.109,0.039] # LandsatLike
			MetOBJ.clouds=''




		if (os.path.exists(OUT) and overwrite == False):

			print OUT+' file Already Processed '
			return
		if not os.path.exists(os.path.dirname(OUT)):
                    os.mkdir(os.path.dirname(OUT))


		detect_clouds=1
		if ( (MetOBJ.clouds == -1) & (MetOBJ.sunazi == 0.) ):
			detect_clouds=0
			print "!Cloud detection disabled, no metadata!"

		fnorm_median_delta=[]
		if (os.path.exists(OUT)):
			os.remove(OUT);
		if (os.path.exists(OUT+'.aux.xml')):
			os.remove(OUT+'.aux.xml');

		if (apply_fnorm == 'Yes'):
			try:
				print "-- Forest Normalization --<br>"
				# compute bands median value inside a Mask (evergreen forest)
				fnorm_median=get_image_medians_from_mask(IN,MetOBJ.sensor,REFmask)#[0.086,0.062,0.043,0.247,0.109,0.039]
				if (len(fnorm_median) > 1):
					fnorm_median_delta=numpy.subtract(fnorm_median_reference,fnorm_median)
			except:
				print "-- FN Failure: memory --"

		res=PiNo_classifier(IN,OUT,MetOBJ.sensor,detect_clouds,MetOBJ.sunazi,fnorm_median_delta)
		if os.path.exists(OUT):
			os.system('gdaladdo  '+OUT+' 2 4 8 16 32 64')


	except Exception,e:
		print "Error"
		print str(e)
		return
	
	
	



if __name__ == "__main__":
	overwrite,apply_fnorm,infile,outfile = getArgs(sys.argv)    
	run_PiNo_classifier(overwrite,apply_fnorm,infile,outfile)

