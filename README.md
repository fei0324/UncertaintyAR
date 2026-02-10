# Topological Characterization and Uncertainty Visualization of Atmospheric Rivers

This repository contains the code associated with the paper  
Lan, F., Gamelin, B., Yan, L., Wang, J., Wang, B. and Guo, H. (2024), Topological Characterization and Uncertainty Visualization of Atmospheric Rivers. Computer Graphics Forum, 43: e15084. https://doi.org/10.1111/cgf.15084

## Installation:

This codebase was tested on **ParaView 5.10.0** with python 3.9.

Many scripts require the **ParaView** and must be executed using `pvpython`. Please make sure that ParaView is installed and it's added to your environment path.


## Dependencies:

The core Python dependencies are:
    + `python=3.9`
    + `numpy`
    + `matplotlib`
    + `networkx`
    + `vtk`
    + `scipy`
    + `alphashape`
    + `shapely`
    + `seaborn`
    + `seaborn-image`

## MetroSet Demo

### Catalog data

The folder `Algorithms/` folder contains AR catalog data from all the AR detection tools for a single time step: **January 8, 2017 at 12:00 pm**. We have 6 hourly data for each algorithm.

Only the `ARCatalog` subfolders are included in this repository. Other intermediate outputs are intentionally excluded due to the size.

### AR identfication

Each AR detection tool may detect multiple ARs at a given time step and all of them are provided by the AR catalog data. The file `demo/2017_7_2.json` specifies the ID of the AR we are interested in for each algorithm. This information is stored in the field `day_hour_num` in the json file as a tuple: `(day_of_year, hour_of_day, AR_ID)`. Both the day of the year and the hour of the day starts from 0. For example, (7, 2, 8) in year 2017 for the `ar_connect` ARDT corresponds to: 
+ AR ID number 8
+ January 8, 2017
+ 12:00 pm

### Background image for MetroSet visualization
The background of the MetroSet is created by visualizing the ivt file in the directory MERRA2IVT and the coastline file. The image of entire globe was cropped to show the region of the AR of interest. The cropped background image is saved as demo/2017_7_2.png

### Creating MetroSet visualization:

**Step 1: Generate individual AR skeletons**

Run the following command:
```bash
$ python processFromJSON.py demo/2017_7_2.json [persistence_threshold]
```

In the paper, we used a very high persistence threshold of 30 to eliminate small branches in the AR structure. This threshold can be changed and the program will automatically compute new critiple points files and morse complex files using the MERRA2 integrated vapor transport (IVT) data stored in the `MERRA2IVT` directory. These generated files are saved under the directory `MSCData`.

The program will run through all the ARs at this specific time step indicated in the json file and create two types of intermediate files.
+ AR skeleton and AR axis: both will be saved under `Algorithms/[algo_name]/GraphAxis` folder
+ Intermediate files including alpha shapes, AR critical points, and morse complex subset: these will be saved under `Algorithms/[algo_name]/IntermediateFiles`

These folders are not included in the github repo due to size constraints.

After the program finish running, we are ready to create the metroset visualization. 

**Step 2: create the metroset uncertainty visualization**

Input command:
```bash
$ python getMetroSet.py
```

The final figure is saved under `figures/metrosets/`

## Contour boxplot demo:
+ Generate contour boxplot data using the function drawContourBoxplot() from getContourBoxplot.py
+ Create the contour boxplot plot by running the rest of the getContourBoxplot.py file. Change `data_dir` to your data directory from the data you just generated.