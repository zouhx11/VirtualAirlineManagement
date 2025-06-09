/**
 * Real-Time Aircraft Tracking App
 * Uses WebSocket for smooth updates without page refreshes!
 */

class AircraftTracker {
    constructor() {
        this.map = null;
        this.socket = null;
        this.aircraftMarkers = new Map();
        this.airportMarkers = new Map();
        this.routeLines = new Map();
        this.currentFlights = [];
        this.timeSpeed = 1;
        
        this.init();
    }

    init() {
        this.initMap();
        this.initSocket();
        this.initUI();
        this.loadInitialData();
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

        console.log('✅ Map initialized with dark theme');
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

        this.socket.on('time_speed_update', (data) => {
            this.timeSpeed = data.speed;
            document.getElementById('time-speed').value = data.speed;
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

        // Route assignment
        document.getElementById('assign-route').addEventListener('click', () => {
            this.assignRoute();
        });

        // Route analysis
        document.getElementById('route-select').addEventListener('change', () => {
            this.analyzeRoute();
        });
        
        document.getElementById('frequency-input').addEventListener('input', () => {
            this.analyzeRoute();
        });
        
        document.getElementById('fare-input').addEventListener('input', () => {
            this.analyzeRoute();
        });

        // 3D View toggles
        this.setup3DViewToggles();
        
        // 3D Flight Mode toggles
        this.setup3DFlightMode();

        console.log('🎮 UI event listeners initialized');
    }

    async loadInitialData() {
        try {
            // Load airports
            const airports = await this.fetchAPI('/api/airports');
            this.addAirports(airports);

            // Load routes and add flight paths
            const routes = await this.fetchAPI('/api/routes');
            const assignments = await this.fetchAPI('/api/assignments');
            this.addFlightPaths(assignments);

            // Load aircraft and fleet data
            const aircraft = await this.fetchAPI('/api/aircraft');
            this.populateAircraftSelect(aircraft);
            this.populateRouteSelect(routes);
            this.updateFleetList(aircraft);
            
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
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    addAirports(airports) {
        Object.entries(airports).forEach(([code, airport]) => {
            const marker = L.marker([airport.lat, airport.lon], {
                icon: L.divIcon({
                    className: 'airport-marker',
                    html: `<i class="fas fa-plane" style="color: #3388ff; font-size: 16px;"></i>`,
                    iconSize: [20, 20]
                })
            });

            marker.bindPopup(`
                <div class="airport-popup">
                    <h4>${code}</h4>
                    <p>${airport.name}</p>
                </div>
            `);

            marker.addTo(this.map);
            this.airportMarkers.set(code, marker);
        });

        console.log(`🛫 Added ${Object.keys(airports).length} airports to map`);
    }

    addFlightPaths(assignments) {
        // Clear existing route lines
        this.routeLines.forEach(line => this.map.removeLayer(line));
        this.routeLines.clear();

        assignments.forEach(assignment => {
            const airports = this.getAirportCoords();
            const depAirport = airports[assignment.departure_airport];
            const arrAirport = airports[assignment.arrival_airport];

            if (depAirport && arrAirport) {
                const line = L.polyline([
                    [depAirport.lat, depAirport.lon],
                    [arrAirport.lat, arrAirport.lon]
                ], {
                    color: '#4CAF50',
                    weight: 2,
                    opacity: 0.6
                });

                line.bindPopup(`
                    <div class="route-popup">
                        <h4>Route</h4>
                        <p>${assignment.departure_airport} → ${assignment.arrival_airport}</p>
                        <p>Distance: ${assignment.distance_nm} nm</p>
                        <p>Frequency: ${assignment.frequency_weekly}/week</p>
                    </div>
                `);

                line.addTo(this.map);
                this.routeLines.set(`${assignment.departure_airport}-${assignment.arrival_airport}`, line);
            }
        });

        console.log(`🗺️ Added ${assignments.length} flight paths`);
    }

    updateAircraft(data) {
        this.currentFlights = data.flights;
        
        // Clear existing aircraft markers
        this.aircraftMarkers.forEach(marker => this.map.removeLayer(marker));
        this.aircraftMarkers.clear();

        // Add updated aircraft positions
        data.flights.forEach(flight => {
            const marker = this.createAircraftMarker(flight);
            marker.addTo(this.map);
            this.aircraftMarkers.set(flight.id, marker);
        });

        // Update UI
        this.updateFlightsList(data.flights);
        this.updateStatistics(data.flights);
        this.updateLastUpdate();
        
        // Update 3D flight view if active
        this.update3DFlights(data.flights);
        
        // Update header economics display periodically (every 10 updates)
        if (this.updateCounter === undefined) this.updateCounter = 0;
        this.updateCounter++;
        if (this.updateCounter % 10 === 0) {
            this.loadEconomics();
        }

        console.log(`✈️ Updated ${data.flights.length} aircraft positions`);
    }

    createAircraftMarker(flight) {
        const icon = this.getAircraftIcon(flight);
        
        const marker = L.marker([flight.lat, flight.lon], { icon });

        marker.bindPopup(`
            <div class="aircraft-popup">
                <h4>${flight.name}</h4>
                <p><strong>Route:</strong> ${flight.route}</p>
                <p><strong>Progress:</strong> ${flight.progress.toFixed(1)}%</p>
                <p><strong>Status:</strong> ${flight.status.replace('_', ' ').toUpperCase()}</p>
                <p><strong>Altitude:</strong> ${flight.altitude.toLocaleString()} ft</p>
                <p><strong>Speed:</strong> ${flight.ground_speed} kts</p>
                <p><strong>Heading:</strong> ${flight.heading.toFixed(0)}°</p>
            </div>
        `);

        return marker;
    }

    getAircraftIcon(flight) {
        const colors = {
            'departing': '#4CAF50',
            'en_route': '#f44336',
            'arriving': '#FF9800'
        };

        const color = colors[flight.status] || '#666';
        
        return L.divIcon({
            className: 'aircraft-marker',
            html: `<i class="fas fa-plane" style="color: ${color}; font-size: 14px; transform: rotate(${flight.heading}deg);"></i>`,
            iconSize: [20, 20]
        });
    }

    updateFlightsList(flights) {
        const container = document.getElementById('flights-list');
        
        if (flights.length === 0) {
            container.innerHTML = '<div class="no-data">No active flights</div>';
            return;
        }

        container.innerHTML = flights.map(flight => `
            <div class="flight-item">
                <h5>${flight.name}</h5>
                <p><strong>Route:</strong> ${flight.route}</p>
                <p><strong>Progress:</strong> ${flight.progress.toFixed(1)}%</p>
                <p><strong>Status:</strong> <span class="flight-status ${flight.status}">${flight.status.replace('_', ' ').toUpperCase()}</span></p>
                <p><strong>Speed:</strong> ${flight.ground_speed} kts</p>
            </div>
        `).join('');
    }

    updateStatistics(flights) {
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
    }

    updateConnectionStatus(connected) {
        const status = document.getElementById('connection-status');
        if (connected) {
            status.textContent = 'Connected';
            status.className = 'status connected';
        } else {
            status.textContent = 'Disconnected';
            status.className = 'status disconnected';
        }
    }

    updateLastUpdate() {
        const now = new Date();
        document.getElementById('last-update').textContent = now.toLocaleTimeString();
    }

    async setTimeSpeed(speed) {
        try {
            const response = await fetch('/api/time_speed', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ speed })
            });
            
            if (response.ok) {
                this.timeSpeed = speed;
                console.log(`⚡ Time speed set to ${speed}x`);
            }
        } catch (error) {
            console.error('❌ Error setting time speed:', error);
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        sidebar.classList.toggle('hidden');
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    async loadMarketplace() {
        try {
            const aircraft = await this.fetchAPI('/api/marketplace');
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

        container.innerHTML = aircraft.slice(0, 10).map(plane => `
            <div class="aircraft-item">
                <h5>${plane.model}</h5>
                <p><strong>Capacity:</strong> ${plane.capacity} passengers</p>
                <p><strong>Range:</strong> ${plane.range.toLocaleString()} nm</p>
                <p><strong>Age:</strong> ${plane.age.toFixed(1)} years</p>
                <p class="price"><strong>Price:</strong> $${plane.price.toFixed(1)}M</p>
                <button class="btn btn-success" onclick="tracker.purchaseAircraft('${plane.id}', 'CASH')">
                    💰 Buy
                </button>
                <button class="btn btn-primary" onclick="tracker.purchaseAircraft('${plane.id}', 'LEASE')">
                    📋 Lease
                </button>
            </div>
        `).join('');
    }

    async purchaseAircraft(aircraftId, financingType) {
        try {
            const response = await fetch('/api/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    aircraft_id: aircraftId, 
                    financing_type: financingType 
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(`✅ ${result.message}`);
                this.loadMarketplace(); // Refresh marketplace
                this.loadInitialData(); // Refresh fleet
            } else {
                alert(`❌ ${result.message}`);
            }
        } catch (error) {
            console.error('❌ Error purchasing aircraft:', error);
            alert('❌ Purchase failed');
        }
    }

    populateAircraftSelect(aircraft) {
        const select = document.getElementById('aircraft-select');
        select.innerHTML = '<option value="">Select Aircraft</option>';
        
        aircraft.forEach(plane => {
            const option = document.createElement('option');
            option.value = plane.id;
            option.textContent = `${plane.registration} (${plane.airframeIcao})`;
            select.appendChild(option);
        });
    }

    populateRouteSelect(routes) {
        const select = document.getElementById('route-select');
        select.innerHTML = '<option value="">Select Route</option>';
        
        routes.forEach(route => {
            const option = document.createElement('option');
            option.value = route.id;
            option.textContent = `${route.departure_airport} → ${route.arrival_airport} (${route.distance_nm} nm)`;
            select.appendChild(option);
        });
    }

    async assignRoute() {
        const aircraftId = document.getElementById('aircraft-select').value;
        const routeId = document.getElementById('route-select').value;
        const frequency = parseInt(document.getElementById('frequency-input').value);
        const fare = parseFloat(document.getElementById('fare-input').value);

        if (!aircraftId || !routeId) {
            alert('Please select both aircraft and route');
            return;
        }

        try {
            const response = await fetch('/api/assign_route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    aircraft_id: aircraftId,
                    route_id: routeId,
                    frequency: frequency,
                    economy_fare: fare,
                    business_fare: fare * 3.5
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(`✅ ${result.message}`);
                this.loadInitialData(); // Refresh data
            } else {
                alert(`❌ ${result.message}`);
            }
        } catch (error) {
            console.error('❌ Error assigning route:', error);
            alert('❌ Route assignment failed');
        }
    }

    updateFleetList(aircraft) {
        const container = document.getElementById('fleet-list');
        
        if (aircraft.length === 0) {
            container.innerHTML = '<div class="no-data">No aircraft in fleet</div>';
            return;
        }

        container.innerHTML = aircraft.map(plane => `
            <div class="fleet-item">
                <h5>${plane.registration}</h5>
                <p><strong>Type:</strong> ${plane.airframeIcao}</p>
                <p><strong>Location:</strong> ${plane.logLocation || 'Unknown'}</p>
            </div>
        `).join('');
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
        
        // Update economics tab if visible
        if (document.getElementById('economics-tab').classList.contains('active')) {
            this.updateEconomicsTab(economics);
        }
    }

    updateEconomicsTab(economics) {
        // Financial metrics
        document.getElementById('monthly-revenue').textContent = `$${economics.monthly_revenue.toFixed(0)}`;
        document.getElementById('monthly-costs').textContent = `$${economics.monthly_costs.toFixed(0)}`;
        
        const netProfitElement = document.getElementById('net-profit');
        netProfitElement.textContent = `$${economics.net_profit.toFixed(0)}`;
        netProfitElement.className = 'metric-value ' + (economics.net_profit >= 0 ? 'positive' : 'negative');
        
        document.getElementById('roi').textContent = `${economics.roi.toFixed(1)}%`;
        
        // Cost breakdown
        const totalCosts = economics.monthly_costs || 1;
        const costs = economics.cost_breakdown;
        
        document.getElementById('fuel-cost').textContent = `$${costs.fuel.toFixed(0)}`;
        document.getElementById('crew-cost').textContent = `$${costs.crew.toFixed(0)}`;
        document.getElementById('maintenance-cost').textContent = `$${costs.maintenance.toFixed(0)}`;
        document.getElementById('fees-cost').textContent = `$${costs.airport_fees.toFixed(0)}`;
        
        // Update cost bar widths
        document.documentElement.style.setProperty('--fuel-width', `${(costs.fuel / totalCosts) * 100}%`);
        document.documentElement.style.setProperty('--crew-width', `${(costs.crew / totalCosts) * 100}%`);
        document.documentElement.style.setProperty('--maintenance-width', `${(costs.maintenance / totalCosts) * 100}%`);
        document.documentElement.style.setProperty('--fees-width', `${(costs.airport_fees / totalCosts) * 100}%`);
        
        // Route performance
        this.updateRoutePerformance(economics.route_performance);
    }

    updateRoutePerformance(routes) {
        const container = document.getElementById('route-performance');
        
        if (routes.length === 0) {
            container.innerHTML = '<div class="no-data">Assign routes to see profitability</div>';
            return;
        }
        
        container.innerHTML = routes.map(route => `
            <div class="route-performance-item">
                <div class="route-info">
                    <div class="route-name">${route.route}</div>
                    <div class="route-stats">${route.frequency}/week • ${route.distance} nm</div>
                </div>
                <div class="route-profit ${route.profit >= 0 ? 'positive' : 'negative'}">
                    $${route.profit.toFixed(0)}/mo
                </div>
            </div>
        `).join('');
    }

    async analyzeRoute() {
        const routeSelect = document.getElementById('route-select');
        const frequencyInput = document.getElementById('frequency-input');
        const fareInput = document.getElementById('fare-input');
        const analysisDiv = document.getElementById('route-analysis');
        
        if (!routeSelect.value) {
            analysisDiv.style.display = 'none';
            return;
        }
        
        try {
            const analysis = await fetch('/api/route_analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    route_id: parseInt(routeSelect.value),
                    frequency: parseInt(frequencyInput.value),
                    economy_fare: parseFloat(fareInput.value),
                    business_fare: parseFloat(fareInput.value) * 3.5
                })
            });
            
            const data = await analysis.json();
            
            if (data.error) {
                console.error('Analysis error:', data.error);
                return;
            }
            
            // Update analysis display
            document.getElementById('analysis-revenue').textContent = `$${data.revenue.monthly_revenue.toFixed(0)}`;
            document.getElementById('analysis-costs').textContent = `$${data.costs.total_monthly_cost.toFixed(0)}`;
            document.getElementById('analysis-profit').textContent = `$${data.profitability.monthly_profit.toFixed(0)}`;
            document.getElementById('analysis-margin').textContent = `${data.profitability.profit_margin.toFixed(1)}%`;
            
            // Update profitability indicator
            const indicator = document.getElementById('profitability-indicator');
            const profit = data.profitability.monthly_profit;
            const margin = data.profitability.profit_margin;
            
            if (profit > 0) {
                if (margin > 20) {
                    indicator.textContent = '🌟 Excellent profit margin! Highly recommended.';
                    indicator.className = 'profitability-indicator profitable';
                } else if (margin > 10) {
                    indicator.textContent = '✅ Good profit margin. Profitable route.';
                    indicator.className = 'profitability-indicator profitable';
                } else {
                    indicator.textContent = '⚠️ Low profit margin. Consider adjusting pricing.';
                    indicator.className = 'profitability-indicator marginal';
                }
            } else {
                indicator.textContent = '❌ Unprofitable route. Try reducing frequency or adjusting fares.';
                indicator.className = 'profitability-indicator unprofitable';
            }
            
            analysisDiv.style.display = 'block';
            
        } catch (error) {
            console.error('❌ Error analyzing route:', error);
        }
    }

    setup3DViewToggles() {
        // Fleet view toggles
        document.getElementById('fleet-2d-view').addEventListener('click', () => {
            this.switchFleetView('2d');
        });
        
        document.getElementById('fleet-3d-view').addEventListener('click', () => {
            this.switchFleetView('3d');
        });
        
        // Marketplace view toggles
        document.getElementById('marketplace-2d-view').addEventListener('click', () => {
            this.switchMarketplaceView('2d');
        });
        
        document.getElementById('marketplace-3d-view').addEventListener('click', () => {
            this.switchMarketplaceView('3d');
        });
    }

    switchFleetView(mode) {
        const list2D = document.getElementById('fleet-list');
        const gallery3D = document.getElementById('fleet-3d-gallery');
        const btn2D = document.getElementById('fleet-2d-view');
        const btn3D = document.getElementById('fleet-3d-view');
        
        if (mode === '3d') {
            list2D.style.display = 'none';
            gallery3D.style.display = 'flex';
            btn2D.classList.remove('active');
            btn3D.classList.add('active');
            
            // Initialize 3D fleet view
            this.init3DFleetView();
        } else {
            list2D.style.display = 'block';
            gallery3D.style.display = 'none';
            btn2D.classList.add('active');
            btn3D.classList.remove('active');
            
            // Dispose 3D viewer
            if (aircraft3DViewer) {
                aircraft3DViewer.dispose();
            }
        }
    }

    switchMarketplaceView(mode) {
        const list2D = document.getElementById('marketplace-list');
        const gallery3D = document.getElementById('marketplace-3d-gallery');
        const btn2D = document.getElementById('marketplace-2d-view');
        const btn3D = document.getElementById('marketplace-3d-view');
        
        if (mode === '3d') {
            list2D.style.display = 'none';
            gallery3D.style.display = 'flex';
            btn2D.classList.remove('active');
            btn3D.classList.add('active');
            
            // Initialize 3D marketplace view
            this.init3DMarketplaceView();
        } else {
            list2D.style.display = 'block';
            gallery3D.style.display = 'none';
            btn2D.classList.add('active');
            btn3D.classList.remove('active');
            
            // Dispose 3D viewer
            if (aircraft3DViewer) {
                aircraft3DViewer.dispose();
            }
        }
    }

    async init3DFleetView() {
        const container = document.getElementById('fleet-3d-container');
        if (!container || !aircraft3DViewer) return;
        
        // Show loading
        container.innerHTML = '<div class="aircraft-3d-loading"><i class="fas fa-spinner fa-spin"></i> Loading 3D View...</div>';
        
        // Setup 3D scene
        setTimeout(() => {
            if (aircraft3DViewer.setupScene(container)) {
                aircraft3DViewer.startAnimation();
                
                // Load first aircraft from fleet
                this.load3DFleetAircraft();
            } else {
                container.innerHTML = '<div class="aircraft-3d-error"><i class="fas fa-exclamation-triangle"></i><br>3D View Error</div>';
            }
        }, 100);
    }

    async init3DMarketplaceView() {
        const container = document.getElementById('marketplace-3d-container');
        if (!container || !aircraft3DViewer) return;
        
        // Show loading
        container.innerHTML = '<div class="aircraft-3d-loading"><i class="fas fa-spinner fa-spin"></i> Loading 3D View...</div>';
        
        // Setup 3D scene
        setTimeout(() => {
            if (aircraft3DViewer.setupScene(container)) {
                aircraft3DViewer.startAnimation();
                
                // Load marketplace aircraft
                this.load3DMarketplaceAircraft();
            } else {
                container.innerHTML = '<div class="aircraft-3d-error"><i class="fas fa-exclamation-triangle"></i><br>3D View Error</div>';
            }
        }, 100);
    }

    async load3DFleetAircraft() {
        try {
            const aircraft = await this.fetchAPI('/api/aircraft');
            if (aircraft.length > 0) {
                // Load first aircraft
                const firstAircraft = aircraft[0];
                const aircraftData = {
                    registration: firstAircraft.registration,
                    airframeIcao: firstAircraft.airframeIcao,
                    location: firstAircraft.logLocation
                };
                
                aircraft3DViewer.loadAircraft(firstAircraft.airframeIcao, aircraftData);
                
                // Add navigation for multiple aircraft
                this.add3DNavigation('fleet', aircraft);
            } else {
                const container = document.getElementById('fleet-3d-container');
                container.innerHTML = '<div class="no-data">No aircraft in fleet</div>';
            }
        } catch (error) {
            console.error('❌ Error loading 3D fleet:', error);
        }
    }

    async load3DMarketplaceAircraft() {
        try {
            const aircraft = await this.fetchAPI('/api/marketplace');
            if (aircraft.length > 0) {
                // Load first aircraft
                const firstAircraft = aircraft[0];
                const aircraftData = {
                    model: firstAircraft.model,
                    capacity: firstAircraft.capacity,
                    range: firstAircraft.range,
                    age: firstAircraft.age,
                    price: firstAircraft.price,
                    location: firstAircraft.location
                };
                
                aircraft3DViewer.loadAircraft(firstAircraft.model, aircraftData);
                
                // Add navigation for multiple aircraft
                this.add3DNavigation('marketplace', aircraft);
            } else {
                const container = document.getElementById('marketplace-3d-container');
                container.innerHTML = '<div class="no-data">No aircraft available</div>';
            }
        } catch (error) {
            console.error('❌ Error loading 3D marketplace:', error);
        }
    }

    add3DNavigation(type, aircraftList) {
        const container = document.getElementById(`${type}-3d-container`);
        if (!container || aircraftList.length <= 1) return;
        
        // Remove existing navigation
        const existingNav = container.querySelector('.model-navigation');
        if (existingNav) {
            existingNav.remove();
        }
        
        // Create navigation
        const navigation = document.createElement('div');
        navigation.className = 'model-navigation';
        
        // Add navigation buttons
        aircraftList.slice(0, 5).forEach((aircraft, index) => {
            const btn = document.createElement('div');
            btn.className = `model-nav-btn ${index === 0 ? 'active' : ''}`;
            btn.textContent = index + 1;
            btn.title = aircraft.registration || aircraft.model || `Aircraft ${index + 1}`;
            
            btn.addEventListener('click', () => {
                // Update active button
                navigation.querySelectorAll('.model-nav-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Load selected aircraft
                if (type === 'fleet') {
                    const aircraftData = {
                        registration: aircraft.registration,
                        airframeIcao: aircraft.airframeIcao,
                        location: aircraft.logLocation
                    };
                    aircraft3DViewer.loadAircraft(aircraft.airframeIcao, aircraftData);
                } else {
                    const aircraftData = {
                        model: aircraft.model,
                        capacity: aircraft.capacity,
                        range: aircraft.range,
                        age: aircraft.age,
                        price: aircraft.price,
                        location: aircraft.location
                    };
                    aircraft3DViewer.loadAircraft(aircraft.model, aircraftData);
                }
            });
            
            navigation.appendChild(btn);
        });
        
        container.appendChild(navigation);
    }
    
    setup3DFlightMode() {
        // 3D Flight mode toggle
        document.getElementById('toggle-3d-flight').addEventListener('click', () => {
            this.switch3DFlightMode(true);
        });
        
        document.getElementById('toggle-2d-map').addEventListener('click', () => {
            this.switch3DFlightMode(false);
        });
        
        // 3D Flight controls
        document.getElementById('flight-3d-follow').addEventListener('click', () => {
            this.set3DFlightCameraMode('follow');
        });
        
        document.getElementById('flight-3d-free').addEventListener('click', () => {
            this.set3DFlightCameraMode('free');
        });
        
        document.getElementById('flight-3d-reset').addEventListener('click', () => {
            this.reset3DFlightView();
        });
    }
    
    switch3DFlightMode(enable3D) {
        const mapContainer = document.getElementById('map');
        const flight3DViewer = document.getElementById('flight-3d-viewer');
        const toggle3DBtn = document.getElementById('toggle-3d-flight');
        const toggle2DBtn = document.getElementById('toggle-2d-map');
        
        if (enable3D) {
            // Hide 2D map, show 3D viewer
            mapContainer.style.display = 'none';
            flight3DViewer.style.display = 'block';
            toggle3DBtn.style.display = 'none';
            toggle2DBtn.style.display = 'inline-block';
            
            // Initialize 3D flight scene
            this.init3DFlightScene();
        } else {
            // Show 2D map, hide 3D viewer
            mapContainer.style.display = 'block';
            flight3DViewer.style.display = 'none';
            toggle3DBtn.style.display = 'inline-block';
            toggle2DBtn.style.display = 'none';
            
            // Dispose 3D flight scene
            this.dispose3DFlightScene();
        }
    }
    
    init3DFlightScene() {
        if (!window.Flight3DViewer) {
            // Create Flight3DViewer class if not exists
            this.createFlight3DViewer();
        }
        
        const container = document.getElementById('flight-3d-container');
        if (!container) return;
        
        // Initialize the 3D flight viewer
        this.flight3DViewer = new window.Flight3DViewer();
        
        if (this.flight3DViewer.setupScene(container)) {
            this.flight3DViewer.startAnimation();
            
            // Load current flights into 3D scene
            this.update3DFlights(this.currentFlights);
            
            console.log('🎆 3D Flight mode initialized');
        } else {
            container.innerHTML = '<div class="aircraft-3d-error"><i class="fas fa-exclamation-triangle"></i><br>3D Flight Mode Error</div>';
        }
    }
    
    dispose3DFlightScene() {
        if (this.flight3DViewer) {
            this.flight3DViewer.dispose();
            this.flight3DViewer = null;
        }
    }
    
    createFlight3DViewer() {
        // Create a specialized 3D viewer for flight tracking
        window.Flight3DViewer = class {
            constructor() {
                this.scene = null;
                this.camera = null;
                this.renderer = null;
                this.controls = null;
                this.aircraftModels = new Map();
                this.cameraMode = 'free';
                this.followTarget = null;
                this.animationId = null;
            }
            
            setupScene(container) {
                if (!container) return false;
                
                container.innerHTML = '';
                
                // Scene setup with realistic sky
                this.scene = new THREE.Scene();
                this.scene.background = new THREE.Color(0x87CEEB); // Sky blue
                this.scene.fog = new THREE.Fog(0x87CEEB, 100, 2000);
                
                // Camera setup
                const width = container.clientWidth;
                const height = container.clientHeight;
                this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 5000);
                this.camera.position.set(0, 500, 1000);
                this.camera.lookAt(0, 0, 0);
                
                // Renderer setup
                this.renderer = new THREE.WebGLRenderer({ antialias: true });
                this.renderer.setSize(width, height);
                this.renderer.shadowMap.enabled = true;
                this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                container.appendChild(this.renderer.domElement);
                
                // Controls
                this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
                this.controls.enableDamping = true;
                this.controls.dampingFactor = 0.05;
                this.controls.minDistance = 50;
                this.controls.maxDistance = 2000;
                this.controls.maxPolarAngle = Math.PI / 2.1;
                
                // Lighting setup
                const ambientLight = new THREE.AmbientLight(0x404040, 0.8);
                this.scene.add(ambientLight);
                
                const sunLight = new THREE.DirectionalLight(0xffffff, 1.2);
                sunLight.position.set(1000, 1000, 500);
                sunLight.castShadow = true;
                sunLight.shadow.mapSize.width = 4096;
                sunLight.shadow.mapSize.height = 4096;
                sunLight.shadow.camera.near = 0.5;
                sunLight.shadow.camera.far = 3000;
                sunLight.shadow.camera.left = -1000;
                sunLight.shadow.camera.right = 1000;
                sunLight.shadow.camera.top = 1000;
                sunLight.shadow.camera.bottom = -1000;
                this.scene.add(sunLight);
                
                // Create world environment
                this.createWorldEnvironment();
                
                return true;
            }
            
            createWorldEnvironment() {
                // Create a simple ground plane
                const groundGeometry = new THREE.PlaneGeometry(4000, 4000);
                const groundMaterial = new THREE.MeshLambertMaterial({ 
                    color: 0x90EE90,
                    transparent: true,
                    opacity: 0.8
                });
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.position.y = -50;
                ground.receiveShadow = true;
                this.scene.add(ground);
                
                // Add some clouds
                for (let i = 0; i < 20; i++) {
                    const cloudGeometry = new THREE.SphereGeometry(50 + Math.random() * 30, 8, 6);
                    const cloudMaterial = new THREE.MeshLambertMaterial({ 
                        color: 0xffffff,
                        transparent: true,
                        opacity: 0.6
                    });
                    const cloud = new THREE.Mesh(cloudGeometry, cloudMaterial);
                    cloud.position.set(
                        (Math.random() - 0.5) * 2000,
                        200 + Math.random() * 300,
                        (Math.random() - 0.5) * 2000
                    );
                    cloud.scale.set(
                        1 + Math.random() * 0.5,
                        0.5 + Math.random() * 0.3,
                        1 + Math.random() * 0.5
                    );
                    this.scene.add(cloud);
                }
            }
            
            updateFlights(flights) {
                // Clear existing aircraft
                this.aircraftModels.forEach(model => {
                    this.scene.remove(model.group);
                });
                this.aircraftModels.clear();
                
                // Add current flights
                flights.forEach(flight => {
                    this.addFlightToScene(flight);
                });
            }
            
            addFlightToScene(flight) {
                // Create aircraft model (use simplified models for performance)
                const aircraftGroup = this.createSimpleAircraftModel(flight);
                
                // Position aircraft based on lat/lon (simplified conversion)
                const x = (flight.lon + 180) * 10 - 1800; // Rough conversion
                const z = -(flight.lat - 90) * 10 + 900;
                const y = flight.altitude * 0.01; // Scale altitude
                
                aircraftGroup.position.set(x, y, z);
                
                // Orient aircraft based on heading
                aircraftGroup.rotation.y = -flight.heading * Math.PI / 180;
                
                this.scene.add(aircraftGroup);
                this.aircraftModels.set(flight.id, {
                    group: aircraftGroup,
                    flight: flight
                });
            }
            
            createSimpleAircraftModel(flight) {
                const group = new THREE.Group();
                
                // Simple aircraft body
                const bodyGeometry = new THREE.CylinderGeometry(2, 1, 20, 8);
                const bodyMaterial = new THREE.MeshPhongMaterial({ color: 0xffffff });
                const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
                body.rotation.z = Math.PI / 2;
                body.castShadow = true;
                group.add(body);
                
                // Wings
                const wingGeometry = new THREE.BoxGeometry(15, 1, 3);
                const wingMaterial = new THREE.MeshPhongMaterial({ color: 0xe0e0e0 });
                const wings = new THREE.Mesh(wingGeometry, wingMaterial);
                wings.position.y = -1;
                wings.castShadow = true;
                group.add(wings);
                
                // Tail
                const tailGeometry = new THREE.BoxGeometry(1, 8, 4);
                const tail = new THREE.Mesh(tailGeometry, wingMaterial);
                tail.position.x = -8;
                tail.position.y = 3;
                tail.castShadow = true;
                group.add(tail);
                
                // Color based on status
                const statusColors = {
                    'departing': 0x4CAF50,
                    'en_route': 0xf44336,
                    'arriving': 0xFF9800
                };
                const statusColor = statusColors[flight.status] || 0x666666;
                
                // Add status indicator
                const indicatorGeometry = new THREE.SphereGeometry(1.5, 8, 6);
                const indicatorMaterial = new THREE.MeshPhongMaterial({ 
                    color: statusColor,
                    emissive: statusColor,
                    emissiveIntensity: 0.3
                });
                const indicator = new THREE.Mesh(indicatorGeometry, indicatorMaterial);
                indicator.position.y = 5;
                group.add(indicator);
                
                // Add flight info label (simplified)
                const labelDiv = document.createElement('div');
                labelDiv.className = 'flight-3d-label';
                labelDiv.textContent = flight.name;
                labelDiv.style.cssText = `
                    position: absolute;
                    background: rgba(0,0,0,0.8);
                    color: white;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 12px;
                    pointer-events: none;
                    z-index: 100;
                `;
                
                return group;
            }
            
            setCameraMode(mode) {
                this.cameraMode = mode;
                
                if (mode === 'follow' && this.aircraftModels.size > 0) {
                    // Follow first aircraft
                    const firstAircraft = this.aircraftModels.values().next().value;
                    this.followTarget = firstAircraft.group;
                }
            }
            
            startAnimation() {
                const animate = () => {
                    this.animationId = requestAnimationFrame(animate);
                    
                    // Update camera based on mode
                    if (this.cameraMode === 'follow' && this.followTarget) {
                        const targetPos = this.followTarget.position;
                        this.camera.position.set(
                            targetPos.x - 100,
                            targetPos.y + 50,
                            targetPos.z + 100
                        );
                        this.camera.lookAt(targetPos);
                    } else if (this.controls) {
                        this.controls.update();
                    }
                    
                    if (this.renderer && this.scene && this.camera) {
                        this.renderer.render(this.scene, this.camera);
                    }
                };
                
                animate();
            }
            
            stopAnimation() {
                if (this.animationId) {
                    cancelAnimationFrame(this.animationId);
                    this.animationId = null;
                }
            }
            
            dispose() {
                this.stopAnimation();
                
                if (this.renderer) {
                    this.renderer.dispose();
                }
                
                this.scene = null;
                this.camera = null;
                this.renderer = null;
                this.controls = null;
                this.aircraftModels.clear();
            }
        };
    }
    
    update3DFlights(flights) {
        if (this.flight3DViewer) {
            this.flight3DViewer.updateFlights(flights);
        }
    }
    
    set3DFlightCameraMode(mode) {
        if (this.flight3DViewer) {
            this.flight3DViewer.setCameraMode(mode);
            
            // Update button states
            const followBtn = document.getElementById('flight-3d-follow');
            const freeBtn = document.getElementById('flight-3d-free');
            
            if (mode === 'follow') {
                followBtn.classList.add('active');
                freeBtn.classList.remove('active');
            } else {
                followBtn.classList.remove('active');
                freeBtn.classList.add('active');
            }
        }
    }
    
    reset3DFlightView() {
        if (this.flight3DViewer && this.flight3DViewer.camera) {
            this.flight3DViewer.camera.position.set(0, 500, 1000);
            this.flight3DViewer.camera.lookAt(0, 0, 0);
            if (this.flight3DViewer.controls) {
                this.flight3DViewer.controls.target.set(0, 0, 0);
                this.flight3DViewer.controls.update();
            }
        }
    }

    getAirportCoords() {
        // Return hardcoded airport coordinates for now
        return {
            'KJFK': {lat: 40.6413, lon: -73.7781},
            'KLAX': {lat: 33.9425, lon: -118.4081},
            'EGLL': {lat: 51.4700, lon: -0.4543},
            'EDDF': {lat: 50.0379, lon: 8.5622},
            'RJTT': {lat: 35.7653, lon: 140.3864},
            'OMDB': {lat: 25.2532, lon: 55.3657},
            'KATL': {lat: 33.6407, lon: -84.4277},
            'KORD': {lat: 41.9742, lon: -87.9073},
            'KBOS': {lat: 42.3656, lon: -71.0096},
            'KDCA': {lat: 38.8512, lon: -77.0402},
            'KLAS': {lat: 36.0840, lon: -115.1537},
            'KMCO': {lat: 28.4312, lon: -81.3081},
            'KSFO': {lat: 37.6213, lon: -122.3790},
            'YSSY': {lat: -33.9399, lon: 151.1753}
        };
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