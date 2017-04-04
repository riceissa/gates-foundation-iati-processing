# Gates Foundation IATI processing

Gates Foundation IATI data is available from the [IATI
Registry](https://iatiregistry.org/publisher/bmgf).

The Gates Foundation IATI data uses version 1.03 of the standard.

    wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-a-f.xml'
    wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-g-m.xml'
    wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-n-s.xml'
    wget 'https://docs.gatesfoundation.org/documents/bmgf-activity-t-z.xml'
    wget 'http://codelists103.archive.iatistandard.org/data/codelist/Country/version/1.01/lang/en.csv' \
        -O Country.csv
    wget 'http://codelists103.archive.iatistandard.org/data/codelist/Region/version/1.0/lang/en.csv' \
        -O Region.csv
    # The aid type CSV from the standard is malformed (fails to escape double
    # quotes) so edit it a little
    wget 'http://codelists103.archive.iatistandard.org/data/codelist/AidType/version/1.0/lang/en.xml' \
        -O AidType.xml
    wget 'http://iatistandard.org/105/codelists/downloads/clv1/codelist/Sector.csv' \
        -O Sector.csv
