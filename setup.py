"""
Script for building the example:

Usage:
    python setup.py py2app
"""
from distutils.core import setup
import py2app

DATA_FILES = ['no-unread.png','unread.png','notify.wav','Growl.framework','newsblur-icon.png']
OPTIONS = {
  'iconfile': 'newsblur-icon.icns',
  'plist': {'CFBundleShortVersionString':'0.3.0',}
}

setup(
    name="BlurNoti",
    app=["blurnoti.py"],
    data_files=DATA_FILES,
    options={'py2app':OPTIONS}
)
