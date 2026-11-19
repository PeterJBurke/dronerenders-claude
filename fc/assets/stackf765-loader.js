/* StackF765 board loader, shared by the Drone, Board and comparison pages.
 *
 * Replaces the reference viewer's native-mesh payload (native-mesh-*.js + native-current-loader.js)
 * with the three GLB models that KiCad exports from the StackF765 design files (../models/*.glb:
 * metres, Y up, board centred in X/Z, PCB bottom face at Y = 0, pin headers toward -Z).
 *
 * Scene convention is the reference's: millimetres, X lateral, +Y toward the nose, Z up,
 * Z = 0 on the top face of the frame's bottom plate, X/Y = 0 at the centre of the 20 x 20 mm FC mount.
 *
 * Every object handed back carries the userData the reference page scripts expect:
 *   board: 'UpperLogic' | 'LowerPower' | 'Service' | undefined (mounting screws)
 *   role:  'board' | 'header' | 'grommet' | 'provisional_hardware' | 'service_illustration'
 *   dupontHeader: true for the 0.1 inch right-angle headers (Upper J1, Lower J2)
 */
import { GLTFLoader } from './GLTFLoader.js';
import { mergeGeometries } from './BufferGeometryUtils.js';

const THREE = window.THREE;

export const DIM = {
  board: [31.5, 48],   // Upper and Lower outline
  service: [18, 32],   // Service outline
  pcb: 1.6,            // PCB thickness
  standoff: 8.0,       // board-to-board standoff
  gap: 9.6,            // Lower top surface -> Upper top surface (standoff + PCB)
  hole: 10,            // 20 x 20 mm mounting pattern: holes at +-10 mm
  grommet: 6.6,        // silicone grommet, overall height ("M3 to M2" type; nominal)
  flange: 2.5,         // grommet flange thickness below and above the PCB
  flangeDia: 6.6,      // grommet flange diameter (the board keeps 7 mm clear around each hole)
  grommetHole: 4.0,    // Lower board mounting hole = grommet waist
  ground: -7.4,        // the drone page's ground grid (just under the frame's cross plate)
  cable: 100,          // service cable length
};
// Soft mounting: the Lower board rides on the lower flanges of four grommets that stand directly on
// the frame plate. Nothing rigid touches the board; the Upper board is carried by the Lower one.
DIM.zLower = DIM.flange;                               // bottom face of the Lower PCB: 2.5
DIM.zUpper = DIM.zLower + DIM.gap;                     // bottom face of the Upper PCB: 12.1

// Same shape as the reference's window.FC_VIEW_METADATA.
export const VIEW_METADATA = {
  board_dimensions_mm: DIM.board,
  floor_z: 0,
  source: 'StackF765 KiCad GLB exports (github.com/PeterJBurke/stackf765)',
  top_planes_mm: { UpperLogic: DIM.zUpper + DIM.pcb, LowerPower: DIM.zLower + DIM.pcb, Service: DIM.pcb },
  hardware_built: false,
};
window.FC_VIEW_METADATA = VIEW_METADATA;

const BOARDS = {
  lower: { key: 'LowerPower', name: 'Lower', headers: ['J2'], z: DIM.zLower },
  upper: { key: 'UpperLogic', name: 'Upper', headers: ['J1'], z: DIM.zUpper },
  service: { key: 'Service', name: 'Service', headers: [], z: 0 },
};
// Where the drone page shows the service board: a loose accessory, not fixed to the frame. It lies
// flat on the ground grid to the right of the frame, between the two right-hand arms, component side
// up, with its cable connector (J2) toward the stack. The user mounts it wherever suits the airframe.
export const SERVICE_SITE = { x: 80, y: 0, z: DIM.ground + 0.1, rotZ: -Math.PI / 2 };

