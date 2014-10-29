#!/usr/bin/env python2

'''
Checks for changes in one or more run folder directories.
'''

import os
import re
import logging

def runfolder(path):
  '''
  Run folder path parser.
  '''
  REGEX = r'^(?P<date>\d{6})_(?P<mac>\w+)_(?P<run>\d+)_(?P<bar>\w+)$'
  return re.compile(REGEX).match(os.path.basename(path))

def runfolder_valid(path):
  '''
  Check that a given path is a valid run folder.
  '''
  return bool(runfolder(os.path.basename(path)))

def runfolder_complete(path):
  '''
  Check that a given path is a valid and complete run folder.
  '''
  COMPLETE = 'RTAComplete.txt'
  return runfolder_valid(path) and os.path.exists(os.path.join(path,COMPLETE))

def main(paths=list(),db='db.sq3',**kwargs):
  import socket
  import sqlite3

  logging.info('Checking for changes in run folders...')
  for path in paths:
    logging.debug('checking %s' % path)

    # Get list of sub-directories to check.
    dirs = map(lambda x: x[0], os.walk(path))[1:] # skip the base dir
    vals = map(lambda x: runfolder_complete(x), dirs)
    map(lambda x: logging.debug('\t%s - %s' % x), zip(dirs,vals))

    # Populate the database.
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__),db))

    # Ensure the table is generated.
    try: conn.execute('''
      CREATE TABLE runfolder(host TEXT, path TEXT, PRIMARY KEY(host,path))
    ''')
    except Exception as err: logging.debug(err)

    # Try inserting documents.
    for run,val in zip(dirs,vals):

      # If run is not ready, skip it.
      if not val: continue

      # Try to insert the run into the database.
      try: conn.execute('''
        INSERT INTO runfolder VALUES (?,?)
      ''',(socket.gethostname(),run))
      except Exception as err: pass

    else: conn.commit()

if __name__ == '__main__':
  import sys
  import argparse

  parser = argparse.ArgumentParser(description='Run folder checker.')

  parser.add_argument('paths',nargs='+',help='Folders to check.')

  parser.add_argument('-d','--debug',dest='loglevel',action='store_const',
                      const=logging.DEBUG,default=logging.INFO,
                      help='Set logging level to DEBUG.')
  parser.add_argument('-l','--logto',dest='ofstream',
                      type=lambda x: open(x,'a'),default=sys.stderr,
                      help='File to which logs should be appended.')

  args = parser.parse_args()

  logging.basicConfig(
    level  = args.loglevel,
    stream = args.ofstream,
    format = '%(asctime)s %(name)-6s %(levelname)-4s %(message)s',
  )

  try: main(**args.__dict__)
  except Exception as err:
    logging.error(err)
    sys.exit(1)
