"""
Unit tests for data cleaner and normalizer.
"""
from src.cleaner import clean_text, normalize_name, clean_state, clean_district, clean_pincode, clean_coordinates

def test_clean_text():
    assert clean_text("  Govt. High School   \n") == "Govt. High School"
    assert clean_text(None) == ""
    assert clean_text("<p>School Name</p>") == "School Name"

def test_normalize_name():
    assert normalize_name("Govt. High Sch. Khammam") == "GOVERNMENT HIGH SCHOOL KHAMMAM"
    assert normalize_name("Z.P.H.S. Wyra") == "ZP HIGH SCHOOL WYRA"
    assert normalize_name("St. Joseph Coll. of Engg.") == "ST JOSEPH COLLEGE OF ENGINEERING"

def test_clean_state():
    assert clean_state("Telangana State") == "TELANGANA"
    assert clean_state("TG") == "TELANGANA"
    assert clean_state("NCT of Delhi") == "DELHI"

def test_clean_district():
    assert clean_district("Khammam District") == "KHAMMAM"
    assert clean_district("HYDERABAD DT.") == "HYDERABAD"

def test_clean_pincode():
    assert clean_pincode("507001") == "507001"
    assert clean_pincode("Pin: 507002, India") == "507002"
    assert clean_pincode("invalid") == ""

def test_clean_coordinates():
    lat, lon = clean_coordinates("17.2472", "80.1514")
    assert lat == 17.2472
    assert lon == 80.1514
    # Out of bounds test
    lat_invalid, lon_invalid = clean_coordinates("55.00", "150.00")
    assert lat_invalid is None
    assert lon_invalid is None
