/**
 * Dukaan Dost AI - 3D Kirana Store WebGL Scene (Three.js)
 * Features 3D Kirana Shop, Floating Rice Bags, Soaps, Milk Packets,
 * Glowing AI Core, Particle field, and Neon Lighting.
 */

window.initKirana3DScene = function (containerId) {
  const container = document.getElementById(containerId);
  if (!container || typeof THREE === 'undefined') return;

  const width = container.clientWidth || 600;
  const height = container.clientHeight || 550;

  // 1. Scene, Camera, Renderer
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x070913, 0.045);

  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 1.2, 5.8);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  container.appendChild(renderer.domElement);

  // 2. Lighting System (Cyber-Kirana Neon Theme)
  const ambientLight = new THREE.AmbientLight(0x231a4a, 1.2);
  scene.add(ambientLight);

  const purpleLight = new THREE.PointLight(0xa855f7, 3.5, 12);
  purpleLight.position.set(-2, 2.5, 2);
  scene.add(purpleLight);

  const mintLight = new THREE.PointLight(0x10b981, 3.8, 12);
  mintLight.position.set(2.5, 1.8, 1.5);
  scene.add(mintLight);

  const topSpot = new THREE.SpotLight(0xffffff, 1.8);
  topSpot.position.set(0, 5, 3);
  topSpot.angle = Math.PI / 4;
  topSpot.penumbra = 0.5;
  scene.add(topSpot);

  // Group to hold all 3D shop elements for rotation
  const shopGroup = new THREE.Group();
  scene.add(shopGroup);

  // 3. 3D Kirana Store Architecture
  // Counter Table
  const counterGeo = new THREE.BoxGeometry(2.8, 0.85, 1.1);
  const counterMat = new THREE.MeshStandardMaterial({
    color: 0x141b34,
    roughness: 0.35,
    metalness: 0.65
  });
  const counter = new THREE.Mesh(counterGeo, counterMat);
  counter.position.set(0, -0.9, 0);
  shopGroup.add(counter);

  // Counter Top Glass/Neon Trim
  const trimGeo = new THREE.BoxGeometry(2.85, 0.06, 1.15);
  const trimMat = new THREE.MeshStandardMaterial({
    color: 0x10b981,
    emissive: 0x10b981,
    emissiveIntensity: 0.6
  });
  const trim = new THREE.Mesh(trimGeo, trimMat);
  trim.position.set(0, -0.45, 0);
  shopGroup.add(trim);

  // Kirana Awning / Canopy (Striped Traditional Canopy)
  const canopyGroup = new THREE.Group();
  const stripeCount = 9;
  const stripeWidth = 2.8 / stripeCount;
  for (let i = 0; i < stripeCount; i++) {
    const sGeo = new THREE.BoxGeometry(stripeWidth, 0.08, 1.4);
    const isPurple = i % 2 === 0;
    const sMat = new THREE.MeshStandardMaterial({
      color: isPurple ? 0x8b5cf6 : 0x10b981,
      roughness: 0.5,
      emissive: isPurple ? 0x7c3aed : 0x059669,
      emissiveIntensity: 0.2
    });
    const stripe = new THREE.Mesh(sGeo, sMat);
    stripe.position.set(-1.4 + (i * stripeWidth) + stripeWidth / 2, 1.7, 0.4);
    stripe.rotation.x = 0.28;
    canopyGroup.add(stripe);
  }
  shopGroup.add(canopyGroup);

  // Back Grocery Shelves
  const shelfGeo = new THREE.BoxGeometry(3.0, 0.08, 0.6);
  const shelfMat = new THREE.MeshStandardMaterial({ color: 0x1f294d, roughness: 0.6 });
  for (let y = 0.2; y <= 1.4; y += 0.5) {
    const shelf = new THREE.Mesh(shelfGeo, shelfMat);
    shelf.position.set(0, y, -0.6);
    shopGroup.add(shelf);
  }

  // 4. Floating Grocery Items
  const floatingItems = [];

  // (A) 3D Rice Bag (సోనా మసూరి బియ్యం / Burlap Sack)
  const bagGeo = new THREE.CylinderGeometry(0.24, 0.28, 0.6, 16);
  const bagMat = new THREE.MeshStandardMaterial({
    color: 0xd4a373,
    roughness: 0.9,
    metalness: 0.1
  });
  const riceBag = new THREE.Mesh(bagGeo, bagMat);
  riceBag.position.set(-1.4, 0.35, 0.8);
  riceBag.rotation.set(0.15, 0.3, -0.1);
  shopGroup.add(riceBag);
  floatingItems.push({ mesh: riceBag, speed: 1.8, range: 0.12, offset: 0 });

  // (B) 3D Soap Bar (Mint & Violet Glowing Box)
  const soapGeo = new THREE.BoxGeometry(0.32, 0.18, 0.22);
  const soapMat = new THREE.MeshStandardMaterial({
    color: 0x34d399,
    roughness: 0.2,
    metalness: 0.8,
    emissive: 0x10b981,
    emissiveIntensity: 0.45
  });
  const soap = new THREE.Mesh(soapGeo, soapMat);
  soap.position.set(1.4, 0.45, 0.7);
  soap.rotation.set(-0.2, -0.4, 0.15);
  shopGroup.add(soap);
  floatingItems.push({ mesh: soap, speed: 2.2, range: 0.14, offset: 1.2 });

  // (C) 3D Milk Packet / Dairy Carton
  const milkGeo = new THREE.ConeGeometry(0.2, 0.45, 4);
  const milkMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    roughness: 0.3,
    metalness: 0.4,
    emissive: 0x0284c7,
    emissiveIntensity: 0.35
  });
  const milk = new THREE.Mesh(milkGeo, milkMat);
  milk.position.set(-0.85, 0.95, 0.5);
  milk.rotation.set(0.2, 0.8, -0.2);
  shopGroup.add(milk);
  floatingItems.push({ mesh: milk, speed: 1.6, range: 0.1, offset: 2.1 });

  // (D) 3D Biscuit Pack
  const biscuitGeo = new THREE.BoxGeometry(0.42, 0.15, 0.16);
  const biscuitMat = new THREE.MeshStandardMaterial({
    color: 0xf59e0b,
    roughness: 0.4,
    emissive: 0xd97706,
    emissiveIntensity: 0.3
  });
  const biscuit = new THREE.Mesh(biscuitGeo, biscuitMat);
  biscuit.position.set(0.9, 1.05, 0.6);
  biscuit.rotation.set(0.3, -0.5, 0.2);
  shopGroup.add(biscuit);
  floatingItems.push({ mesh: biscuit, speed: 2.0, range: 0.11, offset: 3.0 });

  // 5. Central Futuristic AI Orb (Core Intelligence of Dukaan Dost)
  const orbGroup = new THREE.Group();
  orbGroup.position.set(0, 0.3, 0.2);

  const coreGeo = new THREE.SphereGeometry(0.38, 32, 32);
  const coreMat = new THREE.MeshStandardMaterial({
    color: 0xc084fc,
    emissive: 0x9333ea,
    emissiveIntensity: 0.8,
    roughness: 0.15,
    metalness: 0.9
  });
  const aiOrb = new THREE.Mesh(coreGeo, coreMat);
  orbGroup.add(aiOrb);

  // Orbiting Particle Ring
  const ringGeo = new THREE.TorusGeometry(0.65, 0.02, 16, 64);
  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x10b981,
    transparent: true,
    opacity: 0.75
  });
  const ring1 = new THREE.Mesh(ringGeo, ringMat);
  ring1.rotation.x = Math.PI / 2.8;
  orbGroup.add(ring1);

  const ring2 = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({
    color: 0x8b5cf6,
    transparent: true,
    opacity: 0.75
  }));
  ring2.rotation.x = -Math.PI / 2.8;
  ring2.rotation.y = Math.PI / 4;
  orbGroup.add(ring2);

  shopGroup.add(orbGroup);
  floatingItems.push({ mesh: orbGroup, speed: 1.4, range: 0.08, offset: 0.5 });

  // 6. Holographic Data Cards in 3D Space
  function createHoloCard(title, value, colorHex) {
    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 160;
    const ctx = canvas.getContext('2d');

    // Glass Card Background
    ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
    ctx.roundRect(0, 0, 320, 160, 20);
    ctx.fill();

    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 4;
    ctx.roundRect(2, 2, 316, 156, 18);
    ctx.stroke();

    // Text
    ctx.fillStyle = '#94a3b8';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.fillText(title, 24, 48);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 36px Inter, sans-serif';
    ctx.fillText(value, 24, 112);

    const texture = new THREE.CanvasTexture(canvas);
    const planeGeo = new THREE.PlaneGeometry(0.95, 0.48);
    const planeMat = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      opacity: 0.92,
      side: THREE.DoubleSide
    });
    return new THREE.Mesh(planeGeo, planeMat);
  }

  const card1 = createHoloCard("TODAY'S REVENUE", "₹12,450", "#10b981");
  card1.position.set(-1.6, 1.4, 0.3);
  card1.rotation.y = 0.28;
  shopGroup.add(card1);
  floatingItems.push({ mesh: card1, speed: 1.5, range: 0.07, offset: 1.0 });

  const card2 = createHoloCard("RICE STOCK", "25 kg Left", "#8b5cf6");
  card2.position.set(1.65, 1.35, 0.2);
  card2.rotation.y = -0.32;
  shopGroup.add(card2);
  floatingItems.push({ mesh: card2, speed: 1.7, range: 0.08, offset: 2.2 });

  // 7. Background Floating Sparkle Particles
  const partCount = 180;
  const partGeo = new THREE.BufferGeometry();
  const partPositions = new Float32Array(partCount * 3);
  for (let i = 0; i < partCount * 3; i += 3) {
    partPositions[i] = (Math.random() - 0.5) * 8;
    partPositions[i + 1] = (Math.random() - 0.5) * 6;
    partPositions[i + 2] = (Math.random() - 0.5) * 5;
  }
  partGeo.setAttribute('position', new THREE.BufferAttribute(partPositions, 3));
  const partMat = new THREE.PointsMaterial({
    color: 0xc084fc,
    size: 0.035,
    transparent: true,
    opacity: 0.65
  });
  const particles = new THREE.Points(partGeo, partMat);
  scene.add(particles);

  // 8. Mouse Parallax Reaction
  let targetRotationX = 0;
  let targetRotationY = 0;
  window.addEventListener('mousemove', (e) => {
    const nx = (e.clientX / window.innerWidth) * 2 - 1;
    const ny = -(e.clientY / window.innerHeight) * 2 + 1;
    targetRotationY = nx * 0.25;
    targetRotationX = ny * 0.15;
  }, { passive: true });

  // 9. Render Loop
  const clock = new THREE.Clock();
  function animate() {
    requestAnimationFrame(animate);
    const elapsedTime = clock.getElapsedTime();

    // Rotate and pulse AI Orb
    aiOrb.rotation.y = elapsedTime * 0.6;
    ring1.rotation.z = elapsedTime * 0.8;
    ring2.rotation.z = -elapsedTime * 0.65;

    // Floating sinusoidal animation for products & cards
    floatingItems.forEach(item => {
      item.mesh.position.y += Math.sin(elapsedTime * item.speed + item.offset) * 0.0012;
    });

    // Sparkles slow drift
    particles.rotation.y = elapsedTime * 0.04;

    // Smooth cursor-following tilt on shop group
    shopGroup.rotation.y += (targetRotationY - shopGroup.rotation.y) * 0.05;
    shopGroup.rotation.x += (targetRotationX - shopGroup.rotation.x) * 0.05;

    renderer.render(scene, camera);
  }
  animate();

  // Resize handler
  window.addEventListener('resize', () => {
    const newW = container.clientWidth || 600;
    const newH = container.clientHeight || 550;
    camera.aspect = newW / newH;
    camera.updateProjectionMatrix();
    renderer.setSize(newW, newH);
  });
};
