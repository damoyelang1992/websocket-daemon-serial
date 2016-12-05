# -*- coding: utf-8 -*-
#!/usr/bin/python
from setuptools import setup

setup(
    options=dict(py2app=dict(
        resources = ['avrdudes/Darwin/avrdude.conf', 'avrdudes/Darwin/avrdude', 'drivers/Darwin/FTDIUSBSerialDriver_10_4_10_5_10_6_10_7.mpkg'],
        plist = dict(LSBackgroundOnly=True),
        iconfile = "lexin.icns",
    )),
    app=["myserver.py"],
    name="LexinSerialBradge",
    version="0.6",
    setup_requires=["py2app"],
)