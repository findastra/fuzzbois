// Fuzzboi rules and drawing, shared by the Fuzzboi Forge (index.html) and Fuzzboi Friend
// (findastra/fuzzboi-friend, which loads this file from GitHub Pages). One copy of the rules:
// change them here, nowhere else. Plain script, no modules, so it also works from file://.
(function(){
// ---------- trait tables (numbers follow the Procreate layer names) ----------
const ACC = {1:"Cowboy hat",2:"Joint",3:"Birthday hat",4:"Butterfly",5:"Flower",6:"Crown",7:"Glasses",8:"Cheese",9:"Taco"};
const HATS = new Set([1,3,6]);
const RARE = {1:"Hands",2:"Feet",3:"Eyelashes",4:"Blush"};
const FILL = {A:["#d6306e","#5ed546","#a86bf0","#bed3e8","#fbf86a"],
              B:["#ec6e64","#f2bb64","#1d3c8a","#7a1e8e","#e93323"],
              C:["#ae9be0","#ee7fae","#3373f1","#fbf24c","#6ceb96"]};
const OUTLINE = {A:"#151515",B:"#f20ac8",C:"#151515"};
const POS = ["Style","Color","Acc 1","Acc 2","Acc 3","Rare?"];
// bottom → top, mirroring the Procreate stack
const STACK = ["rare2","fill","outline","acc7","eyes","rare4","rare3","rare1","acc9","acc8","acc6","acc5","acc3","acc2","acc1","acc4"];

// every layer the generator can use: [key, Procreate layer name]
const EXPECTED = [];
for (const s of "ABC"){ EXPECTED.push(["outline"+s,"Body Style "+s]); for(let i=1;i<=5;i++) EXPECTED.push(["fill"+s+i, s+i]); }
for (let i=1;i<=9;i++) EXPECTED.push(["acc"+i,`Accessory (${i}): ${ACC[i]}`]);
for (let i=1;i<=4;i++) EXPECTED.push(["rare"+i,`Rarity (${i}): ${RARE[i]}`]);
EXPECTED.push(["eyes","Default Eyes"]);

// TEMPORARY letter rule (2026-10-09): no trait uses A–F yet, so a letter counts as its hex
// value minus 10 (A→0 … F→5). The background is still the exact hex code. Replace this when
// Astra decides what letters mean.
const LETTER_RULE = "Letters A–F count as 0–5 for now (A=0, B=1, C=2, D=3, E=4, F=5). That’s a temporary rule until letters get their own traits.";
function traitDigit(ch){ const v = parseInt(ch,16); return v>9 ? v-10 : v; }

// ---------- decoding ----------
function decode(input){
  const code = String(input||"").toUpperCase();
  const out = {code, valid:true, flags:[], parts:{}};
  if (!/^[0-9A-F]{6}$/.test(code)){ out.valid=false; out.flags.push(["bad","Enter all six characters: 0–9 or A–F."]); return out; }
  const hasLetters = /[A-F]/.test(code);
  if (hasLetters) out.flags.push(["warn",LETTER_RULE]);
  const d = [...code].map(traitDigit);
  const style = d[0]<=2 ? "A" : d[0]<=5 ? "B" : "C";
  const color = d[1]%5 || 5;
  const accs = []; let hat = null; const dropped = [];
  for (const a of d.slice(2,5)){
    if (!a || accs.includes(a)) continue;
    if (HATS.has(a)){ if (hat){ dropped.push(a); continue; } hat = a; }
    accs.push(a);
  }
  if (dropped.length){ out.valid=false; out.flags.push(["bad",`Two hats in one code. Kept the ${ACC[hat].toLowerCase()}, left out the ${dropped.map(x=>ACC[x].toLowerCase()).join(" and ")}. Under your rules this code can’t mint.`]); }
  const dupes = d.slice(2,5).filter((a,i,arr)=>a && arr.indexOf(a)!==i);
  if (dupes.length) out.flags.push(["warn",`The ${ACC[dupes[0]].toLowerCase()} appears twice; it’s drawn once.`]);
  let rares = [];
  if (d[5]===0){
    rares = [1,2,3,4].filter(r => d.slice(0,5).includes(r));
    if (rares.length) out.flags.push(["ok",`Rare! Position 6 is 0, and the code contains ${rares.join(", ")} → ${rares.map(r=>RARE[r]).join(" + ")}.`]);
    else out.flags.push(["warn","Position 6 is 0 but no 1–4 appears elsewhere, so no rarity layer applies under the current rule."]);
  }
  if (accs.includes(8) || accs.includes(9)) out.flags.push(["warn","Your notes say Taco = 8 and Cheese = 9, but the Procreate layers say Cheese (8) and Taco (9). This page follows the layer names."]);
  Object.assign(out.parts,{d,style,color,accs,rares,hasLetters,bg:"#"+code});
  return out;
}

// Plain-words list of what a code makes, for any page.
function describe(p){
  return [
    ["Body style", `Style ${p.style}`],
    ["Body color", `${p.style}${p.color}`, FILL[p.style][p.color-1]],
    ["Accessories", p.accs.length ? p.accs.map(a=>ACC[a]).join(", ") : "None"],
    ["Rarity", p.rares.length ? p.rares.map(r=>RARE[r]).join(" + ") : "Not rare"],
    ["Background", p.bg, p.bg],
  ];
}

// ---------- rendering ----------
function needed(p){ return ["fill"+p.style+p.color, "outline"+p.style, "eyes", ...p.accs.map(a=>"acc"+a), ...p.rares.map(r=>"rare"+r)]; }
function missing(p, layers){ return needed(p).filter(k=>!layers.has(k)); }

// Draws the real art from loaded layers. Resizes the canvas to the layer size.
function drawLayers(cv, p, layers){
  const ctx = cv.getContext("2d");
  const any = layers.get("eyes");
  const W = any.naturalWidth, H = any.naturalHeight;
  if (cv.width!==W || cv.height!==H){ cv.width=W; cv.height=H; }
  ctx.fillStyle = p.bg; ctx.fillRect(0,0,W,H);
  const want = new Set(["fill","outline","eyes", ...p.accs.map(a=>"acc"+a), ...p.rares.map(r=>"rare"+r)]);
  for (const slot of STACK){
    if (!want.has(slot)) continue;
    const k = slot==="fill" ? "fill"+p.style+p.color : slot==="outline" ? "outline"+p.style : slot;
    ctx.drawImage(layers.get(k),0,0,W,H);
  }
}

// A rough sketch so a page works before the layers arrive. Not the art.
function drawStandIn(cv, p){
  if (cv.width!==2048){ cv.width=cv.height=2048; }
  const S = 2048, c = cv.getContext("2d"); c.save();
  c.fillStyle = p.bg; c.fillRect(0,0,S,S);
  const cx=S*.46, cy=S*.54, R=S*.3;
  const n = p.style==="C" ? 11 : p.style==="B" ? 9 : 26;
  const amp = p.style==="C" ? .1 : p.style==="B" ? .32 : .12;
  c.beginPath();
  for (let i=0;i<=n*2;i++){
    const a = i/(n*2)*Math.PI*2 - Math.PI/2;
    const r = R*(1 + (i%2 ? -amp*.4 : amp));
    const x=cx+Math.cos(a)*r, y=cy+Math.sin(a)*r;
    if (!i) c.moveTo(x,y);
    else { const a0=(i-.5)/(n*2)*Math.PI*2-Math.PI/2, r0=R*(p.style==="C"?1.12:.97); c.quadraticCurveTo(cx+Math.cos(a0)*r0, cy+Math.sin(a0)*r0, x, y); }
  }
  c.closePath();
  c.fillStyle = FILL[p.style][p.color-1]; c.fill();
  c.lineWidth = S*.022; c.lineJoin="round"; c.strokeStyle = OUTLINE[p.style]; c.stroke();
  for (const ex of [-.24,.22]){
    c.fillStyle="#050505"; c.beginPath(); c.ellipse(cx+ex*S*.62, cy, S*.042, S*.055, 0, 0, Math.PI*2); c.fill();
    c.fillStyle="#fff"; c.beginPath(); c.arc(cx+ex*S*.62+S*.012, cy+S*.012, S*.017,0,Math.PI*2); c.fill();
    c.beginPath(); c.arc(cx+ex*S*.62-S*.014, cy-S*.022, S*.009,0,Math.PI*2); c.fill();
  }
  c.font = `${S*.045}px Gaegu, cursive`; c.textAlign="left"; c.fillStyle="#ffe95c";
  const tags = [...p.accs.map(a=>ACC[a]), ...p.rares.map(r=>"✶ "+RARE[r])];
  tags.forEach((t,i)=>c.fillText(t, S*.06, S*.1 + i*S*.055));
  c.restore();
}

// ---------- layers ----------
function loadImg(src, cors){
  return new Promise((res,rej)=>{ const im=new Image(); if (cors) im.crossOrigin="anonymous"; im.onload=()=>res(im); im.onerror=rej; im.src=src; });
}
// Loads every layer in <base>/<key>.png into the map. Returns how many loaded.
// cors: true when the layers come from another site (Fuzzboi Friend reads them from GitHub Pages).
async function loadLayers(base, layers, cors){
  let n=0;
  await Promise.all(EXPECTED.map(async ([k])=>{ try{ layers.set(k, await loadImg(`${base}${k}.png`, cors)); n++; }catch(e){} }));
  return n;
}

// Saves a canvas as a PNG through a normal browser download.
function savePng(cv, name){
  return new Promise((res,rej)=>cv.toBlob(b=>{
    if (!b) return rej(new Error("no image"));
    const a=document.createElement("a"); a.href=URL.createObjectURL(b); a.download=name;
    document.body.append(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(a.href), 4000); res();
  },"image/png"));
}

window.Fuzzboi = {ACC,HATS,RARE,FILL,OUTLINE,POS,STACK,EXPECTED,LETTER_RULE,traitDigit,decode,describe,needed,missing,drawLayers,drawStandIn,loadImg,loadLayers,savePng};
})();
