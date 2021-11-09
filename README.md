# Summary

This repository contains tools designed to test the health of the data services provided by the Virtual Solar Observatory (VSO).

## Basic procedure

When run, these tools generate a test query to each of the data sources supported by the VSO, asking for data within the start and end times of data service for that data source. A status code is generated describing the outcome of each request. These results are saved to a summary file. Plots are also generated to visualize the result.

These tools are currently being run daily on the full list of VSO-supported data sources. Visualizations and logs can be found [here](https://aringlis.github.io/vso_health/).
