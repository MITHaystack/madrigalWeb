"""testMadrigalWeb is a unittest for the madrigalWeb module

Written by: Bill Rideout

$Id: testMadrigalWeb.py 7700 2024-09-09 14:26:58Z brideout $
"""

# standard python modules
import unittest
import os, sys, os.path
import datetime
import tempfile
import re

# module to test
import madrigalWeb.madrigalWeb

# constants
user_fullname = 'Bill Rideout - automated test'
user_email = 'brideout@haystack.mit.edu'
user_affiliation = 'MIT Haystack'
url = 'http://millstonehill.haystack.mit.edu'

class TestMadrigalData(unittest.TestCase):
    """Unit test of main class madrigalWeb.madrigalWeb.MadrigalData
    """
    
    def setUp(self):
        self.madData = madrigalWeb.madrigalWeb.MadrigalData(url)
        madExps = self.madData.getExperiments(30, 1998, 1, 19, 0, 0, 0, 1998, 12, 31, 23, 59, 59)
        madExps.sort()
        self.expId = madExps[0].id
        self.madExp = madExps[0]
        self.madExp2 = madExps[1]
        fileList = self.madData.getExperimentFiles(self.expId)
        self.filename = None
        for thisFile in fileList:
            if thisFile.category != 1:
                continue
            if thisFile.kindat < 3400 or thisFile.kindat > 3410:
                continue
            self.filename = thisFile.name
            break
        
        if self.filename is None:
            raise IOError('Basic Millstone Hill test file not found')
        
        self.tempDir = tempfile.gettempdir()
        
    def test_getAllInstruments(self):
        instList = self.madData.getAllInstruments()
        codeList = [inst.code for inst in instList]
        mnemList = [inst.mnemonic for inst in instList]
        self.assertIn(30, codeList)
        self.assertIn('mlh', mnemList)
        s = str(instList[0])
        self.assertTrue(s.find('category') != -1)
        
    def test_getExperiments(self):
        madExps = self.madData.getExperiments(30, 1998, 1, 19, 0, 0, 0, 1998, 1, 21, 23, 59, 59)
        madExps.sort()
        self.assertEqual(self.expId, madExps[0].id)
        
    def test_str_Experiment(self):
        s = str(self.madExp)
        self.assertTrue(s.find('PIEmail') != -1)
        
    def test_compare_Experiments(self):
        self.assertTrue(self.madExp == self.madExp)
        self.assertTrue(self.madExp < self.madExp2)
        self.assertTrue(self.madExp <= self.madExp)
        self.assertTrue(self.madExp <= self.madExp)
        self.assertTrue(self.madExp2 > self.madExp)
        self.assertTrue(self.madExp2 >= self.madExp2)
        
    def test_getExperimentFiles(self):
        fileList = self.madData.getExperimentFiles(self.expId)
        s = str(fileList[0])
        self.assertTrue(s.find('kindatdesc') != -1)
        found = False
        for thisFile in fileList:
            if thisFile.category != 1:
                continue
            if thisFile.kindat < 3400 or thisFile.kindat > 3410:
                continue
            self.assertEqual(self.filename, thisFile.name)
            found = True
            break
        
        self.assertRaises(ValueError, self.madData.getExperimentFiles, -1)
        
        if not found:
            # should not get here
            raise IOError('Basic Millstone Hill test file not found')
    
    def test_getExperimentFileParameters(self):
        fileList = self.madData.getExperimentFiles(self.expId)
        parms = self.madData.getExperimentFileParameters(fileList[0].name)
        s = str(parms[0])
        self.assertTrue(s.find('isMeasured:') != -1)
        
    
    def test_downloadFile(self):
        result = self.madData.downloadFile(self.filename, os.path.join(self.tempDir, "test.txt"), 
                                           user_fullname, user_email, user_affiliation, "simple")
        self.assertIsNone(result)
        os.remove(os.path.join(self.tempDir, "test.txt"))
        result = self.madData.downloadFile(self.filename, os.path.join(self.tempDir, "test.hdf5"), 
                                           user_fullname, user_email, user_affiliation, "hdf5")
        self.assertIsNone(result)
        os.remove(os.path.join(self.tempDir, "test.hdf5"))
        
    def test_simplePrint(self):
        result = self.madData.simplePrint(self.filename, user_fullname, user_email, user_affiliation)
        self.assertTrue(result.find('555.7') != -1)
        
    def test_isprint(self):
        result = self.madData.isprint(self.filename, 'gdalt,ti', 'filter=gdalt,500,600 filter=ti,1900,2.0E+3 date1=1/1/1960 time1=00:00:00 date2=1/1/2024 time2=00:00:00',
                                      user_fullname, user_email, user_affiliation)
        self.assertTrue(result.find('555.7') != -1)
        outputFile = os.path.join(self.tempDir, "test.hdf5")
        self.madData.isprint(self.filename, 'gdalt,ti', 'date1=1/1/1960 time1=00:00:00 date2=1/1/2024 time2=00:00:00',
                             user_fullname, user_email, user_affiliation, outputFile=outputFile)
        self.assertTrue(os.path.exists(outputFile))
        os.remove(outputFile)
        
        
    def test_madCalculator(self):
        result = self.madData.madCalculator(1999,2,15,12,30,0,45,55,5,-170,-150,10,200,2.0E+2,0,
                                            'sdwht, kp', ['kinst'], [30])
        result = str(result)
        self.assertTrue(result.find('45.0, -170.0, 200.0') != -1)
        
    def test_madTimeCalculator(self):
        result = self.madData.madTimeCalculator(1999,2,15,12,30,0,1999,2,15,13,30,0,0.025E+1,'kp, ap3')
        result = str(result)
        self.assertTrue(result.find('1999.0, 2.0, 15.0') != -1)
        
    def test_madTimeCalculator(self):
        result = self.madData.madTimeCalculator(1999,2,15,12,30,0,1999,2,15,13,30,0,0.025E+1,'kp, ap3')
        result = str(result)
        self.assertTrue(result.find('1999.0, 2.0, 15.0') != -1)
        
    def test_madCalculator2(self):
        result = self.madData.madCalculator2(1999,2,15,12,30,0,[45,55],[-170,-150],[200,300],'bmag, pdcon',
                                         ['kp'],[1.0],['ti','te','ne'],
                                         [[1000,1000],[1100,1200],[1e+11,1.2e+11]])
        result = str(result)
        self.assertTrue(result.find('45.0, -170.0, 200.0') != -1)
        
    def test_madCalculator3(self):
        result = self.madData.madCalculator3(yearList=[2001,2001], monthList=[3,3], dayList=[19,20],
                                             hourList=[12,12], minList=[30,40], secList=[20,0],
                                             latList=[[45,46,47,48.5],[46,47,48.2,49,50]],
                                             lonList=[[-70,-71,-72,-73],[-70,-71,-72,-73,-74]],
                                             altList=[[145,200,250,300.5],[2.0E+2,250,300,350,400]],
                                             parms='bmag,pdcon,ne_model',
                                             oneDParmList=[],
                                             oneDParmValues=[],
                                             twoDParmList=[],
                                             twoDParmValues=[])
        result = str(result)
        self.assertTrue(result.find('2001, 3, 19, 12, 30, 20, 45.0, -70.0, 145.0') != -1)
        
    def test_geodeticToRadar(self):
        result = self.madData.geodeticToRadar(42.0, -70.0, 0.1, [50, 51,52], [-80.0, -70.0, -60.0], [200.0, 3.0E+2, 400.0])
        result = str(result)
        self.assertTrue(result.find('[-37.53, 4.02, 1210.47]') != -1)
        
    def test_geodeticToRadar(self):
        result = self.madData.listFileTimes('experiments/1998/mlh/20jan98')
        result = str(result)
        self.assertTrue(result.find('experiments/1998/mlh/20jan98') != -1 and result.find('datetime.datetime(') != -1)
        
    def test_getVersion(self):
        result = self.madData.getVersion()
        result = str(result)
        reStr = r'[0-9]+.[0-9]+'
        foundList = re.findall(reStr, result)
        self.assertTrue(len(foundList) > 0)
        
    def test_compareVersions(self):
        result = self.madData.compareVersions('2.7', '3.2')
        self.assertFalse(result)
        
    def test_getCitedFilesFromUrl(self):
        result = self.madData.getCitedFilesFromUrl('http://cedar.openmadrigal.org/getCitationGroup?id=1000')
        self.assertTrue(len(result) > 1)
        
    def test_getCitationListFromFilters(self):
        startDate = datetime.datetime(1998,1,1)
        endDate = datetime.datetime(1998,2,1)
        inst = ['Millstone*', 'Jicamarca*']
        result = self.madData.getCitationListFromFilters(startDate, endDate, inst)
        self.assertTrue(len(result) > 1)
        
    def test_listFileTimes(self):
        expDir = 'experiments/1998/mlh/20jan98'
        result = self.madData.listFileTimes(expDir)
        self.assertTrue(datetime.datetime(1998,1,1) < result[-1][-1])
        status = False
        for fileInfo in result:
            if fileInfo[0].find('plots') != -2:
                basename = os.path.basename(fileInfo[0])
                downloadName = os.path.join('/tmp', basename)
                self.madData.downloadWebFile(fileInfo[0], downloadName)
                self.assertTrue(os.path.exists(downloadName))
                os.remove(downloadName)
                status = True
                break
        self.assertTrue(status)
        
    def test_traceMagneticField(self):
        year = 1998
        month = 1
        day = 20
        hour = 18
        minute = 30
        second = 0
        inputType = outputType = 0
        alts = [200, 300, 400]
        lats = [42,42,42]
        lons = [-70,-70,-70]
        model = 1 # igrf
        qualifier = 0 # comjugate
        stopAlt = 1000
        result = self.madData.traceMagneticField(year, month, day, hour, minute, second, 
                                                 inputType, outputType, alts, lats, lons, model,
                                                 qualifier, stopAlt)
        self.assertTrue(len(result[-1]) == 3)
        
    
        
        
        
        
testCaseList = (TestMadrigalData,)
        
suite = unittest.TestSuite()
for testCase in testCaseList:
    tests = unittest.TestLoader().loadTestsFromTestCase(testCase)
    suite.addTests(tests)
unittest.TextTestRunner(verbosity=2).run(suite)