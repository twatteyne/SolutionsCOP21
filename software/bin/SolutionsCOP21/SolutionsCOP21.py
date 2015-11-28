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
import traceback
import bottle
import json
import copy
import requests

from SmartMeshSDK                      import HrParser,                   \
                                              sdk_version,                \
                                              FormatUtils
from SmartMeshSDK.ApiException         import APIError
from SmartMeshSDK.IpMgrConnectorSerial import IpMgrConnectorSerial
from SmartMeshSDK.IpMgrConnectorMux    import IpMgrSubscribe
from SmartMeshSDK.protocols.oap        import OAPDispatcher,              \
                                              OAPClient,                  \
                                              OAPMessage,                 \
                                              OAPNotif

#============================ helpers =========================================

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

class AppData(object):
    _instance = None
    _init     = False
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppData,cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def __init__(self):
        if self._init:
            return
        self._init      = True
        self.dataLock   = threading.RLock()
        self.data       = {
            'connector':   None,
            'idToMac':     {},
            'temperature': {},
            'paths':       {},
        }
    def setConnector(self,connector):
        with self.dataLock:
            self.data['connector']          = connector
    def getConnector(self):
        with self.dataLock:
            return self.data['connector']
    def setIdToMac(self,idToMac):
        with self.dataLock:
            self.data['idToMac']            = idToMac
    def getMacFromId(self,id):
        with self.dataLock:
            return self.data['idToMac'][id]
    def setTemperature(self,mac,temperature):
        with self.dataLock:
            self.data['temperature'][mac]   = [temperature,time.time()]
    def setPaths(self,paths):
        with self.dataLock:
            self.data['paths']     = paths
    def get(self):
        with self.dataLock:
            return {
                'temperature': copy.deepcopy(self.data['temperature']),
                'paths':       copy.deepcopy(self.data['paths']),
            }

class Receiver(threading.Thread):
    
    def __init__(self,serialPort,simulation=False):
        
        # store params
        self.serialPort         = serialPort
        self.simulation      = simulation
        
        # local variables
        self.dataLock        = threading.RLock(0)
        self.goOn            = True
        self.hrParser        = HrParser.HrParser()
        self.reconnectEvent  = threading.Event()
        
        # initialize thread
        threading.Thread.__init__(self)
        self.name            = 'Receiver'
        self.start()
    
    def run(self):
        
        while self.goOn:
            
            try:
                print 'Connecting to {0}...'.format(self.serialPort),
                self.connector    = IpMgrConnectorSerial.IpMgrConnectorSerial()
                self.connector.connect({'port': self.serialPort})
                subscriber   = IpMgrSubscribe.IpMgrSubscribe(self.connector)
                subscriber.start()
                subscriber.subscribe(
                    notifTypes =    [
                                        IpMgrSubscribe.IpMgrSubscribe.ERROR,
                                        IpMgrSubscribe.IpMgrSubscribe.FINISH,
                                    ],
                    fun =           self._handle_ErrorFinish,
                    isRlbl =        True,
                )
                subscriber.subscribe(
                    notifTypes    = [
                                        IpMgrSubscribe.IpMgrSubscribe.NOTIFDATA,
                                    ],
                    fun =           self._handle_data,
                    isRlbl =        False,
                )
                self.oap_dispatch = OAPDispatcher.OAPDispatcher()
                self.oap_dispatch.register_notif_handler(self._handle_oap)
                AppData().setConnector(self.connector)
            except Exception as err:
                print 'FAIL:'
                print err
                time.sleep(1)
            else:
                print 'PASS.'
                self.reconnectEvent.clear()
                self.reconnectEvent.wait()
            finally:
                try:
                    self.connector.disconnect()
                except:
                    pass
    
    #======================== public
    
    def close(self):
        try:
            self.connector.disconnect()
        except:
            pass
    
    #======================== private
    
    def _handle_ErrorFinish(self,notifName,notifParams):
        try:
            assert notifName in [
                IpMgrSubscribe.IpMgrSubscribe.ERROR,
                IpMgrSubscribe.IpMgrSubscribe.FINISH,
            ]
            if not self.reconnectEvent.isSet():
                self.reconnectEvent.set()
        except Exception as err:
            logCrash(self.name,err)
    
    def _handle_data(self,notifName, notifParams):
        
        try:
            assert notifName=='notifData'
            self.oap_dispatch.dispatch_pkt(notifName, notifParams)
        except Exception as err:
            criticalError(err)
    
    def _handle_oap(self,mac,notif):
        try:
            if not isinstance(notif,OAPNotif.OAPTempSample):
                return
            mac  = FormatUtils.formatMacString(mac)
            temp = float(notif.samples[0])/100.0
            AppData().setTemperature(mac,temp)
        except Exception as err:
            criticalError(err)

