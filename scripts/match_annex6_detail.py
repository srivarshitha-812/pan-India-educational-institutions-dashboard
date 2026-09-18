import json
import re

with open('data/vci_raw/parsed_recognized.json') as f:
    rec = json.load(f)
with open('data/vci_raw/annexure6_addresses.json') as f:
    annex6 = json.load(f)

# Normalize state names in annex6
state_map = {
    'ndhra': 'Andhra Pradesh',
    'ssam': 'Assam',
    'ihar': 'Bihar',
    'hhattisgarh': 'Chhattisgarh',
    'ujarat': 'Gujarat',
    'aryana': 'Haryana',
    'imachal': 'Himachal Pradesh',
    'ammu': 'Jammu and Kashmir',
    'harkhand': 'Jharkhand',
    'arnataka': 'Karnataka',
    'erala': 'Kerala',
    'adhya': 'Madhya Pradesh',
    'aharashtra': 'Maharashtra',
    'izoram': 'Mizoram',
    'disha': 'Odisha',
    'uducherry': 'Puducherry',
    'unjab': 'Punjab',
    'ajasthan': 'Rajasthan',
    'amil': 'Tamil Nadu',
    'elangana': 'Telangana',
    'ripura': 'Tripura',
    'ttar': 'Uttar Pradesh',
    'ttarakhand': 'Uttarakhand',
    'est': 'West Bengal'
}

def clean_state(raw_st):
    raw_lower = raw_st.lower()
    for k, v in state_map.items():
        if k in raw_lower:
            return v
    return raw_st.strip().title()

for a in annex6:
    a['clean_state'] = clean_state(a['state'])

print(f"Total Annexure 6 colleges: {len(annex6)}")
for i, a in enumerate(annex6):
    print(f"{i+1:02d}. [{a['clean_state']}] {a['college_name']} | Addr: {a['address'][:50]}...")
