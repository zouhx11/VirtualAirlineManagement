/**
 * Real-Time Aircraft Tracking App - MINIMAL WORKING VERSION
 */

class AircraftTracker {
    constructor() {
        this.map = null;
        this.map3D = null;
        this.layer3D = null;
        this.socket = null;
        this.aircraftMarkers = new Map();
        this.airportMarkers = new Map();
        this.aircraft3DModels = new Map();
        this.currentFlights = [];
        this.timeSpeed = 1;
        this.is3DMode = false;
        this.isGlobeMode = false;
        this.globeMap = null;
        this.globeLayer3D = null;
        this.followingFlight = null;
        this.flightTrackingInterval = null;
        this.routeLinesVisible = false;
        this.routeLines = new Map();
        this.isAssigningRoute = false;
        this.currentlyFollowing = null; // Track which aircraft camera is following
        this.freeCameraMode = false; // Free camera mode toggle
        this.selectedFlight = null; // Track selected flight for camera control - null = free camera, selected = locked camera
        this.maptilerApiKey = 'icLNtmi1FuvbINsiGgdt'; // Demo API key for testing
        
        // Airport coordinates
        this.AIRPORTS = {
            'KJFK': { lat: 40.6413, lon: -73.7781, name: 'John F Kennedy Intl' },
            'KLAX': { lat: 33.9425, lon: -118.4081, name: 'Los Angeles Intl' },
            'EGLL': { lat: 51.4700, lon: -0.4543, name: 'London Heathrow' },
            'EDDF': { lat: 50.0379, lon: 8.5622, name: 'Frankfurt am Main' },
            'RJTT': { lat: 35.7653, lon: 140.3864, name: 'Tokyo Narita' },
            'OMDB': { lat: 25.2532, lon: 55.3657, name: 'Dubai Intl' },
            'KATL': { lat: 33.6407, lon: -84.4277, name: 'Atlanta Hartsfield' },
            'KORD': { lat: 41.9742, lon: -87.9073, name: 'Chicago O\'Hare' },
            'KBOS': { lat: 42.3656, lon: -71.0096, name: 'Boston Logan' },
            'KDCA': { lat: 38.8512, lon: -77.0402, name: 'Reagan Washington' },
            'KLAS': { lat: 36.0840, lon: -115.1537, name: 'Las Vegas McCarran' },
            'KMCO': { lat: 28.4312, lon: -81.3081, name: 'Orlando Intl' },
            'KSFO': { lat: 37.6213, lon: -122.3790, name: 'San Francisco Intl' },
            'YSSY': { lat: -33.9399, lon: 151.1753, name: 'Sydney Kingsford Smith' }
        };
        
        // Weather system
        this.weatherSystem = {
            enabled: true,
            currentWeather: new Map(), // airport code -> weather data
            weatherLayers: new Map(),  // weather visual layers
            lastWeatherUpdate: 0,
            weatherTypes: ['clear', 'rain', 'storm', 'snow', 'fog', 'wind']
        };
        
        // Tutorial system
        this.tutorialStep = 1;
        this.tutorialMaxSteps = 8;
        this.tutorialCompleted = this.checkTutorialCompleted();
        
        this.init();
    }

    init() {
        this.initMap();
        this.initSocket();
        this.initUI();
        this.initTutorial();
        this.loadInitialData();
        this.initWeatherSystem();
    }

    initMap() {
        // Initialize Leaflet map with dark theme
        this.map = L.map('map', {
            center: [40.6413, -73.7781], // JFK
            zoom: 3,
            zoomControl: true
        });

        // Add dark tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(this.map);

        console.log('✅ Map initialized');
    }

