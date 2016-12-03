# -*- coding: utf-8 -*-
#!/usr/bin/python
import sys
import logging

import os
import serial
from serial.tools import list_ports
import txaio
import thread
import threading

#needed for py2exe
#import zope.interface
from twisted.internet import reactor
from twisted.internet import error
from twisted.python import log

#needed for py2exe py2app
import autobahn.twisted.resource
from autobahn.twisted.websocket import  WebSocketServerFactory, WebSocketServerProtocol, listenWS
# from autobahn import httpstatus

import json,time,subprocess,base64,tempfile,platform

try:
  import servicemanager
  import _winreg as winreg
  import itertools
except ImportError:
  pass

list = []
serial_port = None
serial_device = None
serial_baudrate = None

logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info("Starting")


def check_drivers_osx(websocket):
    if(os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.FTDIUSBSerialDriver-2.pkg.bom") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.FTDIUSBSerialDriver-2.pkg.plist") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.postflight.pkg.bom") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.postflight.pkg.plist") and os.path.exists("/var/db/receipts/com.FTDI.ftdiusbserialdriverinstaller.preflight.pkg.bom")):
        websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
    else:
        websocket.sendMessage(json.dumps({"type":"check_drivers","installed":False}))

def check_drivers_windows(websocket):
    if(os.path.exists("C:\Windows/System32/DriverStore/FileRepository/arduino.inf_x86_neutral_f13cf06b4049adb5/arduino.inf") or os.path.exists("C:\Windows/System32/DriverStore/FileRepository/arduino.inf_amd64_neutral_f13cf06b4049adb5/arduino.inf") or os.path.exists("C:\Windows/System32/DriverStore/FileRepository/arduino.inf_x86_f13cf06b4049adb5/arduino.inf") or os.path.exists("C:\Windows/System32/DriverStore/FileRepository/arduino.inf_amd64_f13cf06b4049adb5/arduino.inf")):
        websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
    elif(platform.release() == "XP" and os.popen("dir C:\WINDOWS\system32\DRVSTORE").read().find("arduino_") != -1):
        websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
    else:
        websocket.sendMessage(json.dumps({"type":"check_drivers","installed":False}))


def check_permissions_linux(websocket):
    output = os.popen("groups | grep $(ls -l /dev/* | grep /dev/ttyS0 | cut -d ' ' -f 5)").read()
    if output != "":
        websocket.sendMessage(json.dumps({"type":"check_drivers","installed":True}))
    else:
        websocket.sendMessage(json.dumps({"type":"check_drivers","installed":False}))


#ToDo: rename this to make more sense
def check_drivers(websocket):
    if platform.system() == "Darwin":
        check_drivers_osx(websocket)
    elif platform.system() == "Windows":
        check_drivers_windows(websocket)
    elif platform.system() == "Linux":
        check_permissions_linux(websocket)


def install_drivers_osx():
    frozen = getattr(sys, 'frozen', '')
    if frozen == "macosx_app":
        path =  os.getcwd() + """/"""
        print "changing permissions: " + "chmod +x " + os.getcwd() + "/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/Contents/Packages/ftdiusbserialdriverinstallerPostflight.pkg/Contents/Resources/postflight"
        os.system("chmod +x " + os.getcwd() + "/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/Contents/Packages/ftdiusbserialdriverinstallerPostflight.pkg/Contents/Resources/postflight")

        print "changing permissions: " + "chmod +x " + os.getcwd() + "/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/Contents/Packages/ftdiusbserialdriverinstallerPreflight.pkg/Contents/Resources/preflight"
        os.system("chmod +x " + os.getcwd() + "/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/Contents/Packages/ftdiusbserialdriverinstallerPreflight.pkg/Contents/Resources/preflight")
    else:
        path = """drivers/Darwin/"""

    return os.system("""osascript -e 'do shell script "/usr/sbin/installer -pkg """ + path + """FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg/ -target /" with administrator privileges'""")


