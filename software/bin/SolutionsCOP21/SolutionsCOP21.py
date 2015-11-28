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

from SmartMeshSDK                      import HrParser,                   \
                                              sdk_version
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
            'temperature': {},
            'neighbors':   {},
        }
    def setTemperature(self,mac,temperature):
        with self.dataLock:
            self.data['temperature'][mac] = temperature
    def setNeighbors(self,mac,neighbors):
        with self.dataLock:
            self.data['neighbors'][mac]   = neighbors
            print self.data['neighbors']
    def get(self,name):
        with self.dataLock:
            return self.data[name]

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
                    notifTypes =    [
                                        IpMgrSubscribe.IpMgrSubscribe.NOTIFHEALTHREPORT,
                                    ],
                    fun =           self._handle_HealthReport,
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
    
    def _handle_HealthReport(self,notifName, notifParams):
        
        '''
        {
            'Device': {
                'batteryVoltage': 3058,
                'temperature': 23,
                'numRxLost': 0,
                'numTxFai': 0,
                'queueOcc': 33,
                'charge': 801,
                'numRxOk': 0,
                'numTxOk': 32,
                'badLinkSlot': 0,
                'numMacDropped': 0,
                'badLinkOffset': 0,
                'numTxBad': 0,
                'badLinkFrameId': 0,
            },
            'Discovered': {
                'discoveredNeighbors': [
                    {
                        'rssi': -11,
                        'numRx': 1,
                        'neighborId': 2
                    }
                ],
                'numItems':       1,
                'numJoinParents': 1,
            }
        }
        '''
        
        try:
            assert notifName=='notifHealthReport'
            mac    = notifParams.macAddress
            hr     = self.hrParser.parseHr(notifParams.payload)
            if 'Discovered' in hr:
                neighbors = {}
                for n in ht['Discovered']['discoveredNeighbors']:
                    try:
                        m = AppData().getMacFromId(n['neighborId'])
                    except Exception:
                        continue
                    r = n['rssi']
                    neighbors[m] = r
                AppData().setNeighbors(mac,neighbors)
        except Exception as err:
            criticalError(err)
    
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
            temp = notif.samples[0]
            print 'TODO OAP {0} {1}'.format(mac,temp)
        except Exception as err:
            criticalError(err)

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
    web            = WebInterface(receiver)
    
    raw_input("Press any key to stop.")
    
    receiver.close()
    web.close()
    
    sys.exit(0)

if __name__=="__main__":
    main()
