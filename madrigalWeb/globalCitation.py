#!python

"""This script runs a global search through Madrigal data, and returns a citation to the group of files

    This script is a stand-alone application, and can be run from anywhere with a connection to the internet.
    It runs on either unix or windows.  It requires only the MadrigalWeb python module to be installed.

$Id: globalCitation.py 7240 2020-10-02 20:05:22Z brideout $
"""

usage = """
        Usage:

        globalCitation.py  --user_fullname=<user fullname> --user_email=<user email> \
            --user_affiliation=<user affiliation> --startDate=<YYYY-MM-DD>  --endDate=<YYYY-MM-DD> \
            inst=instrument list> [options]

        where:

        --user_fullname=<user fullname> - the full user name (probably in quotes unless your name is
                                          Sting or Madonna)

        --user_email=<user email>

        --user_affiliation=<user affiliation> - user affiliation.  Use quotes if it contains spaces.

        --startDate=<YYYY-MM-DD> - start date to filter experiments before.  Defaults to allow all experiments.

        --endDate=<YYYY-MM-DD> - end date to filter experiments after.  Defaults to allow all experiments.

        --inst=<instrument list> - comma separated list of instrument codes or names.  See Madrigal documentation
                                   for this list.  Defaults to allow all instruments. If names are given, the
                                   argument must be enclosed in double quotes.  An asterick will perform matching as
                                   in glob.  Examples: (--inst=10,30 or --inst="Jicamarca IS Radar,Arecibo*")
                                   
        and options are:
        

        --expName  - filter experiments by the experiment name.  Give all or part of the experiment name. Matching
                     is case insensitive and fnmatch characters * and ? are allowed.  Default is no filtering by 
                     experiment name.
                     
        --excludeExpName - exclude experiments by the experiment name.  Give all or part of the experiment name. Matching
                     is case insensitive and fnmatch characters * and ? are allowed.  Default is no excluding experiments by 
                     experiment name.
                     
        --fileDesc - filter files by their file description string. Give all or part of the file description string. Matching
                     is case insensitive and fnmatch characters * and ? are allowed.  Default is no filtering by 
                     file description.

        --kindat=<kind of data list> - comma separated list of kind of data codes.  See Madrigal documentation
                                       for this list.  Defaults to allow all kinds of data.  If names are given, the
                                       argument must be enclosed in double quotes.  An asterick will perform matching as
                                       in glob. Examples: (--kindat=3001,13201 or 
                                       --kindat="INSCAL Basic Derived Parameters,*efwind*,2001")


        --seasonalStartDate=<MM/DD> - seasonal start date to filter experiments before.  Use this to select only part of the
                                year to collect data.  Defaults to Jan 1.  Example:
                                (--seasonalStartDate=07/01) would only allow experiments after July 1st from each year.

        
        --seasonalEndDate=<MM/DD> - seasonal end date to filter experiments after.  Use this to select only part of the
                                    year to collect data.  Defaults to Dec 31.  Example: 
                                    (--seasonalEndDate=10/31) would only allow experiments before Oct 31 of each year.

        --includeNonDefault - if given, include realtime files when there are no default.  Default is to search only default files.   


        --dateList=<date list> - comma separated list of date strings in the form YYYY-MM-DD, to get experiments for 
                                a list of discrete days. Must include startDate and endDate.                    
"""

import argparse
import sys
import traceback
import datetime

import madrigalWeb.madrigalWeb

