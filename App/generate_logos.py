# generate_logos.py
from PIL import Image, ImageDraw, ImageFont
import os, random
OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "logos")
os.makedirs(OUT_DIR, exist_ok=True)
NAMES = ["Dr A","Dr R","Dr S","Dr M","Dr P","Dr N","Dr K","Dr V","Dr B","Dr R2","Dr S2","Dr D","Dr T","Dr A2","Dr L","Dr O","Dr H","Dr Y","Dr F","Dr G","Dr V2","Dr R3","Dr S3","Dr K2","Dr P2"]
PALETTE = [(59,130,246),(99,102,241),(16,185,129),(244,63,94),(250,204,21),(234,88,12),(14,165,233),(168,85,247)]
W=128; H=128; FONT_SIZE=48
def get_font(s):
    candidates = ["arial.ttf","DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    for p in candidates:
        try: return ImageFont.truetype(p,s)
        except: pass
    from PIL import ImageFont; return ImageFont.load_default()
font = get_font(FONT_SIZE)
for i,name in enumerate(NAMES, start=1):
    init = "".join([t[0] for t in name.replace("Dr","").split() if t]).upper()[:2] or "DR"
    color = random.choice(PALETTE)
    img = Image.new("RGBA",(W,H), color+(255,))
    d = ImageDraw.Draw(img)
    w,h = d.textsize(init,font=font)
    d.text(((W-w)/2,(H-h)/2), init, font=font, fill=(255,255,255,255))
    out = os.path.join(OUT_DIR, f"{i}.png")
    img.save(out)
    print("wrote", out)
print("done")