class Snapshot(threading.Thread):
    
    SNAPSHOT_PERIOD    = 60 # seconds
    
    def __init__(self):
        
        # record params
        
        # initialize thread
        threading.Thread.__init__(self)
        self.name  = 'SnapShot'
        self.start()
    
    def run(self):
        try:
            delay = 0
            while True:
                time.sleep(1)
                if delay==0:
                    self._doSnapshot()
                    delay = self.SNAPSHOT_PERIOD
                delay -= 1;
        except Exception as err:
            criticalError(err)
    
    def _doSnapshot(self):
        try:
            idToMac          = {}
            macs             = []
            connector        = AppData().getConnector()
            currentMac       = (0,0,0,0,0,0,0,0)
            continueAsking   = True
            while continueAsking:
                try:
                    res = connector.dn_getMoteConfig(currentMac,True)
                except APIError:
                    continueAsking = False
                else:
                    idToMac[res.moteId] = FormatUtils.formatMacString(res.macAddress)
                    currentMac    = res.macAddress
                    macs         += [currentMac]
            AppData().setIdToMac(idToMac)
            paths = []
            for mac in macs:
                currentPathId  = 0
                continueAsking = True
                while continueAsking:
                    try:
                        res = connector.dn_getNextPathInfo(mac,0,currentPathId)
                    except APIError:
                        continueAsking = False
                    else:
                        currentPathId  = res.pathId
                        paths += [
                            (
                                FormatUtils.formatMacString(res.source),
                                FormatUtils.formatMacString(res.dest),
                            )
                        ]
            AppData().setPaths(paths)
        except Exception as err:
            print "snapshort FAILED:"
            print err

class Xively(threading.Thread):
    
    SYNC_PERIOD    = 10 # seconds
    
    def __init__(self):
        
        # record params
        
        # initialize thread
        threading.Thread.__init__(self)
        self.name  = 'Xively'
        self.start()
    
    def run(self):
        try:
            delay = 0
            while True:
                time.sleep(1)
                if delay==0:
                    self._syncToXively()
                    delay = self.SYNC_PERIOD
                delay -= 1;
        except Exception as err:
            criticalError(err)
    
    def _syncToXively(self):
        try:
            rawData          = AppData().get()
            xivelyData       = []
            for (m,[t,ts]) in rawData['temperature'].items():
                xivelyData  += ['{0}:{1}'.format(m,t)]
            xivelyData       = "_".join(xivelyData)
            print xivelyData
            r = requests.put(
                "https://api.xively.com/v2/feeds/918651241",
                headers = {
                    "Host":                  "api.xively.com",
                    "X-ApiKey":              "VALDxWNsi0roJQNtrFmCB3mBRBNgqeOAMlag1VcvkAd7peKp"
                },
                json = {
                    "version":               "1.0.0",
                    "datastreams": [
                        {
                            "id":            "temp",
                            "current_value": xivelyData,
                        },
                    ]
                },
            )
        except Exception as err:
            print "syncing to Xively FAILED:"
            print err
        else:
            print "Xively response: {0}".format(r.status_code)

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
            AppData().get()
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
    snapshot       = Snapshot()
    xilvey         = Xively()
    web            = WebInterface(receiver)
    
    raw_input("Press any key to stop.")
    
    receiver.close()
    web.close()
    
    sys.exit(0)

if __name__=="__main__":
    main()