def install_drivers_windows():
    print "installing drivers"
    driver_path = os.environ['PROGRAMFILES'] + "\LexinBridge/drivers/FTDI"
    # driver_path = os.getcwd() + "/drivers/Windows/FTDI/"
    # driver_path = "C:\Users\yaolong\Desktop\websocket-daemon-serial\dist/drivers/Windows/FTDI"
    if platform.machine() == "x86":
            driver_cmd = "dpinst-x86.exe /sw"
    else:
            driver_cmd = "dpinst-amd64.exe /sw"

    print "Installation Path: ", driver_path
    print "Installation cmd: ", driver_cmd
    logging.info("Installation Path:")
    logging.info(driver_path)
    logging.info("Installation CMD:")
    logging.info(driver_cmd)

    proc = subprocess.Popen(driver_cmd, stdout=subprocess.PIPE, shell=True, cwd=driver_path)
    (out, err) = proc.communicate()
    print "program output:", out
    print "program error:", err
    print proc.returncode

    return proc.returncode


def fix_permissions_linux():
    os.system("pkexec gpasswd -a " + os.getlogin() + " $(ls -l /dev/* | grep /dev/ttyS0 | cut -d ' ' -f 5)")


def install_drivers(websocket):
    if platform.system() == "Darwin":
        return_val = install_drivers_osx()
        if(return_val == 0):
            websocket.sendMessage(json.dumps({"type":"installation_output", "success":True}))
        else:
            websocket.sendMessage(json.dumps({"type":"installation_output", "success":False, "error":return_val}))
    elif platform.system() == "Windows":
        return_val = install_drivers_windows()
        if(return_val == 256):
            websocket.sendMessage(json.dumps({"type":"installation_output", "success":True}))
        else:
            websocket.sendMessage(json.dumps({"type":"installation_output", "success":False, "error":return_val}))
    elif platform.system() == "Linux":
        fix_permissions_linux()


def do_install_drivers(websocket):
    # Create a thread as follows
    try:
        thread.start_new_thread(install_drivers, (websocket,))
    except:
        print "Error: unable to start thread"


def check_ports_posix():
    list = list_ports.comports()

    ports = []
    for port in list:
        # if(port[0].startswith("/dev/tty") and not port[0].startswith("/dev/ttyS")):
        ports.append(port[0])
    return ports


def check_ports_windows():
        """ Uses the Win32 registry to return an
        iterator of serial (COM) ports
        existing on this computer.
        """
        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        except WindowsError, e:
                if e.errno == 2:
                        return []
                else:
                        raise e

        ports = []
        for i in itertools.count():
                try:
                        val = winreg.EnumValue(key, i)
                        ports.append(str(val[1]))
                except EnvironmentError:
                        break
        return ports


def check_ports():
        if platform.system() == "Windows":
                return check_ports_windows()
        else:
                return check_ports_posix()


