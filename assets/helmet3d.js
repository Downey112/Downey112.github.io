// LH/26 helmet, rendered in real 3D over the hero portrait.
// Model: "racing helmet" by Rumdidum (Sketchfab), CC BY 4.0, repainted and with a rebuilt visor.
// Fires `helmet:ready` on the canvas after the first frame; on any failure the portrait just shows.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const canvas = document.getElementById('helmet-canvas');
const rig = document.getElementById('helmet-rig');
const hero = document.getElementById('hero');
const BASE = 'assets/';

function decal(text, w, h, font, color) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); g.font = font; g.fillStyle = color;
  g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, w / 2, h / 2);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

function loadImage(src) {
  return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
}

// Rebuild the visor as one smooth lens: fit the shell's front curve, lift it clear of the
// original (hole-ridden) visor, and trace smooth top/bottom edges across its width.
function buildVisor(geo, maskData) {
  const P = geo.attributes.position, N = geo.attributes.normal, UV = geo.attributes.uv;
  const md = maskData;
  const maskAt = (u, v) => md[((Math.floor((1 - v) * 255) * 256) + Math.floor(u * 255)) * 4];
  const X0 = -0.62, X1 = 0.62, Y0 = -0.25, Y1 = 0.6, GX = 72, GY = 50;
  const zmax = new Float32Array(GX * GY).fill(-9), hit = new Uint8Array(GX * GY);
  for (let i = 0; i < P.count; i++) {
    const x = P.getX(i), y = P.getY(i), z = P.getZ(i);
    if (N.getZ(i) < 0.35 || z < 0.1 || x < X0 || x > X1 || y < Y0 || y > Y1) continue;
    const gx = Math.min(GX - 1, Math.floor((x - X0) / (X1 - X0) * GX));
    const gy = Math.min(GY - 1, Math.floor((y - Y0) / (Y1 - Y0) * GY));
    const k = gy * GX + gx;
    if (z > zmax[k]) zmax[k] = z;
    if (maskAt(UV.getX(i), UV.getY(i)) < 110) hit[k] = 1;
  }
  const morph = (a, dil) => {
    const b = new Uint8Array(a.length);
    for (let y = 0; y < GY; y++) for (let x = 0; x < GX; x++) {
      let v = dil ? 0 : 1;
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
        const xx = x + dx, yy = y + dy;
        const s = (xx < 0 || yy < 0 || xx >= GX || yy >= GY) ? 0 : a[yy * GX + xx];
        v = dil ? (v | s) : (v & s);
      }
      b[y * GX + x] = v;
    }
    return b;
  };
  const mask = morph(morph(hit, true), false);
  // keep the largest connected blob (the visor)
  const lab = new Int32Array(GX * GY).fill(-1); let best = -1, bestN = 0, id = 0;
  for (let s0 = 0; s0 < GX * GY; s0++) {
    if (!mask[s0] || lab[s0] >= 0) continue;
    const st = [s0]; lab[s0] = id; let n = 0;
    while (st.length) {
      const k = st.pop(); n++; const x = k % GX, y = (k / GX) | 0;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const xx = x + dx, yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= GX || yy >= GY) continue;
        const kk = yy * GX + xx;
        if (mask[kk] && lab[kk] < 0) { lab[kk] = id; st.push(kk); }
      }
    }
    if (n > bestN) { bestN = n; best = id; }
    id++;
  }
  for (let k = 0; k < mask.length; k++) mask[k] = lab[k] === best ? 1 : 0;

  // least-squares fit z = f(x, y) to the painted shell around the visor
  const feats = (x, y) => [1, x, y, x * x, x * y, y * y, x * x * y, x * x * y * y, x ** 4, x ** 4 * y, y ** 3];
  const F = feats(0, 0).length;
  const A = Array.from({ length: F }, () => new Float64Array(F)), B = new Float64Array(F);
  for (let i = 0; i < P.count; i++) {
    const x = P.getX(i), y = P.getY(i), z = P.getZ(i);
    if (N.getZ(i) < 0.3 || z < 0.1 || x < -0.7 || x > 0.7 || y < -0.4 || y > 0.75) continue;
    if (maskAt(UV.getX(i), UV.getY(i)) < 200) continue;
    const f = feats(x, y);
    for (let r = 0; r < F; r++) { B[r] += f[r] * z; for (let c = 0; c < F; c++) A[r][c] += f[r] * f[c]; }
  }
  for (let r = 0; r < F; r++) A[r][r] += 1e-6;
  const M = A.map((row, r) => [...row, B[r]]);
  for (let c = 0; c < F; c++) {
    let p = c; for (let r = c + 1; r < F; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = 0; r < F; r++) { if (r === c) continue; const f = M[r][c] / M[c][c]; for (let k = c; k <= F; k++) M[r][k] -= f * M[c][k]; }
  }
  const coef = M.map((row, r) => row[F] / row[r]);
  const zFit = (x, y) => feats(x, y).reduce((s, f, i) => s + f * coef[i], 0);

  // smooth lift so the lens clears the original visor everywhere
  let off = new Float32Array(GX * GY);
  for (let y = 0; y < GY; y++) for (let x = 0; x < GX; x++) {
    const k = y * GX + x; if (!mask[k]) continue;
    const px = X0 + (X1 - X0) * (x + 0.5) / GX, py = Y0 + (Y1 - Y0) * (y + 0.5) / GY;
    off[k] = Math.max(0, zmax[k] - zFit(px, py));
  }
  const pass = (a, fn, r) => {
    const o = new Float32Array(a.length);
    for (let y = 0; y < GY; y++) for (let x = 0; x < GX; x++) {
      let acc = 0, c = 0;
      for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
        const xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= GX || yy >= GY) continue;
        const v = a[yy * GX + xx]; if (fn === 'max') acc = Math.max(acc, v); else { acc += v; c++; }
      }
      o[y * GX + x] = fn === 'max' ? acc : acc / c;
    }
    return o;
  };
  off = pass(off, 'max', 4); for (let i = 0; i < 10; i++) off = pass(off, 'avg', 2);
  const offAt = (px, py) => {
    const gx = Math.min(GX - 1, Math.max(0, Math.round((px - X0) / (X1 - X0) * GX - 0.5)));
    const gy = Math.min(GY - 1, Math.max(0, Math.round((py - Y0) / (Y1 - Y0) * GY - 0.5)));
    return off[gy * GX + gx];
  };

  // smooth top and bottom edges, traced column by column
  const xs = [], yb = [], yt = [];
  for (let x = 0; x < GX; x++) {
    let lo = -1, hi = -1;
    for (let y = 0; y < GY; y++) if (mask[y * GX + x]) { if (lo < 0) lo = y; hi = y; }
    if (lo >= 0) { xs.push(X0 + (X1 - X0) * (x + 0.5) / GX); yb.push(Y0 + (Y1 - Y0) * lo / GY); yt.push(Y0 + (Y1 - Y0) * (hi + 1) / GY); }
  }
  const sm = (arr, r, n) => { let a = arr.slice(); for (let i = 0; i < n; i++) a = a.map((_, j) => { let s = 0, c = 0; for (let d = -r; d <= r; d++) { const k = j + d; if (k < 0 || k >= a.length) continue; s += a[k]; c++; } return s / c; }); return a; };
  const ybS = sm(yb, 3, 6), ytS = sm(yt, 3, 6);
  const xl = xs[0], xr = xs[xs.length - 1];
  const interp = (arr, px) => { const t = (px - xl) / (xr - xl) * (arr.length - 1); const i = Math.min(arr.length - 2, Math.max(0, Math.floor(t))); const f = t - i; return arr[i] * (1 - f) + arr[i + 1] * f; };

  const pos = [], col = [], idx = []; const SX = 120, NR = 24;
  const gold = new THREE.Color('#d9a441'), smoke = new THREE.Color('#2a160c');
  for (let i = 0; i <= SX; i++) {
    const px = xl + (xr - xl) * i / SX, b0 = interp(ybS, px), t0 = interp(ytS, px);
    for (let j = 0; j <= NR; j++) {
      const py = b0 + (t0 - b0) * j / NR;
      pos.push(px, py, zFit(px, py) + offAt(px, py) + 0.01);
      const t = Math.min(1, Math.max(0, (Math.abs(px) - 0.16) / 0.38)); const c = smoke.clone().lerp(gold, Math.pow(t, 1.5));
      col.push(c.r, c.g, c.b);
    }
  }
  for (let i = 0; i < SX; i++) for (let j = 0; j < NR; j++) { const a = i * (NR + 1) + j, b = (i + 1) * (NR + 1) + j; idx.push(a, b, b + 1, a, b + 1, a + 1); }
  const vg = new THREE.BufferGeometry();
  vg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  vg.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  vg.setIndex(idx); vg.computeVertexNormals();
  return new THREE.Mesh(vg, new THREE.MeshPhysicalMaterial({
    vertexColors: true, metalness: 0.85, roughness: 0.14, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 0.9,
  }));
}

