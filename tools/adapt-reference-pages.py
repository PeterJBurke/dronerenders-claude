#!/usr/bin/env python3
"""One-off: derive the StackF765 render pages from the reference dronerenders fc/ pages by explicit,
asserted text substitutions (so everything not listed here stays byte-identical to the reference).

Later hand edits made directly in fc/index.html are NOT reproduced by this script: the "Mounting" view
preset, the grommet label and legend entry, and the side-view offset of the frame label (2026-11-19,
rubber grommet mounting). The mounting wording below was updated at the same time."""
import re, pathlib
REF = pathlib.Path('/root/fcclaude/build/ref-dronerenders/fc'); OUT = pathlib.Path('/root/fcclaude-renders/fc')
def sub(s, a, b, n=1):
    assert s.count(a) == n, (s.count(a), a[:90]); return s.replace(a, b)
def rsub(s, pat, b, n=1):
    s2, k = re.subn(pat, lambda m: b, s, flags=re.S); assert k == n, (k, pat[:90]); return s2
IMPORTMAP = '<script type="importmap">{"imports":{"three":"./assets/three-shim.js"}}</script>'
REPO_LINE = 'Renders generated from the KiCad design files at <a class="inline" href="https://github.com/PeterJBurke/stackf765" rel="noopener">github.com/PeterJBurke/stackf765</a>'
STATUS = 'Design verified by rule checks; no hardware built yet.'
NATIVE = r'<script src="assets/native-mesh-00\.js[^>]*></script>.*?<script src="assets/native-current-loader\.js[^>]*></script>'
def strip_hashes(s): return re.sub(r'\?h=[0-9a-f]{12}', '', s)

# ------------------------------------------------------------------ index.html (Drone)
s = strip_hashes((REF / 'index.html').read_text())
s = sub(s, '<title>FC — current native stack candidate</title>', '<title>StackF765 — Drone</title>' + IMPORTMAP)
s = sub(s, '#legend [hidden]{display:none!important}', '#legend [hidden]{display:none!important}aside a.inline{font:inherit;color:inherit;background:none;border:0;padding:0;border-radius:0;text-decoration:underline}')
s = sub(s, '<h1 id="selectedTitle">New FC<br/>', '<h1 id="selectedTitle">StackF765<br/>')
s = sub(s, 'Actual supplied frame meshes and current native board placement. Frame and main flight-controller stack only.',
        'Actual supplied frame meshes and StackF765 board placement. Frame, main flight-controller stack and its service board only.')
s = sub(s, '4″ regular arms · Cargo top/bottom · cross plate<br/>30 mm frame standoffs.',
        '4″ regular arms · Cargo top/bottom · cross plate<br/>30 mm frame standoffs: the four at the nose and tail are shown, the two middle ones (beside the flight controller’s tail end) are left out.<br/>Frame design: MOD-L by ledroneclub, <a class="inline" href="https://www.thingiverse.com/thing:4295478" rel="noopener" target="_blank">Thingiverse thing 4295478</a>, licensed Creative Commons Attribution (CC BY).')
s = rsub(s, r'(?<=<div class="key" id="newFCDetails">).*?(?=</div>)',
         'StackF765: STM32F765VIT6 flight controller, ArduPilot board name StackF765, 2S–3S, 50 A. Upper (flight controller) and Lower (power) boards: 31.5 × 48 mm on 8.0 mm standoffs; Upper top surface 9.6 mm above the Lower’s. Rev B. Soft-mounted, Matek style: a silicone grommet is pressed into each of the Lower board’s four 4 mm holes (20 × 20 mm pattern) and an M2 screw with a washer goes through each grommet into the frame, so the Lower board floats on rubber 2.5 mm above the plate. The Upper board is not fastened to the frame; it sits on the Lower board’s three standoffs. Interboard connectors: Samtec SFMC-110-02-L-D (Lower J1) / FTSH-110-04-L-DV (Upper J3); standoffs Sinhoo SMTSO2080CTJ, 8 mm. Upper J1 is a 3×12 and Lower J2 a 3×9 right-angle header, bodies overhanging the front edge. Service board (USB / buzzer / boot) is on a 100 mm cable and can be mounted anywhere on the airframe; shown loose. It is 18 × 32 mm; the cable is six-wire JST-SH.')
