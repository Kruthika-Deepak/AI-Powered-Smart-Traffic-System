import { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Toaster, toast } from "sonner";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { MapPin, TrendingUp, AlertTriangle, CheckCircle, Navigation, Activity } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Bangalore center coordinates
const BANGALORE_CENTER = [12.9716, 77.5946];

// Traffic locations
const LOCATIONS = [
  { id: "silk_board", name: "Silk Board", lat: 12.9177, lng: 77.6233 },
  { id: "kr_puram", name: "KR Puram", lat: 13.0075, lng: 77.6959 },
  { id: "whitefield", name: "Whitefield", lat: 12.9698, lng: 77.7500 },
  { id: "hebbal", name: "Hebbal", lat: 13.0358, lng: 77.5970 },
];

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

// Map controller component for flying to locations
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom || 14, { duration: 1.5 });
    }
  }, [center, zoom, map]);
  return null;
}

// Traffic marker component
function TrafficMarker({ prediction, location, isSelected }) {
  const getRadius = (severity) => {
    switch (severity) {
      case 3: return 25;
      case 2: return 20;
      default: return 15;
    }
  };

  const getOpacity = (severity) => {
    switch (severity) {
      case 3: return 0.9;
      case 2: return 0.8;
      default: return 0.7;
    }
  };

  // Use the most severe prediction for the marker
  const mostSevere = prediction
    ? prediction.predictions.reduce((max, p) => (p.severity > max.severity ? p : max), prediction.predictions[0])
    : null;

  return (
    <CircleMarker
      center={[location.lat, location.lng]}
      radius={mostSevere ? getRadius(mostSevere.severity) : 12}
      fillColor={mostSevere ? mostSevere.color : "#3B82F6"}
      fillOpacity={mostSevere ? getOpacity(mostSevere.severity) : 0.6}
      color={isSelected ? "#FFFFFF" : "rgba(255,255,255,0.5)"}
      weight={isSelected ? 3 : 2}
      data-testid={`map-marker-${location.id}`}
    >
      <Popup>
        <div className="font-inter text-sm">
          <strong className="text-base">{location.name}</strong>
          {mostSevere && (
            <div className="mt-2">
              <span
                className="inline-block px-2 py-1 rounded text-xs font-medium"
                style={{ backgroundColor: mostSevere.color + "20", color: mostSevere.color }}
              >
                {mostSevere.traffic_level}
              </span>
              <p className="mt-1 text-gray-600">{Math.round(mostSevere.traffic_value)} PCU/hr</p>
            </div>
          )}
        </div>
      </Popup>
    </CircleMarker>
  );
}

// Hour item component
function HourItem({ hour, traffic_value, traffic_level, color }) {
  const getIcon = () => {
    switch (traffic_level) {
      case "High":
        return <AlertTriangle size={14} className="text-red-500" />;
      case "Moderate":
        return <Activity size={14} className="text-amber-500" />;
      default:
        return <CheckCircle size={14} className="text-emerald-500" />;
    }
  };

  return (
    <div className="hour-item animate-fade-in" style={{ animationDelay: `${hour * 50}ms` }}>
      <div className="flex items-center gap-2">
        <span className="hour-time">{String(hour).padStart(2, "0")}:00</span>
        {getIcon()}
      </div>
      <div className="flex items-center gap-2">
        <span className="hour-value" style={{ color }}>
          {Math.round(traffic_value)}
        </span>
        <span className="text-xs text-zinc-500">PCU</span>
      </div>
    </div>
  );
}

