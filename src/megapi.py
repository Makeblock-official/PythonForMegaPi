import serial
import sys,time,math,random
import signal
from time import ctime,sleep
import glob,struct
from multiprocessing import Process,Manager,Array
import threading

class mSerial():
    ser = None
    def __init__(self):
        print self

    def start(self, port='/dev/ttyAMA0'):
        self.ser = serial.Serial(port,115200,timeout=10)

    def device(self):
        return self.ser

    def serialPorts(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        result = []
        for port in ports:
            s = serial.Serial()
            s.port = port
            s.close()
            result.append(port)
        return result

    def writePackage(self,package):
        self.ser.write(package)
        sleep(0.01)

    def read(self):
        return self.ser.read()

    def isOpen(self):
        return self.ser.isOpen()

    def inWaiting(self):
        return self.ser.inWaiting()

    def close(self):
        self.ser.close()
M1 = 9
M2 = 10
A0 = 14
A1 = 15
A2 = 16
A3 = 17
A4 = 18
A6 = 19
A7 = 20
A8 = 21
A9 = 22
A10 = 23
A11 = 24

class MegaPi():
    def __init__(self):
        print "init MegaPi"
        signal.signal(signal.SIGINT, self.exit)
        self.manager = Manager()
        self.__selectors = self.manager.dict()
        self.buffer = []
        self.bufferIndex = 0
        self.isParseStart = False
        self.exiting = False
        self.isParseStartIndex = 0

    def __del__(self):
        self.exiting = True

    def start(self,port='/dev/ttyAMA0'):
        self.device = mSerial()
        self.device.start(port)
        sys.excepthook = self.excepthook
        th = threading.Thread(target=self.__onRead,args=(self.onParse,))
        th.start()

    def excepthook(self, exctype, value, traceback):
        self.close()

    def close(self):
        self.device.close()

    def exit(self, signal, frame):
        self.exiting = True
        sys.exit(0)

    def __onRead(self,callback):
        while True:
            if(self.exiting==True):
                break
            try:	
                if self.device.isOpen()==True:
                    n = self.device.inWaiting()
                    for i in range(n):
                        r = ord(self.device.read())
                        callback(r)
                    sleep(0.01)
                else:	
                    sleep(0.5)
            except Exception,ex:
                print str(ex)
                self.close()
                sleep(1)
    def __writePackage(self,pack):
        self.device.writePackage(pack)

    def __writeRequestPackage(self,deviceId,port,callback):
        extId = ((port<<4)+deviceId)&0xff
        self.__doCallback(extId,callback)
        self.__writePackage(bytearray([0xff,0x55,0x4,extId,0x1,deviceId,port]))

    def digitalRead(self,pin,callback):
        self.__writeRequestPackage(0x1e,pin,callback)

    def analogRead(self,pin,callback):
        self.__writeRequestPackage(0x1f,pin,callback)	

    def lightSensorRead(self,port,callback):
        self.__writeRequestPackage(4,port,callback)

    def ultrasonicSensorRead(self,port,callback):
        self.__writeRequestPackage(1,port,callback)

    def lineFollowerRead(self,port,callback):
        self.__writeRequestPackage(17,port,callback)

    def soundSensorRead(self,port,callback):
        self.__writeRequestPackage(7,port,callback)

    def pirMotionSensorRead(self,port,callback):
        self.__writeRequestPackage(15,port,callback)

    def potentiometerRead(self,port,callback):
        self.__writeRequestPackage(4,port,callback)

    def limitSwitchRead(self,port,callback):
        self.__writeRequestPackage(21,port,callback)

    def temperatureRead(self,port,callback):
        self.__writeRequestPackage(2,port,callback)

    def touchSensorRead(self,port,callback):
        self.__writeRequestPackage(15,port,callback)

    def humitureSensorRead(self,port,type,callback):
        deviceId = 23;
        extId = ((port<<4)+deviceId)&0xff
        self.__doCallback(extId,callback)
        self.__writePackage(bytearray([0xff,0x55,0x5,extId,0x1,deviceId,port,type]))

    def joystickRead(self,port,axis,callback):
        deviceId = 5;
        extId = (((port+axis)<<4)+deviceId)&0xff
        self.__doCallback(extId,callback)
        self.__writePackage(bytearray([0xff,0x55,0x5,extId,0x1,deviceId,port,axis]))

    def gasSensorRead(self,port,callback):
        self.__writeRequestPackage(25,port,callback)

    def flameSensorRead(self,port,callback):
        self.__writeRequestPackage(24,port,callback)

    def compassRead(self,port,callback):
        self.__writeRequestPackage(26,port,callback)

    def angularSensorRead(self,port,slot,callback):
        self.__writeRequestPackage(28,port,callback)

    def buttonRead(self,port,callback):
        self.__writeRequestPackage(22,port,callback)

    def gyroRead(self,axis,callback):
        self.__writeRequestPackage(6,axis,callback)

    def pressureSensorBegin(self):
        self.__writePackage(bytearray([0xff,0x55,0x3,0x0,0x2,29]))
		
    def pressureSensorRead(self,type,callback):
        self.__writeRequestPackage(29,type,callback)

    def digitalWrite(self,pin,level):
        self.__writePackage(bytearray([0xff,0x55,0x5,0x0,0x2,0x1e,pin,level]))

    def pwmWrite(self,pin,pwm):
        self.__writePackage(bytearray([0xff,0x55,0x5,0x0,0x2,0x20,pin,pwm]))

    def motorRun(self,port,speed):
        self.__writePackage(bytearray([0xff,0x55,0x6,0x0,0x2,0xa,port]+self.short2bytes(speed)))

    def motorMove(self,leftSpeed,rightSpeed):
        self.__writePackage(bytearray([0xff,0x55,0x7,0x0,0x2,0x5]+self.short2bytes(-leftSpeed)+self.short2bytes(rightSpeed)))

    def servoRun(self,port,slot,angle):
        self.__writePackage(bytearray([0xff,0x55,0x6,0x0,0x2,0xb,port,slot,angle]))

    def encoderMotorRun(self,slot,speed):
        deviceId = 61;
        self.__writePackage(bytearray([0xff,0x55,0x8,0,0x2,deviceId,0,slot,1]+self.short2bytes(speed)))

    def encoderMotorMove(self,slot,speed,distance,callback):
        deviceId = 61;
        extId = ((slot<<4)+deviceId)&0xff
        self.__doCallback(extId,callback)
        self.__writePackage(bytearray([0xff,0x55,12,extId,0x2,deviceId,0,slot,2]+self.short2bytes(speed)+self.long2bytes(distance)))

    def encoderMotorMoveTo(self,slot,speed,position,callback):
        deviceId = 61;
        extId = ((slot<<4)+deviceId)&0xff
        self.__doCallback(extId,callback)
        self.__writePackage(bytearray([0xff,0x55,12,extId,0x2,deviceId,0,slot,3]+self.short2bytes(speed)+self.long2bytes(position)))


    def encoderMotorPosition(self,slot,callback):
        self.__writeRequestPackage(61,slot,1,callback)

    def encoderMotorSpeed(self,slot,callback):
        self.__writeRequestPackage(61,slot,2,callback)

    def stepperMotorRun(self,port,speed):
        self.__writePackage(bytearray([0xff,0x55,0x7,0,0x2,62,port,0x1]+self.short2bytes(speed)))

    def stepperMotorMove(self,port,distance):
        deviceId = 62;
        extId = ((slot<<4)+deviceId)&0xff
        self.__doCallback(extId,callback)
        self.__writePackage(bytearray([0xff,0x55,11,extId,0x2,deviceId,port,2]+self.short2bytes(speed)+self.long2bytes(distance)))

    def stepperMotorMoveTo(self,port,position):
        deviceId = 62;
        extId = ((slot<<4)+deviceId)&0xff
        self.__doCallback(extId,callback)
        self.__writePackage(bytearray([0xff,0x55,11,extId,0x2,deviceId,port,3]+self.short2bytes(speed)+self.long2bytes(position)))

    def rgbledDisplay(self,port,slot,index,red,green,blue):
        self.__writePackage(bytearray([0xff,0x55,0x9,0x0,0x2,18,port,slot,index,int(red),int(green),int(blue)]))

    def rgbledShow(self,port,slot):
        self.__writePackage(bytearray([0xff,0x55,0x5,0x0,0x2,19,port,slot]))

    def sevenSegmentDisplay(self,port,value):
        self.__writePackage(bytearray([0xff,0x55,0x8,0x0,0x2,9,port]+self.float2bytes(value)))

    def ledMatrixMessage(self,port,x,y,message):
        arr = list(message);
        for i in range(len(arr)):
            arr[i] = ord(arr[i]);
        self.__writePackage(bytearray([0xff,0x55,8+len(arr),0,0x2,41,port,1,self.char2byte(x),self.char2byte(7-y),len(arr)]+arr))
		
    def ledMatrixDisplay(self,port,x,y,buffer):
        self.__writePackage(bytearray([0xff,0x55,7+len(buffer),0,0x2,41,port,2,x,7-y]+buffer))

    def shutterOn(self,port):
        self.__writePackage(bytearray([0xff,0x55,0x5,0,0x3,20,port,1]))

    def shutterOff(self,port):
        self.__writePackage(bytearray([0xff,0x55,0x5,0,0x3,20,port,2]))

    def focusOn(self,port):
        self.__writePackage(bytearray([0xff,0x55,0x5,0,0x3,20,port,3]))

    def focusOff(self,port):
        self.__writePackage(bytearray([0xff,0x55,0x5,0,0x3,20,port,4]))

    def onParse(self, byte):
        position = 0
        value = 0	
        self.buffer+=[byte]
        bufferLength = len(self.buffer)
        if bufferLength >= 2:
            if (self.buffer[bufferLength-1]==0x55 and self.buffer[bufferLength-2]==0xff):
                self.isParseStart = True
                self.isParseStartIndex = bufferLength-2	
            if (self.buffer[bufferLength-1]==0xa and self.buffer[bufferLength-2]==0xd and self.isParseStart==True):			
                self.isParseStart = False
                position = self.isParseStartIndex+2
                extID = self.buffer[position]
                position+=1
                type = self.buffer[position]
                position+=1
                # 1 byte 2 float 3 short 4 len+string 5 double
                if type == 1:
                    value = self.buffer[position]
                if type == 2:
                    value = self.readFloat(position)
                if(value<-512 or value>1023):
                    value = 0
                if type == 3:
                    value = self.readShort(position)
                if type == 4:
                    value = self.readString(position)
                if type == 5:
                    value = self.readDouble(position)
                if type == 6:
                    value = self.readLong(position)
                if(type<=6):
                    self.responseValue(extID,value)
                self.buffer = []

    def readFloat(self, position):
        v = [self.buffer[position], self.buffer[position+1],self.buffer[position+2],self.buffer[position+3]]
        return struct.unpack('<f', struct.pack('4B', *v))[0]
    def readShort(self, position):
        v = [self.buffer[position], self.buffer[position+1]]
        return struct.unpack('<h', struct.pack('2B', *v))[0]
    def readString(self, position):
        l = self.buffer[position]
        position+=1
        s = ""
        for i in Range(l):
            s += self.buffer[position+i].charAt(0)
        return s
    def readDouble(self, position):
        v = [self.buffer[position], self.buffer[position+1],self.buffer[position+2],self.buffer[position+3]]
        return struct.unpack('<f', struct.pack('4B', *v))[0]

    def readLong(self, position):
        v = [self.buffer[position], self.buffer[position+1],self.buffer[position+2],self.buffer[position+3]]
        return struct.unpack('<l', struct.pack('4B', *v))[0]

    def responseValue(self, extID, value):
        self.__selectors["callback_"+str(extID)](value)

    def __doCallback(self, extID, callback):
        self.__selectors["callback_"+str(extID)] = callback

    def float2bytes(self,fval):
        val = struct.pack("f",fval)
        return [ord(val[0]),ord(val[1]),ord(val[2]),ord(val[3])]

    def long2bytes(self,lval):
        val = struct.pack("=l",lval)
        return [ord(val[0]),ord(val[1]),ord(val[2]),ord(val[3])]

    def short2bytes(self,sval):
        val = struct.pack("h",sval)
        return [ord(val[0]),ord(val[1])]
    def char2byte(self,cval):
        val = struct.pack("b",cval)
        return ord(val[0])
