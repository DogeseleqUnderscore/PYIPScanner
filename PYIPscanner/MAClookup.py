from CLIhelpers import *
import json

filepath = "mac_vendors.json"

"""
                                            VERY IMPORTANT!!!!!!!!
    The database that i am using here comes from maclookup.app website (https://maclookup.app/downloads/json-database),
    And is modified to be smaller (~2MB instead od ~6MB but has the same vendors), it instead of having JSON with "JSONS"
    that have the prexix, vendor and other things, only has the prefix as key and vendor as value.
    
    The date that this database comes from is 31.1.2025 (in DD-MM-YYYY format).
    
    Even if the website doesn't provide a license, i will still include this message.
"""

def _get_vendor_from_mac(macaddr):
    prefix_MA_L = macaddr[:8]
    prefix_MA_M = macaddr[:10]
    prefix_MA_S = macaddr[:13]

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

        try:
            return data[prefix_MA_S]
        except KeyError:
            try:
                return data[prefix_MA_M]
            except KeyError:
                try:
                    return data[prefix_MA_L]
                except KeyError:
                    return "[N/D]"



def get_vendor_from_mac_address_no_this_is_not_made_by_chatgpt_trust_me(macaddr: str):
    manufacturer = _get_vendor_from_mac(macaddr)
    return manufacturer



if __name__ == "__main__": # Testing
    test_macs = [
        "48:9E:BD:B4:EA:25",
        "94:A9:90:6A:46:4C",
        "00:50:56:00:00:01",
        "08:00:27:00:00:01", # Real MACs
        "8C:1F:64:97:26:4C",
        "34:D7:F5:40:00:01",
        "8C:1F:64:53:10:01", # MACs with stupid prefixes
        "FF:FF:FF:00:00:01", # Test for non-existent MACs
    ]

    for mac in test_macs:
        vendor = get_vendor_from_mac_address_no_this_is_not_made_by_chatgpt_trust_me(mac)
        print_info(vendor)

    #The result should look like this:
    """
    [#] >> HP Inc.
    [#] >> Espressif Inc.
    [#] >> VMware, Inc.
    [#] >> PCS Systemtechnik GmbH
    [#] >> Federant LLC
    [#] >> Shenzhen Huchi Technology Co.,Ltd.
    [#] >> EA Elektro-Automatik GmbH
    [#] >> [N/D]
    """

