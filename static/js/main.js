/* ═══════════════════════════════════════════════════════════════════════
   SOIL VISION 360 — Main JavaScript
   Handles: Upload, Analysis, Map, Chatbot, Auth, Animations
   ═══════════════════════════════════════════════════════════════════════ */

'use strict';

// ─── APP STATE ─────────────────────────────────────────────────────────────────
const SV360 = {
  currentAnalysis: null,
  currentUser: null,
  cardFlipped: false,
  
  SOIL_THEMES: {
  'Black Soil':    { theme: 'theme-black',  icon: '🌑', color: '#9ca3af', mapColor: '#374151' },
  'Red Soil':      { theme: 'theme-red',    icon: '🔴', color: '#f87171', mapColor: '#7f1d1d' },
  'Clay Soil':     { theme: 'theme-yellow', icon: '🟡', color: '#fbbf24', mapColor: '#78350f' },
  'Alluvial Soil': { theme: 'theme-brown',  icon: '🟫', color: '#d97706', mapColor: '#4a2c0a' },

  'Cinder Soil':   { theme: 'theme-dark',   icon: '🪨', color: '#6b7280', mapColor: '#111827' },
  'Laterite Soil': { theme: 'theme-red',    icon: '🧱', color: '#b91c1c', mapColor: '#7f1d1d' },
  'Peat Soil':     { theme: 'theme-brown',  icon: '🌿', color: '#92400e', mapColor: '#451a03' },
  'Yellow Soil':   { theme: 'theme-yellow', icon: '🌕', color: '#facc15', mapColor: '#a16207' }
},
  
  CROPS: ['Wheat', 'Cotton', 'Sugarcane', 'Paddy', 'Groundnut', 'Millets', 'Maize', 'Sunflower'],
};

// ─── INITIALIZATION ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initUploadZone();
  //initLeafletMap();
  checkAuthState();
  animateHero();
});

// ─── ANIMATIONS ────────────────────────────────────────────────────────────────
function animateHero() {
  const elements = document.querySelectorAll('.hero-badge, .hero-title, .hero-subtitle, .hero-stats, .hero-cta');
  elements.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    setTimeout(() => {
      el.style.transition = 'all 0.7s cubic-bezier(0.23, 1, 0.32, 1)';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, 100 + i * 120);
  });
}

// ─── FILE UPLOAD ────────────────────────────────────────────────────────────────
function initUploadZone() {

  const zone = document.getElementById('uploadZone');
  const input = document.getElementById('fileInput');

  if(!zone || !input) return;

  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });

  zone.addEventListener('dragleave', () => {
    zone.classList.remove('drag-over');
  });
  
  // Drag & drop
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  });

  input.addEventListener('change', () => {
    if (input.files[0]) handleFileSelect(input.files[0]);
  });
}

function handleFileSelect(file) {
  const allowed = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp', 'image/bmp'];
  if (!allowed.includes(file.type)) {
    showToast('Please select a valid image file', 'error');
    return;
  }
  if (file.size > 16 * 1024 * 1024) {
    showToast('File too large — max 16MB', 'error');
    return;
  }
  
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('previewImg').src = e.target.result;
    document.getElementById('previewMeta').textContent =
      `${file.name} · ${(file.size / 1024).toFixed(1)} KB · ${file.type.split('/')[1].toUpperCase()}`;
    document.getElementById('uploadZone').style.display = 'none';
    document.getElementById('previewPanel').style.display = 'flex';
    
    // Store file
    SV360.selectedFile = file;
  };
  reader.readAsDataURL(file);
}

function clearImage() {
  SV360.selectedFile = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('uploadZone').style.display = 'flex';
  document.getElementById('previewPanel').style.display = 'none';
}

