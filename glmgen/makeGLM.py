'''Writes the necessary .glm files for a calibration round. Define recording interval and MySQL schema name here.'''
from __future__ import division

from glmgen import feeder
from glmgen import Milsoft_GridLAB_D_Feeder_Generation

import datetime 
import os
import re
import math

# recording interval (seconds)
interval = 300  

# flag whether we're using mysql for recorder output or not ( implies using .csv files instead )
# Make sure this flag is the same in gleanMetrics.py or there'll be problems. 
use_mysql = 0 # 0 => .csv files; 1 => mysql database

# MySQL schema name
schema = 'CalibrationDB'


def makeGLM(clock, calib_file, baseGLM, case_flag, options, dir, resources_dir='schedules'):
  '''Create populated dict and write it to .glm file
  
  - clock (dictionary) links the three seasonal dates with start and stop timestamps (start simulation full 24 hour before day we're recording)
  - calib_file (string) -- filename of one of the calibration files generated during a calibration round 
  - baseGLM (dictionary) -- orignal base dictionary for use in Milsoft_GridLAB_D_Feeder_Generation.py
  - case_flag (int) -- flag technologies to test
  - options -- parameters we want to override for CPE
  - dir(string)-- directory in which to store created .glm files
  '''
  # Create populated dictionary.
  if calib_file is not None:
    calib_fullpath = dir+'/'+calib_file
  else:
    calib_fullpath = None
  glmDict, last_key = Milsoft_GridLAB_D_Feeder_Generation.GLD_Feeder(
      baseGLM,
      case_flag,
      dir,
      resources_dir,
      options,
      calib_fullpath) 
  
  fnames =  []
  for i in clock.keys():
    # Simulation start
    starttime = clock[i][0]
    # Recording start
    rec_starttime = i
    # Simulation and Recording stop
    stoptime = clock[i][1]
    
    # Calculate limit.
    j = datetime.datetime.strptime(rec_starttime,'%Y-%m-%d %H:%M:%S')
    k = datetime.datetime.strptime(stoptime,'%Y-%m-%d %H:%M:%S')
    diff = (k - j).total_seconds()
    limit = int(math.ceil(diff / interval))
    
    populated_dict = glmDict
    
    # Name the file.
    if calib_file is None:
      id = 'DefaultCalibration'
    else:
      m = re.compile( '\.txt$' )
      id = m.sub('',calib_file)
    date = re.sub('\s.*$','',rec_starttime)
    filename = id + '_' + date + '.glm'
    # ETH@20140411 - hardcoding an overwrite of the omf name.
    filename = "model.glm"
    
    # Get into clock object and set start and stop timestamp.
    for i in populated_dict.keys():
      if 'clock' in populated_dict[i].keys():
        populated_dict[i]['starttime'] = "'{:s}'".format(starttime)
        populated_dict[i]['stoptime'] = "'{:s}'".format(stoptime)
    
    lkey = last_key
    
    if use_mysql == 1:
      # Add GridLAB-D objects for recording into MySQL database.
      populated_dict[lkey] = { 'module' : 'mysql' }
      lkey += 1
      populated_dict[lkey] = {'object' : 'database',
                    'name' : '{:s}'.format(schema),
                    'schema' : '{:s}'.format(schema) }
      lkey += 1
      populated_dict[lkey] = {'object' : 'mysql.recorder',
                    'table' : 'network_node_recorder',
                    'parent' : 'network_node',
                    'property' : 'measured_real_power,measured_real_energy',
                    'interval' : '{:d}'.format(interval),
                    'limit' : '{:d}'.format(limit),
                    'start': "'{:s}'".format(rec_starttime),
                    'connection': schema,
                    'mode': 'a'}
    else:
      # Add GridLAB-D object for recording into *.csv files.
      populated_dict[lkey] = {'object' : 'tape.recorder',
                    'file' : 'csv_output/{:s}_{:s}_network_node_recorder.csv'.format(id,date),
                    'parent' : 'network_node',
                    'property' : 'measured_real_power,measured_real_energy',
                    'interval' : '{:d}'.format(interval),
                    'limit' : '{:d}'.format(limit),
                    'in': "'{:s}'".format(rec_starttime) }
                    
    # Turn dictionary into a *.glm string and print it to a file in the given directory.
    populated_dict.save(os.path.realpath(dir + '/' + filename))
    
    fnames.append(filename)
  return fnames

def main():
  print (__doc__)
  print (makeGLM.__doc__)
if __name__ ==  '__main__':
   main();
