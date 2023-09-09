#!/bin/bash

set -e -o xtrace

. ./CI/set_env.sh job_site.env
. ~/1_Home/virtualenv/jobs/bin/activate

git checkout master


function applying_master_db_migrations {
  rm db.sqlite3 || true
  python3 manage.py migrate
  rm jobs_dump.json || true
  ssh machine "/usr/local/bin/docker exec -i jobs_site_app python3 manage.py dumpdata jobs auth.user --indent 4 --output jobs_dump.json"
  ssh machine "/usr/local/bin/docker cp jobs_site_app:/src/app/jobs_dump.json jobs_dump.json"
  scp machine:/var/services/homes/jace/jobs_dump.json jobs_dump.json
  python3 manage.py loaddata jobs_dump.json
  rm jobs_dump.json || true
  ssh machine "rm jobs_dump.json && /usr/local/bin/docker exec -i jobs_site_app rm jobs_dump.json"
}

applying_master_db_migrations

git checkout -
