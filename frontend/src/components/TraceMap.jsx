import { memo, useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import Icon from './Icon'

function FlyTo({ lat, lon }) {
  const map = useMap()

  useEffect(() => {
    if (lat != null && lon != null) {
      map.flyTo([lat, lon], 10, { duration: 1.5 })
    }
  }, [map, lat, lon])

  return null
}

function TraceMap({ geoTrace, relayHops = [] }) {
  const [analystLocation, setAnalystLocation] = useState(null)
  const [locationError, setLocationError] = useState('')
  const hasGeo = geoTrace?.lat != null && geoTrace?.lon != null
  const center = hasGeo ? [geoTrace.lat, geoTrace.lon] : [20, 0]
  const zoom = hasGeo ? 10 : 2

  // Pulsing marker
  const markerIcon = useMemo(
    () =>
      L.divIcon({
        className: 'custom-map-pin',
        html: `<div class="pulse-marker" style="
          width: 18px; height: 18px;
          background: var(--accent-cyan, #0070f3);
          border-radius: 50%;
          border: 3px solid rgba(255,255,255,0.9);
          box-shadow: 0 0 0 4px rgba(0, 112, 243, 0.14);
        "></div>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
      }),
    []
  )

  const analystIcon = useMemo(() => L.divIcon({
    className: 'custom-map-pin',
    html: '<div style="width:18px;height:18px;background:#7928ca;border-radius:50%;border:3px solid white;box-shadow:0 0 0 4px rgba(121,40,202,.14)"></div>',
    iconSize: [18, 18], iconAnchor: [9, 9],
  }), [])

  const distanceKm = analystLocation && hasGeo ? haversineKm(analystLocation.lat, analystLocation.lon, geoTrace.lat, geoTrace.lon) : null
  const observedRelayIps = [...new Set((Array.isArray(relayHops) ? relayHops : [])
    .map(hop => hop?.ip)
    .filter(Boolean))]
  const requestLocation = () => {
    setLocationError('')
    if (!navigator.geolocation) {
      setLocationError('This browser does not support location access.')
      return
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => setAnalystLocation({ lat: coords.latitude, lon: coords.longitude, accuracy: Math.round(coords.accuracy) }),
      () => setLocationError('Location access was not granted. Your location is not stored.'),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
    )
  }

  return (
    <div className="glass-card" id="trace-map-section">
      <div className="card-header">
        <span className="card-title">
          <span className="card-title-icon"><Icon name="globe" /></span>
          Origin Trace & Geolocation
        </span>
      </div>
      <div className="card-body">
        <div className="trace-map-container">
          <MapContainer
            center={center}
            zoom={zoom}
            scrollWheelZoom
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              maxZoom={19}
            />
            {hasGeo && (
              <>
                <Marker position={[geoTrace.lat, geoTrace.lon]} icon={markerIcon}>
                  <Popup className="custom-popup">
                    <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 13, lineHeight: 1.6, minWidth: 180 }}>
                      <strong style={{ fontSize: 14 }}>
                        {geoTrace.city || 'Unknown'}, {geoTrace.country || 'Unknown'}
                      </strong>
                      <br />
                      <span style={{ color: '#666' }}>IP:</span> {geoTrace.earliest_hop_ip || 'N/A'}
                      <br />
                      <span style={{ color: '#666' }}>ISP:</span> {geoTrace.isp || 'N/A'}
                      <br />
                      <span style={{ color: '#666' }}>Org:</span> {geoTrace.org || 'N/A'}
                      <br />
                      <span style={{ color: '#666' }}>Locality:</span> {geoTrace.location_detail || geoTrace.city || 'N/A'}
                      <br />
                      {geoTrace.is_vpn_or_hosting ? (
                        <span style={{ color: '#ff9500', fontWeight: 600 }}>VPN/Hosting Provider</span>
                      ) : (
                        <span style={{ color: '#10b981' }}>Clean IP</span>
                      )}
                    </div>
                  </Popup>
                </Marker>
                <FlyTo lat={geoTrace.lat} lon={geoTrace.lon} />
              </>
            )}
            {analystLocation && (
              <>
                <Marker position={[analystLocation.lat, analystLocation.lon]} icon={analystIcon}>
                  <Popup><strong>Analyst location</strong><br />Accuracy: approximately {analystLocation.accuracy} m</Popup>
                </Marker>
                {hasGeo && <Polyline positions={[[analystLocation.lat, analystLocation.lon], [geoTrace.lat, geoTrace.lon]]} pathOptions={{ color: '#7928ca', weight: 2, dashArray: '6 8' }} />}
              </>
            )}
          </MapContainer>
        </div>

        {geoTrace && (
          <>
          <div className="map-info">
            <div className="map-info-item">
              <span className="map-info-label">IP:</span>
              <strong>{geoTrace.earliest_hop_ip || 'N/A'}</strong>
            </div>
            <div className="map-info-item">
              <span className="map-info-label">Location:</span>
              <strong>{geoTrace.city || '?'}, {geoTrace.country || '?'}</strong>
            </div>
            <div className="map-info-item location-detail">
              <span className="map-info-label">Nearest locality:</span>
              <strong>{geoTrace.location_detail || 'City-level IP location only'}</strong>
            </div>
            <div className="map-info-item">
              <span className="map-info-label">ISP:</span>
              <strong>{geoTrace.isp || 'N/A'}</strong>
            </div>
            <div className="map-info-item">
              {geoTrace.is_vpn_or_hosting ? (
                <span className="vpn-badge hosting"><Icon name="alert" /> VPN/Hosting</span>
              ) : (
                <span className="vpn-badge clean"><Icon name="check" /> Clean</span>
              )}
            </div>
            {geoTrace.domain_age_days != null && (
              <div className="map-info-item">
                <span className="map-info-label">Domain Age:</span>
                <strong>{geoTrace.domain_age_days} days</strong>
              </div>
            )}
            {geoTrace.whois_registrar && (
              <div className="map-info-item">
                <span className="map-info-label">Registrar:</span>
                <strong>{geoTrace.whois_registrar}</strong>
              </div>
            )}
          </div>
          <div className="relay-path" aria-label="Observed email relay path">
            <div className="relay-path-title">Observed relay path</div>
            {observedRelayIps.length ? (
              <div className="relay-path-items">
                {observedRelayIps.map((ip, index) => (
                  <span className={`relay-hop ${ip === geoTrace.earliest_hop_ip ? 'origin-candidate' : ''}`} key={`${ip}-${index}`}>
                    <b>Hop {index + 1}</b> {ip}
                    {ip === geoTrace.earliest_hop_ip && <em>selected original relay</em>}
                  </span>
                ))}
              </div>
            ) : <span className="relay-path-empty">No parseable IP addresses in the Received headers.</span>}
            <p>Mail commonly crosses several provider relays. The map pin uses the oldest public IP in this email’s Received headers. It identifies the original public relay, not the sender’s precise physical location.</p>
          </div>
          </>
        )}

        <div className="analyst-location-panel">
          <div>
            <div className="analyst-location-title">Analyst distance check</div>
            <div className="analyst-location-copy">Use your device location to compare it with the email origin. It remains only in this browser session.</div>
          </div>
          <button type="button" className="btn-secondary" onClick={requestLocation}><Icon name="location" /> Use my location</button>
          {distanceKm != null && <div className="distance-result"><b>{distanceKm.toLocaleString(undefined, { maximumFractionDigits: 0 })} km</b><span>from email origin</span></div>}
          {analystLocation && <div className="coordinate-result">Your coordinates: {analystLocation.lat.toFixed(4)}, {analystLocation.lon.toFixed(4)} (±{analystLocation.accuracy} m)</div>}
          {locationError && <div className="location-error">{locationError}</div>}
        </div>

        {!hasGeo && (
          <div style={{
            textAlign: 'center',
            padding: 20,
            color: 'var(--text-muted)',
            fontSize: 13,
          }}>
            No map location available. Geolocation requires a public IPv4 address in a Received header; private, local, and malformed relay addresses are intentionally not sent to ip-api.
          </div>
        )}
      </div>
    </div>
  )
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const radians = value => value * Math.PI / 180
  const dLat = radians(lat2 - lat1), dLon = radians(lon2 - lon1)
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(radians(lat1)) * Math.cos(radians(lat2)) * Math.sin(dLon / 2) ** 2
  return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export default memo(TraceMap)
