"""Remove the baked-in navy background from each Procreate layer export.
Edge pixels are un-mixed: each pixel is modelled as bg*(1-a) + F*a where F is one of
the layer's dominant ink colours, so outlines keep clean edges without a navy halo."""
import numpy as np
from PIL import Image
from scipy import ndimage

BG = np.array([21, 34, 140], float)

NAMES = {
    1: "rare2", 2: "fillC5", 3: "fillC4", 4: "fillC3", 5: "fillC2", 6: "fillC1", 7: "outlineC",
    8: "fillB5", 9: "fillB4", 10: "fillB3", 11: "fillB2", 12: "fillB1", 13: "outlineB",
    14: "fillA5", 15: "fillA4", 16: "fillA3", 17: "fillA2", 18: "fillA1", 19: "outlineA",
    20: "acc7", 21: "eyes", 22: "rare4", 23: "rare3", 24: "rare1",
    25: "acc9", 26: "acc8", 27: "acc6", 28: "acc5", 29: "acc3", 30: "acc2", 31: "acc1", 32: "acc4",
}

def dominant_colors(px, k=8):
    """Crude k-means over pixels clearly not background."""
    if len(px) == 0:
        return np.zeros((0, 3))
    rng = np.random.default_rng(0)
    sample = px[rng.choice(len(px), min(len(px), 40000), replace=False)]
    # quantise first to get well-spread seeds
    q = (sample // 24).astype(int)
    keys, counts = np.unique(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2], return_counts=True)
    seeds = keys[np.argsort(-counts)[:k]]
    cent = np.array([[s // 10000, (s // 100) % 100, s % 100] for s in seeds], float) * 24 + 12
    for _ in range(12):
        d = ((sample[:, None, :] - cent[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(len(cent)):
            m = lab == j
            if m.any():
                cent[j] = sample[m].mean(0)
    return cent

def key(path):
    a = np.asarray(Image.open(path).convert("RGB"), float)
    H, W, _ = a.shape
    flat = a.reshape(-1, 3)
    dist = np.sqrt(((flat - BG) ** 2).sum(1))
    solid = flat[dist > 60]
    cents = dominant_colors(solid)
    # add black (outlines) and white (highlights) — common ink colours
    cents = np.vstack([cents, [[0, 0, 0], [255, 255, 255]]])
    alpha = np.ones(len(flat))
    color = flat.copy()
    best_res = np.full(len(flat), np.inf)
    best_a = np.zeros(len(flat))
    best_f = np.zeros((len(flat), 3))
    for F in cents:
        v = F - BG
        vv = (v * v).sum()
        if vv < 100:  # ink too close to background to separate
            continue
        t = np.clip(((flat - BG) @ v) / vv, 0, 1)
        recon = BG + t[:, None] * v
        res = np.sqrt(((flat - recon) ** 2).sum(1))
        better = res < best_res
        best_res[better] = res[better]
        best_a[better] = t[better]
        best_f[better] = F
    explained = best_res < 22          # pixel is a bg/ink blend
    alpha = np.where(explained, best_a, 1.0)
    alpha[dist < 6] = 0.0              # pure background
    # pixels that aren't a clean blend (ink/ink edges inside the art) stay opaque
    edge = explained & (alpha > 0) & (alpha < 0.98)
    color[edge] = best_f[edge]
    # tiny speckles of almost-transparent noise → drop
    alpha[alpha < 0.04] = 0
    rgba = np.dstack([color.reshape(H, W, 3), (alpha * 255).reshape(H, W)]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")

if __name__ == "__main__":
    import os, sys
    os.makedirs("layers", exist_ok=True)
    for n, name in NAMES.items():
        im = key(f"x/fuzzbois/Fuzzbois-{n}.png")
        im.save(f"layers/{name}.png", optimize=True)
        bb = im.getbbox()
        print(n, name, bb)
