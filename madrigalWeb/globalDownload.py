#!python


"""This script runs a global search through Madrigal data from a given URL, and downloads all matching files.

    This script is a stand-alone application, and can be run from anywhere with a connection to the internet.
    It runs on either unix or windows.  It requires only the MadrigalWeb python module to be installed.

$Id: globalDownload.py 7454 2022-09-19 18:31:01Z brideout $
"""

usage = """
        Usage:

        globalDownload.py --url=<Madrigal url> --outputDir=<output directory> \
            --user_fullname=<user fullname> --user_email=<user email> \
            --user_affiliation=<user affiliation> --format=<ascii,hdf5> [options]

        where:

        --url=<Madrigal url> - url to homepage of site to be searched
                                  (ie, http://madrigal.haystack.mit.edu/)
                                  This is required.

        --outputDir=<output directory> - the output directory to store all files in.  Default is to store
            all files in the same directory, and a number is added to the filename if a file might be overwritten.  Set
            --tree flag to store all files in the same directory structure they appear in Madrigal.  This
            allows all files to keep their original names. 

        --user_fullname=<user fullname> - the full user name (probably in quotes unless your name is
                                          Sting or Madonna)

        --user_email=<user email>

        --user_affiliation=<user affiliation> - user affiliation.  Use quotes if it contains spaces.
        
        --format=<ascii or hdf5>

        and options are:

        --startDate=<MM/DD/YYYY> - start date to filter experiments before.  Defaults to allow all experiments.

        --endDate=<MM/DD/YYYY> - end date to filter experiments after.  Defaults to allow all experiments.

        --inst=<instrument list> - comma separated list of instrument codes or names.  See Madrigal documentation
                                   for this list.  Defaults to allow all instruments. If names are given, the
                                   argument must be enclosed in double quotes.  An asterick will perform matching as
                                   in glob.  For example:
                                   
           --inst=10,30
           
           --inst="Jicamarca IS Radar,Arecibo*"

        --expName  - filter experiments by the experiment name.  Give all or part of the experiment name. Matching
                     is case insensitive.  Default is no filtering by experiment name.
                     
        --excludeExpName - exclude experiments by the experiment name.  Give all or part of the experiment name. Matching
                     is case insensitive and fnmatch characters * and ? are allowed.  Default is no excluding experiments by 
                     experiment name.
                     
        --fileDesc - filter files using input file Description string and case-insensitive fnmatch

        --kindat=<kind of data list> - comma separated list of kind of data codes.  See Madrigal documentation
                                       for this list.  Defaults to allow all kinds of data.  If names are given, the
                                       argument must be enclosed in double quotes.  An asterick will perform matching as
                                       in glob. For example:
                                   
            --kindat=3001,13201
        
            --kindat="INSCAL Basic Derived Parameters,*efwind*,2001"


        --seasonalStartDate=<MM/DD> - seasonal start date to filter experiments before.  Use this to select only part of the
                                year to collect data.  Defaults to Jan 1.  Example:  
                                
            --seasonalStartDate=07/01 would only allow experiments after July 1st from each year.

        
        --seasonalEndDate=<MM/DD> - seasonal end date to filter experiments after.  Use this to select only part of the
                                    year to collect data.  Defaults to Dec 31.  Example:  
                                    
            --seasonalEndDate=10/31 would only allow experiments before Oct 31 of each year.
            
        --tree - add if you want to store the downloaded files in the same hierarchy as in Madrigal: 
            <YYYY/<instCode>/<experimentDir>.  Without --tree, stores all downloaded files in one directory.
        
        --includeNonDefault - if given, include realtime files when there are no default.  Default is to search only default files.

        --verbose - if given, print each file processed info to stdout.  Default is to run silently.
        
    Example:
    
        globalDownload.py --url=http://madrigal.haystack.mit.edu --outputDir=/tmp --user_fullname="Bill Rideout" 
           --user_email=brideout@haystack.mit.edu --user_affiliation=MIT --startDate=01/01/1998 
           --endDate=-01/30/1998 --inst=30
                                    
"""

