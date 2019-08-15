#!/usr/bin/env python3

import geoip2.database
import httpagentparser
import time
import sys,os,errno,re,argparse
import json
import datetime
from subprocess import call
from google.cloud import bigquery, storage

ALLOWED_REQUEST_STRING_FIELDS = ['snippet_name', 'metric', 'country', 'campaign', 'locale']

SNIPPETS_DIR = os.environ.get('SNIPPETS_DIR','/workspace/snippets-stats')
S3_SNIPPETS_PATH = os.environ.get('S3_SNIPPETS_PATH','/').strip('/ ')
S3_SNIPPETS_BUCKET = os.environ.get('S3_SNIPPETS_BUCKET',None).strip('/ ')

GEOIP_DB_NAME = 'GeoIP2-Country.mmdb'

def get_snippets_logs(fetch_date = datetime.datetime.now().strftime('%Y-%m-%d')):
  print_debug(3, "Using date %s" % fetch_date)

  fetch_date_l = [ i for i in fetch_date.split('-') ]
  date_no_dashes = ''.join(fetch_date_l)

  # s3 is very sensitive about extra slashses :(
  if S3_SNIPPETS_PATH == '':
    s3_uri = 's3://' + S3_SNIPPETS_BUCKET + '/' + date_no_dashes
  else:
    s3_uri = 's3://' + S3_SNIPPETS_BUCKET + '/' + S3_SNIPPETS_PATH + '/' + date_no_dashes
  aws_command_l = ['aws', 's3', 'sync', s3_uri, os.path.join(SNIPPETS_DIR, fetch_date)]
  print_debug(3, "Calling: %s" % ' '.join(aws_command_l))
  call( aws_command_l )

def print_debug(level, message):
  if debug >= level:
    print("[%s] %s" % (datetime.datetime.now(),message))

def extract_fields(line):
  try:
    json_dict = json.loads(line)
  except ValueError:
    json_dict = { 'ClientHost': '', 'time': '', 'RequestPath': '', 'request_User-Agent': '' }
  return(json_dict.get('ClientHost',''),json_dict.get('time',''),json_dict.get('RequestPath',''),json_dict.get('request_User-Agent',''))

def parse_file(filename, geoip_db_reader, results):
  skip_count_ip_lookup = 0
  skip_count_main_regex_fail = 0
  processed_count = 0

  #with gzip.open(filename, mode='rt') as f:
  with open(filename,encoding="utf-8") as f:
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
  elif os == 'Mac OS' and 'version' in parsed_ua['platform'] and re.match('X',parsed_ua['platform']['version']):
    os = 'Mac OS X'
  elif parsed_ua['platform']['version'] != None:
    os = os + ' ' + parsed_ua['platform']['version']

  ua_family = 'Other'
  ua_major  = 'Other'
  if 'browser' not in parsed_ua:
    # make a best-effort:
    m = re.match('^[^ ]+(?:/[^ ]*)? \(.*?\) [^ ]+(?:/[^ ]*)? ([^/]+)/([^ ]+)', ua)
    if m:
      ua_family = m.group(1)
      ua_major  = m.group(2)
  else:
    ua_family = parsed_ua['browser']['name']
    ua_major  = parsed_ua['browser']['version'] if 'version' in parsed_ua['browser'] else ''
    # god knows why, but sometimes httpagentparser returns 'AndroidBrowser' and sometimes 'Firefox'
    # for the same UA. So let's just force it to Firefox
    if ua_family == 'AndroidBrowser':
      ua_family = 'Firefox'

  ua_major = ua_major.split('.')[0]

  return({ 'os_family': os,
           'ua_family': ua_family,
           'ua_major':  ua_major
         })

def parse_request_string(req_str):
  request_dict = {}
  for m in re.finditer('([^=?]+)=([^&]*)&?',req_str):
    if m.group(1) not in ALLOWED_REQUEST_STRING_FIELDS:
      continue
    request_dict[m.group(1)] = m.group(2)
  return request_dict

def get_date_from(date_to_process, offset):
  date_to_process_l = [ int(i) for i in date_to_process.split('-') ]
  date_to_process   = datetime.date(date_to_process_l[0], date_to_process_l[1], date_to_process_l[2])
  next_day = date_to_process + datetime.timedelta(days=offset)
  return str(next_day)

