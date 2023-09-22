import numpy as np
import glob
import matplotlib.pyplot as plt
import pandas
import datetime
import os

def plot_performance(idl=False):

    if idl:
        df = pandas.read_csv('/home/ainglis/vso_health/vso_health_status_master_record_idl.csv', index_col=0)
        savefilename = 'vso_health_performance_vs_time_idl.pdf'
        savefilename2 = 'vso_health_performance_vs_time_idl.png'
    else:
        df = pandas.read_csv('/home/ainglis/vso_health/vso_health_status_master_record.csv', index_col=0)
        savefilename = 'vso_health_performance_vs_time_python.pdf'
        savefilename2 = 'vso_health_performance_vs_time_python.png'

    total_red = []
    total_yellow = []
    total_green = []
    total_entries = []
    tstamps = []
    
    for c in df.columns[3:]:
        coldata = df[c]
        total_red.append(np.sum(coldata == 8) + np.sum(coldata == 9))
        total_yellow.append(np.sum(coldata == 2))
        total_green.append(np.sum(coldata == 0) + np.sum(coldata == 1))
        total_entries.append(len(coldata))
        tstamps.append(datetime.datetime.strptime(c, '%Y%m%d_%H%M%S'))


    plt.figure(1,figsize=(12,8))
    plt.yticks([0,10,20,30,40,50,60,70,80,90,100])
    plt.grid(which='both')
    plt.plot(tstamps, (np.asarray(total_green) / np.asarray(total_entries))*100.0, 'g+-', label='pass')
    plt.plot(tstamps, (np.asarray(total_yellow) / np.asarray(total_entries))*100.0, 'y+-', label='skipped')
    plt.plot(tstamps, (np.asarray(total_red) / np.asarray(total_entries))*100.0, 'r+-', label='fail')
    plt.ylim([0,100])
    plt.ylabel('%',fontsize=12)
    if idl:
        plt.title('VSO health check performance (IDL)', fontsize=14)
    else:
        plt.title('VSO health check performance (Python)',fontsize=14)
    plt.legend()
    plt.savefig(savefilename)
    plt.savefig(savefilename2)

    plt.close()
    
        
def percent_good_histogram(idl=False):
    
    if idl:
        df = pandas.read_csv('/home/ainglis/vso_health/vso_health_status_master_record_idl.csv', index_col=0)
        savefilename = 'percent_good_per_source_idl.pdf'
        savefilename2 = 'percent_good_per_source_idl.png'
    else:
        df = pandas.read_csv('/home/ainglis/vso_health/vso_health_status_master_record.csv', index_col=0)
        savefilename = 'percent_good_per_source_python.pdf'
        savefilename2 = 'percent_good_per_source_python.png'

     # truncate to the last 30 entries only
    if len(df.columns) < 35:
        df2 = df[df.columns[3:]]
    else:
        df2 = df[df.columns[-30:]]
    # for each source/provider/instrument, plot the percent good as a histogram.

    names = []
    percents_good = []
    percents_skipped = []
    for i, row in df2.iterrows():
        names.append(df.iloc[i][0] + '/' + df.iloc[i][1] + '/' + df.iloc[i][2])
        num_good = np.sum(row == 0.0) + np.sum(row == 1.0)
        num_skipped = np.sum(row == 2.0)
        percents_good.append(num_good / len(row))
        percents_skipped.append(num_skipped / len(row))


    plt.figure(1,figsize=(8,20))
    
    plt.barh(names, np.asarray(percents_good) * 100., color="green")
    plt.barh(names, np.asarray(percents_skipped) * 100., color='yellow')
    plt.grid()
    ax = plt.gca()
    ax.yaxis.set_tick_params(labelsize=6)
    ax.margins(y=0.01)
    if idl:
        plt.title('Percent good in last 30 days (IDL)')
    else:
        plt.title('Percent good in last 30 days (Python)')
    plt.xlabel('Percent good')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(savefilename)
    plt.savefig(savefilename2)


    plt.close()
    
    