import argparse
import sys
import os
import time
import re
import datetime
import fnmatch
import socket

import madrigalWeb.madrigalWeb

def getInstrumentList(inst, server):
    """getInstrumentList takes the user argument inst and coverts it into a list of instrument codes.

    Inputs:

        inst - a string containing a comma separated list of instrument codes or names.  If names are given,
                the argument must be enclosed in double quotes.  An asterick will perform matching as in glob.
                Both names and codes may be mixed together.

        server - the active MadrigalData object to get information from

    Returns:

        a list of instrument codes (int).  Instrument code 0 means all instruments
    """
    if inst == '0':
        return [0]

    retList = []
            
    # make a list
    stringList = inst.split(',')
    # see if any are names
    nameFound = 0
    for item in stringList:
        try:
            int(item)
        except:
            nameFound = 1
            break
        
    if nameFound == 0:
        # all codes
        for item in stringList:
            retList.append(int(item))
        return retList


    # at least one name found - get a list of all instruments
    allInst = server.getAllInstruments()
    # loop through each inst
    for item in stringList:
        # if its an int, just add it
        try:
            code = int(item)
            if code not in retList:
                retList.append(code)
            continue
        except:
            pass
        # its a name if it made it here
        # see if its an exact match or a regular expression with *
        if item.find('*') == -1:
            # exact match (case insensitive)
            instFound = 0
            for thisInst in allInst:
                if item.lower() == thisInst.name.lower():
                    retList.append(thisInst.code)
                    instFound = 1
                    break
            # print warning if none found
            if instFound == 0:
                print('Warning: unable to find instrument ' + str(item))
        else:
            # use regular expression matching
            instFound = 0
            reObj = re.compile(item.replace('*', '.*'))
            for thisInst in allInst:
                m = reObj.search(thisInst.name)
                if m is not None:
                    retList.append(thisInst.code)
                    instFound = 1
        
            # print warning if none found
            if instFound == 0:
                print('Warning: unable to find instrument ' + str(item))

    return retList


def filterExperimentsUsingSeason(expList, seasonalStartDate, seasonalEndDate):
    """filterExperimentsUsingSeason returns a subset of the experiments in expList whose date is within the given season.

    Input:

        expList - a list of MadrigalExperiment objects to be filtered

        seasonalStartDate - in form MM/DD - seasonal start date to filter experiments before

        seasonalEndDate - in form MM/DD - seasonal end date to filter experiments after

    Returns:

        a subset of expList whose times are accepted
    """
    # parse seasonalStartDate and seasonalEndDate
    dateList = seasonalStartDate.split('/')
    if len(dateList) != 2:
        raise ValueError('seasonalStartDate must be in form MM/DD: ' + str(seasonalStartDate))
    try:
        startmonth = int(dateList[0])
        startday = int(dateList[1])
    except:
        raise ValueError('seasonalStartDate must be in form MM/DD: ' + str(seasonalStartDate))

    if startmonth < 1 or startmonth > 12 or startday < 1 or startday > 31:
        raise ValueError('seasonalStartDate must be in form MM/DD: ' + str(seasonalStartDate))

    dateList = seasonalEndDate.split('/')
    if len(dateList) != 2:
        raise ValueError('seasonalEndDate must be in form MM/DD: ' + str(seasonalEndDate))
    try:
        endmonth = int(dateList[0])
        endday = int(dateList[1])
    except:
        raise ValueError('seasonalEndDate must be in form MM/DD: ' + str(seasonalEndDate))

    if endmonth < 1 or endmonth > 12 or endday < 1 or endday > 31:
        raise ValueError('seasonalEndDate must be in form MM/DD: ' + str(seasonalEndDate))

    retList = []

    # now loop through all experiments and add those that pass
    for exp in expList:
        if exp.startmonth < startmonth:
            continue
        elif exp.startmonth == startmonth and exp.startday < startday:
            continue
        if exp.endmonth > endmonth:
            continue
        elif exp.endmonth == endmonth and exp.endday > endday:
            continue
        # accept
        retList.append(exp)

    return retList


