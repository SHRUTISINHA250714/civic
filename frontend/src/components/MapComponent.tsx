'use client';

import { useEffect, useState } from 'react';
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

interface MapMarker {
  id: number;
  latitude: number;
  longitude: number;
  title: string;
  status: string;
  category: string;
}

interface MapComponentProps {
  center: [number, number];
  zoom?: number;
  markers?: MapMarker[];
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

export default function MapComponent({
  center,
  zoom = 13,
  markers = [],
  onLocationSelect,
  interactive = false
}: MapComponentProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

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

      {/* Render Nearby Complaint Markers */}
      {markers.map((marker) => (
        <Marker
          key={marker.id}
          position={[marker.latitude, marker.longitude]}
          icon={createStatusIcon(marker.status)}
        >
          <Popup>
            <div className="p-1 dark:text-slate-800">
              <h4 className="font-semibold text-sm mb-1">{marker.category}</h4>
              <p className="text-xs text-slate-600 mb-1">{marker.title}</p>
              <div className="flex items-center space-x-1.5 mt-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{
                  backgroundColor: marker.status === 'Resolved' ? '#D1FAE5' : '#DBEAFE',
                  color: marker.status === 'Resolved' ? '#065F46' : '#1E40AF'
                }}>
                  {marker.status}
                </span>
                <span className="text-[10px] text-slate-400">ID: #{marker.id}</span>
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
