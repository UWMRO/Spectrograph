import numpy
import os
import random
import time
import logging
import SetupDevice
import shutil
from pylibapogee import pylibapogee as apg

testName = "norm/fast speed switching"
testLog = logging.getLogger('apogeeTest')


def run( baseDir ):
	try:
		testLog.info( "%s STARTED" % (testName) )
		
		#make dir name, deleting or if
		outDir = os.path.join( baseDir, "nfSwitch" )
		if( os.path.exists(outDir) ):
			shutil.rmtree(outDir)

		os.mkdir( outDir )
		
		#look for usb cameras first
		devices = SetupDevice.GetUsbDevices()
		
		# no usb cameras, then look for ethernet cameras
		if( len(devices) == 0 ):
			devices = SetupDevice.GetEthernetDevices()
			
		# exception....no cameras anywhere....
		if( len(devices) == 0 ):
			raise RuntimeError( "No devices found on usb or ethernet" )
			
		cam = SetupDevice.CreateAndConnectCam( devices[0] )
		
		cam.SetCooler( True )
		cam.SetImageCount( 1 )
		
		maxBinR = cam.GetMaxBinRows()
		maxImgR = cam.GetMaxImgRows()
		cam.SetRoiStartRow( 0 )
		cam.SetRoiNumRows( maxImgR )
		rows = cam.GetRoiNumRows()
		
		maxBinC = cam.GetMaxBinCols()
		maxImgC = cam.GetMaxImgCols()
		cam.SetRoiStartCol( 0 )
		cam.SetRoiNumCols( maxImgC )
		cols = cam.GetRoiNumCols()
		
		numAcqImgs = 0
		runCount = 0
		random.seed()
		
		for i in range(0,1000):
			
			if( apg.AdcSpeed_Normal == cam.GetCcdAdcSpeed() ):
				cam.SetCcdAdcSpeed( apg.AdcSpeed_Fast )
			else:
				cam.SetCcdAdcSpeed( apg.AdcSpeed_Normal )
			
			numImgs = random.randint( 1, 10 )
			testLog.info( "%d: going to collect %d images in %d mode" % 
			( i, numImgs, cam.GetCcdAdcSpeed() ) )
			
			for n in range( 0, numImgs ):
				numStr = "%05d" % ( runCount )
				expTime = random.uniform(0.001, 1.0 )
				stopTime =  expTime + 10.0
				testLog.info( "Run %s: starting %f sec exposure" % (numStr,expTime ) )
				t0 = time.time()
				cam.StartExposure( expTime, True )
			
				status = None
				while status != apg.Status_ImageReady:
					if( expTime > 10.0):
						time.sleep( 2 )
					
					status = cam.GetImagingStatus()
	
					if( apg.Status_ConnectionError == status or
						apg.Status_DataError == status or
						apg.Status_PatternError == status ):
						
						msg = "Run %s: FAILED - error in camera status = %d" % (numStr, status)
						raise RuntimeError( msg )
			
					#break the while if we have been trying to
					#get the image
					t1 = time.time()
					diffTime = t1-t0
					if( diffTime > stopTime ):
						msg = "Run %s: FAILED - camera stauts = %d waited %f for image" % (numStr, status, diffTime)
						raise RuntimeError( msg )
					
			
				msg = "Run %s: getting image" % (numStr)
				testLog.info( msg )
				data = cam.GetImage()
				#save only every 10th image
				#in order to not fill up the harddrive
				if( 0 == numAcqImgs % 10 ):
					imgName = "nf-img%s-r%d-c%d.bin" % (numStr, rows, cols)
					fullImgName = os.path.join( outDir, imgName )
					data.tofile( fullImgName )
				numAcqImgs += 1
				runCount += 1
		
		cam.CloseConnection()
		testLog.info( "%s COMPLETED" % (testName) )
		return True
	except:
		 testLog.exception("%s FALIED with exception" % (testName) )
		 return False
