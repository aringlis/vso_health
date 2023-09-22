import pandas
import numpy as np

def percent_good(vso_health_check_file, idl = False):
    result = pandas.read_csv(vso_health_check_file)
    total = len(result)
    percent_green = ((np.sum(result['Status'] == 0) + np.sum(result['Status'] == 1))  / total) * 100.0
    percent_red = ((np.sum(result['Status'] == 8) + np.sum(result['Status'] == 9)) / total) * 100.0
    percent_yellow = (np.sum(result['Status'] == 2) / total) * 100.0

    print(total)
    
    if idl:
      with open('/home/ainglis/vso_health/percent_green_idl.txt', 'w') as f:
          f.write(str(np.round(percent_green,1)))

      with open('/home/ainglis/vso_health/percent_yellow_idl.txt', 'w') as f:
          f.write(str(np.round(percent_yellow,1)))

      with open('/home/ainglis/vso_health/percent_red_idl.txt', 'w') as f:
          f.write(str(np.round(percent_red,1)))

    else:

      with open('/home/ainglis/vso_health/percent_green.txt', 'w') as f:
          f.write(str(np.round(percent_green,1)))
        
      with open('/home/ainglis/vso_health/percent_yellow.txt', 'w') as f:
          f.write(str(np.round(percent_yellow,1)))

      with open('/home/ainglis/vso_health/percent_red.txt', 'w') as f:
          f.write(str(np.round(percent_red,1)))
 

