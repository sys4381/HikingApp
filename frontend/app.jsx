const { useState, useEffect, useRef } = React;

const API_BASE = "http://localhost:8000/api";

function App() {
    const [directory, setDirectory] = useState("");
    const [ingestStatus, setIngestStatus] = useState("");
    const [groups, setGroups] = useState([]);
    const [selectedGroup, setSelectedGroup] = useState(null);
    const [trails, setTrails] = useState([]);
    
    // Fetch Groups
    useEffect(() => {
        fetchGroups();
    }, []);

    const fetchGroups = async () => {
        try {
            const res = await fetch(`${API_BASE}/groups`);
            if (res.ok) {
                const data = await res.json();
                setGroups(data);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleIngest = async (e) => {
        e.preventDefault();
        setIngestStatus("Loading...");
        try {
            const res = await fetch(`${API_BASE}/ingest`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ directory_path: directory })
            });
            const data = await res.json();
            setIngestStatus(data.message || "Failed");
            if (data.message) {
                // Poll for groups every 2s, 5 times or until increased
                let attempts = 0;
                const i = setInterval(() => {
                    fetchGroups();
                    attempts++;
                    if (attempts > 10) clearInterval(i);
                }, 2000);
            }
        } catch (e) {
            setIngestStatus("Error triggering ingest");
        }
    };

    const selectGroup = async (group) => {
        setSelectedGroup(group);
        try {
            const res = await fetch(`${API_BASE}/groups/${group.id}/trails`);
            if (res.ok) {
                const data = await res.json();
                setTrails(data);
            }
        } catch (e) {
            console.error("Failed to fetch trails", e);
        }
    };

    return (
        <div className="app-container">
            <header className="header">
                <h1>🏞️ Hiking Explorer</h1>
                <form className="ingest-form" onSubmit={handleIngest}>
                    <input 
                        type="text" 
                        placeholder="Path to GPX folder (e.g. C:\Hiking)"
                        value={directory}
                        onChange={(e) => setDirectory(e.target.value)}
                        required
                    />
                    <button type="submit">Ingest</button>
                    {ingestStatus && <span className="status-text">{ingestStatus}</span>}
                </form>
            </header>
            
            <main className="main-content">
                <aside className="sidebar">
                    <h2>Trail Groups ({groups.length})</h2>
                    <ul className="group-list">
                        {groups.map(g => (
                            <li 
                                key={g.id} 
                                className={`group-card ${selectedGroup?.id === g.id ? 'active' : ''}`}
                                onClick={() => selectGroup(g)}
                            >
                                <div className="group-info">
                                    <span className="group-title">Lat: {g.center_lat.toFixed(3)}, Lon: {g.center_lon.toFixed(3)}</span>
                                    <span className="group-count">{g.trail_count} Trails</span>
                                </div>
                            </li>
                        ))}
                    </ul>
                </aside>
                <div className="map-area">
                    {selectedGroup ? (
                        <MapViewer group={selectedGroup} trails={trails} />
                    ) : (
                        <div className="empty-state">Select a group to view trails</div>
                    )}
                </div>
            </main>
        </div>
    );
}

// Map Component
function MapViewer({ group, trails }) {
    const mapRef = useRef(null);
    const mapInstance = useRef(null);
    const layerGroup = useRef(null);

    useEffect(() => {
        if (!mapInstance.current && mapRef.current) {
            mapInstance.current = L.map(mapRef.current).setView([group.center_lat, group.center_lon], 11);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }).addTo(mapInstance.current);

            layerGroup.current = L.featureGroup().addTo(mapInstance.current);
        }

        return () => {
            if (mapInstance.current) {
                mapInstance.current.remove();
                mapInstance.current = null;
                layerGroup.current = null;
            }
        };
    }, []);

    // Update markers and polylines when trails change
    useEffect(() => {
        if (!layerGroup.current || !mapInstance.current) return;
        
        layerGroup.current.clearLayers();
        
        trails.forEach(t => {
            // Draw Polyline if available
            if (t.polyline) {
                try {
                    const latlngs = JSON.parse(t.polyline);
                    const line = L.polyline(latlngs, {
                        color: t.difficulty_category === 'Easy' ? '#10b981' :
                               t.difficulty_category === 'Moderate' ? '#f59e0b' : '#ef4444', 
                        weight: 4,
                        opacity: 0.8
                    }).addTo(layerGroup.current);
                    
                    line.bindPopup(`<b>${t.name}</b><br/>${t.length_km.toFixed(1)} km<br/>Gain: ${Math.round(t.elevation_gain_m || 0)}m<br/>${t.difficulty_category}`);
                } catch (e) {
                    console.error("Invalid polyline JSON", e);
                }
            } else {
                // Fallback marker for start point
                L.marker([t.start_lat, t.start_lon]).addTo(layerGroup.current)
                    .bindPopup(`<b>${t.name}</b><br/>${t.length_km.toFixed(1)} km`);
            }
        });
        
        // Fit bounds
        if (trails.length > 0 && layerGroup.current.getLayers().length > 0) {
            mapInstance.current.fitBounds(layerGroup.current.getBounds(), { padding: [50, 50] });
        } else {
            mapInstance.current.setView([group.center_lat, group.center_lon], 11);
        }
        
    }, [trails, group]);

    return (
        <div className="map-wrapper">
            <div className="map-container" ref={mapRef}></div>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
