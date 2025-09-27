'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Load } from '@/types/logistics';

// Fix for default markers in Leaflet with bundlers
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface RouteMapProps {
  load: Load;
  className?: string;
}

export function RouteMap({ load, className }: RouteMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;

    // Initialize map
    const map = L.map(mapRef.current).setView([39.8283, -98.5795], 4);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Create custom icons
    const pickupIcon = L.divIcon({
      html: `<div class="bg-emerald-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">P</div>`,
      className: 'custom-div-icon',
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    const deliveryIcon = L.divIcon({
      html: `<div class="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-medium">D</div>`,
      className: 'custom-div-icon',
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    // Add pickup marker
    const pickupMarker = L.marker(load.pickupCoords, { icon: pickupIcon })
      .addTo(map)
      .bindPopup(`<b>取货</b><br/>${load.stops[0]?.address || ''}`);

    // Add delivery marker  
    const deliveryMarker = L.marker(load.deliveryCoords, { icon: deliveryIcon })
      .addTo(map)
      .bindPopup(`<b>送货</b><br/>${load.stops[1]?.address || ''}`);

    // Draw route line
    const routeCoords = [load.pickupCoords, load.deliveryCoords];
    const routeLine = L.polyline(routeCoords, {
      color: '#10b981', // emerald-500
      weight: 3,
      opacity: 0.8
    }).addTo(map);

    // Fit map to route bounds
    const group = new L.FeatureGroup([pickupMarker, deliveryMarker, routeLine]);
    map.fitBounds(group.getBounds().pad(0.1));

    mapInstanceRef.current = map;

    return () => {
      map.remove();
    };
  }, [load]);

  return (
    <div 
      ref={mapRef} 
      className={className}
      style={{ height: '300px', width: '100%' }}
    />
  );
}