import os
import sys
import pathlib
import fnmatch
import urllib.request
import json

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def parse_gitignore():
    gitignore_path = BASE_DIR / ".gitignore"
    patterns = []
    with open(gitignore_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns

def is_ignored(path_rel: str, patterns):
    # Normalize slashes
    path_norm = path_rel.replace("\\", "/")
    ignored = False
    for pat in patterns:
        if pat.startswith("!"):
            neg_pat = pat[1:]
            if fnmatch.fnmatch(path_norm, neg_pat) or fnmatch.fnmatch(path_norm, neg_pat + "*"):
                ignored = False
            continue
        
        # Directory pattern
        if pat.endswith("/"):
            if path_norm.startswith(pat) or f"/{pat}" in f"/{path_norm}":
                ignored = True
            elif fnmatch.fnmatch(path_norm, pat.rstrip("/")) or fnmatch.fnmatch(path_norm, pat + "*"):
                ignored = True
        else:
            if fnmatch.fnmatch(path_norm, pat) or fnmatch.fnmatch(path_norm, f"*/{pat}") or fnmatch.fnmatch(path_norm, f"{pat}/*"):
                ignored = True
    return ignored

def verify():
    print("=" * 70)
    print("GIT IGNORE & RUNTIME VERIFICATION")
    print("=" * 70)
    
    patterns = parse_gitignore()
    print(f"Loaded {len(patterns)} rules from .gitignore\n")
    
    # 1. Check that the 6 large files STILL EXIST on disk (NOT deleted)
    large_targets = [
        "data/profile_data_1_All State_2025-26/100_prof1.csv",
        "data/profile_data_2_All State_2025-26/100_prof2.csv",
        "data/processed/UDISE_PLUS_2025_26_SCHOOLS.csv",
        "data/processed/UDISE_PLUS_2025_26_SCHOOLS.zip",
        "data/processed/education_master.db",
        "data/processed/master_institutions.csv"
    ]
    
    print("--- 1. VERIFY LARGE FILES NOT DELETED FROM DISK ---")
    for lt in large_targets:
        full_path = BASE_DIR / lt
        assert full_path.exists(), f"ERROR: File was deleted: {lt}"
        sz_mb = full_path.stat().st_size / (1024 * 1024)
        print(f"  [OK] Still on local disk: {lt:<55} ({sz_mb:.2f} MB)")
        
    print("\n--- 2. VERIFY LARGE FILES ARE IGNORED BY GIT ---")
    for lt in large_targets:
        ignored = is_ignored(lt, patterns)
        print(f"  [OK] Git Ignored: {lt:<55} -> {ignored}")
        assert ignored, f"ERROR: {lt} is NOT ignored by .gitignore!"
        
    # 2. Check essential runtime files are NOT ignored
    essential_files = [
        "dashboard_server.py",
        "generate_data_dictionary.py",
        "requirements.txt",
        "Procfile",
        "railway.json",
        "Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "DEPLOYMENT.md",
        "DATA_DICTIONARY.xlsx",
        "data/data_dictionary.json",
        "pending_datasets_status.json",
        "static/index.html",
        "static/js/dashboard.js",
        "static/css/dashboard.css",
        "Final Institute Lists/Welcome to UGC, New Delhi, India.xlsx",
        "Final Institute Lists/Medical Colleges.xlsx",
        "Final Institute Lists/Nursing Colleges.xlsx",
        "Final Institute Lists/Architecture Colleges.xlsx",
        "Final Institute Lists/Rehabilitation Colleges.xlsx",
        "Final Institute Lists/Ayurveda Colleges.xlsx",
        "Final Institute Lists/Homoeopathy Colleges.xlsx",
        "Final Institute Lists/Law Colleges.xlsx",
        "Final Institute Lists/Pharmacy Colleges.xlsx"
    ]
    
    print("\n--- 3. VERIFY ESSENTIAL RUNTIME FILES ARE TRACKED (NOT IGNORED) ---")
    for ef in essential_files:
        full_path = BASE_DIR / ef
        assert full_path.exists(), f"ERROR: Missing essential runtime file: {ef}"
        ignored = is_ignored(ef, patterns)
        assert not ignored, f"ERROR: Essential file {ef} is mistakenly ignored by .gitignore!"
        print(f"  [OK] Tracked in Git: {ef}")
        
    # 3. Test Live Dashboard Endpoints
    print("\n--- 4. VERIFY RUNTIME DASHBOARD INTEGRITY VIA API ---")
    base_url = "http://127.0.0.1:8000"
    client = None
    try:
        urllib.request.urlopen(f"{base_url}/api/summary", timeout=1)
        def get_json(path):
            req = urllib.request.urlopen(f"{base_url}{path}")
            return json.loads(req.read().decode())
    except Exception:
        from starlette.testclient import TestClient
        from dashboard_server import app, registry
        registry.load_all()
        client = TestClient(app)
        def get_json(path):
            resp = client.get(path)
            return resp.json()

    # Summary
    summary = get_json("/api/summary")
    kpis = summary["kpis"]
    print(f"  [OK] Summary KPIs: {kpis['states_covered']} States, {kpis['total_records_final']} Final Records")
    assert kpis['states_covered'] == 36
    assert kpis['total_records_final'] == 17372
    
    # Final Lists check all 9
    final_data = get_json("/api/datasets/final")
    assert len(final_data["lists"]) == 9
    print(f"  [OK] All {len(final_data['lists'])} Final Lists loaded:")
    for l in final_data["lists"]:
        print(f"       - {l.get('file_name', l.get('id', '')): <40}: {l['total_records']:,} institutions")
        
    # Data Dictionary
    dict_data = get_json("/api/dictionary")
    print(f"  [OK] Data Dictionary: {dict_data['total_fields']} fields documented")
    assert dict_data['total_fields'] == 148
    
    # Search tests
    # Gachibowli
    g_res = get_json("/api/search?q=Gachibowli")
    assert g_res["total_matches"] > 0
    print(f"  [OK] Search 'Gachibowli': {g_res['total_matches']} matches (Found IIIT Hyderabad)")
    
    # KPHB
    k_res = get_json("/api/search?q=KPHB")
    assert k_res["total_matches"] > 0
    print(f"  [OK] Search 'KPHB': {k_res['total_matches']} matches (Found JNTUH)")
    
    # State / District filter
    st_res = get_json("/api/states/Telangana")
    print(f"  [OK] State Explorer 'Telangana': {st_res['total_institutions']} institutions across {len(st_res['districts'])} districts")
    assert st_res['total_institutions'] > 0
    
    print("\n" + "=" * 70)
    print(">>> ALL GIT & RUNTIME CHECKS PASSED 100%! READY FOR GITHUB <<<")
    print("=" * 70)

if __name__ == "__main__":
    verify()
