#!/usr/bin/env python3

import xml.etree.ElementTree
import re
import csv

from gates_foundation_maps import SECTOR_TO_CAUSE_AREA, \
        SECTOR_TO_DONOR_CAUSE_AREA_URL, DONEE_RENAME


def elem2list(xml_element, country_codelist, region_codelist,
              aidtype_codelist, sector_codelist):
    '''
    Convert the IATI activity tree into a flat list of transactions.

    Take the root node of an XML containing IATI activity information. Here
    xml_element is of type xml.etree.ElementTree.Element, and its children must
    all be iati-activity tags.

    Return a flat list of dicts. Each dict represents a row to be inserted in
    SQL. Each iati-activity element does *not* correspond to a single dict.
    Rather, each iati-activity tag will be used to generate multiple rows. We
    make a new dict for each "commitment" transaction (and ignore other types
    of transactions). If the transaction belongs in multiple DAC sectors, we
    break it down into multiple dicts, one for each sector; in this case, the
    "amount" listed will be whatever percentage of the total amount that
    belongs to that sector.
    '''
    result = []
    for act in xml_element:
        sectors = act.findall("sector")
        assert len(sectors) > 0, "must have at least one sector"

        # These fields are common among all rows in the activity
        donor = findone(act, 'reporting-org').text
        # Make sure we're talking about the Gates Foundation
        assert donor == "Bill and Melinda Gates Foundation"
        countries = [country_codelist[t.attrib['code']]
                     for t in act.findall("recipient-country")]
        affected_countries = ", ".join(countries)
        regions = [code2region(t.attrib['code'], region_codelist)
                   for t in act.findall("recipient-region")]
        affected_regions = ", ".join(regions)
        aid_type = aidtype_codelist[
                findone(act, "default-aid-type") .attrib['code']]
        notes = (findone(act, 'description').text + "; " + "Aid type: " +
                 aid_type)

        implementers = []
        for p in act.findall('participating-org'):
            if p.attrib['role'] == "Funding":
                assert p.text == "Bill & Melinda Gates Foundation"
            if p.attrib['role'] == "Implementing":
                implementers.append(p.text)
        # This doesn't have to be the case, but as of this writing, for Gates
        # Foundation IATI data, each activity only has one implementing org. If
        # the situation changes we will want to know about it, so place an
        # assertion.
        assert len(implementers) == 1
        implementer = implementers[0]

        # Within each activity, we want a separate SQL row for each combination
        # of transaction and sector
        transactions = act.findall("transaction")
        assert len(transactions) > 0
        for trans in transactions:
            if findone(trans, "transaction-type").attrib["code"] == "C":
                # These fields are common among all rows in the transaction
                donee = findone(trans, "receiver-org").text.strip()
                assert donee == implementer
                if donee in DONEE_RENAME:
                    donee = DONEE_RENAME[donee]
                donation_date = findone(trans, 'transaction-date') \
                    .attrib['iso-date']
                assert re.match(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z",
                                donation_date)
                donation_date_precision = "day"

                # Version 1.03 of the standard doesn't seem to document this,
                # but e.g. version 1.05 states that
                # <http://iatistandard.org/105/codelists/AidType/#use-this-codelist-for>
                # the default aid type can be overridden by an "aid-type" tag
                # in a transaction. But the Gates Foundation data doesn't
                # override this anywhere, so we place an assertion that it
                # doesn't, in case this situation changes in future versions of
                # the data.
                assert len(trans.findall("aid-type")) == 0

                # Save this value for later; we will multiply the total amount
                # by the percentage of the total the sector gets
                total_amount = float(findone(trans, 'value').text)

                # As a sanity check, ensure that the "provider-org" tag under
                # transaction is the Gates Foundation
                provider = findone(trans, "provider-org").text
                assert provider == "Bill & Melinda Gates Foundation"

                for sector in sectors:
                    # Make a new dict and fill in all the fields that are in
                    # common
                    d = {
                        'url': "https://iatiregistry.org/publisher/bmgf",
                        'donation_date_basis': "IATI",
                    }
                    # Fields common on the basis of activity
                    d['donor'] = donor
                    d['affected_countries'] = affected_countries
                    d['affected_regions'] = affected_regions
                    d['notes'] = notes

                    # Fields common on the basis of transaction
                    d['donee'] = donee_normalized(donee)
                    d['donation_date'] = donation_date
                    d['donation_date_precision'] = donation_date_precision

                    # Fields that require sector information
                    sector_name = sector_codelist[sector.attrib["code"]]
                    d['cause_area'] = SECTOR_TO_CAUSE_AREA[sector_name]
                    d['donor_cause_area_url'] = SECTOR_TO_DONOR_CAUSE_AREA_URL[
                            sector_name]
                    # Adjust the amount
                    percent = float(sector.attrib.get("percentage", 100))
                    assert percent > 0, "percent is {}, which is too small".format(percent)
                    assert percent <= 100, "percent is {}, which is too big".format(percent)
                    d['amount'] = total_amount * percent / 100
                    result.append(d)
    return result


