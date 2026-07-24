# globalCitation.py

#### globalCitation.py creates a permenant citation to a group of Madrigal files.

Usage:
```
globalCitation.py  --user_fullname= --user_email= 
            --user_affiliation= --startDate=  --endDate= 
            inst=instrument list [options]

        where:

        --user_fullname= - the full user name (in quotes unless your name is
                                          Sting or Madonna)

        --user_email=

        --user_affiliation= - user affiliation.  Use quotes if it contains spaces.

        --startDate= - start date to filter experiments before.  Defaults to allow all experiments.

        --endDate= - end date to filter experiments after.  Defaults to allow all experiments.

        --inst= - comma separated list of instrument codes or names.  See Madrigal documentation
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

        --kindat= - comma separated list of kind of data codes.  See Madrigal documentation
                                       for this list.  Defaults to allow all kinds of data.  If names are given, the
                                       argument must be enclosed in double quotes.  An asterick will perform matching as
                                       in glob. Examples: (--kindat=3001,13201 or 
                                       --kindat="INSCAL Basic Derived Parameters,*efwind*,2001")


        --seasonalStartDate= - seasonal start date to filter experiments before.  Use this to select only part of the
                                year to collect data.  Defaults to Jan 1.  Example:
                                (--seasonalStartDate=07/01) would only allow experiments after July 1st from each year.

        
        --seasonalEndDate= - seasonal end date to filter experiments after.  Use this to select only part of the
                                    year to collect data.  Defaults to Dec 31.  Example: 
                                    (--seasonalEndDate=10/31) would only allow experiments before Oct 31 of each year.

        --includeNonDefault - if given, include realtime files when there are no default.  Default is to search only default files.  

        --dateList= - comma separated list of date strings in the form YYYY-MM-DD, to get experiments for 
                                a list of discrete days. Must include startDate and endDate. 
```