import type { Meteorite } from '../types/meteorite'
import { formatCoordinates, formatMass, formatYear } from '../utils/format'

interface MeteoriteDetailsProps {
  meteorite: Meteorite | null
}

export default function MeteoriteDetails({ meteorite }: MeteoriteDetailsProps) {
  if (!meteorite) {
    return (
      <section className="panel details-panel">
        <header className="panel-header">
          <h2>Meteorite Details</h2>
        </header>
        <p className="empty-state">Click a point on the globe — facts appear here and an AI summary pops up on the map.</p>
      </section>
    )
  }

  return (
    <section className="panel details-panel">
      <header className="panel-header">
        <h2>{meteorite.name}</h2>
        <p className="panel-subtitle">{meteorite.recclass ?? 'Unknown classification'}</p>
      </header>

      <dl className="detail-grid">
        <div>
          <dt>Mass</dt>
          <dd>{formatMass(meteorite.mass_grams)}</dd>
        </div>
        <div>
          <dt>Year</dt>
          <dd>{formatYear(meteorite.year)}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{meteorite.fall ?? 'Unknown'}</dd>
        </div>
        <div>
          <dt>Location</dt>
          <dd>{formatCoordinates(meteorite.latitude, meteorite.longitude)}</dd>
        </div>
      </dl>
    </section>
  )
}