// ─── SOIL ANALYSIS ─────────────────────────────────────────────────────────────
async function analyzeSoil() {
  if (!SV360.selectedFile) {
    showToast('Please select a soil image first', 'error');
    return;
  }
  
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  
  showLoader();
  
  try {
    const formData = new FormData();
    formData.append('image', SV360.selectedFile);

// ✅ ADD THIS LINE
    const lang = localStorage.getItem("lang") || "en";
    formData.append("lang", lang);
    
    if (SV360.currentUser) {
      formData.append('user_id', SV360.currentUser.id);
    }
    
    // Animate loader steps
    animateLoaderSteps();
    
    const response = await fetch('/api/v1/analyze', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (!response.ok) throw new Error(result.error || 'Analysis failed');
    
    SV360.currentAnalysis = result.data;
    
    hideLoader();
    displayResults(result.data);
    
    showToast(`✓ ${result.data.soil_type} detected! Soil ID: ${result.data.soil_id}`, 'success');

    clearImage();
document.getElementById("fileInput").value = "";
btn.disabled = false;
    
  } catch (err) {
    hideLoader();
    btn.disabled = false;
    showToast(`Analysis failed: ${err.message}`, 'error');
    console.error(err);
  }
}

function animateLoaderSteps() {
  const steps = document.querySelectorAll('.loader-step');
  const texts = ['Scanning soil composition...', 'Classifying soil type...', 'Computing all scores...', 'Finalizing your report...'];
  
  steps.forEach((step, i) => {
    setTimeout(() => {
      steps.forEach(s => s.classList.remove('active'));
      if (i > 0) steps[i-1].classList.add('done');
      steps[i].classList.add('active');
      document.getElementById('loaderText').textContent = texts[i];
    }, i * 800);
  });
}

// ─── RESULTS DISPLAY ───────────────────────────────────────────────────────────
function displayResults(data) {
  const resultsSection = document.getElementById('results');
  resultsSection.style.display = 'block';
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  
  // Apply theme
  applyTheme(data.soil_type);
  
  // Soil ID
  document.getElementById('soilIdDisplay').textContent = data.soil_id;
  
  // Flip card - front
  const soilMeta = SV360.SOIL_THEMES[data.soil_type] || {};
  document.getElementById('cardSoilType').textContent = data.soil_type;
  document.getElementById('cardSoilIcon').textContent = soilMeta.icon || '🌍';
  document.getElementById('cardDescription').textContent = data.description || '';
  document.getElementById('cardRGB').textContent = 
    `RGB: ${data.avg_rgb.r}, ${data.avg_rgb.g}, ${data.avg_rgb.b}`;
  document.getElementById('cardTexture').textContent = `Texture: ${data.texture || '—'}`;
  document.getElementById('cardPH').textContent = `pH: ${data.ph_range || '—'}`;
  
  // Reset card flip
  SV360.cardFlipped = false;
  document.getElementById('resultCard').classList.remove('flipped');
  
  // Circular scores (back of card)
  renderCircularScores(data);
  
  // Score grid
  renderScoreGrid(data);
  
  // House model
  renderHouseModel(data.construction_score, data.construction_advice|| {});
  
  // Crop simulation
  runCropSimulation();
  
  // Risk & climate
  renderRiskPanel(data);
  renderClimatePanel(data.climate_impact || {});
  renderNutrients(data.nutrients || {});
  
  // Crop recommendations
  renderCropRecs(data.crop_recommendations || {});

  renderSoilLayers(data);
  
  // Update chatbot
  updateChatContext(data);
  
}

function applyTheme(soilType) {
  const body = document.getElementById('mainBody');
  const soilMeta = SV360.SOIL_THEMES[soilType] || {};
  
  // Remove all theme classes
  body.classList.remove('theme-default', 'theme-black', 'theme-red', 'theme-yellow', 'theme-brown');
  
  // Apply new theme
  const themeClass = soilMeta.theme || 'theme-default';
  body.classList.add(themeClass);
  
  // Animate bg canvas
 const bg = document.getElementById('bgCanvas');
const color = soilMeta.color || '#4ade80';

if(bg){
  bg.style.background = `
    radial-gradient(ellipse 80% 60% at 20% 20%, ${color}15 0%, transparent 60%),
    radial-gradient(ellipse 60% 80% at 80% 80%, ${color}0a 0%, transparent 60%),
    radial-gradient(ellipse 100% 100% at 50% 50%, var(--c-bg) 0%, #050709 100%)
  `;
}
  
  // Animate globe core
  const core = document.querySelector('.globe-core');
  if (core) {
    const coreColors = {
  'Black Soil': '#1a1a2e',
  'Red Soil': '#7f1d1d',
  'Clay Soil': '#78350f',
  'Alluvial Soil': '#4a2c0a',
  'Cinder Soil': '#111827',
  'Laterite Soil': '#7f1d1d',
  'Peat Soil': '#3f2a14',
  'Yellow Soil': '#a16207'
};
    core.style.background = coreColors[soilType] || '#2d5a27';
  }
}

function renderCircularScores(data) {
  const container = document.getElementById('circularScores');
  const scores = [
    { label: 'Water\nRetention', value: data.water_retention },
    { label: 'Crop\nScore', value: data.crop_score },
    { label: 'Construction', value: data.construction_score },
    { label: 'Heat\nIndex', value: data.heat_index }
  ];
  
  const circumference = 2 * Math.PI * 30; // r=30
  
  container.innerHTML = scores.map(s => `
    <div class="circ-progress">
      <svg class="circ-svg" width="72" height="72" viewBox="0 0 72 72">
        <circle class="circ-track" cx="36" cy="36" r="30"/>
        <circle class="circ-bar" cx="36" cy="36" r="30"
          stroke-dasharray="${circumference}"
          stroke-dashoffset="${circumference}"
          data-target="${(1 - s.value/100) * circumference}"
          style="stroke-dashoffset: ${circumference}"/>
      </svg>
      <div class="circ-label-val">${s.value}%</div>
      <div class="circ-label-name">${s.label.replace('\n', '<br>')}</div>
    </div>
  `).join('');
  
  // Animate after card flip
  setTimeout(() => {
    container.querySelectorAll('.circ-bar').forEach(bar => {
      const target = parseFloat(bar.getAttribute('data-target'));
      bar.style.strokeDashoffset = target;
    });
  }, 900);
}

function renderScoreGrid(data) {
  const grid = document.getElementById('scoreGrid');
  const items = [
    { label: 'Water Retention',      value: data.water_retention,       unit: '%' },
    { label: 'Crop Compatibility',   value: data.crop_score,             unit: '%' },
    { label: 'Construction Score',   value: data.construction_score,     unit: '%' },
    { label: 'Heat Index',           value: data.heat_index,             unit: '%' },
    { label: 'Land Potential',       value: data.land_potential_score,   unit: '%' },
    { label: 'Agriculture ROI',      value: data.agriculture_roi,        unit: '%' }
  ];
  
  grid.innerHTML = items.map(item => `
    <div class="score-item">
      <div class="score-label">${item.label}</div>
      <div class="score-value">${item.value}<span class="score-unit">${item.unit}</span></div>
      <div class="score-bar-wrap">
        <div class="score-bar-fill" style="width: 0%" data-target="${Math.min(item.value, 100)}%"></div>
      </div>
    </div>
  `).join('');
  
  // Animate bars
  setTimeout(() => {
    grid.querySelectorAll('.score-bar-fill').forEach(bar => {
      bar.style.width = bar.getAttribute('data-target');
    });
  }, 300);
}

function renderHouseModel(constructionScore, advice) {
  const model = document.getElementById('houseModel');
  const status = document.getElementById('houseStatus');
  const info = document.getElementById('constructionInfo');
  
  model.classList.remove('stable', 'unstable');
  
  if (constructionScore >= 50) {
    model.classList.add('stable');
    status.textContent = '✅ Structurally Stable';
    status.style.background = 'rgba(74,222,128,0.1)';
    status.style.color = '#4ade80';
    
    // Green glow on house parts
    document.querySelectorAll('.house-body, .house-roof').forEach(el => {
      el.style.fill = 'rgba(74,222,128,0.25)';
      el.style.stroke = 'rgba(74,222,128,0.6)';
    });
  } else {
    model.classList.add('unstable');
    status.textContent = '⚠️ Structural Risk Detected';
    status.style.background = 'rgba(239,68,68,0.1)';
    status.style.color = '#ef4444';
    
    // Red tint on house parts
    document.querySelectorAll('.house-body, .house-roof').forEach(el => {
      el.style.fill = 'rgba(239,68,68,0.15)';
      el.style.stroke = 'rgba(239,68,68,0.4)';
    });
  }
  
  info.innerHTML = `
    <div>Foundation: <b>${advice.foundation_type || '—'}</b></div>
    <div>Suitability: <b>${advice.suitability || 'Moderate'}</b></div>
    <div>Cost Factor: <b>${advice.estimated_cost_factor || 1}x baseline</b></div>
  `;
}

async function runCropSimulation() {
  if (!SV360.currentAnalysis) return;
  
  const crop = document.getElementById('cropSelect').value;
  const data = SV360.currentAnalysis;
  
  const container = document.getElementById('cropStages');
  const yieldEl = document.getElementById('cropYield');
  
  // Loading state
  container.innerHTML = '<div style="color: var(--c-muted); font-size: 0.85rem;">Simulating...</div>';
  
  try {
    const response = await fetch('/api/v1/simulate/crop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        crop: crop,
        crop_score: data.crop_score,
        water_retention: data.water_retention
      })
    });
    
    const result = await response.json();
    
    if (!result.success) throw new Error('Simulation failed');
    
    const sim = result.data;
    
    container.innerHTML = sim.stages.map(stage => `
      <div class="crop-stage">
        <div class="stage-name">${stage.name}</div>
        <div class="stage-bar-wrap">
          <div class="stage-bar" data-target="${stage.success_rate}%" style="width:0%"></div>
        </div>
        <div class="stage-pct">${Math.round(stage.success_rate)}%</div>
      </div>
    `).join('');
    
    yieldEl.innerHTML = `🌾 Estimated Yield: <b>${sim.estimated_yield_tons_per_ha} tons/ha</b> · ${sim.total_days} days · ${sim.success_probability}% success probability`;
    
    // Animate bars
    setTimeout(() => {
      container.querySelectorAll('.stage-bar').forEach(bar => {
        bar.style.width = bar.getAttribute('data-target');
      });
    }, 200);
    
  } catch (err) {
    // Fallback simulation
    const stages = ['Germination', 'Seedling', 'Vegetative', 'Flowering', 'Grain Fill', 'Harvest'];
    const base = (data.crop_score + data.water_retention) / 2;
    container.innerHTML = stages.map((s, i) => {
      const pct = Math.min(100, Math.max(0, base - i * 3));
      return `<div class="crop-stage">
        <div class="stage-name">${s}</div>
        <div class="stage-bar-wrap"><div class="stage-bar" data-target="${pct}%" style="width:0%"></div></div>
        <div class="stage-pct">${Math.round(pct)}%</div>
      </div>`;
    }).join('');
    
    yieldEl.innerHTML = `🌾 Estimated compatibility: <b>${Math.round(base)}%</b> for ${crop}`;
    
    setTimeout(() => {
      container.querySelectorAll('.stage-bar').forEach(bar => {
        bar.style.width = bar.getAttribute('data-target');
      });
    }, 200);
  }
}

