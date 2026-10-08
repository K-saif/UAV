"""Make 4 visually different copies of the Gazebo walking actor.

Recolours BOTH the colours stored inside walk.dae (<diffuse>/<ambient>) and any texture images.
Run:  python3 make_actor_variants.py
Then: export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$HOME/gz_models   (in the terminal that runs `make`)
"""
import colorsys, glob, os, re, shutil, sys

CACHE = os.path.expanduser("~/.gz/fuel/fuel.gazebosim.org/mingfei/models/actor/*/meshes/walk.dae")
OUT = os.path.expanduser("~/gz_models")
HUE_SHIFT_DEG = {"actor_target": 150, "actor_2": 0, "actor_3": 80, "actor_4": -80}

def shift_rgb(r, g, b, deg, boost):
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + deg / 360.0) % 1.0
    if s < 0.25 and v > 0.2:           # grey/white parts get a tint, otherwise a hue shift does nothing
        s = 0.55
    s = min(1.0, s * boost)
    return colorsys.hsv_to_rgb(h, s, v)

# <diffuse><color sid="diffuse">r g b a</color></diffuse>  (same for <ambient>)
COLOR_RE = re.compile(r"(<(?:diffuse|ambient)>\s*<color[^>]*>)([^<]+)(</color>)")

def recolor_dae(path, deg, boost):
    text = open(path, encoding="utf-8").read()
    count = 0
    def repl(m):
        nonlocal count
        vals = [float(x) for x in m.group(2).split()]
        r, g, b = shift_rgb(*vals[:3], deg, boost)
        count += 1
        return f"{m.group(1)}{r:.4f} {g:.4f} {b:.4f} {vals[3] if len(vals) > 3 else 1}{m.group(3)}"
    open(path, "w", encoding="utf-8").write(COLOR_RE.sub(repl, text))
    return count

def recolor_images(root, deg, boost):
    import numpy as np
    from PIL import Image
    n = 0
    for ext in ("png", "jpg", "jpeg"):
        for p in glob.glob(f"{root}/**/*.{ext}", recursive=True):
            img = Image.open(p)
            alpha = img.getchannel("A") if img.mode in ("RGBA", "LA") else None
            hsv = np.array(img.convert("RGB").convert("HSV"), dtype=np.int16)
            hsv[..., 0] = (hsv[..., 0] + int(deg / 360 * 256)) % 256
            hsv[..., 1] = np.clip(hsv[..., 1] * boost, 0, 255)
            out = Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")
            if alpha is not None:
                out.putalpha(alpha)
            out.save(p); n += 1
    return n

found = sorted(glob.glob(CACHE), key=os.path.getmtime)
if not found:
    sys.exit(f"No cached actor found at {CACHE}")
src = os.path.dirname(os.path.dirname(found[-1]))
print("source model:", src)

for name, deg in HUE_SHIFT_DEG.items():
    dst = os.path.join(OUT, name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    if deg == 0:
        print(f"{name}: original colours (kept as reference)")
        continue
    boost = 1.3 if name == "actor_target" else 1.0
    n_col = recolor_dae(os.path.join(dst, "meshes", "walk.dae"), deg, boost)
    n_img = recolor_images(dst, deg, boost)
    print(f"{name}: hue {deg:+d} deg -> {n_col} material colour(s), {n_img} texture image(s)")
    if n_col == 0 and n_img == 0:
        print("  WARNING: nothing recoloured. Colours are probably per-vertex; send me the output of:\n"
              f"  grep -o '<[a-z_]*color[^>]*>' {src}/meshes/walk.dae | sort | uniq -c")