s = rsub(s, r'(?<=<p id="newFCFit">).*?(?=</p>)',
         'KiCad board models with standard dark-green display solder mask, black headers and gold pins applied as display materials. No synthetic pad solids, overlaid board textures or altered board geometry. The orange silicone grommets (generic “M3 to M2” type: 4 mm waist, 6.6 mm flanges, 6.6 mm tall), washers and M2 screws are nominal illustrations, as is the cable route to the loose service board, which lies on the ground grid beside the frame and is not fixed to it. No motors, ESC, battery or other wiring. ' + STATUS)
s = rsub(s, r'(?<=<summary>Current geometry and display limits</summary><p>).*?(?=</p></details>)',
         'Boards are the GLB models KiCad exports from the design files, placed by rigid transforms only: Lower PCB 2.5–4.1 mm above the bottom plate on the lower flanges of its grommets, 8.0 mm standoffs, 31.5 × 48 mm outlines. Colours are display materials, not a fabrication finish. Header visibility toggles the Upper J1 and Lower J2 header models; the interboard connector stays visible. The silicone grommets, M2 screws and cable are simple drawn shapes, not CAD; frame-side nuts are not drawn. The Matek option is a separate historical photo-derived reference.</p><p>' + REPO_LINE + '.</p><p><a class="inline" href="../CREDITS.txt">Credits and licences</a>')
s = sub(s, 'value="ours"/>New FC</label>', 'value="ours"/>StackF765</label>')
s = sub(s, '<div class="label" id="fcLabel">New FC stack<small>', '<div class="label" id="fcLabel">StackF765 stack<small>')
s = sub(s, 'CC BY · New FC placement · fit not qualified</span>', 'CC BY · StackF765 placement · fit not qualified</span>')
s = rsub(s, NATIVE, '<script src="assets/native-frame.js"></script>')
s = sub(s, "<script>\n(()=>{'use strict';", "<script type=\"module\">\nimport{addFrame,addStackF765Assembly}from'./assets/stackf765-loader.js';const THREE=window.THREE;\n(()=>{'use strict';")
s = sub(s, 'addCurrentNativeAssembly(THREE,groups);', 'addFrame(groups);')
s = sub(s, "(ours?'New FC':'Matek F405-WMO')+'<br>MOD-L", "(ours?'StackF765':'Matek F405-WMO')+'<br>MOD-L")
s = sub(s, "'Current native Upper and Lower geometry at an 8.5 mm face gap; unchanged frame and provisional mounting hardware.'",
        "'StackF765 Upper and Lower boards on 8.0 mm standoffs, with the service board on its 100 mm cable; the Lower board is soft-mounted on four silicone grommets (20 × 20 mm, M2 screws).'")
s = sub(s, "ours?'New FC stack<small>Direct rubber-grommet mounting</small>'", "ours?'StackF765 stack<small>Soft-mounted on 4 silicone grommets · 20 × 20 mm · M2</small>'")
s = sub(s, "(ours?'New FC placement':'Matek reference reconstruction')", "(ours?'StackF765 placement':'Matek reference reconstruction')")
s = sub(s, "ours?'New FC uses four rubber grommets.'", "ours?'StackF765 is soft-mounted on four silicone grommets with M2 screws.'")
s = sub(s, "'Toggle exact source-bound external J1/J2 header meshes; interboard pair unchanged'", "'Toggle the external J1/J2 header models; interboard pair unchanged'")
s = sub(s, 'nativeGeometryPreserved:true', 'boardGeometryPreserved:true')
s = sub(s, 'window.cargoViewer={scene,camera,renderer,groups,penny,setView,update,selectFC};window.CARGO_READY=true;',
        'window.cargoViewer={scene,camera,renderer,groups,penny,setView,update,selectFC};')