/* ---- display materials -------------------------------------------------------------------
 * KiCad's export colours are replaced by the reference viewer's board appearance: dark-green solder
 * mask, black header housings, gold pins and gold pad finish. Only materials change; geometry,
 * positions and silkscreen artwork are used exactly as exported.
 */
const near = (c, r, g, b, tol = 0.035) => Math.abs(c.r - r) < tol && Math.abs(c.g - g) < tol && Math.abs(c.b - b) < tol;
// Parts whose KiCad model carries no colour at all (the export leaves them untextured) get a plain
// body colour by reference-designator class, taken from the reference viewer's palette (linear RGB).
const PART_COLOURS = {
  U: [0.051, 0.051, 0.051], Q: [0.051, 0.051, 0.051], D: [0.072, 0.072, 0.072], FB: [0.072, 0.072, 0.072],
  R: [0.041, 0.041, 0.041], C: [0.309, 0.181, 0.0], L: [0.212, 0.212, 0.212], Y: [0.527, 0.527, 0.527],
  J: [0.694, 0.694, 0.62], SW: [0.212, 0.212, 0.212], BZ: [0.041, 0.041, 0.041], H: [0.701, 0.701, 0.701],
};
const isDefault = (m) => !m.name && m.metalness === 1 && m.roughness === 1 && near(m.color, 1, 1, 1, 0.001) && !m.transparent;
function restyle(mat, cls) {
  const c = mat.color, out = mat.clone();
  out.side = THREE.DoubleSide;
  out.envMapIntensity = 1;
  if (isDefault(mat)) {                                              // untextured part
    out.color.setRGB(...(PART_COLOURS[cls] || [0.212, 0.212, 0.212]));
    out.roughness = 0.4; out.metalness = cls === 'Y' ? 0.5 : 0;
    out.userData.kind = 'part';
  } else if (mat.transparent && near(c, 0.08, 0.2, 0.14)) {                 // solder mask
    out.color.setRGB(0.0070, 0.1070, 0.0242);                         // reference display mask, sRGB 0.08 0.36 0.17
    out.opacity = 0.93; out.roughness = 0.4; out.metalness = 0;
    out.userData.kind = 'mask';
  } else if (mat.transparent && near(c, 1, 1, 1)) {                  // silkscreen
    out.color.setRGB(0.93, 0.93, 0.9); out.opacity = 1; out.transparent = false; out.roughness = 0.6; out.metalness = 0;
    out.depthWrite = true;                                           // opaque: must hide the mask beneath it
    out.userData.kind = 'silk';
  } else if (near(c, 0.7, 0.61, 0.0)) {                              // copper layers / pad finish
    out.color.setRGB(0.5704815983772278, 0.295699805021286, 0.021980946883559227);   // reference finish colour
    out.roughness = 0.35; out.metalness = 0.3;
    out.userData.kind = 'finish';
  } else if (near(c, 0.5, 0.5, 0.5) && mat.metalness > 0.9) {        // plated holes / vias
    out.color.setRGB(0.52, 0.5, 0.42); out.roughness = 0.35; out.metalness = 0.8;
    out.userData.kind = 'plating';
  } else if (near(c, 0.3, 0.3, 0.3)) {                               // FR-4 core
    out.color.setRGB(0.66, 0.62, 0.36); out.roughness = 0.6; out.metalness = 0;
    out.userData.kind = 'core';
  } else if (near(c, 0.692, 0.42, 0.051)) {                          // connector pins
    out.color.setRGB(0.57, 0.307, 0.027); out.roughness = 0.4; out.metalness = 0;   // reference pin colour
    out.userData.kind = 'pin';
  } else {                                                           // component bodies
    out.roughness = 0.4; out.metalness = near(c, 0.55, 0.55, 0.6, 0.08) ? 0.5 : 0;
    out.userData.kind = 'part';
  }
  return out;
}
function restyleTree(root) {
  const cache = new Map();
  const refClass = (o) => { for (let p = o; p; p = p.parent) { const m = /^([A-Z]+)[0-9]+$/.exec(p.name || ''); if (m) return m[1]; } return ''; };
  root.traverse((o) => {
    if (!o.isMesh) return;
    const cls = refClass(o);
    const one = (m) => { const k = m.uuid + cls; if (!cache.has(k)) cache.set(k, restyle(m, cls)); return cache.get(k); };
    o.material = Array.isArray(o.material) ? o.material.map(one) : one(o.material);
    const kind = (Array.isArray(o.material) ? o.material[0] : o.material).userData.kind;
    o.renderOrder = kind === 'mask' ? 1 : kind === 'silk' ? 2 : 0;
  });
}

