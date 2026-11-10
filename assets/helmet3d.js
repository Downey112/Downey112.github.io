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

// Shell paint: teal / white / red bands front-to-back with gold edge lines,
// 26 on the chin, LH // 26 on the brow, black rubber lip. Model units: width 1.374, front = +Z.
function shellMaterial() {
  const U = {
    uW: { value: 0.15 }, uLip: { value: -0.7 },
    uTeal: { value: new THREE.Color('#00b8a8') }, uWhite: { value: new THREE.Color('#f2f4f5') },
    uRed: { value: new THREE.Color('#e3260f') }, uGold: { value: new THREE.Color('#c99a3c') },
    uChin: { value: decal('26', 512, 256, 'italic 900 200px Arial', '#d21f0c') }, uChinR: { value: new THREE.Vector4(0, -0.45, 0.4, 0.2) },
    uBrow: { value: decal('LH // 26', 1024, 180, '700 120px Arial', '#0b0d13') }, uBrowR: { value: new THREE.Vector4(0, 0.45, 0.36, 0.064) },
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
uniform sampler2D uChin, uBrow; uniform float uW, uLip;
uniform vec3 uTeal, uWhite, uRed, uGold; uniform vec4 uChinR, uBrowR;
float gLip;`)
      .replace('#include <color_fragment>', `#include <color_fragment>
vec3 liv = vOP.x < -uW ? uTeal : (vOP.x > uW ? uRed : uWhite);
liv = mix(uGold, liv, smoothstep(0.003, 0.008, abs(abs(vOP.x) - uW)));
if (vON.z > 0.35) { vec2 cu = (vOP.xy - uChinR.xy) / uChinR.zw + 0.5;
  if (all(greaterThan(cu, vec2(0.))) && all(lessThan(cu, vec2(1.)))) { vec4 d = texture2D(uChin, cu); liv = mix(liv, d.rgb, d.a); } }
if (vON.z > 0.3) { vec2 bu = (vOP.xy - uBrowR.xy) / uBrowR.zw + 0.5;
  if (all(greaterThan(bu, vec2(0.))) && all(lessThan(bu, vec2(1.)))) { vec4 d = texture2D(uBrow, bu); liv = mix(liv, d.rgb, d.a); } }
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