s = sub(s, "selectFC('ours');setView('iso');\n})();",
        "selectFC('ours');setView('iso');\n"
        "const status=document.getElementById('renderStatus'),statusText=status.textContent;status.textContent='Loading boards…';\n"
        "addStackF765Assembly(groups,{serviceSite:'drone'}).then(()=>{for(const m of groups.fc.children)if(m.userData.dupontHeader)m.visible=headersVisible;refreshSelectionText();window.CARGO_READY=true;update()}).catch(e=>{console.error(e);document.getElementById('error').textContent=e.message;status.textContent='Board models could not be loaded.';document.getElementById('legend').hidden=false});\n})();")
assert 'New FC' not in s and 'native' not in s.replace('native-frame', ''), [m.start() for m in re.finditer('native', s)]
(OUT / 'index.html').write_text(s)

# ------------------------------------------------------------------ board.html
s = strip_hashes((REF / 'board.html').read_text())
s = sub(s, '<title>FC — Board</title>', '<title>StackF765 — Board</title>' + IMPORTMAP)
s = sub(s, '<option value="lower">Lower</option>', '<option value="lower">Lower</option><option value="service">Service</option>')
s = sub(s, '<button id="upperPins"></button><button id="lowerPins"></button>', '<button id="service"></button><button id="upperPins"></button><button id="lowerPins"></button><button id="servicePins"></button>')
s = rsub(s, r'(?<=<aside hidden="" id="legend">).*?(?=<section aria-label="Connector pin reference")',
         '<h1>StackF765 boards</h1>'
         '<p>31.5 × 48 mm boards on 8.0 mm standoffs: Upper top surface 9.6 mm above the Lower’s. Upper is the flight controller (STM32F765VIT6, ArduPilot board name StackF765); Lower is the power board (2S–3S, 50 A). Rev B. Interboard connectors: Samtec SFMC-110-02-L-D (Lower J1) / FTSH-110-04-L-DV (Upper J3); standoffs Sinhoo SMTSO2080CTJ, 8 mm. Upper J1 is a 3×12 and Lower J2 a 3×9 right-angle header, bodies overhanging the front edge. Service board (USB, buzzer, boot): 18 × 32 mm on a 100 mm six-wire JST-SH cable. ' + STATUS + '</p>'
         '<p>Soft-mounted, Matek style: a silicone grommet is pressed into each of the Lower board’s four 4 mm holes (20 × 20 mm pattern) and an M2 screw with a washer goes through each grommet into the frame, so the Lower board floats on rubber 2.5 mm above the plate. The Upper board is not fastened to the frame; it sits on the Lower board’s three standoffs. Here the stack stands on its grommets on the floor grid; “Explode stack” lifts the Upper board and the four screws, leaving the grommets in the Lower board. The orange grommets (generic “M3 to M2” type: 4 mm waist, 6.6 mm flanges), washers and screws are nominal illustrations, not supplier models. No harness wires; the service cable is not drawn on this page.</p>'
         '<p>Standard dark-green display mask, black headers and gold pins are display materials on the KiCad board models; board geometry unchanged. The J1/J2 header toggle preserves the interboard connector.</p>'
         '<p>' + REPO_LINE + '. <a class="inline" href="../CREDITS.txt">Credits and licences</a>.</p>')
s = sub(s, '<span>Current native geometry · provisional hardware · not fabrication-ready</span>', '<span>KiCad board geometry · illustrative silicone grommets and M2 screws · ' + STATUS + '</span>')
s = sub(s, '<script src="assets/current-native-metadata.js"></script>', '')
s = rsub(s, NATIVE, '')
s = sub(s, '<script src="assets/viewer.js"></script><script src="assets/pin-data.js"></script><script src="assets/pin-table.js"></script>',
        '<script src="assets/pin-data.js"></script><script src="assets/pin-table.js"></script><script type="module" src="assets/viewer.js"></script>')
assert 'native' not in s
(OUT / 'board.html').write_text(s)