def filterExperimentsUsingExpName(expList, expName):
    """filterExperimentsUsingExpName returns a subset of the experiments in expList whose name matches.

    Input:

        expList - a list of MadrigalExperiment objects to be filtered

        expName  - filter experiments by the experiment name.  Can be all or part of the experiment name. Matching
                     is case insensitive.

    Returns:

        a subset of expList whose names are accepted
    """
    retList = []
    expNameArg = '*%s*' % (expName.replace(' ', '_')) # since we are using fnmatch

    # now loop through all experiments and add those that pass
    for exp in expList:
        try:
            thisExpName = exp.name.replace(' ', '_')
        except:
            continue

        if not fnmatch.fnmatch(thisExpName.lower(), expNameArg.lower()):
            continue

        # accept
        retList.append(exp)

    return retList


def excludeExperimentsUsingExpName(expList, expName):
    """excludeExperimentsUsingExpName returns a subset of the experiments in expList whose name does not match.

    Input:

        expList - a list of MadrigalExperiment objects to be filtered

        expName  - exclude experiments by the experiment name.  Can be all or part of the experiment name. Matching
                     is case insensitive. None for experiment name always accepted.

    Returns:

        a subset of expList whose names are accepted
    """
    retList = []
    expNameArg = '*%s*' % (expName.replace(' ', '_')) # since we are using fnmatch

    # now loop through all experiments and add those that do not match. No experiment name is always accepted
    for exp in expList:
        try:
            thisExpName = exp.name.replace(' ', '_')
        except:
            retList.append(exp)
            continue

        if not fnmatch.fnmatch(thisExpName.lower(), expNameArg.lower()):
            # accept
            retList.append(exp)

    return retList



def getExperimentFileList(server, expList, includeNonDefault, verbose=False):
    """getExperimentFileList returns a list of MadrigalExperimentFile objects given an experiment list.

    Inputs::

        server - the active MadrigalData object to get information from
        
        expList - the list of desired MadrigalExperiment objects
        
        includeNonDefault - 1 if should include non-default files, 0 otherwise

    Returns:

        a list of MadrigalExperimentFile objects
    """
    retList = []

    for exp in expList:
        time.sleep(0.5)
        try:
            theseExpFiles = server.getExperimentFiles(exp.id, includeNonDefault)
        except:
            # skip experiments with no files
            continue
        for expFile in theseExpFiles:
            retList.append(expFile)
            
        if verbose:
            print('Analyzed exp url %s' % (exp.url))

    return retList


def filterExperimentFilesUsingKindat(expFileList, kindat):
    """filterExperimentFilesUsingKindat returns a subset of the experiment files in expFileList whose kindat is found in kindat argument.

    Input:

        expFileList - a list of MadrigalExperimentFile objects to be filtered

        kindat - the kindat argument passed in by the user - comma separated list of kind of data codes.  If names are given, the
                argument must be enclosed in double quotes.  An asterick will perform matching as in glob.

    Returns:

        a subset of expFileList whose kindat values are accepted
    """
    strList = kindat.split(',')

    # create lists of kindat ints, kindat names, and kindat regular expressions
    kindatCodeList = []
    kindatNameList = []

    for item in strList:
        try:
            value = int(item)
            kindatCodeList.append(value)
            continue
        except:
            pass
        # a non-integer found
        testName = '*' + item.lower().replace(' ', '_') + '*'
        kindatNameList.append(testName)

    # now loop through each experiment file, and add it to a new list if its accepted
    retList = []
    for expFile in expFileList:
        # code match
        if expFile.kindat in kindatCodeList:
            retList.append(expFile)
            continue
        # description match
        try:
            kindatDesc = expFile.kindatdesc.lower()
        except:
            continue
        kindatDesc = kindatDesc.replace(' ', '_')
        for kindatName in kindatNameList:
            if fnmatch.fnmatch(kindatDesc, kindatName):
                retList.append(expFile)
                break

    return retList