function renderRiskPanel(data) {
  const grid = document.getElementById('riskGrid');
  
  const risks = [
    { key: 'Construction Risk', val: data.construction_risk || 'Medium' },
    { key: 'Flood Risk',        val: data.flood_risk || 'Medium' },
    { key: 'Drought Risk',      val: data.heat_index > 75 ? 'High' : 'Medium' },
    { key: 'Erosion Risk',      val: data.water_retention > 70 ? 'Low' : 'High' },
  ];
  
  grid.innerHTML = risks.map(r => {
    const cls = `risk-${r.val.toLowerCase().replace(' ', '-')}`;
    return `<div class="risk-item">
      <span class="risk-key">${r.key}</span>
      <span class="risk-val ${cls}">${r.val}</span>
    </div>`;
  }).join('');
}

function renderClimatePanel(climate) {
  const grid = document.getElementById('climateGrid');
  const items = [
    { key: 'Carbon Sequestration', val: climate.carbon_sequestration || '—' },
    { key: 'Drought Sensitivity',  val: climate.drought_sensitivity || '—' },
    { key: 'Temp Rise Effect',     val: climate.temperature_rise_effect || '—' },
    { key: 'Trend',                val: climate.trend || '—' },
  ];
  
  grid.innerHTML = items.map(i => `
    <div class="climate-item">
      <span class="climate-key">${i.key}</span>
      <span style="font-size:0.8rem; color: var(--c-text)">${i.val}</span>
    </div>
  `).join('');
}

