#!/usr/bin/python3

import xml.etree.ElementTree
import sys
import re

def elem2list(xml_element):
    '''
    Take the root node of an XML containing IATI activity information. Here
    xml_element is of type xml.etree.ElementTree.Element, and its children must
    all be iati-activity tags.

    Return a list of dicts.
    '''
    result = []
    for act in xml_element:
        sectors = act.findall("sector")
        assert len(sectors) > 0, "must have at least one sector"

        # These fields are common among all rows in the activity
        donor = act.find('reporting-org').text
        assert len(act.findall('reporting-org')) == 1
        # Make sure we're talking about the Gates Foundation
        assert donor == "Bill and Melinda Gates Foundation"
        countries = [t.attrib['code'] for t in act.findall("recipient-country")]
        affected_countries = ", ".join(countries)

        implementers = []
        for p in act.findall('participating-org'):
            if p.attrib['role'] == "Funding":
                assert p.text == "Bill & Melinda Gates Foundation"
            if p.attrib['role'] == "Implementing":
                implementers.append(p.text)
        # This doesn't have to be the case, but as of this writing, for Gate
        # Foundation IATI data, each activity only has one implementing org
        assert len(implementers) == 1
        implementer = implementers[0]

        # Within each activity, we want a separate SQL row for each combination
        # of transaction and sector
        transactions = act.findall("transaction")
        assert len(transactions) > 0
        for trans in transactions:
            if trans.find("transaction-type").attrib["code"] == "C":
                # These fields are common among all rows in the transaction
                donee = trans.find("receiver-org").text.strip()
                assert len(trans.findall("receiver-org")) == 1
                assert donee == implementer
                donation_date = trans.find('transaction-date').attrib['iso-date']
                assert re.match(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", donation_date)
                donation_date_precision = "day"

                # Save this value for later; we will multiply the total amount
                # by the percentage of the total the sector gets
                total_amount = float(trans.find('value').text)
                assert len(trans.findall('value')) == 1

                # As a sanity check, ensure that the "provider-org" tag under
                # transaction is the Gates Foundation
                provider = trans.find("provider-org").text
                assert provider == "Bill & Melinda Gates Foundation"

                for sector in sectors:
                    # Make new dict and fill in all the fields that are in
                    # common
                    d = {
                        'url': "https://iatiregistry.org/publisher/bmgf",
                        'donation_date_basis': "IATI",
                    }
                    d['donor'] = donor
                    d['affected_countries'] = affected_countries

                    d['donee'] = donee_normalized(donee)
                    d['donation_date'] = donation_date
                    d['donation_date_precision'] = donation_date_precision


                    d['cause_area'] = sector_code2cause_area(sector.attrib["code"])
                    d['donor_cause_area_url'] = "NULL" # TODO
                    # Adjust the amount
                    percent = float(sector.attrib.get("percentage", 100))
                    d['amount'] = total_amount * percent / 100
                    d['notes'] = "NULL" # TODO
                    result.append(d)
    return result

def sector_code2cause_area(code):
    '''
    Convert the DAC five-digit sector code to a string that represents the
    cause area.
    '''
    return "FIXME"

def donee_normalized(x):
    '''
    Normalize and clean up donee string. Return the cleaned up string.
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
    return x

def mysql_quote(x):
    '''
    Quote the string x using MySQL quoting rules. Probably not safe against
    maliciously formed strings.
    '''
    x = x.replace("\\", "\\\\")
    x = x.replace("'", "''")
    return "'{}'".format(x)

def cook_row(t):
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
    ])
    result += ")"
    return result

def print_sql(iati_list):
    '''
    Take a list of IATI activity dicts.
    '''
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries) values""")
    print("    " + ",\n    ".join(cook_row(t) for t in iati_list) + ";")

if __name__ == "__main__":
    paths = [
        "bmgf-activity-a-f.xml",
        "bmgf-activity-g-m.xml",
        "bmgf-activity-n-s.xml",
        "bmgf-activity-t-z.xml",
    ]
    for p in paths:
        e = xml.etree.ElementTree.parse(p).getroot()
        print_sql(elem2list(e))
