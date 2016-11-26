# -*- coding: utf-8 -*-
#!/usr/bin/python
from setuptools import setup

APP = ['myserver.py']
APP_NAME = "webSerial"
DATA_FILES = ['avrdudes/Darwin/avrdude.conf', 'avrdudes/Darwin/avrdude', 'drivers/Darwin/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg']

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'codebender.icns',
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': "A Serial Websocket Bridge",
        'CFBundleIdentifier': "com.lexin.osx",
        'CFBundleVersion': "0.0.1",
        'CFBundleShortVersionString': "0.0.1"
        # 'NSHumanReadableCopyright': u"Copyright © 2016, LexinSmart, All Rights Reserved"
    }
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)