function renderNutrients(nutrients) {
  const container = document.getElementById('nutrientBars');
  const items = [
    { name: 'Nitrogen (N)',     val: nutrients.nitrogen || 0 },
    { name: 'Phosphorus (P)',   val: nutrients.phosphorus || 0 },
    { name: 'Potassium (K)',    val: nutrients.potassium || 0 },
    { name: 'Organic Matter',  val: nutrients.organic_matter || 0 }
  ];
  
  container.innerHTML = items.map(item => `
    <div class="nutrient-item">
      <div class="nutrient-label">
        <span class="nutrient-name">${item.name}</span>
        <span class="nutrient-pct">${item.val}%</span>
      </div>
      <div class="nutrient-bar-wrap">
        <div class="nutrient-bar" data-target="${item.val}%" style="width:0%"></div>
      </div>
    </div>
  `).join('');
  
  setTimeout(() => {
    container.querySelectorAll('.nutrient-bar').forEach(bar => {
      bar.style.width = bar.getAttribute('data-target');
    });
  }, 400);
}

function renderCropRecs(recs) {
  const grid = document.getElementById('cropRecGrid');
  if (!recs.primary) { grid.innerHTML = ''; return; }
  
  grid.innerHTML = `
    <div class="crop-rec-card">
      <div class="crop-rec-title">Primary Crops</div>
      <div class="crop-rec-items">${(recs.primary || []).map(c => `<span class="crop-tag">${c}</span>`).join('')}</div>
    </div>
    <div class="crop-rec-card">
      <div class="crop-rec-title">Secondary Crops</div>
      <div class="crop-rec-items">${(recs.secondary || []).map(c => `<span class="crop-tag">${c}</span>`).join('')}</div>
    </div>
    <div class="crop-rec-card">
      <div class="crop-rec-title">Avoid</div>
      <div class="crop-rec-items">${(recs.avoid || []).map(c => `<span class="crop-tag avoid">${c}</span>`).join('')}</div>
    </div>
    <div class="crop-rec-card">
      <div class="crop-rec-title">Season & Irrigation</div>
      <div style="font-size:0.82rem; color: var(--c-muted);">
        <div>🗓️ ${recs.season || '—'}</div>
        <div>💧 ${recs.irrigation || '—'}</div>
      </div>
    </div>
  `;
}

