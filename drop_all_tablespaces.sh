#!/bin/bash

# (c) 2010-2011 by Anton Korenyushkin

psql template1 -tc "COPY (SELECT spcname FROM pg_tablespace WHERE spcname NOT LIKE 'pg_%') TO STDOUT" |
while read name; do
    psql -qc "DROP TABLESPACE \"$name\""
done
