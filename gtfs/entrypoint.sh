#! /bin/sh

/wait-for-it.sh -t 120 -h database -p 5432 && gtfs-via-postgres /gtfs/*.txt | sponge | psql -b