#!/usr/bin/env python3
"""
CivicResolve - AI-Powered Civic Issue Reporting & Resolution Platform
Backend Server & REST API using Python standard library (zero external dependencies required)
Features:
- SQLite persistence with automatic schema migrations & demo data seeding
- Google Gemini API integration (REST via urllib) for AI categorization, urgency detection & department routing
- High-accuracy local civic NLP / heuristic classifier fallback when API key is not present or offline
- Multimodal image support for complaint submissions and resolution proof
- Complete Citizen and Municipal Authority REST endpoints
"""

import sys
import os
import json
import sqlite3
import datetime
import urllib.request
import urllib.error
import urllib.parse
import mimetypes
import re
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Paths & Settings
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DB_PATH = BASE_DIR / "civicresolve.db"
PORT = int(os.environ.get("PORT", 8080))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Standard Civic Departments
DEPARTMENTS = [
    {
        "code": "PWD",
        "name": "Public Works & Road Maintenance",
        "icon": "road",
        "description": "Responsible for potholes, asphalt repair, pavements, bridges, and road infrastructure.",
        "default_sla_hours": 24,
        "contact_email": "roads@civicresolve.local"
    },
    {
        "code": "SWM",
        "name": "Sanitation & Waste Management",
        "icon": "trash-2",
        "description": "Handles garbage collection, overflowing dumpsters, illegal dumping, and public cleaning.",
        "default_sla_hours": 12,
        "contact_email": "sanitation@civicresolve.local"
    },
    {
        "code": "BWSSB",
        "name": "Water Supply & Sewerage Board",
        "icon": "droplet",
        "description": "Manages drinking water pipelines, main pipe bursts, sewage overflow, and storm drainage.",
        "default_sla_hours": 18,
        "contact_email": "waterboard@civicresolve.local"
    },
    {
        "code": "ELEC",
        "name": "Electrical & Streetlight Authority",
        "icon": "zap",
        "description": "Operates street lighting, damaged utility poles, exposed live wiring, and transformer safety.",
        "default_sla_hours": 24,
        "contact_email": "electricity@civicresolve.local"
    },
    {
        "code": "PARKS",
        "name": "Parks, Trees & Horticulture",
        "icon": "trees",
        "description": "Maintains municipal parks, fallen trees or dangerous branches blocking transit pathways.",
        "default_sla_hours": 36,
        "contact_email": "parks@civicresolve.local"
    },
    {
        "code": "TRAFFIC",
        "name": "Traffic Management & Signage",
        "icon": "shield-alert",
        "description": "Oversees traffic signals, missing road safety signs, zebra crossings, and blindspot mirrors.",
        "default_sla_hours": 24,
        "contact_email": "traffic@civicresolve.local"
    },
    {
        "code": "HEALTH",
        "name": "Public Health & Vector Control",
        "icon": "activity",
        "description": "Stagnant water mosquito breeding, public sanitization hazards, and carcass removal.",
        "default_sla_hours": 16,
        "contact_email": "health@civicresolve.local"
    }
]

