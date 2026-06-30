"""HTML/Three.js helpers for the animated truck loading viewer."""

from __future__ import annotations

import json
from html import escape
from typing import Any


def packing_viewer_placeholder() -> str:
    return """
    <div class="packing-viewer-empty">
        <div class="viewer-kicker">3D loading viewer</div>
        <div class="viewer-title">Run the proposed GA to generate real box placements.</div>
        <p>
            The next scene will draw a transparent truck container from the selected dimensions
            and animate route boxes into their packed positions.
        </p>
    </div>
    """


def packing_viewer_html(payload: dict[str, Any]) -> str:
    srcdoc = _viewer_document(payload)
    return f"""
    <iframe
        class="packing-viewer-frame"
        title="Animated truck loading viewer"
        srcdoc="{escape(srcdoc, quote=True)}"
        loading="lazy">
    </iframe>
    """


def _viewer_document(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(payload)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600;700&family=Space+Grotesk:wght@500;600;700;800&display=swap');
html, body {{
  width: 100%;
  height: 100%;
  margin: 0;
  overflow: hidden;
  background: #0b0f12;
  color: #edf7f6;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
}}
#app {{
  position: relative;
  width: 100%;
  height: 100vh;
  min-height: 520px;
  background:
    radial-gradient(circle at 22% 16%, rgba(34, 211, 197, 0.16), transparent 24%),
    radial-gradient(circle at 82% 22%, rgba(247, 201, 72, 0.11), transparent 22%),
    linear-gradient(180deg, #0e1418, #080b0e);
}}
#canvas {{
  position: absolute;
  inset: 0;
}}
.hud {{
  position: absolute;
  left: 16px;
  right: 16px;
  top: 14px;
  z-index: 5;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: start;
  pointer-events: none;
}}
.panel {{
  border: 1px solid rgba(255,255,255,0.13);
  border-radius: 12px;
  background: rgba(11, 15, 18, 0.72);
  backdrop-filter: blur(12px);
  box-shadow: 0 18px 42px rgba(0,0,0,0.28);
  padding: 12px;
  pointer-events: auto;
}}
.kicker {{
  color: #22d3c5;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .12em;
  text-transform: uppercase;
}}
.title {{
  margin-top: 4px;
  font-size: 22px;
  font-weight: 800;
  line-height: 1.05;
}}
.meta {{
  margin-top: 8px;
  color: #bac8d1;
  font-size: 13px;
}}
.controls {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}}
button, select {{
  border: 1px solid rgba(255,255,255,.16);
  border-radius: 10px;
  background: rgba(255,255,255,.08);
  color: #edf7f6;
  font: 700 12px "IBM Plex Mono", monospace;
  padding: 8px 10px;
}}
select {{
  max-width: 250px;
}}
button:hover, select:hover {{
  border-color: rgba(34, 211, 197, .66);
}}
.speed-group {{
  display: flex;
  gap: 6px;
}}
.speed-button.active {{
  border-color: rgba(34, 211, 197, .82);
  background: rgba(34, 211, 197, .2);
  color: #ffffff;
}}
.tooltip {{
  position: absolute;
  z-index: 6;
  left: 18px;
  bottom: 18px;
  max-width: min(420px, calc(100% - 36px));
  border: 1px solid rgba(34, 211, 197, .26);
  border-radius: 12px;
  background: rgba(11, 15, 18, .76);
  backdrop-filter: blur(12px);
  padding: 12px;
  color: #e7f1f4;
  font-size: 13px;
  line-height: 1.4;
}}
.fallback {{
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  text-align: center;
  color: #dce8eb;
}}
@media (max-width: 720px) {{
  #app {{ min-height: 560px; }}
  .hud {{ grid-template-columns: 1fr; }}
  .controls {{ justify-content: flex-start; }}
}}
</style>
</head>
<body>
<div id="app">
  <div id="canvas"></div>
  <div class="hud">
    <div class="panel">
      <div class="kicker">Animated packing route</div>
      <div class="title" id="routeTitle">Route viewer</div>
      <div class="meta" id="routeMeta">Loading Three.js scene...</div>
    </div>
    <div class="panel controls">
      <select id="routeSelect" aria-label="Route selector"></select>
      <button id="play">Play</button>
      <button id="pause">Pause</button>
      <button id="replay">Replay</button>
      <div class="speed-group" aria-label="Animation speed">
        <button class="speed-button" data-speed="0.75">0.75x</button>
        <button class="speed-button active" data-speed="1">1x</button>
        <button class="speed-button" data-speed="1.5">1.5x</button>
        <button class="speed-button" data-speed="2.25">2.25x</button>
      </div>
    </div>
  </div>
  <div class="tooltip" id="tooltip">Click a box to inspect its customer and dimensions.</div>
