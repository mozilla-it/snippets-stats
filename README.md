# snippets-stats

A few scripts to ETL the snippets-stats logs

## snippets.py
Processes the files in a local dir ("snippets_dir" in the config.py file) and uploads results to Vertica.

## Helpers

### get_snippets_logs.py
Syncs up a local directory ("snippets_dir" in the config.py file) with the S3 source ("s3_snippets_bucket" and "s3_snippets_path" in config.py).

### get_geoip_db.py
Downloads and installs the latest GeoIP database. Just as soon as I write it.
