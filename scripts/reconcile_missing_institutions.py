import os
import re
import pandas as pd
import openpyxl
import PyPDF2
from collections import defaultdict

# --- Step 1: Helper Normalization Functions ---
def clean_str(s):
    if not s or pd.isna(s):
        return ""
    s = str(s).strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def normalize_name(name):
    if not name:
        return ""
    n = clean_str(name).upper()
    n = re.sub(r'[^A-Z0-9\s]', ' ', n)
    # Remove generic tokens
    tokens_to_remove = [
        'COLLEGE OF NURSING', 'SCHOOL OF NURSING', 'INSTITUTE OF NURSING SCIENCES',
        'INSTITUTE OF NURSING', 'COLLEGE OF NURSE', 'SCHOOL OF NURSE',
        'NURSING SCHOOL', 'NURSING COLLEGE', 'NURSING INSTITUTE',
        'NURSING TRAINING SCHOOL', 'NURSING TRAINING INSTITUTE',
        'MPHW F TRAINING SCHOOL', 'MPHW F TRAINING INSTITUTE',
        'MPHW TRAINING SCHOOL', 'ANM TRAINING SCHOOL', 'GNM TRAINING SCHOOL'
    ]
    for t in sorted(tokens_to_remove, key=len, reverse=True):
        n = n.replace(t, ' ')
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def extract_pincode(text):
    if not text:
        return ""
    m = re.findall(r'\b[1-9]\d{5}\b', str(text))
    return m[-1] if m else ""

def normalize_state(s):
    if not s:
        return ""
    s = clean_str(s).upper()
    mapping = {
        'ANDAMAN & NICOBAR': 'ANDAMAN & NICOBAR',
        'ANDAMAN AND NICOBAR': 'ANDAMAN & NICOBAR',
        'ANDHRA PRADESH': 'ANDHRA PRADESH',
        'ARUNACHAL PRADESH': 'ARUNACHAL PRADESH',
        'ASSAM': 'ASSAM',
        'BIHAR': 'BIHAR',
        'CHANDIGARH': 'CHANDIGARH',
        'CHATTISGARH': 'CHHATTISGARH',
        'CHHATTISGARH': 'CHHATTISGARH',
        'DADRA & NAGAR HAVELI': 'DADRA & NAGAR HAVELI',
        'DAMAN & DIU': 'DAMAN & DIU',
        'DELHI': 'DELHI',
        'GOA': 'GOA',
        'GUJARAT': 'GUJARAT',
        'HARYANA': 'HARYANA',
        'HIMACHAL PRADESH': 'HIMACHAL PRADESH',
        'JAMMU & KASHMIR': 'JAMMU & KASHMIR',
        'JHARKHAND': 'JHARKHAND',
        'KARNATAKA': 'KARNATAKA',
        'KERALA': 'KERALA',
        'LADAKH': 'LADAKH',
        'LAKSHADWEEP': 'LAKSHADWEEP',
        'MADHYA PRADESH': 'MADHYA PRADESH',
        'MAHARASHTRA': 'MAHARASHTRA',
        'MANIPUR': 'MANIPUR',
        'MEGHALAYA': 'MEGHALAYA',
        'MIZORAM': 'MIZORAM',
        'NAGALAND': 'NAGALAND',
        'ORISSA': 'ODISHA',
        'ODISHA': 'ODISHA',
        'PONDICHERRY': 'PUDUCHERRY',
        'PUDUCHERRY': 'PUDUCHERRY',
        'PUNJAB': 'PUNJAB',
        'RAJASTHAN': 'RAJASTHAN',
        'SIKKIM': 'SIKKIM',
        'TAMILNADU': 'TAMIL NADU',
        'TAMIL NADU': 'TAMIL NADU',
        'TELANGANA': 'TELANGANA',
        'TRIPURA': 'TRIPURA',
        'UTTAR PRADESH': 'UTTAR PRADESH',
        'UTTARANCHAL': 'UTTARAKHAND',
        'UTTARAKHAND': 'UTTARAKHAND',
        'WEST BENGAL': 'WEST BENGAL'
    }
    return mapping.get(s, s)

print("Helper functions compiled.")
