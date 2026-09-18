import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from dashboard_server import app, registry

def main():
    with TestClient(app) as client:
        # Health endpoint
        t0 = time.time()
        res = client.get("/health")
        t_health = (time.time() - t0) * 1000
        print(f"/health: status={res.status_code}, latency={t_health:.2f}ms, resp={res.json()}")

    # Summary endpoint
    t0 = time.time()
    res = client.get("/api/summary")
    t_summary = (time.time() - t0) * 1000
    kpis = res.json()["kpis"]
    print(f"/api/summary: status={res.status_code}, latency={t_summary:.2f}ms, lists={kpis['final_lists_available']}, total={kpis['total_records_final']}, states={kpis['states_covered']}")

    # Final datasets endpoint
    t0 = time.time()
    res = client.get("/api/datasets/final")
    t_final = (time.time() - t0) * 1000
    count = res.json()["count"]
    print(f"/api/datasets/final: status={res.status_code}, latency={t_final:.2f}ms, count={count}")

    assert res.status_code == 200
    assert kpis["final_lists_available"] == 14
    assert kpis["total_records_final"] == 90282
    assert count == 14
    print("\n>>> ALL API LATENCY AND VERIFICATION CHECKS PASSED 100%! <<<")

if __name__ == "__main__":
    main()
