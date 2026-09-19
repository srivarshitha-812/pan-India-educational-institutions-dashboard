/**
 * Pan-India Educational Institutions — Executive Review Dashboard Controller
 * Handles live data binding, Chart.js visualizations, server-side pagination,
 * state explorer drill-downs, and global search indexing.
 */

/* ==========================================================================
   GLOBAL CATEGORY COLOR SYSTEM
   Visually distinguishable, accessibility-conscious categorical palette.
   Status colors remain semantic:
   - Green = PASS / COMPLETED (#10b981 / #34d399)
   - Amber/Yellow = IN PROGRESS / WARNING (#f59e0b)
   - Red = HIGH PRIORITY / ERROR / NEEDS REVIEW (#ef4444)
   - Neutral blue/gray = informational (#64748b)
   ========================================================================== */
const CATEGORY_COLOR_MAP = {
  'Pharmacy': {
    hex: '#ea580c',       // Warm Tangerine Orange
    bg: 'rgba(234, 88, 12, 0.15)',
    border: 'rgba(234, 88, 12, 0.45)',
    text: '#fb923c'
  },
  'Architecture': {
    hex: '#0d9488',       // Dark Pine / Deep Teal
    bg: 'rgba(13, 148, 136, 0.15)',
    border: 'rgba(13, 148, 136, 0.45)',
    text: '#2dd4bf'
  },
  'Rehabilitation & Special Education': {
    hex: '#d946ef',       // Vibrant Fuchsia / Orchid
    bg: 'rgba(217, 70, 239, 0.15)',
    border: 'rgba(217, 70, 239, 0.45)',
    text: '#f0abfc'
  },
  'Universities & Higher Education': {
    hex: '#4f46e5',       // Royal Indigo
    bg: 'rgba(79, 70, 229, 0.15)',
    border: 'rgba(79, 70, 229, 0.45)',
    text: '#a5b4fc'
  },
  'Homoeopathy Education': {
    hex: '#0284c7',       // Sky Azure
    bg: 'rgba(2, 132, 199, 0.15)',
    border: 'rgba(2, 132, 199, 0.45)',
    text: '#38bdf8'
  },
  'Nursing': {
    hex: '#7c3aed',       // Electric Purple / Violet
    bg: 'rgba(124, 58, 237, 0.15)',
    border: 'rgba(124, 58, 237, 0.45)',
    text: '#c4b5fd'
  },
  'Dental Education': {
    hex: '#06b6d4',       // Bright Cyan / Turquoise
    bg: 'rgba(6, 182, 212, 0.15)',
    border: 'rgba(6, 182, 212, 0.45)',
    text: '#67e8f9'
  },
  'Medical Education': {
    hex: '#be123c',       // Deep Crimson Rose
    bg: 'rgba(190, 18, 60, 0.15)',
    border: 'rgba(190, 18, 60, 0.45)',
    text: '#fb7185'
  },
  'Ayurveda & Unani Medicine': {
    hex: '#ca8a04',       // Warm Golden Ochre
    bg: 'rgba(202, 138, 4, 0.15)',
    border: 'rgba(202, 138, 4, 0.45)',
    text: '#fde047'
  },
  'Legal Education & Law Colleges': {
    hex: '#1e3a8a',       // Deep Midnight Cobalt
    bg: 'rgba(30, 58, 138, 0.25)',
    border: 'rgba(59, 130, 246, 0.45)',
    text: '#93c5fd'
  },
  'Teacher Education': {
    hex: '#831843',       // Scholarly Wine / Maroon
    bg: 'rgba(131, 24, 67, 0.18)',
    border: 'rgba(131, 24, 67, 0.50)',
    text: '#f472b6'
  },
  'School Education': {
    hex: '#52525b',       // Neutral Zinc
    bg: 'rgba(82, 82, 91, 0.20)',
    border: 'rgba(82, 82, 91, 0.50)',
    text: '#d4d4d8'
  }
};

const FALLBACK_CATEGORY_PALETTE = [
  '#0891b2', '#c026d3', '#e11d48', '#d97706', '#4338ca', '#059669', '#7c3aed', '#b45309'
];

function getCategoryColor(category) {
  if (!category) return '#64748b';
  const entry = CATEGORY_COLOR_MAP[category];
  if (entry) return entry.hex;
  let hash = 0;
  for (let i = 0; i < category.length; i++) {
    hash = category.charCodeAt(i) + ((hash << 5) - hash);
  }
  return FALLBACK_CATEGORY_PALETTE[Math.abs(hash) % FALLBACK_CATEGORY_PALETTE.length];
}

function getCategoryBadgeStyle(category) {
  const entry = CATEGORY_COLOR_MAP[category];
  if (entry) {
    return `background: ${entry.bg}; color: ${entry.text}; border: 1px solid ${entry.border};`;
  }
  const hex = getCategoryColor(category);
  return `background: ${hex}22; color: ${hex}; border: 1px solid ${hex}55;`;
}

function renderCategoryTag(category) {
  const style = getCategoryBadgeStyle(category);
  return `<span class="category-tag" style="${style}"><span class="category-tag-dot"></span>${category || 'Unassigned'}</span>`;
}

class DashboardApp {
  constructor() {
    this.summaryData = null;
    this.sourceDatasets = [];
    this.finalLists = [];
    this.statesList = [];
    this.pendingDatasets = [];
    this.completedPortals = [];
    this.dictionaryData = null;
    this.activeView = 'dashboard';

    // Charts
    this.categoryChart = null;
    this.statesChart = null;

    // Selected State Explorer State
    this.selectedState = null;

    // Record Modal State
    this.modalListId = null;
    this.modalPage = 1;
    this.modalPageSize = 50;
    this.modalStateFilter = 'All';
    this.modalSearch = '';
    this.modalTotalPages = 1;

    // Global Search Debounce
    this.searchDebounceTimer = null;
  }

  async init() {
    console.log('[DashboardApp] Initializing dashboard...');
    this.setupEventListeners();
    await this.loadAllData();
  }