# ------------------------------------------------------------------ assets/viewer.js (Board page)
s = (REF / 'assets/viewer.js').read_text()
s = sub(s, "(()=>{'use strict';const scene=", "import{addStackF765Assembly}from'./stackf765-loader.js';const THREE=window.THREE;\n(async()=>{'use strict';const viewLabelEl=document.getElementById('viewLabel');viewLabelEl.textContent='Loading boards…';const scene=")
s = rsub(s, r"// Shared, source-bound current native payload.*?window\.CARRIER_SURFACES_READY=true;",
         "// The StackF765 KiCad board models (shared loader); the service board lies alone on the floor plane.\n"
         "const nativeGroups={frame:new THREE.Group(),roof:new THREE.Group(),fc:new THREE.Group()};await addStackF765Assembly(nativeGroups,{serviceSite:'bench'});viewLabelEl.textContent='';for(const m of [...nativeGroups.fc.children]){m.userData.baseZ=m.position.z;scene.add(m);items.push(m);}window.CARRIER_SURFACES_READY=true;")
s = sub(s, "const selected=boardOnly==='Upper'?'UpperLogic':boardOnly==='Lower'?'LowerPower':null;", "const selected=boardOnly==='Upper'?'UpperLogic':boardOnly==='Lower'?'LowerPower':boardOnly==='Service'?'Service':null;")
s = sub(s, "m.visible=selected?m.userData.board===selected:true;", "m.visible=selected?m.userData.board===selected:m.userData.board!=='Service';")
s = sub(s, "selected=activePinView==='Upper'?'UpperLogic':'LowerPower';", "selected=activePinView==='Upper'?'UpperLogic':activePinView==='Lower'?'LowerPower':'Service';")
s = sub(s, "[['upperPins','Upper'],['lowerPins','Lower']]", "[['upperPins','Upper'],['lowerPins','Lower'],['servicePins','Service']]", 2)
s = sub(s, "for(const id of ['upperPins','lowerPins'])", "for(const id of ['upperPins','lowerPins','servicePins'])")
s = sub(s, "for(const [id,name]of [['upper','Upper'],['lower','Lower']])document.getElementById(id).onclick", "for(const [id,name]of [['upper','Upper'],['lower','Lower'],['service','Service']])document.getElementById(id).onclick")
s = sub(s, "showPinView(e.target.value==='upper'?'Upper':'Lower')", "showPinView(e.target.value==='upper'?'Upper':e.target.value==='lower'?'Lower':'Service')")
s = sub(s, "if(initialView==='upper-pins'||initialView==='lower-pins')showPinView(initialView==='upper-pins'?'Upper':'Lower');\n})();",
        "if(initialView==='upper-pins'||initialView==='lower-pins'||initialView==='service-pins')showPinView(initialView==='upper-pins'?'Upper':initialView==='lower-pins'?'Lower':'Service');\n})().catch(e=>{console.error(e);document.getElementById('viewLabel').textContent='Board models could not be loaded: '+e.message});")
s = sub(s, "throw new Error('Current board geometry is missing for '+selected)", "throw new Error('Board geometry is missing for '+selected)")
s = sub(s, "throw Error('Mobile view has no current geometry')", "throw Error('Mobile view has no geometry')")
s = sub(s, "// Fit the complete current board", "// Fit the complete board")
(OUT / 'assets/viewer.js').write_text(s)

