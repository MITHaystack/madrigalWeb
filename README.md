# MadrigalWeb - a python API to access the Madrigal database

MadrigalWeb is a pure python module to access data from any Madrigal database.  For documentation and examples go to any Madrigal site such as 
<https://cedar.openmadrigal.org>

The easiest way to use the Madrigal python remote data access API is to simply let the [web interface](https://cedar.openmadrigal.org/chooseScript) generate the command you need. 

### Installing MadrigalWeb

You need to install the madrigalWeb python package first. You can do that with 
```pip install madrigalweb```
or you can download the source [here](https://cedar.openmadrigal.org/madrigalDownload).

### MadrigalWeb command generator

When using the command generator, be sure to select python as the language you want to create the command with. You can choose to download files as they are in Madrigal in either column-delimited ascii, Hdf5, or netCDF4 formats, or you can choose the parameters yourself (including derived parameters), and optionally include filters on the data you get back.

This web interface will generate python commands using one of the following two Python scripts: [globalDownload.py](gd.md) and [globalIsprint.py](gi.md). Use globalDownload.py if you want data **as it is** in Madrigal. Use globalIsprint.py to **choose parameters and/or filters**. You can also create a permanent citation to a group of Madrigal files with [globalCitation.py](gc.md).

### Rules-of-the-Road

Use of Madrigal data is generally subject to the CEDAR Rules-of-the-Road . Prior permission to access the data is not required. However, the user is required to establish early contact with any organization whose data are involved in the project to discuss the intended usage. Data are often subject to limitations which are not immediately evident to new users. Before they are formally submitted, draft copies of all reports and publications must be sent to the contact scientist at all data-supplying organizations along with an offer of co-authorship to scientists who have provided data. This offer may be declined. The Database and the organizations that contributed data must be acknowledged in all reports and publications, and whenever this data is made available through another database. 

For questions or comments, contact [the Madrigal admin](mailto:haystack-madrigal-admin@mit.edu).

### Contributing
##### [madrigalWeb Github](https://github.com/MITHaystack/madrigalWeb)
We encourage all contributions. If you have a problem with the code or would like to see a new feature, please open an issue or send us an email. Or you can submit a pull request.