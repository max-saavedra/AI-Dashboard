<template>
  <div class="chart-card" :class="{ 'chart-card--wide': isWide }">
    <div class="chart-card__header">
      <div class="chart-header__left">
        <span class="chart-type-badge mono">{{ config.chart_type }}</span>
        <h3 class="chart-title">{{ config.title }}</h3>
      </div>
      <button class="info-btn" @click="showInfo = !showInfo" title="Chart details">
        <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"/>
        </svg>
      </button>
    </div>

    <!-- Info overlay -->
    <Transition name="fade">
      <div v-if="showInfo" class="chart-info">
        <p class="chart-info__desc">{{ config.description || 'No description available.' }}</p>
        <div class="chart-info__meta">
          <div class="meta-row"><span>X axis</span><span class="mono">{{ config.x_column }}</span></div>
          <div class="meta-row"><span>Y axis</span><span class="mono">{{ config.y_column }}</span></div>
          <div class="meta-row"><span>Aggregation</span><span class="mono">{{ config.aggregation }}</span></div>
          <div class="meta-row" v-if="config.is_time_series"><span>Type</span><span class="mono">Time series</span></div>
        </div>
        <button class="close-info" @click="showInfo = false">Close</button>
      </div>
    </Transition>

    <!-- Chart -->
    <div class="chart-card__body">
      <apexchart
        v-if="chartOptions && chartSeries.length"
        :type="apexType"
        :options="chartOptions"
        :series="chartSeries"
        height="260"
      />
      <div v-else class="chart-placeholder">
        <span>No data available for this chart</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  config:       { type: Object, required: true },
  filteredData: { type: Object, default: () => ({}) }
})

const showInfo = ref(false)

// Map backend chart_type to ApexCharts type
const apexType = computed(() => {
  const map = { bar: 'bar', line: 'line', pie: 'pie', area: 'area', scatter: 'scatter', table: 'bar' }
  return map[props.config.chart_type] || 'bar'
})

const isWide = computed(() =>
  ['line', 'area'].includes(props.config.chart_type)
)

// Build series from config, applying active filters
const chartSeries = computed(() => {
  const series = props.config.series || []
  if (!series.length) return []
  if (props.config.chart_type === 'pie') {
    return series[0]?.data || []
  }
  return series.map(s => ({ name: s.name, data: s.data }))
})

const chartOptions = computed(() => {
  const categories = props.config.categories || []
  const isPie      = props.config.chart_type === 'pie'

  const base = {
    chart: {
      background: 'transparent',
      toolbar: { show: false },
      animations: { enabled: true, speed: 600, animateGradually: { enabled: true, delay: 80 } },
      fontFamily: 'DM Sans, sans-serif'
    },
    theme: { mode: 'dark' },
    colors: ['#2563EB', '#60A5FA', '#1D4ED8', '#93C5FD', '#1E3A5F'],
    grid: {
      borderColor: '#1E2D47',
      strokeDashArray: 4,
      xaxis: { lines: { show: false } }
    },
    tooltip: {
      theme: 'dark',
      style: { fontFamily: 'DM Sans, sans-serif', fontSize: '12px' },
      y: { formatter: v => formatVal(v) }
    },
    dataLabels: { enabled: false }
  }

  if (isPie) {
    return {
      ...base,
      labels: categories,
      legend: {
        position: 'bottom',
        labels: { colors: '#94A3B8' },
        fontSize: '11px'
      },
      stroke: { width: 2, colors: ['#0D1424'] },
      plotOptions: {
        pie: { donut: { size: '55%', labels: { show: true, total: { show: true, color: '#94A3B8' } } } }
      }
    }
  }

  const isHorizontalBar = props.config.chart_type === 'bar' && categories.length > 8
  return {
    ...base,
    xaxis: {
      categories,
      labels: {
        style: { colors: '#94A3B8', fontSize: '11px' },
        rotate: categories.length > 6 ? -35 : 0
      },
      axisBorder: { color: '#1E2D47' },
      axisTicks:  { color: '#1E2D47' }
    },
    yaxis: {
      labels: {
        style: { colors: '#94A3B8', fontSize: '11px' },
        formatter: v => formatVal(v)
      }
    },
    plotOptions: {
      bar: {
        borderRadius: 4,
        columnWidth: '60%',
        horizontal: isHorizontalBar
      }
    },
    stroke: props.config.chart_type === 'line' || props.config.chart_type === 'area'
      ? { curve: 'smooth', width: 2 }
      : { show: false },
    fill: props.config.chart_type === 'area'
      ? { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] } }
      : { opacity: 1 },
    legend: {
      labels: { colors: '#94A3B8' },
      fontSize: '11px'
    }
  }
})

function formatVal(v) {
  if (v === null || v === undefined) return '—'
  const n = parseFloat(v)
  if (isNaN(n)) return v
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (Math.abs(n) >= 1_000)     return (n / 1_000).toFixed(1) + 'K'
  return n % 1 === 0 ? n.toLocaleString() : n.toFixed(2)
}
</script>

<style scoped>
.chart-card {
  background: var(--col-surface);
  border: 1px solid var(--col-border);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
  position: relative;
  overflow: hidden;
}
.chart-card:hover {
  border-color: var(--col-blue-900);
  box-shadow: var(--shadow-glow);
}
.chart-card--wide { grid-column: span 2; }

.chart-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.chart-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.chart-type-badge {
  flex-shrink: 0;
  font-size: 0.65rem;
  padding: 2px 6px;
  background: rgba(37,99,235,0.15);
  color: var(--col-blue-400);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(37,99,235,0.25);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.chart-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--col-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.info-btn {
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--col-text-dim);
  padding: 4px;
  border-radius: 4px;
  transition: color var(--t-fast);
  display: flex;
  align-items: center;
}
.info-btn:hover { color: var(--col-blue-400); }

/* Info overlay */
.chart-info {
  position: absolute;
  inset: 0;
  background: rgba(13,20,36,0.95);
  backdrop-filter: blur(4px);
  z-index: 10;
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.chart-info__desc {
  font-size: 0.85rem;
  color: var(--col-text-secondary);
  line-height: 1.6;
}
.chart-info__meta { display: flex; flex-direction: column; gap: 6px; }
.meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.78rem;
  color: var(--col-text-dim);
}
.meta-row .mono { color: var(--col-blue-400); font-size: 0.75rem; }
.close-info {
  margin-top: auto;
  background: none;
  border: 1px solid var(--col-border);
  border-radius: var(--radius-md);
  color: var(--col-text-secondary);
  font-family: var(--font-body);
  font-size: 0.83rem;
  padding: 7px 14px;
  cursor: pointer;
  transition: all var(--t-fast);
}
.close-info:hover { border-color: var(--col-blue-600); color: var(--col-text-primary); }

.chart-card__body { min-height: 260px; }

.chart-placeholder {
  height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.83rem;
  color: var(--col-text-dim);
  border: 1px dashed var(--col-border);
  border-radius: var(--radius-md);
}
.mono { font-family: var(--font-mono); }
</style>