# ------------------------------------------------------------------ compare-upper.html / compare-lower.html
for which, Which in (('upper', 'Upper'), ('lower', 'Lower')):
    s = strip_hashes((REF / f'compare-{which}.html').read_text())
    s = sub(s, f'<title>FC — {Which} comparison</title>', f'<title>StackF765 — {Which} comparison</title>' + IMPORTMAP)
    s = sub(s, '<option value="board.html?view=lower-pins">Lower board</option>', '<option value="board.html?view=lower-pins">Lower board</option><option value="board.html?view=service-pins">Service board</option>')
    s = sub(s, 'value="ours"/> Our FC</label>', 'value="ours"/> StackF765</label>')
    s = sub(s, 'type="checkbox"/> Our headers</label>', 'type="checkbox"/> Headers</label>')
    s = sub(s, '<p>Our FC uses the same current native geometry, dark-green display mask and exact header ownership as the Drone and Board pages. Side-by-side placement is a display-only rigid transform; Matek remains a photograph-derived reference, not manufacturer CAD. Hardware and fabrication are not qualified.</p>',
            '<p>StackF765 uses the same KiCad board models, dark-green display mask and header toggle as the Drone and Board pages. Side-by-side placement is a display-only rigid transform; Matek remains a photograph-derived reference, not manufacturer CAD. ' + STATUS + '</p>')
    s = sub(s, '<p>Our FC: <b>31.5 × 48 mm</b>.', '<p>StackF765: <b>31.5 × 48 mm</b>.')
    s = sub(s, '<p>Our board uses current native CAD and pad artwork. Matek uses', '<p>The StackF765 board is the model KiCad exports from the design files, with its pad artwork. Matek uses')
    s = sub(s, 'power pads at the same −Y end as our board.', 'power pads at the same −Y end as the StackF765 board.', 1 if which == 'lower' else 0)
    s = sub(s, '<p class="status">Placement and visualization study. Our electrical routing and hardware qualification remain unfinished.</p>', '<p class="status">Placement and visualization study. ' + STATUS + '</p>')
    s = sub(s, '<p><a href="assets/matek-model-provenance.json">Matek model sources and dimension limits</a></p>', '<p><a href="assets/matek-model-provenance.json">Matek model sources and dimension limits</a></p><p>' + REPO_LINE + '. <a class="inline" href="../CREDITS.txt">Credits and licences</a>.</p>')
    s = rsub(s, r'<div class="scene-label" id="ourLabel"><b>Our FC</b><span>\w+ · native CAD</span></div>', f'<div class="scene-label" id="ourLabel"><b>StackF765</b><span>{Which} · KiCad model</span></div>')
    s = sub(s, '<script src="assets/current-native-metadata.js"></script>', '')
    s = rsub(s, NATIVE, '')
    s = sub(s, '<script src="assets/compare.js"></script>', '<script type="module" src="assets/compare.js"></script>')
    assert 'Our ' not in s and 'native' not in s, s
    (OUT / f'compare-{which}.html').write_text(s)

# ------------------------------------------------------------------ assets/compare.js
s = (REF / 'assets/compare.js').read_text()
s = sub(s, "(()=>{'use strict';const board=", "import{addStackF765Assembly}from'./stackf765-loader.js';const THREE=window.THREE;\n(async()=>{'use strict';const board=")
s = sub(s, "'Our FC: native CAD · Matek: reference 3D · penny Ø19.05 mm'", "'StackF765: KiCad model · Matek: reference 3D · penny Ø19.05 mm'")
s = sub(s, "ours.name='Our FC';", "ours.name='StackF765';")
s = sub(s, "addCurrentNativeAssembly(THREE,ng);", "await addStackF765Assembly(ng,{boards:[board==='UpperLogic'?'upper':'lower'],hardware:false});")
s = sub(s, "throw Error('Unknown current native board')", "throw Error('Unknown board')")
s = sub(s, "throw Error('Current board missing')", "throw Error('Board model missing')")
s = sub(s, "sourceTopZ:topZ,currentNative:true}", "sourceTopZ:topZ,stackF765:true}")
(OUT / 'assets/compare.js').write_text(s)

# ------------------------------------------------------------------ assets/pin-table.js
s = (REF / 'assets/pin-table.js').read_text()
s = sub(s, "throw new Error('Current FC pin data missing')", "throw new Error('StackF765 pin data missing')")
s = sub(s, "intro.textContent='Seven UARTs including GPS. Match the numbered connector and pin-1 mark; screen direction changes when the board is rotated.'", "intro.textContent=data.intro")
s = rsub(s, r"scope\.textContent='Includes all external connectors.*?hardware qualification\.'", "scope.textContent=data.scope")
(OUT / 'assets/pin-table.js').write_text(s)
print('ok')
