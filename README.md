# Gates Foundation IATI processing

Gates Foundation IATI data is available from the [IATI
Registry](https://iatiregistry.org/publisher/bmgf).

As of 2018-08-14, the Gates Foundation IATI data claims to use version 2.03 of
the standard.

## Instructions for getting the data and generating the SQL file

Go to https://iatiregistry.org/publisher/bmgf and make sure the activity files
are the same as in `fetch.sh` (in the past, Gates has made the activity files
more granular over time, so that the file names changed). If the file names are
different, first edit `fetch.sh` to use the new file names.

To run:

```bash
./fetch.sh # fetch external dependencies
./generate_sql.py > out.sql # generate the SQL inserts
```

**2017-07-15 update**: For `Sector.csv`, the sector names have been slightly
modified since the script was written, so if you download straight from the
IATI site, you will get key errors.

Also there is a bug in the XML from Gates, where there is a percentage that
equals 500 (i.e. 500% a.k.a. utter nonsense). An assertion in the script
catches this. If you would like to generate the SQL, edit the XML.