</div>
<script type="module">
const payload = {payload_json};
const container = document.getElementById('canvas');
const routeSelect = document.getElementById('routeSelect');
const routeTitle = document.getElementById('routeTitle');
const routeMeta = document.getElementById('routeMeta');
const tooltip = document.getElementById('tooltip');

let THREE;
try {{
  THREE = await import('https://unpkg.com/three@0.164.1/build/three.module.js');
}} catch (error) {{
  document.getElementById('app').innerHTML = '<div class="fallback"><div><h2>3D viewer could not load</h2><p>Three.js was unavailable. The proposed GA still produced route placements and metrics.</p></div></div>';
  throw error;
}}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0f12);
const camera = new THREE.PerspectiveCamera(42, container.clientWidth / container.clientHeight, 0.01, 1000);
const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

const ambient = new THREE.AmbientLight(0xffffff, 0.72);
scene.add(ambient);
const key = new THREE.DirectionalLight(0xffffff, 1.4);
key.position.set(4, 7, 5);
scene.add(key);

const root = new THREE.Group();
scene.add(root);
const boxesGroup = new THREE.Group();
scene.add(boxesGroup);
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let boxMeshes = [];
let activeRoute = 0;
let playing = true;
let startTime = performance.now();
let speed = 1;

const dims = payload.container;
const axisLabels = payload.axis_labels || {{}};
const scale = 1 / 1000;
const L = dims.L * scale;
const W = dims.W * scale;
const H = dims.H * scale;

function buildContainer() {{
  root.clear();
  const geometry = new THREE.BoxGeometry(L, H, W);
  const edges = new THREE.EdgesGeometry(geometry);
  const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({{ color: 0x22d3c5, transparent: true, opacity: 0.86 }}));
  line.position.set(L / 2, H / 2, W / 2);
  root.add(line);

  const shell = new THREE.Mesh(
    geometry,
    new THREE.MeshPhysicalMaterial({{ color: 0x22d3c5, transparent: true, opacity: 0.055, roughness: 0.55, metalness: 0.05 }})
  );
  shell.position.copy(line.position);
  root.add(shell);

  const floor = new THREE.GridHelper(Math.max(L, W) * 1.35, 18, 0x31525a, 0x1b2a30);
  floor.rotation.x = Math.PI / 2;
  floor.position.set(L / 2, -0.004, W / 2);
  root.add(floor);

  root.add(makeLabel(axisLabels.length || `Length ${{L.toFixed(1)}} m`, L / 2, -0.08, -0.18));
  root.add(makeLabel(axisLabels.width || `Width ${{W.toFixed(1)}} m`, L + 0.18, -0.08, W / 2));
  root.add(makeLabel(axisLabels.height || `Height ${{H.toFixed(1)}} m`, -0.22, H / 2, W + 0.08));
}}

function setCamera() {{
  const longest = Math.max(L, W, H);
  camera.position.set(L * 0.92, Math.max(H * 1.65, longest * 0.9, 2.4), W * 1.85 + longest * 0.55);
  camera.lookAt(L / 2, H * 0.42, W / 2);
}}

function makeLabel(text, x, y, z) {{
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = 'rgba(11, 15, 18, 0.76)';
  roundRect(ctx, 10, 26, 492, 70, 22);
  ctx.fill();
  ctx.strokeStyle = 'rgba(34, 211, 197, 0.72)';
  ctx.lineWidth = 3;
  roundRect(ctx, 10, 26, 492, 70, 22);
  ctx.stroke();
  ctx.fillStyle = '#e7fbf8';
  ctx.font = '700 30px Space Grotesk, Segoe UI, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 256, 62);
  const texture = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: texture, transparent: true }}));
  sprite.position.set(x, y, z);
  sprite.scale.set(1.55, 0.38, 1);
  return sprite;
}}

