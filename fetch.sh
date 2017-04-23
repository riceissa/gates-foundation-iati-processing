#!/bin/bash
wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-a-f.xml'
wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-g-m.xml'
wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-n-s.xml'
wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-t-z.xml'
wget 'http://codelists103.archive.iatistandard.org/data/codelist/Country/version/1.01/lang/en.csv' \
    -O Country.csv
wget 'http://codelists103.archive.iatistandard.org/data/codelist/Region/version/1.0/lang/en.csv' \
    -O Region.csv
# The aid type CSV from the standard is malformed (fails to escape double
# quotes) so use the XML instead
wget 'http://codelists103.archive.iatistandard.org/data/codelist/AidType/version/1.0/lang/en.xml' \
    -O AidType.xml
# Gates Foundation uses some sector codes that aren't in version 1.03 of
# the standard, e.g. 14032. So we use version 1.05 instead, which has all the
# sector codes of interest.
wget 'http://iatistandard.org/105/codelists/downloads/clv1/codelist/Sector.csv' \
    -O Sector.csv
