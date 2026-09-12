/**
 * Pan-India Educational Institutions — Executive Review Dashboard Controller
 * Handles live data binding, Chart.js visualizations, server-side pagination,
 * state explorer drill-downs, and global search indexing.
 */

class DashboardApp {
  constructor() {
    this.summaryData = null;
    this.sourceDatasets = [];
    this.finalLists = [];
    this.statesList = [];
    this.pendingDatasets = [];
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
    document.getElementById('btn-refresh')?.addEventListener('click', () => this.loadAllData());

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

    // Source Table Filter
    document.getElementById('source-cat-filter')?.addEventListener('change', () => this.filterSourceTable());
    document.getElementById('source-search-filter')?.addEventListener('input', () => this.filterSourceTable());

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

  async loadAllData() {
    try {
      const [summaryRes, sourcesRes, finalRes, statesRes, pendingRes, dictRes] = await Promise.all([
        fetch('/api/summary').then(r => r.json()),
        fetch('/api/datasets/sources').then(r => r.json()),
        fetch('/api/datasets/final').then(r => r.json()),
        fetch('/api/states').then(r => r.json()),
        fetch('/api/pending').then(r => r.json()),
        fetch('/api/dictionary?page=1&page_size=500').then(r => r.json()).catch(() => null)
      ]);

      this.summaryData = summaryRes;
      this.sourceDatasets = sourcesRes.datasets;
      this.finalLists = finalRes.lists;
      this.statesList = statesRes.states;
      this.pendingDatasets = pendingRes.pending;
      this.dictionaryData = dictRes;

      this.renderKPIs();
      this.renderCharts();
      this.renderSourceTable();
      this.renderFinalListsTable();
      this.renderDataDictionary();
      this.renderStateExplorer();
      this.renderQualityScorecard();
      this.renderReviewPriority();
      this.renderPendingDatasets();

      // Update badges
      document.getElementById('badge-source-count').textContent = this.sourceDatasets.length;
      document.getElementById('badge-final-count').textContent = this.finalLists.length;
      document.getElementById('badge-pending-count').textContent = this.pendingDatasets.length;
      if (this.dictionaryData && this.dictionaryData.total_fields) {
        const dictBadge = document.getElementById('badge-dictionary-count');
        if (dictBadge) dictBadge.textContent = this.dictionaryData.total_fields;
      }

    } catch (err) {
      console.error('[DashboardApp] Error loading data:', err);
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
      sources: { title: 'Source Datasets Directory', meta: 'Raw & Official Statutory Registers' },
      final: { title: 'Final Institute Lists', meta: 'Deduplicated Higher Education Institution Roster' },
      dictionary: { title: 'Data Dictionary & Schema Specification', meta: 'Official regulatory lineage, field definitions, data types, and allowed values' },
      states: { title: 'State / UT Geographic Explorer', meta: 'Pan-India Sub-National Analysis across 36 States & UTs' },
      quality: { title: 'Data Quality & Integrity Audit', meta: 'Null Value, Duplication & Completeness Scorecard' },
      priority: { title: 'Review Priority Queue', meta: 'Ranked Datasets Requiring Strategic Attention' },
      pending: { title: 'Pending Datasets Roadmap', meta: 'Collection Tracker for Remaining Regulatory Portals' },
      search: { title: 'Global Institution Search', meta: 'Multi-attribute Query across All Final Lists' }
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

    document.getElementById('kpi-datasets-collected').textContent = kpis.datasets_collected;
    document.getElementById('kpi-final-lists').textContent = kpis.final_lists_available;
    document.getElementById('kpi-source-records').textContent = kpis.total_records_source.toLocaleString('en-IN');
    document.getElementById('kpi-final-records').textContent = kpis.total_records_final.toLocaleString('en-IN');
    document.getElementById('kpi-states-covered').textContent = `${kpis.states_covered} / ${kpis.total_states_target}`;
    
    const statesBadge = document.getElementById('kpi-states-badge');
    if (statesBadge) {
      const pct = Math.round((kpis.states_covered / (kpis.total_states_target || 36)) * 100);
      statesBadge.textContent = `${pct}% Target`;
    }

    document.getElementById('kpi-pending-datasets').textContent = kpis.datasets_pending;
    document.getElementById('kpi-review-required').textContent = kpis.datasets_requiring_review;
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

      this.categoryChart = new Chart(catCanvas, {
        type: 'doughnut',
        data: {
          labels: catLabels,
          datasets: [{
            data: catValues,
            backgroundColor: [
              '#3b82f6', // Medical
              '#10b981', // Nursing
              '#8b5cf6', // Universities
              '#f59e0b', // Rehabilitation
              '#ec4899', // Architecture
              '#06b6d4'  // Ayurveda
            ],
            borderWidth: 2,
            borderColor: '#111827'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: {
                color: '#cbd5e1',
                boxWidth: 12,
                font: { size: 11, family: 'Inter' }
              }
            },
            tooltip: {
              callbacks: {
                label: (context) => ` ${context.label}: ${context.raw.toLocaleString('en-IN')} institutions`
              }
            }
          },
          cutout: '68%'
        }
      });
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
            backgroundColor: 'rgba(99, 102, 241, 0.75)',
            borderColor: '#6366f1',
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
        <td><span class="category-tag">${d.category}</span></td>
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

  /* --------------------------------------------------------------------------
     4. Final Institute Lists Table
     -------------------------------------------------------------------------- */
  renderFinalListsTable() {
    const tbody = document.getElementById('final-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    this.finalLists.forEach(l => {
      const tr = document.createElement('tr');
      const statusClass = l.quality_status.toLowerCase();

      tr.innerHTML = `
        <td><span class="category-tag">${l.category}</span></td>
        <td>
          <strong style="color: #fff;">${l.file_name}</strong><br>
          <span style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">${l.file_size_kb} KB</span>
        </td>
        <td><strong style="color: #10b981; font-size: 0.95rem;">${l.total_records.toLocaleString('en-IN')}</strong></td>
        <td>${l.states_covered} / 36</td>
        <td>${l.districts_covered}</td>
        <td>${l.academic_year}</td>
        <td>
          ${l.has_official_id ? `<span style="font-size: 0.74rem; font-family: var(--font-mono); color: #93c5fd;">${l.id_column}</span>` : `<span style="font-size: 0.74rem; color: var(--text-muted);">Not available</span>`}
        </td>
        <td>
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
        <td>
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
        <span>${st.state_name}</span>
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
    document.getElementById('selected-state-name').textContent = stateName;

    try {
      const res = await fetch(`/api/states/${encodeURIComponent(stateName)}`).then(r => r.json());

      document.getElementById('selected-state-total').textContent = `${res.total_institutions.toLocaleString('en-IN')} Total Institutions`;
      const distCount = Object.keys(res.districts).length;
      document.getElementById('selected-state-dist-count').textContent = `${distCount} Districts Populated`;

      // Available Categories Chips
      const catChips = document.getElementById('state-category-chips');
      catChips.innerHTML = '';
      if (Object.keys(res.categories).length === 0) {
        catChips.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;">No final institutions recorded yet.</span>';
      } else {
        Object.entries(res.categories).forEach(([cat, cnt]) => {
          catChips.innerHTML += `
            <div class="category-chip">
              <span>${cat}:</span>
              <strong>${cnt}</strong>
            </div>
          `;
        });
      }

      // Missing Categories Chips
      const missChips = document.getElementById('state-missing-chips');
      missChips.innerHTML = '';
      if (res.missing_categories.length === 0) {
        missChips.innerHTML = '<span style="color: #34d399; font-size: 0.8rem;">✓ All 6 major regulated sectors have representation in this State!</span>';
      } else {
        res.missing_categories.forEach(mc => {
          missChips.innerHTML += `
            <div class="category-chip missing-chip">
              <span>⚠️ ${mc}</span>
            </div>
          `;
        });
      }

      // Top Districts List
      const distList = document.getElementById('state-districts-list');
      distList.innerHTML = '';
      const sortedDists = Object.entries(res.districts).sort((a,b) => b[1] - a[1]);
      if (sortedDists.length === 0) {
        distList.innerHTML = '<span style="color: var(--text-muted);">District data unassigned for this state.</span>';
      } else {
        sortedDists.forEach(([dname, dcnt]) => {
          distList.innerHTML += `
            <div style="background: var(--bg-surface); padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); display: flex; justify-content: space-between;">
              <span style="color: #fff;">${dname}</span>
              <strong style="color: #93c5fd;">${dcnt}</strong>
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
        <td><span class="category-tag">${inst.category}</span></td>
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
        <td><span class="status-pill ${l.quality_status.toLowerCase()}">${l.quality_status}</span></td>
      `;
      tbody.appendChild(tr);
    });

    // Key Source Datasets
    this.sourceDatasets.forEach(d => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <strong style="color: #93c5fd;">[Source] ${d.name}</strong><br>
          <span style="font-size: 0.72rem; color: var(--text-muted);">${d.file_name}</span>
        </td>
        <td>${d.total_records.toLocaleString('en-IN')}</td>
        <td>${d.unique_records.toLocaleString('en-IN')}</td>
        <td>${d.has_official_id ? d.duplicate_ids : '<span style="color: var(--text-muted);">N/A</span>'}</td>
        <td>${d.id === 'udise_plus_schools' ? '<span style="color: #ef4444; font-weight: 700;">Withheld in DSP</span>' : '0'}</td>
        <td>0</td>
        <td>0</td>
        <td>0</td>
        <td>${d.id === 'udise_plus_schools' ? '38' : '0'}</td>
        <td><span class="status-pill ${d.quality_status.toLowerCase()}">${d.quality_status}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  /* --------------------------------------------------------------------------
     8. Review Priority Queue
     -------------------------------------------------------------------------- */
  renderReviewPriority() {
    const highCont = document.getElementById('priority-high-container');
    const medCont = document.getElementById('priority-medium-container');
    const lowCont = document.getElementById('priority-low-container');

    if (!highCont || !medCont || !lowCont) return;

    highCont.innerHTML = '';
    medCont.innerHTML = '';
    lowCont.innerHTML = '';

    const allItems = [
      ...this.sourceDatasets.map(d => ({ ...d, isFinal: false })),
      ...this.finalLists.map(l => ({ ...l, name: `${l.category} (${l.file_name})`, isFinal: true }))
    ];

    allItems.forEach(item => {
      const priority = item.review_priority;
      const card = document.createElement('div');
      card.className = 'chart-card';
      card.style.display = 'flex';
      card.style.flexDirection = 'column';
      card.style.justifyContent = 'space-between';

      const buttonAction = item.isFinal
        ? `onclick="window.dashboardApp.openRecordModal('${item.id}')"`
        : `onclick="window.dashboardApp.showSourceDetail(${JSON.stringify(item).replace(/"/g, '&quot;')})"`;

      card.innerHTML = `
        <div>
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
            <span class="priority-badge ${priority.toLowerCase()}">${priority} PRIORITY</span>
            <span style="font-size: 0.72rem; color: var(--text-muted);">${item.isFinal ? 'FINAL LIST' : 'SOURCE'}</span>
          </div>
          <h4 style="font-family: var(--font-heading); font-size: 1.05rem; color: #fff; margin-bottom: 6px;">${item.name}</h4>
          <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px;">
            Total Institutions / Records: <strong style="color: #fff;">${item.total_records.toLocaleString('en-IN')}</strong>
          </div>
          <p style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 16px;">
            ${item.notes || (item.issues ? item.issues.join(', ') : 'Validated registry.')}
          </p>
        </div>
        <div style="display: flex; justify-content: flex-end;">
          <button class="btn btn-outline btn-sm" ${buttonAction}>
            ${item.isFinal ? 'Review Cleaned Roster →' : 'Inspect Audit →'}
          </button>
        </div>
      `;

      if (priority === 'HIGH') highCont.appendChild(card);
      else if (priority === 'MEDIUM') medCont.appendChild(card);
      else lowCont.appendChild(card);
    });
  }

  /* --------------------------------------------------------------------------
     9. Pending Regulatory Datasets
     -------------------------------------------------------------------------- */
  renderPendingDatasets() {
    const grid = document.getElementById('pending-grid');
    if (!grid) return;
    grid.innerHTML = '';

    this.pendingDatasets.forEach(p => {
      const card = document.createElement('div');
      card.className = 'pending-card';

      let statusBadge = 'warning';
      if (p.status === 'VALIDATED' || p.status === 'COLLECTED') statusBadge = 'success';
      else if (p.status === 'NOT STARTED') statusBadge = 'danger';

      card.innerHTML = `
        <div class="pending-card-top">
          <div class="pending-authority">${p.authority}</div>
          <h3 class="pending-title">${p.sector}</h3>
          <div class="pending-status-row">
            <span class="status-pill ${statusBadge}">${p.status}</span>
            <span style="font-size: 0.75rem; color: var(--text-muted);">${p.estimated_institutions}</span>
          </div>
          <div class="pending-notes">${p.notes}</div>
          <div class="pending-action-plan"><strong>Action Plan:</strong> ${p.action_plan}</div>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid var(--border-color); padding-top: 12px; margin-top: 12px;">
          <span style="font-size: 0.75rem; color: var(--text-muted);">Harvested: ${p.collected_count}</span>
          <button class="btn btn-outline btn-sm" onclick="window.dashboardApp.openPendingEditModal('${p.id}')">
            Update Status
          </button>
        </div>
      `;
      grid.appendChild(card);
    });
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
          <td><span class="category-tag">${r.category}</span></td>
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

    // Populate dataset dropdown
    const select = document.getElementById('dict-dataset-filter');
    if (select && select.options.length <= 1) {
      datasets.forEach(ds => {
        const opt = document.createElement('option');
        opt.value = ds;
        const count = records.filter(r => r.dataset === ds).length;
        opt.textContent = `${ds} (${count})`;
        select.appendChild(opt);
      });
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
