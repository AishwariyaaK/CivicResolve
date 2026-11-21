# Moving CivicResolve to Google AI Studio 🚀

This guide provides step-by-step instructions to set up, test, and run CivicResolve's AI triage engine inside **Google AI Studio** ([aistudio.google.com](https://aistudio.google.com/)).

---

## Part 1: Setting Up the Prompt in Google AI Studio

1. Navigate to [Google AI Studio](https://aistudio.google.com/) and sign in with your Google account.
2. Click **"Create New Prompt"** ➔ Select **"Structured Prompt"** or **"Chat Prompt"** (Structured Prompt is recommended for JSON triage).
3. Select Model: **Gemini 2.0 Flash** (or **Gemini 1.5 Flash**).

### 1. System Instructions
In the **System Instructions** box, paste:
```text
You are the AI Chief Municipal Triage Officer for 'CivicResolve', an intelligent civic issue reporting and resolution platform.
Your task is to analyze civic complaints submitted by citizens (with text and optional photos), identify the civic category, assess urgency and public safety risk, determine the correct municipal department, calculate an SLA target, and return a clean JSON response.

Valid Categories:
- Roads & Pavements
- Sanitation & Waste
- Water Supply & Drainage
- Electrical & Streetlights
- Parks & Public Spaces
- Traffic & Transportation
- Public Health & Safety

Valid Departments:
- Public Works & Road Maintenance
- Sanitation & Waste Management
- Water Supply & Sewerage Board
- Electrical & Streetlight Authority
- Parks, Trees & Horticulture
- Traffic Management & Signage
- Public Health & Vector Control

Priority Tiers:
- Critical (85-100 score): Immediate public hazard, electrocution risk, high-speed collision, severe flooding, school/hospital proximity. SLA: 6-12 hours.
- High (65-84 score): Health hazard, major road pothole, overflowing garbage, blocked transit. SLA: 12-24 hours.
- Medium (40-64 score): Drainage slowness, damaged sidewalk, fallen tree limb in park. SLA: 24-48 hours.
- Low (1-39 score): Aesthetic issues, minor litter, faded signage. SLA: 48-72 hours.
```

---

### 2. Model Settings (Right-Hand Panel)
- **Model:** `Gemini 2.0 Flash`
- **Temperature:** `0.2` (low temperature ensures deterministic, consistent triage)
- **Response MIME Type:** Select `application/json`
- **JSON Schema:** (Paste under Structured Output if prompted)
```json
{
  "type": "object",
  "properties": {
    "category": { "type": "string" },
    "priority": { "type": "string", "enum": ["Critical", "High", "Medium", "Low"] },
    "priority_score": { "type": "integer" },
    "recommended_department": { "type": "string" },
    "reasoning": { "type": "string" },
    "safety_hazards": { "type": "array", "items": { "type": "string" } },
    "estimated_sla_hours": { "type": "integer" },
    "confidence": { "type": "number" }
  },
  "required": ["category", "priority", "priority_score", "recommended_department", "reasoning", "safety_hazards", "estimated_sla_hours"]
}
```

---

### 3. Test Cases (Few-Shot Examples)

#### Test Case 1: Pothole (Input)
```text
Title: Severe Pothole Cluster on Highway Pedestrian Crossing
Description: Deep 10-inch pothole crater in the middle of a two-lane road. Two motorcycles skidded this morning during rush hour.
Location: 5th Main Ave & 12th Cross, Downtown Metro Sector
```
**Expected AI Output:**
```json
{
  "category": "Roads & Pavements",
  "priority": "Critical",
  "priority_score": 92,
  "recommended_department": "Public Works & Road Maintenance",
  "reasoning": "High-speed road hazard with documented skidding incidents adjacent to a pedestrian crossing. Poses an imminent risk of fatal accidents.",
  "safety_hazards": ["Vehicular skidding", "Pedestrian collision hazard", "Two-wheeler rollover risk"],
  "estimated_sla_hours": 12,
  "confidence": 0.96
}
```

#### Test Case 2: Water Main Burst (Input)
```text
Title: Major High-Pressure Water Main Rupture
Description: Drinking water conduit ruptured underneath the pavement outside St. Jude School. Clean water is gushing into the street flooding the sidewalk and basement ramps.
Location: 45 School Road, North Suburb Ward
```
**Expected AI Output:**
```json
{
  "category": "Water Supply & Drainage",
  "priority": "Critical",
  "priority_score": 95,
  "recommended_department": "Water Supply & Sewerage Board",
  "reasoning": "Ruptured high-pressure potable water conduit causing structural soil erosion beneath the sidewalk and flooding a school approach. Requires immediate valve isolation.",
  "safety_hazards": ["Basement flooding", "Pavement subsidence", "Drinking water contamination risk", "School access obstruction"],
  "estimated_sla_hours": 6,
  "confidence": 0.98
}
```

---

## Part 2: Connecting Google AI Studio to Your CivicResolve App

### 1. Generate an API Key
1. In Google AI Studio, click **"Get API key"** in the top-left sidebar.
2. Click **"Create API key in new project"** (or select an existing Google Cloud project).
3. Copy the generated key (starts with `AIzaSy...`).

### 2. Connect to CivicResolve
You have two easy ways to plug your key into CivicResolve:

#### Option A: In the Web UI (Instant)
1. Start CivicResolve:
   ```bash
   python server.py
   ```
2. Open `http://localhost:8080` (or `http://localhost:$PORT`).
3. In the top-right navbar, click the **"Civic AI Engine"** badge.
4. Paste your Google AI Studio API key and click **"Save Key"**.
5. The badge will immediately switch to **"Google Gemini Live"** with a green pulse indicator!

#### Option B: Via Environment Variable
In PowerShell or Command Prompt before starting the server:
```powershell
$env:GEMINI_API_KEY="AIzaSyYourGeneratedKeyHere"
python server.py
```
Or in standard CMD:
```cmd
set GEMINI_API_KEY=AIzaSyYourGeneratedKeyHere
python server.py
```

---

## Part 3: Exporting Code Directly from Google AI Studio

If you want to view the standalone code generated by Google AI Studio:
1. In your Google AI Studio prompt tab, click **"Get Code"** in the top-right corner.
2. Select **Python**:
   - Google AI Studio will generate the `google-genai` Python snippet:
   ```python
   from google import genai

   client = genai.Client(api_key="YOUR_API_KEY")

   response = client.models.generate_content(
       model="gemini-2.0-flash",
       contents="Complaint details...",
   )
   print(response.text)
   ```
3. CivicResolve already implements this via a direct, lightweight HTTP call (`urllib.request`) in [server.py](file:///C:/Users/aishw/.gemini/antigravity/scratch/civicresolve/server.py#L225-L290), which means you can run CivicResolve anywhere without even needing to install extra packages.
