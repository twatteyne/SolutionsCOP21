#!/usr/bin/python

#============================ adjust path =====================================

import sys
import os
if __name__ == "__main__":
    here = sys.path[0]
    sys.path.insert(0, os.path.join(here, '..', '..'))

#============================ imports =========================================

import sys
import time
import threading
import struct
import math
import traceback
import Tkinter
import winsound
import bottle
import json
import random
import requests

from SmartMeshSDK                       import sdk_version
from SmartMeshSDK.IpMgrConnectorSerial  import IpMgrConnectorSerial
from SmartMeshSDK.IpMgrConnectorMux     import IpMgrSubscribe

#============================ helpers =========================================

def radToDeg(rad):
    return rad*57.3

def degToRad(rad):
    return rad/57.3

def printDebug(stringToPrint):
    #print stringToPrint
    pass

def currentUtcTime():
    return time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime())

def logCrash(threadName,err):
    output  = []
    output += ["==============================================================="]
    output += [currentUtcTime()]
    output += [""]
    output += ["CRASH in Thread {0}!".format(threadName)]
    output += [""]
    output += ["=== exception type ==="]
    output += [str(type(err))]
    output += [""]
    output += ["=== traceback ==="]
    output += [traceback.format_exc()]
    output  = '\n'.join(output)
    print output

def criticalError(err):
    traceback.print_exc()
    print 'Script ended with an error.'
    time.sleep(1)
    sys.exit(-1)

#============================ classes =========================================

class Receiver(object):
    
    def __init__(self,comPort,simulation=False):
        
        # store params
        self.comPort    = comPort
        self.simulation = simulation
        
        # local variables
        self.dataLock   = threading.RLock(0)
        if not self.simulation:
            self.connector  = IpMgrConnectorSerial.IpMgrConnectorSerial()
            self.connector.connect({'port': self.comPort})
            self.subscriber = IpMgrSubscribe.IpMgrSubscribe(self.connector)
            self.subscriber.start()
            self.subscriber.subscribe(
                notifTypes  =   [
                                    IpMgrSubscribe.IpMgrSubscribe.NOTIFDATA,
                                ],
                fun =           self._handle_data,
                isRlbl =        False,
            )
    
    #======================== public
    
    def close(self):
        self.connector.disconnect()
    
    #======================== private
    
    def _handle_data(self,notifName, notifParams):
        
        try:
            assert notifName=='notifData'
            
            print "TODO _handle_data"
            print notifParams
        
        except Exception as err:
            criticalError(err)

class Snapshot(threading.Thread):
    
    SNAPSHOT_PERIOD    = 5 # seconds
    
    def __init__(self,receiver):
        
        # record params
        self.receiver = receiver
        
        # initialize the parent class
        threading.Thread.__init__(self)
        
        # start myself
        self.start()
    
    def run(self):
        
        try:
            
            delay = 0
            
            while True:
                # wait before getting data
                time.sleep(1)
                
                if delay==0:
                    self._doSnapshot()
                    delay = SNAPSHOT_PERIOD
                
                delay -= 1;
        
        except Exception as err:
            criticalError(err)
    
    def _doSnapshot(self):
        print "TODO _doSnapshot"
    
class WebInterface(threading.Thread):
    
    def __init__(self,receiver):
        
        # store params
        self.receiver   = receiver
        
        # initialize web server
        self.web        = bottle.Bottle()
        self.web.route(path='/data.json',        method='GET', callback=self._cb_data_GET)
        self.web.route(path='/',                 method='GET', callback=self._cb_root_GET)
        self.web.route(path='/<filename>',       method='GET', callback=self._cb_static_GET)
        
        # start the thread
        threading.Thread.__init__(self)
        self.name       = 'WebInterface'
        self.daemon     = True
        self.start()
    
    def run(self):
        try:
            # wait for banner
            time.sleep(0.5)
            
            self.web.run(
                host   = 'localhost',
                port   = 8080,
                quiet  = True,
                debug  = False,
            )
        except Exception as err:
            logCrash(self.name,err)
    
    #======================== public ==========================================
    
    def close(self):
        # bottle thread is daemon, it will close when main thread closes
        pass
    
    #======================== private ==========================================
    
    def _cb_data_GET(self):
        return json.dumps(
            {
                'poipoi':    True,
            }
        )
        
    def _cb_root_GET(self):
        return bottle.static_file('index.html',root='static/.')
    
    def _cb_static_GET(self,filename):
        return bottle.static_file(filename,root='static/.')

#============================ main ============================================

def main():
    print 'SolutionsCOP21 application'
    print 'SmartMesh SDK {0}\n'.format('.'.join([str(b) for b in sdk_version.VERSION]))
    
    receiver       = Receiver('COM9',simulation=False)
    snapshot       = Snapshot(receiver)
    web            = WebInterface(receiver)
    
    raw_input("Press any key to stop.")
    
    receiver.close()
    web.close()
    
    sys.exit(0)

if __name__=="__main__":
    main()
