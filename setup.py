"""set up file for the Python Madrigal Remote API

$Id: setup.py 7655 2024-06-27 20:20:49Z kcariglia $
"""
import os, os.path, sys

from setuptools import setup
    
setup(url="http://cedar.openmadrigal.org",
      scripts=['madrigalWeb/globalIsprint.py', 'madrigalWeb/globalDownload.py',
               'madrigalWeb/globalCitation.py',
               'madrigalWeb/exampleMadrigalWebServices.py'],
      test_suite="tests",
      )

    