# MadrigalWeb API Reference

The easiest way to use the Madrigal python remote data access API is to simply let the [web interface](https://cedar.openmadrigal.org/chooseScript) generate the command you need. 

You need to install the madrigalWeb python package first. You can do that with 
```pip install madrigalweb```
or you can download the source [here](https://cedar.openmadrigal.org/madrigalDownload).

When using the command generator, be sure to select python as the language you want to create the command with. You can choose to download files as they are in Madrigal in either column-delimited ascii, Hdf5, or netCDF4 formats, or you can choose the parameters yourself (including derived parameters), and optionally include filters on the data you get back.

The rest of this reference page is for those who want to go beyond the automatically generated commands and write more advanced python applications that access Madrigal data.

This page pulls additional documentation directly from the source code.

::: madrigalWeb.madrigalWeb.MadrigalData
    options:
      docstring_style: numpy
      docstring_section_style: table
      filters: ["!__get",]
      heading: "MadrigalData"
      heading_level: 2

::: madrigalWeb.madrigalWeb.MadrigalExperiment
    options:
      docstring_style: numpy
      filters: ["!_",]
      heading: "MadrigalExperiment"
      heading_level: 2

::: madrigalWeb.madrigalWeb.MadrigalExperimentFile
    options:
      docstring_style: numpy
      filters: ["!_",]
      heading: "MadrigalExperimentFile"
      heading_level: 2

::: madrigalWeb.madrigalWeb.MadrigalInstrument
    options:
      docstring_style: numpy
      filters: ["!_",]
      heading: "MadrigalInstrument"
      heading_level: 2

::: madrigalWeb.madrigalWeb.MadrigalParameter
    options:
      docstring_style: numpy
      filters: ["!_",]
      heading: "MadrigalParameter"
      heading_level: 2