/* KiCad writes every pad, track segment and drill as its own primitive, so a board arrives as some
 * twenty thousand tiny meshes. Each top-level node (one per component, one per board layer) is
 * collapsed to one mesh per material: identical triangles, a few dozen draw calls instead. */
function mergeNode(node) {
  if (node.isMesh) return;
  node.updateWorldMatrix(true, true);
  const inv = node.matrixWorld.clone().invert(), buckets = new Map(), rel = new THREE.Matrix4();
  node.traverse((o) => {
    if (!o.isMesh || Array.isArray(o.material)) return;
    const g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry.clone();
    for (const name of Object.keys(g.attributes)) if (name !== 'position' && name !== 'normal') g.deleteAttribute(name);
    if (!g.attributes.normal) g.computeVertexNormals();
    g.applyMatrix4(rel.multiplyMatrices(inv, o.matrixWorld));
    if (!buckets.has(o.material)) buckets.set(o.material, { geos: [], order: o.renderOrder });
    buckets.get(o.material).geos.push(g);
  });
  if (!buckets.size) return;
  node.clear();
  for (const [material, b] of buckets) {
    const merged = b.geos.length === 1 ? b.geos[0] : mergeGeometries(b.geos, false);
    if (!merged) throw new Error('Could not merge board geometry for ' + node.name);
    for (const g of b.geos) if (g !== merged) g.dispose();
    const mesh = new THREE.Mesh(merged, material);
    mesh.renderOrder = b.order;
    node.add(mesh);
  }
}

function loadGLB(url, onProgress) {
  return new Promise((resolve, reject) => new GLTFLoader().load(url, resolve, onProgress, () => reject(new Error('Could not load ' + url))));
}

/* Load one board. Resolves to { body, headers, parts }:
 *   body    Group in scene convention (mm, Z up, origin at the centre of the PCB's bottom face,
 *           pin headers toward +Y). A rotation and a uniform scale only, so nothing is mirrored.
 *   headers Group with the same origin holding only the right-angle 0.1 inch header models.
 *   parts   name -> Vector3 position of each reference designator in the body's frame (mm).
 */
export async function loadBoard(id, base, onProgress) {
  const def = BOARDS[id], gltf = await loadGLB(base + id + '.glb', onProgress);
  const body = new THREE.Group(), headers = new THREE.Group(), model = gltf.scene;
  body.name = def.name; headers.name = def.name + '/headers';
  model.scale.setScalar(1000);            // KiCad exports metres
  model.rotation.x = Math.PI / 2;         // Y up -> Z up; KiCad -Z (header edge) -> +Y
  body.add(model);
  restyleTree(model);
  body.updateMatrixWorld(true);
  const top = model.children.length === 1 && !model.children[0].isMesh ? model.children[0] : model;
  for (const node of [...top.children]) mergeNode(node);
  body.updateMatrixWorld(true);
  const parts = {}, boxes = {};
  model.traverse((o) => {
    if (!o.name || o.name.startsWith('=>') || !/^[A-Z]+[0-9]+$/.test(o.name)) return;
    parts[o.name] = new THREE.Vector3().setFromMatrixPosition(o.matrixWorld);
    const b = new THREE.Box3().setFromObject(o);
    if (!b.isEmpty()) boxes[o.name] = b;
  });
  for (const ref of def.headers) {
    const h = model.getObjectByName(ref);
    if (!h) continue;
    const world = h.matrixWorld.clone();
    h.removeFromParent();
    world.decompose(h.position, h.quaternion, h.scale);
    headers.add(h);
  }
  for (const g of [body, headers]) g.userData = { group: 'fc', board: def.key, role: g === body ? 'board' : 'header', dupontHeader: g === headers, stackF765: true };
  body.userData.parts = parts; body.userData.partBoxes = boxes;
  return { id, body, headers, parts, boxes };
}

