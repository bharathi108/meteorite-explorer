import type { FallFilter, MeteoriteFilters } from '../types/meteorite'

interface FilterPanelProps {
  filters: MeteoriteFilters
  onChange: (filters: MeteoriteFilters) => void
  onReset: () => void
  total: number
  shown: number
  loading: boolean
  refreshing: boolean
  viewportScoped: boolean
}

export default function FilterPanel({
  filters,
  onChange,
  onReset,
  total,
  shown,
  loading,
  refreshing,
  viewportScoped,
}: FilterPanelProps) {
  const update = (patch: Partial<MeteoriteFilters>) => {
    onChange({ ...filters, ...patch })
  }

  return (
    <section className="panel filter-panel">
      <header className="panel-header">
        <h2>Explore</h2>
        <p className="panel-subtitle">
          {loading
            ? 'Loading meteorites…'
            : refreshing
              ? 'Updating view…'
              : viewportScoped
                ? `${shown.toLocaleString()} in view · ${total.toLocaleString()} matching`
                : `${shown.toLocaleString()} shown · ${total.toLocaleString()} matching worldwide`}
        </p>
      </header>

      <div className="field">
        <label htmlFor="search">Search</label>
        <input
          id="search"
          type="search"
          placeholder="Meteorite name"
          value={filters.search}
          onChange={(e) => update({ search: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="recclass">Classification</label>
        <input
          id="recclass"
          type="text"
          placeholder="e.g. L5, H6, EH4"
          value={filters.recclass}
          onChange={(e) => update({ recclass: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="fall">Fall status</label>
        <select
          id="fall"
          value={filters.fall}
          onChange={(e) => update({ fall: e.target.value as FallFilter })}
        >
          <option value="">Any</option>
          <option value="Fell">Fell (observed)</option>
          <option value="Found">Found</option>
        </select>
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="minYear">Min year</label>
          <input
            id="minYear"
            type="number"
            placeholder="1800"
            value={filters.minYear}
            onChange={(e) => update({ minYear: e.target.value })}
          />
        </div>
        <div className="field">
          <label htmlFor="maxYear">Max year</label>
          <input
            id="maxYear"
            type="number"
            placeholder="2024"
            value={filters.maxYear}
            onChange={(e) => update({ maxYear: e.target.value })}
          />
        </div>
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor="minMass">Min mass (g)</label>
          <input
            id="minMass"
            type="number"
            placeholder="0"
            value={filters.minMass}
            onChange={(e) => update({ minMass: e.target.value })}
          />
        </div>
        <div className="field">
          <label htmlFor="maxMass">Max mass (g)</label>
          <input
            id="maxMass"
            type="number"
            placeholder="100000"
            value={filters.maxMass}
            onChange={(e) => update({ maxMass: e.target.value })}
          />
        </div>
      </div>

      <button type="button" className="btn-secondary" onClick={onReset}>
        Reset filters
      </button>
    </section>
  )
}