def vso_quadrant_chart():

    python_health_check_files = glob.glob('/home/ainglis/vso_health/vso_health_checks/*.csv')
    latest_python_health_check = max(python_health_check_files,key = os.path.getctime)
    python_result = pandas.read_csv(latest_python_health_check)
	    
    idl_health_check_files = glob.glob('/home/ainglis/vso_health/vso_health_idl_version/vso_health_checks_idl/*.csv')
    idl_health_check_files.sort()    
    #latest_idl_health_check = max(idl_health_check_files, key = os.path.getctime) #doesn't work because they all have the same ctime due to rysnc
    latest_idl_health_check = idl_health_check_files[-1]
    idl_result = pandas.read_csv(latest_idl_health_check)
    print(latest_python_health_check)
    print(latest_idl_health_check)



    
    plt.figure(1,figsize=(10,10))
    plt.subplots_adjust(top=0.95,bottom=0.1,right=0.95,left=0.1)

    plt.xlim([0,2])
    plt.ylim([0,2])

    plt.axvline(1.0)
    plt.axhline(1.0)

    ax = plt.gca()
    ax.set_xticks([0.5,1.5])
    ax.set_yticks([0.5,1.5])
    ax.set_xticklabels(['Pass','Fail'])
    ax.set_yticklabels(['Pass','Fail'])

    plt.xlabel('Python',fontsize=16)
    plt.ylabel('IDL',fontsize=16)
    plt.title('VSO Health Test Quadrant Chart ' + datetime.datetime.today().date().isoformat(),fontsize=18)

    plt.fill_between([0,1.0],[1.0,1.0],color='lightgreen',alpha=0.5)
    plt.fill_between([1.0,2.0],[1.0,1.0],color='lightsalmon',alpha=0.5)
    plt.fill_between([0,1.0],[2.0,2.0],y2 = [1.0,1.0],color='lightsalmon',alpha=0.5)
    plt.fill_between([1.0,2.0],[2.0,2.0],y2=[1.0,1.0],color='firebrick',alpha=0.5)
    

    xpos = [0.02,0.52] * 70
    greengreen=0
    redred=0
    greenred=0
    redgreen=0
    totalsources = len(python_result)

    for i, row in python_result.iterrows():
        textstring = row.Provider + '/'+row.Source + '/'+row.Instrument
        if (row.Status in [0,1]) and (idl_result.iloc[i].Status in [0,1]):
            #these sources go in the Pass/Pass quadrant
            plt.text(xpos[i] +(np.random.random()*0.1), 0.008 + (0.008*i), textstring,fontsize=5)
            greengreen+=1            

        elif (row.Status in [8,9]) and (idl_result.iloc[i].Status in [0,1,2]):
            #these sources go in the Fail/Pass quadrant
            plt.text(1 + xpos[i] + (np.random.random()*0.1), 0.008 + (0.008*i), textstring,fontsize=8)
            redgreen+=1
            
        elif (row.Status in [0,1,2]) and (idl_result.iloc[i].Status in [8,9]):
            #these sources go in the Pass/Fail quadrant
            plt.text(xpos[i] + (np.random.random()*0.1), 1.008 + (0.008*i), textstring,fontsize=8)
            greenred+=1
            
        elif (row.Status in [8,9]) and (idl_result.iloc[i].Status in [8,9]):
            #these sources go in the Fail/Fail quadrant
            plt.text(1 + xpos[i] + (np.random.random()*0.1), 1.008 +  (0.008*i), textstring,fontsize=8,weight='bold')
            redred+=1
            
        else:
            pass
            
        
    plt.text(0.45,0.5,str(np.round((greengreen / totalsources)*100.0,1))+'%',color='white',alpha=0.5,fontsize=20)
    plt.text(0.45,1.5,str(np.round((greenred / totalsources)*100.0,1))+'%',color='white',alpha=0.5,fontsize=20)
    plt.text(1.45,0.5,str(np.round((redgreen / totalsources)*100.0,1))+'%',color='white',alpha=0.5,fontsize=20)
    plt.text(1.45,1.5,str(np.round((redred / totalsources)*100.0,1))+'%',color='white',alpha=0.5,fontsize=20)    

    plt.savefig('vso_health_quadrant_chart.png', dpi=300)
    
    