/* ---- mounting hardware (illustrative shapes generated here; not part of the KiCad export) ---- */
function cyl(r, z0, z1, mat, seg = 28) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, z1 - z0, seg), mat);
  m.rotation.x = Math.PI / 2; m.position.z = (z0 + z1) / 2;
  return m;
}
/* Soft mounting, Matek style: a silicone grommet pressed into each of the Lower board's four 4 mm
 * holes (20 x 20 mm pattern), an M2 screw with a washer through each grommet into the frame. The
 * grommet is a revolved profile: lower flange standing on the frame plate, 4 mm waist in the PCB,
 * upper flange under the washer, M2 bore. The Upper board has no holes here; it is not fastened to
 * the frame and sits on the Lower board's three standoffs.
 *   tip  Z of the screw tip: below the bottom plate on the drone page, 0 where there is no frame.
 * Returns objects for groups.fc: four grommets (role 'grommet', board 'LowerPower': they stay in the
 * board) and four screws with washers (role 'provisional_hardware': lifted when the stack is exploded).
 */
export const GROMMET_COLOUR = 0xe4472b;                               // orange-red silicone
export function grommetProfile() {
  const R = DIM.flangeDia / 2, w = DIM.grommetHole / 2 - 0.06, bore = 1.05, f = 0.7, clear = 0.12;
  const z0 = DIM.zLower - DIM.flange, z1 = z0 + DIM.grommet, zb = DIM.zLower - clear, zt = DIM.zLower + DIM.pcb + clear;
  const pts = [], arc = (cr, cz, a0, a1) => { for (let i = 0; i <= 6; i++) { const a = (a0 + (a1 - a0) * i / 6) * Math.PI / 180; pts.push(new THREE.Vector2(cr + f * Math.cos(a), cz + f * Math.sin(a))); } };
  pts.push(new THREE.Vector2(bore, z0));
  arc(R - f, z0 + f, -90, 0); arc(R - f, zb - f, 0, 90);              // lower flange, rounded rim
  pts.push(new THREE.Vector2(w, zb), new THREE.Vector2(w, zt));       // waist through the PCB
  arc(R - f, zt + f, -90, 0); arc(R - f, z1 - f, 0, 90);              // upper flange
  pts.push(new THREE.Vector2(bore, z1));
  return pts;
}
export function makeMountHardware({ tip = 0 } = {}) {
  const steel = new THREE.MeshStandardMaterial({ color: 0xb4b9c0, metalness: 0.85, roughness: 0.34 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x1b1d20, metalness: 0.5, roughness: 0.6 });
  const rubber = new THREE.MeshStandardMaterial({ color: GROMMET_COLOUR, metalness: 0, roughness: 0.92, envMapIntensity: 0.25 });
  const z1 = DIM.zLower - DIM.flange + DIM.grommet, out = [], prof = grommetProfile();
  for (const sx of [-1, 1]) for (const sy of [-1, 1]) {
    const gr = new THREE.Mesh(new THREE.LatheGeometry(prof, 40), rubber);
    gr.rotation.x = Math.PI / 2;                                       // lathe axis Y -> Z
    const g = new THREE.Group(); g.add(gr);
    g.name = 'Hardware/silicone grommet (illustrative)';
    g.userData = { group: 'fc', board: 'LowerPower', role: 'grommet', dupontHeader: false, illustrative: true };
    const sc = new THREE.Group();                                      // washer, socket-head cap, hex socket, shank
    sc.add(cyl(2.4, z1, z1 + 0.3, steel), cyl(1.9, z1 + 0.3, z1 + 2.3, steel), cyl(0.95, z1 + 2.26, z1 + 2.32, dark, 6), cyl(1.0, tip, z1 + 0.3, steel, 16));
    sc.name = 'Hardware/M2 screw and washer (illustrative)';
    sc.userData = { group: 'fc', role: 'provisional_hardware', dupontHeader: false, illustrative: true };
    for (const o of [g, sc]) { o.position.set(sx * DIM.hole, sy * DIM.hole, 0); out.push(o); }
  }
  return out;
}

