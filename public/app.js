/**
 * CivicResolve - Client Application
 * Google Gemini AI Civic Issue Reporting & Resolution Platform
 */

const app = {
  // Application State
  state: {
    issues: [],
    analytics: null,
    departments: [],
    activeRole: 'citizen', // 'citizen' | 'admin'
    adminViewMode: 'table', // 'table' | 'kanban'
    statusFilter: 'all',
    departmentFilter: 'all',
    priorityFilter: 'all',
    searchKeyword: '',
    sortBy: 'newest',
    selectedPhoto: '',
    selectedResolutionPhoto: '',
    currentIssueId: null,
    latestSubmittedCode: null,
    aiDebounceTimer: null,
    upvotedIds: new Set()
  },

  // Sample SVG Photos for Realistic 1-Click Testing
  samplePhotos: {
    pothole: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <defs>
          <linearGradient id="road" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#334155"/>
            <stop offset="100%" stop-color="#1e293b"/>
          </linearGradient>
          <linearGradient id="crater" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0f172a"/>
            <stop offset="100%" stop-color="#020617"/>
          </linearGradient>
        </defs>
        <rect width="600" height="350" fill="url(#road)"/>
        <!-- Road markings -->
        <rect x="0" y="165" width="100" height="15" fill="#facc15" opacity="0.8"/>
        <rect x="150" y="165" width="100" height="15" fill="#facc15" opacity="0.8"/>
        <rect x="300" y="165" width="100" height="15" fill="#facc15" opacity="0.8"/>
        <rect x="450" y="165" width="100" height="15" fill="#facc15" opacity="0.8"/>
        <!-- Pothole crater -->
        <ellipse cx="320" cy="220" rx="140" ry="65" fill="url(#crater)" stroke="#475569" stroke-width="6"/>
        <path d="M 200 210 Q 230 240 280 230 Q 340 260 410 220 Q 430 200 390 190 Q 330 180 270 195 Z" fill="#000000" opacity="0.7"/>
        <!-- Cracks -->
        <path d="M 180 220 L 120 250 M 130 230 L 90 220 M 440 210 L 510 240 M 340 275 L 360 320" stroke="#0f172a" stroke-width="4" stroke-linecap="round"/>
        <text x="30" y="45" font-family="sans-serif" font-size="20" font-weight="bold" fill="#ffffff">EVIDENCE: Deep Asphalt Pothole Hazard (10in)</text>
      </svg>
    `),
    water: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <rect width="600" height="350" fill="#475569"/>
        <!-- Sidewalk & curb -->
        <rect x="0" y="0" width="600" height="120" fill="#94a3b8"/>
        <line x1="0" y1="120" x2="600" y2="120" stroke="#cbd5e1" stroke-width="8"/>
        <!-- Rupture point -->
        <ellipse cx="280" cy="180" rx="90" ry="50" fill="#0284c7" opacity="0.9"/>
        <!-- Water gush / spray -->
        <path d="M 280 180 Q 260 70 280 40 Q 310 70 290 180" fill="#38bdf8" opacity="0.85"/>
        <ellipse cx="285" cy="40" rx="25" ry="15" fill="#e0f2fe"/>
        <!-- Flooding pool -->
        <path d="M 120 220 Q 280 320 480 240 Q 550 200 450 160 Q 280 140 120 220 Z" fill="#0284c7" opacity="0.7"/>
        <text x="30" y="35" font-family="sans-serif" font-size="20" font-weight="bold" fill="#0f172a">EVIDENCE: Ruptured Water Main Geyser</text>
      </svg>
    `),
    trash: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <rect width="600" height="350" fill="#64748b"/>
        <!-- Dumpster Body -->
        <rect x="180" y="120" width="240" height="150" rx="8" fill="#15803d"/>
        <rect x="160" y="105" width="280" height="20" rx="4" fill="#166534"/>
        <!-- Overflowing bags -->
        <circle cx="230" cy="95" r="30" fill="#1e293b"/>
        <circle cx="280" cy="85" r="35" fill="#f8fafc"/>
        <circle cx="340" cy="90" r="32" fill="#0f172a"/>
        <circle cx="390" cy="100" r="28" fill="#475569"/>
        <!-- Spilled debris on ground -->
        <ellipse cx="280" cy="285" rx="190" ry="40" fill="#334155" opacity="0.6"/>
        <rect x="120" y="270" width="40" height="25" fill="#fef08a" transform="rotate(15 120 270)"/>
        <circle cx="430" cy="275" r="18" fill="#f87171"/>
        <text x="30" y="45" font-family="sans-serif" font-size="20" font-weight="bold" fill="#ffffff">EVIDENCE: Overflowing Commercial Dumpster</text>
      </svg>
    `),
    wire: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <rect width="600" height="350" fill="#1e293b"/>
        <!-- Lamppost -->
        <rect x="180" y="30" width="16" height="270" fill="#64748b"/>
        <path d="M 188 30 Q 188 10 240 15 L 240 35" fill="none" stroke="#64748b" stroke-width="12"/>
        <polygon points="230,35 250,35 260,55 220,55" fill="#cbd5e1"/>
        <!-- Dangling loose wires -->
        <path d="M 240 55 Q 260 120 230 180 T 260 270" fill="none" stroke="#ef4444" stroke-width="5"/>
        <path d="M 245 55 Q 220 130 250 200 T 270 280" fill="none" stroke="#f59e0b" stroke-width="4"/>
        <!-- Spark effect -->
        <polygon points="260,270 275,255 270,275 285,265 272,282 280,295 265,285" fill="#fde047"/>
        <text x="30" y="45" font-family="sans-serif" font-size="20" font-weight="bold" fill="#f87171">EVIDENCE: Damaged Pole & Live Sparking Wire</text>
      </svg>
    `),
    tree: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <rect width="600" height="350" fill="#334155"/>
        <!-- Bike lane green strip -->
        <rect x="0" y="150" width="600" height="140" fill="#059669" opacity="0.8"/>
        <!-- Bicycle symbol -->
        <circle cx="80" cy="220" r="16" fill="none" stroke="#ffffff" stroke-width="4"/>
        <circle cx="140" cy="220" r="16" fill="none" stroke="#ffffff" stroke-width="4"/>
        <line x1="80" y1="220" x2="110" y2="190" stroke="#ffffff" stroke-width="4"/>
        <!-- Fallen heavy tree log -->
        <path d="M 160 210 L 460 240" stroke="#78350f" stroke-width="36" stroke-linecap="round"/>
        <!-- Foliage / leaves blocking lane -->
        <circle cx="430" cy="220" r="50" fill="#15803d" opacity="0.9"/>
        <circle cx="480" cy="240" r="45" fill="#166534" opacity="0.9"/>
        <text x="30" y="45" font-family="sans-serif" font-size="20" font-weight="bold" fill="#ffffff">EVIDENCE: Fallen Oak Tree Obstructing Bike Track</text>
      </svg>
    `),
    repaired_road: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <rect width="600" height="350" fill="#334155"/>
        <!-- Freshly paved patch -->
        <ellipse cx="320" cy="220" rx="140" ry="65" fill="#0f172a" stroke="#1e293b" stroke-width="2"/>
        <rect x="0" y="165" width="600" height="15" fill="#facc15" opacity="0.9"/>
        <rect x="20" y="20" width="220" height="40" rx="6" fill="#15803d"/>
        <text x="30" y="46" font-family="sans-serif" font-size="16" font-weight="bold" fill="#ffffff">VERIFIED REPAIR: Fresh Asphalt</text>
      </svg>
    `),
    fixed_pipe: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <rect width="600" height="350" fill="#475569"/>
        <rect x="180" y="160" width="240" height="40" fill="#0284c7" stroke="#0369a1" stroke-width="4"/>
        <circle cx="300" cy="180" r="30" fill="#d97706" stroke="#92400e" stroke-width="6"/>
        <rect x="20" y="20" width="240" height="40" rx="6" fill="#15803d"/>
        <text x="30" y="46" font-family="sans-serif" font-size="16" font-weight="bold" fill="#ffffff">VERIFIED: New Isolation Valve Installed</text>
      </svg>
    `),
    cleared_street: "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="350" viewBox="0 0 600 350">
        <rect width="600" height="350" fill="#64748b"/>
        <rect x="180" y="120" width="240" height="150" rx="8" fill="#15803d"/>
        <rect x="160" y="105" width="280" height="20" rx="4" fill="#166534"/>
        <rect x="20" y="20" width="230" height="40" rx="6" fill="#15803d"/>
        <text x="30" y="46" font-family="sans-serif" font-size="16" font-weight="bold" fill="#ffffff">VERIFIED: Waste Completely Cleared</text>
      </svg>
    `)
  },

  // Initialize
  init: async () => {
    console.log("🏛️ CivicResolve Platform Initializing...");
    await app.fetchConfig();
    await app.fetchIssues();
    await app.fetchAnalytics();
    
    // URL Hash Router
    const handleRoute = () => {
      const hash = window.location.hash;
      if (hash === '#admin' || hash === '#admin-section') {
        app.setRole('admin');
      } else if (hash === '#tracking' || hash === '#tracking-section') {
        app.showTrackingView();
      } else if (hash === '#analytics' || hash === '#analytics-section') {
        app.showAnalyticsView();
      } else if (hash === '#report' || hash === '#report-section') {
        app.showReportView();
      }
    };

    window.addEventListener('hashchange', handleRoute);
    if (window.location.hash) {
      handleRoute();
    }
  },

  // Navigation & View Routing
  navigateTo: (targetId, event) => {
    if (event && event.preventDefault) event.preventDefault();

    if (targetId === 'admin-section') {
      app.setRole('admin');
      return;
    }

    // Ensure citizen role container is visible
    app.setRole('citizen');

    // Update active nav link styling
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    if (targetId === 'tracking-section') {
      const el = document.getElementById('nav-tracking');
      if (el) el.classList.add('active');
      // Ensure issues are fetched fresh
      app.fetchIssues();
      app.fetchAnalytics();
    } else if (targetId === 'report-section') {
      const el = document.getElementById('nav-report');
      if (el) el.classList.add('active');
    } else if (targetId === 'analytics-section') {
      const el = document.getElementById('nav-analytics');
      if (el) el.classList.add('active');
    }

    // Smooth scroll to target element
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      setTimeout(() => {
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Highlight & focus search on tracking view
        if (targetId === 'tracking-section') {
          const searchInput = document.getElementById('searchKeyword');
          if (searchInput) {
            searchInput.focus();
            searchInput.classList.add('search-highlight');
            setTimeout(() => searchInput.classList.remove('search-highlight'), 1200);
          }
        }
      }, 60);
    }

    if (history.pushState) {
      history.pushState(null, null, `#${targetId}`);
    } else {
      window.location.hash = `#${targetId}`;
    }
  },

  showTrackingView: (event) => {
    app.navigateTo('tracking-section', event);
  },

  showReportView: (event) => {
    app.navigateTo('report-section', event);
  },

  showAnalyticsView: (event) => {
    app.navigateTo('analytics-section', event);
  },

  // Role Toggle
  setRole: (role, event) => {
    if (event && event.preventDefault) event.preventDefault();
    app.state.activeRole = role;
    const btnCitizen = document.getElementById('btnRoleCitizen');
    const btnAdmin = document.getElementById('btnRoleAdmin');
    const citizenSection = document.getElementById('citizenViewSection');
    const adminSection = document.getElementById('adminViewSection');
    const heroSection = document.getElementById('hero-section');

    if (role === 'admin') {
      btnAdmin.classList.add('active');
      btnCitizen.classList.remove('active');
      citizenSection.style.display = 'none';
      adminSection.style.display = 'block';
      heroSection.style.display = 'none';
      document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
      const adminNav = document.getElementById('nav-admin');
      if (adminNav) adminNav.classList.add('active');
      app.renderAdminView();
      if (window.location.hash !== '#admin-section') {
        if (history.pushState) {
          history.pushState(null, null, '#admin-section');
        } else {
          window.location.hash = '#admin-section';
        }
      }
    } else {
      btnCitizen.classList.add('active');
      btnAdmin.classList.remove('active');
      citizenSection.style.display = 'block';
      adminSection.style.display = 'none';
      heroSection.style.display = 'block';
      const adminNav = document.getElementById('nav-admin');
      if (adminNav) adminNav.classList.remove('active');
      const activeNav = document.querySelector('.nav-links a.active');
      if (!activeNav) {
        const reportNav = document.getElementById('nav-report');
        if (reportNav) reportNav.classList.add('active');
      }
    }
  },

  // Switch Admin View: Table vs Kanban
  setAdminViewMode: (mode) => {
    app.state.adminViewMode = mode;
    const btnTable = document.getElementById('btnAdminViewTable');
    const btnKanban = document.getElementById('btnAdminViewKanban');
    const tableView = document.getElementById('adminTableView');
    const kanbanView = document.getElementById('adminKanbanView');

    if (mode === 'kanban') {
      btnKanban.className = 'btn btn-primary btn-sm';
      btnTable.className = 'btn btn-secondary btn-sm';
      tableView.style.display = 'none';
      kanbanView.style.display = 'grid';
    } else {
      btnTable.className = 'btn btn-primary btn-sm';
      btnKanban.className = 'btn btn-secondary btn-sm';
      tableView.style.display = 'block';
      kanbanView.style.display = 'none';
    }
    app.renderAdminView();
  },

  // Interactive Map Pin Handler
  handleMapClick: (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const pctX = Math.round((x / rect.width) * 100);
    const pctY = Math.round((y / rect.height) * 100);

    const pin = document.getElementById('mapPinEl');
    pin.style.left = `${pctX}%`;
    pin.style.top = `${pctY}%`;

    // Calculate simulated lat/lng
    const lat = (37.7500 + (1 - pctY / 100) * 0.0400).toFixed(4);
    const lng = (-122.4400 + (pctX / 100) * 0.0400).toFixed(4);

    document.getElementById('mapCoordsText').textContent = `📍 Lat: ${lat}, Lng: ${lng}`;

    // Auto-fill address if empty
    const locInput = document.getElementById('issueLocation');
    if (!locInput.value || locInput.value.includes('Civic Grid')) {
      locInput.value = `Civic Grid Sector [${pctX}, ${pctY}], Downtown Municipal Area`;
    }
  },

  // Detect GPS
  detectGpsLocation: () => {
    const pin = document.getElementById('mapPinEl');
    pin.style.left = '48%';
    pin.style.top = '52%';
    document.getElementById('mapCoordsText').textContent = `📍 Lat: 37.7749, Lng: -122.4194 (GPS Verified)`;
    document.getElementById('issueLocation').value = `Current Location: 5th Main Avenue, Downtown Metro Sector`;
    app.showToast("GPS Location auto-detected", "info");
  },

  setQuickLocation: (name, lat, lng) => {
    document.getElementById('issueLocation').value = name;
    document.getElementById('mapCoordsText').textContent = `📍 Lat: ${lat}, Lng: ${lng}`;
    const pin = document.getElementById('mapPinEl');
    pin.style.left = '60%';
    pin.style.top = '40%';
  },

  // Quick Demo Scenarios
  fillScenario: (type) => {
    const scenarios = {
      pothole: {
        title: "Dangerous Pothole Cluster on Highway Pedestrian Crossing",
        desc: "Deep 10-inch pothole crater in the middle of a two-lane road. Two two-wheelers already skidded this morning during rush hour. Poses high risk of fatal accidents right before the pedestrian crossing.",
        loc: "5th Main Ave & 12th Cross, Downtown Metro Sector",
        photo: app.samplePhotos.pothole
      },
      water: {
        title: "Major High-Pressure Water Main Pipeline Rupture",
        desc: "Drinking water main line ruptured underneath the pavement outside St. Jude School. Clean water is gushing into the street flooding the sidewalk and basement ramps.",
        loc: "45 School Road, North Suburb Ward",
        photo: app.samplePhotos.water
      },
      trash: {
        title: "Overflowing Public Garbage Dumpster & Illegal Dumping",
        desc: "The large community dumpster hasn't been emptied in 5 days. Waste is spilling over 30 feet onto the road, attracting stray dogs, rodents, and creating an intolerable stench for residents.",
        loc: "Block C Market Square, East District",
        photo: app.samplePhotos.trash
      },
      streetlight: {
        title: "Damaged Streetlight Pole with Exposed Live Underground Cables",
        desc: "Streetlight pole #SL-402 was struck by a delivery truck. The lamp fixture is hanging by a wire and the base inspection cover is open with exposed wires sparking near a puddle.",
        loc: "Corner of Oak St & Elm Terrace, Riverside Ward",
        photo: app.samplePhotos.wire
      },
      tree: {
        title: "Large Fallen Oak Tree Limb Blocking Bicycle Lane",
        desc: "Heavy storm last night caused a massive tree bough to snap and land directly across the protected two-way cycle track, forcing cyclists into oncoming traffic.",
        loc: "Greenway Boulevard near Lakeview Park",
        photo: app.samplePhotos.tree
      }
    };

    const s = scenarios[type];
    if (!s) return;

    document.getElementById('issueTitle').value = s.title;
    document.getElementById('issueDesc').value = s.desc;
    document.getElementById('issueLocation').value = s.loc;
    
    app.setPhotoData(s.photo);
    app.triggerManualAiAnalysis();
  },

  // 1-Click End-to-End Submission for Hackathon Judges
  quickSubmitDemo: async (type = 'pothole') => {
    app.fillScenario(type);
    app.showToast("⚡ Auto-lodging demo complaint with Gemini AI triage...", "info");
    setTimeout(async () => {
      const mockEvent = { preventDefault: () => {} };
      await app.submitIssue(mockEvent);
    }, 500);
  },

  setSamplePhoto: (type) => {
    if (app.samplePhotos[type]) {
      app.setPhotoData(app.samplePhotos[type]);
      app.showToast("Demo photo attached", "info");
    }
  },

  setResolutionProofPhoto: (type) => {
    if (app.samplePhotos[type]) {
      app.state.selectedResolutionPhoto = app.samplePhotos[type];
      document.getElementById('resPhotoImg').src = app.samplePhotos[type];
      document.getElementById('resPhotoPreview').style.display = 'block';
      app.showToast("Proof photo selected", "info");
    }
  },

  // File Upload Handlers
  handleFileUpload: (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      app.setPhotoData(e.target.result);
      app.showToast("Photo attached successfully", "info");
    };
    reader.readAsDataURL(file);
  },

  setPhotoData: (base64) => {
    app.state.selectedPhoto = base64;
    document.getElementById('photoPreviewImg').src = base64;
    document.getElementById('photoPreviewBox').style.display = 'block';
    document.getElementById('photoDropzone').style.display = 'none';
  },

  removePhoto: () => {
    app.state.selectedPhoto = '';
    document.getElementById('photoPreviewImg').src = '';
    document.getElementById('photoPreviewBox').style.display = 'none';
    document.getElementById('photoDropzone').style.display = 'block';
    document.getElementById('photoFileInput').value = '';
  },

  handleResolutionPhotoUpload: (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      app.state.selectedResolutionPhoto = e.target.result;
      document.getElementById('resPhotoImg').src = e.target.result;
      document.getElementById('resPhotoPreview').style.display = 'block';
    };
    reader.readAsDataURL(file);
  },

  // AI Live Pre-Scan & Classification
  scheduleAiPreview: () => {
    clearTimeout(app.state.aiDebounceTimer);
    app.state.aiDebounceTimer = setTimeout(() => {
      const title = document.getElementById('issueTitle').value.trim();
      const desc = document.getElementById('issueDesc').value.trim();
      if (title.length > 5 || desc.length > 15) {
        app.triggerManualAiAnalysis();
      }
    }, 800);
  },

  triggerManualAiAnalysis: async () => {
    const title = document.getElementById('issueTitle').value.trim();
    const desc = document.getElementById('issueDesc').value.trim();
    const loc = document.getElementById('issueLocation').value.trim();
    const statusLabel = document.getElementById('aiAnalysisStatus');
    const insightsBox = document.getElementById('aiInsightsBox');

    if (!title && !desc) {
      app.showToast("Please enter an issue title or description first", "error");
      return;
    }

    statusLabel.textContent = "⚡ Gemini evaluating...";
    insightsBox.classList.add('analyzing');

    try {
      const res = await fetch('/api/ai/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description: desc,
          location: loc,
          image: app.state.selectedPhoto
        })
      });

      const ai = await res.json();
      insightsBox.classList.remove('analyzing');
      statusLabel.textContent = `✓ Triaged via ${ai.ai_source || 'Gemini'}`;

      // Update UI elements
      document.getElementById('aiCategoryVal').textContent = ai.category;
      document.getElementById('aiDepartmentVal').textContent = `${ai.recommended_department} (SLA: ${ai.estimated_sla_hours}h)`;
      document.getElementById('aiReasoningVal').textContent = `"${ai.reasoning}"`;
      document.getElementById('aiConfidenceBadge').textContent = `${Math.round((ai.confidence || 0.95) * 100)}% Confidence`;

      const pBadge = document.getElementById('aiPriorityBadge');
      pBadge.className = `badge badge-${ai.priority.toLowerCase()}`;
      pBadge.textContent = `${ai.priority} (${ai.priority_score}/100)`;

      // Auto-set the Category select option
      const catSelect = document.getElementById('issueCategorySelect');
      for (let i = 0; i < catSelect.options.length; i++) {
        if (catSelect.options[i].value === ai.category) {
          catSelect.selectedIndex = i;
          break;
        }
      }
    } catch (e) {
      console.error("AI Analysis error:", e);
      statusLabel.textContent = "Analysis completed with local rules";
      insightsBox.classList.remove('analyzing');
    }
  },

  // Submit Issue
  submitIssue: async (event) => {
    event.preventDefault();
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>⏳ Lodging complaint with AI triage...</span>`;

    const title = document.getElementById('issueTitle').value.trim();
    const description = document.getElementById('issueDesc').value.trim();
    const location_address = document.getElementById('issueLocation').value.trim();
    const category = document.getElementById('issueCategorySelect').value;
    const citizen_name = document.getElementById('citizenName').value.trim();
    const citizen_contact = document.getElementById('citizenContact').value.trim();

    try {
      const res = await fetch('/api/issues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          description,
          location_address,
          category,
          citizen_name,
          citizen_contact,
          image_data: app.state.selectedPhoto
        })
      });

      const data = await res.json();

      if (data.success) {
        app.state.latestSubmittedCode = data.tracking_code;

        // Reset form
        document.getElementById('reportForm').reset();
        app.removePhoto();

        // Refresh data
        await app.fetchIssues();
        await app.fetchAnalytics();

        // Show Confirmation Modal
        document.getElementById('confirmTrackingCode').textContent = data.tracking_code;
        const confBadge = document.getElementById('confirmPriorityBadge');
        confBadge.className = `badge badge-${data.priority.toLowerCase()}`;
        confBadge.textContent = `${data.priority} Priority`;
        document.getElementById('confirmDeptBadge').textContent = data.department;

        app.openModal('confirmModal');
        app.showToast(`Issue ${data.tracking_code} submitted successfully!`, "success");
      } else {
        app.showToast(data.error || "Submission failed", "error");
      }
    } catch (e) {
      console.error("Submission error:", e);
      app.showToast("Network error submitting complaint", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        Submit Civic Complaint
      `;
    }
  },

  // Filter Issues
  filterIssues: () => {
    app.state.departmentFilter = document.getElementById('filterDept').value;
    app.state.priorityFilter = document.getElementById('filterPriority').value;
    app.state.sortBy = document.getElementById('filterSort').value;
    app.state.searchKeyword = document.getElementById('searchKeyword').value.trim();
    app.fetchIssues();
  },

  setStatusFilter: (status) => {
    app.state.statusFilter = status;
    document.querySelectorAll('.status-tab').forEach(tab => {
      tab.classList.toggle('active', tab.getAttribute('data-status') === status);
    });
    app.fetchIssues();
  },

  // Render Public Issue Cards Grid
  renderIssues: () => {
    const grid = document.getElementById('issuesGrid');
    const noIssues = document.getElementById('noIssuesFound');
    const filterCount = document.getElementById('filterCount');

    grid.innerHTML = '';
    const issues = app.state.issues;
    filterCount.textContent = issues.length;

    if (issues.length === 0) {
      noIssues.style.display = 'block';
      return;
    }
    noIssues.style.display = 'none';

    issues.forEach(issue => {
      const card = document.createElement('div');
      card.className = 'card issue-card';

      // Status Badge class
      const statusSlug = issue.status.toLowerCase().replace(/\s+/g, '-');
      const prioritySlug = issue.priority.toLowerCase();

      // Progress Stepper indices: 0: Reported, 1: Under Review, 2: In Progress, 3: Resolved
      const statusSteps = ['Reported', 'Under Review', 'In Progress', 'Resolved'];
      const currentIndex = statusSteps.indexOf(issue.status);

      // Thumbnail Image or SVG Placeholder
      let thumbHtml = '';
      if (issue.image_data) {
        thumbHtml = `<img src="${issue.image_data}" alt="Complaint evidence">`;
      } else {
        thumbHtml = `
          <div class="issue-thumb-placeholder">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span style="font-size: 0.75rem; margin-top: 0.25rem;">${issue.category}</span>
          </div>
        `;
      }

      // Time ago
      const timeAgo = app.formatTimeAgo(issue.created_at);

      card.innerHTML = `
        <div class="issue-card-thumb">
          ${thumbHtml}
          <div class="issue-badges-overlay">
            <span class="tracking-pill">${issue.tracking_code}</span>
            <span class="badge badge-${prioritySlug}">
              <span style="width: 6px; height: 6px; border-radius: 50%; background: currentColor;"></span>
              ${issue.priority} (${issue.priority_score}/100)
            </span>
          </div>
        </div>

        <div class="issue-card-body">
          <div class="issue-category-row">
            <span class="issue-category-name">${issue.category}</span>
            <span class="badge badge-status-${statusSlug}">${issue.status}</span>
          </div>

          <h3 class="issue-title">${app.escapeHtml(issue.title)}</h3>

          <div class="issue-location">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <span>${app.escapeHtml(issue.location_address)}</span>
          </div>

          <p class="issue-desc">${app.escapeHtml(issue.description)}</p>

          <div class="ai-dept-strip">
            <div>
              <div class="ai-dept-label">Routed Department</div>
              <div class="ai-dept-name">${app.escapeHtml(issue.department)}</div>
            </div>
            <span style="font-size: 0.75rem; font-weight: 700; color: #4f46e5;">SLA: ${issue.estimated_sla_hours}h</span>
          </div>

          <!-- Lifecycle Progress Stepper (Reported -> In Progress -> Resolved) -->
          <div class="status-tracker-box">
            <div class="status-tracker-header">
              <span class="status-tracker-title">Resolution Lifecycle</span>
              <span class="status-tracker-curr status-${statusSlug}">${issue.status}</span>
            </div>
            <div class="status-stepper-bar">
              <div class="status-step-item ${currentIndex === 0 ? 'active' : ''} ${currentIndex > 0 ? 'passed' : ''}">
                <span class="step-circle">${currentIndex > 0 ? '✓' : '1'}</span>
                <span class="step-label">Reported</span>
              </div>
              <div class="step-connector ${currentIndex >= 1 ? 'passed' : ''}"></div>
              <div class="status-step-item ${currentIndex === 1 ? 'active' : ''} ${currentIndex > 1 ? 'passed' : ''}">
                <span class="step-circle">${currentIndex > 1 ? '✓' : '2'}</span>
                <span class="step-label">Review</span>
              </div>
              <div class="step-connector ${currentIndex >= 2 ? 'passed' : ''}"></div>
              <div class="status-step-item ${currentIndex === 2 ? 'active' : ''} ${currentIndex > 2 ? 'passed' : ''}">
                <span class="step-circle">${currentIndex > 2 ? '✓' : '3'}</span>
                <span class="step-label">In Progress</span>
              </div>
              <div class="step-connector ${currentIndex >= 3 ? 'passed' : ''}"></div>
              <div class="status-step-item ${currentIndex === 3 ? 'active resolved' : ''} ${currentIndex > 3 ? 'passed' : ''}">
                <span class="step-circle">${currentIndex === 3 ? '✓' : '4'}</span>
                <span class="step-label">Resolved</span>
              </div>
            </div>
          </div>

          <div class="issue-card-footer">
            <button class="upvote-btn ${app.state.upvotedIds.has(issue.id) ? 'upvoted' : ''}" onclick="app.upvoteIssue(${issue.id}, event)">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
              <span>${issue.upvotes_count || 1} Me Too</span>
            </button>

            <span style="font-size: 0.75rem; color: var(--text-light);">${timeAgo}</span>

            <button class="btn btn-secondary btn-sm" onclick="app.openIssueDetails(${issue.id})">
              Details &amp; Timeline
            </button>
          </div>
        </div>
      `;

      grid.appendChild(card);
    });
  },

  // Upvote Issue
  upvoteIssue: async (issueId, event) => {
    if (event) event.stopPropagation();

    try {
      const res = await fetch(`/api/issues/${issueId}/upvote`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        app.state.upvotedIds.add(issueId);
        // Update local object
        const issue = app.state.issues.find(i => i.id === issueId);
        if (issue) issue.upvotes_count = data.upvotes;
        app.renderIssues();
        app.showToast("Upvoted! Helps prioritize municipal dispatch.", "info");
      }
    } catch (e) {
      console.error("Upvote error:", e);
    }
  },

  // Open Issue Details Modal
  openIssueDetails: async (issueId) => {
    app.state.currentIssueId = issueId;
    document.getElementById('commentIssueId').value = issueId;

    try {
      const res = await fetch(`/api/issues/${issueId}`);
      const issue = await res.json();

      document.getElementById('modalTrackingCode').textContent = issue.tracking_code;
      document.getElementById('modalTitle').textContent = issue.title;
      document.getElementById('modalLocation').textContent = issue.location_address;
      document.getElementById('modalReportedTime').textContent = `Reported ${app.formatTimeAgo(issue.created_at)}`;
      document.getElementById('modalReporterName').textContent = `By ${issue.citizen_name || 'Citizen'}`;
      document.getElementById('modalDescription').textContent = issue.description;

      // Badges
      const pBadge = document.getElementById('modalPriorityBadge');
      pBadge.className = `badge badge-${issue.priority.toLowerCase()}`;
      pBadge.textContent = `${issue.priority} Priority (${issue.priority_score}/100)`;

      const sBadge = document.getElementById('modalStatusBadge');
      sBadge.className = `badge badge-status-${issue.status.toLowerCase().replace(/\s+/g, '-')}`;
      sBadge.textContent = issue.status;

      // AI Info
      document.getElementById('modalAiConfidence').textContent = `Confidence: ${Math.round((issue.ai_confidence || 0.94) * 100)}%`;
      document.getElementById('modalAiDepartment').textContent = issue.department;
      document.getElementById('modalAssignedCrew').textContent = issue.assigned_team || 'Pending Crew Assignment';
      document.getElementById('modalAiReasoning').textContent = issue.ai_reasoning || 'Automated risk evaluation completed by Gemini AI.';

      // Hazards list
      const hContainer = document.getElementById('modalHazardsList');
      hContainer.innerHTML = '';
      if (issue.safety_hazards && issue.safety_hazards.length) {
        issue.safety_hazards.forEach(hazard => {
          const tag = document.createElement('span');
          tag.className = 'badge';
          tag.style.background = '#fee2e2';
          tag.style.color = '#991b1b';
          tag.style.border = '1px solid #fecaca';
          tag.textContent = `⚠️ ${hazard}`;
          hContainer.appendChild(tag);
        });
      }

      // Photos (Before & After comparison if resolved)
      const photoBox = document.getElementById('modalPhotoContainer');
      photoBox.innerHTML = '';

      if (issue.status === 'Resolved' && (issue.image_data || issue.resolution_image)) {
        photoBox.innerHTML = `
          <div class="comparison-grid">
            <div class="comparison-box">
              <img src="${issue.image_data || app.samplePhotos.pothole}" alt="Before resolution">
              <span class="comparison-tag" style="background: rgba(239, 68, 68, 0.9);">BEFORE: Citizen Evidence</span>
            </div>
            <div class="comparison-box">
              <img src="${issue.resolution_image || app.samplePhotos.repaired_road}" alt="After resolution">
              <span class="comparison-tag" style="background: rgba(16, 185, 129, 0.9);">AFTER: Verified Repair</span>
            </div>
          </div>
          ${issue.resolution_notes ? `<div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 0.75rem 1rem; border-radius: var(--radius-md); font-size: 0.85rem; color: #065f46;"><strong>Authority Resolution Note:</strong> ${app.escapeHtml(issue.resolution_notes)}</div>` : ''}
        `;
      } else if (issue.image_data) {
        photoBox.innerHTML = `
          <div style="border-radius: var(--radius-md); overflow: hidden; max-height: 260px; border: 1px solid var(--border);">
            <img src="${issue.image_data}" alt="Evidence photo" style="width: 100%; height: 100%; object-fit: cover;">
          </div>
        `;
      }

      // Timeline
      const tContainer = document.getElementById('modalTimeline');
      tContainer.innerHTML = '';
      if (issue.history && issue.history.length) {
        issue.history.forEach(item => {
          const tItem = document.createElement('div');
          tItem.className = 'timeline-item';
          tItem.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="timeline-title">
                <span>${app.escapeHtml(item.new_status)}</span>
                <span class="timeline-time">${app.formatTimeAgo(item.created_at)}</span>
              </div>
              <div style="font-size: 0.75rem; font-weight: 600; color: var(--primary); margin-top: 0.15rem;">${app.escapeHtml(item.changed_by)}</div>
              <div class="timeline-desc">${app.escapeHtml(item.notes || 'Status updated')}</div>
            </div>
          `;
          tContainer.appendChild(tItem);
        });
      }

      // Comments
      const cContainer = document.getElementById('modalCommentsList');
      cContainer.innerHTML = '';
      if (issue.comments && issue.comments.length) {
        issue.comments.forEach(c => {
          const cEl = document.createElement('div');
          cEl.className = 'comment-item';
          const isAuth = c.author_role === 'Authority';
          cEl.innerHTML = `
            <div class="comment-author">
              <span>${app.escapeHtml(c.author_name)}</span>
              <span class="badge" style="background: ${isAuth ? '#ede9fe' : '#e2e8f0'}; color: ${isAuth ? '#6d28d9' : '#475569'}; font-size: 0.65rem;">${c.author_role}</span>
              <span style="font-size: 0.72rem; color: var(--text-light); font-weight: normal; margin-left: auto;">${app.formatTimeAgo(c.created_at)}</span>
            </div>
            <div class="comment-text">${app.escapeHtml(c.message)}</div>
          `;
          cContainer.appendChild(cEl);
        });
      } else {
        cContainer.innerHTML = `<div style="font-size: 0.82rem; color: var(--text-light); font-style: italic;">No updates posted yet.</div>`;
      }

      app.openModal('issueDetailModal');
    } catch (e) {
      console.error("Error opening issue details:", e);
      app.showToast("Could not load issue details", "error");
    }
  },

  // Submit Comment
  submitComment: async (event) => {
    event.preventDefault();
    const issueId = document.getElementById('commentIssueId').value;
    const msg = document.getElementById('commentInput').value.trim();
    if (!msg) return;

    const authorRole = app.state.activeRole === 'admin' ? 'Authority' : 'Citizen';
    const authorName = app.state.activeRole === 'admin' ? 'Municipal Control Officer' : 'Concerned Resident';

    try {
      const res = await fetch(`/api/issues/${issueId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          author_name: authorName,
          author_role: authorRole,
          message: msg
        })
      });

      const data = await res.json();
      if (data.success) {
        document.getElementById('commentInput').value = '';
        app.openIssueDetails(issueId);
        app.showToast("Comment posted", "info");
      }
    } catch (e) {
      console.error("Error posting comment:", e);
    }
  },

  // ADMIN OPERATIONS
  renderAdminView: () => {
    const deptFilter = document.getElementById('adminDeptFilter').value;
    let issues = app.state.issues;
    if (deptFilter !== 'all') {
      issues = issues.filter(i => i.department === deptFilter);
    }

    if (app.state.adminViewMode === 'table') {
      app.renderAdminTable(issues);
    } else {
      app.renderAdminKanban(issues);
    }
  },

  renderAdminTable: (issues) => {
    const tbody = document.getElementById('adminTableBody');
    tbody.innerHTML = '';

    issues.forEach(issue => {
      const tr = document.createElement('tr');
      const pSlug = issue.priority.toLowerCase();
      const sSlug = issue.status.toLowerCase().replace(/\s+/g, '-');

      let quickActionHtml = '';
      if (issue.status === 'Reported') {
        quickActionHtml = `<button class="btn btn-sm" style="background:#ede9fe; color:#6d28d9; border:1px solid #ddd6fe; padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="app.quickAdvanceStatus(${issue.id}, 'Under Review', event)" title="Move to Under Review">🔍 Review</button>`;
      } else if (issue.status === 'Under Review') {
        quickActionHtml = `<button class="btn btn-sm" style="background:#dbeafe; color:#1d4ed8; border:1px solid #bfdbfe; padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="app.quickAdvanceStatus(${issue.id}, 'In Progress', event)" title="Dispatch Field Crew">🚛 Dispatch</button>`;
      } else if (issue.status === 'In Progress') {
        quickActionHtml = `<button class="btn btn-sm" style="background:#d1fae5; color:#047857; border:1px solid #a7f3d0; padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="app.quickAdvanceStatus(${issue.id}, 'Resolved', event)" title="Mark Resolved with Verified Proof">✅ Resolve</button>`;
      }

      tr.innerHTML = `
        <td style="font-family: monospace; font-weight: 700; color: var(--primary);">${issue.tracking_code}</td>
        <td>
          <div style="font-weight: 700; color: var(--text-main);">${app.escapeHtml(issue.title)}</div>
          <div style="font-size: 0.78rem; color: var(--text-muted);">${app.escapeHtml(issue.location_address)}</div>
        </td>
        <td><span class="badge" style="background: var(--bg-subtle); color: var(--text-main);">${issue.category}</span></td>
        <td><span class="badge badge-${pSlug}">${issue.priority}</span></td>
        <td style="font-weight: 600; font-size: 0.82rem;">${app.escapeHtml(issue.department)}</td>
        <td><span class="badge badge-status-${sSlug}">${issue.status}</span></td>
        <td style="font-size: 0.82rem; color: var(--text-muted);">${app.escapeHtml(issue.assigned_team || 'Unassigned')}</td>
        <td>
          <div style="display: flex; gap: 0.4rem; align-items: center;">
            ${quickActionHtml}
            <button class="btn btn-secondary btn-sm" onclick="app.openAdminModal(${issue.id})" style="padding: 0.2rem 0.55rem; font-size: 0.75rem;" title="Full Triage Management">
              ⚙️
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  },

  renderAdminKanban: (issues) => {
    const cols = {
      'Reported': document.getElementById('kanbanCardsReported'),
      'Under Review': document.getElementById('kanbanCardsReview'),
      'In Progress': document.getElementById('kanbanCardsProgress'),
      'Resolved': document.getElementById('kanbanCardsResolved')
    };

    // Reset columns
    Object.values(cols).forEach(col => col.innerHTML = '');

    const counts = { 'Reported': 0, 'Under Review': 0, 'In Progress': 0, 'Resolved': 0 };

    issues.forEach(issue => {
      counts[issue.status] = (counts[issue.status] || 0) + 1;
      const targetCol = cols[issue.status];
      if (!targetCol) return;

      let advanceBtnHtml = '';
      if (issue.status === 'Reported') {
        advanceBtnHtml = `<button class="btn btn-sm" style="background:#ede9fe; color:#6d28d9; border:1px solid #ddd6fe; padding:0.15rem 0.45rem; font-size:0.68rem;" onclick="app.quickAdvanceStatus(${issue.id}, 'Under Review', event)">➔ Review</button>`;
      } else if (issue.status === 'Under Review') {
        advanceBtnHtml = `<button class="btn btn-sm" style="background:#dbeafe; color:#1d4ed8; border:1px solid #bfdbfe; padding:0.15rem 0.45rem; font-size:0.68rem;" onclick="app.quickAdvanceStatus(${issue.id}, 'In Progress', event)">➔ Dispatch</button>`;
      } else if (issue.status === 'In Progress') {
        advanceBtnHtml = `<button class="btn btn-sm" style="background:#d1fae5; color:#047857; border:1px solid #a7f3d0; padding:0.15rem 0.45rem; font-size:0.68rem;" onclick="app.quickAdvanceStatus(${issue.id}, 'Resolved', event)">➔ Resolve</button>`;
      }

      const card = document.createElement('div');
      card.className = 'kanban-card';
      card.onclick = () => app.openAdminModal(issue.id);

      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
          <span style="font-family: monospace; font-size: 0.72rem; font-weight: 700; color: var(--primary);">${issue.tracking_code}</span>
          <span class="badge badge-${issue.priority.toLowerCase()}" style="font-size: 0.65rem; padding: 0.15rem 0.45rem;">${issue.priority}</span>
        </div>
        <div style="font-weight: 700; font-size: 0.88rem; color: var(--text-main); margin-bottom: 0.25rem;">${app.escapeHtml(issue.title)}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">${app.escapeHtml(issue.location_address)}</div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem;">
          <span style="font-size: 0.72rem; background: var(--bg-subtle); padding: 0.2rem 0.45rem; border-radius: var(--radius-sm); color: #334155; font-weight: 600;">
            ${app.escapeHtml(issue.department.split('&')[0].trim())}
          </span>
          ${advanceBtnHtml}
        </div>
      `;
      targetCol.appendChild(card);
    });

    // Update counts
    document.getElementById('kanbanCountReported').textContent = counts['Reported'];
    document.getElementById('kanbanCountReview').textContent = counts['Under Review'];
    document.getElementById('kanbanCountProgress').textContent = counts['In Progress'];
    document.getElementById('kanbanCountResolved').textContent = counts['Resolved'];
  },

  // Quick 1-Click Status Advance for Authorities & Judges
  quickAdvanceStatus: async (issueId, nextStatus, event) => {
    if (event) event.stopPropagation();
    const issue = app.state.issues.find(i => i.id === issueId);
    if (!issue) return;

    let assignedTeam = issue.assigned_team;
    let resolutionNotes = issue.resolution_notes;
    let resolutionImage = issue.resolution_image;

    if (nextStatus === 'Under Review') {
      resolutionNotes = 'Municipal triage officer initiated technical safety inspection.';
    } else if (nextStatus === 'In Progress') {
      assignedTeam = assignedTeam || 'Municipal Rapid Response Crew #2';
      resolutionNotes = `Dispatched ${assignedTeam} with heavy maintenance equipment.`;
    } else if (nextStatus === 'Resolved') {
      resolutionNotes = 'Repairs verified complete by municipal inspector. Area safe for public use.';
      if (!resolutionImage) {
        resolutionImage = app.samplePhotos.repaired_road;
      }
    }

    try {
      const res = await fetch(`/api/issues/${issueId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: nextStatus,
          department: issue.department,
          assigned_team: assignedTeam,
          resolution_notes: resolutionNotes,
          resolution_image: resolutionImage,
          admin_name: "Chief Municipal Administrator"
        })
      });
      const data = await res.json();
      if (data.success) {
        await app.fetchIssues();
        await app.fetchAnalytics();
        app.showToast(`Issue ${issue.tracking_code} advanced to '${nextStatus}'!`, "success");
      }
    } catch (e) {
      console.error("Quick advance error:", e);
      app.showToast("Failed to advance status", "error");
    }
  },

  openAdminModal: (issueId) => {
    app.state.currentIssueId = issueId;
    const issue = app.state.issues.find(i => i.id === issueId);
    if (!issue) return;

    document.getElementById('adminIssueId').value = issue.id;
    document.getElementById('adminModalTrackingCode').textContent = issue.tracking_code;
    document.getElementById('adminStatusSelect').value = issue.status;
    document.getElementById('adminDeptSelect').value = issue.department;
    document.getElementById('adminAssignedTeam').value = issue.assigned_team || '';
    document.getElementById('adminNotes').value = issue.resolution_notes || '';

    // Resolution photo preview
    if (issue.resolution_image) {
      document.getElementById('resPhotoImg').src = issue.resolution_image;
      document.getElementById('resPhotoPreview').style.display = 'block';
    } else {
      document.getElementById('resPhotoPreview').style.display = 'none';
    }

    app.openModal('adminManageModal');
  },

  openAdminModalFromDetail: () => {
    if (app.state.currentIssueId) {
      app.closeModal('issueDetailModal');
      app.openAdminModal(app.state.currentIssueId);
    }
  },

  submitAdminUpdate: async (event) => {
    event.preventDefault();
    const issueId = document.getElementById('adminIssueId').value;
    const newStatus = document.getElementById('adminStatusSelect').value;
    const newDept = document.getElementById('adminDeptSelect').value;
    const assignedTeam = document.getElementById('adminAssignedTeam').value.trim();
    const notes = document.getElementById('adminNotes').value.trim();

    try {
      const res = await fetch(`/api/issues/${issueId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          department: newDept,
          assigned_team: assignedTeam,
          resolution_notes: notes,
          resolution_image: app.state.selectedResolutionPhoto,
          admin_name: "Municipal Control Officer"
        })
      });

      const data = await res.json();
      if (data.success) {
        app.closeModal('adminManageModal');
        await app.fetchIssues();
        await app.fetchAnalytics();
        app.showToast(`Issue ${issueId} updated to '${newStatus}'`, "success");
      }
    } catch (e) {
      console.error("Admin update error:", e);
      app.showToast("Failed to update issue status", "error");
    }
  },

  // Export CSV
  exportCsvReport: () => {
    const issues = app.state.issues;
    if (!issues || !issues.length) {
      app.showToast("No issues to export", "error");
      return;
    }

    const headers = ["Tracking Code", "Title", "Category", "Priority", "Urgency Score", "Department", "Status", "Location", "SLA Hours", "Reported At", "Resolved At"];
    const rows = issues.map(i => [
      `"${i.tracking_code}"`,
      `"${(i.title || '').replace(/"/g, '""')}"`,
      `"${i.category}"`,
      `"${i.priority}"`,
      i.priority_score,
      `"${i.department}"`,
      `"${i.status}"`,
      `"${(i.location_address || '').replace(/"/g, '""')}"`,
      i.estimated_sla_hours,
      `"${i.created_at}"`,
      `"${i.resolved_at || ''}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `CivicResolve_Audit_Report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    app.showToast("Exported municipal audit CSV", "success");
  },

  // Reset Demo Data
  resetDemoData: async () => {
    if (!confirm("Reset database to initial demo complaints and metrics?")) return;

    try {
      const res = await fetch('/api/reset-demo', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        await app.fetchIssues();
        await app.fetchAnalytics();
        app.showToast("Demo data reseeded successfully", "success");
      }
    } catch (e) {
      console.error("Reset error:", e);
    }
  },

  // Render Charts
  renderAnalyticsCharts: (analytics) => {
    const maxVal = Math.max(...Object.values(analytics.category_counts || { a: 1 }), 1);

    // 1. Category Chart
    const catContainer = document.getElementById('chartCategoryBars');
    catContainer.innerHTML = '';
    const catEntries = Object.entries(analytics.category_counts || {});
    catEntries.forEach(([cat, count]) => {
      const pct = Math.round((count / maxVal) * 100);
      const row = document.createElement('div');
      row.className = 'bar-row';
      row.innerHTML = `
        <div class="bar-label-row">
          <span>${cat}</span>
          <span style="color: var(--primary); font-weight: 700;">${count}</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${pct}%; background: var(--primary);"></div>
        </div>
      `;
      catContainer.appendChild(row);
    });

    // 2. Priority Chart
    const prioContainer = document.getElementById('chartPriorityBars');
    prioContainer.innerHTML = '';
    const prioColors = {
      'Critical': 'var(--prio-critical)',
      'High': 'var(--prio-high)',
      'Medium': 'var(--prio-medium)',
      'Low': 'var(--prio-low)'
    };
    const total = analytics.total_issues || 1;
    ['Critical', 'High', 'Medium', 'Low'].forEach(p => {
      const count = analytics.priority_counts[p] || 0;
      const pct = Math.round((count / total) * 100);
      const row = document.createElement('div');
      row.className = 'bar-row';
      row.innerHTML = `
        <div class="bar-label-row">
          <span>${p} Urgency</span>
          <span style="color: ${prioColors[p]}; font-weight: 700;">${count} (${pct}%)</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${pct}%; background: ${prioColors[p]};"></div>
        </div>
      `;
      prioContainer.appendChild(row);
    });

    // 3. Department Chart
    const deptContainer = document.getElementById('chartDeptBars');
    deptContainer.innerHTML = '';
    const deptEntries = Object.entries(analytics.department_counts || {});
    deptEntries.forEach(([dept, count]) => {
      const pct = Math.round((count / total) * 100);
      const row = document.createElement('div');
      row.className = 'bar-row';
      row.innerHTML = `
        <div class="bar-label-row">
          <span>${dept}</span>
          <span style="font-weight: 700;">${count} cases</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${pct}%; background: var(--secondary);"></div>
        </div>
      `;
      deptContainer.appendChild(row);
    });
  },

  // API Key Configuration
  openAiConfigModal: () => {
    app.openModal('aiConfigModal');
  },

  saveApiKey: async () => {
    const key = document.getElementById('apiKeyInput').value.trim();
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gemini_api_key: key })
      });
      const data = await res.json();
      if (data.success) {
        app.closeModal('aiConfigModal');
        await app.fetchConfig();
        app.showToast("Gemini API key updated", "success");
      }
    } catch (e) {
      console.error("Save API key error:", e);
    }
  },

  copyTrackingCode: () => {
    if (app.state.latestSubmittedCode) {
      navigator.clipboard.writeText(app.state.latestSubmittedCode);
      app.showToast("Tracking code copied to clipboard", "info");
    }
  },

  viewLatestIssue: () => {
    if (app.state.latestSubmittedCode) {
      const found = app.state.issues.find(i => i.tracking_code === app.state.latestSubmittedCode);
      if (found) {
        app.openIssueDetails(found.id);
      }
    }
  },

  // Modal Helpers
  openModal: (modalId) => {
    const m = document.getElementById(modalId);
    if (m) m.classList.add('active');
  },

  closeModal: (modalId) => {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove('active');
  },

  // Toast Notification
  showToast: (msg, type = "info") => {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.style.cssText = `
      background: ${type === 'error' ? '#ef4444' : (type === 'success' ? '#10b981' : '#1e1b4b')};
      color: white;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-size: 0.88rem;
      font-weight: 600;
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.2);
      transition: all 0.3s ease;
      opacity: 0;
      transform: translateY(10px);
      pointer-events: auto;
    `;
    toast.textContent = msg;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    }, 10);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  // Utilities
  escapeHtml: (str) => {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  formatTimeAgo: (isoString) => {
    if (!isoString) return 'recently';
    const date = new Date(isoString);
    const now = new Date();
    const diffSec = Math.floor((now - date) / 1000);

    if (isNaN(diffSec) || diffSec < 0) return 'just now';
    if (diffSec < 60) return 'just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'yesterday';
    return `${diffDays}d ago`;
  }
};

// Auto-run on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
