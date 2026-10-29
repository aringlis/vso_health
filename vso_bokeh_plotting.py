import os
import pandas as pd
import numpy as np
import datetime
import platform
import sunpy
from bokeh.io import output_file, show, export_png 
from bokeh.models import (BasicTicker, ColorBar, ColumnDataSource, 
                            LinearColorMapper, PrintfTickFormatter)
from bokeh.models import Legend, Title
from bokeh.plotting import figure  
from bokeh.transform import transform, factor_cmap 

from html2image import Html2Image


data_path = os.path.expanduser(os.path.expanduser('~/vso_health/'))

def vso_health_bokeh_plot(idl = None):

# Sources we no longer test; hidden from the plot but kept in the master CSV.
    RETIRED_SOURCES = [
    'SFO/SFO/CFDT1',
    'SFO/SFO/CFDT2',
    'ESA/Proba2/LYRA',
    'ESA/Proba2/SWAP',
    'OMP/OMP/CLIMSO',
    'ROB/PROBA2/SWAP'
    ]


    if idl:
        output_file(os.path.join(data_path,"vso_source_health_summary_idl.html"),'VSO health summary (IDL)')
        df = pd.read_csv(os.path.join(data_path,'vso_health_status_master_record_idl.csv'))
        png_outfilename = 'vso_source_health_summary_idl.png'
        ssw_path = '/service/solarsoft/'
        ssw_last_update = os.path.getmtime(os.path.join(ssw_path,'gen/setup/ssw_map.dat'))
        ssw_last_update_date = datetime.datetime.fromtimestamp(ssw_last_update).date().strftime('%Y-%m-%d')
    else:    
        output_file(os.path.join(data_path,"vso_source_health_summary_python.html"),'VSO health summary')
        df = pd.read_csv(os.path.join(data_path,'vso_health_status_master_record.csv'))
        png_outfilename = 'vso_source_health_summary_python.png'
    
    # truncate to the last 30 entries only
    if len(df.columns) < 35:
        df2 = df[df.columns[3:]]
    else:
        df2 = df[df.columns[-30:]]

    
    #get thet time of the latest data in the file
    latest_data_time = datetime.datetime.strptime(df.columns[-1],'%Y%m%d_%H%M%S')

    #re-cast the Instrument column so that it includes Provider/Source info as well
    newnames = []
    for i, item in df.iterrows(): 
        newnames.append(item['Provider'] + '/' + item['Source'] + '/' + item['Instrument']) 
    df2['Instrument'] = newnames

    #drop the retired sources from display
    unknown = set(RETIRED_SOURCES) - set(df2['Instrument'])
    if unknown:
        print('Warning: RETIRED_SOURCES entries not found in data:', sorted(unknown))
    df2 = df2[~df2['Instrument'].isin(RETIRED_SOURCES)]

    #manipulate dataframe into right format
 #   df2.columns.name = 'Time' 
  #  df2.set_index('Instrument',inplace=True)
   # df3 = pd.DataFrame(df2.stack(dropna=False), columns=['Health_value']).reset_index()
   # df4 = df3.copy()
   # df4['Label'] = 'None'

    #create another column with more descriptive labels for the legend
    #should be a more efficient way to do this
   ## label_list = []
   # for i, r in df3.iterrows():
    #    if r['Health_value'] == 0: 
     #       label_list.append('Status: 0 (Pass)') 
      #  elif r['Health_value'] == 1: 
      #      label_list.append('Status: 1 (Pass on known query)') 
      #  elif r['Health_value'] == 2: 
       #     label_list.append('Status: 2 (Skipped)') 
      #  elif r['Health_value'] == 8: 
       #     label_list.append('Status: 8 (Fail on download)') 
       # elif r['Health_value'] == 9: 
       ##     label_list.append('Status: 9 (Fail, no response/no data)')
      #  elif r['Health_value'] == 10:
       #     label_list.append('Status: 10 (Fail, other)')
       # elif np.isnan(r['Health_value']):
        #    label_list.append('N/A') 
    #df4['Label'] = label_list

    STATUS_LABELS = {
    0:  'Status: 0 (Pass)',
    1:  'Status: 1 (Pass on known query)',
    2:  'Status: 2 (Skipped)',
    8:  'Status: 8 (Fail on download)',
    9:  'Status: 9 (Fail, no response/no data)',
    10: 'Status: 10 (Fail, other)',
        }

    # reshape to long format: one row per (Instrument, Time)
    df4 = (df2.set_index('Instrument').rename_axis(columns='Time').stack(dropna=False)
               .rename('Health_value').reset_index())

    # descriptive legend labels; anything not in the dict (including NaN) becomes 'N/A'
    df4['Label'] = df4['Health_value'].map(STATUS_LABELS).fillna('N/A')

    # Claude stuff: query times: same rows/columns as the master file, in a parallel CSV
    qt_name = ('vso_health_status_master_record_idl_querytimes.csv' if idl
               else 'vso_health_status_master_record_querytimes.csv')
    qt_path = os.path.join(data_path, qt_name)

    if os.path.exists(qt_path):
        qt = pd.read_csv(qt_path)
        qt['Instrument'] = qt['Provider'] + '/' + qt['Source'] + '/' + qt['Instrument']

        # use exactly the same run columns as the status plot
        run_cols = [c for c in df2.columns if c != 'Instrument']
        qt_long = (qt.set_index('Instrument')
                     .reindex(columns=run_cols)
                     .rename_axis(columns='Time')
                     .stack(dropna=False)
                     .rename('query_times')
                     .reset_index())

        df4 = df4.merge(qt_long, on=['Instrument', 'Time'], how='left')
        df4['query_times'] = df4['query_times'].astype(object).fillna('N/A')
    else:
        print('Warning: query times file not found:', qt_path)
        df4['query_times'] = 'N/A'
    

    #create the bokeh plot
    p = figure(width=1400,height=1500,x_range=list(df4['Time'].unique()), y_range=list(reversed(df4['Instrument'].unique()) ),
                   tools = 'hover', tooltips = [('Time','@Time'), ('Instrument','@Instrument'),('Status','@Health_value'),
                   ('Query time','@query_times')])

    if idl:
        p.title.text = ' VSO source health status (IDL): Latest data ' + datetime.datetime.strftime(latest_data_time, "%Y-%m-%d %H:%M" + ' UT')
        #p.title.text = ' VSO source health status (IDL): Generated at ' + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M" + ' UT')
        p.add_layout(Title(text="Report generated at "+ datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M" + ' UT')
                               + '.                  SSW last update ' + ssw_last_update_date
                               + '                   Sources tested: ' + str(len(df4['Instrument'].unique())),text_font_size="10pt", text_font_style="italic"), 'above')
    else:
        p.title.text = ' VSO source health status (Python): Latest data ' + datetime.datetime.strftime(latest_data_time, "%Y-%m-%d %H:%M" + ' UT')
        #p.title.text = ' VSO source health status (Python): Generated at ' + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M" + ' UT')
        p.add_layout(Title(text="Report generated at "+ datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M" + ' UT')
                               + '.                    Python version ' + platform.python_version() + '. SunPy version ' + sunpy.__version__
                               + '                     Sources tested: ' + str(len(df4['Instrument'].unique())),text_font_size="10pt", text_font_style="italic"), 'above')

    #p.add_layout(Title(text="Report generated at "+ datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M" + ' UT'), text_font_size="10pt", text_font_style="italic"), 'above')
    p.add_layout(Legend(), 'right')
    p.title.text_font_size = '16pt'    
    
    #define the color map for the plot
    colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    mapper = LinearColorMapper(palette=colors, low=df4.Health_value.min(), high=df4.Health_value.max())

    colors2 = ['seagreen','mediumseagreen','gold','gold','red','red','red','red','orangered','firebrick']
    mapper2 = LinearColorMapper(palette = colors2, low=df4.Health_value.min(), high=df4.Health_value.max())

    

    p.rect(x = 'Time', y = 'Instrument', width=1, height=1, source = df4.sort_values('Health_value', kind = 'stable'), line_color='black', 
               fill_color = transform('Health_value', mapper2), legend_field = 'Label')#'Health_value')

    p.xaxis.major_label_orientation = np.pi/4#'vertical'
    p.legend.location = 'center_right'
    show(p)
    export_png(p, filename = png_outfilename)
    


def convert_html_to_png():

    hti = Html2Image(output_path = data_path)

    input_file = os.path.join(data_path,"vso_source_health_summary.html")
    
    hti.screenshot(
        html_file=input_file,
        save_as="vso_source_health_summary.png",
        size=(1370, 1420)
        )