def filterExperimentFilesUsingStatus(expFileList):
    """filterExperimentFilesUsingStatus returns a subset of the experiment files in expFileList with default status.

    Input:

        expFileList - a list of MadrigalExperimentFile objects to be filtered.

    Returns:

        a subset of expFileList with default status
    """

    retList = []
    for expFile in expFileList:
        if expFile.category == 1:
            retList.append(expFile)

    return retList


def filterExperimentFilesUsingFileDesc(expFileList, fileDesc):
    """filterExperimentFilesUsingFileDesc returns a subset of the experiment files in expFileList with filtered
       using fileDesc string and case-insensitive fnmatch.

    Input:

        expFileList - a list of MadrigalExperimentFile objects to be filtered.

    Returns:

        a subset of expFileList with file descriptions that match
    """

    retList = []
    fileDescArg = '*%s*' % (fileDesc.replace(' ', '_')) # since we are using fnmatch

    # now loop through all experiments and add those that pass
    for expFile in expFileList:
        try:
            thisExpFileDesc = expFile.status.replace(' ', '_')
        except:
            continue

        if not fnmatch.fnmatch(thisExpFileDesc.lower(), fileDescArg.lower()):
            continue
        
        # accept
        retList.append(expFile)

    return retList


def getTimesOfExperiment(expList, expId):
    """getTimesOfExperiment returns a list of the start and end time of the experiment given expId.

    Input:

        expList - the list of MadrigalExperiment objects

        expId - the experiment id

    Returns:

        a list of:
            (startyear,
            startmonth,
            startday,
            starthour,
            startmin,
            startsec,
            endyear,
            endmonth,
            endday,
            endhour,
            endmin,
            endsec)
    """

    retList = None
    for exp in expList:
        if exp.id == expId:
            retList = (exp.startyear,
                       exp.startmonth,
                       exp.startday,
                       exp.starthour,
                       exp.startmin,
                       exp.startsec,
                       exp.endyear,
                       exp.endmonth,
                       exp.endday,
                       exp.endhour,
                       exp.endmin,
                       exp.endsec)

    return retList

def getSubdirectoryFromFullFile(fullFilename):
    """get the subdirectory to store this file in from the full file name
    
    Return everything after experiments* and before filename
    """
    dirname = os.path.dirname(fullFilename)
    i = dirname.find('/experiments')
    if i == -1:
        raise ValueError('Illegal filename %s' % (fullFilename))
    dirname = dirname[i+len('/experiments'):]
    i = dirname.find('/')
    if i == -1:
        raise ValueError('Illegal filename %s' % (fullFilename))
    return(dirname[i+1:])




