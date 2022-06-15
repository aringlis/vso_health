#!/usr/local/bin/python3

from query_vso_health import query_vso_providers, create_master_status_file, cleanup_query_files
from vso_bokeh_plotting import vso_health_bokeh_plot, convert_html_to_png
#from vso_report_helpers import generate_report
from vso_report_helpers import percent_good
from plot_performance import plot_performance

# instruments in the skip list will not be tested
skiplist = ['K-Cor','chp','dpm','mk4','cp','ChroTel','BCS','HXT','SXT','WBS','XRT','CFDT1','CFDT2']

# query each of the instruments supported by the VSO in turn
flags, fname = query_vso_providers(skip_download = False, skip_list = skiplist)

# create the updated master status file
df_master, df = create_master_status_file()

# use the master status file to create a dynamic html plot
vso_health_bokeh_plot()
#convert_html_to_png()

# write out the percent txt files
percent_good(fname)

cleanup_query_files()

plot_performance()
