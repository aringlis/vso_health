
from query_vso_health import query_vso_providers, create_master_status_file
from vso_bokeh_plotting import vso_health_bokeh_plot


flags = query_vso_providers(skip_download = False)

df_master, df = create_master_status_file()

vso_health_bokeh_plot()