def findone(element, match):
    '''
    Find exactly one element matching match, and ensure that there is exactly
    one element. Here element is of type xml.etree.ElementTree.Element.
    '''
    assert len(element.findall(match)) == 1
    return element.find(match)


def code2region(code, region_codelist):
    '''
    Convert the region code to the region name.
    '''
    if code in region_codelist:
        return region_codelist[code]
    elif code.lstrip("0") in region_codelist:
        return region_codelist[code.lstrip("0")]
    raise ValueError("cannot decode region")


def donee_normalized(x):
    '''
    Normalize and clean up donee string. Return the cleaned up string.

    The Gates IATI XML promises UTF-8, and it *is* valid UTF-8 as far as I can
    make out, except there's a bunch of Hebrew letters where there shouldn't
    be.
    '''
    x = x.replace("ח", "ç")
    x = x.replace("י", "é")
    x = x.replace("ף", "ó")
    x = x.replace("ד", "ã")
    x = x.replace("ם", "í")
    x = x.replace("צ", "ö")
    x = x.replace("א", "à")
    x = x.replace("ט", "è")
    x = x.replace("ע", "ò")
    x = x.replace("ב", "á")
    x = x.replace("ה", "ä")
    x = x.replace("כ", "ë")
    x = x.replace("\u05b9", "É")
    x = re.sub(r",? inc\.?$", "", x, flags=re.IGNORECASE)
    if x in DONEE_RENAME:
        x = DONEE_RENAME[x]
    return x


def mysql_quote(x):
    '''
    Quote the string x using MySQL quoting rules. If x is the empty string,
    return "NULL". Probably not safe against maliciously formed strings, but
    whatever; our XML input is fixed and from a basically trustable source..
    '''
    if not x:
        return "NULL"
    x = x.replace("\\", "\\\\")
    x = x.replace("'", "''")
    return "'{}'".format(x)


def cooked_row(t):
    '''
    Take a transaction dictionary t. Return a string that can be used directly
    in a SQL insert statement (without trailing comma).
    '''
    result = "("
    result += ",".join([
        mysql_quote(t['donor']),
        mysql_quote(t['donee']),
        str(t['amount']),
        mysql_quote(t['donation_date']),
        mysql_quote(t['donation_date_precision']),
        mysql_quote(t['donation_date_basis']),
        mysql_quote(t['cause_area']),
        mysql_quote(t['url']),
        mysql_quote(t['donor_cause_area_url']),
        mysql_quote(t['notes']),
        mysql_quote(t['affected_countries']),
        mysql_quote(t['affected_regions']),
    ])
    result += ")"
    return result


def print_sql(iati_list):
    '''
    Take a list of IATI activity dicts.
    '''
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries,
    affected_regions) values""")
    print("    " + ",\n    ".join(cooked_row(t) for t in iati_list) + ";")


if __name__ == "__main__":
    # Prepare country codelist
    country_codelist = {}
    with open("Country.csv", newline='') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            code, name, _ = row
            # The standard capitalizes country names (which we don't want) so
            # just keep the initial capital letter
            country_codelist[code] = name[0] + name[1:].lower()

    # Prepare region codelist
    region_codelist = {}
    with open("Region.csv", newline='') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            code, name = row
            cruft = ", regional"
            if name.endswith(cruft):
                name = name[:-len(cruft)]
            region_codelist[code] = name

    # Prepare aid type codelist; the CSV version of the codelist is malformed
    # (doesn't escape quotes correctly) so we use the XML instead
    aidtype_codelist = {}
    e = xml.etree.ElementTree.parse("AidType.xml").getroot()
    for aidtype in e:
        aidtype_codelist[aidtype.find("code").text] = aidtype.find("name").text

    # Prepare sector codelist
    sector_codelist = {}
    with open("Sector.csv", newline='') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            code, name, _, _, _, _, _ = row
            sector_codelist[code] = name

    paths = [
        "bmgf-activity-a-f.xml",
        "bmgf-activity-g-m.xml",
        "bmgf-activity-n-s.xml",
        "bmgf-activity-t-z.xml",
    ]
    for p in paths:
        e = xml.etree.ElementTree.parse(p).getroot()
        print_sql(elem2list(e, country_codelist, region_codelist,
                  aidtype_codelist, sector_codelist))