function App() {
  const [selectedLocation, setSelectedLocation] = useState("");
  const [selectedDay, setSelectedDay] = useState("");
  const [startHour, setStartHour] = useState("");
  const [endHour, setEndHour] = useState("");
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mapCenter, setMapCenter] = useState(BANGALORE_CENTER);
  const [mapZoom, setMapZoom] = useState(12);

  const handlePredict = async () => {
    if (!selectedLocation || !selectedDay || startHour === "" || endHour === "") {
      toast.error("Please fill all fields");
      return;
    }

    if (parseInt(endHour) < parseInt(startHour)) {
      toast.error("End hour must be greater than or equal to start hour");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/predict-traffic`, {
        place: selectedLocation,
        day: selectedDay,
        start_hour: parseInt(startHour),
        end_hour: parseInt(endHour),
      });

      setPredictions(response.data);
      toast.success("Traffic prediction generated");

      // Fly to selected location
      const location = LOCATIONS.find((l) => l.id === selectedLocation);
      if (location) {
        setMapCenter([location.lat, location.lng]);
        setMapZoom(14);
      }
    } catch (error) {
      console.error("Prediction error:", error);
      toast.error(error.response?.data?.detail || "Failed to generate prediction");
    } finally {
      setLoading(false);
    }
  };

  const selectedLocationData = LOCATIONS.find((l) => l.id === selectedLocation);

  return (
    <div className="dashboard-container" data-testid="dashboard">
      <Toaster position="top-right" theme="light" richColors />

      {/* Sidebar Controls */}
      <aside className="sidebar" data-testid="sidebar">
        {/* Header */}
        <div className="mb-2">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Navigation size={20} className="text-blue-600" />
            </div>
            <div>
              <h1 className="font-rajdhani font-bold text-xl text-slate-900 tracking-tight">
                Traffic Sentinel
              </h1>
              <p className="text-xs text-slate-500 font-mono">BANGALORE</p>
            </div>
          </div>
        </div>

        {/* Location Selection */}
        <div>
          <label className="section-header">Select Location</label>
          <Select value={selectedLocation} onValueChange={setSelectedLocation}>
            <SelectTrigger className="w-full bg-white border-slate-200" data-testid="location-select">
              <SelectValue placeholder="Choose location" />
            </SelectTrigger>
            <SelectContent>
              {LOCATIONS.map((loc) => (
                <SelectItem key={loc.id} value={loc.id} data-testid={`location-option-${loc.id}`}>
                  <div className="flex items-center gap-2">
                    <MapPin size={14} className="text-slate-500" />
                    {loc.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Day Selection */}
        <div>
          <label className="section-header">Day of Week</label>
          <Select value={selectedDay} onValueChange={setSelectedDay}>
            <SelectTrigger className="w-full bg-white border-slate-200" data-testid="day-select">
              <SelectValue placeholder="Choose day" />
            </SelectTrigger>
            <SelectContent>
              {DAYS.map((day) => (
                <SelectItem key={day} value={day} data-testid={`day-option-${day.toLowerCase()}`}>
                  {day}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Time Range */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="section-header">Start Hour</label>
            <Select value={startHour} onValueChange={setStartHour}>
              <SelectTrigger className="w-full bg-white border-slate-200" data-testid="start-hour-select">
                <SelectValue placeholder="From" />
              </SelectTrigger>
              <SelectContent>
                {HOURS.map((hour) => (
                  <SelectItem key={hour} value={String(hour)}>
                    {String(hour).padStart(2, "0")}:00
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="section-header">End Hour</label>
            <Select value={endHour} onValueChange={setEndHour}>
              <SelectTrigger className="w-full bg-white border-slate-200" data-testid="end-hour-select">
                <SelectValue placeholder="To" />
              </SelectTrigger>
              <SelectContent>
                {HOURS.map((hour) => (
                  <SelectItem key={hour} value={String(hour)}>
                    {String(hour).padStart(2, "0")}:00
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Predict Button */}
        <Button
          className="predict-button w-full"
          onClick={handlePredict}
          disabled={loading}
          data-testid="predict-button"
        >
          {loading ? (
            <div className="flex items-center gap-2">
              <div className="loading-spinner" />
              Analyzing...
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <TrendingUp size={18} />
              Generate Prediction
            </div>
          )}
        </Button>

        {/* Legend */}
        <div className="mt-auto pt-4 border-t border-slate-200">
          <label className="section-header">Traffic Legend</label>
          <div className="legend">
            <div className="legend-item">
              <div className="legend-dot" style={{ backgroundColor: "#10B981" }} />
              <span>Normal</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot" style={{ backgroundColor: "#F59E0B" }} />
              <span>Moderate</span>
            </div>
            <div className="legend-item">
              <div className="legend-dot" style={{ backgroundColor: "#EF4444" }} />
              <span>High</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Map Area */}
      <main className="map-container" data-testid="map-container">
        <MapContainer
          center={BANGALORE_CENTER}
          zoom={12}
          style={{ width: "100%", height: "100%" }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapController center={mapCenter} zoom={mapZoom} />

          {/* Render markers for all locations */}
          {LOCATIONS.map((location) => (
            <TrafficMarker
              key={location.id}
              location={location}
              prediction={predictions && predictions.place === location.id ? predictions : null}
              isSelected={selectedLocation === location.id}
            />
          ))}
        </MapContainer>

        {/* Results Panel */}
        {predictions && (
          <div className="overlay-panel results-panel" data-testid="results-panel">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-rajdhani font-semibold text-lg text-slate-900">
                  {predictions.place_name}
                </h2>
                <p className="text-xs text-slate-500 font-mono">{predictions.day}</p>
              </div>
              <Badge
                variant="outline"
                className={`traffic-badge traffic-badge-${predictions.predictions.find(p => p.severity === Math.max(...predictions.predictions.map(x => x.severity)))?.traffic_level.toLowerCase()}`}
              >
                Peak: {predictions.peak_hour}:00
              </Badge>
            </div>

            <ScrollArea className="h-[280px] pr-2">
              <div className="space-y-1">
                {predictions.predictions.map((pred) => (
                  <HourItem key={pred.hour} {...pred} />
                ))}
              </div>
            </ScrollArea>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-slate-200">
              <div className="text-center">
                <p className="text-xs text-slate-500 font-mono uppercase">Peak Traffic</p>
                <p className="text-xl font-rajdhani font-bold text-red-600">
                  {Math.round(predictions.peak_traffic)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-slate-500 font-mono uppercase">Average</p>
                <p className="text-xl font-rajdhani font-bold text-slate-700">
                  {Math.round(predictions.average_traffic)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Insights Panel */}
        {predictions && (
          <div className="overlay-panel insights-panel" data-testid="insights-panel">
            <div className="insight-card">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle size={16} className="text-blue-600" />
                </div>
                <div>
                  <h3 className="font-rajdhani font-semibold text-sm text-slate-900 mb-1">
                    Congestion Insight
                  </h3>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {predictions.insight}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!predictions && (
          <div className="overlay-panel results-panel" data-testid="empty-state">
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
                <MapPin size={28} className="text-slate-400" />
              </div>
              <h3 className="font-rajdhani font-semibold text-slate-900 mb-2">
                Select Parameters
              </h3>
              <p className="text-sm text-slate-500">
                Choose a location, day, and time range to generate traffic predictions.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