// ─── FLIP CARD ─────────────────────────────────────────────────────────────────
function flipCard() {
  const card = document.getElementById('resultCard');
  SV360.cardFlipped = !SV360.cardFlipped;
  card.classList.toggle('flipped');
  
  // Animate circular progress when flipped to back
  if (SV360.cardFlipped) {
    setTimeout(() => {
      document.querySelectorAll('.circ-bar').forEach(bar => {
        const target = bar.getAttribute('data-target');
        if (target) bar.style.strokeDashoffset = target;
      });
    }, 400);
  }
}

// ─── CHATBOT ───────────────────────────────────────────────────────────────────
function updateChatContext(data) {
  const badge = document.getElementById('chatSoilBadge');

  if(!badge) return;

  const meta = SV360.SOIL_THEMES[data.soil_type] || {};
  badge.textContent = `${meta.icon || ''} ${data.soil_type}`;
  
  // Add context message
  addBotMessage(`Great! I've analyzed your soil. You have <b>${data.soil_type}</b> with a land potential score of <b>${data.land_potential_score}%</b>. Ask me anything about it!`);
}

function quickChat(message) {
  document.getElementById('chatInput').value = message;
  sendChat();
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;
  
  input.value = '';
  addUserMessage(message);
  
  // Typing indicator
  const typingId = addTypingIndicator();
  
  try {
    const analysis = SV360.currentAnalysis || {};
    
    const response = await fetch('/api/v1/chatbot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
      message: message,
      soil_type: analysis.soil_type || '',
      construction_score: analysis.construction_score ?? null,
      crop_score: analysis.crop_score ?? null,
      lang: localStorage.getItem("lang") || "en"   // ✅ ADD THIS
    })
    });
    
    const result = await response.json();
    removeTypingIndicator(typingId);
    
    if (result.success) {
      addBotMessage(result.response);
    } else {
      addBotMessage("I encountered an issue. Please try again!");
    }
    
  } catch (err) {
    removeTypingIndicator(typingId);
    addBotMessage("Connection issue. Please check your server and try again.");
  }
}

