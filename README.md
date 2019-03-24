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
# Fetch external dependencies into data-retrieved-YYYY-MM-DD
./fetch.sh

# Generate the SQL inserts.  Make sure to change YYYY-MM-DD to the
# current date.
./generate_sql.py data-retrieved-YYYY-MM-DD > out.sql
```

There is a bug in the XML from Gates, where there is a percentage that
equals 500 (i.e. 500% a.k.a. utter nonsense). An assertion in the script
catches this. If you would like to generate the SQL, edit the XML.

It's probably from this part in data-retrieved-YYYY-MM-DD/bmgf-activity-a-c.xml:

{'notes': 'to increase access of smallholder farmers to improved crop varieties using a variety of production and distribution strategies; Aid type: Project-type interventions', 'cause_area': 'Agriculture/agricultural research','donation_date_basis': 'IATI', 'donor_cause_area_url': 'http://www.gatesfoundation.org/What-We-Do/Global-Development/Agricultural-Development', 'donor': 'Bill and Melinda Gates Foundation', 'affected_regions': '', 'donation_date_precision': 'day', 'donation_date': '2006-12-01', 'donee': 'Alliance for a Green Revolution in Africa', 'url': 'https://iatiregistry.org/publisher/bmgf', 'affected_countries': 'Burkina faso,Ethiopia, Ghana, Kenya, Mali, Malawi, Mozambique, Niger, Nigeria, Rwanda, Tanzania,united republic of, Uganda, South africa, Zambia'}

If it is this sort of thing, try running the command:

```bash
sed -i 's/500.000000000001/100.0/g' data-retrieved-YYYY-MM-DD/bmgf-activity-a-c.xml
```