// Round cable along a smooth path through `pts` ([x,y,z] mm); never dips below `floor` if given.
function makeCable(pts, radius = 1.25, floor = -Infinity) {
  let curve = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
  if (floor > -Infinity) curve = new THREE.CatmullRomCurve3(curve.getPoints(160).map((p) => p.setZ(Math.max(p.z, floor))), false, 'centripetal');
  const mesh = new THREE.Mesh(new THREE.TubeGeometry(curve, 96, radius, 10, false),
    new THREE.MeshStandardMaterial({ color: 0x2b2d31, metalness: 0, roughness: 0.6 }));
  mesh.userData.length = curve.getLength();
  return mesh;
}
// From the Upper board's cable connector (J5, on the right-hand edge, opening toward +X) the cable
// leaves horizontally, drapes over the edge of the bottom plate down to the ground, and lies there in
// one slack bow into the loose service board's connector (J2). The sideways slack is sized so the
// drawn cable is the real 100 mm.
function routeCable(upper, service, radius = 1.25) {
  const end = (b, ref) => {
    b.body.updateMatrixWorld(true);
    if (b.boxes[ref]) { const box = new THREE.Box3().setFromObject(b.body.getObjectByName(ref)); return { c: box.getCenter(new THREE.Vector3()), min: box.min.x, max: box.max.x }; }
    if (!b.parts[ref]) return null;
    const c = b.parts[ref].clone().applyMatrix4(b.body.matrixWorld); c.z += 1; return { c, min: c.x - 2, max: c.x + 2 };   // connector has no 3D model in this export
  };
  const a = end(upper, 'J5'), b = end(service, 'J2');
  if (!a || !b) return null;
  const ax = a.max, ay = a.c.y, az = a.c.z + 0.2, bx = b.min, by = b.c.y, bz = b.c.z, g = DIM.ground + radius + 0.05;
  const x0 = ax + 21, run = bx - 7 - x0;                 // where it reaches the ground; length of the ground run
  const lie = (t, h) => [x0 + t * run, ay + (by - ay) * t + h * Math.sin(Math.PI * t) ** 1.5, g];   // one slack bow on the ground, toward the nose
  const path = (h) => [[ax - 1.5, ay, az], [ax + 3, ay, az], [ax + 9, ay, az - 3.5], [ax + 14, ay, az - 12],
    [ax + 17.5, ay, g + 6], lie(0, h), lie(0.14, h), lie(0.28, h), lie(0.5, h), lie(0.72, h), lie(0.86, h), lie(1, h),
    [bx - 2.5, by, bz], [bx + 1.5, by, bz]];
  let lo = 0, hi = 34, cable = null;
  for (let i = 0; i < 18; i++) {
    const h = (lo + hi) / 2;
    cable = makeCable(path(h), radius, g);
    if (cable.userData.length < DIM.cable) lo = h; else hi = h;
    if (i < 17) cable.geometry.dispose();
  }
  cable.userData.slack = (lo + hi) / 2;
  return cable;
}

