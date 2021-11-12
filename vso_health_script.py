
from query_vso_health import query_vso_providers, create_master_status_file
from vso_bokeh_plotting import vso_health_bokeh_plot

skiplist = ['K-Cor','chp','dpm','mk4','cp','ChroTel','CAII','FILM',
                'HA2','KPDC','PHOKA','TM-1001','TM-1010','BCS','HXT','SXT','WBS','XRT']

flags = query_vso_providers(skip_download = False, skip_list = skiplist)

df_master, df = create_master_status_file()

vso_health_bokeh_plot()

