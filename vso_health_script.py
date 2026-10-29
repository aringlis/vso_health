#!/usr/local/bin/python3

from query_vso_health import query_vso_providers, create_master_status_file, cleanup_query_files, verify_todays_health_check_exists
from query_vso_health import create_missing_health_check
from vso_bokeh_plotting import vso_health_bokeh_plot, convert_html_to_png
#from vso_report_helpers import generate_report
from vso_report_helpers import percent_good, sources_with_problems
from plot_performance import plot_performance, percent_good_histogram
import datetime
import os

# instruments in the skip list will not be tested
skiplist = ['KIS/ChroTel/ChroTel','NGDC/GOES-12/SXI-0','OVRO/OVRO/OVSA']

# query each of the instruments supported by the VSO in turn
flags, fname = query_vso_providers(skip_download = False, skip_list = skiplist, test_known_queries = False)

# create the updated master status file
df_master = create_master_status_file()

# use the master status file to create a dynamic html plot
vso_health_bokeh_plot()

# write out the percent txt files
percent_good(fname)
sources_with_problems(fname)

cleanup_query_files()

plot_performance()
plot_performance(idl=True)
percent_good_histogram()
percent_good_histogram(idl=True)