def like_insert_into_bq_i_guess(date, results):
  bq = bigquery.Client()

  dataset_id = "snippets"
  table_id = "snippet_count"

  table_ref = bq.dataset(dataset_id).table(table_id)
  table = bq.get_table(table_ref)
  
  q = bq.query("DELETE FROM snippets.snippet_count WHERE date=\"{}\"".format(date))
  q.result() # waits for finish
  
  insert_rows = []

  for key in results:
    data_l = results[key][0]
    count  = results[key][1]

    values = (date, data_l[0], data_l[1], data_l[2],data_l[3], data_l[4], count, data_l[5],data_l[6], data_l[7], data_l[8])
    insert_rows += [values]
  if len(insert_rows) > 0:
    max_queries = 1000
    chunks = [insert_rows[i * max_queries:(i + 1) * max_queries] for i in range((len(insert_rows) + max_queries - 1) // max_queries )]
    for c in chunks:
      err = bq.insert_rows(table, c)
      if len(err) > 0:
        print(c)
        print(err)

if __name__ == "__main__":
 
  parser = argparse.ArgumentParser(description="Parse snippets-stats logs")
  parser.add_argument('-d', '--debug', action='store', help='debug level', type=int, default=3)
  parser.add_argument('--date', action='store', help='date to process', type=str)
  parser.add_argument('--geoip-gcs-bucket', action='store', help='gcs bucket where geoip db lives', type=str)
  args = parser.parse_args()

  debug = args.debug

  print_debug(1, "Starting...")


  if not args.date:
    # by default, load the data from yesterday
    load_date = get_date_from(datetime.datetime.now().strftime('%Y-%m-%d'),-1)
  else:
    load_date = args.date

  GEOIP_DB_PATH = os.path.join(SNIPPETS_DIR,GEOIP_DB_NAME)
  if args.geoip_gcs_bucket:
    gcs = storage.Client()
    gcs_bucket = gcs.get_bucket(args.geoip_gcs_bucket)
    blob = gcs_bucket.blob(GEOIP_DB_NAME)
    blob.download_to_filename(GEOIP_DB_PATH)


  # because we need to get the logs from day X from the directory for day X+1:
  date_1_day_forward = get_date_from(load_date, 1)

  # load geoip db
  reader = geoip2.database.Reader(GEOIP_DB_PATH)

  # this copies the logs from s3 locally
  get_snippets_logs(date_1_day_forward)

  date_l = [ i for i in date_1_day_forward.split('-') ]
  date_no_dashes = ''.join(date_l)

  logs_path = os.path.join(SNIPPETS_DIR, date_1_day_forward)

  # the hits for day X are in the log dated day X+1
  file_pattern = "^snippets.log-%s" % date_no_dashes
  
  print_debug(3, "Date specified       :  %s" % args.date)
  print_debug(3, "Date to load         :  %s" % load_date)
  print_debug(3, "Date + 1             :  %s" % date_1_day_forward)
  print_debug(3, "Date + 1 (no dashes) :  %s" % date_no_dashes)
  print_debug(3, "Local logs path      :  %s" % logs_path)
  print_debug(3, "File pattern         :  %s" % file_pattern)

  results = {}
  total_processed = 0
  total_files = 0
  total_skips = 0
  for instance_id in os.listdir(logs_path):
    full_logs_path = os.path.join(logs_path, instance_id)
    for file in os.listdir(full_logs_path):
      if re.match(file_pattern, file):
        total_files += 1
        print("Processing filename: %s/%s" % (full_logs_path,file))
        results,processed,skipped = parse_file(os.path.join(full_logs_path, file),reader,results)
        total_skips += skipped
        total_processed += processed
      else:
        print("Filename: %s not a match" % file)

  like_insert_into_bq_i_guess(load_date, results)

  print_debug(3, "Summary:")
  print_debug(3, "Files processed  : %d" % total_files)
  print_debug(3, "Records processed: %d" % total_processed)
  print_debug(3, "Records skipped  : %d" % total_skips)
  print_debug(1, "Finished.")
