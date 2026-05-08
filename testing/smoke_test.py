import urllib.request, json, sys

BASE = "http://localhost:8000"
results = []

def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read())

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
          headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def put(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
          headers={"Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def run_check(num, label, fn):
    try:
        r = fn()
        print("PASS [%2d] %s" % (num, label))
        results.append(("PASS", num, label))
        return r
    except Exception as e:
        print("FAIL [%2d] %s" % (num, label))
        print("       Error: %s" % e)
        results.append(("FAIL", num, label))
        return None

# 1. GET /config
def test1():
    cfg = get("/config")
    for f in ["ss_rate", "medicare_rate", "futa_rate"]:
        assert f in cfg, "Missing: %s" % f
    return cfg
run_check(1, "GET /config -> ss_rate, medicare_rate, futa_rate", test1)

# 2. GET /suta-rates
def test2():
    rates = get("/suta-rates")
    assert isinstance(rates, list), "Not a list"
    assert len(rates) == 51, "Expected 51, got %d" % len(rates)
    return rates
run_check(2, "GET /suta-rates -> 51 state rows", test2)

# 3. POST /clients
new_client = [None]
def test3():
    result = post("/clients", {})
    assert "id" in result, "No id in response: %s" % result
    new_client[0] = result
    return result
run_check(3, "POST /clients {} -> {id: ...}", test3)

# 4. GET /clients/{id}
def test4():
    assert new_client[0], "No client from test 3"
    client = get("/clients/%d" % new_client[0]["id"])
    assert client["id"] == new_client[0]["id"], "ID mismatch"
    return client
run_check(4, "GET /clients/{id} -> client record", test4)

# 5. PUT /clients/{id}
def test5():
    assert new_client[0], "No client from test 3"
    updated = put("/clients/%d" % new_client[0]["id"], {"legal_name": "Test Corp"})
    assert updated["legal_name"] == "Test Corp", "Name not updated: %s" % updated.get("legal_name")
    return updated
run_check(5, "PUT /clients/{id} with legal_name -> updated", test5)

# 6. GET /clients list
def test6():
    clients = get("/clients")
    assert isinstance(clients, list), "Not a list"
    assert new_client[0], "No client from test 3"
    ids = [c["id"] for c in clients]
    assert new_client[0]["id"] in ids, "New client not in list"
    return clients
run_check(6, "GET /clients -> list includes new client", test6)

# 7. POST /calculate
def test7():
    payload = {
        "ftes": 10, "ptes": 2, "w2s_generated": 12,
        "wc_lines": [{"state": "TX", "wc_code": "8810", "annual_gw": 500000,
                      "ftes": 10, "ptes": 2, "current_client_rate": 0.5, "manual_rate": 1.2}],
        "proposed_mod": 1.0, "wc_carve_out": False,
        "suta_lines": [{"state": "TX", "gws": 500000, "total_wses": 11.5,
                        "billing_rate": 0.027, "cost_rate": 0.018, "threshold": 9000,
                        "turnover_pct": 0.1, "current_client_rate": 0.03}],
        "admin_method": 1, "admin_rate": 0.05, "payroll_frequency": "biweekly",
        "wc_policy_adj": 0.0,
        "internal_commission_pct": 0.25, "external_commission_pct": 0.0,
        "broker_wc_commission_pct": 0.0,
        "implementation_fee": 0.0, "epli_fee": 0.0, "tlm_fee": 0.0, "wire_ach_fee": 0.0
    }
    result = post("/calculate", payload)
    for key in ["admin_overview", "wc_overview", "taxes_overview"]:
        assert key in result, "Missing key: %s" % key
    return result
run_check(7, "POST /calculate -> summary with admin_overview, wc_overview, taxes_overview", test7)

# 8-10. Static HTML files
for num, path, label in [
    (8,  "/static/dashboard.html", "GET /static/dashboard.html -> 200"),
    (9,  "/static/client.html",    "GET /static/client.html -> 200"),
    (10, "/static/config.html",    "GET /static/config.html -> 200"),
]:
    def make_test(p):
        def t():
            with urllib.request.urlopen(BASE + p) as r:
                assert r.status == 200, "Status %d" % r.status
        return t
    run_check(num, label, make_test(path))

# Summary
print()
print("=" * 50)
passed = sum(1 for r in results if r[0] == "PASS")
failed = sum(1 for r in results if r[0] == "FAIL")
print("Results: %d PASS, %d FAIL" % (passed, failed))
if failed > 0:
    sys.exit(1)
