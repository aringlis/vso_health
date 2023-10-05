import os
import pandas as pd
import numpy as np
import datetime
from bokeh.io import output_file, show, export_png 
from bokeh.models import (BasicTicker, ColorBar, ColumnDataSource, 
                            LinearColorMapper, PrintfTickFormatter)
from bokeh.models import Legend
from bokeh.plotting import figure  
from bokeh.transform import transform, factor_cmap 

from html2image import Html2Image


data_path = os.path.expanduser(os.path.expanduser('~/vso_health/'))

def vso_health_bokeh_plot(idl = None):

    if idl:
        output_file(os.path.join(data_path,"vso_source_health_summary_idl.html"),'VSO health summary (IDL)')
        df = pd.read_csv(os.path.join(data_path,'vso_health_status_master_record_idl.csv'))
        png_outfilename = 'vso_source_health_summary_idl.png'
    else:    
        output_file(os.path.join(data_path,"vso_source_health_summary_python.html"),'VSO health summary')
        df = pd.read_csv(os.path.join(data_path,'vso_health_status_master_record.csv'))
        png_outfilename = 'vso_source_health_summary_python.png'
    
    # truncate to the last 30 entries only
    if len(df.columns) < 35:
        df2 = df[df.columns[3:]]
    else:
        df2 = df[df.columns[-30:]]

    #re-cast the Instrument column so that it includes Provider/Source info as well
    newnames = []
    for i, item in df.iterrows(): 
        newnames.append(item['Provider'] + '/' + item['Source'] + '/' + item['Instrument']) 
    df2['Instrument'] = newnames

    #manipulate dataframe into right format
    df2.columns.name = 'Time' 
    df2.set_index('Instrument',inplace=True)
    df3 = pd.DataFrame(df2.stack(dropna=False), columns=['Health_value']).reset_index()
    df4 = df3.copy()
    df4['Label'] = 'None'

    #create another column with more descriptive labels for the legend
    #should be a more efficient way to do this
    label_list = []
    for i, r in df3.iterrows():
        if r['Health_value'] == 0: 
            label_list.append('Status: 0 (Pass)') 
        elif r['Health_value'] == 1: 
            label_list.append('Status: 1 (Pass on known query)') 
        elif r['Health_value'] == 2: 
            label_list.append('Status: 2 (Skipped)') 
        elif r['Health_value'] == 8: 
            label_list.append('Status: 8 (Fail on download)') 
        elif r['Health_value'] == 9: 
            label_list.append('Status: 9 (Fail, no response/no data)')
        elif np.isnan(r['Health_value']):
            label_list.append('N/A') 
    df4['Label'] = label_list
    
    #convert times to datetime format
   # tims = []
    #for e in df3['Time']:
     #   tims.append(datetime.datetime.strptime(df3['Time'][0],'%Y%m%d_%H%M%S'))
    #df3['Time'] = tims

    #create the bokeh plot
    p = figure(width=1400,height=1400,x_range=list(df4['Time'].unique()), y_range=list(reversed(df4['Instrument'].unique()) ),
                   tools = 'hover', tooltips = [('Time','@Time'), ('Instrument','@Instrument'),('Status','@Health_value')])

    if idl:
        p.title.text = ' VSO source health status (IDL): Generated at ' + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M" + ' UT')
    else:
        p.title.text = ' VSO source health status (Python): Generated at ' + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M" + ' UT')
    p.add_layout(Legend(), 'right')
    p.title.text_font_size = '16pt'    
    
    #define the color map for the plot
    colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    mapper = LinearColorMapper(palette=colors, low=df4.Health_value.min(), high=df4.Health_value.max())

    colors2 = ['seagreen','mediumseagreen','gold','gold','red','red','red','red','orangered','firebrick']
    mapper2 = LinearColorMapper(palette = colors2, low=df4.Health_value.min(), high=df4.Health_value.max())

    

    p.rect(x = 'Time', y = 'Instrument', width=1, height=1, source = df4, line_color='black', 
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