function paintMaterial(tl) {
  const map = tl.load(BASE + 'helmet-base.webp'); map.colorSpace = THREE.SRGBColorSpace;
  const U = {
    uPaint: { value: tl.load(BASE + 'helmet-paint.webp') },
    uW: { value: 0.15 },
    uTeal: { value: new THREE.Color('#00b8a8') }, uWhite: { value: new THREE.Color('#f2f4f5') },
    uRed: { value: new THREE.Color('#e3260f') }, uGold: { value: new THREE.Color('#c99a3c') },
    uChin: { value: decal('26', 512, 256, 'italic 900 200px Arial', '#d21f0c') }, uChinR: { value: new THREE.Vector4(0, -0.33, 0.42, 0.21) },
    uBrow: { value: decal('LH // 26', 1024, 180, '700 120px Arial', '#0b0d13') }, uBrowR: { value: new THREE.Vector4(0, 0.52, 0.34, 0.06) },
  };
  const mat = new THREE.MeshPhysicalMaterial({ map, clearcoat: 1, clearcoatRoughness: 0.06, roughness: 0.5, metalness: 0.2 });
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vOP; varying vec3 vON;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvOP = position; vON = normal;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vOP; varying vec3 vON;
uniform sampler2D uPaint, uChin, uBrow; uniform float uW;
uniform vec3 uTeal, uWhite, uRed, uGold; uniform vec4 uChinR, uBrowR;
float gPaint;`)
      .replace('#include <map_fragment>', `#include <map_fragment>
gPaint = texture2D(uPaint, vMapUv).r;
vec3 liv = vOP.x < -uW ? uTeal : (vOP.x > uW ? uRed : uWhite);
liv = mix(uGold, liv, smoothstep(0.003, 0.008, abs(abs(vOP.x) - uW)));
if (vON.z > 0.35) { vec2 cu = (vOP.xy - uChinR.xy) / uChinR.zw + 0.5;
  if (all(greaterThan(cu, vec2(0.))) && all(lessThan(cu, vec2(1.)))) { vec4 d = texture2D(uChin, cu); liv = mix(liv, d.rgb, d.a); } }
if (vON.z > 0.3 && vON.y > -0.2) { vec2 bu = (vOP.xy - uBrowR.xy) / uBrowR.zw + 0.5;
  if (all(greaterThan(bu, vec2(0.))) && all(lessThan(bu, vec2(1.)))) { vec4 d = texture2D(uBrow, bu); liv = mix(liv, d.rgb, d.a); } }
diffuseColor.rgb = mix(diffuseColor.rgb, liv, gPaint);`)
      .replace('#include <roughnessmap_fragment>', '#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.22, gPaint);')
      .replace('#include <metalnessmap_fragment>', '#include <metalnessmap_fragment>\nmetalnessFactor = mix(metalnessFactor, 0.0, gPaint);');
  };
  return mat;
}

async function init() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  const key = new THREE.DirectionalLight(0xffffff, 1.2); key.position.set(-2, 3, 4); scene.add(key);
  const camera = new THREE.PerspectiveCamera(20, 1, 0.1, 50);

  const tl = new THREE.TextureLoader();
  const [gltf, maskImg] = await Promise.all([
    new GLTFLoader().loadAsync(BASE + 'helmet.glb'),
    loadImage(BASE + 'helmet-paint.webp'),
  ]);
  const cv = document.createElement('canvas'); cv.width = 256; cv.height = 256;
  const cx = cv.getContext('2d'); cx.drawImage(maskImg, 0, 0, 256, 256);
  const maskData = cx.getImageData(0, 0, 256, 256).data;

  // Bake the quantized node transform into plain float positions (original model units).
  gltf.scene.updateMatrixWorld(true);
  let mesh = null; gltf.scene.traverse((o) => { if (o.isMesh && !mesh) mesh = o; });
  const geo = mesh.geometry, p = geo.attributes.position, arr = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { arr[i * 3] = p.getX(i); arr[i * 3 + 1] = p.getY(i); arr[i * 3 + 2] = p.getZ(i); }
  geo.setAttribute('position', new THREE.Float32BufferAttribute(arr, 3));
  geo.applyMatrix4(mesh.matrixWorld);

  const helmet = new THREE.Mesh(geo, paintMaterial(tl));
  const group = new THREE.Group(); group.add(helmet); group.add(buildVisor(geo, maskData)); scene.add(group);

  const size = () => {
    const w = canvas.clientWidth, h = canvas.clientHeight; if (!w || !h) return;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    // frame the helmet's front so it fills the canvas width
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
