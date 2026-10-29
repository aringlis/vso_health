#!/usr/local/bin/python3

import numpy as np
import glob
import sys
import datetime
sys.path.append('/home/ainglis/vso_health/')
from query_vso_health import create_master_status_file, cleanup_query_files
from query_vso_health import create_missing_health_check, verify_todays_health_check_exists
from vso_bokeh_plotting import vso_health_bokeh_plot
from vso_report_helpers import percent_good, sources_with_problems
from plot_performance import vso_quadrant_chart

# create the updated master status file
df_master = create_master_status_file(idl = True)

# use the master status file to create a dynamic html plot
vso_health_bokeh_plot(idl = True)

# create the percent good text files
idl_files = glob.glob('/home/ainglis/vso_health/vso_health_idl_version/vso_health_checks_idl/*')
fname = np.sort(idl_files)[-1]
percent_good(fname, idl=True)
sources_with_problems(fname,idl=True)
vso_quadrant_chart()