/* Load the boards and add them to groups.fc (the name and role of the reference's
 * addCurrentNativeAssembly). Options:
 *   boards     which GLBs to load, default all three
 *   hardware   add the illustrative grommets and M2 screws (default true)
 *   serviceSite 'drone' = loose on the ground grid beside the frame, on its 100 mm cable;
 *               'bench' = alone at the origin, lying on the floor plane (Board page)
 *   base       URL of the models folder
 *   onProgress(loadedBytes)
 */
export async function addStackF765Assembly(groups, options = {}) {
  const ids = options.boards || ['lower', 'upper', 'service'];
  const base = options.base || new URL('../models/', import.meta.url).href;
  const done = {};
  const progress = (id) => (e) => { done[id] = e.loaded; if (options.onProgress) options.onProgress(Object.values(done).reduce((a, b) => a + b, 0)); };
  const loaded = {};
  for (const b of await Promise.all(ids.map((id) => loadBoard(id, base, progress(id))))) loaded[b.id] = b;
  const counts = { boards: ids.length, hardware: 0, headers: 0, cableMm: null };
  for (const id of ['lower', 'upper']) {
    const b = loaded[id]; if (!b) continue;
    for (const g of [b.body, b.headers]) { g.position.z = BOARDS[id].z; groups.fc.add(g); }
    counts.headers += b.headers.children.length;
  }
  if (loaded.lower && options.hardware !== false) for (const h of makeMountHardware({ tip: options.serviceSite === 'drone' ? -6.8 : 0 })) { groups.fc.add(h); counts.hardware++; }
  if (loaded.service) {
    const s = loaded.service;
    if (options.serviceSite === 'drone') {
      s.body.position.set(SERVICE_SITE.x, SERVICE_SITE.y, SERVICE_SITE.z);
      s.body.rotation.z = SERVICE_SITE.rotZ;
      groups.fc.add(s.body);
      if (loaded.upper) {
        const cable = routeCable(loaded.upper, s);
        if (cable) {
          cable.name = 'Service/cable (illustrative route)';
          cable.userData = { ...cable.userData, group: 'fc', board: 'Service', role: 'service_illustration', dupontHeader: false, illustrative: true };
          groups.fc.add(cable); counts.cableMm = cable.userData.length;
        }
      }
    } else groups.fc.add(s.body);
  }
  window.STACKF765_ASSEMBLY_COUNTS = counts;
  return { loaded, counts };
}

/* The MOD-L 4" HD Cargo frame meshes, exactly as the reference packs and draws them
 * (native-frame.js -> window.CURRENT_FRAME_MESHES; this is the frame half of the reference's
 * addCurrentNativeAssembly, unchanged), except that the two middle standoffs are not drawn. */
// The frame's two middle standoffs (x = +-16.7, y = -28 mm) stand right behind the tail corners of the
// flight controller, over its battery / ESC solder pads. They are not needed and are left out; the four
// standoffs at the nose and tail ends stay. The packed mesh file itself is unchanged.
export const OMITTED_FRAME_MESHES = ['Frame/Standoff-3', 'Frame/Standoff-4'];
export function addFrame(groups) {
  const decode = (s, T) => { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new T(u.buffer); };
  const linear = (x) => (x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4));
  let n = 0;
  for (const d of window.CURRENT_FRAME_MESHES) {
    if (OMITTED_FRAME_MESHES.includes(d.name)) continue;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(decode(d.p, Float32Array), 3));
    g.setAttribute('normal', new THREE.BufferAttribute(decode(d.n, Float32Array), 3));
    const c = decode(d.c, Float32Array); for (let i = 0; i < c.length; i++) c[i] = linear(c[i]);
    g.setAttribute('color', new THREE.BufferAttribute(c, 3));
    g.setIndex(new THREE.BufferAttribute(decode(d.i, Uint32Array), 1));
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.77, metalness: 0.16, side: THREE.DoubleSide }));
    m.name = d.name; groups[d.group].add(m); n++;
  }
  if (n !== 11) throw Error('Frame mesh count mismatch');
  return n;
}
