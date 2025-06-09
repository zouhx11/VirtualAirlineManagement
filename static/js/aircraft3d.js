/**
 * Aircraft 3D Viewer Controller
 * Handles 3D model loading, display, and interaction
 */

class Aircraft3DViewer {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.currentModel = null;
        this.models = new Map(); // Cache loaded models
        this.currentContainer = null;
        this.animationId = null;
        
        // Aircraft model mappings (simplified for now)
        this.aircraftModels = {
            // Map aircraft types to model files
            'A320': 'generic_airliner.gltf',
            'A321': 'generic_airliner.gltf',
            'A330': 'generic_widebody.gltf',
            'A350': 'generic_widebody.gltf',
            'B737': 'generic_airliner.gltf',
            'B738': 'generic_airliner.gltf',
            'B777': 'generic_widebody.gltf',
            'B787': 'generic_widebody.gltf',
            'default': 'generic_aircraft.gltf'
        };
        
        this.init();
    }

    init() {
        console.log('🎮 Initializing Aircraft 3D Viewer...');
        this.createDefaultModels();
    }

    createDefaultModels() {
        // Create procedural 3D aircraft models using Three.js geometry
        // This is our fallback when GLTF models aren't available
        this.createGenericAircraftModel();
        this.createGenericAirlinerModel();
        this.createGenericWidebodyModel();
    }

    createGenericAircraftModel() {
        const group = new THREE.Group();
        
        // Enhanced materials with realistic properties
        const fuselageMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xffffff,
            shininess: 100,
            specular: 0x222222
        });
        const wingMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xe8e8e8,
            shininess: 80,
            specular: 0x111111
        });
        const engineMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x444444,
            shininess: 200,
            specular: 0x666666
        });
        
        // More detailed fuselage with nose cone
        const fuselageGeometry = new THREE.CylinderGeometry(0.8, 0.6, 12, 16);
        const fuselage = new THREE.Mesh(fuselageGeometry, fuselageMaterial);
        fuselage.rotation.z = Math.PI / 2;
        fuselage.castShadow = true;
        fuselage.receiveShadow = true;
        group.add(fuselage);
        
        // Nose cone
        const noseGeometry = new THREE.ConeGeometry(0.6, 2, 12);
        const nose = new THREE.Mesh(noseGeometry, fuselageMaterial);
        nose.position.x = 7;
        nose.rotation.z = -Math.PI / 2;
        nose.castShadow = true;
        group.add(nose);
        
        // Wings with better shape
        const wingGeometry = new THREE.BoxGeometry(8, 0.3, 2.5);
        const wings = new THREE.Mesh(wingGeometry, wingMaterial);
        wings.position.y = -0.5;
        wings.castShadow = true;
        wings.receiveShadow = true;
        group.add(wings);
        
        // Wing tips
        const wingtipGeometry = new THREE.ConeGeometry(0.3, 1, 6);
        const wingtipMaterial = new THREE.MeshPhongMaterial({ color: 0xff4444 });
        
        const wingtip1 = new THREE.Mesh(wingtipGeometry, wingtipMaterial);
        wingtip1.position.set(0, -0.5, 4.2);
        wingtip1.rotation.z = Math.PI / 2;
        group.add(wingtip1);
        
        const wingtip2 = new THREE.Mesh(wingtipGeometry, wingtipMaterial);
        wingtip2.position.set(0, -0.5, -4.2);
        wingtip2.rotation.z = -Math.PI / 2;
        group.add(wingtip2);
        
        // Vertical tail
        const tailGeometry = new THREE.BoxGeometry(0.3, 3.5, 2.5);
        const tail = new THREE.Mesh(tailGeometry, wingMaterial);
        tail.position.x = -5;
        tail.position.y = 1.5;
        tail.castShadow = true;
        group.add(tail);
        
        // Horizontal stabilizer
        const stabGeometry = new THREE.BoxGeometry(3, 0.2, 1);
        const stab = new THREE.Mesh(stabGeometry, wingMaterial);
        stab.position.x = -5;
        stab.position.y = 0.5;
        stab.castShadow = true;
        group.add(stab);
        
        // Enhanced engines with details
        const engineGeometry = new THREE.CylinderGeometry(0.5, 0.4, 2.5, 12);
        
        const engine1 = new THREE.Mesh(engineGeometry, engineMaterial);
        engine1.position.set(1, -1.2, 2.5);
        engine1.rotation.z = Math.PI / 2;
        engine1.castShadow = true;
        group.add(engine1);
        
        const engine2 = new THREE.Mesh(engineGeometry, engineMaterial);
        engine2.position.set(1, -1.2, -2.5);
        engine2.rotation.z = Math.PI / 2;
        engine2.castShadow = true;
        group.add(engine2);
        
        // Engine intakes
        const intakeGeometry = new THREE.RingGeometry(0.3, 0.5, 16);
        const intakeMaterial = new THREE.MeshPhongMaterial({ color: 0x111111 });
        
        const intake1 = new THREE.Mesh(intakeGeometry, intakeMaterial);
        intake1.position.set(2.2, -1.2, 2.5);
        intake1.rotation.y = Math.PI / 2;
        group.add(intake1);
        
        const intake2 = new THREE.Mesh(intakeGeometry, intakeMaterial);
        intake2.position.set(2.2, -1.2, -2.5);
        intake2.rotation.y = Math.PI / 2;
        group.add(intake2);
        
        // Windows
        const windowGeometry = new THREE.PlaneGeometry(8, 0.5);
        const windowMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x4488ff,
            transparent: true,
            opacity: 0.7
        });
        const windows = new THREE.Mesh(windowGeometry, windowMaterial);
        windows.position.set(0, 0.9, 0);
        windows.rotation.x = -Math.PI / 2;
        group.add(windows);
        
        // Store the model
        this.models.set('generic_aircraft', group);
        console.log('✈️ Created enhanced generic aircraft model');
    }

    createGenericAirlinerModel() {
        const group = new THREE.Group();
        
        // Enhanced materials for realistic appearance
        const fuselageMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xffffff,
            shininess: 150,
            specular: 0x333333,
            transparent: false
        });
        const wingMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xe8e8e8,
            shininess: 120,
            specular: 0x222222
        });
        const engineMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x444444,
            shininess: 200,
            specular: 0x777777,
            emissive: 0x111111
        });
        
        // Enhanced fuselage with nose cone
        const fuselageGeometry = new THREE.CylinderGeometry(1.2, 1.0, 16, 20);
        const fuselage = new THREE.Mesh(fuselageGeometry, fuselageMaterial);
        fuselage.rotation.z = Math.PI / 2;
        fuselage.castShadow = true;
        fuselage.receiveShadow = true;
        group.add(fuselage);
        
        // Nose cone with better shape
        const noseGeometry = new THREE.ConeGeometry(1.0, 3, 16);
        const nose = new THREE.Mesh(noseGeometry, fuselageMaterial);
        nose.position.x = 9.5;
        nose.rotation.z = -Math.PI / 2;
        nose.castShadow = true;
        group.add(nose);
        
        // Wings with better aerodynamic shape
        const wingShape = new THREE.Shape();
        wingShape.moveTo(-6, 0);
        wingShape.lineTo(6, 0);
        wingShape.lineTo(4, 2.5);
        wingShape.lineTo(-4, 2.5);
        wingShape.lineTo(-6, 0);
        
        const wingGeometry = new THREE.ExtrudeGeometry(wingShape, {
            depth: 0.3,
            bevelEnabled: true,
            bevelThickness: 0.1,
            bevelSize: 0.1
        });
        const wings = new THREE.Mesh(wingGeometry, wingMaterial);
        wings.position.set(0, -0.8, -1.25);
        wings.rotation.x = -Math.PI / 2;
        wings.castShadow = true;
        wings.receiveShadow = true;
        group.add(wings);
        
        // Winglets
        const wingletGeometry = new THREE.BoxGeometry(0.2, 1.5, 0.8);
        const wingletMaterial = new THREE.MeshPhongMaterial({ color: 0x2196F3 });
        
        const winglet1 = new THREE.Mesh(wingletGeometry, wingletMaterial);
        winglet1.position.set(4, 0, 1.3);
        winglet1.rotation.z = Math.PI / 12;
        winglet1.castShadow = true;
        group.add(winglet1);
        
        const winglet2 = new THREE.Mesh(wingletGeometry, wingletMaterial);
        winglet2.position.set(4, 0, -1.3);
        winglet2.rotation.z = -Math.PI / 12;
        winglet2.castShadow = true;
        group.add(winglet2);
        
        // Vertical tail with better proportions
        const tailGeometry = new THREE.BoxGeometry(0.4, 5, 3.5);
        const tail = new THREE.Mesh(tailGeometry, wingMaterial);
        tail.position.x = -7;
        tail.position.y = 2;
        tail.castShadow = true;
        tail.receiveShadow = true;
        group.add(tail);
        
        // Horizontal stabilizer
        const stabGeometry = new THREE.BoxGeometry(4, 0.3, 1.2);
        const stab = new THREE.Mesh(stabGeometry, wingMaterial);
        stab.position.x = -7;
        stab.position.y = 0.5;
        stab.castShadow = true;
        group.add(stab);
        
        // Enhanced engines with details
        const engineGeometry = new THREE.CylinderGeometry(0.7, 0.6, 3.5, 16);
        
        const engine1 = new THREE.Mesh(engineGeometry, engineMaterial);
        engine1.position.set(2, -1.5, 3);
        engine1.rotation.z = Math.PI / 2;
        engine1.castShadow = true;
        group.add(engine1);
        
        const engine2 = new THREE.Mesh(engineGeometry, engineMaterial);
        engine2.position.set(2, -1.5, -3);
        engine2.rotation.z = Math.PI / 2;
        engine2.castShadow = true;
        group.add(engine2);
        
        // Engine intakes with realistic appearance
        const intakeGeometry = new THREE.RingGeometry(0.5, 0.7, 16);
        const intakeMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x111111,
            emissive: 0x222222
        });
        
        const intake1 = new THREE.Mesh(intakeGeometry, intakeMaterial);
        intake1.position.set(3.7, -1.5, 3);
        intake1.rotation.y = Math.PI / 2;
        group.add(intake1);
        
        const intake2 = new THREE.Mesh(intakeGeometry, intakeMaterial);
        intake2.position.set(3.7, -1.5, -3);
        intake2.rotation.y = Math.PI / 2;
        group.add(intake2);
        
        // Cockpit windows
        const windowGeometry = new THREE.PlaneGeometry(3, 1);
        const windowMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x4488ff,
            transparent: true,
            opacity: 0.8,
            emissive: 0x002244
        });
        const windows = new THREE.Mesh(windowGeometry, windowMaterial);
        windows.position.set(6, 0.9, 0);
        windows.rotation.x = -Math.PI / 2;
        group.add(windows);
        
        // Passenger windows along fuselage
        for (let i = -4; i <= 4; i += 1.5) {
            const passengerWindow = new THREE.Mesh(
                new THREE.PlaneGeometry(0.3, 0.4),
                new THREE.MeshPhongMaterial({ 
                    color: 0x6699ff,
                    transparent: true,
                    opacity: 0.9
                })
            );
            passengerWindow.position.set(i, 1.1, 0);
            passengerWindow.rotation.x = -Math.PI / 2;
            group.add(passengerWindow);
        }
        
        // Enhanced airline livery
        const stripeGeometry = new THREE.BoxGeometry(15, 0.15, 0.4);
        const stripeMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x2196F3,
            shininess: 100
        });
        const stripe = new THREE.Mesh(stripeGeometry, stripeMaterial);
        stripe.position.y = 0.5;
        group.add(stripe);
        
        // Logo area (simple geometric logo)
        const logoGeometry = new THREE.BoxGeometry(2, 0.2, 1.5);
        const logoMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x4CAF50,
            shininess: 150
        });
        const logo = new THREE.Mesh(logoGeometry, logoMaterial);
        logo.position.set(-3, 0.8, 0);
        group.add(logo);
        
        this.models.set('generic_airliner', group);
        console.log('✈️ Created enhanced airliner model with realistic materials');
    }

    createGenericWidebodyModel() {
        const group = new THREE.Group();
        
        // Premium materials for widebody
        const fuselageMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xf8f8f8,
            shininess: 180,
            specular: 0x444444,
            reflectivity: 0.3
        });
        const wingMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xe8e8e8,
            shininess: 140,
            specular: 0x333333
        });
        const engineMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x333333,
            shininess: 220,
            specular: 0x888888,
            emissive: 0x111111
        });
        
        // Larger, more detailed fuselage
        const fuselageGeometry = new THREE.CylinderGeometry(1.8, 1.5, 22, 24);
        const fuselage = new THREE.Mesh(fuselageGeometry, fuselageMaterial);
        fuselage.rotation.z = Math.PI / 2;
        fuselage.castShadow = true;
        fuselage.receiveShadow = true;
        group.add(fuselage);
        
        // Enhanced nose with better aerodynamics
        const noseGeometry = new THREE.ConeGeometry(1.5, 4, 20);
        const nose = new THREE.Mesh(noseGeometry, fuselageMaterial);
        nose.position.x = 13;
        nose.rotation.z = -Math.PI / 2;
        nose.castShadow = true;
        group.add(nose);
        
        // Larger wings with swept design
        const wingShape = new THREE.Shape();
        wingShape.moveTo(-8, 0);
        wingShape.lineTo(8, 0);
        wingShape.lineTo(6, 4);
        wingShape.lineTo(-6, 4);
        wingShape.lineTo(-8, 0);
        
        const wingGeometry = new THREE.ExtrudeGeometry(wingShape, {
            depth: 0.5,
            bevelEnabled: true,
            bevelThickness: 0.2,
            bevelSize: 0.1
        });
        const wings = new THREE.Mesh(wingGeometry, wingMaterial);
        wings.position.set(0, -1.2, -2);
        wings.rotation.x = -Math.PI / 2;
        wings.rotation.z = Math.PI / 24; // Slight sweep
        wings.castShadow = true;
        wings.receiveShadow = true;
        group.add(wings);
        
        // Enhanced winglets
        const wingletGeometry = new THREE.BoxGeometry(0.3, 2.5, 1.2);
        const wingletMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x2196F3,
            shininess: 150
        });
        
        const winglet1 = new THREE.Mesh(wingletGeometry, wingletMaterial);
        winglet1.position.set(6, 0.5, 2.2);
        winglet1.rotation.z = Math.PI / 8;
        winglet1.rotation.x = Math.PI / 16;
        winglet1.castShadow = true;
        group.add(winglet1);
        
        const winglet2 = new THREE.Mesh(wingletGeometry, wingletMaterial);
        winglet2.position.set(6, 0.5, -2.2);
        winglet2.rotation.z = -Math.PI / 8;
        winglet2.rotation.x = -Math.PI / 16;
        winglet2.castShadow = true;
        group.add(winglet2);
        
        // Larger tail assembly
        const tailGeometry = new THREE.BoxGeometry(0.5, 6, 5);
        const tail = new THREE.Mesh(tailGeometry, wingMaterial);
        tail.position.x = -9;
        tail.position.y = 2.5;
        tail.castShadow = true;
        tail.receiveShadow = true;
        group.add(tail);
        
        // Horizontal stabilizer
        const stabGeometry = new THREE.BoxGeometry(5, 0.4, 1.5);
        const stab = new THREE.Mesh(stabGeometry, wingMaterial);
        stab.position.x = -9;
        stab.position.y = 0.8;
        stab.castShadow = true;
        group.add(stab);
        
        // Large twin engines with realistic details
        const engineGeometry = new THREE.CylinderGeometry(1.0, 0.9, 5, 20);
        
        const engine1 = new THREE.Mesh(engineGeometry, engineMaterial);
        engine1.position.set(3, -2.2, 5);
        engine1.rotation.z = Math.PI / 2;
        engine1.castShadow = true;
        group.add(engine1);
        
        const engine2 = new THREE.Mesh(engineGeometry, engineMaterial);
        engine2.position.set(3, -2.2, -5);
        engine2.rotation.z = Math.PI / 2;
        engine2.castShadow = true;
        group.add(engine2);
        
        // Engine nacelles
        const nacelleGeometry = new THREE.CylinderGeometry(1.1, 1.0, 6, 16);
        const nacelleMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x666666,
            shininess: 100
        });
        
        const nacelle1 = new THREE.Mesh(nacelleGeometry, nacelleMaterial);
        nacelle1.position.set(3, -2.2, 5);
        nacelle1.rotation.z = Math.PI / 2;
        group.add(nacelle1);
        
        const nacelle2 = new THREE.Mesh(nacelleGeometry, nacelleMaterial);
        nacelle2.position.set(3, -2.2, -5);
        nacelle2.rotation.z = Math.PI / 2;
        group.add(nacelle2);
        
        // Large engine intakes
        const intakeGeometry = new THREE.RingGeometry(0.7, 1.0, 20);
        const intakeMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x111111,
            emissive: 0x333333
        });
        
        const intake1 = new THREE.Mesh(intakeGeometry, intakeMaterial);
        intake1.position.set(5.5, -2.2, 5);
        intake1.rotation.y = Math.PI / 2;
        group.add(intake1);
        
        const intake2 = new THREE.Mesh(intakeGeometry, intakeMaterial);
        intake2.position.set(5.5, -2.2, -5);
        intake2.rotation.y = Math.PI / 2;
        group.add(intake2);
        
        // Cockpit windows
        const cockpitGeometry = new THREE.PlaneGeometry(4, 1.5);
        const cockpitMaterial = new THREE.MeshPhongMaterial({ 
            color: 0x4488ff,
            transparent: true,
            opacity: 0.8,
            emissive: 0x002244
        });
        const cockpit = new THREE.Mesh(cockpitGeometry, cockpitMaterial);
        cockpit.position.set(8, 1.2, 0);
        cockpit.rotation.x = -Math.PI / 2;
        group.add(cockpit);
        
        // Multiple rows of passenger windows
        for (let row = 0; row < 3; row++) {
            for (let i = -8; i <= 6; i += 1.2) {
                const passengerWindow = new THREE.Mesh(
                    new THREE.PlaneGeometry(0.4, 0.5),
                    new THREE.MeshPhongMaterial({ 
                        color: 0x6699ff,
                        transparent: true,
                        opacity: 0.9
                    })
                );
                passengerWindow.position.set(i, 1.6 - row * 0.8, 0);
                passengerWindow.rotation.x = -Math.PI / 2;
                group.add(passengerWindow);
            }
        }
        
        // Premium airline livery with multiple stripes
        const stripe1Geometry = new THREE.BoxGeometry(20, 0.2, 0.5);
        const stripe1Material = new THREE.MeshPhongMaterial({ 
            color: 0x4CAF50,
            shininess: 120
        });
        const stripe1 = new THREE.Mesh(stripe1Geometry, stripe1Material);
        stripe1.position.y = 1.0;
        group.add(stripe1);
        
        const stripe2Geometry = new THREE.BoxGeometry(20, 0.2, 0.5);
        const stripe2Material = new THREE.MeshPhongMaterial({ 
            color: 0x2196F3,
            shininess: 120
        });
        const stripe2 = new THREE.Mesh(stripe2Geometry, stripe2Material);
        stripe2.position.y = 0.4;
        group.add(stripe2);
        
        // Premium logo area
        const logoGeometry = new THREE.BoxGeometry(3, 0.3, 2);
        const logoMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xFF9800,
            shininess: 200,
            emissive: 0x331100
        });
        const logo = new THREE.Mesh(logoGeometry, logoMaterial);
        logo.position.set(-2, 1.2, 0);
        group.add(logo);
        
        this.models.set('generic_widebody', group);
        console.log('✈️ Created enhanced widebody model with premium materials');
    }

    setupScene(container) {
        if (!container) return false;
        
        this.currentContainer = container;
        
        // Clear any existing content
        container.innerHTML = '';
        
        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);
        
        // Camera setup
        const width = container.clientWidth;
        const height = container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(20, 8, 20);
        this.camera.lookAt(0, 0, 0);
        
        // Renderer setup
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(this.renderer.domElement);
        
        // Controls setup
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.1;
        this.controls.autoRotate = true;
        this.controls.autoRotateSpeed = 2;
        this.controls.target.set(0, 0, 0);
        this.controls.minDistance = 5;
        this.controls.maxDistance = 50;
        
        // Lighting setup
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(20, 20, 20);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        const spotLight = new THREE.SpotLight(0x4CAF50, 0.5);
        spotLight.position.set(-10, 15, 10);
        this.scene.add(spotLight);
        
        // Add controls overlay
        this.addControlsOverlay(container);
        
        console.log('🎬 3D Scene setup complete');
        return true;
    }

    addControlsOverlay(container) {
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'aircraft-3d-controls';
        controlsDiv.innerHTML = `
            <button class="btn btn-secondary" id="reset-view" title="Reset View">
                <i class="fas fa-home"></i>
            </button>
            <button class="btn btn-secondary" id="toggle-rotation" title="Toggle Auto-Rotation">
                <i class="fas fa-sync-alt"></i>
            </button>
        `;
        container.appendChild(controlsDiv);
        
        // Add event listeners
        controlsDiv.querySelector('#reset-view').addEventListener('click', () => {
            this.resetView();
        });
        
        controlsDiv.querySelector('#toggle-rotation').addEventListener('click', () => {
            this.controls.autoRotate = !this.controls.autoRotate;
        });
    }

    loadAircraft(aircraftType, aircraftData) {
        if (!this.scene) {
            console.error('❌ Scene not initialized');
            return false;
        }
        
        // Clear current model
        if (this.currentModel) {
            this.scene.remove(this.currentModel);
        }
        
        // Determine which model to use
        let modelKey = 'generic_aircraft';
        if (aircraftType) {
            const type = aircraftType.toUpperCase();
            if (type.includes('A320') || type.includes('A321') || type.includes('B737') || type.includes('B738')) {
                modelKey = 'generic_airliner';
            } else if (type.includes('A330') || type.includes('A350') || type.includes('B777') || type.includes('B787')) {
                modelKey = 'generic_widebody';
            }
        }
        
        // Load the model
        const model = this.models.get(modelKey);
        if (model) {
            // Clone the model so we can have multiple instances
            this.currentModel = model.clone();
            this.scene.add(this.currentModel);
            
            // Center the model properly
            const box = new THREE.Box3().setFromObject(this.currentModel);
            const center = box.getCenter(new THREE.Vector3());
            this.currentModel.position.sub(center); // Center the model
            
            // Scale the model appropriately
            const size = box.getSize(new THREE.Vector3());
            const maxSize = Math.max(size.x, size.y, size.z);
            const targetSize = 8; // Desired size
            const scale = targetSize / maxSize;
            this.currentModel.scale.setScalar(scale);
            
            // Update aircraft info if provided
            if (aircraftData) {
                this.updateAircraftInfo(aircraftData);
            }
            
            console.log(`✈️ Loaded ${modelKey} model for ${aircraftType || 'unknown aircraft'}`);
            return true;
        }
        
        console.error(`❌ Model ${modelKey} not found`);
        return false;
    }

    updateAircraftInfo(aircraftData) {
        const infoContainer = this.currentContainer.parentElement.querySelector('.aircraft-3d-info');
        if (!infoContainer) return;
        
        infoContainer.innerHTML = `
            <h5>${aircraftData.registration || aircraftData.model || 'Aircraft'}</h5>
            <p><strong>Type:</strong> ${aircraftData.airframeIcao || aircraftData.model || 'Unknown'}</p>
            ${aircraftData.age !== undefined ? `<p><strong>Age:</strong> ${aircraftData.age} years</p>` : ''}
            ${aircraftData.capacity ? `<p><strong>Capacity:</strong> ${aircraftData.capacity} passengers</p>` : ''}
            ${aircraftData.range ? `<p><strong>Range:</strong> ${aircraftData.range.toLocaleString()} nm</p>` : ''}
            ${aircraftData.price !== undefined ? `<p><strong>Price:</strong> $${aircraftData.price}M</p>` : ''}
            ${aircraftData.location ? `<p><strong>Location:</strong> ${aircraftData.location}</p>` : ''}
        `;
    }

    startAnimation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        const animate = () => {
            this.animationId = requestAnimationFrame(animate);
            
            if (this.controls) {
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

    resetView() {
        if (this.camera && this.controls) {
            this.camera.position.set(20, 8, 20);
            this.camera.lookAt(0, 0, 0);
            this.controls.target.set(0, 0, 0);
            this.controls.update();
        }
    }

    dispose() {
        this.stopAnimation();
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.currentContainer) {
            this.currentContainer.innerHTML = '';
        }
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.currentModel = null;
        this.currentContainer = null;
    }

    // Handle window resize
    onWindowResize() {
        if (!this.currentContainer || !this.camera || !this.renderer) return;
        
        const width = this.currentContainer.clientWidth;
        const height = this.currentContainer.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
}

// Global 3D viewer instance
let aircraft3DViewer = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    aircraft3DViewer = new Aircraft3DViewer();
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (aircraft3DViewer) {
            aircraft3DViewer.onWindowResize();
        }
    });
});

// Export for use in other scripts
window.Aircraft3DViewer = Aircraft3DViewer;