# parse command line
parser = argparse.ArgumentParser(
        description='Run a global search through Madrigal data, and returns a citation to the group of files.',
        usage=usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
# Required arguments
parser.add_argument('--user_fullname', required=True, help='Full user name (quoted if contains spaces)')
parser.add_argument('--user_email', required=True, help='User email address')
parser.add_argument('--user_affiliation', required=True, help='User affiliation (quoted if contains spaces)')
parser.add_argument('--startDate', help='Start date in YYYY-MM-DD format to filter experiments before.  Defaults to allow all experiments.')
parser.add_argument('--endDate', help='End date in YYYY-MM-DD format to filter experiments after.  Defaults to allow all experiments.')
parser.add_argument('--inst', default=None, help='Comma separated list of instrument codes or names. See Madrigal documentation \
                                   for this list.  Defaults to allow all instruments. If names are given, the \
                                   argument must be enclosed in double quotes.  An asterisk will perform matching as \
                                   in glob.')
    
# Optional arguments
parser.add_argument('--kindat', default=None, help='Comma separated list of kind of data codes. See Madrigal documentation \
                                       for this list.  Defaults to allow all kinds of data.  If names are given, the \
                                       argument must be enclosed in double quotes.  An asterisk will perform matching as \
                                       in glob.')
parser.add_argument('--seasonalStartDate', type=str, default='01/01', help='Seasonal start date in MM/DD format to filter experiments before.  Use this to select only part of the \
                                year to collect data.  Defaults to Jan 1.')
parser.add_argument('--seasonalEndDate', type=str, default='12/31', help='Seasonal end date in MM/DD format to filter experiments after.  Use this to select only part of the \
                                    year to collect data.  Defaults to Dec 31.')
parser.add_argument('--includeNonDefault', action='store_true', help='Include realtime files when no default')
parser.add_argument('--expName', type=str, help='Filter experiments by experiment name. Give all or part of the experiment name. Matching \
                     is case insensitive and fnmatch characters * and ? are allowed.')
parser.add_argument('--excludeExpName', type=str, help='Exclude experiments by experiment name. Give all or part of the experiment name. Matching \
                     is case insensitive and fnmatch characters * and ? are allowed.')
parser.add_argument('--fileDesc', type=str, help='Filter files by file description string. Give all or part of the file description string. Matching \
                     is case insensitive and fnmatch characters * and ? are allowed.')
parser.add_argument('--dateList', help="comma separated list of date strings in the form YYYY-MM-DD, to get experiments for \
                                a list of discrete days. Must include startDate and endDate. ")
    
args = parser.parse_args()

# Validate and convert dates
try:
    args.startDate = datetime.datetime.strptime(args.startDate, '%Y-%m-%d')
except Exception:
    traceback.print_exc()
    parser.error('startDate must be in format YYYY-MM-DD')

try:
    args.endDate = datetime.datetime.strptime(args.endDate, '%Y-%m-%d')
except Exception:
    traceback.print_exc()
    parser.error('endDate must be in format YYYY-MM-DD')

# Split comma separated lists into Python lists if provided
args.inst = [item.strip() for item in args.inst.split(',')]

if args.kindat:
    args.kindat = [item.strip() for item in args.kindat.split(',')]

if args.dateList:
    args.dateList = [datetime.datetime.strptime(item.strip(), '%Y-%m-%d') for item in args.dateList.split(',')]

# set default values
user_fullname=args.user_fullname
user_email=args.user_email
user_affiliation=args.user_affiliation
startDate = args.startDate
endDate = args.endDate
inst = args.inst
kindat = args.kindat
seasonalStartDate = args.seasonalStartDate
seasonalEndDate = args.seasonalEndDate
includeNonDefault = args.includeNonDefault
skipVerification = False
expName = args.expName
excludeExpName = args.excludeExpName
fileDesc = args.fileDesc
dateList = args.dateList

# verify the url is valid
server = madrigalWeb.madrigalWeb.MadrigalData('https://cedar.openmadrigal.org')

citationList = server.getCitationListFromFilters(startDate, endDate, inst, kindat, 
                                                 seasonalStartDate, seasonalEndDate, 
                                                 includeNonDefault, expName, excludeExpName, 
                                                 fileDesc, dateList)

print('\nThe following file citations will be in this group citation:\n')
for citation in citationList:
    print(citation)
    
if not skipVerification:
    print('\nAre you sure you want to create a permanent citation to this group of files? (y/n)')
    verify = input()
    if verify.lower() != 'y':
        print('Citation not created.')
        sys.exit(-1)
        
citation = server.createCitationGroupFromList(citationList, user_fullname, user_email, user_affiliation)

print('Created group citation: %s' % (citation))
        
    





