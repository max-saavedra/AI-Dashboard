<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dashboard__header">
      <div class="header__left">
        <div class="header__meta">
          <h1 class="header__title">{{ store.result?.dataset_summary?.split('.')[0] || 'Dashboard' }}</h1>
          <div class="header__tags">
            <span v-for="tag in store.userContext.tags" :key="tag" class="tag-badge">{{ tag }}</span>
            <span v-if="store.userContext.role" class="role-badge">{{ store.userContext.role }}</span>
          </div>
        </div>
        <div class="header__stats">
          <div class="stat-chip">
            <span class="stat-chip__val mono">{{ store.result?.row_count?.toLocaleString() }}</span>
            <span class="stat-chip__label">rows</span>
          </div>
          <div class="stat-chip">
            <span class="stat-chip__val mono">{{ store.result?.columns?.length }}</span>
            <span class="stat-chip__label">columns</span>
          </div>
          <div class="stat-chip">
            <span class="stat-chip__val mono">{{ store.result?.chart_configs?.length }}</span>
            <span class="stat-chip__label">charts</span>
          </div>
        </div>
      </div>

      <div class="header__right">
        <button class="btn btn--ghost btn--sm" @click="showChartPicker = true">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM14 11a1 1 0 011 1v1h1a1 1 0 110 2h-1v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-1a1 1 0 011-1z"/></svg>
          Charts
        </button>
        <button class="btn btn--ghost btn--sm" @click="showFilters = !showFilters">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path fill-rule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.553.894l-4 2A1 1 0 016 17v-5.586L3.293 6.707A1 1 0 013 6V3z"/></svg>
          Filters
          <span v-if="filterCount" class="filter-badge">{{ filterCount }}</span>
        </button>
        <button class="btn btn--primary btn--sm" @click="showSummaryPanel = true">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/></svg>
          Summary
        </button>
        <button class="btn btn--ghost btn--sm" @click="store.resetToIdle()">
          + New
        </button>
      </div>
    </div>

    <!-- Filters bar -->
    <Transition name="slide-down">
      <div v-if="showFilters" class="filters-bar">
        <div v-for="col in store.result?.filter_columns" :key="col" class="filter-group">
          <label class="filter-label">{{ humanize(col) }}</label>
          <select class="filter-select" @change="e => store.setFilter(col, e.target.value)">
            <option value="">All</option>
            <option v-for="val in getUniqueValues(col)" :key="val" :value="val">{{ val }}</option>
          </select>
        </div>
        <button v-if="filterCount" class="clear-filters" @click="clearFilters">Clear all</button>
      </div>
    </Transition>

    <!-- KPI cards -->
    <div class="dashboard__kpis">
      <div v-for="(stats, col) in visibleKpis" :key="col" class="kpi-card">
        <span class="kpi-card__label">{{ humanize(col) }}</span>
        <span class="kpi-card__value mono">{{ formatNum(stats.sum) }}</span>
        <div class="kpi-card__meta">
          <span>avg {{ formatNum(stats.mean) }}</span>
          <span class="kpi-card__trend" :class="trendClass(col)">
            {{ trendArrow(col) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Charts grid -->
    <div class="dashboard__charts">
      <TransitionGroup name="chart-appear">
        <ChartCard
          v-for="chart in store.currentCharts"
          :key="chart.id"
          :config="chart"
          :filtered-data="getFilteredData(chart)"
        />
      </TransitionGroup>

      <div v-if="!store.currentCharts.length" class="charts-empty">
        <p>No charts selected. Click <strong>Charts</strong> to add some.</p>
      </div>
    </div>

    <!-- Chat panel (always visible at bottom) -->
    <DataChat />

    <!-- Chart picker modal -->
    <Teleport to="body">
      <div v-if="showChartPicker" class="modal-backdrop" @click="showChartPicker = false">
        <div class="modal chart-picker" @click.stop>
          <div class="modal__head">
            <h3>Available Charts</h3>
            <button class="icon-btn" @click="showChartPicker = false">✕</button>
          </div>
          <div class="chart-picker__grid">
            <label
              v-for="chart in store.result?.chart_configs"
              :key="chart.id"
              class="chart-picker__item"
              :class="{ 'chart-picker__item--on': store.visibleCharts.includes(chart.id) }"
            >
              <input type="checkbox"
                :checked="store.visibleCharts.includes(chart.id)"
                @change="store.toggleChart(chart.id)"
              />
              <div class="chart-picker__info">
                <span class="chart-picker__type mono">{{ chart.chart_type }}</span>
                <span class="chart-picker__title">{{ chart.title }}</span>
                <span class="chart-picker__desc">{{ chart.description }}</span>
              </div>
              <div class="chart-picker__check">{{ store.visibleCharts.includes(chart.id) ? '✓' : '' }}</div>
            </label>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Summary modal -->
    <Teleport to="body">
      <SummaryModal v-if="showSummaryPanel" @close="showSummaryPanel = false" />
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import ChartCard from './ChartCard.vue'
import DataChat from './DataChat.vue'
import SummaryModal from './SummaryModal.vue'

const store = useWorkspaceStore()

const showFilters     = ref(false)
const showChartPicker = ref(false)
const showSummaryPanel = ref(false)

const filterCount = computed(() => Object.keys(store.activeFilters).length)

const visibleKpis = computed(() => {
  const kpis = store.result?.kpis?.kpis || {}
  // Show up to 4 KPI cards
  return Object.fromEntries(Object.entries(kpis).slice(0, 4))
})

function humanize(snake) {
  return snake.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatNum(v) {
  if (v === undefined || v === null) return '—'
  const n = parseFloat(v)
  if (isNaN(n)) return '—'
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (Math.abs(n) >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return n % 1 === 0 ? n.toLocaleString() : n.toFixed(2)
}

function getUniqueValues(col) {
  const records = store.result?.kpis?.breakdowns
    ?.find(b => b.dimension === col)
    ?.data.map(d => d.label) || []
  return [...new Set(records)].slice(0, 30)
}

function clearFilters() {
  store.activeFilters = {}
}

function trendClass(col) {
  const trends = store.result?.kpis?.trends || []
  const t = trends.find(tr => tr.measure === col)
  if (!t) return ''
  return t.trend_direction === 'increasing' ? 'trend--up'
       : t.trend_direction === 'decreasing' ? 'trend--down' : ''
}

function trendArrow(col) {
  const trends = store.result?.kpis?.trends || []
  const t = trends.find(tr => tr.measure === col)
  if (!t) return ''
  return t.trend_direction === 'increasing' ? '↑'
       : t.trend_direction === 'decreasing' ? '↓' : '→'
}

function getFilteredData(chart) {
  // Pass active filters to chart for client-side filtering
  return store.activeFilters
}
</script>

<style scoped>
.dashboard {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  gap: 0;
}

/* Header */
.dashboard__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--col-border);
  gap: 16px;
  flex-wrap: wrap;
  background: var(--col-surface);
  position: sticky;
  top: 0;
  z-index: 20;
}
.header__left  { display: flex; flex-direction: column; gap: 8px; flex: 1; min-width: 0; }
.header__meta  { display: flex; flex-direction: column; gap: 4px; }
.header__title { font-size: 1.1rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.header__tags  { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-badge, .role-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-family: var(--font-mono);
}
.tag-badge  { background: rgba(37,99,235,0.15); color: var(--col-blue-400); border: 1px solid rgba(37,99,235,0.25); }
.role-badge { background: var(--col-elevated); color: var(--col-text-dim); border: 1px solid var(--col-border); }
.header__stats { display: flex; gap: 12px; }
.stat-chip { display: flex; flex-direction: column; gap: 1px; }
.stat-chip__val   { font-size: 0.9rem; color: var(--col-text-primary); }
.stat-chip__label { font-size: 0.65rem; color: var(--col-text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
.header__right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.filter-badge { background: var(--col-blue-600); color: white; border-radius: var(--radius-full); font-size: 0.65rem; padding: 1px 5px; font-family: var(--font-mono); }

/* Filters bar */
.filters-bar {
  padding: 12px 24px;
  border-bottom: 1px solid var(--col-border);
  background: var(--col-elevated);
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: flex-end;
}
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-label { font-size: 0.72rem; color: var(--col-text-dim); font-family: var(--font-mono); text-transform: uppercase; }
.filter-select {
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-primary);
  font-family: var(--font-body);
  font-size: 0.83rem;
  padding: 6px 10px;
  min-width: 140px;
}
.filter-select:focus { outline: none; border-color: var(--col-blue-600); }
.filter-select option { background: var(--col-elevated); }
.clear-filters {
  background: none;
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-dim);
  font-family: var(--font-body);
  font-size: 0.8rem;
  padding: 6px 12px;
  cursor: pointer;
  align-self: flex-end;
  transition: all var(--t-fast);
}
.clear-filters:hover { color: var(--col-error); border-color: var(--col-error); }

/* KPI cards */
.dashboard__kpis {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  overflow-x: auto;
  border-bottom: 1px solid var(--col-border);
}
.kpi-card {
  flex-shrink: 0;
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-lg);
  padding: 14px 18px;
  min-width: 160px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color var(--t-fast);
}
.kpi-card:hover { border-color: var(--col-blue-600); }
.kpi-card__label { font-size: 0.72rem; color: var(--col-text-dim); text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-card__value { font-size: 1.4rem; font-weight: 700; color: var(--col-text-primary); line-height: 1; }
.kpi-card__meta  { display: flex; align-items: center; justify-content: space-between; font-size: 0.72rem; color: var(--col-text-dim); }
.kpi-card__trend { font-weight: 700; }
.trend--up   { color: var(--col-success); }
.trend--down { color: var(--col-error); }

/* Charts grid */
.dashboard__charts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  padding: 16px 24px;
}
.charts-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 24px;
  color: var(--col-text-dim);
  font-size: 0.9rem;
}

/* Chart appear transition */
.chart-appear-enter-active { transition: all 0.3s ease; }
.chart-appear-enter-from   { opacity: 0; transform: scale(0.97); }

/* Filters slide */
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.2s ease; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }

/* Chart picker modal */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; backdrop-filter: blur(4px);
}
.modal {
  background: var(--col-elevated); border: 1px solid var(--col-border);
  border-radius: var(--radius-xl); padding: 24px;
  max-width: 560px; width: 90%; animation: fadeIn 0.2s ease;
}
.modal__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal__head h3 { font-size: 1rem; }
.icon-btn { background: none; border: none; cursor: pointer; color: var(--col-text-dim); font-size: 1rem; padding: 4px; border-radius: 4px; }
.icon-btn:hover { color: var(--col-text-primary); }

.chart-picker { max-height: 80vh; display: flex; flex-direction: column; }
.chart-picker__grid { overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.chart-picker__item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px; border-radius: var(--radius-md);
  border: 1px solid var(--col-border);
  cursor: pointer; transition: all var(--t-fast);
}
.chart-picker__item input { display: none; }
.chart-picker__item:hover { border-color: var(--col-blue-600); background: rgba(37,99,235,0.05); }
.chart-picker__item--on { border-color: var(--col-blue-600); background: rgba(37,99,235,0.08); }
.chart-picker__info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.chart-picker__type { font-size: 0.68rem; color: var(--col-blue-400); font-family: var(--font-mono); text-transform: uppercase; }
.chart-picker__title { font-size: 0.88rem; color: var(--col-text-primary); font-weight: 500; }
.chart-picker__desc { font-size: 0.77rem; color: var(--col-text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chart-picker__check { color: var(--col-blue-400); font-weight: 700; width: 20px; text-align: center; }

/* Buttons */
.btn { display: inline-flex; align-items: center; gap: 6px; border-radius: var(--radius-md); font-size: 0.83rem; font-weight: 500; font-family: var(--font-body); cursor: pointer; border: none; transition: all var(--t-fast); }
.btn--sm { padding: 7px 12px; }
.btn--ghost { background: transparent; color: var(--col-text-secondary); border: 1px solid var(--col-border); }
.btn--ghost:hover { border-color: var(--col-blue-600); color: var(--col-text-primary); }
.btn--primary { background: var(--col-blue-600); color: white; }
.btn--primary:hover { background: var(--col-blue-700); }
.mono { font-family: var(--font-mono); }
</style>
