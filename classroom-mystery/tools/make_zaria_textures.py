# Tileable textures for Zaria's character (512 px each). Colour + normal maps.
import numpy as np, sys, os
from PIL import Image
OUT = sys.argv[1]; N = 512
rng = np.random.default_rng(11)

def fbm(beta=2.0, lo=2, hi=None, aniso=(1, 1)):
    """Periodic (tileable) noise: random phases with a 1/f^beta envelope."""
    fx = np.fft.fftfreq(N)[None, :] * N * aniso[0]
    fy = np.fft.fftfreq(N)[:, None] * N * aniso[1]
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[f < lo] = 0
    if hi: amp[f > hi] = 0
    spec = amp * np.exp(2j * np.pi * rng.random((N, N)))
    n = np.real(np.fft.ifft2(spec))
    return (n - n.mean()) / (n.std() + 1e-9)

def hexc(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)

def save(name, rgb):
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(os.path.join(OUT, name + '.jpg'), quality=88)

def normal(name, h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nx, ny, nz = -dx, dy, np.ones_like(h)          # OpenGL style (green = up)
    l = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    rgb = np.stack([nx / l, ny / l, nz / l], -1) * 127.5 + 127.5
    save(name + '_n', rgb)

def colour(base, h, amt):
    return hexc(base)[None, None, :] * (1 + amt * h[..., None])

# 1. Black fleece (hoodie body): soft fuzz + little pills
fuzz = fbm(1.2, 8) * 0.6 + fbm(2.5, 2) * 0.4
pills = (rng.random((N, N)) > 0.996).astype(float)
pills = np.real(np.fft.ifft2(np.fft.fft2(pills) * np.fft.fft2(np.pad(np.ones((3, 3)) / 9, ((0, N - 3), (0, N - 3))))))
h = fuzz * 0.6 + pills * 6
save('zaria_fleece', colour('#232428', fuzz * 0.5 + pills * 3, 0.09)); normal('zaria_fleece', h, 1.2)

# 2. Black rib knit (cuffs and hem): vertical ribs
x = np.arange(N)[None, :] / N
rib = np.sin(2 * np.pi * 40 * x) * np.ones((N, 1))
h = rib + fbm(1.5, 10) * 0.25
save('zaria_rib', colour('#1d1e21', rib * 0.6 + fbm(1.5, 10) * 0.4, 0.12)); normal('zaria_rib', h, 2.5)

# 3. Woodland camo tank top
base = np.zeros((N, N, 3)) + hexc('#77744d')
for col, thr, seed_beta in (('#a39c7a', 0.65, 3.2), ('#4b4a33', 0.55, 3.4), ('#2e2c22', 1.05, 3.6)):
    m = fbm(seed_beta, 2, 22)
    mask = 1 / (1 + np.exp(-(m - thr) * 18))
    base = base * (1 - mask[..., None]) + hexc(col)[None, None, :] * mask[..., None]
knit = fbm(1.0, 40) * 0.5 + np.sin(2 * np.pi * 96 * x) * 0.4
save('zaria_camo', base * (1 + 0.06 * knit[..., None])); normal('zaria_camo', knit, 1.0)

# 4. Heather black sweatpants: fine vertical fibres
streak = fbm(1.0, 6, None, aniso=(0.12, 1))
fine = fbm(0.8, 30)
save('zaria_jogger', colour('#222327', streak * 0.6 + fine * 0.4, 0.13)); normal('zaria_jogger', fine * 0.5 + streak * 0.5, 1.0)

# 5. Hair: strands running along v, with lighter brown highlights
strands = fbm(1.4, 4, None, aniso=(0.03, 1))
wisps = fbm(1.0, 20, None, aniso=(0.08, 1))
hl = np.clip(fbm(2.2, 2, 24, aniso=(0.12, 1)) - 0.6, 0, None)
hair = hexc('#221913')[None, None, :] * (1 + 0.28 * strands[..., None] + 0.18 * wisps[..., None])
hair += hexc('#5e4230')[None, None, :] * 0.28 * hl[..., None]
save('zaria_hair', hair); normal('zaria_hair', strands * 1.0 + wisps * 0.3, 2.0)

# 6. Skin: very soft variation
sk = fbm(2.5, 2) * 0.6 + fbm(1.0, 40) * 0.4
save('zaria_skin', colour('#a86e4b', sk, 0.035))

# 7. White leather sneaker upper: pebbled grain
grain = fbm(0.6, 30)
save('zaria_leather', colour('#efeeea', grain * 0.6 + fbm(2.5, 2) * 0.4, 0.025)); normal('zaria_leather', grain, 0.9)

# 8. Sole: off-white rubber with horizontal grooves (side wall)
y = np.arange(N)[:, None] / N
groove = (np.abs(np.sin(2 * np.pi * 6 * y)) < 0.18).astype(float) * np.ones((1, N))
h = -groove + fbm(0.8, 30) * 0.2
save('zaria_sole', colour('#dedcd6', -groove * 0.8 + fbm(0.8, 30) * 0.3, 0.06)); normal('zaria_sole', h, 3.0)

# 9. Zipper teeth: little metal teeth across the zip
teeth = (np.sin(2 * np.pi * 16 * y) > 0) * np.ones((1, N))
zip_rgb = np.where(teeth[..., None] > 0, hexc('#b4b6b9'), hexc('#3a3b3e'))
save('zaria_zip', zip_rgb); normal('zaria_zip', teeth.astype(float), 3.0)
print(sorted(os.listdir(OUT)))
