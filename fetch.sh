#!/bin/bash
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-a-c.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-d-f.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-g-h.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-i.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-j-l.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-m-o.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-p-r.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-s-t.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-u.xml'
wget 'https://docs.gatesfoundation.org/Documents/bmgf-activity-v-z.xml'

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
