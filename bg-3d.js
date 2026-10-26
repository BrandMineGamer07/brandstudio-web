// ========================================================
// BRAND STUDIO - ULTRA 3D CYBER SPACE & NEBULA BACKGROUND
// 60FPS High-Performance WebGL Three.js Engine
// ========================================================

(function () {
    function initBrand3D() {
        // Target container
        let container = document.getElementById('vanta-bg') || document.getElementById('brand-3d-bg');
        if (!container) {
            container = document.createElement('div');
            container.id = 'vanta-bg';
            container.className = 'fixed inset-0 pointer-events-none';
            container.style.zIndex = '-20';
            document.body.prepend(container);
        }

        // Check if Three.js is loaded, else load dynamically
        if (typeof THREE === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js';
            script.onload = () => setupScene(container);
            document.head.appendChild(script);
        } else {
            setupScene(container);
        }
    }

    function setupScene(container) {
        // Clear previous canvas if any
        container.innerHTML = '';

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 1, 2000);
        camera.position.z = 600;

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: false, powerPreference: 'high-performance' });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.domElement.style.position = 'fixed';
        renderer.domElement.style.top = '0';
        renderer.domElement.style.left = '0';
        renderer.domElement.style.width = '100vw';
        renderer.domElement.style.height = '100vh';
        renderer.domElement.style.pointerEvents = 'none';
        container.appendChild(renderer.domElement);

        // --- GENERATE GLOWING RADIAL SPRITE TEXTURE ON THE FLY ---
        function createGlowSprite() {
            const canvas = document.createElement('canvas');
            canvas.width = 64;
            canvas.height = 64;
            const ctx = canvas.getContext('2d');
            const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
            gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
            gradient.addColorStop(0.2, 'rgba(16, 185, 129, 0.9)');
            gradient.addColorStop(0.55, 'rgba(6, 182, 212, 0.35)');
            gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, 64, 64);
            return new THREE.CanvasTexture(canvas);
        }

        const glowTexture = createGlowSprite();

        // --- LAYER 1: VAST 3D STARFIELD NEBULA (2,000 Cosmic Stars) ---
        const starCount = 2000;
        const starGeo = new THREE.BufferGeometry();
        const starPositions = new Float32Array(starCount * 3);
        const starColors = new Float32Array(starCount * 3);

        const colorPalette = [
            new THREE.Color(0x10b981), // Emerald
            new THREE.Color(0x06b6d4), // Cyan
            new THREE.Color(0x34d399), // Mint
            new THREE.Color(0xa855f7), // Purple
            new THREE.Color(0xffffff)  // White
        ];

        for (let i = 0; i < starCount; i++) {
            // Spherical cosmic distribution
            const r = 300 + Math.random() * 900;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);

            starPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            starPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            starPositions[i * 3 + 2] = r * Math.cos(phi);

            // Assign subtle cosmic hue
            const col = colorPalette[Math.floor(Math.random() * colorPalette.length)];
            starColors[i * 3] = col.r;
            starColors[i * 3 + 1] = col.g;
            starColors[i * 3 + 2] = col.b;
        }

        starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
        starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

        const starMaterial = new THREE.PointsMaterial({
            size: 4.5,
            map: glowTexture,
            vertexColors: true,
            transparent: true,
            opacity: 0.85,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const starField = new THREE.Points(starGeo, starMaterial);
        scene.add(starField);

        // --- LAYER 2: FOREGROUND GLOWING CYBER PARTICLES (350 Floating Motes) ---
        const fgCount = 350;
        const fgGeo = new THREE.BufferGeometry();
        const fgPositions = new Float32Array(fgCount * 3);
        for (let i = 0; i < fgCount * 3; i += 3) {
            fgPositions[i] = (Math.random() - 0.5) * 1200;
            fgPositions[i + 1] = (Math.random() - 0.5) * 800;
            fgPositions[i + 2] = (Math.random() - 0.5) * 700 + 200;
        }
        fgGeo.setAttribute('position', new THREE.BufferAttribute(fgPositions, 3));

        const fgMaterial = new THREE.PointsMaterial({
            size: 8.0,
            map: glowTexture,
            color: 0x10b981,
            transparent: true,
            opacity: 0.7,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const fgParticles = new THREE.Points(fgGeo, fgMaterial);
        scene.add(fgParticles);

        // --- LAYER 3: 3D CYBER GEOMETRIC CONSTELLATION CORE ---
        // Subtle wireframe geometric orb floating in the background
        const geoCore = new THREE.IcosahedronGeometry(220, 1);
        const geoMat = new THREE.MeshBasicMaterial({
            color: 0x10b981,
            wireframe: true,
            transparent: true,
            opacity: 0.08,
            blending: THREE.AdditiveBlending
        });
        const cyberMesh = new THREE.Mesh(geoCore, geoMat);
        scene.add(cyberMesh);

        // Subtle outer cyan geometric ring
        const ringGeo = new THREE.TorusGeometry(320, 1.2, 16, 80);
        const ringMat = new THREE.MeshBasicMaterial({
            color: 0x06b6d4,
            transparent: true,
            opacity: 0.12,
            blending: THREE.AdditiveBlending
        });
        const cyberRing = new THREE.Mesh(ringGeo, ringMat);
        cyberRing.rotation.x = Math.PI / 3;
        scene.add(cyberRing);

        // --- MOUSE & GYRO INTERACTION ---
        let mouseX = 0;
        let mouseY = 0;
        let targetX = 0;
        let targetY = 0;
        let halfX = window.innerWidth / 2;
        let halfY = window.innerHeight / 2;

        window.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX - halfX) * 0.4;
            mouseY = (e.clientY - halfY) * 0.4;
        }, { passive: true });

        // Touch parallax on mobile
        window.addEventListener('touchmove', (e) => {
            if (e.touches.length > 0) {
                mouseX = (e.touches[0].clientX - halfX) * 0.3;
                mouseY = (e.touches[0].clientY - halfY) * 0.3;
            }
        }, { passive: true });

        // --- ANIMATION LOOP (LOCKED TO 60FPS SMOOTH DRIFT) ---
        let clock = new THREE.Clock();

        function animate() {
            requestAnimationFrame(animate);

            const elapsedTime = clock.getElapsedTime();

            // Smooth parallax lerp
            targetX += (mouseX - targetX) * 0.04;
            targetY += (mouseY - targetY) * 0.04;

            camera.position.x = targetX * 0.8;
            camera.position.y = -targetY * 0.8;
            camera.lookAt(scene.position);

            // Cosmic rotations
            starField.rotation.y = elapsedTime * 0.015;
            starField.rotation.x = elapsedTime * 0.008;

            fgParticles.rotation.y = -elapsedTime * 0.02;
            fgParticles.rotation.z = elapsedTime * 0.01;

            // Cyber geometric floating rotation & pulsation
            cyberMesh.rotation.x = elapsedTime * 0.05;
            cyberMesh.rotation.y = elapsedTime * 0.08;
            cyberRing.rotation.z = elapsedTime * 0.04;

            const scalePulse = 1 + Math.sin(elapsedTime * 0.8) * 0.05;
            cyberMesh.scale.set(scalePulse, scalePulse, scalePulse);

            renderer.render(scene, camera);
        }

        animate();

        // --- RESIZE HANDLER ---
        window.addEventListener('resize', () => {
            halfX = window.innerWidth / 2;
            halfY = window.innerHeight / 2;
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }, { passive: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBrand3D);
    } else {
        initBrand3D();
    }
})();
