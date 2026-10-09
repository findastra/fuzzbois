# Fuzzbois

## 👉 Make your Fuzzboi: **[findastra.github.io/fuzzbois](https://findastra.github.io/fuzzbois/)**

Type any six-digit hex code (like `C0FFEE`) and save that exact Fuzzboi as a PNG. Its pet app is [Fuzzboi Friend](https://findastra.github.io/fuzzboi-friend/) ([repo](https://github.com/findastra/fuzzboi-friend)).

Fuzzy little characters built from a six-digit hash code. Every code picks a body style, a body color, up to three accessories and sometimes a rarity, and the same six digits become the background color. By Astra.

![Fuzzboi #456900](art/fuzzboi-456900-original.png)

## What's in here

| Folder | What it is |
|---|---|
| `site/` | **Fuzzboi Forge**, [live here](https://findastra.github.io/fuzzbois/). Type a code, get that exact Fuzzboi at 2048×2048 and save it as a PNG. `site/fuzzboi.js` holds the rules and drawing (Fuzzboi Friend loads the same file); `site/layers/` holds the 32 cut-out layers it stacks. |
| `art/procreate-export/` | The original Procreate "PNG Files" export (`Fuzzbois-1.png` … `Fuzzbois-33.png`), navy background baked in. 33 is the design notes page. |
| `art/banner/` | The Fuzzbois parade banner and the nine sprites cut from it. |
| `3d/` | The 3D Fuzzboi #456800 (red, crown, taco, blush): Blender source, FBX, Unity package, previews, and the script that builds it. |
| `tools/key_layers.py` | Removes the baked-in navy background from a Procreate export and names each layer by its trait. |
| `legacy/2021/` | `Ownable.sol` from the 2021 NFT attempt (an OpenZeppelin contract, previously committed under the file name "SPDX License Identifier: MIT"). |

## Run the generator

The easy way is the website: <https://findastra.github.io/fuzzbois/> (a code in the address, like `#456900`, opens that Fuzzboi). GitHub Pages serves the repo root from `main`; `index.html` there sends visitors on to `site/`.

To run it on your own PC: browsers won't export a canvas built from `file://` images, so serve the folder:

```sh
cd site
python3 -m http.server 8000
# open http://localhost:8000/#456900
```

The page loads every layer in `site/layers/` automatically. A code in the address (`#456900`) opens that Fuzzboi.

## The code

**The rules are Astra's handwritten design notes, [`art/procreate-export/Fuzzbois-33.png`](art/procreate-export/Fuzzbois-33.png).** When anything here disagrees with that sheet, the sheet wins.

Positions are read left to right. **For now, letters A–F count as 0–5** (A=0, B=1, C=2, D=3, E=4, F=5) so every hex code makes a Fuzzboi; the background still uses the exact code. This is a temporary rule (2026-10-09) until letters get their own traits.

| Position | Trait | Rule |
|---|---|---|
| 1 | Body style | 0–2 → **A** (fuzzy black outline) · 3–5 → **B** (pink spiky outline) · 6–9 → **C** (cloud) |
| 2 | Body color | 1/6 → 1 · 2/7 → 2 · 3/8 → 3 · 4/9 → 4 · 5/0 → 5 |
| 3 | Accessory 1 | see list |
| 4 | Accessory 2 | see list |
| 5 | Accessory 3 | see list · no Fuzzboi wears two hats |
| 6 | Rare flag | 0 = rare |
| all six | Background | the code itself, as a hex color |

**Accessories** (from the design notes): 0 nothing · 1 cowboy hat · 2 joint · 3 birthday hat · 4 butterfly · 5 flower · 6 crown · 7 glasses · 8 taco · 9 cheese. Hats are 1, 3 and 6. The Procreate layers were numbered with cheese and taco the other way round, and the layer files keep those names (`acc8.png` is the cheese, `acc9.png` the taco); `site/fuzzboi.js` maps 8 → taco and 9 → cheese.

**Rarities:** 1 hands · 2 feet · 3 eyelashes · 4 blush. From the notes: if position 6 is 0 the Fuzzboi is rare, and it gets every rarity whose number appears in the code ("if whole hash # contains 1, 2, and/or 3 get all!", with blush = 4 added).

Layer order, bottom to top: feet, body fill, body outline, glasses, eyes, blush, eyelashes, hands, taco, cheese, crown, flower, birthday hat, joint, cowboy hat, butterfly.

### Not on the design notes yet

- **Letters A–F.** The notes use a hex code as the background color, but give no trait to letters. Until Astra adds them, the pages count a letter as its value minus 10 (A=0 … F=5). That stopgap was chosen by Claude on 2026-10-09, not by Astra; it's in `site/fuzzboi.js`, and the page says so whenever a code has a letter.
- **Position 6 is 0 but no 1–4 appears.** The notes say a 0 there means rare, but not which rarity it gets if the code has no 1, 2, 3 or 4. The pages show no rarity and say why.
- A side effect of the rules as written: a cloud body (position 1 is 6–9) can only get hands from a 1 in an accessory slot, so a cloud with hands always wears the cowboy hat.

## Exporting layers from Procreate

1. Open the Layers panel and **uncheck "Background color"** so the layers come out transparent.
2. Actions (wrench) → Share → Share Layers → **PNG Files**.
3. Files arrive as `Fuzzbois-1.png` … numbered from the bottom of the stack; the generator maps those numbers to traits. If the background was left on, run `python3 tools/key_layers.py` from a folder containing `x/fuzzbois/` to cut it out.

## 3D

`3d/build_fuzzboi.py` builds the model with Blender's Python module (`pip install bpy`) and checks that the crown and taco don't intersect the body, nudging them out if they do. `python3 3d/build_fuzzboi.py render` also renders previews. Import `Fuzzboi_456800.unitypackage` into Unity via Assets → Import Package → Custom Package. The pink rim is an inverted hull, so it needs a back-face-culled shader (Unity Standard works; Poiyomi or lilToon look better in VRChat). It's about 170k triangles: fine as a world prop, too heavy for an avatar.