    initSocket() {
        // Connect to Flask-SocketIO
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('🔌 Connected to server');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from server');
            this.updateConnectionStatus(false);
        });

        this.socket.on('aircraft_update', (data) => {
            this.updateAircraft(data);
        });

        console.log('🚀 WebSocket initialized');
    }

    initUI() {
        // Time speed control
        document.getElementById('time-speed').addEventListener('change', (e) => {
            this.setTimeSpeed(parseFloat(e.target.value));
        });

        // Sidebar toggle
        document.getElementById('toggle-sidebar').addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Marketplace
        document.getElementById('load-marketplace').addEventListener('click', () => {
            this.loadMarketplace();
        });

        // 3D Flight Mode Controls
        document.getElementById('toggle-3d-flight').addEventListener('click', () => {
            this.toggle3DFlightMode();
        });

        document.getElementById('toggle-globe-mode').addEventListener('click', () => {
            this.toggleGlobeFlightMode();
        });

        document.getElementById('toggle-2d-map').addEventListener('click', () => {
            this.toggle2DMapMode();
        });

        document.getElementById('toggle-free-camera').addEventListener('click', () => {
            this.toggleFreeCamera();
        });

        document.getElementById('exit-3d-mode').addEventListener('click', () => {
            this.toggle2DMapMode();
        });

        document.getElementById('exit-globe-mode').addEventListener('click', () => {
            this.toggle2DMapMode();
        });

        // Route lines toggle
        document.getElementById('toggle-routes').addEventListener('click', () => {
            this.toggleRouteLines();
        });

        // Weather toggle
        document.getElementById('toggle-weather').addEventListener('click', () => {
            this.toggleWeather();
        });

        console.log('🎮 UI initialized');
    }

    async loadInitialData() {
        try {
            // Load airports
            const airports = await this.fetchAPI('/api/airports');
            this.addAirports(airports);

            // Load economics data
            this.loadEconomics();

            console.log('📊 Initial data loaded');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
        }
    }

    async fetchAPI(endpoint) {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    }

    addAirports(airports) {
        Object.entries(airports).forEach(([code, airport]) => {
            const marker = L.circleMarker([airport.lat, airport.lon], {
                radius: 8,
                fillColor: '#3388ff',
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(this.map);

            marker.bindPopup(`<b>${airport.name}</b><br>Code: ${code}`);
            this.airportMarkers.set(code, marker);
        });

        console.log(`✈️ Added ${Object.keys(airports).length} airports`);
    }

    async loadEconomics() {
        try {
            const economics = await this.fetchAPI('/api/economics');
            this.updateEconomicsDisplay(economics);
        } catch (error) {
            console.error('❌ Error loading economics:', error);
        }
    }

    updateEconomicsDisplay(economics) {
        // Update header controls
        document.getElementById('cash-balance').textContent = `$${economics.cash_balance.toFixed(1)}M`;
        document.getElementById('fleet-count').textContent = `${economics.fleet_size} aircraft`;
        
        const profitElement = document.getElementById('monthly-profit');
        profitElement.textContent = `$${economics.net_profit.toFixed(0)}`;
        profitElement.className = 'profit-amount ' + (economics.net_profit >= 0 ? 'positive' : 'negative');
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (connected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status connected';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status disconnected';
        }
    }

    setTimeSpeed(speed) {
        this.timeSpeed = speed;
        console.log(`⚡ Setting time speed to ${speed}x`);
        
        if (this.socket) {
            // Use the correct API endpoint
            fetch('/api/time_speed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ speed: speed })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`✅ Speed set to ${data.speed}x successfully`);
                } else {
                    console.error('❌ Failed to set speed:', data.error);
                }
            })
            .catch(error => {
                console.error('❌ Error setting speed:', error);
            });
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('collapsed');
    }

    switchTab(tabName) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Remove active class from all buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        
        // Show selected tab
        document.getElementById(`${tabName}-tab`).classList.add('active');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Load tab-specific data
        if (tabName === 'marketplace') {
            this.loadMarketplace();
        } else if (tabName === 'routes') {
            this.loadRoutesData();
        } else if (tabName === 'fleet') {
            this.loadFleetData();
        }
    }

    async loadMarketplace() {
        try {
            const aircraft = await this.fetchAPI('/api/marketplace');
            console.log('📊 Marketplace data received:', aircraft);
            this.updateMarketplaceList(aircraft);
        } catch (error) {
            console.error('❌ Error loading marketplace:', error);
        }
    }

    updateMarketplaceList(aircraft) {
        const container = document.getElementById('marketplace-list');
        
        if (aircraft.length === 0) {
            container.innerHTML = '<div class="no-data">No aircraft available</div>';
            return;
        }

        container.innerHTML = aircraft.slice(0, 10).map((plane, index) => {
            const aircraftId = plane.id || `aircraft_${index}_${Date.now()}`;
            console.log(`🛩️ Aircraft ${index}:`, plane);
            return `
            <div class="aircraft-item">
                <h5>${plane.model || 'A321'}</h5>
                <p><strong>Capacity:</strong> ${plane.capacity || 220} passengers</p>
                <p><strong>Range:</strong> ${(plane.range || 3200).toLocaleString()} nm</p>
                <p><strong>Age:</strong> ${(plane.age || 0).toFixed(1)} years</p>
                <p class="price"><strong>Price:</strong> $${(plane.price || 100).toFixed(1)}M</p>
                <div class="aircraft-actions">
                    <button class="btn btn-secondary" onclick="tracker.show3DModel('${plane.model || 'A321'}', ${JSON.stringify(plane).replace(/"/g, '&quot;')})">
                        🎲 3D
                    </button>
                    <button class="btn btn-success" onclick="tracker.purchaseAircraft('${aircraftId}', 'CASH')">
                        💰 Buy
                    </button>
                    <button class="btn btn-primary" onclick="tracker.purchaseAircraft('${aircraftId}', 'LEASE')">
                        📋 Lease
                    </button>
                </div>
            </div>
        `;
        }).join('');
    }

    show3DModel(aircraftModel, aircraftData) {
        console.log('🎲 Opening 3D model for:', aircraftModel);
        this.createAndShow3DViewer(aircraftModel, aircraftData);
    }

    createAndShow3DViewer(aircraftModel, aircraftData) {
        // Create popup if it doesn't exist
        let popup = document.getElementById('aircraft-3d-popup');
        if (!popup) {
            popup = document.createElement('div');
            popup.id = 'aircraft-3d-popup';
            popup.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
            `;
            document.body.appendChild(popup);
        }

        // Create content container with Google's model-viewer
        popup.innerHTML = `
            <div style="
                background: white;
                border-radius: 10px;
                padding: 20px;
                max-width: 90%;
                max-height: 90%;
                width: 800px;
                height: 650px;
                display: flex;
                flex-direction: column;
                position: relative;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                ">
                    <h3 style="margin: 0; color: #333;">${aircraftModel} - 3D View</h3>
                    <button id="close-3d-popup" style="
                        background: #ff4444;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 8px 12px;
                        cursor: pointer;
                        font-size: 14px;
                    ">✕ Close</button>
                </div>
                <model-viewer 
                    src="/static/models/aircraft/a321.glb"
                    alt="A321 Aircraft 3D Model"
                    auto-rotate 
                    camera-controls 
                    style="
                        flex: 1;
                        width: 100%; 
                        height: 500px;
                        border-radius: 5px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    ">
                </model-viewer>
                <div style="
                    margin-top: 15px;
                    padding: 10px;
                    background: #f5f5f5;
                    border-radius: 5px;
                    font-size: 14px;
                ">
                    <strong>Model:</strong> ${aircraftModel} | 
                    <strong>Capacity:</strong> ${aircraftData.capacity || 220} passengers | 
                    <strong>Range:</strong> ${aircraftData.range ? aircraftData.range.toLocaleString() : '3,200'} nm | 
                    <strong>Price:</strong> $${aircraftData.price ? aircraftData.price.toFixed(1) : 'N/A'}M
                </div>
            </div>
        `;

        // Show popup
        popup.style.display = 'flex';

        // Setup close button
        document.getElementById('close-3d-popup').onclick = () => {
            popup.style.display = 'none';
        };
    }

    // No longer needed - using Google model-viewer instead of Three.js

    async purchaseAircraft(aircraftId, financingType) {
        console.log(`💰 Attempting to purchase aircraft: ${aircraftId} with ${financingType}`);
        
        if (!aircraftId || aircraftId === 'undefined') {
            alert('❌ Invalid aircraft ID');
            return;
        }
        
        try {
            const requestData = { 
                aircraft_id: aircraftId, 
                financing_type: financingType 
            };
            console.log('📤 Purchase request:', requestData);
            
            const response = await fetch('/api/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            console.log('📥 Purchase response:', result);
            
            if (result.success) {
                alert(`✅ ${result.message}`);
                this.loadMarketplace(); // Refresh marketplace
                this.loadEconomics(); // Refresh cash balance
            } else {
                alert(`❌ ${result.message || 'Purchase failed'}`);
            }
        } catch (error) {
            console.error('❌ Error purchasing aircraft:', error);
            alert(`❌ Purchase failed: ${error.message}`);
        }
    }

    updateAircraft(data) {
        // Always store current flights regardless of mode
        if (data.flights) {
            this.currentFlights = data.flights;
        }
        
        if (this.isGlobeMode && this.globeLayer3D) {
            this.updateGlobeAircraft(data);
        } else if (this.is3DMode && this.layer3D) {
            this.update3DAircraft(data);
        } else {
            this.update2DAircraft(data);
        }
        console.log('📡 Aircraft update received:', data.flights ? data.flights.length : 0, 'flights');
    }

    update2DAircraft(data) {
        // Clear existing aircraft markers
        this.aircraftMarkers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.aircraftMarkers.clear();
        
        // Clear existing route lines
        this.routeLines.forEach(line => {
            this.map.removeLayer(line);
        });
        this.routeLines.clear();

        if (!data.flights) return;

        // Add new aircraft markers with plane icons
        data.flights.forEach(flight => {
            const color = flight.color || 'red';
            
            // Calculate proper heading towards destination
            const heading = this.calculateProperHeading(flight);
            
            console.log(`✈️ Creating marker for ${flight.name} with heading ${heading}°`);
            
            // Create custom plane icon based on status
            const planeIcon = L.divIcon({
                className: 'aircraft-marker',
                html: `<i class="fas fa-plane" style="color: ${color}; font-size: 16px; transform: rotate(${heading}deg);"></i>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            
            const marker = L.marker([flight.lat, flight.lon], {
                icon: planeIcon
            }).addTo(this.map);

            // Check for weather impact at current location
            const weatherImpact = this.checkWeatherImpact(flight);
            
            marker.bindPopup(`
                <b>${flight.name}</b><br>
                Route: ${flight.route}<br>
                Status: ${flight.status}<br>
                Progress: ${flight.progress.toFixed(1)}%<br>
                Speed: ${flight.ground_speed} knots<br>
                Altitude: ${flight.altitude} ft<br>
                Heading: ${heading.toFixed(0)}°<br>
                ${weatherImpact.message ? `<br><span style="color: ${weatherImpact.color};">⚠️ ${weatherImpact.message}</span>` : ''}
            `);

            this.aircraftMarkers.set(flight.id, marker);
            
            // Add route line if enabled
            if (this.routeLinesVisible) {
                this.addRouteLineForFlight(flight);
            }
        });

        // Add resting aircraft markers
        this.addRestingAircraftMarkers(data.flights);
        
        // 📹 CAMERA FOLLOWING: Follow selected flight in 2D mode
        this.follow2DMapCamera(data.flights);

        // Update statistics
        this.updateFlightStats(data.flights);
    }
    
    follow2DMapCamera(flights) {
        // 📹 CAMERA FOLLOWING for 2D Map: Follow selected flight
        if (!this.selectedFlight || !flights || !this.map) {
            console.log(`🎥 2D SKIP: selectedFlight=${this.selectedFlight}, flights=${flights?.length}, map=${!!this.map}`);
            return;
        }
        
        // Find the selected flight
        const selectedFlight = flights.find(flight => flight.id === this.selectedFlight);
        if (!selectedFlight) {
            console.log(`🎥 2D SKIP: Selected flight ${this.selectedFlight} not found in current flights`);
            return;
        }
        
        console.log(`🎥 2D FOLLOW: Following flight ${selectedFlight.id} at ${selectedFlight.lat}, ${selectedFlight.lon} (${selectedFlight.status})`);
        
        // Follow the aircraft with smooth camera movement
        const currentZoom = this.map.getZoom();
        let targetZoom = currentZoom;
        
        // Adjust zoom based on flight status for better viewing
        switch (selectedFlight.status) {
            case 'parked':
                targetZoom = Math.max(12, currentZoom); // Close zoom for parked aircraft
                break;
            case 'departing':
            case 'arriving':
                targetZoom = Math.max(10, currentZoom); // Medium zoom for takeoff/landing
                break;
            case 'en_route':
                targetZoom = Math.min(8, currentZoom); // Wider view for cruising
                break;
        }
        
        // Smooth camera movement to follow the aircraft
        this.map.flyTo([selectedFlight.lat, selectedFlight.lon], targetZoom, {
            duration: 1.5, // Smooth 1.5 second transition
            easeLinearity: 0.5
        });
    }
    
    async addRestingAircraftMarkers(activeFlights) {
        try {
            // Get all route assignments to see which aircraft should be resting
            const assignments = await this.fetchAPI('/api/assignments');
            const aircraft = await this.fetchAPI('/api/aircraft');
            
            // Create a set of aircraft currently flying
            const flyingAircraftIds = new Set(activeFlights.map(f => f.aircraft_id));
            
            // Find aircraft with assignments that are not currently flying
            const restingAircraft = assignments.filter(assignment => 
                !flyingAircraftIds.has(assignment.aircraft_id) && assignment.active
            );
            
            // Create aircraft lookup map
            const aircraftMap = new Map(aircraft.map(a => [a.id, a]));
            
            // Add resting markers
            restingAircraft.forEach(assignment => {
                const aircraftInfo = aircraftMap.get(assignment.aircraft_id);
                if (!aircraftInfo) return;
                
                // Place aircraft at departure airport
                const airport = this.AIRPORTS[assignment.departure_airport];
                if (!airport) return;
                
                // Calculate next departure time (simplified)
                const nextDeparture = this.calculateNextDeparture(assignment);
                
                // Create resting aircraft icon
                const restingIcon = L.divIcon({
                    className: 'aircraft-marker resting-aircraft',
                    html: `<i class="fas fa-bed" style="color: #FFC107; font-size: 14px;"></i>`,
                    iconSize: [18, 18],
                    iconAnchor: [9, 9]
                });
                
                const marker = L.marker([airport.lat, airport.lon], {
                    icon: restingIcon
                }).addTo(this.map);
                
                marker.bindPopup(`
                    <b>🛏️ ${aircraftInfo.registration || `Aircraft-${assignment.aircraft_id}`}</b><br>
                    Status: Resting at ${assignment.departure_airport}<br>
                    Aircraft: ${aircraftInfo.airframeIcao || 'Unknown'}<br>
                    Route: ${assignment.departure_airport} → ${assignment.arrival_airport}<br>
                    Next Departure: ${nextDeparture}<br>
                    Frequency: ${assignment.frequency_weekly}/week
                `);
                
                this.aircraftMarkers.set(`resting-${assignment.aircraft_id}`, marker);
            });
            
        } catch (error) {
            console.error('❌ Error adding resting aircraft markers:', error);
        }
    }
    
    calculateNextDeparture(assignment) {
        // Calculate next departure time based on new single-flight system
        const now = Date.now() / 1000; // Current time in seconds
        const timeSpeed = this.timeSpeed || 1;
        const currentTime = now * timeSpeed;
        
        // Flight cycle parameters (matching backend logic)
        const cycleDurationHours = 168 / assignment.frequency_weekly;
        const cycleDurationSeconds = cycleDurationHours * 3600;
        
        // Estimate flight time (simplified calculation)
        const flightTimeHours = 1; // Simplified estimate for fast gameplay
        const flightTimeSeconds = flightTimeHours * 3600;
        
        // Current position in cycle
        const currentCycleTime = currentTime % cycleDurationSeconds;
        
        if (currentCycleTime < flightTimeSeconds) {
            // Currently flying - next departure is after rest period
            const timeToRest = flightTimeSeconds - currentCycleTime;
            const restTime = 0.5 * 3600; // 30 minutes rest
            const timeToNextDeparture = timeToRest + restTime;
            
            const nextDeparture = new Date((now + timeToNextDeparture / timeSpeed) * 1000);
            return this.formatTime(nextDeparture);
        } else {
            // Currently resting - next departure is at next cycle
            const timeToNextCycle = cycleDurationSeconds - currentCycleTime;
            const nextDeparture = new Date((now + timeToNextCycle / timeSpeed) * 1000);
            return this.formatTime(nextDeparture);
        }
    }

    formatTime(date) {
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    async toggle3DFlightMode() {
        console.log('🎲 Switching to 3D flight mode...');
        
        if (!this.map3D) {
            await this.init3DMap();
        }
        
        this.is3DMode = true;
        
        // Hide 2D map and legend, show 3D viewer
        document.getElementById('map').style.display = 'none';
        document.getElementById('flight-3d-viewer').style.display = 'block';
        document.querySelector('.legend').style.display = 'none'; // Hide legend in 3D mode
        
        // Toggle button visibility
        document.getElementById('toggle-3d-flight').style.display = 'none';
        document.getElementById('toggle-2d-map').style.display = 'inline-block';
        
        // Show real aircraft immediately if available
        if (this.currentFlights.length > 0) {
            console.log(`🛩️ Adding ${this.currentFlights.length} real aircraft to 3D scene`);
            this.update3DAircraft({ flights: this.currentFlights });
            
            // Center map on first aircraft
            const firstFlight = this.currentFlights[0];
            this.map3D.setCenter([firstFlight.lon, firstFlight.lat]);
            this.map3D.setZoom(8);
            this.map3D.setPitch(60);
        } else {
            console.log('⚠️ No flights available yet - waiting for real-time data');
            // Show message while waiting for flights
            const container = document.getElementById('flight-3d-container');
            const loadingDiv = container.querySelector('.aircraft-3d-loading');
            if (loadingDiv) {
                loadingDiv.innerHTML = '<i class="fas fa-plane"></i> Waiting for flight data...';
                loadingDiv.style.display = 'block';
            }
        }
        
        console.log('✅ 3D flight mode activated');
    }

    toggle2DMapMode() {
        console.log('🗺️ Switching to 2D map mode...');
        
        this.is3DMode = false;
        this.isGlobeMode = false;
        
        // Show 2D map and legend, hide 3D and globe viewers
        document.getElementById('map').style.display = 'block';
        document.getElementById('flight-3d-viewer').style.display = 'none';
        document.getElementById('globe-flight-viewer').style.display = 'none';
        document.querySelector('.legend').style.display = 'block'; // Show legend in 2D mode
        
        // Toggle button visibility
        document.getElementById('toggle-3d-flight').style.display = 'inline-block';
        document.getElementById('toggle-globe-mode').style.display = 'inline-block';
        document.getElementById('toggle-2d-map').style.display = 'none';
        document.getElementById('toggle-free-camera').style.display = 'none';
        
        console.log('✅ 2D map mode activated');
    }

    async toggleGlobeFlightMode() {
        console.log('🌍 Switching to Globe Flight mode...');
        
        // Set mode flags first
        this.isGlobeMode = true;
        this.is3DMode = false;
        
        // Always update UI regardless of globe initialization success
        // Hide 2D map, 3D viewer, and legend; show globe viewer
        document.getElementById('map').style.display = 'none';
        document.getElementById('flight-3d-viewer').style.display = 'none';
        document.getElementById('globe-flight-viewer').style.display = 'block';
        document.querySelector('.legend').style.display = 'none'; // Hide legend in globe mode
        
        // Toggle button visibility - ALWAYS show free camera button in globe mode
        document.getElementById('toggle-3d-flight').style.display = 'none';
        document.getElementById('toggle-globe-mode').style.display = 'none';
        document.getElementById('toggle-2d-map').style.display = 'inline-block';
        document.getElementById('toggle-free-camera').style.display = 'inline-block';
        
        // Try to initialize globe map if not already done
        if (!this.globeMap) {
            try {
                await this.initGlobeMap();
                // Setup globe controls only if initialization succeeds
                this.setupGlobeControls();
            } catch (error) {
                console.error('❌ Globe initialization failed, but UI is still functional:', error);
                // Show a message in the globe container
                const container = document.getElementById('globe-flight-container');
                container.innerHTML = `
                    <div class="globe-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Globe View Not Available</h3>
                        <p>3D Globe mode requires MapTiler API key. Free camera controls are still available.</p>
                        <p>You can still use the 2D map with all flight tracking features.</p>
                    </div>
                `;
            }
        } else {
            // Setup globe controls if map already exists
            this.setupGlobeControls();
        }
        
        console.log('✅ Globe Flight mode activated (UI ready, free camera available)');
    }

    toggleFreeCamera() {
        this.freeCameraMode = !this.freeCameraMode;
        const button = document.getElementById('toggle-free-camera');
        
        if (this.freeCameraMode) {
            // Enable free camera mode
            button.classList.add('active');
            button.innerHTML = '<i class="fas fa-video"></i> Free Camera ON';
            console.log('🎥 FREE CAMERA MODE: Enabled - You control the camera!');
        } else {
            // Disable free camera mode
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-video"></i> Free Camera';
            console.log('📹 AUTO CAMERA MODE: Enabled - Camera follows aircraft automatically');
        }
    }

    async initGlobeMap() {
        try {
            console.log('🌍 Initializing Globe Flight Map...');
            
            // Remove loading indicator
            const loadingElement = document.querySelector('.globe-loading');
            if (loadingElement) {
                loadingElement.remove();
            }
            
            // Configure MapTiler SDK
            maptilersdk.config.apiKey = this.maptilerApiKey;
            
            // Create globe map container
            const globeContainer = document.getElementById('globe-flight-container');
            const mapContainer = document.createElement('div');
            mapContainer.id = 'globe-map-container';
            globeContainer.appendChild(mapContainer);
            
            // Initialize MapTiler globe map exactly like tutorial
            const paris = [2.3120283730734648, 48.8556923989924];
            
            this.globeMap = new maptilersdk.Map({
                container: 'globe-map-container',
                style: maptilersdk.MapStyle.STREETS.DARK, // Dark theme like tutorial
                zoom: 2,
                center: paris,
                maptilerLogo: true,
                maxPitch: 95,
                pitch: 71,
                hash: false,
                projection: 'globe' // Enable globe projection
            });
            
            await this.globeMap.onReadyAsync();
            
            // Add 3D layer for aircraft
            this.globeLayer3D = new maptiler3d.Layer3D("globe-aircraft-layer");
            this.globeMap.addLayer(this.globeLayer3D);
            
            // Configure lighting exactly like tutorial
            this.globeLayer3D.setAmbientLight({intensity: 2});
            this.globeLayer3D.addPointLight("point-light", {intensity: 30});
            
            console.log('✅ Globe map initialized');
            
        } catch (error) {
            console.error('❌ Globe map initialization error:', error);
            const container = document.getElementById('globe-flight-container');
            container.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #ff6b6b;">
                    <div style="text-align: center;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h3>Globe Mode Error</h3>
                        <p>Failed to initialize globe flight mode</p>
                        <button onclick="tracker.toggle2DMapMode()" style="
                            background: #007bff; color: white; border: none; 
                            padding: 10px 20px; border-radius: 5px; cursor: pointer;
                        ">Back to 2D Map</button>
                    </div>
                </div>
            `;
        }
    }

    setupGlobeControls() {
        // Show real aircraft immediately if available
        if (this.currentFlights.length > 0) {
            console.log(`🛩️ Adding ${this.currentFlights.length} real aircraft to globe scene`);
            this.updateGlobeAircraft({ flights: this.currentFlights });
            
            // Center globe on first aircraft
            const firstFlight = this.currentFlights[0];
            this.globeMap.flyTo({
                center: [firstFlight.lon, firstFlight.lat],
                zoom: 6,
                pitch: 71,
                duration: 2000
            });
        } else {
            console.log('⚠️ No flights available yet - waiting for real-time data');
        }
    }

    async updateGlobeAircraft(data) {
        if (!this.globeLayer3D || !data.flights) return;

        // Remove loading indicator when we have real flights
        const loadingElement = document.querySelector('.globe-loading');
        if (loadingElement) {
            loadingElement.remove();
        }

        try {
            console.log(`🌍 GLOBE UPDATE: Processing ${data.flights.length} flights - selectedFlight: ${this.selectedFlight}`);
            for (const flight of data.flights) {
                const aircraftId = `globe-aircraft-${flight.id}`;
                console.log(`🌍 PROCESSING: Flight ID ${flight.id} -> Aircraft ID ${aircraftId}`);
                
                // Check if aircraft already exists
                const existingAircraft = this.aircraft3DModels.has(aircraftId);
                
                if (!existingAircraft) {
                    // Calculate proper heading towards arrival airport
                    const properHeading = this.calculateProperHeading(flight);
                    
                    // Calculate altitude-based scale and position for 3D effect with auto-zoom
                    const altitudeMeters = flight.altitude_meters || (flight.altitude * 0.3048) || 10000;
                    const { scale, visualAltitude, cameraZoom } = this.calculateAircraftScale(flight, altitudeMeters);
                    
                    console.log(`🛫 Aircraft ${flight.id} at ${flight.altitude}ft (${altitudeMeters}m), scale: ${scale}, status: ${flight.status}`);
                    
                    // Add new aircraft to globe with realistic 3D positioning
                    await this.globeLayer3D.addMeshFromURL(
                        aircraftId,
                        "/static/models/aircraft/a340.glb", // Your local file
                        {
                            lngLat: [flight.lon, flight.lat],
                            heading: properHeading,
                            scale: scale, // Dynamic scale based on altitude
                            altitude: visualAltitude, // Realistic altitude for 3D positioning
                            altitudeReference: maptiler3d.AltitudeReference.MEAN_SEA_LEVEL,
                        }
                    );
                    
                    // 📹 AUTO-ZOOM: Adjust camera zoom to maintain aircraft visibility
                    this.autoZoomForAircraft(flight, cameraZoom);
                    
                    this.aircraft3DModels.set(aircraftId, {
                        flight: flight,
                        lastUpdate: Date.now()
                    });
                    
                    console.log(`✈️ Added aircraft ${flight.id} to globe at ${flight.lat}, ${flight.lon}`);
                } else {
                    // Calculate proper heading towards arrival airport
                    const properHeading = this.calculateProperHeading(flight);
                    
                    // Calculate altitude-based scale and position for 3D effect with auto-zoom
                    const altitudeMeters = flight.altitude_meters || (flight.altitude * 0.3048) || 10000;
                    const { scale, visualAltitude, cameraZoom } = this.calculateAircraftScale(flight, altitudeMeters);
                    
                    // Update existing aircraft position with dynamic scaling
                    this.globeLayer3D.modifyMesh(aircraftId, {
                        lngLat: [flight.lon, flight.lat],
                        heading: properHeading,
                        scale: scale, // Dynamic scale based on altitude
                        altitude: visualAltitude // Realistic altitude for 3D positioning
                    });
                    
                    // 📹 AUTO-ZOOM: Adjust camera zoom to maintain aircraft visibility
                    this.autoZoomForAircraft(flight, cameraZoom);
                    
                    // Update stored data
                    this.aircraft3DModels.set(aircraftId, {
                        flight: flight,
                        lastUpdate: Date.now()
                    });
                    
                    // 📹 CAMERA FOLLOWING: Follow aircraft during landing/takeoff for dramatic effect
                    this.followAircraftIfLandingOrTakeoff(flight);
                }
            }

            // Remove aircraft that are no longer in the data
            const currentFlightIds = new Set(data.flights.map(f => `globe-aircraft-${f.id}`));
            for (const [aircraftId, aircraftData] of this.aircraft3DModels.entries()) {
                if (!currentFlightIds.has(aircraftId) && aircraftId.startsWith('globe-aircraft-')) {
                    try {
                        this.globeLayer3D.removeMesh(aircraftId);
                        this.aircraft3DModels.delete(aircraftId);
                        console.log(`🗑️ Removed aircraft ${aircraftId} from globe`);
                    } catch (error) {
                        console.error(`❌ Error removing aircraft ${aircraftId}:`, error);
                    }
                }
            }

            // Follow the selected flight if tracking is enabled
            if (this.followingFlight) {
                const updatedFlight = data.flights.find(f => f.id === this.followingFlight.id);
                if (updatedFlight) {
                    this.globeMap.flyTo({
                        center: [updatedFlight.lon, updatedFlight.lat],
                        pitch: 71,
                        zoom: 8,
                        duration: 1000
                    });
                    this.followingFlight = updatedFlight; // Update position
                }
            }

        } catch (error) {
            console.error('❌ Error updating globe aircraft:', error);
        }
    }
    
    setupGlobeClickHandler() {
        console.log('✅ Globe click handlers setup');
    }
    
    followFlightOnGlobe(flight) {
        if (!flight || !this.globeMap) return;
        
        console.log(`📹 Following flight ${flight.id} on globe`);
        
        this.globeMap.flyTo({
            center: [flight.lon, flight.lat],
            pitch: 71,
            zoom: 8,
            duration: 1500
        });
        
        // Store the followed flight for continued tracking
        this.followingFlight = flight;
    }

    async init3DMap() {
        try {
            console.log('🎲 Initializing 3D map...');
            
            // Remove loading indicator immediately
            const loadingElement = document.querySelector('.aircraft-3d-loading');
            if (loadingElement) {
                loadingElement.style.display = 'none';
                console.log('✅ Loading indicator hidden');
            }
            
            // Check if MapTiler SDK is loaded
            console.log('🔍 Checking MapTiler SDK...', typeof maptilersdk, typeof maptiler3d);
            
            // Set MapTiler API key
            if (typeof maptilersdk !== 'undefined') {
                maptilersdk.config.apiKey = this.maptilerApiKey;
                console.log('🔑 API key set:', this.maptilerApiKey);
            } else {
                throw new Error('MapTiler SDK not loaded');
            }
            
            if (typeof maptiler3d === 'undefined') {
                throw new Error('MapTiler 3D SDK not loaded');
            }
            
            // Initialize 3D map - will center on actual flights later
            const defaultCenter = [-73.7781, 40.6413]; // JFK as default
            console.log('🗺️ Creating map...');
            
            this.map3D = new maptilersdk.Map({
                container: 'flight-3d-container',
                style: maptilersdk.MapStyle.STREETS.DARK,
                zoom: 6, // Lower zoom to see larger area
                center: defaultCenter,
                maxPitch: 85,
                terrainControl: true,
                terrain: true,
                terrainExaggeration: 0.001,
                maptilerLogo: true,
            });

            console.log('⏳ Waiting for map to be ready...');
            await this.map3D.onReadyAsync();
            console.log('✅ Map ready!');

            // Configure sky and atmosphere
            this.map3D.setSky({
                "sky-color": "#0C2E4B",
                "horizon-color": "#09112F",
                "fog-color": "#09112F",
                "fog-ground-blend": 0.5,
                "horizon-fog-blend": 0.1,
                "sky-horizon-blend": 1.0,
                "atmosphere-blend": 0.5,
            });
            console.log('🌌 Sky configured');

            // Add 3D layer
            this.layer3D = new maptiler3d.Layer3D("aircraft-3d-layer");
            this.map3D.addLayer(this.layer3D);
            console.log('🏗️ 3D layer added');

            // Configure lighting
            this.layer3D.setAmbientLight({ intensity: 2 });
            this.layer3D.addPointLight("point-light", { intensity: 30 });
            console.log('💡 Lighting configured');

            console.log('✅ 3D map fully initialized');
            
        } catch (error) {
            console.error('❌ 3D Map initialization failed:', error);
            
            // Show error message instead of loading
            const container = document.getElementById('flight-3d-container');
            if (container) {
                container.innerHTML = `
                    <div style="
                        position: absolute; top: 50%; left: 50%; 
                        transform: translate(-50%, -50%);
                        background: rgba(255, 0, 0, 0.8); 
                        color: white; padding: 20px; 
                        border-radius: 8px; text-align: center;
                    ">
                        <h3>❌ 3D View Failed to Load</h3>
                        <p>Error: ${error.message}</p>
                        <p>Check browser console for details</p>
                        <button onclick="tracker.toggle2DMapMode()" style="
                            background: #007bff; color: white; border: none; 
                            padding: 10px 20px; border-radius: 5px; cursor: pointer;
                        ">Back to 2D Map</button>
                    </div>
                `;
            }
        }
    }


    async update3DAircraft(data) {
        if (!this.layer3D || !data.flights) return;

        // Remove loading indicator when we have real flights
        const loadingElement = document.querySelector('.aircraft-3d-loading');
        if (loadingElement && data.flights.length > 0) {
            loadingElement.style.display = 'none';
            console.log(`📡 Showing ${data.flights.length} real aircraft in 3D`);
        }

        // Store current flights for state management
        this.currentFlights = data.flights;

        // Update each aircraft with route-based animation
        for (const flight of data.flights) {
            const modelId = `aircraft-${flight.id}`;
            
            try {
                // Check if aircraft model already exists
                if (!this.aircraft3DModels.has(flight.id)) {
                    // Add new aircraft model using local A321 model
                    await this.layer3D.addMeshFromURL(
                        modelId,
                        "/static/models/aircraft/a321.glb",
                        {
                            lngLat: [flight.lon, flight.lat],
                            heading: flight.heading || 0,
                            scale: 200, // Much larger scale for maximum visibility
                            altitude: 5000, // Lower altitude for better visibility
                            altitudeReference: maptiler3d.AltitudeReference.MEAN_SEA_LEVEL,
                        }
                    );
                    
                    this.aircraft3DModels.set(flight.id, {
                        modelId: modelId,
                        flight: flight,
                        departureAirport: [flight.dep_airport_lon || flight.lon, flight.dep_airport_lat || flight.lat],
                        arrivalAirport: [flight.arr_airport_lon || flight.lon, flight.arr_airport_lat || flight.lat]
                    });
                    
                    console.log(`✈️ Added 3D aircraft: ${flight.id} at real position [${flight.lon}, ${flight.lat}]`);
                } else {
                    // Update existing aircraft position with smooth animation
                    const aircraftData = this.aircraft3DModels.get(flight.id);
                    
                    // Calculate heading based on movement direction
                    const heading = this.calculateHeading(aircraftData.flight, flight);
                    
                    this.layer3D.modifyMesh(modelId, {
                        lngLat: [flight.lon, flight.lat],
                        heading: heading,
                        altitude: 5000 // Keep at visible altitude
                    });
                    
                    // Update stored flight data
                    aircraftData.flight = flight;
                    
                    console.log(`🔄 Updated aircraft ${flight.id} to [${flight.lon}, ${flight.lat}] heading: ${heading.toFixed(1)}°`);
                }

            } catch (error) {
                console.error(`❌ Error updating 3D aircraft ${flight.id}:`, error);
            }
        }

        // Remove aircraft that are no longer active
        this.aircraft3DModels.forEach((aircraftData, flightId) => {
            const stillActive = data.flights.find(f => f.id === flightId);
            if (!stillActive) {
                try {
                    this.layer3D.removeMesh(aircraftData.modelId);
                    this.aircraft3DModels.delete(flightId);
                    console.log(`🗑️ Removed inactive aircraft: ${flightId}`);
                } catch (error) {
                    console.error(`❌ Error removing aircraft ${flightId}:`, error);
                }
            }
        });

        // Update flight statistics
        this.updateFlightStats(data.flights);
    }

    calculateHeading(oldFlight, newFlight) {
        // Calculate heading based on movement direction
        if (!oldFlight) return newFlight.heading || 0;
        
        const deltaLat = newFlight.lat - oldFlight.lat;
        const deltaLon = newFlight.lon - oldFlight.lon;
        
        if (Math.abs(deltaLat) < 0.0001 && Math.abs(deltaLon) < 0.0001) {
            return newFlight.heading || 0; // No movement, keep current heading
        }
        
        let heading = Math.atan2(deltaLon, deltaLat) * 180 / Math.PI;
        if (heading < 0) heading += 360;
        
        return heading;
    }


    updateFlightStats(flights) {
        const stats = {
            total: flights.length,
            departing: flights.filter(f => f.status === 'departing').length,
            enroute: flights.filter(f => f.status === 'en_route').length,
            arriving: flights.filter(f => f.status === 'arriving').length
        };

        document.getElementById('total-flights').textContent = stats.total;
        document.getElementById('departing-flights').textContent = stats.departing;
        document.getElementById('enroute-flights').textContent = stats.enroute;
        document.getElementById('arriving-flights').textContent = stats.arriving;

        // Update flights list
        const flightsList = document.getElementById('flights-list');
        if (flights.length === 0) {
            flightsList.innerHTML = '<div class="no-data">No active flights</div>';
        } else {
            flightsList.innerHTML = flights.map(flight => {
                const isSelected = this.selectedFlight === flight.id;
                console.log(`🎨 RENDER: Flight ${flight.id} - isSelected: ${isSelected}, selectedFlight: ${this.selectedFlight}`);
                
                const html = `
                <div class="flight-item ${isSelected ? 'selected' : ''}" 
                     onclick="tracker.selectFlight('${flight.id}')" 
                     style="cursor: pointer;" 
                     data-flight-id="${flight.id}" 
                     data-selected="${isSelected}">
                    <div class="flight-header">
                        <div class="flight-title">
                            <i class="fas fa-${isSelected ? 'video' : 'plane'}"></i>
                            <strong>${flight.name}</strong>
                            ${isSelected ? '<span class="camera-indicator">📹 Camera Locked</span>' : ''}
                        </div>
                        <span class="flight-status ${flight.status}">${flight.status}</span>
                    </div>
                    <div class="flight-details">
                        <div>Route: ${flight.route}</div>
                        <div>Progress: ${flight.progress.toFixed(1)}%</div>
                        <div>Speed: ${flight.ground_speed} kt</div>
                        <div>Alt: ${flight.altitude} ft</div>
                    </div>
                </div>
                `;
                
                if (isSelected) {
                    console.log(`✅ SELECTED HTML for ${flight.id}:`, html.substring(0, 100) + '...');
                }
                
                return html;
            }).join('');
        }
        
        // Update route assignments display if Routes tab is active
        this.updateRouteAssignmentsIfVisible();
    }
    
    updateRouteAssignmentsIfVisible() {
        // Check if routes tab is active
        const routesTab = document.getElementById('routes-tab');
        if (routesTab && routesTab.classList.contains('active')) {
            // Refresh assignments display to update flight statuses
            this.refreshRouteAssignments();
        }
    }
    
    async refreshRouteAssignments() {
        try {
            const [fleetAircraft, routes, assignments] = await Promise.all([
                this.fetchAPI('/api/aircraft'),
                this.fetchAPI('/api/routes'),
                this.fetchAPI('/api/assignments')
            ]);
            
            this.displayRouteAssignments(assignments, fleetAircraft, routes);
        } catch (error) {
            console.error('❌ Error refreshing route assignments:', error);
        }
    }

    focusOnFlight(flightId) {
        const flight = this.currentFlights.find(f => f.id === flightId);
        if (!flight) return;

        if (this.isGlobeMode && this.globeMap) {
            // Globe mode: follow flight like 3D mode
            this.followFlightOnGlobe(flight);
            console.log(`🌍 Focused on flight: ${flightId} in globe mode`);
        } else if (this.is3DMode && this.map3D) {
            // Tutorial-style route animation: center on aircraft and follow
            this.map3D.setCenter([flight.lon, flight.lat]);
            this.map3D.setZoom(8); // Good zoom level to see aircraft
            this.map3D.setPitch(60); // Nice 3D angle
            
            // Set this flight as the one to follow
            this.followingFlight = flight;
            
            // Start following the flight automatically (like tutorial's trackFlight)
            this.startFlightTracking(flight);
            
            console.log(`🎯 Focused on flight: ${flightId} - now tracking route`);
        } else if (this.map) {
            this.map.setView([flight.lat, flight.lon], 8);
            console.log(`🎯 Focused on flight: ${flightId}`);
        }
    }

    startFlightTracking(flight) {
        // Implement tutorial-style tracking
        if (this.flightTrackingInterval) {
            clearInterval(this.flightTrackingInterval);
        }
        
        this.flightTrackingInterval = setInterval(() => {
            if (this.followingFlight && this.map3D && this.is3DMode) {
                const currentFlight = this.currentFlights.find(f => f.id === this.followingFlight.id);
                if (currentFlight) {
                    // Smoothly follow the aircraft like in the tutorial
                    this.map3D.setCenter([currentFlight.lon, currentFlight.lat]);
                    // Optional: rotate the bearing slightly for dynamic effect
                    // this.map3D.setBearing(360 * currentFlight.progress / 100);
                }
            }
        }, 1000); // Update every second for smooth tracking
    }

    async loadRoutesData() {
        try {
            console.log('📊 Loading routes data...');
            
            // Load both fleet aircraft and owned aircraft, routes, and existing assignments
            const [fleetAircraft, ownedAircraft, routes, assignments] = await Promise.all([
                this.fetchAPI('/api/aircraft'),
                this.fetchAPI('/api/owned_aircraft'), 
                this.fetchAPI('/api/routes'),
                this.fetchAPI('/api/assignments')
            ]);
            
            console.log('✈️ Fleet aircraft loaded:', fleetAircraft.length);
            console.log('🛒 Owned aircraft loaded:', ownedAircraft.length);
            console.log('🗺️ Routes loaded:', routes.length);
            console.log('📋 Assignments loaded:', assignments.length);
            
            // Populate aircraft dropdown with fleet aircraft (needed for assignments)
            const aircraftSelect = document.getElementById('aircraft-select');
            aircraftSelect.innerHTML = '<option value="">Select Aircraft</option>';
            
            fleetAircraft.forEach(plane => {
                const option = document.createElement('option');
                option.value = plane.id;
                option.textContent = `${plane.registration || plane.id} (${plane.airframeIcao || 'A321'})`;
                aircraftSelect.appendChild(option);
            });
            
            // Populate routes dropdown
            const routeSelect = document.getElementById('route-select');
            routeSelect.innerHTML = '<option value="">Select Route</option>';
            
            routes.forEach(route => {
                const option = document.createElement('option');
                option.value = route.id;
                option.textContent = `${route.departure_airport} → ${route.arrival_airport} (${route.distance_nm} nm)`;
                routeSelect.appendChild(option);
            });
            
            // Display existing route assignments (using both fleet and owned aircraft for lookup)
            // Combine fleet and owned aircraft for better lookup
            const allAircraft = [...fleetAircraft];
            
            // Add owned aircraft that might not be in fleet yet
            ownedAircraft.forEach(owned => {
                if (!fleetAircraft.find(fleet => fleet.id === owned.id)) {
                    // Convert owned aircraft format to fleet format
                    allAircraft.push({
                        id: owned.id,
                        registration: owned.registration || owned.id,
                        airframeIcao: owned.airframeIcao || owned.model || 'A321',
                        model: owned.model
                    });
                }
            });
            
            this.displayRouteAssignments(assignments, allAircraft, routes);
            
            // Add route analysis functionality
            this.setupRouteAnalysis();
            
        } catch (error) {
            console.error('❌ Error loading routes data:', error);
        }
    }

    async loadFleetData() {
        try {
            console.log('🚁 Loading fleet data...');
            
            // Try to get owned aircraft from the marketplace API
            const response = await fetch('/api/owned_aircraft');
            let ownedAircraft = [];
            
            if (response.ok) {
                ownedAircraft = await response.json();
            } else {
                // Fallback: get from regular aircraft API
                const allAircraft = await this.fetchAPI('/api/aircraft');
                ownedAircraft = allAircraft; // Show all aircraft as owned for now
            }
            
            console.log('✈️ Owned aircraft:', ownedAircraft.length);
            
            const fleetList = document.getElementById('fleet-list');
            
            if (ownedAircraft.length === 0) {
                fleetList.innerHTML = '<div class="no-data">No aircraft in fleet. Purchase aircraft from the marketplace!</div>';
                return;
            }
            
            fleetList.innerHTML = ownedAircraft.map(aircraft => `
                <div class="fleet-item">
                    <h5>${aircraft.registration || aircraft.id}</h5>
                    <div class="aircraft-details">
                        <p><strong>Model:</strong> ${aircraft.airframeIcao || aircraft.model || 'A321'}</p>
                        <p><strong>Location:</strong> ${aircraft.logLocation || aircraft.location || 'JFK'}</p>
                        <p><strong>Status:</strong> ${aircraft.status || 'Active'}</p>
                        ${aircraft.purchase_price ? `<p><strong>Value:</strong> $${aircraft.purchase_price.toFixed(1)}M</p>` : ''}
                        ${aircraft.monthly_payment ? `<p><strong>Monthly Payment:</strong> $${aircraft.monthly_payment.toFixed(1)}k</p>` : ''}
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            console.error('❌ Error loading fleet data:', error);
            const fleetList = document.getElementById('fleet-list');
            fleetList.innerHTML = '<div class="no-data">Error loading fleet data</div>';
        }
    }

    displayRouteAssignments(assignments, aircraft, routes) {
        const assignmentsList = document.getElementById('assignments-list');
        
        if (assignments.length === 0) {
            assignmentsList.innerHTML = '<div class="no-data">No route assignments yet</div>';
            return;
        }
        
        // Create a map for quick aircraft and route lookups
        const aircraftMap = new Map(aircraft.map(a => [String(a.id), a])); // Ensure string keys
        const routesMap = new Map(routes.map(r => [r.id, r]));
        
        // Debug logging
        console.log('🔍 Debug - Aircraft IDs in map:', Array.from(aircraftMap.keys()));
        console.log('🔍 Debug - Assignment aircraft IDs:', assignments.map(a => String(a.aircraft_id)));
        
        assignmentsList.innerHTML = assignments.map(assignment => {
            const aircraftIdStr = String(assignment.aircraft_id);
            const aircraftInfo = aircraftMap.get(aircraftIdStr) || { 
                registration: `Aircraft-${assignment.aircraft_id}`, 
                airframeIcao: 'Unknown',
                id: assignment.aircraft_id
            };
            
            // Debug log for missing aircraft
            if (!aircraftMap.get(aircraftIdStr)) {
                console.warn(`⚠️ Aircraft ID ${aircraftIdStr} not found in fleet data. Available IDs:`, Array.from(aircraftMap.keys()));
                console.info('💡 Tip: Click "Sync Aircraft Fleet" button to synchronize owned aircraft to fleet database');
            }
            
            // Check if aircraft is currently flying (simplified check)
            const isFlying = this.isAircraftFlying(assignment.aircraft_id);
            const canDelete = !isFlying;
            
            return `
                <div class="assignment-item">
                    <div class="assignment-header">
                        <div class="assignment-title">
                            ${aircraftInfo.registration || aircraftInfo.id} → ${assignment.departure_airport}-${assignment.arrival_airport}
                        </div>
                        <div class="assignment-actions">
                            ${canDelete ? 
                                `<button class="btn btn-danger btn-sm" onclick="tracker.removeAssignment('${assignment.aircraft_id}', '${assignment.route_id}')">
                                    <i class="fas fa-trash"></i> Remove
                                </button>` :
                                `<button class="btn btn-secondary btn-sm" disabled title="Cannot remove while aircraft is flying">
                                    <i class="fas fa-plane"></i> Flying
                                </button>`
                            }
                        </div>
                    </div>
                    <div class="assignment-details">
                        <p><strong>Aircraft:</strong> ${aircraftInfo.airframeIcao || aircraftInfo.model || 'Unknown Model'} ${aircraftInfo.airframeIcao === 'Unknown' ? '(⚠️ Sync Fleet)' : ''}</p>
                        <p><strong>Distance:</strong> ${assignment.distance_nm || 'N/A'} nm</p>
                        <p><strong>Frequency:</strong> ${assignment.frequency_weekly}/week</p>
                        <p><strong>Economy:</strong> $${assignment.fare_economy}</p>
                        <p><strong>Business:</strong> $${assignment.fare_business}</p>
                        <p><strong>Status:</strong> ${isFlying ? '✈️ In Flight' : '🏠 At Gate'}</p>
                    </div>
                </div>
            `;
        }).join('');
    }

    selectFlight(flightId) {
        console.log(`🖱️ CLICK: User clicked flight ${flightId}`);
        console.log(`🔍 DEBUG: Current selectedFlight = ${this.selectedFlight}`);
        console.log(`🔍 DEBUG: Clicked flight ID = ${flightId}`);
        console.log(`🔍 DEBUG: Are they equal? ${this.selectedFlight === flightId}`);
        
        // Toggle flight selection
        if (this.selectedFlight === flightId) {
            // Deselect if already selected - switch to free camera
            this.selectedFlight = null;
            console.log(`📹 FREE CAMERA: Deselected flight ${flightId}, camera is now free to move`);
        } else {
            // Select new flight - lock camera to this flight
            this.selectedFlight = flightId;
            console.log(`📹 CAMERA LOCKED: Selected flight ${flightId}, camera will follow this aircraft`);
        }
        
        console.log(`🔍 DEBUG: After toggle, selectedFlight = ${this.selectedFlight}`);
        
        // Immediately update visual state without waiting for full refresh
        this.updateFlightSelectionVisuals();
    }
    
    updateFlightSelectionVisuals() {
        console.log(`🎨 UPDATE VISUALS: selectedFlight = ${this.selectedFlight}`);
        
        const allFlightItems = document.querySelectorAll('.flight-item');
        allFlightItems.forEach(item => {
            const flightId = item.getAttribute('data-flight-id');
            const titleDiv = item.querySelector('.flight-title');
            const icon = item.querySelector('.flight-title i');
            
            if (flightId === this.selectedFlight) {
                // Make this flight selected
                console.log(`🎨 SELECTING: ${flightId}`);
                item.classList.add('selected');
                if (icon) icon.className = 'fas fa-video';
                
                // Add camera indicator if not present
                let cameraIndicator = item.querySelector('.camera-indicator');
                if (!cameraIndicator && titleDiv) {
                    cameraIndicator = document.createElement('span');
                    cameraIndicator.className = 'camera-indicator';
                    cameraIndicator.textContent = '📹 Camera Locked';
                    titleDiv.appendChild(cameraIndicator);
                }
            } else {
                // Make this flight unselected
                console.log(`🎨 DESELECTING: ${flightId}`);
                item.classList.remove('selected');
                if (icon) icon.className = 'fas fa-plane';
                
                // Remove camera indicator if present
                const cameraIndicator = item.querySelector('.camera-indicator');
                if (cameraIndicator) {
                    cameraIndicator.remove();
                }
            }
        });
    }

    isAircraftFlying(aircraftId) {
        // Check if the aircraft is currently in flight
        if (!this.currentFlights || this.currentFlights.length === 0) {
            return false;
        }
        
        // Look for active flights using this aircraft
        const activeFlights = this.currentFlights.filter(flight => 
            flight.aircraft_id == aircraftId && 
            (flight.status === 'en_route' || flight.status === 'departing' || flight.status === 'arriving')
        );
        
        return activeFlights.length > 0;
    }


    async removeAssignment(aircraftId, routeId, showConfirm = true) {
        // Check if aircraft is currently flying
        if (this.isAircraftFlying(aircraftId)) {
            alert('❌ Cannot remove route assignment while aircraft is in flight. Please wait for the aircraft to land.');
            return;
        }
        
        if (showConfirm && !confirm('Are you sure you want to remove this route assignment?')) {
            return;
        }
        
        try {
            console.log(`🗑️ Removing assignment: Aircraft ${aircraftId}, Route ${routeId}`);
            
            const response = await fetch('/api/remove_assignment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    aircraft_id: aircraftId,
                    route_id: routeId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (showConfirm) {
                    alert(`✅ ${result.message}`);
                }
                // Refresh the routes data
                this.loadRoutesData();
                this.loadEconomics();
            } else {
                alert(`❌ ${result.message || 'Failed to remove assignment'}`);
            }
            
        } catch (error) {
            console.error('❌ Error removing assignment:', error);
            if (showConfirm) {
                alert('❌ Error removing assignment');
            }
        }
    }

    resetAssignmentForm() {
        document.getElementById('aircraft-select').value = '';
        document.getElementById('route-select').value = '';
        document.getElementById('frequency-input').value = 7;
        document.getElementById('fare-input').value = 250;
        
        // Hide analysis
        document.getElementById('route-analysis').style.display = 'none';
    }

    async assignRoute() {
        // Prevent duplicate calls
        if (this.isAssigningRoute) {
            console.log('❌ Route assignment already in progress, ignoring duplicate call');
            return;
        }
        
        const aircraftId = document.getElementById('aircraft-select').value;
        const routeId = document.getElementById('route-select').value;
        const frequency = parseInt(document.getElementById('frequency-input').value) || 7;
        const economyFare = parseInt(document.getElementById('fare-input').value) || 250;
        const businessFare = Math.round(economyFare * 3.5);
        
        if (!aircraftId || !routeId) {
            alert('Please select both aircraft and route');
            return;
        }
        
        this.isAssigningRoute = true;
        const assignButton = document.getElementById('assign-route');
        const originalText = assignButton.innerHTML;
        assignButton.disabled = true;
        assignButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Assigning...';
        
        try {
            // First check if aircraft is already assigned
            const existingAssignments = await this.fetchAPI('/api/assignments');
            const existingAssignment = existingAssignments.find(a => 
                a.aircraft_id == aircraftId && a.active === 1
            );
            
            if (existingAssignment) {
                alert(`❌ Aircraft is already assigned to route ${existingAssignment.departure_airport} → ${existingAssignment.arrival_airport}. Please remove the existing assignment first.`);
                return;
            }
            
            console.log(`🛩️ Assigning aircraft ${aircraftId} to route ${routeId}`);
            
            const response = await fetch('/api/assign_route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    aircraft_id: aircraftId,
                    route_id: routeId,
                    frequency: frequency,
                    economy_fare: economyFare,
                    business_fare: businessFare
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(`✅ ${result.message}`);
                // Refresh routes data and economics
                this.loadRoutesData();
                this.loadEconomics();
                // Reset form
                this.resetAssignmentForm();
            } else {
                alert(`❌ ${result.message || 'Assignment failed'}`);
            }
            
        } catch (error) {
            console.error('❌ Route assignment error:', error);
            alert('❌ Route assignment failed');
        } finally {
            this.isAssigningRoute = false;
            assignButton.disabled = false;
            assignButton.innerHTML = originalText;
        }
    }

    setupRouteAnalysis() {
        const routeSelect = document.getElementById('route-select');
        const frequencyInput = document.getElementById('frequency-input');
        const fareInput = document.getElementById('fare-input');
        const analysisDiv = document.getElementById('route-analysis');
        const assignButton = document.getElementById('assign-route');
        
        // Show analysis when route is selected
        const showAnalysis = async () => {
            const routeId = routeSelect.value;
            const frequency = parseInt(frequencyInput.value) || 7;
            const economyFare = parseInt(fareInput.value) || 250;
            
            if (!routeId) {
                analysisDiv.style.display = 'none';
                return;
            }
            
            try {
                const analysis = await fetch('/api/route_analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        route_id: routeId,
                        frequency: frequency,
                        economy_fare: economyFare,
                        business_fare: economyFare * 3.5 // Standard business class multiplier
                    })
                }).then(r => r.json());
                
                // Update analysis display
                document.getElementById('analysis-revenue').textContent = `$${analysis.revenue?.monthly_revenue?.toFixed(0) || 0}`;
                document.getElementById('analysis-costs').textContent = `$${analysis.costs?.monthly_total?.toFixed(0) || 0}`;
                document.getElementById('analysis-profit').textContent = `$${analysis.profitability?.monthly_profit?.toFixed(0) || 0}`;
                document.getElementById('analysis-margin').textContent = `${analysis.profitability?.profit_margin?.toFixed(1) || 0}%`;
                
                const indicator = document.getElementById('profitability-indicator');
                const profit = analysis.profitability?.monthly_profit || 0;
                
                if (profit > 50000) {
                    indicator.textContent = '💰 Highly Profitable';
                    indicator.className = 'profitability-indicator profitable';
                } else if (profit > 0) {
                    indicator.textContent = '📈 Profitable';
                    indicator.className = 'profitability-indicator profitable';
                } else if (profit > -25000) {
                    indicator.textContent = '⚠️ Marginal';
                    indicator.className = 'profitability-indicator marginal';
                } else {
                    indicator.textContent = '📉 Unprofitable';
                    indicator.className = 'profitability-indicator unprofitable';
                }
                
                analysisDiv.style.display = 'block';
                
            } catch (error) {
                console.error('❌ Route analysis error:', error);
            }
        };
        
        // Add event listeners
        routeSelect.addEventListener('change', showAnalysis);
        frequencyInput.addEventListener('input', showAnalysis);
        fareInput.addEventListener('input', showAnalysis);
        
        // Handle route assignment (prevent multiple event listeners)
        assignButton.removeEventListener('click', this.assignRoute);
        assignButton.addEventListener('click', () => {
            this.assignRoute();
        });
        
        // Handle aircraft sync
        const syncButton = document.getElementById('sync-aircraft');
        if (syncButton) {
            syncButton.addEventListener('click', () => {
                this.syncAircraftFleet();
            });
        }
    }
    
    async syncAircraftFleet() {
        try {
            const syncButton = document.getElementById('sync-aircraft');
            syncButton.disabled = true;
            syncButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
            
            const response = await fetch('/api/sync_aircraft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(`✅ ${result.message}`);
                // Reload routes data to show synced aircraft
                this.loadRoutesData();
            } else {
                alert(`❌ ${result.message}`);
            }
            
        } catch (error) {
            console.error('❌ Aircraft sync error:', error);
            alert('❌ Error syncing aircraft fleet');
        } finally {
            const syncButton = document.getElementById('sync-aircraft');
            syncButton.disabled = false;
            syncButton.innerHTML = '<i class="fas fa-sync"></i> Sync Aircraft Fleet';
        }
    }

    calculateProperHeading(flight) {
        // Extract departure and arrival airports from route string
        const routeParts = flight.route?.split(' → ') || ['', ''];
        const depAirport = routeParts[0];
        const arrAirport = routeParts[1];
        
        console.log(`🧭 Calculating heading for ${flight.name}: ${depAirport} → ${arrAirport}`);
        
        // Get airport coordinates (add more airports as needed)
        const airports = {
            'KJFK': { lat: 40.6413, lon: -73.7781 },
            'KLAX': { lat: 33.9425, lon: -118.4081 },
            'EGLL': { lat: 51.4700, lon: -0.4543 },
            'EDDF': { lat: 50.0379, lon: 8.5622 },
            'RJTT': { lat: 35.7653, lon: 140.3864 },
            'OMDB': { lat: 25.2532, lon: 55.3657 },
            'KATL': { lat: 33.6407, lon: -84.4277 },
            'KORD': { lat: 41.9742, lon: -87.9073 },
            'KBOS': { lat: 42.3656, lon: -71.0096 },
            'KDCA': { lat: 38.8512, lon: -77.0402 },
            'KLAS': { lat: 36.0840, lon: -115.1537 },
            'KMCO': { lat: 28.4312, lon: -81.3081 },
            'KSFO': { lat: 37.6213, lon: -122.3790 },
            'YSSY': { lat: -33.9399, lon: 151.1753 }
        };
        
        const destAirport = airports[arrAirport];
        if (!destAirport) {
            console.log(`❌ Destination airport ${arrAirport} not found, using fallback`);
            return flight.heading || 0; // Fallback to provided heading
        }
        
        console.log(`📍 Current: [${flight.lat}, ${flight.lon}] → Destination: [${destAirport.lat}, ${destAirport.lon}]`);
        
        // Calculate proper bearing using great circle navigation
        const lat1 = flight.lat * Math.PI / 180;  // Current position latitude in radians
        const lon1 = flight.lon * Math.PI / 180;  // Current position longitude in radians
        const lat2 = destAirport.lat * Math.PI / 180;  // Destination latitude in radians
        const lon2 = destAirport.lon * Math.PI / 180;  // Destination longitude in radians
        
        const deltaLon = lon2 - lon1;
        
        const y = Math.sin(deltaLon) * Math.cos(lat2);
        const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(deltaLon);
        
        let bearing = Math.atan2(y, x) * 180 / Math.PI;
        
        // Normalize navigation bearing to 0-360
        bearing = (bearing + 360) % 360;
        
        // Convert from navigation bearing to CSS rotation
        // Navigation: 0° = North, 90° = East, 180° = South, 270° = West
        // Font Awesome plane icon by default points to the RIGHT (east)
        // So we need to subtract 90° to align north bearing with upward rotation
        // bearing = 0° (north) → CSS rotation = -90° (up) → normalized = 270°
        // bearing = 90° (east) → CSS rotation = 0° (right)
        const cssRotation = (bearing - 90 + 360) % 360;
        
        console.log(`🧭 Calculated bearing: ${bearing.toFixed(1)}° → CSS rotation: ${cssRotation.toFixed(1)}°`);
        
        // Test some known cases for debugging
        if (depAirport === 'KJFK' && arrAirport === 'KLAX') {
            console.log('🧪 JFK→LAX should point roughly southwest (≈225°)');
        } else if (depAirport === 'KLAX' && arrAirport === 'KJFK') {
            console.log('🧪 LAX→JFK should point roughly northeast (≈45°)');
        } else if (depAirport === 'KATL' && arrAirport === 'EDDF') {
            console.log('🧪 KATL→EDDF (Atlanta→Frankfurt) should point northeast (≈45-60°)');
            console.log(`🧪 Coordinates: KATL[33.64, -84.43] → EDDF[50.04, 8.56]`);
            console.log(`🧪 Expected: Lat diff: ${destAirport.lat - flight.lat} (positive = north)`);
            console.log(`🧪 Expected: Lon diff: ${destAirport.lon - flight.lon} (positive = east)`);
            console.log(`🧪 This should be NORTHEAST direction (45-60°)`);
            
            // Manual verification of the calculation
            const manualY = Math.sin((destAirport.lon * Math.PI / 180) - (flight.lon * Math.PI / 180)) * Math.cos(destAirport.lat * Math.PI / 180);
            const manualX = Math.cos(flight.lat * Math.PI / 180) * Math.sin(destAirport.lat * Math.PI / 180) - Math.sin(flight.lat * Math.PI / 180) * Math.cos(destAirport.lat * Math.PI / 180) * Math.cos((destAirport.lon * Math.PI / 180) - (flight.lon * Math.PI / 180));
            const manualBearing = Math.atan2(manualY, manualX) * 180 / Math.PI;
            console.log(`🧪 Manual calculation: y=${manualY.toFixed(3)}, x=${manualX.toFixed(3)}, bearing=${((manualBearing + 360) % 360).toFixed(1)}°`);
        }
        
        return cssRotation;
    }

    calculateAircraftScale(flight, altitudeMeters) {
        // 🛫 REALISTIC 3D TAKEOFF & LANDING ANIMATIONS WITH AUTO-ZOOM! 🛬
        
        const status = flight.status;
        const progress = flight.progress / 100; // Convert to 0-1
        const cruiseAltitudeMeters = 10668; // 35,000 feet in meters
        
        let scale, visualAltitude, cameraZoom;
        
        if (status === 'parked') {
            // 🅿️ PARKED: Aircraft is resting at airport - extremely tiny size on ground
            scale = 0.1; // MICROSCOPIC for parked aircraft (like real airplane from space)
            visualAltitude = 5; // On the ground at airport
            cameraZoom = 20; // MAXIMUM ZOOM to see microscopic parked aircraft
            
            console.log(`🅿️ PARKED: scale=${scale} (MICROSCOPIC parked aircraft), alt=${visualAltitude}m, zoom=${cameraZoom}`);
            
        } else if (status === 'departing') {
            // 🛫 TAKEOFF: Aircraft starts TINY (realistic airplane size on runway) and gets BIGGER as it climbs towards space
            const takeoffProgress = Math.min(progress / 0.05, 1.0); // 0 to 1 during first 5%
            
            // Aircraft gets BIGGER as it climbs higher (closer to space camera perspective)
            scale = 0.1 + (99.9 * takeoffProgress); // 0.1 → 100 (EXTREME size increase climbing to space)
            visualAltitude = 5 + (cruiseAltitudeMeters - 5) * takeoffProgress; // Climb from runway to cruise
            
            // 📹 AUTO-ZOOM: Zoom out as aircraft gets bigger to maintain apparent size
            cameraZoom = 20 - (10 * takeoffProgress); // 20 → 10 (zoom out as aircraft gets bigger)
            
            console.log(`🛫 TAKEOFF: progress=${(progress*100).toFixed(1)}%, scale=${scale.toFixed(1)} (tiny→big), alt=${visualAltitude.toFixed(0)}m, zoom=${cameraZoom.toFixed(1)}`);
            
        } else if (status === 'arriving') {
            // 🛬 LANDING: Aircraft starts BIG (high altitude, close to space camera) and gets TINY as it descends to runway
            const landingProgress = (progress - 0.95) / 0.05; // 0 to 1 during last 5%
            const safeLandingProgress = Math.max(0, Math.min(1, landingProgress));
            
            // Aircraft gets TINY as it descends farther from space camera (realistic space perspective!)
            scale = 100 - (99.9 * safeLandingProgress); // 100 → 0.1 (EXTREME size decrease landing on runway)
            visualAltitude = cruiseAltitudeMeters - (cruiseAltitudeMeters - 5) * safeLandingProgress; // Descend to runway
            
            // 📹 AUTO-ZOOM: Zoom in as aircraft gets smaller to maintain apparent size
            cameraZoom = 10 + (10 * safeLandingProgress); // 10 → 20 (zoom in as aircraft gets smaller)
            
            console.log(`🛬 LANDING: progress=${(progress*100).toFixed(1)}%, scale=${scale.toFixed(1)} (big→tiny), alt=${visualAltitude.toFixed(0)}m, zoom=${cameraZoom.toFixed(1)}`);
            
        } else {
            // ✈️ CRUISE: Large size at high altitude (close to space camera)
            scale = 100; // Maximum scale for high altitude cruise (close to space camera)
            visualAltitude = cruiseAltitudeMeters; // High cruise altitude
            cameraZoom = 10; // Wide zoom for cruise
            
            console.log(`✈️ CRUISE: scale=${scale} (HUGE - close to space camera), alt=${visualAltitude.toFixed(0)}m, zoom=${cameraZoom}`);
        }
        
        // Ensure reasonable scale bounds - allow extremely tiny aircraft on ground
        scale = Math.max(0.1, Math.min(150, scale)); // Allow much smaller aircraft on ground
        
        // Ensure aircraft land/park properly on runway with extreme zoom
        if (status === 'arriving' && progress > 99.8) {
            visualAltitude = 5; // ACTUALLY ON THE RUNWAY
            scale = 0.1; // MICROSCOPIC realistic airplane size
            cameraZoom = 20; // MAXIMUM ZOOM to see microscopic aircraft
        } else if (status === 'departing' && progress < 0.2) {
            visualAltitude = 5; // STARTING ON THE RUNWAY
            scale = 0.1; // MICROSCOPIC realistic airplane size
            cameraZoom = 20; // MAXIMUM ZOOM to see microscopic aircraft
        } else {
            visualAltitude = Math.max(5, visualAltitude); // Allow runway altitude
        }
        
        return { scale, visualAltitude, cameraZoom };
    }

    followAircraftIfLandingOrTakeoff(flight) {
        // 📹 DRAMATIC CAMERA FOLLOWING during critical phases
        if (!this.globeMap || !flight) return;
        
        // 🎥 SKIP CAMERA FOLLOWING if no flight is selected (free camera mode)
        if (!this.selectedFlight) {
            console.log(`🎥 SKIP: No flight selected, camera is free`);
            return;
        }
        
        // 🎥 ONLY FOLLOW if this flight matches the selected flight
        console.log(`🎥 CHECK: flight.id="${flight.id}", selectedFlight="${this.selectedFlight}", match=${flight.id === this.selectedFlight}`);
        if (flight.id !== this.selectedFlight) {
            return;
        }
        
        console.log(`🎥 FOLLOWING: Camera will follow flight ${flight.id} (${flight.status})`);
        
        const status = flight.status;
        const progress = flight.progress;
        
        // Follow aircraft during ALL phases when selected (not just critical phases)
        if (status === 'parked') {
            // 🅿️ PARKED FOLLOWING: Zoom in very close to see microscopic parked aircraft
            console.log(`📹 Following PARKED aircraft ${flight.id} - MAXIMUM ZOOM to see microscopic aircraft`);
            this.globeMap.flyTo({
                center: [flight.lon, flight.lat],
                zoom: 20, // MAXIMUM zoom to see microscopic parked aircraft
                pitch: 45, // Good angle to see parked aircraft
                bearing: 0,
                duration: 800 // Quick zoom
            });
            
        } else if (status === 'departing' && progress <= 5) {
            // 🛫 TAKEOFF FOLLOWING: Watch aircraft climb from runway
            console.log(`📹 Following takeoff of ${flight.id} at ${progress.toFixed(1)}% progress`);
            this.globeMap.flyTo({
                center: [flight.lon, flight.lat],
                zoom: 16, // Close zoom for takeoff detail
                pitch: 60, // Angled view to see climbing aircraft
                bearing: 0,
                duration: 1500 // Smooth camera movement
            });
            
        } else if (status === 'arriving' && progress >= 95) {
            // 🛬 LANDING FOLLOWING: Watch aircraft approach and land on runway
            console.log(`📹 Following landing of ${flight.id} at ${progress.toFixed(1)}% progress`);
            this.globeMap.flyTo({
                center: [flight.lon, flight.lat],
                zoom: 17, // Very close zoom for landing detail
                pitch: 65, // Steep angle to see descent to runway
                bearing: 0,
                duration: 1200 // Quick camera movement for landing
            });
            
        } else if (status === 'en_route') {
            // ✈️ CRUISE FOLLOWING: Follow aircraft during cruise with wider view
            console.log(`📹 Following CRUISE aircraft ${flight.id} at ${progress.toFixed(1)}% progress`);
            this.globeMap.flyTo({
                center: [flight.lon, flight.lat],
                zoom: 8, // Wider zoom for cruise flight
                pitch: 45, // Moderate angle for cruise view
                bearing: 0,
                duration: 2000 // Slower, smoother movement for cruise
            });
            
        } else {
            // 🌐 DEFAULT FOLLOWING: Follow any other status
            console.log(`📹 Following aircraft ${flight.id} (${status}) at ${progress.toFixed(1)}% progress`);
            this.globeMap.flyTo({
                center: [flight.lon, flight.lat],
                zoom: 10, // Medium zoom for general following
                pitch: 50,
                bearing: 0,
                duration: 1500
            });
        }
        
        // Store the followed aircraft for reference
        this.currentlyFollowing = flight.id;
    }

    autoZoomForAircraft(flight, targetZoom) {
        // 📹 AUTO-ZOOM: Automatically adjust camera zoom to maintain aircraft visibility
        if (!this.globeMap || !flight || !targetZoom) return;
        
        // 🎥 SKIP AUTO-ZOOM if no flight is selected (free camera mode)
        if (!this.selectedFlight) {
            return;
        }
        
        // 🎥 ONLY AUTO-ZOOM if this flight matches the selected flight
        console.log(`🔍 ZOOM CHECK: flight.id="${flight.id}", selectedFlight="${this.selectedFlight}", match=${flight.id === this.selectedFlight}`);
        if (flight.id !== this.selectedFlight) {
            return;
        }
        
        console.log(`🔍 AUTO-ZOOM: Will auto-zoom for flight ${flight.id}`);
        
        // Only auto-zoom for aircraft in critical phases (parked, takeoff, landing)
        const criticalPhases = ['parked', 'departing', 'arriving'];
        if (!criticalPhases.includes(flight.status)) {
            return; // Skip auto-zoom for cruising aircraft
        }
        
        const currentZoom = this.globeMap.getZoom();
        const zoomDifference = Math.abs(currentZoom - targetZoom);
        
        // More aggressive zoom threshold for critical phases
        if (zoomDifference > 0.3) {
            console.log(`📹 AUTO-ZOOM (${flight.status}): Aircraft ${flight.id} - zoom ${currentZoom.toFixed(1)} → ${targetZoom} (scale: ${(targetZoom === 20 ? 'TINY' : 'BIG')})`);
            
            // Immediate zoom change for critical phases
            this.globeMap.flyTo({
                center: [flight.lon, flight.lat], // Center on aircraft
                zoom: targetZoom,
                pitch: 45, // Better angle to see aircraft
                bearing: this.globeMap.getBearing(),
                duration: 800 // Fast zoom transition
            });
        }
    }

    toggleRouteLines() {
        this.routeLinesVisible = !this.routeLinesVisible;
        const button = document.getElementById('toggle-routes');
        
        if (this.routeLinesVisible) {
            button.classList.add('active');
            button.innerHTML = '<i class="fas fa-route"></i> Hide Routes';
            console.log('📍 Route lines enabled');
            
            // Add route lines for all current flights
            this.currentFlights.forEach(flight => {
                this.addRouteLineForFlight(flight);
            });
        } else {
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-route"></i> Routes';
            console.log('📍 Route lines disabled');
            
            // Remove all route lines
            this.routeLines.forEach(line => {
                this.map.removeLayer(line);
            });
            this.routeLines.clear();
        }
    }

    addRouteLineForFlight(flight) {
        // Remove existing route line for this flight
        if (this.routeLines.has(flight.id)) {
            this.map.removeLayer(this.routeLines.get(flight.id));
        }
        
        // Extract departure and arrival airports from route string
        const routeParts = flight.route?.split(' → ') || ['', ''];
        const depAirport = routeParts[0];
        const arrAirport = routeParts[1];
        
        const airports = {
            'KJFK': { lat: 40.6413, lon: -73.7781 },
            'KLAX': { lat: 33.9425, lon: -118.4081 },
            'EGLL': { lat: 51.4700, lon: -0.4543 },
            'EDDF': { lat: 50.0379, lon: 8.5622 },
            'RJTT': { lat: 35.7653, lon: 140.3864 },
            'OMDB': { lat: 25.2532, lon: 55.3657 },
            'KATL': { lat: 33.6407, lon: -84.4277 },
            'KORD': { lat: 41.9742, lon: -87.9073 },
            'KBOS': { lat: 42.3656, lon: -71.0096 },
            'KDCA': { lat: 38.8512, lon: -77.0402 },
            'KLAS': { lat: 36.0840, lon: -115.1537 },
            'KMCO': { lat: 28.4312, lon: -81.3081 },
            'KSFO': { lat: 37.6213, lon: -122.3790 },
            'YSSY': { lat: -33.9399, lon: 151.1753 }
        };
        
        const dep = airports[depAirport];
        const arr = airports[arrAirport];
        
        if (!dep || !arr) return;
        
        // Create route line from departure to arrival
        const routeLine = L.polyline([
            [dep.lat, dep.lon],
            [arr.lat, arr.lon]
        ], {
            color: flight.color || '#FF6B35',
            weight: 2,
            opacity: 0.7,
            dashArray: '10, 10',
            interactive: false
        }).addTo(this.map);
        
        // Store the route line
        this.routeLines.set(flight.id, routeLine);
    }

    initWeatherSystem() {
        console.log('🌦️ Initializing weather system...');
        
        // Generate initial weather for all airports
        this.generateRandomWeather();
        
        // Update weather every 2-5 minutes
        setInterval(() => {
            this.updateWeather();
        }, (2 + Math.random() * 3) * 60000); // 2-5 minutes
        
        console.log('✅ Weather system initialized');
    }

    generateRandomWeather() {
        const airports = ['KJFK', 'KLAX', 'EGLL', 'EDDF', 'RJTT', 'OMDB', 'KATL', 'KORD', 'KBOS', 'KDCA', 'KLAS', 'KMCO', 'KSFO', 'YSSY'];
        
        airports.forEach(airportCode => {
            const weather = this.generateWeatherForAirport(airportCode);
            this.weatherSystem.currentWeather.set(airportCode, weather);
            this.addWeatherLayer(airportCode, weather);
        });
        
        console.log(`🌤️ Generated weather for ${airports.length} airports`);
    }

    generateWeatherForAirport(airportCode) {
        // Weight weather types based on realism
        const weatherChances = {
            'clear': 0.4,      // 40% chance - most common
            'rain': 0.25,      // 25% chance
            'fog': 0.15,       // 15% chance
            'wind': 0.1,       // 10% chance - strong winds
            'storm': 0.07,     // 7% chance
            'snow': 0.03       // 3% chance - rare except winter
        };
        
        // Adjust based on location (simplified)
        if (['YSSY', 'OMDB'].includes(airportCode)) {
            weatherChances.snow = 0; // No snow in warm climates
            weatherChances.clear = 0.6;
        }
        
        const random = Math.random();
        let cumulative = 0;
        
        for (const [type, chance] of Object.entries(weatherChances)) {
            cumulative += chance;
            if (random <= cumulative) {
                return {
                    type: type,
                    intensity: this.getWeatherIntensity(type),
                    visibility: this.getVisibility(type),
                    windSpeed: Math.floor(Math.random() * 30) + 5, // 5-35 knots
                    temperature: Math.floor(Math.random() * 40) + 10, // 10-50°C
                    pressure: Math.floor(Math.random() * 50) + 990, // 990-1040 hPa
                    timestamp: Date.now(),
                    duration: (Math.random() * 60 + 30) * 60000 // 30-90 minutes
                };
            }
        }
        
        // Fallback to clear weather
        return {
            type: 'clear',
            intensity: 'light',
            visibility: 10,
            windSpeed: 8,
            temperature: 22,
            pressure: 1013,
            timestamp: Date.now(),
            duration: 60 * 60000
        };
    }

    getWeatherIntensity(type) {
        const intensities = {
            'clear': 'none',
            'rain': ['light', 'moderate', 'heavy'][Math.floor(Math.random() * 3)],
            'storm': ['moderate', 'severe'][Math.floor(Math.random() * 2)],
            'snow': ['light', 'moderate', 'heavy'][Math.floor(Math.random() * 3)],
            'fog': ['light', 'dense'][Math.floor(Math.random() * 2)],
            'wind': ['moderate', 'strong', 'severe'][Math.floor(Math.random() * 3)]
        };
        
        return intensities[type] || 'light';
    }

    getVisibility(type) {
        const visibilityRanges = {
            'clear': 10,
            'rain': Math.random() * 3 + 4,      // 4-7 km
            'storm': Math.random() * 2 + 2,     // 2-4 km
            'snow': Math.random() * 3 + 3,      // 3-6 km
            'fog': Math.random() * 1 + 0.5,     // 0.5-1.5 km
            'wind': Math.random() * 3 + 6       // 6-9 km
        };
        
        return Math.round((visibilityRanges[type] || 10) * 10) / 10;
    }

    addWeatherLayer(airportCode, weather) {
        const airports = {
            'KJFK': { lat: 40.6413, lon: -73.7781 },
            'KLAX': { lat: 33.9425, lon: -118.4081 },
            'EGLL': { lat: 51.4700, lon: -0.4543 },
            'EDDF': { lat: 50.0379, lon: 8.5622 },
            'RJTT': { lat: 35.7653, lon: 140.3864 },
            'OMDB': { lat: 25.2532, lon: 55.3657 },
            'KATL': { lat: 33.6407, lon: -84.4277 },
            'KORD': { lat: 41.9742, lon: -87.9073 },
            'KBOS': { lat: 42.3656, lon: -71.0096 },
            'KDCA': { lat: 38.8512, lon: -77.0402 },
            'KLAS': { lat: 36.0840, lon: -115.1537 },
            'KMCO': { lat: 28.4312, lon: -81.3081 },
            'KSFO': { lat: 37.6213, lon: -122.3790 },
            'YSSY': { lat: -33.9399, lon: 151.1753 }
        };

        const airport = airports[airportCode];
        if (!airport) return;

        // Remove existing weather layer
        if (this.weatherSystem.weatherLayers.has(airportCode)) {
            this.map.removeLayer(this.weatherSystem.weatherLayers.get(airportCode));
        }

        const weatherLayer = this.createWeatherVisualization(airport, weather);
        if (weatherLayer) {
            weatherLayer.addTo(this.map);
            this.weatherSystem.weatherLayers.set(airportCode, weatherLayer);
        }

        console.log(`🌧️ Added ${weather.type} weather at ${airportCode} (${weather.intensity})`);
    }

    createWeatherVisualization(airport, weather) {
        const radius = this.getWeatherRadius(weather);
        const color = this.getWeatherColor(weather);
        const opacity = this.getWeatherOpacity(weather);

        switch (weather.type) {
            case 'rain':
                return this.createRainLayer(airport, radius, weather.intensity);
            
            case 'storm':
                return this.createStormLayer(airport, radius, weather.intensity);
            
            case 'snow':
                return this.createSnowLayer(airport, radius, weather.intensity);
            
            case 'fog':
                return this.createFogLayer(airport, radius, weather.intensity);
            
            case 'wind':
                return this.createWindLayer(airport, radius, weather.intensity);
            
            default:
                return null; // Clear weather - no visualization
        }
    }

    getWeatherRadius(weather) {
        const baseRadius = {
            'rain': 15000,    // 15km
            'storm': 25000,   // 25km
            'snow': 20000,    // 20km
            'fog': 10000,     // 10km
            'wind': 30000     // 30km
        };

        const intensityMultiplier = {
            'light': 0.7,
            'moderate': 1.0,
            'heavy': 1.4,
            'severe': 1.8,
            'dense': 1.2,
            'strong': 1.3
        };

        const base = baseRadius[weather.type] || 15000;
        const multiplier = intensityMultiplier[weather.intensity] || 1.0;
        
        return base * multiplier;
    }

    getWeatherColor(weather) {
        const colors = {
            'rain': '#4A90E2',
            'storm': '#8B4E8C',
            'snow': '#E8F4FD',
            'fog': '#B0BEC5',
            'wind': '#FFC107'
        };
        
        return colors[weather.type] || '#CCCCCC';
    }

    getWeatherOpacity(weather) {
        const opacities = {
            'light': 0.3,
            'moderate': 0.5,
            'heavy': 0.7,
            'severe': 0.8,
            'dense': 0.6,
            'strong': 0.4
        };
        
        return opacities[weather.intensity] || 0.3;
    }

    createRainLayer(airport, radius, intensity) {
        const opacity = this.getWeatherOpacity({ intensity });
        
        const rainLayer = L.layerGroup();
        
        // Main rain area
        const rainCircle = L.circle([airport.lat, airport.lon], {
            radius: radius,
            fillColor: '#4A90E2',
            color: '#2E5C8A',
            weight: 2,
            opacity: 0.8,
            fillOpacity: opacity,
            className: 'weather-rain'
        });
        
        // Add animated rain effect
        const rainMarker = L.divIcon({
            className: 'weather-icon rain-icon',
            html: `<div class="rain-animation ${intensity}">
                      <i class="fas fa-cloud-rain" style="color: #4A90E2; font-size: 20px;"></i>
                      <div class="rain-drops"></div>
                   </div>`,
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });
        
        const rainIconMarker = L.marker([airport.lat, airport.lon], { icon: rainMarker });
        
        rainLayer.addLayer(rainCircle);
        rainLayer.addLayer(rainIconMarker);
        
        return rainLayer;
    }

    createStormLayer(airport, radius, intensity) {
        const opacity = this.getWeatherOpacity({ intensity });
        
        const stormLayer = L.layerGroup();
        
        // Main storm area with pulsing effect
        const stormCircle = L.circle([airport.lat, airport.lon], {
            radius: radius,
            fillColor: '#8B4E8C',
            color: '#5A2D5C',
            weight: 3,
            opacity: 0.9,
            fillOpacity: opacity,
            className: 'weather-storm pulsing'
        });
        
        // Lightning effect marker
        const stormMarker = L.divIcon({
            className: 'weather-icon storm-icon',
            html: `<div class="storm-animation ${intensity}">
                      <i class="fas fa-bolt" style="color: #FFD700; font-size: 24px;"></i>
                      <div class="lightning-flash"></div>
                   </div>`,
            iconSize: [50, 50],
            iconAnchor: [25, 25]
        });
        
        const stormIconMarker = L.marker([airport.lat, airport.lon], { icon: stormMarker });
        
        stormLayer.addLayer(stormCircle);
        stormLayer.addLayer(stormIconMarker);
        
        return stormLayer;
    }

    createSnowLayer(airport, radius, intensity) {
        const opacity = this.getWeatherOpacity({ intensity });
        
        const snowLayer = L.layerGroup();
        
        const snowCircle = L.circle([airport.lat, airport.lon], {
            radius: radius,
            fillColor: '#E8F4FD',
            color: '#B3D9F2',
            weight: 2,
            opacity: 0.7,
            fillOpacity: opacity,
            className: 'weather-snow'
        });
        
        const snowMarker = L.divIcon({
            className: 'weather-icon snow-icon',
            html: `<div class="snow-animation ${intensity}">
                      <i class="fas fa-snowflake" style="color: #E8F4FD; font-size: 20px;"></i>
                      <div class="snow-particles"></div>
                   </div>`,
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });
        
        const snowIconMarker = L.marker([airport.lat, airport.lon], { icon: snowMarker });
        
        snowLayer.addLayer(snowCircle);
        snowLayer.addLayer(snowIconMarker);
        
        return snowLayer;
    }

    createFogLayer(airport, radius, intensity) {
        const opacity = this.getWeatherOpacity({ intensity });
        
        const fogLayer = L.layerGroup();
        
        const fogCircle = L.circle([airport.lat, airport.lon], {
            radius: radius,
            fillColor: '#B0BEC5',
            color: '#78909C',
            weight: 1,
            opacity: 0.6,
            fillOpacity: opacity,
            className: 'weather-fog'
        });
        
        const fogMarker = L.divIcon({
            className: 'weather-icon fog-icon',
            html: `<div class="fog-animation ${intensity}">
                      <i class="fas fa-smog" style="color: #B0BEC5; font-size: 18px;"></i>
                      <div class="fog-particles"></div>
                   </div>`,
            iconSize: [35, 35],
            iconAnchor: [17, 17]
        });
        
        const fogIconMarker = L.marker([airport.lat, airport.lon], { icon: fogMarker });
        
        fogLayer.addLayer(fogCircle);
        fogLayer.addLayer(fogIconMarker);
        
        return fogLayer;
    }

    createWindLayer(airport, radius, intensity) {
        const opacity = this.getWeatherOpacity({ intensity });
        
        const windLayer = L.layerGroup();
        
        const windCircle = L.circle([airport.lat, airport.lon], {
            radius: radius,
            fillColor: '#FFC107',
            color: '#FF8F00',
            weight: 2,
            opacity: 0.6,
            fillOpacity: opacity * 0.5, // Lower opacity for wind
            className: 'weather-wind'
        });
        
        const windMarker = L.divIcon({
            className: 'weather-icon wind-icon',
            html: `<div class="wind-animation ${intensity}">
                      <i class="fas fa-wind" style="color: #FFC107; font-size: 20px;"></i>
                      <div class="wind-lines"></div>
                   </div>`,
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });
        
        const windIconMarker = L.marker([airport.lat, airport.lon], { icon: windMarker });
        
        windLayer.addLayer(windCircle);
        windLayer.addLayer(windIconMarker);
        
        return windLayer;
    }

    updateWeather() {
        console.log('🌦️ Updating weather conditions...');
        
        // 30% chance to change weather at each airport
        this.weatherSystem.currentWeather.forEach((weather, airportCode) => {
            if (Math.random() < 0.3) {
                const newWeather = this.generateWeatherForAirport(airportCode);
                this.weatherSystem.currentWeather.set(airportCode, newWeather);
                this.addWeatherLayer(airportCode, newWeather);
                
                console.log(`🌤️ ${airportCode}: ${weather.type} → ${newWeather.type}`);
            }
        });
        
        // Broadcast weather update to show notifications
        this.showWeatherNotification();
    }

    showWeatherNotification() {
        // Show a brief notification about weather changes
        const notification = document.createElement('div');
        notification.className = 'weather-notification';
        notification.innerHTML = `
            <i class="fas fa-cloud"></i>
            Weather conditions updated
        `;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: rgba(45, 45, 45, 0.95);
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            z-index: 2000;
            font-size: 14px;
            border-left: 4px solid #4CAF50;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    toggleWeather() {
        this.weatherSystem.enabled = !this.weatherSystem.enabled;
        const button = document.getElementById('toggle-weather');
        
        if (this.weatherSystem.enabled) {
            button.classList.add('active');
            button.innerHTML = '<i class="fas fa-cloud"></i> Weather';
            console.log('🌦️ Weather system enabled');
            
            // Show all weather layers
            this.weatherSystem.weatherLayers.forEach((layer, airportCode) => {
                layer.addTo(this.map);
            });
            
            // Generate weather if none exists
            if (this.weatherSystem.currentWeather.size === 0) {
                this.generateRandomWeather();
            }
        } else {
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-cloud-off"></i> Weather';
            console.log('🌦️ Weather system disabled');
            
            // Hide all weather layers
            this.weatherSystem.weatherLayers.forEach((layer, airportCode) => {
                this.map.removeLayer(layer);
            });
        }
    }

    checkWeatherImpact(flight) {
        if (!this.weatherSystem.enabled) {
            return { message: null, color: 'white' };
        }

        // Check weather at nearby airports (simplified impact calculation)
        const nearbyWeather = this.findNearbyWeather(flight.lat, flight.lon);
        if (!nearbyWeather) {
            return { message: null, color: 'white' };
        }

        const { weather, distance } = nearbyWeather;
        
        // Weather affects flights within range
        if (distance > this.getWeatherRadius(weather) / 1000) {
            return { message: null, color: 'white' };
        }

        switch (weather.type) {
            case 'storm':
                return { 
                    message: weather.intensity === 'severe' ? 'SEVERE WEATHER - DIVERTING' : 'Storm affecting flight',
                    color: '#8B4E8C'
                };
            case 'fog':
                return { 
                    message: weather.intensity === 'dense' ? 'Low visibility - Reduced speed' : 'Light fog conditions',
                    color: '#B0BEC5'
                };
            case 'wind':
                if (weather.intensity === 'severe') {
                    return { message: 'Strong winds - Turbulence expected', color: '#FFC107' };
                }
                break;
            case 'snow':
                if (weather.intensity === 'heavy') {
                    return { message: 'Heavy snow - Approach delays possible', color: '#E8F4FD' };
                }
                break;
            case 'rain':
                if (weather.intensity === 'heavy') {
                    return { message: 'Heavy rain - Reduced visibility', color: '#4A90E2' };
                }
                break;
        }

        return { message: null, color: 'white' };
    }

    findNearbyWeather(lat, lon) {
        let closestWeather = null;
        let minDistance = Infinity;

        this.weatherSystem.currentWeather.forEach((weather, airportCode) => {
            const airports = {
                'KJFK': { lat: 40.6413, lon: -73.7781 },
                'KLAX': { lat: 33.9425, lon: -118.4081 },
                'EGLL': { lat: 51.4700, lon: -0.4543 },
                'EDDF': { lat: 50.0379, lon: 8.5622 },
                'RJTT': { lat: 35.7653, lon: 140.3864 },
                'OMDB': { lat: 25.2532, lon: 55.3657 },
                'KATL': { lat: 33.6407, lon: -84.4277 },
                'KORD': { lat: 41.9742, lon: -87.9073 },
                'KBOS': { lat: 42.3656, lon: -71.0096 },
                'KDCA': { lat: 38.8512, lon: -77.0402 },
                'KLAS': { lat: 36.0840, lon: -115.1537 },
                'KMCO': { lat: 28.4312, lon: -81.3081 },
                'KSFO': { lat: 37.6213, lon: -122.3790 },
                'YSSY': { lat: -33.9399, lon: 151.1753 }
            };

            const airport = airports[airportCode];
            if (!airport) return;

            // Calculate distance using Haversine formula (simplified)
            const deltaLat = (airport.lat - lat) * Math.PI / 180;
            const deltaLon = (airport.lon - lon) * Math.PI / 180;
            const a = Math.sin(deltaLat/2) * Math.sin(deltaLat/2) +
                     Math.cos(lat * Math.PI / 180) * Math.cos(airport.lat * Math.PI / 180) *
                     Math.sin(deltaLon/2) * Math.sin(deltaLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            const distance = 6371 * c; // Earth radius in km

            if (distance < minDistance) {
                minDistance = distance;
                closestWeather = { weather, distance };
            }
        });

        return closestWeather;
    }

    // Tutorial System Methods
    checkTutorialCompleted() {
        return localStorage.getItem('tutorialCompleted') === 'true';
    }

    initTutorial() {
        console.log('🎓 Initializing tutorial system...');
        
        // Show tutorial if not completed
        if (!this.tutorialCompleted) {
            this.showTutorial();
        } else {
            this.hideTutorial();
        }
        
        // Setup tutorial navigation
        document.getElementById('tutorial-next').addEventListener('click', () => {
            this.nextTutorialStep();
        });
        
        document.getElementById('tutorial-prev').addEventListener('click', () => {
            this.prevTutorialStep();
        });
        
        document.getElementById('tutorial-finish').addEventListener('click', () => {
            this.completeTutorial();
        });
        
        document.getElementById('skip-tutorial').addEventListener('click', () => {
            this.skipTutorial();
        });
        
        // Help button to restart tutorial
        document.getElementById('help-tutorial').addEventListener('click', () => {
            this.restartTutorial();
        });
        
        console.log('✅ Tutorial system initialized');
    }

    showTutorial() {
        document.getElementById('tutorial-overlay').style.display = 'flex';
        this.updateTutorialStep();
    }

    hideTutorial() {
        document.getElementById('tutorial-overlay').style.display = 'none';
    }

    nextTutorialStep() {
        if (this.tutorialStep < this.tutorialMaxSteps) {
            this.tutorialStep++;
            this.updateTutorialStep();
        }
    }

    prevTutorialStep() {
        if (this.tutorialStep > 1) {
            this.tutorialStep--;
            this.updateTutorialStep();
        }
    }

    updateTutorialStep() {
        // Hide all steps
        document.querySelectorAll('.tutorial-step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show current step
        document.querySelector(`[data-step="${this.tutorialStep}"]`).classList.add('active');
        
        // Update progress bar
        const progressPercent = (this.tutorialStep / this.tutorialMaxSteps) * 100;
        document.getElementById('tutorial-progress').style.width = `${progressPercent}%`;
        
        // Update step counter
        document.getElementById('step-counter').textContent = `${this.tutorialStep} / ${this.tutorialMaxSteps}`;
        
        // Update navigation buttons
        const prevBtn = document.getElementById('tutorial-prev');
        const nextBtn = document.getElementById('tutorial-next');
        const finishBtn = document.getElementById('tutorial-finish');
        
        prevBtn.disabled = this.tutorialStep === 1;
        
        if (this.tutorialStep === this.tutorialMaxSteps) {
            nextBtn.style.display = 'none';
            finishBtn.style.display = 'inline-block';
        } else {
            nextBtn.style.display = 'inline-block';
            finishBtn.style.display = 'none';
        }
        
        console.log(`📖 Tutorial step: ${this.tutorialStep}/${this.tutorialMaxSteps}`);
    }

    completeTutorial() {
        localStorage.setItem('tutorialCompleted', 'true');
        this.tutorialCompleted = true;
        this.hideTutorial();
        
        // Show completion message
        this.showTutorialCompletionMessage();
        
        console.log('🎉 Tutorial completed!');
    }

    skipTutorial() {
        if (confirm('Are you sure you want to skip the tutorial? You can always access help later.')) {
            this.completeTutorial();
        }
    }

    showTutorialCompletionMessage() {
        const notification = document.createElement('div');
        notification.className = 'tutorial-completion-notification';
        notification.innerHTML = `
            <div class="completion-content">
                <i class="fas fa-graduation-cap"></i>
                <h3>Welcome to Your Airline Empire!</h3>
                <p>Tutorial completed successfully. You're now ready to build the world's greatest airline!</p>
                <div class="completion-stats">
                    <div class="stat">
                        <i class="fas fa-dollar-sign"></i>
                        <span>$100M Starting Capital</span>
                    </div>
                    <div class="stat">
                        <i class="fas fa-globe"></i>
                        <span>14 Global Airports</span>
                    </div>
                    <div class="stat">
                        <i class="fas fa-plane"></i>
                        <span>12+ Aircraft Models</span>
                    </div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="btn btn-success">
                    <i class="fas fa-rocket"></i> Let's Fly!
                </button>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 15000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.5s ease-out;
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            .completion-content {
                background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
                border-radius: 15px;
                padding: 40px;
                text-align: center;
                max-width: 500px;
                border: 2px solid #4CAF50;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
            }
            .completion-content i.fa-graduation-cap {
                font-size: 4rem;
                color: #4CAF50;
                margin-bottom: 20px;
                text-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
            }
            .completion-content h3 {
                color: #4CAF50;
                margin-bottom: 15px;
                font-size: 1.8rem;
            }
            .completion-content p {
                color: #cccccc;
                margin-bottom: 25px;
                font-size: 1.1rem;
                line-height: 1.5;
            }
            .completion-stats {
                display: flex;
                justify-content: space-around;
                margin: 25px 0;
                gap: 15px;
                flex-wrap: wrap;
            }
            .completion-stats .stat {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                padding: 15px;
                background: rgba(76, 175, 80, 0.1);
                border-radius: 8px;
                border: 1px solid rgba(76, 175, 80, 0.3);
                flex: 1;
                min-width: 120px;
            }
            .completion-stats .stat i {
                color: #4CAF50;
                font-size: 1.5rem;
            }
            .completion-stats .stat span {
                color: white;
                font-size: 0.9rem;
                font-weight: 500;
                text-align: center;
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(notification);
        
        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
                style.remove();
            }
        }, 8000);
    }

    // Helper method to restart tutorial (for testing or if user wants to see it again)
    restartTutorial() {
        localStorage.removeItem('tutorialCompleted');
        this.tutorialCompleted = false;
        this.tutorialStep = 1;
        this.showTutorial();
    }
}

// Initialize the app when page loads
let tracker;
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Aircraft Tracker...');
    tracker = new AircraftTracker();
});

// Global functions for onclick handlers
window.tracker = tracker;