# Database Setup
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Issues Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            priority_score INTEGER NOT NULL DEFAULT 50,
            department TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Reported',
            location_address TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            citizen_name TEXT DEFAULT 'Anonymous Citizen',
            citizen_contact TEXT DEFAULT '',
            image_data TEXT DEFAULT '',
            resolution_image TEXT DEFAULT '',
            resolution_notes TEXT DEFAULT '',
            assigned_team TEXT DEFAULT '',
            ai_reasoning TEXT DEFAULT '',
            ai_confidence REAL DEFAULT 0.90,
            safety_hazards TEXT DEFAULT '[]',
            estimated_sla_hours INTEGER DEFAULT 24,
            upvotes_count INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT DEFAULT ''
        )
    """)
    
    # Status History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            old_status TEXT NOT NULL,
            new_status TEXT NOT NULL,
            changed_by TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
        )
    """)
    
    # Comments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            author_role TEXT NOT NULL DEFAULT 'Citizen',
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE
        )
    """)
    
    # Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    # Check if empty, seed demo data
    cursor.execute("SELECT COUNT(*) FROM issues")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_demo_data(cursor)
        conn.commit()
        
    conn.close()

def seed_demo_data(cursor):
    now = datetime.datetime.now(datetime.timezone.utc)
    
    demo_issues = [
        {
            "tracking_code": "CR-2026-0101",
            "title": "Severe Pothole Cluster on 5th Main Avenue Crossroad",
            "description": "Deep 10-inch pothole in the middle of a two-lane road right before the pedestrian crossing. Two two-wheelers already skidded this morning during rush hour. Poses high risk of fatal accidents.",
            "category": "Roads & Pavements",
            "priority": "Critical",
            "priority_score": 92,
            "department": "Public Works & Road Maintenance",
            "status": "In Progress",
            "location_address": "5th Main Ave & 12th Cross, Downtown Metro Sector",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "citizen_name": "Marcus Vance",
            "citizen_contact": "marcus.v@email.com",
            "assigned_team": "Downtown Asphalt Rapid Response Crew #4",
            "ai_reasoning": "High-speed road hazard with documented skidding incidents. Proximity to pedestrian crossing makes it a severe public safety emergency requiring immediate barricading and patch work.",
            "ai_confidence": 0.96,
            "safety_hazards": json.dumps(["Vehicular skidding", "Pedestrian collision hazard", "Two-wheeler rollover risk"]),
            "estimated_sla_hours": 12,
            "upvotes_count": 34,
            "days_ago": 1,
            "status_history": [
                ("None", "Reported", "Citizen Submission", "Initial complaint filed with photo"),
                ("Reported", "Under Review", "Automated Triage AI", "Gemini flagged urgency as Critical (92/100)"),
                ("Under Review", "In Progress", "Chief Engineer Patel", "Dispatched Crew #4 with cold mix asphalt")
            ],
            "comments": [
                ("Marcus Vance", "Citizen", "Saw another cyclist almost crash here an hour ago!"),
                ("Municipal Control Room", "Authority", "Crew #4 has reached location with safety cones and flashing signs. Cold mix repair underway.")
            ]
        },
        {
            "tracking_code": "CR-2026-0102",
            "title": "Major High-Pressure Water Main Pipeline Burst",
            "description": "Drinking water main line ruptured underneath the pavement outside St. Jude School. Clean water is gushing into the street flooding the sidewalk and basement ramps.",
            "category": "Water Supply & Drainage",
            "priority": "Critical",
            "priority_score": 95,
            "department": "Water Supply & Sewerage Board",
            "status": "Under Review",
            "location_address": "45 School Road, North Suburb Ward",
            "latitude": 37.7833,
            "longitude": -122.4167,
            "citizen_name": "Elena Rostova",
            "citizen_contact": "elena.r@email.com",
            "assigned_team": "Water Works Zone 2 Emergency Valve Unit",
            "ai_reasoning": "Ruptured high-pressure potable water conduit causing structural soil erosion beneath sidewalk and flooding nearby school approach. Immediate valve isolation required.",
            "ai_confidence": 0.98,
            "safety_hazards": json.dumps(["Basement flooding", "Pavement subsidence", "Drinking water contamination risk", "Traffic obstruction"]),
            "estimated_sla_hours": 6,
            "upvotes_count": 52,
            "days_ago": 0.5,
            "status_history": [
                ("None", "Reported", "Citizen Submission", "Filed via CivicResolve Mobile Portal"),
                ("Reported", "Under Review", "Duty Officer Jenkins", "Notified BWSSB hydraulic engineers to isolate sector valve #14")
            ],
            "comments": [
                ("Elena Rostova", "Citizen", "Water is now reaching the school gate! Please hurry!"),
                ("Duty Officer Jenkins", "Authority", "Valve isolation team has shut off Sector 3 supply line to stop the surge.")
            ]
        },
        {
            "tracking_code": "CR-2026-0103",
            "title": "Overflowing Public Garbage Dumpster & Illegal Dumping",
            "description": "The large community dumpster hasn't been emptied in 5 days. Waste is spilling over 30 feet onto the road, attracting stray dogs, rodents, and creating an intolerable stench for residents.",
            "category": "Sanitation & Waste",
            "priority": "High",
            "priority_score": 78,
            "department": "Sanitation & Waste Management",
            "status": "Reported",
            "location_address": "Block C Market Square, East District",
            "latitude": 37.7650,
            "longitude": -122.4250,
            "citizen_name": "Devon Miller",
            "citizen_contact": "devon.m@email.com",
            "assigned_team": "",
            "ai_reasoning": "Accumulation of decomposing municipal solid waste near food market poses vector-borne health hazards and blocks pedestrian walkways.",
            "ai_confidence": 0.94,
            "safety_hazards": json.dumps(["Vector-borne disease vector", "Rodent infestation", "Walkway blockage"]),
            "estimated_sla_hours": 12,
            "upvotes_count": 19,
            "days_ago": 2,
            "status_history": [
                ("None", "Reported", "Citizen Submission", "Report submitted with waste photo")
            ],
            "comments": [
                ("Devon Miller", "Citizen", "The smell is spreading into nearby grocery stores.")
            ]
        },
        {
            "tracking_code": "CR-2026-0104",
            "title": "Broken Streetlight & Exposed Underground Cables",
            "description": "Streetlight pole #SL-402 was struck by a delivery truck. The lamp fixture is hanging by a wire and the base inspection cover is open with exposed wires near a puddle.",
            "category": "Electrical & Streetlights",
            "priority": "High",
            "priority_score": 88,
            "department": "Electrical & Streetlight Authority",
            "status": "In Progress",
            "location_address": "Corner of Oak St & Elm Terrace, Riverside Ward",
            "latitude": 37.7700,
            "longitude": -122.4300,
            "citizen_name": "Aisha Khan",
            "citizen_contact": "aisha.k@email.com",
            "assigned_team": "Grid Safety Crew 7",
            "ai_reasoning": "High voltage electrocution hazard due to exposed cables near surface water puddle, along with overhead falling hazard from dangling luminaire.",
            "ai_confidence": 0.97,
            "safety_hazards": json.dumps(["Electrocution hazard", "Overhead falling object", "Nighttime visibility blindspot"]),
            "estimated_sla_hours": 18,
            "upvotes_count": 27,
            "days_ago": 1.5,
            "status_history": [
                ("None", "Reported", "Citizen Submission", "Urgent alert submitted"),
                ("Reported", "In Progress", "Electrical Dispatch", "Power tripped on circuit 4B. Crew dispatched to replace pole.")
            ],
            "comments": [
                ("Aisha Khan", "Citizen", "Thank you for cutting power quickly!")
            ]
        },
        {
            "tracking_code": "CR-2026-0105",
            "title": "Large Fallen Oak Tree Limb Blocking Bicycle Lane",
            "description": "Heavy storm last night caused a massive tree bough to snap and land directly across the protected two-way cycle track, forcing cyclists into traffic.",
            "category": "Parks & Public Spaces",
            "priority": "Medium",
            "priority_score": 62,
            "department": "Parks, Trees & Horticulture",
            "status": "Resolved",
            "location_address": "Greenway Boulevard near Lakeview Park",
            "latitude": 37.7600,
            "longitude": -122.4400,
            "citizen_name": "Liam Thorne",
            "citizen_contact": "liam.t@email.com",
            "assigned_team": "Urban Forestry Chainsaw Unit 3",
            "ai_reasoning": "Obstruction of dedicated cycling corridor diverts vulnerable road users into vehicular lane. Non-fatal but moderate transit friction.",
            "ai_confidence": 0.92,
            "safety_hazards": json.dumps(["Bicycle lane obstruction", "Cyclist traffic diversion"]),
            "estimated_sla_hours": 24,
            "upvotes_count": 14,
            "days_ago": 3,
            "status_history": [
                ("None", "Reported", "Citizen Submission", "Filed via web portal"),
                ("Reported", "In Progress", "Parks Supervisor", "Unit 3 dispatched with industrial woodchipper"),
                ("In Progress", "Resolved", "Parks Supervisor", "Tree limb sawed, chipped, and cycle track cleared and swept clean.")
            ],
            "comments": [
                ("Liam Thorne", "Citizen", "Confirming the lane is completely clear now. Great response time!"),
                ("Parks Supervisor", "Authority", "Resolved in under 4 hours. Debris repurposed into municipal mulch.")
            ]
        },
        {
            "tracking_code": "CR-2026-0106",
            "title": "Clogged Stormwater Drain Causing Stagnant Water Basin",
            "description": "Catch basin grate is choked with plastic debris and silt. Even light drizzle causes 4 inches of foul stagnant water that doesn't drain for days.",
            "category": "Water Supply & Drainage",
            "priority": "Medium",
            "priority_score": 58,
            "department": "Water Supply & Sewerage Board",
            "status": "Reported",
            "location_address": "88 Industrial Way, Sector 6",
            "latitude": 37.7550,
            "longitude": -122.4100,
            "citizen_name": "Priya Sharma",
            "citizen_contact": "priya.s@email.com",
            "assigned_team": "",
            "ai_reasoning": "Drainage inefficiency leading to localized water accumulation. Poses mosquito breeding concern and minor pedestrian inconvenience.",
            "ai_confidence": 0.91,
            "safety_hazards": json.dumps(["Mosquito vector breeding", "Minor road shoulder flooding"]),
            "estimated_sla_hours": 36,
            "upvotes_count": 9,
            "days_ago": 4,
            "status_history": [
                ("None", "Reported", "Citizen Submission", "Logged with photo")
            ],
            "comments": []
        }
    ]
    
    for item in demo_issues:
        created_time = (now - datetime.timedelta(days=item["days_ago"])).isoformat()
        updated_time = (now - datetime.timedelta(hours=4 * item["days_ago"])).isoformat()
        resolved_time = updated_time if item["status"] == "Resolved" else ""
        resolution_notes = "Tree limb completely dismantled, cleared, and track swept clean." if item["status"] == "Resolved" else ""
        
        cursor.execute("""
            INSERT INTO issues (
                tracking_code, title, description, category, priority, priority_score,
                department, status, location_address, latitude, longitude,
                citizen_name, citizen_contact, assigned_team, ai_reasoning, ai_confidence,
                safety_hazards, estimated_sla_hours, upvotes_count, created_at, updated_at,
                resolved_at, resolution_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["tracking_code"], item["title"], item["description"], item["category"],
            item["priority"], item["priority_score"], item["department"], item["status"],
            item["location_address"], item["latitude"], item["longitude"], item["citizen_name"],
            item["citizen_contact"], item["assigned_team"], item["ai_reasoning"], item["ai_confidence"],
            item["safety_hazards"], item["estimated_sla_hours"], item["upvotes_count"],
            created_time, updated_time, resolved_time, resolution_notes
        ))
        
        issue_id = cursor.lastrowid
        
        # Insert status history
        for old_st, new_st, changed_by, notes in item["status_history"]:
            cursor.execute("""
                INSERT INTO status_history (issue_id, old_status, new_status, changed_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (issue_id, old_st, new_st, changed_by, notes, created_time))
            
        # Insert comments
        for author, role, msg in item["comments"]:
            cursor.execute("""
                INSERT INTO comments (issue_id, author_name, author_role, message, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (issue_id, author, role, msg, updated_time))

# Smart Rule-Based Civic NLP AI Engine (Instant fallback / Offline intelligence)
def local_civic_ai_classify(title, description, location="", image_base64=None):
    text = f"{title} {description} {location}".lower()
    
    # 1. Category Detection Rules
    category_scores = {
        "Roads & Pavements": 0,
        "Sanitation & Waste": 0,
        "Water Supply & Drainage": 0,
        "Electrical & Streetlights": 0,
        "Parks & Public Spaces": 0,
        "Traffic & Transportation": 0,
        "Public Health & Safety": 0
    }
    
    # Road keywords / stems
    road_kw = ["pothole", "asphalt", "crater", "road", "pavement", "sidewalk", "curb", "footpath", "manhole", "tarmac", "sinkhole", "uneven road", "street surface", "skid", "rut", "bumpy"]
    for kw in road_kw:
        if kw in text:
            category_scores["Roads & Pavements"] += 4
            
    # Sanitation keywords / stems
    sanitation_kw = ["garbage", "trash", "dumpster", "waste", "rubbish", "litter", "debris", "overflowing bin", "stench", "smell", "dumping", "sweeping", "dead animal", "carcass", "refuse", "filth"]
    for kw in sanitation_kw:
        if kw in text:
            category_scores["Sanitation & Waste"] += 4
            
    # Water & Drainage keywords / stems
    water_kw = ["water", "pipe", "pipeline", "leak", "burst", "sewer", "sewage", "drain", "drainage", "flood", "flooding", "gush", "waterlog", "stormwater", "overflow", "gutter", "puddle", "catch basin"]
    for kw in water_kw:
        if kw in text:
            category_scores["Water Supply & Drainage"] += 4
            
    # Electrical keywords / stems
    elec_kw = ["streetlight", "street light", "lamp", "pole", "wire", "cable", "electric", "spark", "transformer", "darkness", "exposed wire", "blackout", "shock", "live wire", "luminaire"]
    for kw in elec_kw:
        if kw in text:
            category_scores["Electrical & Streetlights"] += 4
            
    # Parks & Trees keywords / stems
    parks_kw = ["tree", "branch", "bough", "limb", "park", "garden", "lawn", "overgrown", "grass", "playground", "swing", "bench", "fallen tree", "horticulture", "foliage"]
    for kw in parks_kw:
        if kw in text:
            category_scores["Parks & Public Spaces"] += 4
            
    # Traffic keywords / stems
    traffic_kw = ["traffic light", "signal", "traffic sign", "speed breaker", "zebra crossing", "stop sign", "barrier", "congestion", "divider", "blindspot", "pedestrian crossing"]
    for kw in traffic_kw:
        if kw in text:
            category_scores["Traffic & Transportation"] += 4
            
    # Public health keywords / stems
    health_kw = ["mosquito", "dengue", "malaria", "stagnant water", "contamination", "toxic", "hazard", "health risk", "infestation", "rats", "rodent", "pathogen"]
    for kw in health_kw:
        if kw in text:
            category_scores["Public Health & Safety"] += 4

    # Pick highest category
    best_category = max(category_scores.items(), key=lambda x: x[1])
    if best_category[1] == 0:
        detected_category = "Roads & Pavements" # sensible default
    else:
        detected_category = best_category[0]
        
    # 2. Priority & Urgency Scoring
    # Critical risk triggers (+30 to +50)
    critical_triggers = [
        "burst", "live wire", "exposed wire", "gush", "sinkhole", "skid", "accident",
        "fatal", "electrocution", "spark", "fire hazard", "hospital",
        "deep crater", "falling hazard", "severe flood", "collapsed", "emergency", "blindspot"
    ]
    # High risk triggers (+15 to +25)
    high_triggers = [
        "overflow", "pothole", "sewage", "stench", "darkness", "broken streetlight",
        "dead animal", "rats", "mosquito", "block", "impassable", "struck", "fracture", "injury", "school"
    ]
    # Medium risk triggers (+8 to +12)
    medium_triggers = [
        "drain", "curb", "tree branch", "sidewalk", "flicker", "dirty", "litter", "cracked", "slow leak", "pavement"
    ]
    
    score = 40 # baseline
    hazards = []
    
    for trig in critical_triggers:
        if trig in text:
            score += 25
            hazards.append(f"Critical safety factor detected: '{trig}'")
            
    for trig in high_triggers:
        if trig in text:
            score += 15
            hazards.append(f"Elevated risk condition: '{trig}'")
            
    for trig in medium_triggers:
        if trig in text:
            score += 8
            
    # High pedestrian/institutional zone boosts
    if any(loc_kw in text for loc_kw in ["school", "hospital", "highway", "main road", "metro", "kindergarten", "elderly"]):
        score += 15
        hazards.append("High-density public / institutional zone proximity")
        
    # Cap score
    score = max(25, min(98, score))
    
    # Priority tiers
    if score >= 85:
        priority = "Critical"
        sla_hours = 8
    elif score >= 65:
        priority = "High"
        sla_hours = 18
    elif score >= 45:
        priority = "Medium"
        sla_hours = 36
    else:
        priority = "Low"
        sla_hours = 72
        
    # 3. Department Recommendation
    dept_map = {
        "Roads & Pavements": "Public Works & Road Maintenance",
        "Sanitation & Waste": "Sanitation & Waste Management",
        "Water Supply & Drainage": "Water Supply & Sewerage Board",
        "Electrical & Streetlights": "Electrical & Streetlight Authority",
        "Parks & Public Spaces": "Parks, Trees & Horticulture",
        "Traffic & Transportation": "Traffic Management & Signage",
        "Public Health & Safety": "Public Health & Vector Control"
    }
    recommended_dept = dept_map.get(detected_category, "Public Works & Road Maintenance")
    
    # 4. Formulate Detailed AI Reasoning
    reasoning_parts = []
    reasoning_parts.append(f"CivicResolve AI analyzed the incident context and classified it as '{detected_category}' with {priority} urgency (Priority Index: {score}/100).")
    if hazards:
        reasoning_parts.append(f"Safety factors evaluated: {', '.join(hazards[:3])}.")
    reasoning_parts.append(f"Automated dispatch directed to {recommended_dept} with an accelerated SLA target of {sla_hours} hours.")
    
    return {
        "category": detected_category,
        "priority": priority,
        "priority_score": score,
        "recommended_department": recommended_dept,
        "reasoning": " ".join(reasoning_parts),
        "safety_hazards": hazards if hazards else ["Standard municipal maintenance requirement"],
        "estimated_sla_hours": sla_hours,
        "confidence": 0.94,
        "ai_source": "CivicResolve Smart NLP Engine"
    }

# Gemini API Integration
def gemini_ai_classify(title, description, location="", image_base64=None, api_key=None):
    key = api_key or GEMINI_API_KEY
    if not key:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key='gemini_api_key'")
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            key = row[0]
            
    if not key:
        # Fallback to smart local rule-based AI
        return local_civic_ai_classify(title, description, location, image_base64)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
    
    prompt = f"""
You are the AI Chief Municipal Triage Officer for 'CivicResolve', an intelligent civic issue management system.
Analyze this civic citizen complaint thoroughly and respond ONLY with valid, minified JSON.

Complaint Details:
- Title: {title}
- Description: {description}
- Location: {location}

Valid Categories:
- "Roads & Pavements"
- "Sanitation & Waste"
- "Water Supply & Drainage"
- "Electrical & Streetlights"
- "Parks & Public Spaces"
- "Traffic & Transportation"
- "Public Health & Safety"

Valid Departments:
- "Public Works & Road Maintenance"
- "Sanitation & Waste Management"
- "Water Supply & Sewerage Board"
- "Electrical & Streetlight Authority"
- "Parks, Trees & Horticulture"
- "Traffic Management & Signage"
- "Public Health & Vector Control"

JSON Schema to return:
{{
  "category": "<one of valid categories>",
  "priority": "<Critical | High | Medium | Low>",
  "priority_score": <integer 1 to 100 representing urgency and public safety risk>,
  "recommended_department": "<one of valid departments>",
  "reasoning": "<concise 2-3 sentence explanation of the risk, why this priority and department were selected>",
  "safety_hazards": ["<short hazard string 1>", "<short hazard string 2>"],
  "estimated_sla_hours": <integer hours for resolution target, e.g. 6 to 48>,
  "confidence": <float 0.80 to 0.99>
}}
Do NOT include markdown formatting or backticks. Return raw JSON string only.
"""
    
    parts = [{"text": prompt}]
    
    # If image provided, attach as inlineData
    if image_base64 and len(image_base64) > 100:
        mime = "image/jpeg"
        data_clean = image_base64
        if "data:" in image_base64 and ";base64," in image_base64:
            header, data_clean = image_base64.split(";base64,")
            mime = header.replace("data:", "")
        parts.append({
            "inline_data": {
                "mime_type": mime,
                "data": data_clean
            }
        })
        
    payload = {
        "contents": [
            {
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean markdown codeblocks if any
            clean_json = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE).strip()
            parsed = json.loads(clean_json)
            parsed["ai_source"] = "Google Gemini 2.0 Flash"
            return parsed
    except urllib.error.HTTPError as he:
        print(f"[Gemini API HTTP Error {he.code}] {he.reason} - activating instant fallback", file=sys.stderr)
        local_result = local_civic_ai_classify(title, description, location, image_base64)
        if he.code == 429:
            local_result["ai_source"] = "CivicResolve Engine (Rate-Limit Protected - 429)"
            local_result["reasoning"] = "[AI Quota Protected] " + local_result["reasoning"]
        elif he.code in [500, 502, 503, 504]:
            local_result["ai_source"] = f"CivicResolve Engine (Service {he.code} Fallback)"
        else:
            local_result["ai_source"] = f"CivicResolve Engine (HTTP {he.code} Fallback)"
        return local_result
    except Exception as e:
        print(f"[Gemini API Notice] Falling back to local civic AI engine: {e}", file=sys.stderr)
        local_result = local_civic_ai_classify(title, description, location, image_base64)
        local_result["ai_source"] = "CivicResolve Engine (Resilient Fallback)"
        return local_result

# HTTP Request Handler
class CivicResolveHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and disable aggressive caching for API
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def send_json(self, status_code, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status_code, message):
        self.send_json(status_code, {"error": message, "success": False})

    def parse_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            raw_body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_body)
        except Exception as e:
            return None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Health & Config
        if path == "/api/health":
            self.send_json(200, {
                "status": "healthy",
                "service": "CivicResolve API",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
            return

        if path == "/api/config":
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key='gemini_api_key'")
            row = c.fetchone()
            conn.close()
            has_db_key = bool(row and row[0])
            has_env_key = bool(GEMINI_API_KEY)
            self.send_json(200, {
                "gemini_configured": has_db_key or has_env_key,
                "gemini_source": "Database" if has_db_key else ("Environment" if has_env_key else "Local Smart AI Engine (Simulated)")
            })
            return

        # Departments
        if path == "/api/departments":
            self.send_json(200, {"departments": DEPARTMENTS, "total": len(DEPARTMENTS)})
            return

        # Analytics
        if path == "/api/analytics":
            self.handle_analytics()
            return

        # Issues List
        if path == "/api/issues":
            self.handle_get_issues(query)
            return

        # Single Issue Details
        match = re.match(r"^/api/issues/(\d+)$", path)
        if match:
            issue_id = int(match.group(1))
            self.handle_get_single_issue(issue_id)
            return

        # Static File Serving
        self.serve_static(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        if body is None:
            self.send_error_json(400, "Invalid JSON in request body")
            return

        # AI Classification endpoint (pre-submission preview or standalone test)
        if path == "/api/ai/classify":
            title = body.get("title", "")
            description = body.get("description", "")
            location = body.get("location", "")
            image_base64 = body.get("image", None)
            
            if not title and not description:
                self.send_error_json(400, "Title or description required for classification")
                return

            result = gemini_ai_classify(title, description, location, image_base64)
            self.send_json(200, result)
            return

        # Save Gemini API Key
        if path == "/api/config":
            api_key = body.get("gemini_api_key", "").strip()
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('gemini_api_key', ?)", (api_key,))
            conn.commit()
            conn.close()
            self.send_json(200, {"success": True, "message": "API key updated successfully"})
            return

        # Submit New Issue
        if path == "/api/issues":
            self.handle_create_issue(body)
            return

        # Upvote an Issue
        upvote_match = re.match(r"^/api/issues/(\d+)/upvote$", path)
        if upvote_match:
            issue_id = int(upvote_match.group(1))
            self.handle_upvote(issue_id)
            return

        # Add Comment / Citizen Update
        comment_match = re.match(r"^/api/issues/(\d+)/comments$", path)
        if comment_match:
            issue_id = int(comment_match.group(1))
            self.handle_add_comment(issue_id, body)
            return

        # Reset Demo Data
        if path == "/api/reset-demo":
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM status_history")
            c.execute("DELETE FROM comments")
            c.execute("DELETE FROM issues")
            seed_demo_data(c)
            conn.commit()
            conn.close()
            self.send_json(200, {"success": True, "message": "Demo data reset successfully"})
            return

        self.send_error_json(404, "Endpoint not found")

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()

        if body is None:
            self.send_error_json(400, "Invalid JSON in request body")
            return

        # Update Issue Status / Department / Resolution
        match = re.match(r"^/api/issues/(\d+)$", path)
        if match:
            issue_id = int(match.group(1))
            self.handle_update_issue(issue_id, body)
            return

        self.send_error_json(404, "Endpoint not found")

    # API Handlers
    def handle_get_issues(self, query):
        status_filter = query.get("status", [None])[0]
        dept_filter = query.get("department", [None])[0]
        priority_filter = query.get("priority", [None])[0]
        category_filter = query.get("category", [None])[0]
        search_kw = query.get("search", [None])[0]
        sort_by = query.get("sort", ["newest"])[0]

        sql = "SELECT * FROM issues WHERE 1=1"
        params = []

        if status_filter and status_filter != "all":
            sql += " AND status = ?"
            params.append(status_filter)

        if dept_filter and dept_filter != "all":
            sql += " AND department = ?"
            params.append(dept_filter)

        if priority_filter and priority_filter != "all":
            sql += " AND priority = ?"
            params.append(priority_filter)

        if category_filter and category_filter != "all":
            sql += " AND category = ?"
            params.append(category_filter)

        if search_kw:
            sql += " AND (title LIKE ? OR description LIKE ? OR location_address LIKE ? OR tracking_code LIKE ?)"
            term = f"%{search_kw}%"
            params.extend([term, term, term, term])

        # Sorting
        if sort_by == "priority":
            sql += " ORDER BY priority_score DESC, created_at DESC"
        elif sort_by == "upvotes":
            sql += " ORDER BY upvotes_count DESC, created_at DESC"
        elif sort_by == "oldest":
            sql += " ORDER BY created_at ASC"
        else: # newest
            sql += " ORDER BY created_at DESC"

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(sql, params)
        rows = c.fetchall()

        issues_list = []
        for r in rows:
            d = dict(r)
            try:
                d["safety_hazards"] = json.loads(d["safety_hazards"])
            except:
                d["safety_hazards"] = []
            issues_list.append(d)

        conn.close()
        self.send_json(200, {"issues": issues_list, "total": len(issues_list)})

    def handle_get_single_issue(self, issue_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
        issue_row = c.fetchone()
        if not issue_row:
            conn.close()
            self.send_error_json(404, "Civic issue not found")
            return

        issue_data = dict(issue_row)
        try:
            issue_data["safety_hazards"] = json.loads(issue_data["safety_hazards"])
        except:
            issue_data["safety_hazards"] = []

        # Get history
        c.execute("SELECT * FROM status_history WHERE issue_id = ? ORDER BY created_at ASC", (issue_id,))
        issue_data["history"] = [dict(r) for r in c.fetchall()]

        # Get comments
        c.execute("SELECT * FROM comments WHERE issue_id = ? ORDER BY created_at ASC", (issue_id,))
        issue_data["comments"] = [dict(r) for r in c.fetchall()]

        conn.close()
        self.send_json(200, issue_data)

    def handle_create_issue(self, body):
        title = body.get("title", "").strip()
        description = body.get("description", "").strip()
        location_address = body.get("location_address", "").strip()
        latitude = body.get("latitude", 37.7749)
        longitude = body.get("longitude", -122.4194)
        citizen_name = body.get("citizen_name", "Anonymous Citizen").strip() or "Anonymous Citizen"
        citizen_contact = body.get("citizen_contact", "").strip()
        image_data = body.get("image_data", "")
        
        # User specified or override
        manual_category = body.get("category", "")
        
        if not title or not description:
            self.send_error_json(400, "Title and description are required")
            return

        if not location_address:
            location_address = "Civic Center District, Downtown"

        # Run AI Classification
        ai_res = gemini_ai_classify(title, description, location_address, image_data)
        
        category = manual_category if manual_category else ai_res["category"]
        priority = ai_res["priority"]
        priority_score = ai_res.get("priority_score", 50)
        department = ai_res["recommended_department"]
        reasoning = ai_res.get("reasoning", "")
        confidence = ai_res.get("confidence", 0.92)
        hazards = json.dumps(ai_res.get("safety_hazards", []))
        sla_hours = ai_res.get("estimated_sla_hours", 24)

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Generate unique tracking code
        c.execute("SELECT COUNT(*) FROM issues")
        next_seq = c.fetchone()[0] + 101
        year = datetime.datetime.now().year
        tracking_code = f"CR-{year}-{next_seq:04d}"

        c.execute("""
            INSERT INTO issues (
                tracking_code, title, description, category, priority, priority_score,
                department, status, location_address, latitude, longitude,
                citizen_name, citizen_contact, image_data, ai_reasoning, ai_confidence,
                safety_hazards, estimated_sla_hours, upvotes_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            tracking_code, title, description, category, priority, priority_score,
            department, "Reported", location_address, latitude, longitude,
            citizen_name, citizen_contact, image_data, reasoning, confidence,
            hazards, sla_hours, now_iso, now_iso
        ))

        new_id = c.lastrowid

        # Insert initial status history
        c.execute("""
            INSERT INTO status_history (issue_id, old_status, new_status, changed_by, notes, created_at)
            VALUES (?, 'None', 'Reported', 'Citizen Submission', 'Complaint submitted via CivicResolve Portal', ?)
        """, (new_id, now_iso))

        # Insert AI Triage entry if high priority
        if priority in ["Critical", "High"]:
            c.execute("""
                INSERT INTO status_history (issue_id, old_status, new_status, changed_by, notes, created_at)
                VALUES (?, 'Reported', 'Reported', 'AI Triage Engine', ?, ?)
            """, (new_id, f"Gemini prioritized issue as {priority} ({priority_score}/100) - Fast-tracked to {department}", now_iso))

        conn.commit()
        conn.close()

        self.send_json(201, {
            "success": True,
            "message": "Civic issue successfully submitted and classified",
            "issue_id": new_id,
            "tracking_code": tracking_code,
            "category": category,
            "priority": priority,
            "priority_score": priority_score,
            "department": department,
            "ai_reasoning": reasoning
        })

    def handle_update_issue(self, issue_id, body):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
        current = c.fetchone()
        if not current:
            conn.close()
            self.send_error_json(404, "Issue not found")
            return

        old_status = current["status"]
        new_status = body.get("status", old_status)
        new_department = body.get("department", current["department"])
        assigned_team = body.get("assigned_team", current["assigned_team"])
        resolution_notes = body.get("resolution_notes", current["resolution_notes"])
        resolution_image = body.get("resolution_image", current["resolution_image"])
        admin_name = body.get("admin_name", "Municipal Authority")
        action_note = body.get("note", "")

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        resolved_at = now_iso if new_status == "Resolved" and old_status != "Resolved" else current["resolved_at"]

        c.execute("""
            UPDATE issues SET
                status = ?,
                department = ?,
                assigned_team = ?,
                resolution_notes = ?,
                resolution_image = ?,
                resolved_at = ?,
                updated_at = ?
            WHERE id = ?
        """, (new_status, new_department, assigned_team, resolution_notes, resolution_image, resolved_at, now_iso, issue_id))

        # If status changed or department reassigned, log in history
        if new_status != old_status or new_department != current["department"] or action_note:
            note_text = action_note
            if new_status != old_status and not note_text:
                note_text = f"Status updated from '{old_status}' to '{new_status}'"
            if new_department != current["department"]:
                note_text += f" [Department reassigned to {new_department}]"

            c.execute("""
                INSERT INTO status_history (issue_id, old_status, new_status, changed_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (issue_id, old_status, new_status, admin_name, note_text, now_iso))

        conn.commit()
        conn.close()

        self.send_json(200, {
            "success": True,
            "message": "Civic issue successfully updated",
            "issue_id": issue_id,
            "new_status": new_status,
            "department": new_department
        })

    def handle_upvote(self, issue_id):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE issues SET upvotes_count = upvotes_count + 1 WHERE id = ?", (issue_id,))
        c.execute("SELECT upvotes_count FROM issues WHERE id = ?", (issue_id,))
        row = c.fetchone()
        conn.commit()
        conn.close()

        if not row:
            self.send_error_json(404, "Issue not found")
            return

        self.send_json(200, {"success": True, "upvotes": row[0]})

    def handle_add_comment(self, issue_id, body):
        author_name = body.get("author_name", "Citizen").strip() or "Citizen"
        author_role = body.get("author_role", "Citizen").strip() or "Citizen"
        message = body.get("message", "").strip()

        if not message:
            self.send_error_json(400, "Comment message cannot be empty")
            return

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO comments (issue_id, author_name, author_role, message, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (issue_id, author_name, author_role, message, now_iso))
        comment_id = c.lastrowid
        conn.commit()
        conn.close()

        self.send_json(201, {
            "success": True,
            "comment": {
                "id": comment_id,
                "author_name": author_name,
                "author_role": author_role,
                "message": message,
                "created_at": now_iso
            }
        })

    def handle_analytics(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Overall counts
        c.execute("SELECT COUNT(*) FROM issues")
        total_issues = c.fetchone()[0]

        c.execute("SELECT status, COUNT(*) FROM issues GROUP BY status")
        status_counts = dict(c.fetchall())

        c.execute("SELECT priority, COUNT(*) FROM issues GROUP BY priority")
        priority_counts = dict(c.fetchall())

        c.execute("SELECT department, COUNT(*) FROM issues GROUP BY department")
        dept_counts = dict(c.fetchall())

        c.execute("SELECT category, COUNT(*) FROM issues GROUP BY category")
        category_counts = dict(c.fetchall())

        # Average resolution time
        c.execute("SELECT AVG(estimated_sla_hours) FROM issues")
        avg_sla = round(c.fetchone()[0] or 24, 1)

        # Critical issues count
        critical_count = priority_counts.get("Critical", 0)

        conn.close()

        self.send_json(200, {
            "total_issues": total_issues,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "department_counts": dept_counts,
            "category_counts": category_counts,
            "avg_sla_hours": avg_sla,
            "critical_count": critical_count,
            "resolved_count": status_counts.get("Resolved", 0),
            "in_progress_count": status_counts.get("In Progress", 0),
            "under_review_count": status_counts.get("Under Review", 0),
            "reported_count": status_counts.get("Reported", 0)
        })

    # Serve static assets
    def serve_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"

        # Sanitize path to prevent directory traversal
        clean_path = os.path.normpath(path.lstrip("/"))
        file_path = PUBLIC_DIR / clean_path

        if not file_path.is_file() or not str(file_path).startswith(str(PUBLIC_DIR)):
            # If SPA route fallback or 404
            index_path = PUBLIC_DIR / "index.html"
            if index_path.exists():
                file_path = index_path
            else:
                self.send_error(404, "File Not Found")
                return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        if file_path.suffix == ".js":
            mime_type = "application/javascript"
        elif file_path.suffix == ".css":
            mime_type = "text/css"
        elif file_path.suffix == ".svg":
            mime_type = "image/svg+xml"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

def run_server():
    init_db()
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, CivicResolveHandler)
    print(f"================================================================")
    print(f"🚀 CivicResolve Server running on http://0.0.0.0:{PORT}")
    print(f"🏛️ Citizen Portal: http://localhost:{PORT}")
    print(f"🏢 Admin Dashboard: http://localhost:{PORT}#admin")
    print(f"🧠 AI Engine: Google Gemini with rate-limit resilient local fallback")
    print(f"📁 Database: {DB_PATH}")
    print(f"================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping CivicResolve server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
