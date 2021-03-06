#!/usr/bin/env python3

import xml.etree.ElementTree
import re
import csv
import glob
import json
import sys

from gates_foundation_maps import SECTOR_TO_CAUSE_AREA, \
        SECTOR_TO_DONOR_CAUSE_AREA_URL, DONEE_RENAME

def main():
    try:
        data_dir = sys.argv[1]
    except IndexError:
        print("Please specify a data directory", file=sys.stderr)
        quit()

    # Prepare country codelist
    country_codelist = {}
    with open(data_dir + "/Country.json", "r") as f:
        j = json.load(f)
        for country in j["Country"]:
            # The standard capitalizes country names (which we don't want) so
            # just keep the initial capital letter
            name = country["name"]
            country_codelist[country["code"]] = name[0] + name[1:].lower()

    # Prepare region codelist
    region_codelist = {}
    with open(data_dir + "/Region.json", "r") as f:
        j = json.load(f)
        for region in j["Region"]:
            code = region["code"]
            name = region["name"]
            cruft = ", regional"
            if name.endswith(cruft):
                name = name[:-len(cruft)]
            region_codelist[code] = name

    organization_role_codelist = {}
    with open(data_dir + "/OrganisationRole.json", "r") as f:
        j = json.load(f)
        for role in j["OrganisationRole"]:
            organization_role_codelist[role["code"]] = role["name"]

    # Prepare aid type codelist; the CSV version of the codelist is malformed
    # (doesn't escape quotes correctly) so we use the XML instead
    aidtype_codelist = {}
    with open(data_dir + "/AidType.json", "r") as f:
        j = json.load(f)
        for aidtype in j["AidType"]:
            aidtype_codelist[aidtype["code"]] = aidtype["name"]

    # Prepare sector codelist
    sector_codelist = {}
    with open(data_dir + "/Sector.json", "r") as f:
        j = json.load(f)
        for sector in j["Sector"]:
            code = sector["code"]
            name = sector["name"]
            sector_codelist[code] = name

    transaction_codelist = {}
    with open(data_dir + "/TransactionType.json", "r") as f:
        j = json.load(f)
        for transaction_type in j["TransactionType"]:
            transaction_codelist[transaction_type["code"]] = transaction_type["name"]

    paths = sorted(glob.glob(data_dir + "/bmgf-*.xml"))
    for p in paths:
        print("Doing", p, file=sys.stderr)
        e = xml.etree.ElementTree.parse(p).getroot()
        print_sql(elem2list(e, country_codelist, region_codelist,
                  aidtype_codelist, sector_codelist, organization_role_codelist,
                  transaction_codelist))


def elem2list(xml_element, country_codelist, region_codelist,
              aidtype_codelist, sector_codelist, organization_role_codelist,
              transaction_codelist):
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
        if len(sectors) <= 0:
            # Use "Sectors not specified"
            sectors = xml.etree.ElementTree.fromstring("""<sector percentage="100" code="99810" vocabulary="1"></sector>""")

        # These fields are common among all rows in the activity
        donor = findone(findone(act, 'reporting-org'), 'narrative').text
        # Make sure we're talking about the Gates Foundation
        assert donor == "Bill and Melinda Gates Foundation", donor
        countries = [country_codelist[t.attrib['code']]
                     for t in act.findall("recipient-country")]
        affected_countries = "|".join(countries)
        regions = [code2region(t.attrib['code'], region_codelist)
                   for t in act.findall("recipient-region")]
        affected_regions = "|".join(regions)
        aid_type = aidtype_codelist[findone(act, "default-aid-type").attrib['code']]
        notes = (findone(findone(act, 'description'), 'narrative').text + "; " + "Aid type: " +
                 aid_type)

        implementers = []
        for p in act.findall('participating-org'):
            if organization_role_codelist[p.attrib['role']] == "Funding":
                assert findone(p, "narrative").text == "Bill and Melinda Gates Foundation"
            if organization_role_codelist[p.attrib['role']] == "Implementing":
                implementers.append(findone(p, "narrative").text)
        # This doesn't have to be the case, but as of this writing, for Gates
        # Foundation IATI data, each activity only has one implementing org. If
        # the situation changes we will want to know about it, so place an
        # assertion.
        assert len(implementers) == 1
        implementer = implementers[0]

        # Within each activity, we want a separate SQL row for each
        # (transaction, sector) combination
        transactions = act.findall("transaction")
        for trans in transactions:
            if transaction_codelist[findone(trans, "transaction-type").attrib["code"]] == "Outgoing Commitment":
                # These fields are common among all rows in the transaction
                donee = findone(findone(trans, "receiver-org"), "narrative").text.strip()
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
                provider = findone(findone(trans, "provider-org"), "narrative").text
                assert provider == "Bill and Melinda Gates Foundation"

                for sector in sectors:
                    # Make a new dict and fill in all the fields that are in
                    # common
                    d = {
                        'url': "https://iatiregistry.org/publisher/bmgf",
                        'donation_date_basis': "IATI",
                    }
                    # Fields common on the basis of activity
                    d['donor'] = donor
                    d['affected_countries'] = country_normalized(affected_countries)
                    d['affected_regions'] = affected_regions
                    d['notes'] = notes

                    # Fields common on the basis of transaction
                    d['donee'] = donee_normalized(donee)
                    d['donation_date'] = donation_date
                    d['donation_date_precision'] = donation_date_precision

                    # Fields that require sector information
                    sector_name = sector_codelist[sector.attrib["code"]]

                    # TODO change this back to make sure we know all the sector names
                    # d['cause_area'] = SECTOR_TO_CAUSE_AREA[sector_name]
                    d['cause_area'] = SECTOR_TO_CAUSE_AREA.get(sector_name, sector_name)
                    if sector_name not in SECTOR_TO_CAUSE_AREA:
                        print("unknown sector:", sector_name, file=sys.stderr)

                    # TODO change this back to make sure we know all the sector names
                    # d['donor_cause_area_url'] = SECTOR_TO_DONOR_CAUSE_AREA_URL[sector_name]
                    d['donor_cause_area_url'] = SECTOR_TO_DONOR_CAUSE_AREA_URL.get(sector_name, sector_name)
                    if sector_name not in SECTOR_TO_DONOR_CAUSE_AREA_URL:
                        print("unknown sector:", sector_name, file=sys.stderr)

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


def country_normalized(x):
    if x.lower() == "united states":
        return "United States"
    if x.lower() == "south africa":
        return "South Africa"
    if x.lower() == "united kingdom":
        return "United Kingdom"
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
    main()
