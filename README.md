# madrigalWeb - a python API to access the Madrigal database

madrigalWeb is a pure python module to access data from any Madrigal database.  For documentation and examples go to any Madrigal site such as 
http://cedar.openmadrigal.org

The easiest way to use the Madrigal python remote data access API is to simply let the web interface write the script you need for you. Just choose the *Access data* pull-down menu and choose *Create a command to download multiple exps*. Then follow the instructions, and you will have the command you need to download whatever you want from Madrigal. Be sure to select python as the language you want to create the command with. You can choose to download files as they are in Madrigal in either column-delimited ascii, Hdf5, or netCDF4 formats, or you can choose the parameters yourself (including derived parameters), and optionally include filters on the data you get back.

This web interface will generate python commands using one of the following two Python scripts: globalDownload.py and globalIsprint.py. Use globalDownload.py if you want data as it is in Madrigal. Use globalIsprint.py to choose parameters and/or filters. These two scripts are documented below, for those who do not want to use the web interface to generate the needed arguments:

See the online documentation for the script globalCitation.py. This script is used to create a permanent citation to a group of Madrigal files.

For questions or comments, contact Bill Rideout at brideout@mit.edu or Katherine Cariglia at cariglia@mit.edu