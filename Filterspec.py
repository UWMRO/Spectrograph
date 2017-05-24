#!/user/local/bin python
import  time, wx, thread, os, subprocess, pyfits, re
import serial
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as dt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from pytz import timezone
import scipy
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from scipy import linspace, polyval, polyfit, sqrt, stats, randn
from ctypes import *
import sys

# move line db to directory, error checking on dir

class PageOne(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.comphome=os.getenv('HOME')
        self.imaging=False
        self.stepper=None
        self.ser=None
        self.proc=None
        self.wave_range=50
        if self.comphome == '/Users/jwhueh':
            self.debug=True

        else:
            self.debug=False
            """from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
            from Phidgets.Events.Events import AttachEventArgs, DetachEventArgs, ErrorEventArgs, InputChangeEventArgs, CurrentChangeEventArgs, StepperPositionChangeEventArgs, VelocityChangeEventArgs
            from Phidgets.Devices.Stepper import Stepper"""
        
            #thread.start_new_thread(self.initShutter,())
            
            try:
                self.proc=subprocess.Popen("/opt/apogee/src/apogee_test/alta", stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                thread.start_new_thread(self.cameraTemp,())
                thread.start_new_thread(self.tempQuery,())
                
            except:
                print 'failed to open camera device'
                print 'starting without camera control'
                self.proc=None
                self.debug=True

        self.textBox=wx.TextCtrl(self,size=(300,200), style= wx.TE_READONLY | wx.TE_MULTILINE | wx.VSCROLL)

        x1=410
        y1=5
        self.gotoLabel=wx.StaticText(self,-1,"Wavelength: ",pos=(x1,y1))
        self.gotoText=wx.TextCtrl(self,size=(100,-1),pos=(x1+100,y1))
        self.gotoText.SetValue('800')
        self.gotoButton=wx.Button(self,-1,"Goto Wavelength",pos=(x1+200,y1))
        self.Bind(wx.EVT_BUTTON, self.gotoEvent, self.gotoButton)

        x1=325
        y1=y1+35
        self.calText=wx.StaticText(self,pos=(x1,y1))
        self.calText.SetLabel('TDI Mode Range')
        x1=x1+125
        wr=['400-600','500-700','600-800','800-1000']
        self.calBox=wx.ComboBox(self,-1,choices=wr, pos=(x1,y1), style=wx.CB_READONLY)
        
        x1=x1+200
        self.waveBox=wx.CheckBox(self,-1,'Narrow Band Pass', pos=(x1,y1))
        self.waveBox.SetValue(False)

	self.cameraText=wx.TextCtrl(self,size=(250,-1))	
	self.cameraButton=wx.Button(self,-1,"Camera Command")
	self.Bind(wx.EVT_BUTTON, self.cameraCmd, self.cameraButton)       

        x3=325
        self.darkRunButton=wx.Button(self,-1,"Dark",pos=(x3,170))
        self.darkRunButton.parVal='dark'
        self.Bind(wx.EVT_BUTTON, self.runTakeSeq, self.darkRunButton)

        x3=x3+85
        self.arcRunButton=wx.Button(self,-1,"ARC",pos=(x3,170))
        self.arcRunButton.parVal='arc'
        self.Bind(wx.EVT_BUTTON, self.runTakeSeq, self.arcRunButton)
        
        x3=x3+85
        self.flatRunButton=wx.Button(self,-1,"Flat",pos=(x3,170))
        self.flatRunButton.parVal='flat'
        self.Bind(wx.EVT_BUTTON, self.runTakeSeq, self.flatRunButton)

        x3=x3+85
        self.filterRunButton=wx.Button(self,-1,"Filter",pos=(x3,170))
        self.filterRunButton.parVal='object'
        self.Bind(wx.EVT_BUTTON, self.runTakeSeq, self.filterRunButton)

        self.cmdText=wx.TextCtrl(self,size=(150,-1))

        self.cmdButton=wx.Button(self,-1,"Spectrograph Command")
        self.Bind(wx.EVT_BUTTON,self.cmdExec,self.cmdButton)

        """self.info=['?nm','?mirror','?grating','?turret','?microns','model','serial', 'side-ent-slit', '?gratings']
        self.infoBox=wx.ComboBox(self, -1, choices=self.info, style=wx.CB_READONLY)

        self.infoButton = wx.Button(self, -1, "Retrieve Info")
        self.Bind(wx.EVT_BUTTON, self.retrieveInfo, self.infoButton)"""

        """self.status=wx.StaticText(self)
        self.status.SetLabel('Not Connected')"""

        self.ccdTempText=wx.StaticText(self,-1)
        self.ccdTempText.SetLabel('Camera Temp:')
        self.ccdTemp=wx.StaticText(self)
        self.ccdTemp.SetLabel('0C')

        """self.shutterText=wx.TextCtrl(self,size=(150,-1))
        self.shutterText.AppendText('5000')
        
        self.shutterButton=wx.Button(self,-1,"Shutter Command")
        self.Bind(wx.EVT_BUTTON,self.move,self.shutterButton)

        self.calButton=wx.Button(self,-1,"Cal")
        self.calButton.parVal='cal'
        self.Bind(wx.EVT_BUTTON,self.moveCal,self.calButton)

        self.filterButton=wx.Button(self,-1,"Filter")
        self.filterButton.parVal='filter'
        self.Bind(wx.EVT_BUTTON,self.moveFilter,self.filterButton)"""

        self.vbox=wx.BoxSizer(wx.VERTICAL)
        self.vbox2=wx.BoxSizer(wx.VERTICAL)
        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2=wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox3=wx.BoxSizer(wx.HORIZONTAL)
        self.hbox4=wx.BoxSizer(wx.HORIZONTAL)
        #self.hbox5=wx.BoxSizer(wx.HORIZONTAL)

        self.hbox4.Add(self.textBox,0)
        self.hbox4.Add(self.vbox2,0)

        #self.hbox1.Add(self.status,0)
        self.hbox1.Add(self.ccdTempText,0)
        self.hbox1.Add(self.ccdTemp,0)

        self.hbox2.Add(self.cmdText,0)
        self.hbox2.Add(self.cmdButton,0)
        self.hbox2.Add(self.cameraText,0)
	self.hbox2.Add(self.cameraButton,0)

        """self.hbox3.Add(self.infoBox,0)
        self.hbox3.Add(self.infoButton,0)"""

        """self.hbox5.Add(self.shutterText,0)
        self.hbox5.Add(self.shutterButton,0)
        self.hbox5.Add(self.filterButton,0)
        self.hbox5.Add(self.calButton,0)"""

        self.vbox.Add(self.hbox4,0)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox1,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        self.vbox.Add(self.hbox2,0,wx.ALIGN_CENTER)
        self.vbox.AddSpacer(10)
        #self.vbox.Add(self.hbox3,0,wx.ALIGN_CENTER)
        #self.vbox.AddSpacer(10)
        #self.vbox.Add(self.hbox5,0,wx.ALIGN_CENTER)
        #self.vbox.AddSpacer(10)
        x=375
        y=75
        self.titlePos=wx.StaticText(self,-1,"Wavelength       Grating      Slit Width", pos=(x-10,y))
        y=90
        self.gotoPos=wx.StaticText(self,-1,"000.00", pos=(x,y))
        self.gratingPos=wx.StaticText(self,-1,"1", pos=(x+115,y))
        self.slitPos=wx.StaticText(self,-1,"000", pos=(x+175,y))

        y=120
        self.titleFilter=wx.StaticText(self,-1,"Filter Name                Center        EXP", pos=(x,y))
        
        x=350
        y=140
        self.filterName=wx.TextCtrl(self,size=(175,-1),pos=(x-20,y))
        self.filterCenter=wx.TextCtrl(self,size=(75,-1),pos=(x+160,y))
        self.filterEXP=wx.TextCtrl(self,size=(75,-1),pos=(x+240,y))

        self.filterName.AppendText('')
        self.filterCenter.AppendText('500')
        self.filterEXP.AppendText('2')

        self.SetSizer(self.vbox)

        if self.debug==False:
                    try:
                        self.openPort()
                    except:
                        self.proc.stdin.write('exit 1 1 1\n')
                        print 'start or connect spectrograph'


    def openPort(self):
        self.ser=serial.Serial('/dev/ttyUSB0')
        self.textBox.AppendText('Starting Up\n')
        self.ser.write('model\r')
        self.textBox.AppendText(self.parser(self.ser.readline())[1]+'\n')
 
        self.ser.write('?nm\r')
        self.gotoPos.SetLabel(self.parser(self.ser.readline())[1])

        self.ser.write('?grating\r')
        self.gratingPos.SetLabel(self.parser(self.ser.readline())[1])

        self.ser.write('side-ent-slit\r')
        self.textBox.AppendText(self.parser(self.ser.readline())[1]+'\n')

        self.ser.write('?microns\r')
        self.slitPos.SetLabel(self.parser(self.ser.readline())[1])

        return

    def parser(self, input):
        raw=input.replace('\r\n','')
        num=input.split(' ')[1]
        num_respond=input.split(' ')[0]
        return [raw,num,num_respond]

    def retrieveInfo(self,event):
        cmd=self.infoBox.GetValue()
        self.ser.write(str(cmd)+'\r')
        if cmd=='?gratings':
            time.sleep(.5)
            for x in range(11):
                self.textBox.AppendText(self.parser(self.ser.readline())[0]+'\n')
                time.sleep(.1)
        else:
            time.sleep(.1)
            self.textBox.AppendText(self.parser(self.ser.readline())[0]+'\n')
        return

    def cmdExec(self,event):
        cmd=self.cmdText.GetValue()
        self.ser.write(str(cmd)+'\r')
        time.sleep(.5)
        self.textBox.AppendText(self.parser(self.ser.readline())[0]+'\n')
        return

    def gotoEvent(self,event):
        thread.start_new_thread(self.goto,(self.gotoText.GetValue(),))

    def goto(self, wave):
        if self.debug==True:
            wx.CallAfter(self.textBox.AppendText,(str(wave)+' goto\n'))
            self.gotoPos.SetLabel(str(wave))
            return
        else:
            self.ser.write(str(wave)+' goto\r')
            time.sleep(.1)
            r=self.parser(self.ser.readline())
            self.textBox.AppendText(r[0]+'\n')
            print r
            self.gotoPos.SetLabel(r[2])
            return     


    def scan(self, wave):
        self.ser.write(str(wave)+' >nm\r')
        time.sleep(.1)
        r=self.parser(self.ser.readline())
        self.textBox.AppendText(r[0]+'\n')
        print r
        return                   

    def grating(self, event):
        g=self.gratingText.GetValue()
        self.ser.write(str(g)+' grating\r')
        time.sleep(.1)
        r=self.parser(self.ser.readline())
        self.textBox.AppendText(r[0]+'\n')
        self.gratingPos.SetLabel(r[2])
        return                

    def slit(self, event):
        wave=self.slitText.GetValue()
        self.ser.write(wave+ ' microns\r')
        time.sleep(.1)
        r=self.parser(self.ser.readline())
        self.textBox.AppendText(r[0]+'\n')
        self.slitPos.SetLabel(r[2])                  
        return     

    def takeImage(self, name, t, shutter):
        wx.CallAfter(self.textBox.AppendText,('Taking Image, '+str(name)+'\n'))
	self.proc.stdin.write('image '+name+' '+t+' '+shutter+'\n')
	return

    def runTakeSeq(self,event):
        button= event.GetEventObject()
        print button.parVal
        thread.start_new_thread(self.takeSeq,(button.parVal,))

    def takeSeq(self, type):
        
        r1=['500','700']
        r2=['600','800']
        r3=['1000','800']
        current_nm=0 
        ccd_rate='fast'
        sr=None
        scan_rate=[['1250 nm/min\r','400','600'],['1235 nm/min\r','500','700'],['1210 nm/min\r','600','800'],['1190 nm/min\r','800','1000']]
        
         
        if self.waveBox.GetValue()!=True:  
            if self.calBox.GetValue()=='400-600':
                sr=scan_rate[0][0]
                x='short'
                start=scan_rate[0][2]
                end=scan_rate[0][1]
            if self.calBox.GetValue()=='500-700':
                sr=scan_rate[1][0]
                x='medium'
                start=scan_rate[1][1]
                end=scan_rate[1][1]
            if self.calBox.GetValue()=='600-800':
                sr=scan_rate[2][0]
                x='medium_2'
                start=scan_rate[2][2]
                end=scan_rate[2][1]
            if self.calBox.GetValue()=='800-1000':
                sr=scan_rate[3][0]
                x='long'
                start=scan_rate[3][2]
                end=scan_rate[3][1]

            wx.CallAfter(self.textBox.AppendText,('setting scan rate: '+sr+'\r'))
            self.ser.write(sr)
            self.ser.readline()
            time.sleep(1)
            wx.CallAfter(self.textBox.AppendText,('Taking '+ str(type)+'\n'))
            new_num=0
            name=self.filterName.GetValue()+'_'+str(type)+'_'+str(x)+'.fits'
            
            if os.path.exists(name):
                dir='/opt/FilterSpec/'
                self.files=subprocess.Popen(['ls',dir],shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                p=self.files.stdout.readlines()
                for f in p:
                    l=f.split('.')
                    if re.search(name.split('.')[0],l[0]):
                        if len(l)!=2:
                            new_num=int(l[1])+1
                            
                    name=self.filterName.GetValue()+'_'+str(type)+'_'+str(x)+'.'+str(new_num)+'.fits'
            wx.CallAfter(self.textBox.AppendText,('setting name: '+ name+'\n'))
            wx.CallAfter(self.textBox.AppendText,('setting start point: '+start+'nm\n'))
            wx.CallAfter(self.goto,(start))
            time.sleep(1)
            self.imaging=True
            wx.CallAfter(self.textBox.AppendText,('starting filter scan\n'))
            cmdStr='tdi '+str(type) +' ' + str(name) + ' '+ str(ccd_rate)
            wx.CallAfter(self.proc.stdin.write,(cmdStr+'\n'))
            wx.CallAfter(self.scan,(end))
            #wx.CallAfter(self.status.SetLabel,('MOVING'))
            while float(current_nm) != float(end):
                self.ser.write('?nm\r')
                current_nm=self.parser(self.ser.readline())[1]
                wx.CallAfter(self.gotoPos.SetLabel,(str(current_nm)))
                time.sleep(1)
            time.sleep(2)
            #wx.CallAfter(self.status.SetLabel,('STOPPED'))
            self.ser.write('mono-stop \r')
            wx.CallAfter(self.textBox.AppendText,(self.parser(self.ser.readline())[0]+'\n'))
            self.imaging=False
        else:
            center=self.filterCenter.GetValue()
            name=self.filterName.GetValue()+'_'+str(center)+'_'+str(type)+'_narrow.fits'
            new_num=0
            if os.path.exists(name):
                dir='/opt/FilterSpec/'
                self.files=subprocess.Popen(['ls',dir],shell=False,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                p=self.files.stdout.readlines()
                for f in p:
                    l=f.split('.')
                    if re.search(name.split('.')[0],l[0]):
                        if len(l)!=2:
                            new_num=int(l[1])+1
            
                name=self.filterName.GetValue()+'_'+str(center)+'_'+str(type)+'_narrow.'+str(new_num)+'.fits'
            wx.CallAfter(self.textBox.AppendText,(str(name+'\n')))
            wx.CallAfter(self.goto,(center))
            time.sleep(1)
            self.imaging=True
            if str(type)=='dark':
                t=0
            else:
                t=1
            wx.CallAfter(self.textBox.AppendText,('Starting image\n'))
            cmdStr='image '+str(name)+' '+str(self.filterEXP.GetValue()) +' '+ str(t)
            wx.CallAfter(self.proc.stdin.write,(cmdStr+'\n'))
            self.imaging=False
            wx.CallAfter(self.textBox.AppendText,('Image Finished \n'))
        return

    def cameraCmd(self, event):
	text=self.cameraText.GetValue()
        self.proc.stdin.write(str(text)+"\n")
	return

    def tempQuery(self):
        while True:
            if self.imaging==False:
                self.proc.stdin.write('status 1 1 1 \n')
            time.sleep(10)

    def cameraTemp(self):
        line=None
        running=True
        x=0
        self.proc.stdin.write('status 1 1 1  \n')
        for o in range(46):
            print self.proc.stdout.readline().rstrip('\n')
        while running==True:
            line=self.proc.stdout.readline().rstrip('\n')
            print line          
            if re.search('CCD Temp:',line):
                wx.CallAfter(self.ccdTemp.SetLabel,(line.split(':')[1]))
            time.sleep(.5)
            
    def initShutter(self):
        print 'Shutter Starting'
        
        try:
            self.stepper = Stepper()
        except RuntimeError as e:
            print("Runtime Exception: %s" % e.details)
            print("Exiting....")
            exit(1)

        self.stepper.openPhidget()
        self.stepper.waitForAttach(10000)


        print("|------------|----------------------------------|--------------|------------|")
        print("|- Attached -|-              Type              -|- Serial No. -|-  Version -|")
        print("|------------|----------------------------------|--------------|------------|")
        print("|- %8s -|- %30s -|- %10d -|- %8d -|" % (self.stepper.isAttached(), self.stepper.getDeviceName(), self.stepper.getSerialNum(), self.stepper.getDeviceVersion()))
        print("|------------|----------------------------------|--------------|------------|")
        print("Number of Motors: %i" % (self.stepper.getMotorCount()))
        
        print("Set the current position as start position...")
        self.stepper.setCurrentPosition(0, 0)
        time.sleep(1)
        
        print("Set the motor as engaged...")
        self.stepper.setEngaged(0, True)
        time.sleep(1)
        
        self.stepper.setAcceleration(0, 87543)
        self.stepper.setVelocityLimit(0, 6200)
        self.stepper.setCurrentLimit(0, 0.26)
        time.sleep(2)
        return

    def move(self,event):
        self.stepper.setTargetPosition(0,int(self.shutterText.GetValue()))
        return

    def moveFilter(self,pos):
        self.stepper.setTargetPosition(0,-800)
        return

    def moveCal(self,pos):
        self.stepper.setTargetPosition(0,0)
        return

class  PageTwo(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        
        self.dir=None
        self.comphome=os.getenv('HOME')
        if self.comphome == '/Users/jwhueh':
            self.debug=True
            self.dir='/Users/jwhueh/Scripts/FilterSpec/'
        else:
            self.debug=False
            self.dir='/opt/FilterSpec/'
        self.norm=[]
        self.currentFilter=None
        

        self.dpi = 70
        self.fig = Figure((13.0, 6.5), dpi=self.dpi)
        self.canvas = FigCanvas(self, -1, self.fig)

        self.toolbar2 = NavigationToolbar(self.canvas)

        x=75
        y=525
        self.fileLabel=wx.StaticText(self, pos=(x,y))
        self.fileLabel.SetLabel('Input File: ')
        x=x+75
        self.fileText=wx.TextCtrl(self,size=(200,-1), pos=(x,y))

        x=75
        y=y+30
        self.filterSizeText=wx.StaticText(self, pos=(x,y))
        self.filterSizeText.SetLabel('Filter Size:')

        x=x+75
        filt=['3x3','3x3narrow','2x2','2x2narrow']
        self.filterSize=wx.ComboBox(self,-1, pos=(x,y),choices=filt,style= wx.CB_READONLY)

        x=75
        y=y+30
        self.fitDegText=wx.StaticText(self, pos=(x,y))
        self.fitDegText.SetLabel('Degree of Fit:')

        x=x+100
        fitDeg=['2','3','4','5']
        self.fitDegCombo=wx.ComboBox(self,-1, pos=(x,y),choices=fitDeg,style= wx.CB_READONLY)

        x=75
        y=y+30
        self.lineSizeText=wx.StaticText(self, pos=(x,y))
        self.lineSizeText.SetLabel('Line File:')

        x=x+75
        self.lineText=wx.TextCtrl(self,size=(100,-1), pos=(x,y))
        
        y=y+30
        lines=['lines_short.dat','lines_673.dat','lines_665.dat','lines_489.dat','lines_475.dat']
        self.lineBox=wx.ComboBox(self,-1,choices=lines,pos=(x,y),style=wx.CB_READONLY)
        
        x=75
        y=y+30
        self.normButton = wx.Button(self, -1, "Calc Normalization", pos=(x,y))
        self.Bind(wx.EVT_BUTTON, self.normalizeFactor, self.normButton)

        y=y+30
        self.mapButton = wx.Button(self, -1, "Map Wavelengths", pos=(x,y))
        self.Bind(wx.EVT_BUTTON, self.waveMap, self.mapButton)


        self.fit=None
        self.flatSpec=None
        self.filterSpec=None
        self.darkSpec=None
        self.arcSpec=None
        self.w=[]

        self.init_pix=[]
        self.init_wavecal=[]
        self.lineActPos=[]
        
        

        self.initButton = wx.Button(self, -1, "Init")
        self.Bind(wx.EVT_BUTTON, self.init, self.initButton)

        self.graphButton = wx.Button(self, -1, "Graph Raw")
        self.Bind(wx.EVT_BUTTON, self.graph, self.graphButton)

        self.darkButton = wx.Button(self, -1, "Dark Sub")
        self.Bind(wx.EVT_BUTTON, self.darkSub, self.darkButton)

        self.norm2Button = wx.Button(self, -1, "Normalize")
        self.Bind(wx.EVT_BUTTON, self.normalize, self.norm2Button)

        self.waveButton = wx.Button(self, -1, "Find Wavelengths")
        self.Bind(wx.EVT_BUTTON, self.wave, self.waveButton)

        self.curveButton = wx.Button(self, -1, "Filter Curve")
        self.Bind(wx.EVT_BUTTON, self.makeCurve, self.curveButton)


        self.darkLabel=wx.StaticText(self)
        self.darkLabel.SetLabel('dark: ')
        self.darkText=wx.TextCtrl(self,size=(400,-1))
        
        self.arcLabel=wx.StaticText(self)
        self.arcLabel.SetLabel('arc: ')
        self.arcText=wx.TextCtrl(self,size=(400,-1))

        self.flatLabel=wx.StaticText(self)
        self.flatLabel.SetLabel('flat: ')
        self.flatText=wx.TextCtrl(self,size=(400,-1))

        self.filterLabel=wx.StaticText(self)
        self.filterLabel.SetLabel('object: ')
        self.filterText=wx.TextCtrl(self,size=(400,-1))

        self.fitLabel=wx.StaticText(self)
        self.fitLabel.SetLabel('fit: ')
        self.fitText=wx.TextCtrl(self,size=(400,-1))

        self.vbox=wx.BoxSizer(wx.VERTICAL)
        self.hbox1=wx.BoxSizer(wx.HORIZONTAL)
        self.gbox=wx.GridSizer(rows=5, cols=2, hgap=5, vgap=5)

        self.gbox.Add(self.darkLabel,0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.darkText,0, wx.ALIGN_LEFT)
        self.gbox.Add(self.arcLabel,0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.arcText,0, wx.ALIGN_LEFT)
        self.gbox.Add(self.flatLabel,0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.flatText,0, wx.ALIGN_LEFT)
        self.gbox.Add(self.filterLabel,0, wx.ALIGN_RIGHT)
        self.gbox.Add(self.filterText,0, wx.ALIGN_LEFT)
        self.gbox.Add(self.fitLabel,0,wx.ALIGN_RIGHT)
        self.gbox.Add(self.fitText,0,wx.ALIGN_LEFT)

        self.hbox1.Add(self.initButton,0,wx.ALIGN_CENTER)
        self.hbox1.Add(self.graphButton,0, wx.ALIGN_CENTER)
        self.hbox1.Add(self.darkButton,0, wx.ALIGN_CENTER)
        self.hbox1.Add(self.norm2Button,0,wx.ALIGN_CENTER)
        self.hbox1.Add(self.waveButton,0,wx.ALIGN_CENTER)
        self.hbox1.Add(self.curveButton,0,wx.ALIGN_CENTER)
        
        self.vbox.Add(self.canvas,0, wx.ALIGN_CENTER)
        self.vbox.Add(self.toolbar2,0, wx.ALIGN_CENTER)
        self.vbox.Add(self.hbox1,0, wx.ALIGN_CENTER)
        self.vbox.Add(self.gbox,0, wx.ALIGN_LEFT)

        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def init(self,event):
        arcImage=None
        darkImage=None
        flatImage=None
        filterImage=None
        x=0
        self.files=subprocess.Popen(['ls',self.dir],shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p=self.files.stdout.readlines()
        for f in p:
            if re.search(str(self.fileText.GetValue()), f):
                if re.search('arc',f):
                    arcImage=self.dir+f
                    self.arcText.SetValue(str(arcImage))
                    x=x+1
                if re.search('flat',f):
                    flatImage=self.dir+f
                    self.flatText.SetValue(str(flatImage))
                    x=x+1
                if re.search('object',f):
                    filterImage=self.dir+f
                    self.filterText.SetValue(str(filterImage))
                    x=x+1
                if re.search('dark',f):
                    darkImage=self.dir+f
                    self.darkText.SetValue(str(darkImage))
                    x=x+1

    def graph(self,event):  
        self.fig.clf()
        try:
            if self.darkText.GetValue()!='':
                self.graphDark(self.darkText.GetValue())     
        except:
            None
        try:
            if self.arcText.GetValue()!='':
                self.graphARC(self.arcText.GetValue(), 221)
        except:
            None
        try:
            if self.flatText.GetValue()!='':
                self.graphFlat(self.flatText.GetValue())
        except:
            None
        try:
            if self.filterText.GetValue()!='':
                self.graphFilter(self.filterText.GetValue())     
        except:
            None
        return

    def normalizeFactor(self,event):
        norm_factor=[]
        fold=self.dir+'norm_'+str(self.filterSize.GetValue())+'.dat'
        f=open(fold,'w')
        for i,m in enumerate(self.filterSpec):
            n=float(self.flatSpec[i])/float(m)
            norm_factor.append(n)
            f.write(str(n)+'\n')
        f.close()
        self.norm=norm_factor
        return norm_factor

    def normalize(self, event):
        y=[]
        leak=[]
        fold=self.dir+'norm_'+str(self.filterSize.GetValue())+'.dat'
        if os.path.exists(fold):
            f=open(fold,'r')
            for line in f.readlines():
                self.norm.append(line.rstrip('\n'))
            f.close()
        #f_in=open(dir+'leak_filter.dat','r')
        #for line in f_in:
        #    leak.append(line.rstrip('\n'))
        #f_in.close()
        if self.norm!=None:
            for i,f in enumerate(self.filterSpec):
                #leak_sub=(float(leak[i])-float(self.darkSpec[i]))
                #leak_sub=float(self.darkSpec[i])
                #y.append((f-leak_sub)*float(self.norm[i]))
                y.append((f)*float(self.norm[i]))
        self.ax2 = self.fig.add_subplot(222)
        self.ax2.clear()
        for xlabel_i in self.ax2.get_xticklabels():
            xlabel_i.set_fontsize(8) 
        for ylabel_i in self.ax2.get_yticklabels():
            ylabel_i.set_fontsize(8)
        self.ax2.set_ylabel('counts', size='x-small')
        self.ax2.set_xlabel('pixel', size='x-small')
        self.ax2.set_title('Filter Flat', size='x-small')
        self.ax2.plot(self.w, y,'k')
        self.canvas.draw()
        self.filterSpec=y
        return


    def darkSub(self,event):
        tmp=[]
        for i,f in enumerate(self.filterSpec):
            tmp.append(f-self.darkSpec[i])
        self.filterSpec=tmp
        tmp=[]
        for i,fl in enumerate(self.flatSpec):
            tmp.append(fl-self.darkSpec[i])
        self.flatSpec=tmp
        tmp=[]
        self.ax2 = self.fig.add_subplot(222)
        self.ax2.clear()
        for xlabel_i in self.ax2.get_xticklabels():
            xlabel_i.set_fontsize(8) 
        for ylabel_i in self.ax2.get_yticklabels():
            ylabel_i.set_fontsize(8)
        self.ax2.set_ylabel('counts', size='x-small')
        self.ax2.set_xlabel('pixel', size='x-small')
        self.ax2.set_title('Filter Flat', size='x-small')
        self.ax2.plot(self.w, self.filterSpec,'k')

        self.ax3 = self.fig.add_subplot(223)
        self.ax3.clear()
        for xlabel_i in self.ax3.get_xticklabels():
            xlabel_i.set_fontsize(8) 
        for ylabel_i in self.ax3.get_yticklabels():
            ylabel_i.set_fontsize(8) 
        self.ax3.set_ylabel('counts', size='x-small')
        self.ax3.set_xlabel('pixel', size='x-small')
        self.ax3.set_title('Calibration Flat', size='x-small')
        self.ax3.plot(self.w, self.flatSpec,'k')
        self.canvas.draw()
        
        return
        
    def graphARC(self, image, sub):
        y=[]
        y_mod=[]
        im=pyfits.getdata(str(image))
        self.ax1 = self.fig.add_subplot(sub)
        self.ax1.clear()
        if re.search('narrow',str(image)):
            trans=zip(*im[1:1024])
            wave=range(len(trans[1023]))
            row=im[1:1024]
        else:
            trans=zip(*im[1:4800])
            wave=range(len(trans[1023]))
            row=im[1:4800]
        for t in row:
            y.append(sum(t[500:525])/25)
        min=np.min(y)
        for m in y:
            y_mod.append(m-min)
        self.arcSpec=y_mod
        for xlabel_i in self.ax1.get_xticklabels():
            xlabel_i.set_fontsize(8) 
        for ylabel_i in self.ax1.get_yticklabels():
            ylabel_i.set_fontsize(8)
        self.ax1.set_ylabel('counts', size='x-small')
        self.ax1.set_xlabel('pixel', size='x-small')
        self.ax1.set_title('Hg(Ne) Calibration ARC', size='x-small')
        self.ax1.plot(wave, y_mod,'k')
        self.canvas.draw()
        return

    def graphFilter(self, image):
        y=[]
        im=pyfits.getdata(str(image))
        self.ax2 = self.fig.add_subplot(222)
        self.ax2.clear()
        if re.search('narrow',str(image)):
            trans=zip(*im[1:1024])
            wave=range(len(trans[1023]))
            row=im[1:1024]
        else: 
            trans=zip(*im[1:4800])
            wave=range(len(trans[1023]))
            row=im[1:4800]
        self.w=wave
        for t in row:
            y.append(sum(t[450:610])/161)
        self.ax2.clear()
        for xlabel_i in self.ax2.get_xticklabels():
            xlabel_i.set_fontsize(8) 
        for ylabel_i in self.ax2.get_yticklabels():
            ylabel_i.set_fontsize(8)
        self.ax2.set_ylabel('counts', size='x-small')
        self.ax2.set_xlabel('pixel', size='x-small')
        self.ax2.set_title('Filter Flat', size='x-small')
        self.ax2.plot(wave, y,'k')
        self.canvas.draw()
        self.filterSpec=y
        return

    def graphFlat(self, image):
        y=[]
        im=pyfits.getdata(str(image))
        self.ax3 = self.fig.add_subplot(223)
        self.ax3.clear()
        if re.search('narrow',str(image)):
            trans=zip(*im[1:1024])
            wave=range(len(trans[1023]))
            row=im[1:1024]
        else:
            trans=zip(*im[1:4800])
            wave=range(len(trans[1023]))
            row=im[1:4800]
        for t in row:
            y.append(sum(t[450:610])/161)
        self.ax3.clear()
        for xlabel_i in self.ax3.get_xticklabels():
            xlabel_i.set_fontsize(8) 
        for ylabel_i in self.ax3.get_yticklabels():
            ylabel_i.set_fontsize(8) 
        self.ax3.set_ylabel('counts', size='x-small')
        self.ax3.set_xlabel('pixel', size='x-small')
        self.ax3.set_title('Calibration Flat', size='x-small')
        self.ax3.plot(wave, y,'k')
        self.canvas.draw()
        self.flatSpec=y
        return

    def graphDark(self, image):
        y=[]
        im=pyfits.getdata(str(image))
        self.ax4 = self.fig.add_subplot(224)
        self.ax4.clear()
        if re.search('narrow',str(image)):
            trans=zip(*im[1:1024])
            wave=range(len(trans[1023]))
            row=im[1:1024]
            r=512
        else:
            trans=zip(*im[1:4800])
            wave=range(len(trans[1023]))
            row=im[1:4800]
            r=1800
        for t in row:
            y.append(sum(t[450:610])/161)
        for xlabel_i in self.ax4.get_xticklabels():
            xlabel_i.set_fontsize(8) 
        for ylabel_i in self.ax4.get_yticklabels():
            ylabel_i.set_fontsize(8)  
        self.ax4.set_ylabel('counts', size='x-small')
        self.ax4.set_xlabel('pixel', size='x-small')
        self.ax4.set_title('Calibration Dark', size='x-small')
        self.ax4.plot(wave, y,'k')
        self.canvas.draw()
        self.darkSpec=y
        return

    def waveMap(self,event):
        filter=self.filterSize.GetValue()
        prev=0
        linePos=[]
        lineCorPos=[]
        lineMax=[]
        lineCorMax=[]
        lineActDiff=[]
        lineTheDiff=[]
        wavecal=[]
        pix=[]
        lines=[]
        wl=[]
        self.fig.clf()
        self.graphARC(self.arcText.GetValue(),111)
        for index,pixel in enumerate(self.arcSpec):             
            if pixel > prev:
                prev=pixel
            else:
                if pixel>500:
                    linePos.append(index)
                    lineMax.append(prev)
                    max=index
                    prev=0
        for i,p in enumerate(linePos):     
                try:
                    if abs(linePos[i+1]-p) <10:
                        linePos.pop(i+1)
                        lineMax.pop(i+1)
                    if abs(linePos[i+2]-p) <20:
                        linePos.pop(i+2)
                        lineMax.pop(i+2)
                except:
                    print 'error'
        for i,l in enumerate(linePos):
            m=self.fwhm(self.arcSpec, l)
            lineCorPos.append(m[0])
            lineCorMax.append(m[1])
        linePos=[]
        lineMax   
        for i,l in enumerate(lineCorPos):
            try:
                c=lineCorPos.count(l)
                for i in range(c-1):
                    ind=lineCorPos.index(l)
                    lineCorPos.pop(ind)
                    lineCorMax.pop(ind)
            except:
                None
                 
        print 'linePos:', lineCorPos
        for i,l in enumerate(lineCorPos):
            self.ax1.vlines(l,lineCorMax[i]+1000,lineCorMax[i]+5000,'r', linewidth=2)
            
        self.canvas.draw()
        self.lineActPos=lineCorPos
        return

    def wave(self,event):
        pix=[]
        wavecal=[]
        lineFile=None
        if self.lineText.GetValue()=='':
            lineFile=self.lineBox.GetValue()
        else:
            lineFile=self.lineText.GetValue()
        f=open(lineFile,'r')
        for line in f.readlines():
            l=line.split()
            self.init_wavecal.append(float(l[0]))
            self.init_pix.append(float(l[1]))
            print l[0], l[1]
        f.close()

        for i,p in enumerate(self.init_pix):
            for f in self.lineActPos:
                if abs(p-f) < 20:
                    pix.append(f)
                    wavecal.append(self.init_wavecal[i])
 
        x=np.arange(len(self.arcSpec))
        if self.fitDegCombo.GetValue()=='2':
            z=polyfit(pix,wavecal,1)
            print z
            w=(z[0]*x)+(z[1])
        elif self.fitDegCombo.GetValue()=='3':
            z=polyfit(pix,wavecal,2)
            print z
            w=(z[0]*x*x)+(z[1]*x)+(z[2])
        elif self.fitDegCombo.GetValue()=='4':
            z=polyfit(pix,wavecal,3)
            print z
            w=(z[0]*x*x*x)+(z[1]*x*x)+(z[2]*x)+z[3]
        elif self.fitDegCombo.GetValue()=='5':
            z=polyfit(pix,wavecal,4)
            print z
            w=(z[0]*x*x*x*x)+(z[1]*x*x*x)+(z[2]*x*x) +(z[3]*x)+z[4]
  
        self.fit=w
        self.fitText.SetValue('%sp^3 %sp^2 %sp %s' % (str(z[0]), str(z[1]),str(0),str(0)))
        self.fig.clf()
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.clear()
        for xlabel_i in self.ax1.get_xticklabels():
            xlabel_i.set_fontsize(10) 
        for ylabel_i in self.ax1.get_yticklabels():
            ylabel_i.set_fontsize(10)

        self.ax1.set_ylabel('counts', size='small')
        self.ax1.set_xlabel('wavelength (nm)', size='small')
        self.ax1.set_title('Hg(Ne) Calibration ARC', size='small')
        self.ax1.plot(w, self.arcSpec,'k')
        self.canvas.draw()
        return

    def fwhm(self,arr, mp):
        max_pixel=int(mp)
        max_ind=arr.index(np.amax(arr[max_pixel-25:max_pixel+25]))
        max=np.amax(arr[max_pixel-25:max_pixel+25])
        return [max_ind, max]

    def makeCurve(self,event):
        diff_arr=[]
        #print len(self.filterSpec), len(self.flatSpec)
        for a in range(len(self.filterSpec)):
            try:
                diff_arr.append(float(self.filterSpec[a])/float(self.flatSpec[a]))
            except:
                diff_arr.append(float(0))
 
        self.fig.clf()
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.clear()
        for xlabel_i in self.ax1.get_xticklabels():
            xlabel_i.set_fontsize(10) 
        for ylabel_i in self.ax1.get_yticklabels():
            ylabel_i.set_fontsize(10)

        self.ax1.set_ylabel('counts', size='small')
        self.ax1.set_xlabel('wavelength (nm)', size='small')
        self.ax1.set_title('Differential Filter Curve', size='small')
        self.ax1.plot(self.fit, diff_arr,'k')
        self.ax1.set_ylim(0,1)
        self.canvas.draw()
        f_out=open(self.dir+str(self.fileText.GetValue())+'.txt','w')
        for i,d in enumerate(diff_arr):
            f_out.write(str(self.fit[i])+'    '+str(d)+'\n')
        f_out.close()
        return

class FilterSpect(wx.Frame):
    title='Filter Spectrum'
    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title,size=(800,350))

        currentImage=None
        
        p=wx.Panel(self)
        nb=wx.Notebook(p)
        page1=PageOne(nb)
        page2=PageTwo(nb)

        nb.AddPage(page1,"Imaging")
        self.pageo=nb.GetPage(0)

        nb.AddPage(page2,"Reduction")
        self.paget=nb.GetPage(1)

        self.createMenu()

        sizer=wx.BoxSizer()
        sizer.Add(nb,1,wx.EXPAND)
        p.SetSizer(sizer)
        p.Layout()

    def createMenu(self):
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)   
        
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def on_exit(self, event):
        if self.pageo.ser !=None:
            self.pageo.ser.close()
        try:
            self.pageo.proc.stdin.write('exit 1 1 1\n')
        except:
            None
        self.Destroy()
 

if __name__=="__main__":
  app = wx.PySimpleApp()
  app.frame = FilterSpect()
  app.frame.Show()
  app.MainLoop()