def flash_arduino(cpu, ptc, prt, bad, binary):
    print "flashing arduino"

    if platform.system() == "Windows":
        # bash_shell_path = os.environ['PROGRAMFILES'] + "\LexinBridge/avrdudes/" + platform.system()
        # bash_shell_path = os.getcwd() + "/avrdudes/" + platform.system()
        # bash_shell_path = "C:\Users\yaolong\Desktop\websocket-daemon-serial\dist/avrdudes/Windows"
        bash_shell_path = os.environ['PROGRAMFILES'] + "\LexinBridge/avrdudes"
        logging.info("flash_arduino avrdude directory:")
        logging.info(bash_shell_path)
        bash_shell_cmd =  "avrdude"
    else:
        frozen = getattr(sys, 'frozen', '')
        if frozen == "macosx_app":
            bash_shell_path = os.getcwd()
            print "changing permissions: " + "chmod o+x " + os.getcwd() + "/avrdude"
            os.system("chmod +x " + os.getcwd() + "/avrdude")
        else:
            bash_shell_path = os.getcwd() + "/avrdudes/" + platform.system()
        bash_shell_cmd =  "./avrdude"
    bash_shell_cnf = " -Cavrdude.conf"

    #TODO: Check about verbose options and speed
    # bash_shell_vbz = " -v -v -v -v"
    bash_shell_vbz = " "
    bash_shell_cpu = " -p" + cpu
    bash_shell_ptc = " -c" + ptc
    bash_shell_prt = " -P" + prt
    bash_shell_bad = " -b" + bad
    # TODO: Check for .bin vs .hex
    # binary = base64.b64decode(binary)
    bin_file = tempfile.NamedTemporaryFile(delete=False)
    print "file name: ", bin_file.name
    logging.info("temp filename: %s\n", bin_file.name)
    bin_file.write(binary)
    bin_file.close()
    bash_shell_file = " -Uflash:w:" + bin_file.name + ":i"
    bash_shell = bash_shell_cmd + bash_shell_cnf + bash_shell_vbz + bash_shell_cpu + bash_shell_ptc + bash_shell_prt + bash_shell_bad + " -D" + bash_shell_file
    print "Flashing Path: ", bash_shell_path
    print "Flashing cmd: ", bash_shell
    logging.info("Flashing Path:")
    logging.info(bash_shell_path)
    logging.info("Flashing cmd:")
    logging.info(bash_shell)
    proc = subprocess.Popen(bash_shell, stdout=subprocess.PIPE, shell=True, cwd=bash_shell_path)
    (out, err) = proc.communicate()
    print "program output:\n", out
    print "program error:\n", err

    print proc.returncode
    os.unlink(bin_file.name)
    return proc.returncode


def flash(websocket, cpu, ptc, prt, bad, binary):
    flash_val = flash_arduino(cpu, ptc, prt, bad, binary)
    websocket.sendMessage(json.dumps({"type":"flashing_output", "retval":flash_val}))


def do_flash(websocket, cpu, ptc, prt, bad, binary):
    # Create a thread as follows
    try:
        thread.start_new_thread(flash, (websocket, cpu, ptc, prt, bad, binary,))
    except:
        print "Error: unable to start thread"


class EchoServerProtocol(WebSocketServerProtocol):
    def onMessage(self, msg, binary):
        try:
            message = json.loads(msg)
        except ValueError:
            logging.info("Received message: %s", msg)
            print "Received message: ", msg
        if message["type"] == "ack":
            self.sendMessage(msg, binary)
        else:
            logging.info("Received message: %s", msg)
            print "Received message: ", msg


        if message["type"] == "version":
            self.sendMessage(json.dumps({"type":"version", "version":"0.1"}) ,binary)
        elif message["type"] == "flash":
            if platform.system() == "Windows":
                                message["prt"] = '\\\\.\\' + message["prt"]
            do_flash(self, message["cpu"], message["ptc"], message["prt"], message["bad"], message["binary"])
        elif message["type"] == "message":
            print message["text"]
        elif message["type"] == "list_ports":
            ports = check_ports()
            self.sendMessage(json.dumps({"type":"ports", "ports":ports}))
        elif message["type"] == "check_drivers":
            check_drivers(self)
        elif message["type"] == "install_drivers":
            do_install_drivers(self)
        elif message["type"] == "set_serial":
            global serial_port
            global serial_device
            global serial_baudrate
            if serial_port == None:
                serial_device = message["port"]
                serial_baudrate = message["baudrate"]
            else:
                self.sendMessage(json.dumps({"type":"error", "message":"You cannot set port while a serial connection is still open"}))

    # def onConnect(self, request):

    def onOpen(self):
        self.factory.register(self)
        self.sendMessage(json.dumps({"text":"Socket Opened"}));
        ports = check_ports()
        print "Sending Ports Message"
        self.sendMessage(json.dumps({"type":"ports", "ports":ports}))

    def connectionLost(self, reason):
        self.factory.unregister(self)
        WebSocketServerProtocol.connectionLost(self, reason)


def update_ports(factory):
    print "Starting check for ports"
    old_ports = []
    while 1:
        ports = check_ports()
        if(ports != old_ports):
            for port in ports:
                print port
            print "Sending Ports Message"
            factory.broadcast(json.dumps({"type":"ports", "ports":ports}))
        old_ports = ports
        time.sleep(0.05)


