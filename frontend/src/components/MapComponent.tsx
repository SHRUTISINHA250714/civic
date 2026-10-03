'use client';

import { useEffect, useSyncExternalStore } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix the missing default marker icon assets issue in Leaflet
const DefaultIcon = L.icon({
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [16, -28],
  shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// Helper to create color-coded status icons
const createStatusIcon = (status: string) => {
  let color = '#3B82F6'; // Registered - Blue
  if (status === 'Accepted') color = '#F59E0B'; // Orange
  if (status === 'In Progress') color = '#8B5CF6'; // Purple
  if (status === 'Resolved') color = '#10B981'; // Green
  if (status === 'Closed') color = '#6B7280'; // Gray

  const html = `<span style="background-color: ${color}; width: 14px; height: 14px; border: 2px solid white; border-radius: 50%; display: inline-block; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></span>`;
  
  return L.divIcon({
    html: html,
    className: 'custom-status-icon',
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

// Helper to create Current Hotspot icons (flame/pulse)
const createCurrentHotspotIcon = (intensity: number = 75) => {
  const size = Math.min(38, Math.max(24, Math.round(intensity / 3)));
  const html = `
    <div style="position:relative; width:${size}px; height:${size}px; display:flex; align-items:center; justify-content:center;">
      <span style="position:absolute; width:100%; height:100%; border-radius:50%; background:rgba(239, 68, 68, 0.35); animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite;"></span>
      <span style="position:relative; width:${size-6}px; height:${size-6}px; border-radius:50%; background:#EF4444; border:2px solid white; color:white; font-size:10px; font-weight:bold; display:flex; align-items:center; justify-content:center; box-shadow:0 0 8px rgba(239,68,68,0.8);">🔥</span>
    </div>
  `;
  return L.divIcon({
    html,
    className: 'current-hotspot-icon',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
};

// Helper to create Predicted Hotspot icons (ML radar/forecast)
const createPredictedHotspotIcon = (risk: number = 75) => {
  const size = Math.min(38, Math.max(24, Math.round(risk / 3)));
  const html = `
    <div style="position:relative; width:${size}px; height:${size}px; display:flex; align-items:center; justify-content:center;">
      <span style="position:absolute; width:100%; height:100%; border-radius:50%; background:rgba(99, 102, 241, 0.35); animation:pulse 2s cubic-bezier(0.4,0,0.6,1) infinite;"></span>
      <span style="position:relative; width:${size-6}px; height:${size-6}px; border-radius:50%; background:#6366F1; border:2px solid white; color:white; font-size:10px; font-weight:bold; display:flex; align-items:center; justify-content:center; box-shadow:0 0 8px rgba(99,102,241,0.8);">⚡</span>
    </div>
  `;
  return L.divIcon({
    html,
    className: 'predicted-hotspot-icon',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
};

export interface MapMarker {
  id: number;
  latitude: number;
  longitude: number;
  title: string;
  status: string;
  category: string;
  impact_count?: number;
  priority?: string;
  agency?: string;
  department?: string;
  location_address?: string;
}

export interface HotspotMarker {
  name: string;
  latitude: number;
  longitude: number;
  type: 'current' | 'predicted';
  intensity_score?: number;
  risk_score?: number;
  risk_level?: string;
  active_complaint_count?: number;
  total_impact_count?: number;
  top_category?: string;
  department?: string;
  predicted_surge?: number;
  recommended_action?: string;
}

export interface MapComponentProps {
  center: [number, number];
  zoom?: number;
  markers?: MapMarker[];
  hotspots?: HotspotMarker[];
  onLocationSelect?: (lat: number, lon: number) => void;
  interactive?: boolean;
}

// Inner helper component to handle map clicks and centering updates
function MapController({ 
  center, 
  onLocationSelect, 
  interactive 
}: { 
  center: [number, number]; 
  onLocationSelect?: (lat: number, lon: number) => void;
  interactive?: boolean;
}) {
  const map = useMap();
  
  // Center map when center coordinates change
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);

  // Click handler for location selection
  useMapEvents({
    click(e) {
      if (interactive && onLocationSelect) {
        onLocationSelect(e.latlng.lat, e.latlng.lng);
      }
    }
  });

  return null;
}

const emptySubscribe = () => () => {};

export default function MapComponent({
  center,
  zoom = 13,
  markers = [],
  hotspots = [],
  onLocationSelect,
  interactive = false
}: MapComponentProps) {
  const isMounted = useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false
  );

  if (!isMounted) {
    return (
      <div className="w-full h-full bg-slate-100 dark:bg-slate-800 animate-pulse flex items-center justify-center text-slate-500 rounded-xl">
        Loading Map Engine...
      </div>
    );
  }

  return (
    <MapContainer 
      center={center} 
      zoom={zoom} 
      className="w-full h-full rounded-xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      <MapController 
        center={center} 
        onLocationSelect={onLocationSelect} 
        interactive={interactive}
      />

      {/* Render Current Selection Marker */}
      {interactive && onLocationSelect && (
        <Marker position={center} />
      )}

      {/* Render Current & Predicted Hotspots (Phase 15 GIS Enhancement) */}
      {hotspots.map((h, idx) => {
        const isCurrent = h.type === 'current';
        const icon = isCurrent 
          ? createCurrentHotspotIcon(h.intensity_score || 75) 
          : createPredictedHotspotIcon(h.risk_score || 75);

        return (
          <Marker
            key={`hotspot-${h.name}-${idx}`}
            position={[h.latitude, h.longitude]}
            icon={icon}
          >
            <Popup>
              <div className="p-1.5 min-w-[210px] text-slate-800">
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                    isCurrent ? 'bg-red-100 text-red-800' : 'bg-indigo-100 text-indigo-800'
                  }`}>
                    {isCurrent ? '🔥 Current Hotspot' : '⚡ Predicted Hotspot'}
                  </span>
                  <span className="text-[10px] font-bold text-slate-500">
                    Score: {isCurrent ? h.intensity_score : h.risk_score}/100
                  </span>
                </div>
                <h4 className="font-bold text-sm text-slate-900">{h.name} Ward</h4>
                {isCurrent ? (
                  <div className="mt-1 space-y-1 text-xs text-slate-600">
                    <p className="font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded border border-purple-200">
                      👥 Citizen Impact: {h.total_impact_count || 1} reports
                    </p>
                    <p>Active Issues: <span className="font-bold text-slate-800">{h.active_complaint_count || 0}</span></p>
                    <p>Top Issue: <span className="font-semibold">{h.top_category || 'General'}</span> ({h.department || 'BBMP'})</p>
                  </div>
                ) : (
                  <div className="mt-1 space-y-1 text-xs text-slate-600">
                    <p className="font-semibold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                      Surge Forecast: +{h.predicted_surge || 25}% weekly
                    </p>
                    <p>Primary Risk: <span className="font-bold text-slate-800">{h.top_category || 'Monsoon Flooding'}</span></p>
                    {h.recommended_action && (
                      <p className="text-[11px] italic text-slate-500 border-t border-slate-150 pt-1 mt-1">
                        🎯 {h.recommended_action}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        );
      })}

      {/* Render Complaint Markers */}
      {markers.map((marker) => (
        <Marker
          key={marker.id}
          position={[marker.latitude, marker.longitude]}
          icon={createStatusIcon(marker.status)}
        >
          <Popup>
            <div className="p-1 dark:text-slate-800 min-w-[190px]">
              <div className="flex items-center justify-between mb-1">
                <h4 className="font-semibold text-sm">{marker.category}</h4>
                <span className="text-[10px] font-mono text-slate-400">#{marker.id}</span>
              </div>
              <p className="text-xs text-slate-600 mb-1 line-clamp-2">{marker.title}</p>
              
              {/* Reported by X people (Phase 15 Requirement 10) */}
              <div className="flex items-center gap-1.5 my-1.5 text-[11px] font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                <span>👥 Reported by {marker.impact_count || 1} {(marker.impact_count || 1) === 1 ? 'person' : 'people'}</span>
              </div>

              {marker.location_address && (
                <p className="text-[10px] text-slate-500 truncate mb-1">
                  📍 {marker.location_address}
                </p>
              )}

              <div className="flex items-center justify-between mt-2 pt-1 border-t border-slate-100">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{
                  backgroundColor: marker.status === 'Resolved' ? '#D1FAE5' : '#DBEAFE',
                  color: marker.status === 'Resolved' ? '#065F46' : '#1E40AF'
                }}>
                  {marker.status}
                </span>
                {marker.priority && (
                  <span className={`text-[10px] font-bold ${
                    marker.priority === 'Critical' ? 'text-red-600' :
                    marker.priority === 'High' ? 'text-amber-600' : 'text-blue-600'
                  }`}>
                    {marker.priority}
                  </span>
                )}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
