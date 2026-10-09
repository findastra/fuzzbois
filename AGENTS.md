# Rules for assistants working on Fuzzbois (fuzzbois)

Public credit is always **Astra**, never a legal name. Fuzzbois are Astra's own drawings: do not add anyone else's art, and do not generate or redraw the layers.

Website (Fuzzboi Forge) and shared rules file with Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-09. Record your model name and version here when you change something substantial.

- **Live site:** <https://findastra.github.io/fuzzbois/>. GitHub Pages serves `main` from the repo root; `index.html` forwards to `site/`. Keep `.nojekyll`.
- **One copy of the rules:** `site/fuzzboi.js` holds the trait tables, decoding and drawing. The Forge (`site/index.html`) and Fuzzboi Friend (`findastra/fuzzboi-friend`, loading it from the live site) both use it, so a change here changes both. Keep it a plain script (no modules) and keep `window.Fuzzboi`'s names stable.
- **Letters A–F are a temporary rule** (count as 0–5, 2026-10-09) until Astra decides. Card: `findastra/fuzzboi-friend` handoffs/001.
- The repo description starts with the website link, and the Website field is set to it.
- Check after a change: serve the repo (`python -m http.server`) and try `456900`, `C0FFEE` and `A1361F` (two hats), Save PNG, and phone width.