  setupEventListeners() {
    // Mobile Navigation Toggle & Backdrop
    document.getElementById('mobile-menu-toggle')?.addEventListener('click', () => this.toggleMobileSidebar());
    document.getElementById('sidebar-backdrop')?.addEventListener('click', () => this.toggleMobileSidebar(false));
    document.getElementById('sidebar-close-btn')?.addEventListener('click', () => this.toggleMobileSidebar(false));

    window.addEventListener('resize', () => {
      if (window.innerWidth > 1024) {
        this.toggleMobileSidebar(false);
      }
    });

    // Nav Items
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', () => {
        const view = item.getAttribute('data-view');
        this.switchView(view);
      });
    });

    // Refresh Data
    document.getElementById('btn-refresh')?.addEventListener('click', async () => {
      const btn = document.getElementById('btn-refresh');
      const origHtml = btn ? btn.innerHTML : '';
      try {
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" style="width: 0.85rem; height: 0.85rem; border-width: 2px; display: inline-block; vertical-align: middle; margin-right: 4px;"></span> Refreshing dataset metadata...';
        }
        await fetch('/api/refresh', { method: 'POST' });
      } catch (e) {
        console.warn('Refresh endpoint call:', e);
      } finally {
        await this.loadAllData();
        if (btn) {
          btn.innerHTML = '<span style="color: #10b981; font-weight: 600;">✓ Refreshed</span>';
          setTimeout(() => {
            btn.innerHTML = origHtml;
            btn.disabled = false;
          }, 1800);
        }
      }
    });
    document.getElementById('btn-retry-connection')?.addEventListener('click', () => this.loadAllData());

    // Dictionary Filters
    document.getElementById('dict-search-input')?.addEventListener('input', () => this.filterDataDictionary());
    document.getElementById('dict-dataset-filter')?.addEventListener('change', () => this.filterDataDictionary());
    document.getElementById('dict-class-filter')?.addEventListener('change', () => this.filterDataDictionary());

    // Top Header Quick Search
    const quickSearch = document.getElementById('quick-search-input');
    quickSearch?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && quickSearch.value.trim().length >= 2) {
        this.switchView('search');
        const searchInput = document.getElementById('search-view-input');
        if (searchInput) {
          searchInput.value = quickSearch.value;
          this.executeGlobalSearch(quickSearch.value);
        }
      }
    });

    // Search View Input
    const searchViewInput = document.getElementById('search-view-input');
    searchViewInput?.addEventListener('input', (e) => {
      clearTimeout(this.searchDebounceTimer);
      const val = e.target.value.trim();
      this.searchDebounceTimer = setTimeout(() => {
        this.executeGlobalSearch(val);
      }, 300);
    });


    // State Search Filter
    document.getElementById('state-search')?.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      document.querySelectorAll('.state-item').forEach(el => {
        const name = el.getAttribute('data-state-name').toLowerCase();
        el.style.display = name.includes(q) ? 'flex' : 'none';
      });
    });

    // State Institution Search Filter
    document.getElementById('state-inst-search')?.addEventListener('input', (e) => {
      this.filterStateInstitutions(e.target.value.trim());
    });

    // Modal Pagination & Filters
    document.getElementById('btn-modal-prev')?.addEventListener('click', () => {
      if (this.modalPage > 1) {
        this.modalPage--;
        this.fetchModalRecords();
      }
    });

    document.getElementById('btn-modal-next')?.addEventListener('click', () => {
      if (this.modalPage < this.modalTotalPages) {
        this.modalPage++;
        this.fetchModalRecords();
      }
    });

    document.getElementById('modal-state-filter')?.addEventListener('change', (e) => {
      this.modalStateFilter = e.target.value;
      this.modalPage = 1;
      this.fetchModalRecords();
    });

    document.getElementById('modal-page-size')?.addEventListener('change', (e) => {
      this.modalPageSize = parseInt(e.target.value);
      this.modalPage = 1;
      this.fetchModalRecords();
    });

    document.getElementById('modal-search-input')?.addEventListener('input', (e) => {
      clearTimeout(this.searchDebounceTimer);
      this.searchDebounceTimer = setTimeout(() => {
        this.modalSearch = e.target.value.trim();
        this.modalPage = 1;
        this.fetchModalRecords();
      }, 300);
    });

    // Save Pending Update
    document.getElementById('btn-save-pending')?.addEventListener('click', () => this.savePendingStatusUpdate());
  }

  async loadAllData(retryCount = 0) {
    try {
      const [summaryRes, finalRes, statesRes, pendingRes, dictRes, priorityRes] = await Promise.all([
        fetch('/api/summary').then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        }),
        fetch('/api/datasets/final').then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        }),
        fetch('/api/states').then(r => r.json()),
        fetch('/api/pending').then(r => r.json()),
        fetch('/api/dictionary?page=1&page_size=500').then(r => r.json()).catch(() => null),
        fetch('/api/review-priority').then(r => r.json()).catch(() => null)
      ]);

      this.summaryData = summaryRes;
      this.finalLists = finalRes.lists;
      this.statesList = statesRes.states;
      this.pendingDatasets = pendingRes.pending || [];
      this.completedPortals = pendingRes.completed || [];
      this.dictionaryData = dictRes;
      this.reviewPriorityData = priorityRes;

      this.renderKPIs();
      this.renderCharts();
      this.renderFinalListsTable();
      this.renderDataDictionary();
      this.renderStateExplorer();
      this.renderQualityScorecard();
      this.renderReviewPriority();
      this.renderPendingDatasets();

      // Update badges
      const badgeFinal = document.getElementById('badge-final-count');
      if (badgeFinal) badgeFinal.textContent = this.finalLists.length;
      const badgePending = document.getElementById('badge-pending-count');
      if (badgePending) badgePending.textContent = this.pendingDatasets.length;
      const badgePendingQueue = document.getElementById('badge-pending-queue-count');
      if (badgePendingQueue) badgePendingQueue.textContent = `${this.pendingDatasets.length} Portals Awaiting Collection`;
      if (this.dictionaryData && this.dictionaryData.total_fields) {
        const dictBadge = document.getElementById('badge-dictionary-count');
        if (dictBadge) dictBadge.textContent = this.dictionaryData.total_fields;
      }
      // Update High Priority sidebar badge from actual review priority count
      const priorityBadge = document.getElementById('badge-priority-count');
      if (priorityBadge && this.reviewPriorityData) {
        const highCount = this.reviewPriorityData.high_count || 0;
        priorityBadge.textContent = highCount > 0 ? `${highCount} HIGH` : 'HIGH';
      }

      // Hide error banner on success
      const banner = document.getElementById('connection-error-banner');
      if (banner) banner.style.display = 'none';

    } catch (err) {
      console.error('[DashboardApp] Error loading data:', err);
      if (retryCount < 2) {
        console.log(`[DashboardApp] Retrying connection in 2.5s (attempt ${retryCount + 1}/2)...`);
        setTimeout(() => this.loadAllData(retryCount + 1), 2500);
        return;
      }
      const banner = document.getElementById('connection-error-banner');
      if (banner) {
        banner.style.display = 'block';
        const detail = document.getElementById('connection-error-detail');
        if (detail) detail.textContent = `Error: ${err.message || 'Network request failed'}. Please click Retry, check your DNS settings, or run locally via http://localhost:8000.`;
      }
    }
  }

  switchView(viewName) {
    this.activeView = viewName;

    // Automatically close mobile sidebar when switching views on mobile/tablet
    this.toggleMobileSidebar(false);

    // Update nav active
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.toggle('active', item.getAttribute('data-view') === viewName);
    });

    // Update views
    document.querySelectorAll('.tab-view').forEach(view => {
      view.classList.toggle('active', view.id === `view-${viewName}`);
    });

    // Update Page Title
    const titleMap = {
      dashboard: { title: 'Executive Overview', meta: 'National Institution Datasets & Cleaned Census Lists' },
      final: { title: 'Institutes List', meta: 'Deduplicated Higher Education Institution Roster' },
      dictionary: { title: 'Data Dictionary & Schema Specification', meta: 'Official regulatory lineage, field definitions, data types, and allowed values' },
      states: { title: 'State / UT Geographic Explorer', meta: 'Pan-India Sub-National Analysis across 36 States & UTs' },
      quality: { title: 'Data Quality & Integrity Audit', meta: 'Null Value, Duplication & Completeness Scorecard' },
      priority: { title: 'Review Priority Queue', meta: 'Ranked Datasets Requiring Strategic Attention' },
      pending: { title: 'Pending Datasets', meta: 'Remaining Regulatory Portals (Pending Collection)' },
      search: { title: 'Global Institution Search', meta: 'Multi-attribute Query across Institutes List' }
    };

    const cur = titleMap[viewName] || { title: 'Dashboard', meta: '' };
    document.getElementById('page-title').textContent = cur.title;
    document.getElementById('header-meta').textContent = cur.meta;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  toggleMobileSidebar(forceState) {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    const toggleBtn = document.getElementById('mobile-menu-toggle');
    if (!sidebar) return;
    const shouldOpen = forceState !== undefined ? forceState : !sidebar.classList.contains('open');
    sidebar.classList.toggle('open', shouldOpen);
    if (backdrop) backdrop.classList.toggle('open', shouldOpen);
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
      toggleBtn.classList.toggle('active', shouldOpen);
    }
    document.body.classList.toggle('sidebar-drawer-open', shouldOpen);
    // Reset horizontal scroll drift on Android Chrome after sidebar animation
    if (!shouldOpen) {
      const mainContent = document.querySelector('.main-content');
      if (mainContent) mainContent.scrollLeft = 0;
    }
  }

  /* --------------------------------------------------------------------------
     1. KPI Rendering
     -------------------------------------------------------------------------- */
  renderKPIs() {
    if (!this.summaryData) return;
    const kpis = this.summaryData.kpis;

    const elFinal = document.getElementById('kpi-final-lists');
    if (elFinal) elFinal.textContent = kpis.final_lists_available;

    const elFinalRec = document.getElementById('kpi-final-records');
    if (elFinalRec) elFinalRec.textContent = kpis.total_records_final.toLocaleString('en-IN');

    const elStates = document.getElementById('kpi-states-covered');
    if (elStates) elStates.textContent = `${kpis.states_covered} / ${kpis.total_states_target}`;
    
    const statesBadge = document.getElementById('kpi-states-badge');
    if (statesBadge) {
      const pct = Math.round((kpis.states_covered / (kpis.total_states_target || 36)) * 100);
      statesBadge.textContent = `${pct}% Target`;
    }

    const elPending = document.getElementById('kpi-pending-datasets');
    if (elPending) elPending.textContent = kpis.datasets_pending;

    const elReview = document.getElementById('kpi-review-required');
    if (elReview) elReview.textContent = kpis.datasets_requiring_review;

    // Dynamically update Recommended Review Flow description with current dataset count and records
    const flowDesc = document.getElementById('review-flow-desc');
    if (flowDesc) {
      flowDesc.innerHTML = `Begin by reviewing the <strong>Institutes List</strong> (${kpis.final_lists_available} cleaned datasets, ${kpis.total_records_final.toLocaleString('en-IN')} institutions), explore geographic spread in <strong>State/UT Explorer</strong>, and inspect the <strong>Dataset Collection Roadmap</strong>.`;
    }
  }

  /* --------------------------------------------------------------------------
     2. Charts Rendering
     -------------------------------------------------------------------------- */
  renderCharts() {
    if (!this.summaryData) return;
    const breakdowns = this.summaryData.breakdowns;

    // Category Doughnut Chart
    const catCanvas = document.getElementById('categoryChart');
    if (catCanvas && window.Chart) {
      if (this.categoryChart) this.categoryChart.destroy();

      const catLabels = Object.keys(breakdowns.institutions_by_category);
      const catValues = Object.values(breakdowns.institutions_by_category);
      const catColors = catLabels.map(cat => getCategoryColor(cat));

      this.categoryChart = new Chart(catCanvas, {
        type: 'doughnut',
        data: {
          labels: catLabels,
          datasets: [{
            data: catValues,
            backgroundColor: catColors,
            hoverBackgroundColor: catColors,
            borderWidth: 2,
            borderColor: '#0f172a'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false // Dedicated responsive HTML legend
            },
            tooltip: {
              callbacks: {
                label: (context) => ` ${context.label}: ${context.raw.toLocaleString('en-IN')} institutions`
              }
            }
          },
          cutout: '66%'
        }
      });

      // Render custom responsive HTML legend for all 16 categories
      const legendContainer = document.getElementById('categoryChartLegend');
      if (legendContainer) {
        legendContainer.innerHTML = catLabels.map((cat, i) => {
          const color = catColors[i];
          const val = catValues[i] || 0;
          return `
            <div class="cat-legend-item" data-index="${i}" title="${cat}: ${val.toLocaleString('en-IN')} institutions">
              <span class="cat-legend-dot" style="background-color: ${color};"></span>
              <span class="cat-legend-label">${cat}</span>
            </div>
          `;
        }).join('');

        // Interactive slice highlighting and toggle visibility
        legendContainer.querySelectorAll('.cat-legend-item').forEach(item => {
          const idx = parseInt(item.getAttribute('data-index'), 10);
          
          item.addEventListener('click', () => {
            const isVisible = this.categoryChart.getDataVisibility(idx);
            this.categoryChart.toggleDataVisibility(idx);
            this.categoryChart.update();
            item.classList.toggle('hidden', isVisible);
          });

          item.addEventListener('mouseenter', () => {
            if (this.categoryChart && this.categoryChart.getDataVisibility(idx)) {
              this.categoryChart.setActiveElements([{ datasetIndex: 0, index: idx }]);
              this.categoryChart.update();
            }
          });

          item.addEventListener('mouseleave', () => {
            if (this.categoryChart) {
              this.categoryChart.setActiveElements([]);
              this.categoryChart.update();
            }
          });
        });
      }
    }

    // Top 10 States Horizontal Bar Chart
    const statesCanvas = document.getElementById('statesChart');
    if (statesCanvas && window.Chart) {
      if (this.statesChart) this.statesChart.destroy();

      const topStates = breakdowns.top_states || [];
      const sLabels = topStates.map(s => s.state);
      const sValues = topStates.map(s => s.count);

      this.statesChart = new Chart(statesCanvas, {
        type: 'bar',
        data: {
          labels: sLabels,
          datasets: [{
            label: 'Institutions',
            data: sValues,
            backgroundColor: sValues.map((_, i) => [
              'rgba(99,102,241,0.80)',
              'rgba(16,185,129,0.80)',
              'rgba(239,68,68,0.80)',
              'rgba(245,158,11,0.80)',
              'rgba(139,92,246,0.80)',
              'rgba(6,182,212,0.80)',
              'rgba(236,72,153,0.80)',
              'rgba(132,204,22,0.80)',
              'rgba(249,115,22,0.80)',
              'rgba(56,189,248,0.80)',
            ][i % 10]),
            borderColor: sValues.map((_, i) => [
              '#6366f1','#10b981','#ef4444','#f59e0b','#8b5cf6',
              '#06b6d4','#ec4899','#84cc16','#f97316','#38bdf8',
            ][i % 10]),
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${ctx.raw.toLocaleString('en-IN')} institutions`
              }
            }
          },
          scales: {
            x: {
              grid: { color: 'rgba(255, 255, 255, 0.06)' },
              ticks: { color: '#94a3b8', font: { size: 10 } }
            },
            y: {
              grid: { display: false },
              ticks: { color: '#e2e8f0', font: { size: 11 } }
            }
          }
        }
      });
    }
  }

  /* --------------------------------------------------------------------------
     3. Source Datasets Table
     -------------------------------------------------------------------------- */
  renderSourceTable() {
    const tbody = document.getElementById('sources-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    this.sourceDatasets.forEach(d => {
      const tr = document.createElement('tr');
      tr.className = 'clickable-row';
      tr.addEventListener('click', () => this.showSourceDetail(d));

      const statusClass = d.quality_status.toLowerCase();
      const priorityClass = d.review_priority.toLowerCase();

      tr.innerHTML = `
        <td>
          <strong style="color: #fff;">${d.name}</strong><br>
          <span style="font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-muted);">${d.file_name}</span>
        </td>
        <td>${renderCategoryTag(d.category)}</td>
        <td><strong style="color: #fff;">${d.total_records.toLocaleString('en-IN')}</strong></td>
        <td>${d.states_covered} / 36</td>
        <td>${d.districts_covered}</td>
        <td>${d.academic_year}</td>
        <td>${d.source}</td>
        <td>
          <span style="font-size: 0.74rem; font-family: var(--font-mono); color: #93c5fd;">${d.official_id_name}</span>
        </td>
        <td>
          <span class="status-pill ${statusClass}">${d.quality_status}</span>
        </td>
        <td>
          <span class="priority-badge ${priorityClass}">${d.review_priority}</span>
        </td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); window.dashboardApp.showSourceDetail(${JSON.stringify(d).replace(/"/g, '&quot;')})">
            Audit
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  filterSourceTable() {
    const cat = document.getElementById('source-cat-filter')?.value || 'All';
    const q = document.getElementById('source-search-filter')?.value.toLowerCase() || '';

    const rows = document.querySelectorAll('#sources-table-body tr');
    rows.forEach((r, idx) => {
      const d = this.sourceDatasets[idx];
      if (!d) return;
      const matchCat = (cat === 'All' || d.category === cat);
      const matchQ = (d.name.toLowerCase().includes(q) || d.file_name.toLowerCase().includes(q) || d.source.toLowerCase().includes(q));
      r.style.display = (matchCat && matchQ) ? '' : 'none';
    });
  }

  showSourceDetail(dataset) {
    const modal = document.getElementById('detail-modal');
    const body = document.getElementById('detail-modal-body');
    document.getElementById('detail-modal-title').textContent = dataset.name;
    document.getElementById('detail-modal-subtitle').textContent = `Official Source: ${dataset.source}`;

    body.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px;">
        <div class="chart-card">
          <div style="font-size: 0.75rem; color: var(--text-muted);">TOTAL ROWS / RECORDS</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #fff;">${dataset.total_records.toLocaleString('en-IN')}</div>
        </div>
        <div class="chart-card">
          <div style="font-size: 0.75rem; color: var(--text-muted);">GEOGRAPHIC COVERAGE</div>
          <div style="font-size: 1.6rem; font-weight: 800; color: #34d399;">${dataset.states_covered} States, ${dataset.districts_covered} Districts</div>
        </div>
      </div>

      <div class="table-wrapper" style="margin-bottom: 20px;">
        <table class="data-table">
          <tr><td style="width: 200px; font-weight: 600;">Academic Year:</td><td>${dataset.academic_year}</td></tr>
          <tr><td style="font-weight: 600;">Official ID Schema:</td><td><code style="color: #93c5fd;">${dataset.official_id_name}</code></td></tr>
          <tr><td style="font-weight: 600;">File Path on Disk:</td><td><code style="color: var(--text-muted); font-size: 0.75rem;">${dataset.file_path}</code></td></tr>
          <tr><td style="font-weight: 600;">Data Quality Status:</td><td><span class="status-pill ${dataset.quality_status.toLowerCase()}">${dataset.quality_status}</span></td></tr>
          <tr><td style="font-weight: 600;">Review Priority:</td><td><span class="priority-badge ${dataset.review_priority.toLowerCase()}">${dataset.review_priority}</span></td></tr>
          <tr><td style="font-weight: 600;">Key Columns:</td><td>${dataset.important_columns.join(', ')}</td></tr>
        </table>
      </div>

      <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 16px; margin-bottom: 20px;">
        <h4 style="font-family: var(--font-heading); font-size: 0.92rem; color: #f59e0b; margin-bottom: 6px;">Audit Notes & Data Limitations</h4>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.45;">
          ${dataset.missing_important_fields}
        </p>
        <p style="font-size: 0.82rem; color: var(--text-muted); margin-top: 6px;">
          ${dataset.notes}
        </p>
      </div>

      <div style="display: flex; justify-content: flex-end;">
        <button class="btn btn-outline" onclick="window.dashboardApp.closeModal('detail-modal')">Close Audit</button>
      </div>
    `;

    modal.classList.add('open');
  }

  /* Helper: converts quality_status string to a valid CSS class name */
  statusToCssClass(status) {
    if (!status) return 'pass';
    const s = status.toLowerCase();
    if (s.includes('source limitation')) return 'pass_source_limitation';
    if (s.includes('needs review') || s.includes('needs_review')) return 'needs_review';
    if (s.includes('incomplete')) return 'incomplete';
    if (s.includes('warning')) return 'warning';
    return s.replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'pass';
  }

  /* --------------------------------------------------------------------------
     4. Final Institute Lists Table
     -------------------------------------------------------------------------- */
  renderFinalListsTable() {
    const tbody = document.getElementById('final-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    this.finalLists.forEach(l => {
      const tr = document.createElement('tr');
      const statusClass = this.statusToCssClass(l.quality_status);

      tr.innerHTML = `
        <td>${renderCategoryTag(l.category)}</td>
        <td>
          <div class="final-filename">${l.file_name}</div>
          <span class="final-filesize">${l.file_size_kb} KB</span>
        </td>
        <td style="text-align: right;"><strong class="final-inst-count">${l.total_records.toLocaleString('en-IN')}</strong></td>
        <td>${l.states_covered} / 36</td>
        <td style="text-align: right;">${l.districts_covered}</td>
        <td>${l.academic_year}</td>
        <td>
          ${l.has_official_id ? `<span style="font-size: 0.74rem; font-family: var(--font-mono); color: #93c5fd;">${l.id_column}</span>` : `<span style="font-size: 0.74rem; color: var(--text-muted);">Not available</span>`}
        </td>
        <td style="text-align: center;">
          ${l.has_official_id ? (l.duplicate_ids > 0 ? `<span style="color: #ef4444; font-weight: 700;">${l.duplicate_ids}</span>` : `<span style="color: #10b981;">0</span>`) : `<span style="color: var(--text-muted);">N/A</span>`}
        </td>
        <td>
          <span style="font-size: 0.75rem; color: var(--text-secondary);">
            ${l.missing_names > 0 ? `${l.missing_names} names; ` : ''}${l.missing_pin > 0 ? `${l.missing_pin} PINs` : 'Clean'}
          </span>
        </td>
        <td>
          <span class="status-pill ${statusClass}">${l.quality_status}</span>
        </td>
        <td style="text-align: right;">
          <button class="btn btn-primary btn-sm" onclick="window.dashboardApp.openRecordModal('${l.id}')">
            Review List →
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  /* --------------------------------------------------------------------------
     5. Server-side Paginated Final List Record Modal
     -------------------------------------------------------------------------- */
  async openRecordModal(listId) {
    this.modalListId = listId;
    this.modalPage = 1;
    this.modalSearch = '';
    this.modalStateFilter = 'All';

    const listInfo = this.finalLists.find(l => l.id === listId);
    if (!listInfo) return;

    document.getElementById('modal-list-title').textContent = `${listInfo.category} — ${listInfo.file_name}`;
    document.getElementById('modal-list-subtitle').textContent = `Total Cleaned Institutions: ${listInfo.total_records.toLocaleString('en-IN')} | Academic Year: ${listInfo.academic_year}`;

    // Populate State Filter options
    const stateFilter = document.getElementById('modal-state-filter');
    stateFilter.innerHTML = '<option value="All">All States / UTs</option>';
    if (listInfo.state_counts) {
      Object.keys(listInfo.state_counts).sort().forEach(st => {
        stateFilter.innerHTML += `<option value="${st}">${st} (${listInfo.state_counts[st]})</option>`;
      });
    }

    // Reset input
    document.getElementById('modal-search-input').value = '';

    await this.fetchModalRecords();
    document.getElementById('record-modal').classList.add('open');
  }

  async fetchModalRecords() {
    if (!this.modalListId) return;

    const tbody = document.getElementById('modal-records-tbody');
    const thead = document.getElementById('modal-records-thead');
    tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 24px; color: var(--text-muted);">Loading live records from disk...</td></tr>';

    try {
      const url = `/api/final/${this.modalListId}/records?page=${this.modalPage}&page_size=${this.modalPageSize}&state=${encodeURIComponent(this.modalStateFilter)}&search=${encodeURIComponent(this.modalSearch)}`;
      const res = await fetch(url).then(r => r.json());

      this.modalTotalPages = res.total_pages;

      // Render Header
      thead.innerHTML = '';
      const trHead = document.createElement('tr');
      res.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        trHead.appendChild(th);
      });
      thead.appendChild(trHead);

      // Render Body
      tbody.innerHTML = '';
      if (res.records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 32px; color: var(--text-muted);">No matching institutions found for criteria.</td></tr>';
      } else {
        res.records.forEach(rec => {
          const tr = document.createElement('tr');
          res.columns.forEach(col => {
            const td = document.createElement('td');
            const val = rec[col];
            td.textContent = (val !== null && val !== undefined) ? String(val) : '—';
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });
      }

      // Update Pagination Bar
      const startIdx = (this.modalPage - 1) * this.modalPageSize + 1;
      const endIdx = Math.min(this.modalPage * this.modalPageSize, res.total_records);
      document.getElementById('modal-pagination-info').textContent = `Showing records ${res.total_records > 0 ? startIdx : 0} - ${endIdx} of ${res.total_records.toLocaleString('en-IN')}`;
      document.getElementById('modal-page-num').textContent = `Page ${this.modalPage} of ${res.total_pages}`;

      document.getElementById('btn-modal-prev').disabled = (this.modalPage <= 1);
      document.getElementById('btn-modal-next').disabled = (this.modalPage >= res.total_pages);

    } catch (err) {
      console.error('[RecordModal] Error fetching records:', err);
      tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; color: #ef4444; padding: 24px;">Failed to load records.</td></tr>';
    }
  }

  /* --------------------------------------------------------------------------
     6. State / UT Explorer
     -------------------------------------------------------------------------- */
  renderStateExplorer() {
    const listScroll = document.getElementById('state-list-scroll');
    if (!listScroll) return;
    listScroll.innerHTML = '';

    this.statesList.forEach((st, idx) => {
      const item = document.createElement('div');
      item.className = `state-item ${idx === 0 ? 'active' : ''}`;
      item.setAttribute('data-state-name', st.state_name);
      item.innerHTML = `
        <span class="state-item-name">${st.state_name}</span>
        <span class="state-item-count">${st.total_institutions}</span>
      `;

      item.addEventListener('click', () => {
        document.querySelectorAll('.state-item').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
        this.selectState(st.state_name);
      });

      listScroll.appendChild(item);
    });

    if (this.statesList.length > 0) {
      this.selectState(this.statesList[0].state_name);
    }
  }

  async selectState(stateName) {
    this.selectedState = stateName;
    const nameEl = document.getElementById('selected-state-name');
    if (nameEl) nameEl.textContent = stateName;

    try {
      const res = await fetch(`/api/states/${encodeURIComponent(stateName)}`).then(r => r.json());

      const totalInstEl = document.getElementById('selected-state-total');
      if (totalInstEl) totalInstEl.textContent = `${res.total_institutions.toLocaleString('en-IN')} Total Institutions`;
      
      const distCount = Object.keys(res.districts || {}).length;
      const distCountEl = document.getElementById('selected-state-dist-count');
      if (distCountEl) distCountEl.textContent = `${distCount} Districts Populated`;

      // Dynamic calculation of total categories (Y) and represented categories (X)
      // Both are calculated dynamically from dataset registry and never hardcoded
      const allExpected = res.all_categories_expected || [];
      const totalExpected = res.total_categories_count !== undefined ? res.total_categories_count : (allExpected.length || 0);
      const representedCount = res.represented_categories_count !== undefined 
        ? res.represented_categories_count 
        : Object.keys(res.categories || {}).filter(c => res.categories[c] > 0).length;

      // Update Category Badge in state header
      const catBadge = document.getElementById('selected-state-categories');
      if (catBadge) {
        catBadge.textContent = `${representedCount} / ${totalExpected} Categories`;
      }

      // Representation Tag: Display exact required text
      // "✓ X of Y institute categories have representation in this State!"
      const repTag = document.getElementById('state-representation-tag');
      if (repTag) {
        repTag.textContent = `✓ ${representedCount} of ${totalExpected} institute categories have representation in this State!`;
        if (representedCount === totalExpected && totalExpected > 0) {
          repTag.className = 'state-representation-tag all-represented';
        } else {
          repTag.className = 'state-representation-tag has-gaps';
        }
      }

      // Available Categories Chips
      const catChips = document.getElementById('state-category-chips');
      if (catChips) {
        catChips.innerHTML = '';
        const catEntries = Object.entries(res.categories || {}).filter(([_, cnt]) => cnt > 0);
        if (catEntries.length === 0) {
          catChips.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem; grid-column: 1/-1;">No institutions recorded in active categories yet.</span>';
        } else {
          catEntries.forEach(([cat, cnt]) => {
            const chip = document.createElement('div');
            chip.className = 'category-chip';
            const catColor = getCategoryColor(cat);
            chip.style.setProperty('--chip-color', catColor);
            chip.innerHTML = `
              <div class="category-chip-label">
                <span class="category-chip-dot" style="background-color: ${catColor};"></span>
                <span class="category-chip-name">${cat}</span>
              </div>
              <strong class="category-chip-count">${cnt.toLocaleString('en-IN')}</strong>
            `;
            catChips.appendChild(chip);
          });
        }
      }

      // Missing Categories / Gaps
      const missChips = document.getElementById('state-missing-chips');
      const gapsTitle = document.getElementById('state-gaps-title');
      const missingCats = res.missing_categories || [];

      if (missChips) {
        missChips.innerHTML = '';
        if (missingCats.length === 0) {
          if (gapsTitle) {
            gapsTitle.textContent = 'Category Coverage Status:';
            gapsTitle.style.color = '#34d399';
          }
          missChips.innerHTML = `
            <div class="state-rep-success-card">
              <span class="state-rep-check">✓</span>
              <span class="state-rep-desc">✓ ${representedCount} of ${totalExpected} institute categories have representation in this State!</span>
            </div>
          `;
        } else {
          if (gapsTitle) {
            gapsTitle.textContent = `Remaining Sector Gaps in this State (${missingCats.length}):`;
            gapsTitle.style.color = '#f87171';
          }
          missingCats.forEach(mc => {
            const chip = document.createElement('div');
            chip.className = 'category-chip missing-chip';
            chip.innerHTML = `
              <span class="missing-chip-icon">⚠️</span>
              <span class="missing-chip-name">${mc}</span>
            `;
            missChips.appendChild(chip);
          });
        }
      }

      // Top Districts List
      const distList = document.getElementById('state-districts-list');
      distList.innerHTML = '';
      const sortedDists = Object.entries(res.districts).sort((a,b) => b[1] - a[1]);
      if (sortedDists.length === 0) {
        distList.innerHTML = '<span style="color: var(--text-muted); grid-column: 1/-1;">District data unassigned for this state.</span>';
      } else {
        sortedDists.forEach(([dname, dcnt]) => {
          distList.innerHTML += `
            <div style="background: var(--bg-surface); padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; gap: 8px; min-width: 0; word-break: break-word;">
              <span style="color: #fff; min-width: 0; word-break: break-word;">${dname}</span>
              <strong style="color: #93c5fd; flex-shrink: 0;">${dcnt}</strong>
            </div>
          `;
        });
      }

      // Institutions Roster Table
      this.renderStateInstitutions(res.institutions);

    } catch (err) {
      console.error('[StateExplorer] Error fetching state details:', err);
    }
  }

  renderStateInstitutions(institutions) {
    const tbody = document.getElementById('state-institutions-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!institutions || institutions.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">No institutions found.</td></tr>';
      return;
    }

    institutions.forEach(inst => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong style="color: #fff;">${inst.institution_name}</strong></td>
        <td>${renderCategoryTag(inst.category)}</td>
        <td>${inst.district}</td>
        <td><code style="color: #93c5fd; font-size: 0.75rem;">${inst.official_id}</code></td>
        <td><span style="font-size: 0.72rem; color: var(--text-muted);">${inst.dataset_name}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  async filterStateInstitutions(searchTerm) {
    if (!this.selectedState) return;
    const url = `/api/states/${encodeURIComponent(this.selectedState)}?search=${encodeURIComponent(searchTerm)}`;
    const res = await fetch(url).then(r => r.json());
    this.renderStateInstitutions(res.institutions);
  }

  /* --------------------------------------------------------------------------
     7. Data Quality Audit Scorecard
     -------------------------------------------------------------------------- */
  renderQualityScorecard() {
    const tbody = document.getElementById('quality-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    // Final Lists
    this.finalLists.forEach(l => {
      const tr = document.createElement('tr');
      const statusClass = this.statusToCssClass(l.quality_status);
      // Build source limitation tooltip / note text
      const sourceLimitNotes = (l.source_limitation_notes || []).join(' | ');
      const statusLabel = l.quality_status;
      tr.innerHTML = `
        <td>
          <strong style="color: #fff;">${l.category}</strong><br>
          <span style="font-size: 0.72rem; color: var(--text-muted);">${l.file_name}</span>
        </td>
        <td>${l.total_records.toLocaleString('en-IN')}</td>
        <td>${l.unique_records.toLocaleString('en-IN')}</td>
        <td>${l.has_official_id ? (l.duplicate_ids > 0 ? `<span style="color: #ef4444; font-weight:700;">${l.duplicate_ids}</span>` : '0') : '<span style="color: var(--text-muted);">N/A</span>'}</td>
        <td>${l.missing_names > 0 ? `<span style="color: #ef4444;">${l.missing_names}</span>` : '0'}</td>
        <td>${l.missing_state > 0 ? `<span style="color: #f59e0b;">${l.missing_state}</span>` : '0'}</td>
        <td>${l.missing_district > 0 ? `<span style="color: #f59e0b;">${l.missing_district}</span>` : '0'}</td>
        <td>${l.missing_address > 0 ? l.missing_address : '0'}</td>
        <td>${l.missing_pin > 0 ? l.missing_pin : '0'}</td>
        <td>
          <span class="status-pill ${statusClass}" title="${sourceLimitNotes}">${statusLabel}</span>
          ${sourceLimitNotes ? `<div style="font-size:0.68rem;color:var(--text-muted);margin-top:3px;line-height:1.3;">ℹ️ Source limitation</div>` : ''}
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  /* --------------------------------------------------------------------------
     8. Review Priority Queue
     -------------------------------------------------------------------------- */
  renderReviewPriority() {
    const highCont = document.getElementById('priority-high-container');
    const medSection = document.querySelector('#view-priority > div > div:nth-child(2)');
    const medCont = document.getElementById('priority-medium-container');
    const lowCont = document.getElementById('priority-low-container');

    if (!highCont || !medCont || !lowCont) return;

    highCont.innerHTML = '';
    medCont.innerHTML = '';
    lowCont.innerHTML = '';

    const data = this.reviewPriorityData;
    if (!data) {
      highCont.innerHTML = '<p style="color: var(--text-muted); padding: 20px;">Loading priority data...</p>';
      return;
    }

    const renderCard = (item) => {
      const card = document.createElement('div');
      card.className = 'chart-card';
      card.style.display = 'flex';
      card.style.flexDirection = 'column';
      card.style.justifyContent = 'space-between';

      const priority = item.priority || 'LOW';
      const isExcluded = item.data_type === 'EXCLUDED_LARGE_DATASET';
      const isFinal = item.isFinal;

      let actionBtn = '';
      if (isExcluded) {
        // UDISE+ — no modal, just informational
        actionBtn = `<span style="font-size: 0.75rem; color: #f87171; font-style: italic;">⚠️ Records excluded from browser memory (1.47M scale)</span>`;
      } else if (isFinal) {
        actionBtn = `<button class="btn btn-outline btn-sm" onclick="window.dashboardApp.openRecordModal('${item.id}')">Review Cleaned Roster →</button>`;
      } else {
        actionBtn = `<button class="btn btn-outline btn-sm" onclick="window.dashboardApp.switchView('quality')">View Quality Scorecard →</button>`;
      }

      // Build notes / reason text
      let noteText = '';
      if (item.reason) {
        noteText = item.reason;
      } else if (item.notes && item.notes.length > 0) {
        noteText = item.notes.join(' ');
      } else if (item.issues && item.issues.length > 0) {
        noteText = item.issues.join(', ');
      } else {
        noteText = item.quality_status === 'PASS' ? 'Validated registry.' : (item.quality_status || 'Reviewed.');
      }

      const recordLabel = isExcluded ? 'Total Records (National Census):' : 'Total Institutions / Records:';
      const typeLabel = isExcluded ? 'EXCLUDED — LARGE DATASET' : (isFinal ? 'INSTITUTES LIST' : 'SOURCE');
      const acYear = item.academic_year || '';

      card.innerHTML = `
        <div>
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span class="priority-badge ${priority.toLowerCase()}">${priority} PRIORITY</span>
            <span style="font-size: 0.72rem; color: var(--text-muted);">${typeLabel}</span>
          </div>
          <h4 style="font-family: var(--font-heading); font-size: 1.05rem; color: #fff; margin-bottom: 4px;">${item.name}</h4>
          ${acYear ? `<div style="font-size: 0.75rem; color: #a5b4fc; margin-bottom: 6px;">Academic Year: ${acYear}</div>` : ''}
          <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 8px;">
            ${recordLabel} <strong style="color: #fff;">${(item.total_records || 0).toLocaleString('en-IN')}</strong>
          </div>
          ${item.action_required ? `<div style="font-size: 0.78rem; color: #f59e0b; background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); border-radius: 4px; padding: 6px 10px; margin-bottom: 10px;"><strong>Action Required:</strong> ${item.action_required}</div>` : ''}
          <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 16px;">${noteText}</p>
        </div>
        <div style="display: flex; justify-content: flex-end;">
          ${actionBtn}
        </div>
      `;
      return card;
    };

    // Render HIGH
    (data.high || []).forEach(item => highCont.appendChild(renderCard(item)));
    if ((data.high || []).length === 0) {
      highCont.innerHTML = '<p style="color: var(--text-muted); padding: 16px; font-size: 0.85rem;">No high priority items at this time.</p>';
    }

    // Render MEDIUM — hide section entirely if empty
    const medParent = medCont ? medCont.parentElement : null;
    if ((data.medium || []).length === 0) {
      if (medParent) medParent.style.display = 'none';
    } else {
      if (medParent) medParent.style.display = '';
      data.medium.forEach(item => medCont.appendChild(renderCard(item)));
    }

    // Render LOW
    (data.low || []).forEach(item => lowCont.appendChild(renderCard(item)));
    if ((data.low || []).length === 0) {
      lowCont.innerHTML = '<p style="color: var(--text-muted); padding: 16px; font-size: 0.85rem;">No low priority items.</p>';
    }
  }

  /* --------------------------------------------------------------------------
     9. Pending Regulatory Datasets
     -------------------------------------------------------------------------- */
  renderPendingDatasets() {
    const grid = document.getElementById('pending-grid');

    // Render Strict Pending Queue (only genuinely pending portals)
    if (grid) {
      grid.innerHTML = '';
      if (!this.pendingDatasets || this.pendingDatasets.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 32px; color: var(--text-muted); background: var(--bg-surface); border-radius: var(--radius-md); border: 1px solid var(--border-color);">All recognized regulatory councils have been completed and integrated!</div>';
      } else {
        this.pendingDatasets.forEach(p => {
          const card = document.createElement('div');
          card.className = 'pending-card';

          let statusBadge = 'warning';
          if (p.status === 'NOT STARTED') statusBadge = 'danger';
          else if (p.status === 'IN PROGRESS') statusBadge = 'warning';

          card.innerHTML = `
            <div class="pending-card-top">
              <div class="pending-authority">${p.authority}</div>
              <h3 class="pending-title">${p.sector}</h3>
              <div class="pending-status-row">
                <span class="status-pill ${statusBadge}">${p.status}</span>
                <span style="font-size: 0.75rem; color: var(--text-muted);">${p.estimated_institutions || 'Count not established'}</span>
              </div>
              <div class="pending-notes">${p.notes}</div>
              <div class="pending-action-plan"><strong>Action Plan:</strong> ${p.action_plan}</div>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid var(--border-color); padding-top: 12px; margin-top: 12px;">
              <span style="font-size: 0.75rem; color: var(--text-muted);">Harvested: ${p.collected_count > 0 ? p.collected_count : 0}</span>
              <button class="btn btn-outline btn-sm" onclick="window.dashboardApp.openPendingEditModal('${p.id}')">
                Update Status
              </button>
            </div>
          `;
          grid.appendChild(card);
        });
      }
    }
  }

  viewFinalList(fileId) {
    this.switchView('final-lists');
    this.openRecordModal(fileId);
  }

  openPendingEditModal(pendingId) {
    const item = this.pendingDatasets.find(p => p.id === pendingId);
    if (!item) return;

    document.getElementById('pending-edit-id').value = item.id;
    document.getElementById('pending-edit-sector').textContent = `${item.sector} (${item.authority})`;
    document.getElementById('pending-edit-status').value = item.status;
    document.getElementById('pending-edit-notes').value = item.notes;

    document.getElementById('pending-modal').classList.add('open');
  }

  async savePendingStatusUpdate() {
    const id = document.getElementById('pending-edit-id').value;
    const status = document.getElementById('pending-edit-status').value;
    const notes = document.getElementById('pending-edit-notes').value;

    try {
      const res = await fetch('/api/pending/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, status, notes })
      }).then(r => r.json());

      if (res.success) {
        // Update local state
        const item = this.pendingDatasets.find(p => p.id === id);
        if (item) {
          item.status = status;
          item.notes = notes;
        }
        this.renderPendingDatasets();
        this.closeModal('pending-modal');
      }
    } catch (err) {
      console.error('[Pending] Error updating status:', err);
    }
  }

  /* --------------------------------------------------------------------------
     10. Global Search
     -------------------------------------------------------------------------- */
  async executeGlobalSearch(term) {
    const tbody = document.getElementById('search-table-body');
    const counter = document.getElementById('search-results-count');
    if (!tbody || !counter) return;

    if (!term || term.length < 2) {
      counter.textContent = 'Type at least 2 characters';
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 32px;">Enter a search term above.</td></tr>';
      return;
    }

    counter.textContent = 'Searching...';

    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(term)}&limit=50`).then(r => r.json());

      counter.textContent = `Found ${res.total_matches} institutions matching "${term}"`;
      tbody.innerHTML = '';

      if (res.results.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 32px;">No institutions found matching search criteria.</td></tr>';
        return;
      }

      res.results.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${renderCategoryTag(r.category)}</td>
          <td>
            <strong style="color: #fff;">${r.institution}</strong>
            ${r.address ? `<div style="font-size: 0.74rem; color: var(--text-muted); margin-top: 3px; line-height: 1.3;">📍 ${r.address}</div>` : ''}
            ${r.university ? `<div style="font-size: 0.72rem; color: #93c5fd; margin-top: 2px;">🏛️ ${r.university}</div>` : ''}
          </td>
          <td>${r.state}</td>
          <td>${r.district || 'Not Specified'}</td>
          <td><code style="color: #93c5fd; font-size: 0.75rem;">${r.official_id}</code></td>
          <td>${r.pincode || '—'}</td>
        `;
        tbody.appendChild(tr);
      });

    } catch (err) {
      console.error('[Search] Error executing search:', err);
      counter.textContent = 'Search error';
    }
  }

  /* --------------------------------------------------------------------------
     10. Data Dictionary Rendering & Filtering
     -------------------------------------------------------------------------- */
  renderDataDictionary() {
    if (!this.dictionaryData) return;
    const records = this.dictionaryData.records || [];
    const datasets = this.dictionaryData.available_datasets || [];
    const totalFields = this.dictionaryData.total_fields || records.length;

    // Populate dataset dropdown
    const select = document.getElementById('dict-dataset-filter');
    if (select) {
      // Always update the "All Datasets" option with the live total
      select.options[0].textContent = `All Datasets (${totalFields} Fields)`;
      if (select.options.length <= 1) {
        datasets.forEach(ds => {
          const opt = document.createElement('option');
          opt.value = ds;
          const count = records.filter(r => r.dataset === ds).length;
          opt.textContent = `${ds} (${count})`;
          select.appendChild(opt);
        });
      }
    }

    // Populate KPI counts
    const totalCount = records.length;
    const sourceCount = records.filter(r => r.field_classification === 'SOURCE FIELD').length;
    const derivedCount = records.filter(r => r.field_classification === 'DERIVED FIELD').length;
    const calcCount = records.filter(r => r.field_classification === 'DASHBOARD-CALCULATED FIELD').length;

    const elTotal = document.getElementById('dict-kpi-total');
    if (elTotal) elTotal.textContent = totalCount;
    const elSource = document.getElementById('dict-kpi-source');
    if (elSource) elSource.textContent = sourceCount;
    const elDerived = document.getElementById('dict-kpi-derived');
    if (elDerived) elDerived.textContent = derivedCount;
    const elCalc = document.getElementById('dict-kpi-calculated');
    if (elCalc) elCalc.textContent = calcCount;

    this.filterDataDictionary();
  }

  filterDataDictionary() {
    if (!this.dictionaryData) return;
    const all = this.dictionaryData.records || [];

    const searchVal = (document.getElementById('dict-search-input')?.value || '').trim().toLowerCase();
    const datasetVal = document.getElementById('dict-dataset-filter')?.value || 'All';
    const classVal = document.getElementById('dict-class-filter')?.value || 'All';

    let filtered = all;

    if (datasetVal !== 'All') {
      filtered = filtered.filter(r => r.dataset === datasetVal);
    }

    if (classVal !== 'All') {
      filtered = filtered.filter(r => r.field_classification === classVal);
    }

    if (searchVal) {
      filtered = filtered.filter(r =>
        (r.field_name && r.field_name.toLowerCase().includes(searchVal)) ||
        (r.description && r.description.toLowerCase().includes(searchVal)) ||
        (r.dataset && r.dataset.toLowerCase().includes(searchVal)) ||
        (r.allowed_values && r.allowed_values.toLowerCase().includes(searchVal)) ||
        (r.notes && r.notes.toLowerCase().includes(searchVal)) ||
        (r.example_value && r.example_value.toLowerCase().includes(searchVal))
      );
    }

    // Update results counter
    const counter = document.getElementById('dict-results-count');
    if (counter) {
      counter.textContent = `Showing ${filtered.length} of ${all.length} documented fields`;
    }

    const tbody = document.getElementById('dictionary-table-body');
    if (!tbody) return;

    if (filtered.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted); padding: 32px;">No fields match the specified filters.</td></tr>';
      return;
    }

    tbody.innerHTML = filtered.map(r => {
      let badgeClass = 'badge-source';
      if (r.field_classification === 'DERIVED FIELD') badgeClass = 'badge-derived';
      else if (r.field_classification === 'DASHBOARD-CALCULATED FIELD') badgeClass = 'badge-calculated';

      return `
        <tr>
          <td>
            <strong style="color: #cbd5e1; font-size: 0.82rem;">${r.dataset}</strong>
            <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">AY: ${r.academic_year}</div>
          </td>
          <td><span class="dict-field-name">${r.field_name}</span></td>
          <td><span class="badge-classification ${badgeClass}">${r.field_classification.replace(' FIELD', '')}</span></td>
          <td><span class="dict-data-type">${r.data_type}</span></td>
          <td><span style="font-size: 0.78rem; font-weight: 600; color: ${r.is_required && r.is_required.startsWith('Yes') ? '#34d399' : '#94a3b8'};">${r.is_required}</span></td>
          <td style="line-height: 1.45; font-size: 0.82rem; color: #f1f5f9;">${r.description}</td>
          <td style="font-size: 0.78rem; color: #94a3b8; line-height: 1.4;"><code style="color: #38bdf8; font-size: 0.75rem; word-break: break-word;">${r.allowed_values}</code></td>
          <td><span class="dict-example">${r.example_value}</span></td>
          <td style="font-size: 0.78rem; color: var(--text-muted); line-height: 1.4;">${r.notes}</td>
        </tr>
      `;
    }).join('');
  }

  closeModal(modalId) {
    document.getElementById(modalId)?.classList.remove('open');
  }
}

// Instantiate and initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.dashboardApp = new DashboardApp();
  window.dashboardApp.init();
});
