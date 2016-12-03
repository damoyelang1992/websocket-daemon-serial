'''
 Original windows service code:

 Author: Alex Baker
 Date: 7th July 2008
 Description : Simple python program to generate wrap as a service based on example on the web, see link below.

 http://essiene.blogspot.com/2005/04/python-windows-services.html

 Usage : python aservice.py install
 Usage : python aservice.py start
 Usage : python aservice.py stop
 Usage : python aservice.py remove

 C:\>python aservice.py  --username <username> --password <PASSWORD> --startup auto install

'''

import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil
import os,servicemanager,logging,thread,myserver
# import win32traceutil


def checkForStop(self):
    self.timeout = 60000

    while 1:
        # Wait for service stop signal, if I timeout, loop again
        rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
        # Check to see if self.hWaitStop happened
        if rc == win32event.WAIT_OBJECT_0:
            # Stop signal encountered
            servicemanager.LogInfoMsg("LexinSmartDeamon - STOPPED")
            # TODO: Improve this. Windows consider it an error right now
            os._exit(0)
        else:
            servicemanager.LogInfoMsg("LexinSmartDeamon - is alive and well")


class aservice(win32serviceutil.ServiceFramework):
    _svc_name_ = "LexinSmartDaemon"
    _svc_display_name_ = "LexinSmartSerialBridge"
    _svc_description_ = "allows the browser to communicate with the usb devices"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # import win32traceutil
        # logging.basicConfig(filename='app.log', level=logging.INFO)
        logging.info("running daemon")
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))

        servicemanager.LogInfoMsg(os.getcwd())

        # TODO: Move this to threading model and start/stop the thread only when we have registered clients
        # Create a thread as follows
        try:
            thread.start_new_thread(checkForStop, (self,))
        except:
            print "Error: unable to start thread"
        myserver.main()


def ctrlHandler(ctrlType):
    return True


if __name__ == '__main__':
    win32api.SetConsoleCtrlHandler(ctrlHandler, True)
    win32serviceutil.HandleCommandLine(aservice)