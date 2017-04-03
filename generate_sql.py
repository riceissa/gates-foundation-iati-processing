#!/usr/bin/python3

import xml.etree.ElementTree

def elem2list(xml_element):
    '''
    Take the root node of an XML containing IATI activity information. Here
    xml_element is of type xml.etree.ElementTree.Element, and its children must
    all be iati-activity tags.

    Return a list of dicts.
    '''
    for act in xml_element:
        donor = act.find('reporting-org').text
        url = "https://iatiregistry.org/publisher/bmgf"
        countries = [t.attrib['code'] for t in act.findall("recipient-country")]
        affected_countries = ", ".join(countries)
        for trans in act.findall("transaction"):
            # Make new dict and fill in all the fields that are in common
            d = {}
            d['donor'] = donor
            d['url'] = url
            d['cause_area'] =
            d['affected_countries'] = 
            d['donation_date_basis'] = "IATI"
            """
            donor_cause_area_url,
            notes,
            affected_states"""

            d['amount'] = float(trans.find('value').text)
            d['donee'] = trans.find("receiver-org").text.strip()
            d['donation_date'] = trans.find('transaction-date').attrib['iso-date']
            d['donation_date_precision'] = "day"

def mysql_quote(x):
    '''
    Quote the string x using MySQL quoting rules. Probably not safe against
    maliciously formed strings.
    '''
    x = x.replace("\\", "\\\\")
    x = x.replace("'", "''")
    return "'{}'".format(x)

def print_sql(iati_list):
    '''
    Take a list of IATI activity dicts.
    '''
    print("""insert into donations (donor, donee, amount, donation_date,
    donation_date_precision, donation_date_basis, cause_area, url,
    donor_cause_area_url, notes, affected_countries, affected_states) values""")
    for t in iati_list:
        print()

if __name__ == "__main__":
    e = xml.etree.ElementTree.parse(xml_path).getroot()
