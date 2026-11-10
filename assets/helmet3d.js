// LH/26 helmet, rendered in real 3D over the hero portrait.
// Model: "F1 helmet" by huzaifainnovator (Sketchfab), CC BY 4.0. The original sponsor
// livery texture is dropped; the shell is painted procedurally in the LH/26 livery.
// Fires `helmet:ready` on the canvas after the first frame; on any failure the portrait just shows.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const canvas = document.getElementById('helmet-canvas');
const rig = document.getElementById('helmet-rig');
const hero = document.getElementById('hero');

function decal(text, w, h, font, color) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); g.font = font; g.fillStyle = color;
  g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, w / 2, h / 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// Jalur Gemilang crescent and 14-point star, yellow on transparent (flag proportions).
function crescentStar(w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); const cy = h / 2, R = h * 0.42;
  g.fillStyle = '#ffcc00';
  g.beginPath(); g.arc(w * 0.36, cy, R, 0, Math.PI * 2); g.fill();
  g.globalCompositeOperation = 'destination-out';
  g.beginPath(); g.arc(w * 0.36 + R * 0.25, cy, R * 0.86, 0, Math.PI * 2); g.fill();
  g.globalCompositeOperation = 'source-over';
  const sx = w * 0.66, sr = h * 0.36, ir = sr * 0.55; g.beginPath();
  for (let i = 0; i < 28; i++) { const a = -Math.PI / 2 + i * Math.PI / 14, r = i % 2 ? ir : sr; g.lineTo(sx + r * Math.cos(a), cy + r * Math.sin(a)); }
  g.closePath(); g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

function outlinedNumber(text) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 256;
  const g = c.getContext('2d'); g.font = 'italic 900 200px Arial'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round'; g.lineWidth = 26; g.strokeStyle = '#010066'; g.strokeText(text, 256, 128);
  g.fillStyle = '#ffffff'; g.fillText(text, 256, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// Shell paint, Malaysia themed (Jalur Gemilang): navy crown as the canton with the yellow
// crescent and star on the forehead, red/white stripes around the lower shell, gold pinstripe
// on the boundary, 26 on the chin, LH // 26 on the back, black rubber lip.
// Model units: width 1.374, height 1.562, front = +Z.
function shellMaterial() {
  const U = {
    uCrown: { value: 0.42 }, uStripe: { value: 0.16 }, uLip: { value: -0.7 },
    uNavy: { value: new THREE.Color('#010066') }, uYellow: { value: new THREE.Color('#ffcc00') },
    uRed: { value: new THREE.Color('#cc0001') }, uWhite: { value: new THREE.Color('#f4f5f6') }, uGold: { value: new THREE.Color('#d4a23a') },
    uChin: { value: outlinedNumber('26') }, uChinR: { value: new THREE.Vector4(0, -0.45, 0.42, 0.21) },
    uBrow: { value: crescentStar(512, 256) }, uBrowR: { value: new THREE.Vector4(0, 0.585, 0.4, 0.2) },
    uBack: { value: decal('LH // 26', 1024, 180, '700 120px Arial', '#ffcc00') }, uBackR: { value: new THREE.Vector4(0, 0.5, 0.5, 0.088) },
  };
  const mat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.22, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.05 });
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vOP; varying vec3 vON;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvOP = position; vON = normal;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vOP; varying vec3 vON;
uniform sampler2D uChin, uBrow, uBack; uniform float uCrown, uStripe, uLip;
uniform vec3 uNavy, uYellow, uWhite, uRed, uGold; uniform vec4 uChinR, uBrowR, uBackR;
float gLip;`)
      .replace('#include <color_fragment>', `#include <color_fragment>
float s = floor((uCrown - vOP.y) / uStripe);
vec3 liv = vOP.y > uCrown ? uNavy : (mod(s, 2.) < 0.5 ? uRed : uWhite);
liv = mix(uGold, liv, smoothstep(0.004, 0.01, abs(vOP.y - uCrown)));
if (vON.z > 0.35) { vec2 cu = (vOP.xy - uChinR.xy) / uChinR.zw + 0.5;
  if (all(greaterThan(cu, vec2(0.))) && all(lessThan(cu, vec2(1.)))) { vec4 d = texture2D(uChin, cu); liv = mix(liv, d.rgb, d.a); } }
if (vON.z > 0.2) { vec2 bu = (vOP.xy - uBrowR.xy) / uBrowR.zw + 0.5;
  if (all(greaterThan(bu, vec2(0.))) && all(lessThan(bu, vec2(1.)))) { vec4 d = texture2D(uBrow, bu); liv = mix(liv, d.rgb, d.a); } }
