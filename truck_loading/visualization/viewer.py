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
@import url('https://fonts.googleapis.com/css2?family=M+PLUS+Code+Latin:wght@400;500;600;700&family=VT323&display=swap');
html, body {{
  width: 100%;
  height: 100%;
  margin: 0;
  overflow: hidden;
  background: #0b0f12;
  color: #edf7f6;
  font-family: "M PLUS Code Latin";
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
  left: 14px;
  right: 14px;
  top: 12px;
  z-index: 5;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: start;
  pointer-events: none;
}}
.panel {{
  border: 1px solid rgba(178,246,242,0.16);
  border-radius: 12px;
  background: rgba(5, 10, 14, 0.66);
  backdrop-filter: blur(12px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 14px 34px rgba(0,0,0,0.22);
  padding: 10px;
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
  font-family: "VT323";
  font-size: 18px;
  font-weight: 800;
  line-height: 1.05;
}}
.meta {{
  margin-top: 6px;
  color: #bac8d1;
  font-size: 11px;
}}
.controls {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}}
button, select {{
  border: 1px solid rgba(178,246,242,.18);
  border-radius: 10px;
  background: rgba(5, 10, 14, .88);
  color: #edf7f6;
  font: 700 12px "M PLUS Code Latin";
  padding: 7px 9px;
  color-scheme: dark;
}}
select {{
  max-width: 250px;
  min-width: 250px;
  appearance: none;
  padding-right: 34px;
  background:
    linear-gradient(45deg, transparent 50%, #e7f1f4 50%) calc(100% - 16px) 50% / 7px 7px no-repeat,
    linear-gradient(135deg, #e7f1f4 50%, transparent 50%) calc(100% - 11px) 50% / 7px 7px no-repeat,
    rgba(12, 18, 23, .94);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
select option {{
  background: #0b1117;
  color: #edf7f6;
  font: 700 13px "M PLUS Code Latin";
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
  background: rgba(34, 211, 197, .18);
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
      <button id="resetView">Reset view</button>
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

const sceneGroup = new THREE.Group();
scene.add(sceneGroup);
const root = new THREE.Group();
sceneGroup.add(root);
const boxesGroup = new THREE.Group();
sceneGroup.add(boxesGroup);
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let boxMeshes = [];
let activeRoute = 0;
let playing = true;
let startTime = performance.now();
let speed = 1;
let dragging = false;
let lastPointer = {{ x: 0, y: 0 }};
let viewYaw = -0.18;
const fixedPitch = -0.08;

const dims = payload.container;
const axisLabels = payload.axis_labels || {{}};
const scale = 1 / 1000;
const L = dims.L * scale;
const W = dims.W * scale;
const H = dims.H * scale;
const center = new THREE.Vector3(L / 2, H / 2, W / 2);

function buildContainer() {{
  root.clear();
  root.position.set(-center.x, -center.y, -center.z);
  boxesGroup.position.set(-center.x, -center.y, -center.z);
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

  addDimensionRail(
    axisLabels.length || `Length ${{L.toFixed(1)}} m`,
    new THREE.Vector3(0, -0.035, -0.12),
    new THREE.Vector3(L, -0.035, -0.12),
    new THREE.Vector3(0, 0, 0.12)
  );
  addDimensionRail(
    axisLabels.width || `Width ${{W.toFixed(1)}} m`,
    new THREE.Vector3(L + 0.12, -0.035, 0),
    new THREE.Vector3(L + 0.12, -0.035, W),
    new THREE.Vector3(-0.12, 0, 0)
  );
  addDimensionRail(
    axisLabels.height || `Height ${{H.toFixed(1)}} m`,
    new THREE.Vector3(-0.12, 0, W + 0.1),
    new THREE.Vector3(-0.12, H, W + 0.1),
    new THREE.Vector3(0.12, 0, 0)
  );
  root.add(makeLabel('Back', -0.18, H + 0.16, W / 2));
  root.add(makeLabel('Front', L + 0.18, H + 0.16, W / 2));
}}

function setCamera() {{
  const longest = Math.max(L, W, H);
  camera.position.set(longest * 0.82, Math.max(H * 1.28, longest * 0.62, 1.8), longest * 1.42);
  camera.lookAt(0, 0, 0);
}}

function resetView() {{
  viewYaw = -0.18;
  applyViewRotation();
  setCamera();
}}

function applyViewRotation() {{
  sceneGroup.rotation.set(fixedPitch, viewYaw, 0);
}}

function addLine(start, end, color = 0x7ff6ef, opacity = 0.9) {{
  const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
  const line = new THREE.Line(
    geometry,
    new THREE.LineBasicMaterial({{ color, transparent: true, opacity }})
  );
  root.add(line);
  return line;
}}

function addDimensionRail(text, start, end, tickOffset) {{
  addLine(start, end, 0x7ff6ef, 0.88);
  addLine(start, start.clone().add(tickOffset), 0x7ff6ef, 0.82);
  addLine(end, end.clone().add(tickOffset), 0x7ff6ef, 0.82);
  const mid = start.clone().add(end).multiplyScalar(0.5).add(tickOffset.clone().multiplyScalar(0.58));
  root.add(makeLabel(text, mid.x, mid.y, mid.z));
}}

function makeLabel(text, x, y, z) {{
  const canvas = document.createElement('canvas');
  canvas.width = 384;
  canvas.height = 96;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = 'rgba(5, 10, 14, 0.84)';
  roundRect(ctx, 10, 25, 364, 48, 16);
  ctx.fill();
  ctx.strokeStyle = 'rgba(34, 211, 197, 0.72)';
  ctx.lineWidth = 2;
  roundRect(ctx, 10, 25, 364, 48, 16);
  ctx.stroke();
  ctx.fillStyle = '#e7fbf8';
  ctx.font = '700 18px M PLUS Code Latin';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 192, 49);
  const texture = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({{ map: texture, transparent: true }}));
  sprite.position.set(x, y, z);
  sprite.scale.set(0.86, 0.22, 1);
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
document.getElementById('resetView').addEventListener('click', resetView);
document.querySelectorAll('.speed-button').forEach(button => {{
  button.addEventListener('click', () => {{
    speed = Number(button.dataset.speed);
    document.querySelectorAll('.speed-button').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
  }});
}});
renderer.domElement.addEventListener('click', inspect);
renderer.domElement.addEventListener('pointerdown', event => {{
  dragging = true;
  lastPointer = {{ x: event.clientX, y: event.clientY }};
  renderer.domElement.setPointerCapture(event.pointerId);
}});
renderer.domElement.addEventListener('pointermove', event => {{
  if (!dragging) return;
  const dx = event.clientX - lastPointer.x;
  lastPointer = {{ x: event.clientX, y: event.clientY }};
  viewYaw += dx * 0.006;
  applyViewRotation();
}});
renderer.domElement.addEventListener('pointerup', event => {{
  dragging = false;
  renderer.domElement.releasePointerCapture(event.pointerId);
}});
renderer.domElement.addEventListener('pointercancel', () => {{
  dragging = false;
}});
window.addEventListener('resize', () => {{
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
}});

buildContainer();
resetView();
buildRoute(0);
requestAnimationFrame(animate);
</script>
</body>
</html>"""
