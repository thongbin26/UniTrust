import httpx
import sys

def main():
    print("--- 3. Health Checks ---")
    r1 = httpx.get("http://127.0.0.1:8000/health")
    print(f"Backend /health: {r1.status_code}")
    
    r2 = httpx.get("http://127.0.0.1:8501/healthz")
    print(f"Frontend /healthz: {r2.status_code} - {r2.text}")
    
    print("\n--- 5. Demo Cases via /verify ---")
    
    # Case A
    case_a = "Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 26/06/2026."
    res_a = httpx.post("http://127.0.0.1:8000/verify", json={"text": case_a}, timeout=20.0)
    print(f"Case A HTTP Status: {res_a.status_code}")
    if res_a.status_code == 200:
        data = res_a.json()["results"][0]
        print(f"  Trust State: {data['verdict']}")
        print(f"  Temporal State: {data['temporal_status']}")
        print(f"  Abstention: {data.get('abstention_reason')}")
        prov = data.get("primary_provenance")
        print(f"  Provenance: {'Present' if prov else 'None'} " + (f"(notice_id={prov['notice_id']}, version_id={prov['version_id']})" if prov else ""))

    # Case B
    case_b = "Sinh viên khóa 2022 ngành CNTT ký tên theo danh sách lớp và nộp 01 ảnh thẻ 2x3 trước 16h00 ngày 30/06/2026."
    res_b = httpx.post("http://127.0.0.1:8000/verify", json={"text": case_b}, timeout=20.0)
    print(f"\nCase B HTTP Status: {res_b.status_code}")
    if res_b.status_code == 200:
        data = res_b.json()["results"][0]
        print(f"  Trust State: {data['verdict']}")
        print(f"  Temporal State: {data['temporal_status']}")
        print(f"  Abstention: {data.get('abstention_reason')}")
        prov = data.get("primary_provenance")
        print(f"  Provenance: {'Present' if prov else 'None'} " + (f"(notice_id={prov['notice_id']}, version_id={prov['version_id']})" if prov else ""))

    # Case C
    case_c = "Đại học yêu cầu sinh viên đi học mặc áo màu đỏ"
    res_c = httpx.post("http://127.0.0.1:8000/verify", json={"text": case_c}, timeout=20.0)
    print(f"\nCase C HTTP Status: {res_c.status_code}")
    if res_c.status_code == 200:
        data = res_c.json()["results"][0]
        print(f"  Trust State: {data['verdict']}")
        print(f"  Temporal State: {data['temporal_status']}")
        print(f"  Abstention: {data.get('abstention_reason')}")
        prov = data.get("primary_provenance")
        print(f"  Provenance: {'Present' if prov else 'None'} " + (f"(notice_id={prov['notice_id']}, version_id={prov['version_id']})" if prov else ""))

    print("\n--- 6. Evidence Endpoints ---")
    ev1 = httpx.get("http://127.0.0.1:8000/evidence/notices/13")
    print(f"GET /evidence/notices/13: {ev1.status_code}")
    
    ev2 = httpx.get("http://127.0.0.1:8000/evidence/notices/13/versions")
    print(f"GET /evidence/notices/13/versions: {ev2.status_code} - {ev2.json() if ev2.status_code == 200 else ''}")
    
    ev3 = httpx.get("http://127.0.0.1:8000/evidence/notices/13/changes")
    print(f"GET /evidence/notices/13/changes: {ev3.status_code} - {ev3.json() if ev3.status_code == 200 else ''}")

    print("\n--- 7. For You Endpoint ---")
    fy = httpx.post("http://127.0.0.1:8000/for-you", json={"major": "CNTT", "cohort": "K22"})
    print(f"POST /for-you: {fy.status_code}")
    if fy.status_code == 200:
        obs = fy.json()["obligations"]
        applies = sum(1 for o in obs if o["applicability"]["status"] == "APPLIES")
        does_not_apply = sum(1 for o in obs if o["applicability"]["status"] == "DOES_NOT_APPLY")
        unknown = sum(1 for o in obs if o["applicability"]["status"] == "UNKNOWN")
        print(f"APPLIES: {applies}")
        print(f"DOES_NOT_APPLY: {does_not_apply}")
        print(f"UNKNOWN: {unknown}")

if __name__ == "__main__":
    main()