if (vON.z < -0.3) { vec2 ku = vec2(-(vOP.x - uBackR.x), vOP.y - uBackR.y) / uBackR.zw + 0.5;
  if (all(greaterThan(ku, vec2(0.))) && all(lessThan(ku, vec2(1.)))) { vec4 d = texture2D(uBack, ku); liv = mix(liv, d.rgb, d.a); } }
gLip = 1. - smoothstep(uLip, uLip + 0.02, vOP.y);
liv = mix(liv, vec3(0.04), gLip);
diffuseColor.rgb = liv;`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.7, gLip);');
  };
  return mat;
}

// Visor: smoked glass with gold iridium toward the edges (vertex colours by |x|).
function visorMaterial(geo) {
  const p = geo.attributes.position, col = new Float32Array(p.count * 3);
  const gold = new THREE.Color('#d9a441'), smoke = new THREE.Color('#24130b'), c = new THREE.Color();
  for (let i = 0; i < p.count; i++) {
    const t = Math.min(1, Math.max(0, (Math.abs(p.getX(i)) - 0.16) / 0.42));
    c.copy(smoke).lerp(gold, Math.pow(t, 1.5)); col.set([c.r, c.g, c.b], i * 3);
  }
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return new THREE.MeshPhysicalMaterial({
    vertexColors: true, metalness: 0.85, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.04,
    envMapIntensity: 1.0, side: THREE.DoubleSide,
  });
}

// Expand the quantized positions into plain floats in model units.
function bake(mesh) {
  const geo = mesh.geometry.clone(), p = geo.attributes.position, arr = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { arr[i * 3] = p.getX(i); arr[i * 3 + 1] = p.getY(i); arr[i * 3 + 2] = p.getZ(i); }
  geo.setAttribute('position', new THREE.Float32BufferAttribute(arr, 3));
  geo.applyMatrix4(mesh.matrixWorld);
  return geo;
}

async function init() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const key = new THREE.DirectionalLight(0xffffff, 1.2); key.position.set(-2, 3, 4); scene.add(key);
  const camera = new THREE.PerspectiveCamera(20, 1, 0.1, 50);

  const gltf = await new GLTFLoader().loadAsync('assets/helmet-f1.glb');
  gltf.scene.updateMatrixWorld(true);
  const meshes = []; gltf.scene.traverse((o) => { if (o.isMesh) meshes.push(o); });
  const geos = meshes.map(bake).sort((a, b) => b.attributes.position.count - a.attributes.position.count);
  const [shellGeo, visorGeo] = geos;  // shell is the larger part

  const group = new THREE.Group();
  group.add(new THREE.Mesh(shellGeo, shellMaterial()));
  group.add(new THREE.Mesh(visorGeo, visorMaterial(visorGeo)));
  scene.add(group);

  const size = () => {
    const w = canvas.clientWidth, h = canvas.clientHeight; if (!w || !h) return;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const halfW = 0.74, dist = halfW / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / camera.aspect + 0.95;
    camera.position.set(0, 0.02, dist); camera.lookAt(0, 0.02, 0); camera.updateProjectionMatrix();
  };

  // Gentle turn toward the cursor shows it is a real object.
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let tgt = { y: 0, x: 0 }, cur = { y: 0, x: 0 }, raf = 0;
  const frame = () => {
    const k = reduce ? 1 : 0.12;
    cur.y += (tgt.y - cur.y) * k; cur.x += (tgt.x - cur.x) * k;
    group.rotation.set(cur.x, cur.y, 0);
    renderer.render(scene, camera);
    raf = (Math.abs(tgt.y - cur.y) > 1e-4 || Math.abs(tgt.x - cur.x) > 1e-4) ? requestAnimationFrame(frame) : 0;
  };
  const kick = () => { if (!raf) raf = requestAnimationFrame(frame); };
  hero.addEventListener('pointermove', (e) => {
    if (e.pointerType === 'touch') return;
    const b = rig.getBoundingClientRect();
    const nx = Math.max(-1, Math.min(1, (e.clientX - (b.left + b.width / 2)) / (b.width * 1.5)));
    const ny = Math.max(-1, Math.min(1, (e.clientY - (b.top + b.height / 2)) / (b.height * 1.5)));
    tgt = { y: nx * 0.22, x: ny * 0.1 }; kick();
  });
  hero.addEventListener('pointerleave', () => { tgt = { y: 0, x: 0 }; kick(); });
  new ResizeObserver(() => { size(); kick(); }).observe(canvas);

  size(); renderer.render(scene, camera);
  canvas.dispatchEvent(new CustomEvent('helmet:ready', { bubbles: true }));
}

init().catch((err) => { console.warn('3D helmet unavailable:', err); });