################### CUSTOM FACTORY ###################
class BroadcastServerFactory(WebSocketServerFactory):
    """
    Simple broadcast server broadcasting any message it receives to all
    currently connected clients.
    """

    def __init__(self, url):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []
        self.tick()

        #TODO: Move this to threading model and start/stop the thread only when we have registered clients
        # Create a thread as follows
        try:
            thread.start_new_thread(update_ports, (self, ))
        except:
            print "Error: unable to start thread"

    def tick(self):
        self.broadcast(json.dumps({"type":"heartbeat"}))
        reactor.callLater(1, self.tick)

    def register(self, client):
        if not client in self.clients:
            # print "registered client " + client.peerstr
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            # print "unregistered client " + client.peerstr
            self.clients.remove(client)

    def broadcast(self, msg):
        # print "broadcasting message '%s' .." % msg
        for c in self.clients:
            c.sendMessage(msg)
            # print "message sent to " + c.peerstr

################### END CUSTOM FACTORY ###################

################ WEBSERIAL CODE


class ReaderThread(threading.Thread, ):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, websocket_port, serial_port):
        super(ReaderThread, self).__init__()
        self._stop = threading.Event()
        self.websocket_port = websocket_port
        self.serial_port = serial_port

    def stop(self):
        self.run = False
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        self.run = True
        self.read()

    def read(self):
        """loop and copy serial->console"""
        try:
            while self.run:
		try:
                    #I Got this Error,when Serialport BaudRate Error
                    data = self.serial_port.read().decode("ascii")
                except UnicodeDecodeError:
                    print("SerialBaud Error!")
                    data = "SerialBaud Error!\r\n"
                if(data != ""):
                    # sys.stdout.write(data)
                    # sys.stdout.flush()
                    self.websocket_port.sendMessage(str(data))
        except serial.SerialException, e:
            raise


def writer(serial_port, data):
    serial_port.write(data)


class WebSerialProtocol(WebSocketServerProtocol):
    def __init__(self):
        self.is_closed = txaio.create_future()
        self.connection_invalid = False

    def onMessage(self, msg, binary):
        global serial_port
        global serial_device
        global serial_baudrate

        if serial_port != None:
            writer(serial_port, msg)
            print("SerialData:"+msg)
        else:
            print "Could not send data. No active serial connections"

    def onConnect(self, request):
		print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
		# print("WebSocket connection open.")
        global serial_port
        global serial_device
        global serial_baudrate

        print "Connect Message Received"
        serial_port = serial.Serial(serial_device, baudrate= serial_baudrate, timeout=0)
        self.read_thread = ReaderThread(self, serial_port)
        self.read_thread.daemon = True
        self.read_thread.start()

    def connectionLost(self, reason):
        global serial_port
        global serial_device
        global serial_baudrate

        if not self.connection_invalid:
            print "Disconnect Message Received"
            if serial_port != None:
                oldserial = serial_port
                serial_port = None
                serial_device = None
                serial_baudrate = None
                self.read_thread.stop()
                self.read_thread.join()
                oldserial.close()
        WebSocketServerProtocol.connectionLost(self, reason)


log.startLogging(sys.stdout)


def main():
    try:
        ServerFactory = BroadcastServerFactory

        factory = ServerFactory("ws://localhost:9000")
        factory.protocol = EchoServerProtocol

        factory2 = WebSocketServerFactory("ws://localhost:9001")
        factory2.protocol = WebSerialProtocol

        reactor.listenTCP(9000, factory)
        reactor.listenTCP(9001, factory2)
        reactor.run()
    except error.CannotListenError, e:
        print "Port is already used. Exiting..."
        os._exit(0)


if __name__ == '__main__':
    login_items_cmd = "osascript -e \"tell application \\\"System Events\\\" to make login item at end with properties { name: \\\"codebender\\\", path: \\\"" + os.getcwd().replace("/Contents/Resources", "") + "\\\", hidden:false }\""
    print "Adding app to login items:"
    print login_items_cmd
    os.system(login_items_cmd)
    main()