function roundRect(ctx, x, y, width, height, radius) {{
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}}

function boxPosition(placement) {{
  return new THREE.Vector3(
    (placement.x + placement.l / 2) * scale,
    (placement.z + placement.h / 2) * scale,
    (placement.y + placement.w / 2) * scale
  );
}}

function buildRoute(index) {{
  activeRoute = index;
  boxesGroup.clear();
  boxMeshes = [];
  const route = payload.routes[index];
  routeTitle.textContent = `Route ${{route.route_index}} | ${{route.customer_count}} customers`;
  routeMeta.textContent = `${{route.boxes_packed}}/${{route.boxes_total}} boxes packed | Fill ${{(route.fill_rate * 100).toFixed(1)}}% | Distance ${{route.distance.toFixed(1)}}`;
  tooltip.textContent = route.customer_labels.slice(0, 6).join(' -> ') + (route.customer_labels.length > 6 ? ' ...' : '');

  route.placements.forEach((placement, order) => {{
    const geometry = new THREE.BoxGeometry(placement.l * scale, placement.h * scale, placement.w * scale);
    const material = new THREE.MeshStandardMaterial({{ color: placement.color, roughness: 0.58, metalness: 0.05 }});
    const mesh = new THREE.Mesh(geometry, material);
    const finalPosition = boxPosition(placement);
    mesh.position.set(-L * 0.35 - (order % 6) * 0.08, H + 0.8 + (order % 4) * 0.08, W / 2);
    mesh.userData = {{ placement, finalPosition, order }};
    boxesGroup.add(mesh);

    const edge = new THREE.LineSegments(
      new THREE.EdgesGeometry(geometry),
      new THREE.LineBasicMaterial({{ color: 0xffffff, transparent: true, opacity: 0.36 }})
    );
    edge.userData = mesh.userData;
    mesh.add(edge);
    boxMeshes.push(mesh);
  }});
  startTime = performance.now();
  playing = true;
}}

function easeOutCubic(t) {{
  return 1 - Math.pow(1 - t, 3);
}}

function animate(now) {{
  requestAnimationFrame(animate);
  if (playing) {{
    const elapsed = (now - startTime) / 1000 * speed;
    boxMeshes.forEach(mesh => {{
      const delay = mesh.userData.order * 0.085;
      const t = Math.max(0, Math.min(1, (elapsed - delay) / 0.9));
      mesh.position.lerpVectors(mesh.position, mesh.userData.finalPosition, easeOutCubic(t) * 0.08);
      if (t >= 1) mesh.position.copy(mesh.userData.finalPosition);
    }});
  }}
  root.rotation.y = Math.sin(now * 0.00022) * 0.04;
  boxesGroup.rotation.y = root.rotation.y;
  renderer.render(scene, camera);
}}

function inspect(event) {{
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(boxMeshes, false)[0];
  if (!hit) return;
  const p = hit.object.userData.placement;
  tooltip.innerHTML = `<strong>${{p.customer_label}}</strong><br>Box ${{p.box_id}} | ${{(p.l/1000).toFixed(2)}} x ${{(p.w/1000).toFixed(2)}} x ${{(p.h/1000).toFixed(2)}} m`;
}}

payload.routes.forEach((route, index) => {{
  const option = document.createElement('option');
  option.value = String(index);
  option.textContent = `Route ${{route.route_index}} - ${{route.boxes_packed}}/${{route.boxes_total}} boxes`;
  routeSelect.appendChild(option);
}});
routeSelect.addEventListener('change', event => buildRoute(Number(event.target.value)));
document.getElementById('play').addEventListener('click', () => {{ playing = true; }});
document.getElementById('pause').addEventListener('click', () => {{ playing = false; }});
document.getElementById('replay').addEventListener('click', () => buildRoute(activeRoute));
document.querySelectorAll('.speed-button').forEach(button => {{
  button.addEventListener('click', () => {{
    speed = Number(button.dataset.speed);
    document.querySelectorAll('.speed-button').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
  }});
}});
renderer.domElement.addEventListener('click', inspect);
window.addEventListener('resize', () => {{
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
}});

buildContainer();
setCamera();
buildRoute(0);
requestAnimationFrame(animate);
</script>
</body>
</html>"""
