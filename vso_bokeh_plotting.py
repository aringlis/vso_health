import os
import pandas as pd
import datetime
from bokeh.io import output_file, show 
from bokeh.models import (BasicTicker, ColorBar, ColumnDataSource, 
                            LinearColorMapper, PrintfTickFormatter)
from bokeh.models import Legend
from bokeh.plotting import figure  
from bokeh.transform import transform, factor_cmap 

data_path = os.path.expanduser('~/physics/data_curation/vso_health/')

def vso_health_bokeh_plot():

    output_file(os.path.join(data_path,"vso_health_bokeh_plot_files/vso_source_health_summary.html"))
    
    df = pd.read_csv(os.path.join(data_path,'vso_health_status_master_record.csv'))
    df2 = df[df.columns[3:]] 

    #re-cast the Instrument column so that it includes Provider/Source info as well
    newnames = []
    for i, item in df.iterrows(): 
        newnames.append(item['Provider'] + '/' + item['Source'] + '/' + item['Instrument']) 
    df2['Instrument'] = newnames

    #manipulate dataframe into right format
    df2.columns.name = 'Time' 
    df2.set_index('Instrument',inplace=True)
    df3 = pd.DataFrame(df2.stack(), columns=['Health_value']).reset_index()

    #convert times to datetime format
   # tims = []
    #for e in df3['Time']:
     #   tims.append(datetime.datetime.strptime(df3['Time'][0],'%Y%m%d_%H%M%S'))
    #df3['Time'] = tims

    #create the bokeh plot
    p = figure(width=1200,height=1400,x_range=list(df3['Time'].unique()), y_range=list(reversed(df3['Instrument'].unique()) ),
                   tools = 'hover', tooltips = [('Time','@Time'), ('Instrument','@Instrument'),('Status','@Health_value')])

    p.title.text = ' VSO source health status'
    p.add_layout(Legend(), 'right')
    
    
    #define the color map for the plot
    colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    mapper = LinearColorMapper(palette=colors, low=df3.Health_value.min(), high=df3.Health_value.max())

    colors2 = ['seagreen','mediumseagreen','gold','gold','red','red','red','red','orangered','firebrick']
    mapper2 = LinearColorMapper(palette = colors2, low=df3.Health_value.min(), high=df3.Health_value.max())

    

    p.rect(x = 'Time', y = 'Instrument', width=1, height=1, source = df3, line_color='black', 
               fill_color = transform('Health_value', mapper2), legend_field = 'Health_value')

    p.xaxis.major_label_orientation = 'vertical'
    p.legend.location = 'center_right'
    show(p)
