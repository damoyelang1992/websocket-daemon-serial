from distutils.core import setup
import py2exe

my_data_files = [('avrdudes/Windows', ['avrdudes/Windows/avrdude.conf']),
                ('avrdudes/Windows', ['avrdudes/Windows/avrdude.exe']),
                ('avrdudes/Windows', ['avrdudes/Windows/libusb0.dll']),
                ('drivers/Windows/FTDI', ['drivers/Windows/FTDI/arduino.cat']),
                ('drivers/Windows/FTDI', ['drivers/Windows/FTDI/arduino.inf']),
                ('drivers/Windows/FTDI', ['drivers/Windows/FTDI/dpinst-x86.exe']),
                ('drivers/Windows/FTDI', ['drivers/Windows/FTDI/dpinst-amd64.exe']),
                ('vcredist_x86.exe')]


setup(options = {"py2exe": {"compressed": 1, "bundle_files": 1} },
      zipfile = None,
      data_files = my_data_files,
      console=['myserver.py'])