function addUserMessage(text) {
  const msgs = document.getElementById('chatMessages');
  msgs.insertAdjacentHTML('beforeend', `
    <div class="message user-msg">
      <div class="msg-avatar">👤</div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
    </div>
  `);
  msgs.scrollTop = msgs.scrollHeight;
}

function addBotMessage(text) {
  const msgs = document.getElementById('chatMessages');
  msgs.insertAdjacentHTML('beforeend', `
    <div class="message bot-msg">
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">${text}</div>
    </div>
  `);
  msgs.scrollTop = msgs.scrollHeight;
}

function addTypingIndicator() {
  const id = 'typing-' + Date.now();
  const msgs = document.getElementById('chatMessages');
  msgs.insertAdjacentHTML('beforeend', `
    <div class="message bot-msg typing-indicator" id="${id}">
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}
// ─── NAV AUTH STATE ────────────────────────────────────────────────────────────

/**
 * updateNavBtn — switches nav between "Sign In" and logged-in user menu.
 * Call this whenever auth state changes.
 */
function updateNavBtn(user) {
  const signinBtn  = document.getElementById('navAuthBtn');
  const userMenu   = document.getElementById('navUserMenu');
  const userName   = document.getElementById('navUserName');
  const adminLink  = document.getElementById('navAdminLink');

  if (user) {
    // Hide "Sign In", show user menu
    if (signinBtn)  signinBtn.style.display  = 'none';
    if (userMenu)   userMenu.style.display   = 'block';
    if (userName)   userName.textContent     = user.name.split(' ')[0];
    if (adminLink)  adminLink.style.display  = user.role === 'admin' ? 'flex' : 'none';
  } else {
    // Show "Sign In", hide user menu
    if (signinBtn)  signinBtn.style.display  = '';
    if (userMenu)   userMenu.style.display   = 'none';
    if (signinBtn)  signinBtn.onclick = () => {
  window.location.href = "/auth/login-page";
};
    closeUserDropdown();
  }
}

function toggleUserDropdown() {
  const dd = document.getElementById('navDropdown');
  if (dd) dd.classList.toggle('open');
}

function closeUserDropdown() {
  const dd = document.getElementById('navDropdown');
  if (dd) dd.classList.remove('open');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {

const menu = document.getElementById("navUserMenu");

if(menu && !menu.contains(e.target)){
closeUserDropdown();
}

});
// ─── AUTH ──────────────────────────────────────────────────────────────────────
function openAuthModal() { document.getElementById('authModal').style.display = 'flex'; }
function closeAuthModal() { document.getElementById('authModal').style.display = 'none'; }

function switchTab(tab) {
  document.getElementById('loginForm').style.display = tab === 'login' ? 'flex' : 'none';
  document.getElementById('registerForm').style.display = tab === 'register' ? 'flex' : 'none';
  document.querySelectorAll('.modal-tab').forEach((t, i) => {
    t.classList.toggle('active', (i === 0 && tab === 'login') || (i === 1 && tab === 'register'));
  });
}

async function doLogin() {
  const email = document.getElementById('loginEmail').value;
  const password = document.getElementById('loginPassword').value;
  const msg = document.getElementById('authMessage');
  
  try {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const result = await response.json();
    
    if (response.ok && result.success) {
      SV360.currentUser = result.user;
      closeAuthModal();
      showToast(`Welcome back, ${result.user.name}!`, 'success');
      document.querySelector('.nav-btn').textContent = result.user.name;
      
      if (result.user.role === 'admin') {
        document.getElementById('adminSection').style.display = 'block';
        loadDashboard();
      }
    } else {
      msg.textContent = result.error || 'Login failed';
      msg.className = 'modal-message error';
    }
    
  } catch (err) {
    msg.textContent = 'Connection error. Is the server running?';
    msg.className = 'modal-message error';
  }
}

async function doRegister() {
  const name = document.getElementById('regName').value;
  const email = document.getElementById('regEmail').value;
  const password = document.getElementById('regPassword').value;
  const msg = document.getElementById('authMessage');
  
  try {
    const response = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });
    
    const result = await response.json();
    
    if (response.ok && result.success) {
      msg.textContent = 'Account created! Please sign in.';
      msg.className = 'modal-message success';
      switchTab('login');
    } else {
      msg.textContent = result.error || 'Registration failed';
      msg.className = 'modal-message error';
    }
    
  } catch (err) {
    msg.textContent = 'Connection error';
    msg.className = 'modal-message error';
  }
}
function checkAuthState(){

fetch('/auth/me',{credentials:"include"})
.then(r=>r.json())
.then(result=>{

if(result.success){

SV360.currentUser = result.user;
updateNavBtn(result.user);

}else{

updateNavBtn(null);

}

})
.catch(()=>{

updateNavBtn(null);

});

}
// ─── DASHBOARD ─────────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const response = await fetch('/api/v1/dashboard/stats');
    const result = await response.json();
    if (!result.success) return;
    
    const data = result.data;
    
    // Stats cards
    document.getElementById('dashboardStats').innerHTML = `
      <div class="dash-stat">
        <div class="dash-num">${data.total_analyses.toLocaleString()}</div>
        <div class="dash-label">Total Analyses</div>
      </div>
      <div class="dash-stat">
        <div class="dash-num">${data.total_users.toLocaleString()}</div>
        <div class="dash-label">Registered Users</div>
      </div>
      <div class="dash-stat">
        <div class="dash-num">${data.averages.crop_score}%</div>
        <div class="dash-label">Avg Crop Score</div>
      </div>
      <div class="dash-stat">
        <div class="dash-num">${data.averages.land_potential}%</div>
        <div class="dash-label">Avg Land Potential</div>
      </div>
    `;
    
    // Soil distribution
    const distEl = document.getElementById('soilDonut');
   const colors = {
 'Black Soil': '#374151',
 'Red Soil': '#7f1d1d',
 'Clay Soil': '#78350f',
 'Alluvial Soil': '#4a2c0a',
 'Cinder Soil': '#111827',
 'Laterite Soil': '#991b1b',
 'Peat Soil': '#3f2a14',
 'Yellow Soil': '#a16207'
};

const total = Object.values(data.soil_distribution).reduce((a,b)=>a+b,0);
    
    distEl.innerHTML = Object.entries(data.soil_distribution).map(([type, count]) => `
      <div class="donut-slice">
        <div class="donut-dot" style="background:${colors[type] || '#888'}"></div>
        <span>${type}: <b>${count}</b> (${Math.round(count/total*100)}%)</span>
      </div>
    `).join('');
    
    // Score bars
    const chartEl = document.getElementById('scoreChart');
    const avgs = data.averages;
    chartEl.innerHTML = Object.entries(avgs).map(([key, val]) => `
      <div class="bar-item">
        <div class="bar-label">
          <span>${key.replace(/_/g, ' ')}</span>
          <span>${val}%</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width: ${val}%"></div>
        </div>
      </div>
    `).join('');
    
  } catch (err) {
    console.warn('Dashboard load failed:', err);
  }
}

// ─── PDF DOWNLOAD ──────────────────────────────────────────────────────────────
async function downloadReport() {
  if (!SV360.currentAnalysis) {
    showToast('No analysis to download', 'error');
    return;
  }
  
  showToast('Generating PDF report...', 'success');
  
  try {
    const response = await fetch('/reports/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        soil_id: SV360.currentAnalysis.soil_id,
        analysis: SV360.currentAnalysis,
        image_path: SV360.currentAnalysis.image_path
      })
    });
    
    if (!response.ok) throw new Error('PDF generation failed');
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Soil_Vision_360_${SV360.currentAnalysis.soil_id}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('Report downloaded!', 'success');
    
  } catch (err) {
    showToast(`Download failed: ${err.message}`, 'error');
  }
}

function shareResult() {
  if (!SV360.currentAnalysis) return;
  const url = `${window.location.origin}/reports/view/${SV360.currentAnalysis.soil_id}`;
  if (navigator.share) {
    navigator.share({ title: 'Soil Vision 360 Report', url });
  } else {
    navigator.clipboard.writeText(url).then(() => showToast('Report URL copied!', 'success'));
  }
}

function copySoilId() {
  const id = document.getElementById('soilIdDisplay').textContent;
  navigator.clipboard.writeText(id).then(() => showToast('Soil ID copied!', 'success'));
}

// ─── LOADER ────────────────────────────────────────────────────────────────────
function showLoader() { document.getElementById('analysisLoader').style.display = 'flex'; }
function hideLoader() { document.getElementById('analysisLoader').style.display = 'none'; }

// ─── MOBILE MENU ───────────────────────────────────────────────────────────────
function toggleMobileMenu() {
  const links = document.querySelector('.nav-links');
  links.style.display = links.style.display === 'flex' ? 'none' : 'flex';
  links.style.flexDirection = 'column';
  links.style.position = 'absolute';
  links.style.top = '70px';
  links.style.right = '1rem';
  links.style.background = 'rgba(10,12,16,0.95)';
  links.style.padding = '1rem';
  links.style.borderRadius = '12px';
  links.style.border = '1px solid rgba(255,255,255,0.08)';
  links.style.backdropFilter = 'blur(20px)';
  links.style.zIndex = '200';
}

// ─── TOAST ─────────────────────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// ─── UTILS ─────────────────────────────────────────────────────────────────────
function escapeHtml(text) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}

// Smooth reveal on scroll
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('section').forEach(section => {
  section.style.opacity = '0';
  section.style.transform = 'translateY(30px)';
  section.style.transition = 'all 0.7s cubic-bezier(0.23, 1, 0.32, 1)';
  observer.observe(section);
});

function openChatbotPage(){
   window.location.href = "/chatbot";
}

function renderSoilLayers(data){

const container = document.getElementById("soilLayers");
if(!container || !data.layers) return;

let html = `<div class="soil-layers-grid">`;

data.layers.forEach(layer=>{

let colorClass="layer-default";

// ❌ DON'T use Tamil text for logic
const raw = layer.original || layer.layer;

// ✅ use English for detection if available
const name = raw.toLowerCase();

if(name.includes("red")) colorClass="layer-red";
else if(name.includes("topsoil")) colorClass="layer-topsoil";
else if(name.includes("sand")) colorClass="layer-sand";
else if(name.includes("clay")) colorClass="layer-clay";
else if(name.includes("laterite")) colorClass="layer-laterite";
else if(name.includes("black")) colorClass="layer-black";
else if(name.includes("peat")) colorClass="layer-peat";
else if(name.includes("yellow")) colorClass="layer-yellow";
else if(name.includes("alluvial")) colorClass="layer-alluvial";
else if(name.includes("rock")) colorClass="layer-rock";

html += `
<div class="soil-layer-card ${colorClass}">
<div class="crop-rec-title">${layer.layer}</div>
<div>${layer.depth_start}m - ${layer.depth_end}m</div>
</div>
`;

});

html += `</div>`;

container.innerHTML = html;
}

function logoutUser(){

fetch('/auth/logout', {
  method: "POST",
  credentials: "include"
})
.then(()=>{

SV360.currentUser = null;

updateNavBtn(null);

showToast("Logged out successfully","success");

window.location.href="/";  


});

}

function openMyReports(){
window.location.href="/reports/view/latest";
}

async function loadLang(lang){

 const res = await fetch(`/static/lang/${lang}.json`);
 const data = await res.json();

 document.querySelectorAll("[data-lang]").forEach(el=>{

   const key = el.getAttribute("data-lang");

   if(data[key]){

     if(el.tagName === "INPUT" || el.tagName === "TEXTAREA"){
       el.placeholder = data[key];   // ✅ placeholder
     } 
     else {
       el.innerHTML = data[key];
     }

   }

 });

}

function toggleLang(){

  const current = localStorage.getItem("lang") || "en";
  const lang = current === "ta" ? "en" : "ta";

  localStorage.setItem("lang", lang);

  loadLang(lang);

  const slider = document.getElementById("langSlider");

  if(slider){
    slider.style.left = lang === "ta" ? "50%" : "0";
  }

}

document.addEventListener("DOMContentLoaded", () => {

  const lang = localStorage.getItem("lang") || "en";
  loadLang(lang);

});
