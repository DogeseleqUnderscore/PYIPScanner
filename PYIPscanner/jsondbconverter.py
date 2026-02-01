import json

file = "mac-vendors-export.json"
target = "mac_vendors_list.json"

with open(file, "r", encoding="utf-8") as f:
    data = json.load(f)
    converted = {}
    for entry in data:
        converted[entry["macPrefix"]] = entry['vendorName']

    with open(target, "w", encoding="utf-8") as file:
        json.dump(converted, file, indent=4, ensure_ascii=False)
