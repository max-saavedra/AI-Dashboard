/**
 * composables/useChartFilters.js
 *
 * Reactive composable that applies the workspace activeFilters to
 * a chart's series data for client-side filtering (RNF-02 < 200 ms).
 */

import { computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'

export function useChartFilters(config) {
  const store = useWorkspaceStore()

  /**
   * Return series data filtered by the currently active dimension filters.
   * When no filters are active the original series is returned unchanged.
   */
  const filteredSeries = computed(() => {
    const filters = store.activeFilters
    if (!Object.keys(filters).length) return config.series

    // Check if this chart's x_column is being filtered
    const filterValue = filters[config.x_column]
    if (!filterValue) return config.series

    const idx = config.categories.indexOf(filterValue)
    if (idx === -1) return config.series

    // Return only the matching data point
    return config.series.map(s => ({
      name: s.name,
      data: [s.data[idx]]
    }))
  })

  const filteredCategories = computed(() => {
    const filters = store.activeFilters
    if (!Object.keys(filters).length) return config.categories
    const filterValue = filters[config.x_column]
    if (!filterValue) return config.categories
    return config.categories.includes(filterValue) ? [filterValue] : config.categories
  })

  return { filteredSeries, filteredCategories }
}
