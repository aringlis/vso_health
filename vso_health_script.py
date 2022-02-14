
from query_vso_health import query_vso_providers, create_master_status_file
from vso_bokeh_plotting import vso_health_bokeh_plot
from vso_report_helpers import generate_report

# instruments in the skip list will not be tested
skiplist = ['K-Cor','chp','dpm','mk4','cp','ChroTel','CAII','FILM',
                'HA2','KPDC','PHOKA','TM-1001','TM-1010','BCS','HXT','SXT','WBS','XRT']

# query each of the instruments supported by the VSO in turn
flags, fname = query_vso_providers(skip_download = False, skip_list = skiplist)

# create the updated master status file
df_master, df = create_master_status_file()

# use the master status file to create a dynamic html plot
vso_health_bokeh_plot()

# generate a report of the latest VSO health check
report_fname = generate_report(fname)



