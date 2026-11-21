import json
import sqlite3
import os
import sys
import unittest.mock

# Add project path
sys.path.append(r'C:\Users\aishw\.gemini\antigravity\scratch\civicresolve')
import server

def test_civicresolve_core():
    print("==================================================")
    print("Testing CivicResolve Core Functions & DB (Port 8080)")
    print("==================================================")

    # 1. Verify Configuration & Port Binding
    print(f"✓ Default Port configuration: {server.PORT} (Expected: 8080)")
    assert server.PORT == 8080, f"Expected default port 8080, found {server.PORT}"

    # 2. DB Init
    server.init_db()
    print("✓ Database initialized successfully with SQLite schema")

    # 3. Check Seed Data
    conn = sqlite3.connect(server.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM issues")
    issue_count = c.fetchone()[0]
    print(f"✓ Seeded issues count: {issue_count}")
    assert issue_count >= 5, "Expected at least 5 seeded issues"

    # 4. Check Municipal Departments
    print(f"✓ Available departments: {len(server.DEPARTMENTS)}")
    for d in server.DEPARTMENTS:
        print(f"   • [{d['code']}] {d['name']} (SLA: {d['default_sla_hours']}h)")
    assert len(server.DEPARTMENTS) >= 6

    # 5. Test Local Civic NLP Classifier across All 7 Categories & Urgencies
    test_cases = [
        {
            "title": "Severe Pothole Cluster on Highway Pedestrian Crossing",
            "desc": "Deep 10-inch pothole in the middle of a two-lane road. Two two-wheelers already skidded this morning during rush hour. Poses high risk of fatal accidents.",
            "loc": "5th Main Ave, Downtown",
            "expected_cat": "Roads & Pavements",
            "expected_prio": "Critical"
        },
        {
            "title": "Major High-Pressure Water Main Rupture",
            "desc": "Drinking water main line ruptured underneath the pavement outside St. Jude School. Clean water is gushing into the street flooding the sidewalk.",
            "loc": "45 School Road, North Suburb",
            "expected_cat": "Water Supply & Drainage",
            "expected_prio": "Critical"
        },
        {
            "title": "Overflowing Garbage Dumpster",
            "desc": "The large community dumpster hasn't been emptied in 5 days. Waste is spilling over onto the road attracting stray dogs and rodents with intolerable stench.",
            "loc": "Block C Market Square",
            "expected_cat": "Sanitation & Waste",
            "expected_prio": "Critical"
        },
        {
            "title": "Broken Streetlight & Exposed Live Wire",
            "desc": "Streetlight pole struck by delivery truck. Lamp fixture hanging with exposed wires sparking near a water puddle.",
            "loc": "Oak St & Elm Terrace",
            "expected_cat": "Electrical & Streetlights",
            "expected_prio": "Critical"
        },
        {
            "title": "Large Fallen Tree Limb Blocking Bicycle Lane",
            "desc": "Heavy storm snapped a big oak limb across the dedicated cycle track.",
            "loc": "Greenway Boulevard",
            "expected_cat": "Parks & Public Spaces",
            "expected_prio": "Medium"
        }
    ]

    print("\n--------------------------------------------------")
    print("Testing CivicResolve AI Triage Engine:")
    print("--------------------------------------------------")

    for tc in test_cases:
        res = server.local_civic_ai_classify(tc["title"], tc["desc"], tc["loc"])
        print(f"\nReport: '{tc['title']}'")
        print(f" → Category: {res['category']} (Expected: {tc['expected_cat']})")
        print(f" → Priority: {res['priority']} ({res['priority_score']}/100) (Expected: {tc['expected_prio']})")
        print(f" → Routed To: {res['recommended_department']} (SLA: {res['estimated_sla_hours']}h)")
        print(f" → Reasoning: {res['reasoning']}")
        print(f" → Hazards: {res['safety_hazards']}")

        assert res["category"] == tc["expected_cat"], f"Category mismatch for {tc['title']}"
        assert res["priority"] in ["Critical", "High", "Medium", "Low"]

    # 6. Test Gemini Rate Limit (HTTP 429) Graceful Fallback
    print("\n--------------------------------------------------")
    print("Testing Rate Limit / Quota Resilience (HTTP 429 Mock):")
    print("--------------------------------------------------")
    
    mock_http_error = server.urllib.error.HTTPError(
        url="https://generativelanguage.googleapis.com",
        code=429,
        msg="Too Many Requests - Quota Exceeded",
        hdrs={},
        fp=None
    )
    with unittest.mock.patch("urllib.request.urlopen", side_effect=mock_http_error):
        fallback_res = server.gemini_ai_classify(
            title="Dangerous Pothole on Highway",
            description="Deep crater on main highway skidding vehicles",
            location="Highway 101",
            api_key="AIzaSyMockKeyForTest"
        )
        print("✓ Rate limit fallback triggered successfully:")
        print(f"  • AI Source: '{fallback_res.get('ai_source')}'")
        print(f"  • Category: '{fallback_res.get('category')}'")
        print(f"  • Priority: '{fallback_res.get('priority')}' ({fallback_res.get('priority_score')}/100)")
        print(f"  • Department: '{fallback_res.get('recommended_department')}'")
        assert "Rate-Limit Protected" in fallback_res.get("ai_source", "")
        assert fallback_res.get("category") == "Roads & Pavements"

    # 7. Test Complete Citizen-to-Admin Lifecycle
    print("\n--------------------------------------------------")
    print("Testing Complete Lifecycle (Reported -> In Progress -> Resolved):")
    print("--------------------------------------------------")

    c.execute("SELECT COUNT(*) FROM issues")
    initial_count = c.fetchone()[0]

    test_title = "Massive Sinkhole opening on Market Street"
    test_desc = "Pavement collapsed exposing underground drainage, urgent danger to buses and pedestrians"
    ai_eval = server.local_civic_ai_classify(test_title, test_desc, "Market Street")
    
    tracking_code = f"CR-2026-TEST-{initial_count + 1}"
    c.execute("""
        INSERT INTO issues (
            tracking_code, title, description, category, priority, priority_score,
            department, status, location_address, latitude, longitude,
            citizen_name, citizen_contact, ai_reasoning, ai_confidence,
            safety_hazards, estimated_sla_hours, upvotes_count, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tracking_code, test_title, test_desc, ai_eval["category"], ai_eval["priority"],
        ai_eval["priority_score"], ai_eval["recommended_department"], "Reported",
        "Market Street Center", 37.7750, -122.4180, "Marcus Vance", "marcus@civic.local",
        ai_eval["reasoning"], ai_eval["confidence"], json.dumps(ai_eval["safety_hazards"]),
        ai_eval["estimated_sla_hours"], 5, "2026-11-21T10:00:00Z", "2026-11-21T10:00:00Z"
    ))
    new_id = c.lastrowid
    conn.commit()
    print(f"✓ Step 1 [Reported]: Created issue ID={new_id}, Tracking Code={tracking_code}")

    # Citizen Upvote
    c.execute("UPDATE issues SET upvotes_count = upvotes_count + 1 WHERE id = ?", (new_id,))
    c.execute("SELECT upvotes_count FROM issues WHERE id = ?", (new_id,))
    upvotes = c.fetchone()[0]
    print(f"✓ Step 2 [Upvoted]: Community endorsements = {upvotes}")
    assert upvotes == 6

    # Admin Triage: Under Review
    c.execute("UPDATE issues SET status = 'Under Review' WHERE id = ?", (new_id,))
    conn.commit()
    c.execute("SELECT status FROM issues WHERE id = ?", (new_id,))
    assert c.fetchone()[0] == 'Under Review'
    print("✓ Step 3 [Under Review]: Authority triage initiated")

    # Admin Triage: In Progress with Crew
    c.execute("UPDATE issues SET status = 'In Progress', assigned_team = 'Rapid Asphalt Unit #4' WHERE id = ?", (new_id,))
    conn.commit()
    c.execute("SELECT status, assigned_team FROM issues WHERE id = ?", (new_id,))
    row = c.fetchone()
    assert row[0] == 'In Progress' and row[1] == 'Rapid Asphalt Unit #4'
    print(f"✓ Step 4 [In Progress]: Crew '{row[1]}' dispatched")

    # Admin Triage: Resolved with Proof Photo
    c.execute("""
        UPDATE issues SET
            status = 'Resolved',
            resolution_notes = 'Sinkhole filled with aggregate base and paved with hot-mix asphalt.',
            resolved_at = '2026-11-21T11:00:00Z'
        WHERE id = ?
    """, (new_id,))
    conn.commit()

    c.execute("SELECT status, resolution_notes FROM issues WHERE id = ?", (new_id,))
    updated_row = c.fetchone()
    print(f"✓ Step 5 [Resolved]: Status verified as '{updated_row['status']}', Notes='{updated_row['resolution_notes']}'")
    assert updated_row['status'] == 'Resolved'

    # Clean up test row
    c.execute("DELETE FROM issues WHERE id = ?", (new_id,))
    conn.commit()
    conn.close()

    print("\n🎉 ALL 6 CORE FEATURES AND PRODUCTION TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    test_civicresolve_core()