# parse command line
parser = argparse.ArgumentParser(
        description='Run a global search through Madrigal data and download data matching input criteria.',
        usage=usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
# Required arguments
parser.add_argument('--url', type=str, required=True, help="URL of the main page of a Madrigal site.")
parser.add_argument('--outputDir', type=str, required=True, help="Path to a valid, writable output directory.")
parser.add_argument('--user_fullname', required=True, help='Full user name (quoted if contains spaces)')
parser.add_argument('--user_email', required=True, help='User email address')
parser.add_argument('--user_affiliation', required=True, help='User affiliation (quoted if contains spaces)')
parser.add_argument('--format', type=str, choices=['ascii', 'hdf5', 'netCDF4'], required=True, help="Output data format (ascii, hdf5, netCDF4).")

# Optional arguments
parser.add_argument('--startDate', required=True, help='Start date in YYYY-MM-DD format to filter experiments before.  Defaults to allow all experiments.')
parser.add_argument('--endDate', required=True, help='End date in YYYY-MM-DD format to filter experiments after.  Defaults to allow all experiments.')
parser.add_argument('--inst', default='0', help='Comma separated list of instrument codes or names. See Madrigal documentation \
                                   for this list.  Defaults to allow all instruments. If names are given, the \
                                   argument must be enclosed in double quotes.  An asterisk will perform matching as \
                                   in glob.')
parser.add_argument('--kindat', default='0', help='Comma separated list of kind of data codes. See Madrigal documentation \
                                       for this list.  Defaults to allow all kinds of data.  If names are given, the \
                                       argument must be enclosed in double quotes.  An asterisk will perform matching as \
                                       in glob.')
parser.add_argument('--seasonalStartDate', type=str, default='01/01', help='Seasonal start date in MM/DD format to filter experiments before.  Use this to select only part of the \
                                year to collect data.  Defaults to Jan 1.')
parser.add_argument('--seasonalEndDate', type=str, default='12/31', help='Seasonal end date in MM/DD format to filter experiments after.  Use this to select only part of the \
                                    year to collect data.  Defaults to Dec 31.')
parser.add_argument('--tree', action='store_true', help="add if you want to store the downloaded files in the same hierarchy as in Madrigal: \
   <YYYY/<instCode>/<experimentDir>.  Without --tree, stores all downloaded files in one directory.")
parser.add_argument('--includeNonDefault', action='store_true', help='Include realtime files when no default')
parser.add_argument('--verbose', action='store_true', help="Flag to enable verbose output.")
parser.add_argument('--expName', type=str, help='Filter experiments by experiment name. Give all or part of the experiment name. Matching \
                     is case insensitive and fnmatch characters * and ? are allowed.')
parser.add_argument('--excludeExpName', type=str, help='Exclude experiments by experiment name. Give all or part of the experiment name. Matching \
                     is case insensitive and fnmatch characters * and ? are allowed.')
parser.add_argument('--fileDesc', type=str, help='Filter files by file description string. Give all or part of the file description string. Matching \
                     is case insensitive and fnmatch characters * and ? are allowed.')

# Parse the command line arguments
args = parser.parse_args()

# Set default values for optional parameters
url = args.url
outputDir = args.outputDir
user_fullname = args.user_fullname
user_email = args.user_email
user_affiliation = args.user_affiliation
format = args.format if args.format != 'ascii' else 'simple'  # Convert 'ascii' to 'simple'
startDate = args.startDate
endDate = args.endDate
inst = args.inst
kindat = args.kindat
seasonalStartDate = args.seasonalStartDate
seasonalEndDate = args.seasonalEndDate
tree = args.tree
includeNonDefault = 1 if args.includeNonDefault else 0
verbose = 1 if args.verbose else 0
expName = args.expName
excludeExpName = args.excludeExpName
fileDesc = args.fileDesc

# check that outputDir exists
if outputDir is None:
    print('--outputDir argument required - must be a valid, writable file directory')
    sys.exit(0)
elif not os.access(outputDir, os.W_OK):
    try:
        os.makedirs(outputDir)
    except:
        raise IOError('Unable to either write to or create %s' % (outputDir))

# set startDate
if startDate is None:
    startyear = 1950
    startmonth = 1
    startday = 1
else:
    dateList = startDate.split('/')
    if len(dateList) != 3:
        print('--startDate must be in the form MM/DD/YYYY: ' + str(startDate))
        sys.exit(0)
    startmonth = int(dateList[0])
    startday = int(dateList[1])
    startyear = int(dateList[2])
    if startmonth < 1 or startmonth > 12 or startday < 1 or startday > 31:
        print('--startDate must be in the form MM/DD/YYYY: ' + str(startDate))
        sys.exit(0)
    try:
        datetime.datetime(startyear, startmonth, startday)
    except:
        print('Invalid startDate <%s>' % (str(startDate)))
        sys.exit(0)

# set endDate
if endDate is None:
    # chose one year from today
    nextYear = time.time() + 365*24*60*60
    nextYear = time.gmtime(nextYear)
    endyear = nextYear[0]
    endmonth = nextYear[1]
    endday = nextYear[2]
else:
    dateList = endDate.split('/')
    if len(dateList) != 3:
        print('--endDate must be in the form MM/DD/YYYY: ' + str(endDate))
        sys.exit(0)
    endmonth = int(dateList[0])
    endday = int(dateList[1])
    endyear = int(dateList[2])
    if endmonth < 1 or endmonth > 12 or endday < 1 or endday > 31:
        print('--endDate must be in the form MM/DD/YYYY: ' + str(endDate))
        sys.exit(0)
    try:
        datetime.datetime(endyear, endmonth, endday)
    except:
        print('Invalid endDate <%s>' % (str(endDate)))
        sys.exit(0)

timeList = (startyear, startmonth, startday, 0, 0, 0,
            endyear, endmonth, endday, 23, 59, 59)
    

# verify the url is valid
server = madrigalWeb.madrigalWeb.MadrigalData(url)

# now, create a list of instrument codes desired from the inst argument
instList = getInstrumentList(inst, server)

# get the list of all experiments for the given instruments and time range
expList = server.getExperiments(instList,
                                startyear,
                                startmonth,
                                startday,
                                0,
                                0,
                                0,
                                endyear,
                                endmonth,
                                endday,
                                23,
                                59,
                                59)

expList.sort()

# filter experiments using seasonal filter if needed
if seasonalStartDate != '01/01' or seasonalEndDate != '12/31':
    expList = filterExperimentsUsingSeason(expList, seasonalStartDate, seasonalEndDate)

# filter experiments using expName if needed
if expName is not None:
    expList = filterExperimentsUsingExpName(expList, expName)
    
# exclude experiments using expName if needed
if excludeExpName is not None:
    expList = excludeExperimentsUsingExpName(expList, excludeExpName)

# get list of all experiment files given the expList
expFileList = getExperimentFileList(server, expList, includeNonDefault, verbose)


# filter expFileList using kindat filter if needed
if kindat != '0':
    expFileList = filterExperimentFilesUsingKindat(expFileList, kindat)
    
# filter expFileList using fileDesc filter if needed
if fileDesc is not None:
    expFileList = filterExperimentFilesUsingFileDesc(expFileList, fileDesc)

# print error if no files selected
if len(expFileList) == 0:
    print('No files selected with these arguments')
    sys.exit(0)

# print message if verbose
numFiles = len(expFileList)
if verbose:
    print("%i files being downloaded" % (numFiles))

# loop through each file to download
for i in range(numFiles):
    if verbose:
        print('Downloading file %i of %i: %s' % (i+1, numFiles, expFileList[i].name))
    if tree:
        subDir = getSubdirectoryFromFullFile(expFileList[i].name)
        saveDir = os.path.join(outputDir, subDir)
        try:
            os.makedirs(saveDir)
        except:
            pass
    else:
        saveDir = outputDir
    basename = os.path.basename(expFileList[i].name)
    if format == 'simple' and basename[-4:] != '.txt':
        basename += '.txt'
    elif format == 'hdf5' and basename[-5:] != '.hdf5':
        basename += '.hdf5'
    saveName = os.path.join(saveDir, basename)
    # make sure the file name is unique
    if os.access(saveName, os.R_OK):
        # add number
        count = 1
        while(True):
            newName = saveName[0:saveName.rfind('.')] + '_%i' % (count-1) + saveName[saveName.rfind('.'):]
            if not os.access(newName, os.R_OK):
                saveName = newName
                break
            else:
                count += 1

    time.sleep(0.5)
    try:
        server.downloadFile(expFileList[i].name, saveName,
                            user_fullname, user_email, user_affiliation,
                            format)
        # check that final file is not empty
        if os.path.getsize(saveName) == 0:
            if verbose:
                print(f"Downloaded file {saveName} is empty, removing..")
            os.system(f"rm {saveName}")
        
        # success
        if verbose:
            print(f"Downloaded file {saveName}")
    except socket.timeout:
        print(('Failure downloading %s because it took more than allowed number of seconds' % (expFileList[i].name)))

