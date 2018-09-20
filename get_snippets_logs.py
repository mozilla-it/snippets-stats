#!/usr/bin/env python3

import time
import sys,os,errno,re,argparse
import datetime
from subprocess import call
from config import config

proxies = config['proxies']

def print_debug(level, message):
  if debug >= level:
    print("[%s] %s" % (datetime.datetime.now(),message))

def get_snippets_logs(fetch_date):

  if not fetch_date:
    fetch_date = datetime.datetime.now().strftime('%Y-%m-%d')
    print_debug(3, "No date given. Using %s" % fetch_date)

  fetch_date_l = [ i for i in fetch_date.split('-') ]
  date_no_dashes = ''.join(fetch_date_l)

  os.environ['AWS_ACCESS_KEY_ID']     = config['s3_snippets_bucket_AK']
  os.environ['AWS_SECRET_ACCESS_KEY'] = config['s3_snippets_bucket_SK']

  # s3 is very sensitive about extra slashses :(
  if config['s3_snippets_path'].strip('/ ') == '':
    s3_uri = 's3://' + config['s3_snippets_bucket'].strip('/ ') + '/' + date_no_dashes
  else:
    s3_uri = 's3://' + config['s3_snippets_bucket'].strip('/ ') + '/' + \
                       config['s3_snippets_path'].strip('/ ')   + '/' + date_no_dashes
  aws_command_l = ['aws', 's3', 'sync', s3_uri, os.path.join(s3_uri,config['snippets_dir'], fetch_date)]
  print_debug(3, "Calling: %s" % ' '.join(aws_command_l))
  call( aws_command_l )

if __name__ == "__main__":
 
  parser = argparse.ArgumentParser(description="Get snippets-stats logs from S3")
  parser.add_argument('-d', '--debug', action='store', help='debug level', type=int, default=3)
  parser.add_argument('--date', action='store', help='date to fetch', type=str, default='')
  args = parser.parse_args()

  debug = args.debug

  print_debug(1, "Starting...")

  get_snippets_logs(args.date)

  print_debug(1, "Finished.")
