import numpy as np
import datetime
import sunpy
from sunpy.net import vso, attrs as a

import copy
import os
import csv
import warnings
import logging
import glob
import pandas
import time
from subprocess import PIPE, run

data_path = os.path.expanduser('~/vso_health/')

# Ignore all SunPy deprecation warnings
warnings.simplefilter('ignore', sunpy.util.exceptions.SunpyDeprecationWarning)

def read_vso_sources():
    sources = csv.DictReader(open(os.path.join(data_path,'vso_sources.csv')))

    return sources


def query_vso_providers(skip_download=True, skip_list = [],test_known_queries = False):
    '''This function performs a test on each Provider/Source/Instrument combination supported
    by the VSO, to see whether a VSO query results in success. This is done by generating a query
    for a randomized time interval between the known start and end times of data provision for each 
    Provider/Source/Instrument combination. If the randomized query fails, a query for a time interval
    where there is known to be data is attempted.

    The output is saved to CSV format and is also returned in the 'flags' variable.
    Flags can take the following output values:
        0: Query successful
        1: Random query failed but known query successful
        2: Item was skipped (using skip_list)
        8: Random query or known query successful but download failed
        9: Fail

    '''

    script_start_time = time.perf_counter()
    
    fname_append = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')     
    logging.basicConfig(filename=os.path.join(data_path,'logs/query_vso_' + fname_append + '.log'), level=logging.INFO,
format='%(asctime)s %(levelname)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
    logging.Formatter.converter = time.gmtime
    logging.info(r'Current 1-min load average: ' + str(os.getloadavg()[0]))
    logging.info(r'Current 5-min load average: ' + str(os.getloadavg()[1]))
    logging.info(r'Current 15-min load average: ' + str(os.getloadavg()[2]))
   # skip_list = [] #['SJ','SP1','SP2','Hi_C','Hi-C21']
    
    client = vso.VSOClient()

    # get a list of all the possible vso sources to check
    sources = read_vso_sources()

    # get a list of known successful queries as a backup test
    known_queries = list(csv.DictReader(open(os.path.join(data_path,'vso_known_query_database_full.csv'))))

    flag_list = []

    for s in list(sources):
        flag_entry = {}
        flag_entry['Provider'] = s['Provider']
        flag_entry['Source'] = s['Source']
        flag_entry['Instrument'] = s['Instrument']
        
        # first, select a random time within the data source availability window

        # special case for SDAC/SDO/AIA synoptic data
        if (s['Provider'] == 'SDAC') and (s['Instrument'] == 'AIA'):
            t1_query = datetime.datetime.now() - datetime.timedelta(days = 4)
            t2_query = t1_query + datetime.timedelta(days = 1)
        else:
            # all other cases
            t1 = datetime.datetime.strptime(s['Date_Start'],'%Y-%m-%d')
            if s['Date_End']:
                t2 = datetime.datetime.strptime(s['Date_End'],'%Y-%m-%d')
            else:
                t2 = datetime.datetime.today()

            dt = (t2-t1).total_seconds() 
            dt_randomize = dt * np.random.uniform()
        
            t1_query = t1 + datetime.timedelta(seconds = dt_randomize)
            # special case for JSOC/AIA and JSOC/HMI. If the query duration is too long, it returns summary records, causing a timeout on download
            if (s['Provider'] == 'JSOC') and ( (s['Instrument'] == 'AIA') or (s['Instrument'] == 'HMI') ):
                t2_query = t1 + datetime.timedelta(seconds = dt_randomize + 3600)
            else:
                t2_query = t1 + datetime.timedelta(seconds = dt_randomize + 86400)


        if s['Provider'] + '/' + s['Source'] + '/' + s['Instrument'] not in skip_list:
            logging.info('Query: ' + s['Provider'] + ' | ' + s['Source'] +
                    ' | ' + s['Instrument'] + ' between ' + t1_query.isoformat() + ' and ' +
                    t2_query.isoformat())


    
            # now make the query
            flag_entry['Querytime'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
            if not test_known_queries:
                try:
                    result = client.search(a.Time(t1_query, t2_query), a.Provider(s['Provider']),
                         	               a.Source(s['Source']), a.Instrument(s['Instrument']) , response_format = 'legacy')
                except:
                    logging.info('Search did not return a result for : ' + s['Provider'] + ' | ' + s['Source'] +
                        ' | ' + s['Instrument'])
                    flag_entry['Status'] = 10
                    continue
            else:
                result = []

            if (len(result) == 0) or (test_known_queries == True):
                # try a query at a time where we know there should be data
                try:
                    query = [k for k in known_queries if (k['Instrument'] == s['Instrument']) and (k['Source'] == s['Source']) and 
                            (k['Provider'] == s['Provider']) ][0]
                    print(query)
                    known_t1 = datetime.datetime.strptime(query['Date_Start'],'%Y-%m-%d %H:%M:%S.%f')
                    known_t2 = datetime.datetime.strptime(query['Date_End'],'%Y-%m-%d %H:%M:%S.%f')
                    result2 = client.search(a.Time(known_t1, known_t2), a.Provider(s['Provider']),
                                        a.Source(s['Source']), a.Instrument(s['Instrument']),
                                                response_format = 'legacy')
                    logging.info('Random query failed. Trying known query: '  + s['Provider'] + ' | ' + s['Source'] +
                        ' | ' + s['Instrument'] + ' between ' + known_t1.isoformat() + ' and ' +
                        known_t2.isoformat())


                    if len(result2) == 0:
                        flag_entry['Status'] = 9
                    else:
                        flag_entry['Status'] = 1
                        result = copy.deepcopy(result2)

                except IndexError:
                    logging.info('Random query failed. No known query for: '  + s['Provider'] + ' | ' + s['Source'] +
                        ' | ' + s['Instrument'])
                    flag_entry['Status'] = 9

            else:
                flag_entry['Status'] = 0
            

                
            if not skip_download and len(result) > 0:
                try:
                    dl = client.fetch(result[0], path = os.path.expanduser('~/vso_health_temp_data'))
                    if len(dl.errors) !=0: 
                        flag_entry['Status'] = 8
                    elif (len(dl) == 0):
                        flag_entry['Status'] = 8
                    else:
                        pass
                except:
                    #if the download fails due to a hard error (e.g. Evans radioheliograph), catch this and continue
                    flag_entry['Status'] = 8

        

                
        else:
            logging.info('Skipping: ' + s['Provider'] + ' | ' + s['Source'] +
                    ' | ' + s['Instrument'])

            flag_entry['Status'] = 2

        flag_list.append(flag_entry)

            
    # write the results of the check to a csv file
  #  fname_ext = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    fname = os.path.join(data_path,'vso_health_checks/vso_health_check_' + fname_append + '.csv')
            
  #  with open(fname,'w') as f: 
   #     for key in flags.keys(): 
    #        f.write(key + ',' + str(flags[key]) + '\n') 

    header = ['Provider','Source','Instrument','Status','Querytime']
    with open(fname,'w') as f:
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(flag_list)
            
    logging.info(r'Current 1-min load average: ' + str(os.getloadavg()[0]))
    logging.info(r'Current 5-min load average: ' + str(os.getloadavg()[1]))
    logging.info(r'Current 15-min load average: ' + str(os.getloadavg()[2]))
    script_total_time = time.perf_counter() - script_start_time
    logging.info(f"VSO health queries completed after: {script_total_time:.2f} seconds")
    return flag_list, fname
        

    

    
def find_query_with_data(instrument = 'SECCHI', n_iterations = 40):
    '''Repeatedly generate queries for a VSO-supported instrument with randomized
    search times, to attempt to find a query that returns data.'''
    
    
    import warnings
    logging.basicConfig(filename='example2.log', level=logging.WARNING)
    
    client = vso.VSOClient()

    # get a list of all the possible vso sources to check
    sources = read_vso_sources()
    sources = list(sources)

    for s in sources: 
        if s['Instrument'] == instrument:
            source_dict = s

    # first, select a random time within the data source availability window
    t1 = datetime.datetime.strptime(source_dict['Date_Start'],'%Y-%m-%d')
    if source_dict['Date_End']:
        t2 = datetime.datetime.strptime(source_dict['Date_End'],'%Y-%m-%d')
    else:
        t2 = datetime.datetime.today()

    dt = (t2-t1).total_seconds() 

    success = 0
    successful_query_dict = {}

    # repeatedly generate queries until we get a succesful result
    for i in range(0,n_iterations):
        
        dt_randomize = dt * np.random.uniform()
        
        t1_query = t1 + datetime.timedelta(seconds = dt_randomize)
        t2_query = t1 + datetime.timedelta(seconds = dt_randomize + (86400*3))

        # now make the query
        result = client.search(a.Time(t1_query, t2_query), a.Provider(source_dict['Provider']),
                                    a.Source(source_dict['Source']), a.Instrument(source_dict['Instrument']), response_format = 'legacy')

        if len(result) > 0:
            # if query returns data then remember the query and stop searching
            t1_success = t1_query
            t2_success = t2_query
            success = True
            break
        
        
    if success:  
        successful_query_dict['Provider'] = source_dict['Provider']
        successful_query_dict['Source'] = source_dict['Source']
        successful_query_dict['Instrument'] = source_dict['Instrument']
        successful_query_dict['Date_Start'] = t1_success
        successful_query_dict['Date_End'] = t2_success



    return successful_query_dict, result


        
def create_known_query_database():
    '''Create a file containing VSO queries for each supported instrument that
    are known to return results.'''
    
    sources = read_vso_sources()

    database = []
    
    for s in list(sources):
        result = find_query_with_data(instrument = s['Instrument'])
        database.append(result[0])


    header = ['Provider','Source','Instrument','Date_Start','Date_End']
    with open(os.path.join(data_path,'vso_known_query_database.csv','w')) as f:
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(database)
    
    return database
        

#def create_master_status_file(idl = None):
#    '''Read all existing VSO health check files and create a master record.'''
#
#    if idl:
#        files = glob.glob(os.path.join(data_path,'vso_health_idl_version/vso_health_checks_idl/vso_health_check*.csv'))
#    else:
#        files = glob.glob(os.path.join(data_path,'vso_health_checks/vso_health_check*.csv'))
#
#    files.sort()
#    filestrings = os.path.basename(files[0]).split('_')
#    file_date = filestrings[3]
#    file_time = filestrings[4].split('.')[0]
#    column_id = file_date + '_' + file_time
#
#    df_master = pandas.read_csv(files[0])
#    df_master.rename({'Status':column_id},axis = 'columns', inplace=True)
#    
#    for f in files[1:]:
#        # extract the date and time for each VSO check file
#        filestrings = os.path.basename(f).split('_')
#        file_date = filestrings[3]
#        file_time = filestrings[4].split('.')[0]
#        column_id = file_date + '_' + file_time
#
#        
#        df = pandas.read_csv(f)
#        df.rename({'Status':column_id},axis = 'columns', inplace=True)
#
#        df_master = pandas.merge(df_master, df, how='right')
#
#
 #   if idl:
#        df_master.to_csv(os.path.join(data_path,'vso_health_status_master_record_idl.csv'))
#    else:
#        df_master.to_csv(os.path.join(data_path,'vso_health_status_master_record.csv'))
#
#    return df_master, df

        

        


def create_master_status_file(idl = None):
    if idl:
        pattern = 'vso_health_idl_version/vso_health_checks_idl/vso_health_check*.csv'
        out = 'vso_health_status_master_record_idl.csv'

    else:
        pattern = 'vso_health_checks/vso_health_check*.csv'
        out = 'vso_health_status_master_record.csv'

    out_times = out.replace('.csv','_querytimes.csv')

    files = sorted(glob.glob(os.path.join(data_path, pattern)))
    keys = ['Provider', 'Source', 'Instrument']

    columns = []
    time_cols = []
    for f in files:
        parts = os.path.basename(f).split('_')
        column_id = parts[3] + '_' + parts[4].split('.')[0]
        #s = pandas.read_csv(f).set_index(keys)['Status'].rename(column_id)
        df = pandas.read_csv(f).reindex(columns=keys + ['Status', 'Querytime'])
        df = df.set_index(keys)
       # assert s.index.is_unique, f'duplicate instrument keys in {f}'
        assert df.index.is_unique, f'duplicate instrument keys in {f}'

        columns.append(df['Status'].rename(column_id))
        time_cols.append(df['Querytime'].rename(column_id))
       # columns.append(s)

    # one outer join on the index; a row missing from one run is just NaN there
    df_master = pandas.concat(columns, axis=1).sort_index().reset_index()
    df_master.to_csv(os.path.join(data_path, out), index=False)

    df_times = pandas.concat(time_cols, axis=1).sort_index().reset_index()
    df_times.to_csv(os.path.join(data_path, out_times), index=False)
    return df_master

def cleanup_query_files():
    '''Remove downloaded files from the sunpy/data directory'''


    now = datetime.datetime.now().timestamp()
    path = os.path.expanduser('~/vso_health_temp_data/')

    files = os.listdir(path)

    for f in files:
        full_fname = os.path.join(path,f)
        # remove files downloaded in the 2 hours
        #if os.stat(full_fname).st_mtime > (now - 7200.):
         #   if os.path.isfile(full_fname):
        os.remove(full_fname)



def verify_todays_health_check_exists(idl=False):
    datestr = datetime.datetime.today().strftime('%Y%m%d')
    if idl:
        files = glob.glob('/home/ainglis/vso_health/vso_health_idl_version/vso_health_checks_idl/vso_health_check_' + datestr + '*.csv')
    else:
        files = glob.glob('/home/ainglis/vso_health/vso_health_checks/vso_health_check_' + datestr + '*.csv')
    if files:
        return True
    else:
        return False



def create_missing_health_check(outfilename = 'vso_health_check_null.csv',idl=False):
    '''Sometimes we need to create a dummy file to insert into the vso health database. This happens
       if a day was missed for some reason.'''

    if idl:
        full_fname = os.path.join('/home/ainglis/vso_health/vso_health_idl_version/vso_health_checks_idl',outfilename)
    else:
        full_fname = os.path.join('/home/ainglis/vso_health/vso_health_checks',outfilename)

    header = ['Provider','Source','Instrument','Status']
    sources = read_vso_sources()
    flag_list = []
    
    for s in sources:
        flag_entry = {}
        flag_entry['Provider'] = s['Provider']
        flag_entry['Source'] = s['Source']
        flag_entry['Instrument'] = s['Instrument']
        flag_entry['Status'] = 2
        flag_list.append(flag_entry)

    with open(full_fname,'w') as f:
        w = csv.DictWriter(f, header)
        w.writeheader()
        w.writerows(flag_list)




