#!/usr/bin/env python3

#
#
# TODO: handle dates at all
# TODO: use commercial version of IP database?
# TODO: handle updating IP database (outside of this script, tho)
#
#

import geoip2.database
import httpagentparser
import time
import sys,os,errno,re,argparse
import json
from datetime import datetime
from config import config

ALLOWED_REQUEST_STRING_FIELDS = ('snippet_name', 'metric', 'country', 'campaign', 'locale')


proxies = config['proxies']

def print_debug(level, message):
  if debug >= level:
    print("[%s] %s" % (datetime.now(),message))

def extract_fields(line):
  json_dict = json.loads(line)
  #print(json_dict)
  #print(json_dict['ClientHost'])
  #print(json_dict['time'])
  #print(json_dict['RequestPath'])
  #print(json_dict['request_User-Agent'])
  return(json_dict['ClientHost'],json_dict['time'],json_dict['RequestPath'],json_dict['request_User-Agent'])

def parse_file(filename, geoip_db_reader, results):
  skip_count_ip_lookup = 0
  skip_count_main_regex_fail = 0
  processed_count = 0

  with open(filename) as f:
    for line in f:
      (ip,date,request_str,ua_str) = extract_fields(line)
      if not ip:
        skip_count_main_regex_fail += 1
      else:
        request_dict = parse_request_string(request_str)
        ua_dict = parse_ua_string(ua_str)

        try:
          country_code = geoip_db_reader.country(ip).country.iso_code
          if not country_code:
            # if no country, replace with continent
            country_code = geoip_db_reader.country(ip).continent.code
            if not country_code:
              country_code = 'XX'
        except:
          country_code = 'XX'

        data_array = [
          ua_dict['ua_family'],
          ua_dict['ua_major'],
          ua_dict['os_family'],
          country_code,
          request_dict.get('snippet_name',''),
          request_dict.get('locale',''),
          request_dict.get('metric',''),
          request_dict.get('country',''),
          request_dict.get('campaign','')
        ]

        unique_key = ''.join(data_array)

        if unique_key in results:
          results[unique_key][1] += 1000
        else:
          results[unique_key] = [data_array,1000]

        processed_count += 1

  return(results, processed_count, skip_count_ip_lookup + skip_count_main_regex_fail)

def parse_ua_string(ua):
  parsed_ua = httpagentparser.detect(ua)
  os = parsed_ua['platform']['name']
  if os == None:
    os = 'Other'
  elif os == 'Mac OS' and re.match('X',parsed_ua['platform']['version']):
    os = 'Mac OS X'
  elif parsed_ua['platform']['version'] != None:
    os = os + ' ' + parsed_ua['platform']['version']

  ua_family = 'Other'
  ua_major  = 'Other'
  if 'browser' not in parsed_ua:
    # make a best-effort:
    #print(ua)
    m = re.match('^[^ ]+(?:/[^ ]*)? \(.*?\) [^ ]+(?:/[^ ]*)? ([^/]+)/([^ ]+)', ua)
    if m:
      #print(m[1])
      #print(m[2])
      ua_family = m[1]
      ua_major  = m[2]
  else:
    ua_family = parsed_ua['browser']['name']
    ua_major  = parsed_ua['browser']['version']

  ua_major = ua_major.split('.')[0]

  return({ 'os_family': os,
           'ua_family': ua_family,
           'ua_major':  ua_major
         })

def parse_request_string(req_str):
  request_dict = {}
  for m in re.finditer('([^=]+)=([^&]*)&?',req_str):
    if m[1] not in ALLOWED_REQUEST_STRING_FIELDS:
      continue
    request_dict[m[1]] = m[2]
  return request_dict

if __name__ == "__main__":
 
  parser = argparse.ArgumentParser(description="Parse snippets-stats logs")
  parser.add_argument('-d', '--debug', action='store', help='debug level', type=int, default=3)
  #parser.add_argument('-f', '--force', action='store_true', help='force changes even if there are a lot')
  args = parser.parse_args()

  debug = args.debug

  print_debug(1, "Starting...")

  reader = geoip2.database.Reader(config['geoip_db_loc'])
  
  results = {}
  total_processed = 0
  total_files = 0
  total_skips = 0
  for file in os.listdir(config['snippets_dir']):
    if re.match('^snippets.log-', file):
      total_files += 1
      print("Processing filename: %s" % file)
      results,processed,skipped = parse_file(os.path.join(config['snippets_dir'],file),reader,results)
      total_skips += skipped
      total_processed += processed
    else:
      print("Filename: %s not a match" % file)

#  for key in results:
#    print(results[key])
#    if results[key][0][4] == '7905' and results[key][0][0] == 'Firefox' and results[key][0][1] == '60' and results[key][0][2] == 'Windows 10':
#      print(results[key])
#    if results[key][1] > 10000:
#      print(results[key][0],results[key][1])

  #like_insert_into_vertica_i_guess(results)

  print("Summary:")
  print("Files processed  : %d" % total_files)
  print("Records processed: %d" % total_processed)
  print("Records skipped  : %d" % total_skips)
  print_debug(1, "Finished.")
