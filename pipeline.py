"""Pipeline Tugas 2 Komputasi Multimedia: A, B, C.

Penanda ``# %%`` memisahkan empat sel notebook. Notebook memakai potongan kode
yang sama, sehingga tidak ada salinan logika yang perlu disinkronkan manual.
"""
# %% [1] Persiapan dan konfigurasi
from pathlib import Path
import shutil
import time
import struct
import os

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

if "__file__" in globals():
    ROOT = Path(__file__).resolve().parent
else:  # notebook dijalankan dari folder notebooks/
    ROOT = Path.cwd().resolve().parent if Path.cwd().name == "notebooks" else Path.cwd().resolve()
DATASET_FRAMES = ROOT / "dataset" / "DAiSEE" / "frames"
RESULTS = ROOT / "results"


def aktifkan_cairo():
    kandidat = []
    if os.environ.get("GTK_RUNTIME"):
        kandidat.append(Path(os.environ["GTK_RUNTIME"]))
    if os.environ.get("LOCALAPPDATA"):
        kandidat.append(Path(os.environ["LOCALAPPDATA"]) / "gtk3-runtime")
    kandidat.append(ROOT / ".tools" / "gtk3-runtime")
    for root in kandidat:
        for bin_dir in (root / "$_63_", root / "bin"):
            if (bin_dir / "libcairo-2.dll").exists():
                if hasattr(os, "add_dll_directory"):
                    os.add_dll_directory(str(bin_dir))
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]
                fonts = root / "etc" / "fonts"
                if fonts.exists():
                    os.environ.setdefault("FONTCONFIG_PATH", str(fonts))
                return


aktifkan_cairo()
try:
    import cairosvg
except (ImportError, OSError):
    cairosvg = None
    print("CairoSVG tidak dapat dimuat: paket atau libcairo-2.dll tidak ditemukan.")


A_ORIGINAL = RESULTS / "A_Augmentation" / "original"
A_TECHS = ["horizontal_flip", "rotation", "crop_resize", "brightness_contrast", "gaussian_noise", "gaussian_blur"]
for t in A_TECHS:
    (RESULTS / "A_Augmentation" / t).mkdir(parents=True, exist_ok=True)
A_ORIGINAL.mkdir(parents=True, exist_ok=True)

COMPRESSION_INPUT = ROOT / "data" / "compression_input"
COMPRESSION_INPUT.mkdir(parents=True, exist_ok=True)
COMPRESSED = RESULTS / "B_Compression" / "compressed"
COMPARISON = RESULTS / "B_Compression" / "comparison"
GRAPHS = RESULTS / "B_Compression" / "graphs"
for d in (COMPRESSED, COMPARISON, GRAPHS):
    d.mkdir(parents=True, exist_ok=True)

WM = RESULTS / "C_Watermarking"
for d in ("visible", "invisible", "extracted", "robustness_test"):
    (WM / d).mkdir(parents=True, exist_ok=True)
for path in (WM / "robustness_test").iterdir():
    if path.is_file():
        path.unlink()

# %% [2] Augmentasi data
for folder in [A_ORIGINAL, *(RESULTS / "A_Augmentation" / t for t in A_TECHS)]:
    for path in folder.iterdir():
        if path.is_file():
            path.unlink()

daftar_gambar = sorted(DATASET_FRAMES.glob("gambar_*.png"))
if len(daftar_gambar) != 10:
    raise ValueError(
        f"Frame DAiSEE ditemukan {len(daftar_gambar)}. Jalankan prepare_daisee.py."
    )

for gambar in daftar_gambar:
    shutil.copy2(gambar, A_ORIGINAL / gambar.name)

print("Jumlah frame DAiSEE ditemukan:", len(daftar_gambar))

def baca_gambar(path):
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Gagal membaca {path}")
    return img

def simpan_gambar(path, img):
    cv2.imwrite(str(path), img)


def siapkan_256(path):
    img = baca_gambar(path)
    h, w = img.shape[:2]
    sisi = min(h, w)
    y0 = (h - sisi) // 2
    x0 = (w - sisi) // 2
    persegi = img[y0:y0 + sisi, x0:x0 + sisi]
    return cv2.resize(persegi, (256, 256), interpolation=cv2.INTER_AREA)


def hitung_psnr(asli, rekonstruksi):
    if np.array_equal(asli, rekonstruksi):
        return float("inf")
    return peak_signal_noise_ratio(asli, rekonstruksi, data_range=255)


rng = np.random.default_rng(42)
for nomor in range(1, 11):
    kandidat = list(A_ORIGINAL.glob(f"gambar_{nomor:02d}_*"))
    if not kandidat:
        continue
    src = kandidat[0]
    img = baca_gambar(src)
    h, w = img.shape[:2]

    hf = cv2.flip(img, 1)
    simpan_gambar(RESULTS / "A_Augmentation" / "horizontal_flip" / src.name, hf)

    M = cv2.getRotationMatrix2D((w / 2, h / 2), 10, 1.0)
    rot = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    simpan_gambar(RESULTS / "A_Augmentation" / "rotation" / src.name, rot)

    crop_h = int(h * 0.8)
    crop_w = int(w * 0.8)
    y0 = (h - crop_h) // 2
    x0 = (w - crop_w) // 2
    crop = img[y0:y0 + crop_h, x0:x0 + crop_w]
    crop_resized = cv2.resize(crop, (w, h), interpolation=cv2.INTER_LINEAR)
    simpan_gambar(RESULTS / "A_Augmentation" / "crop_resize" / src.name, crop_resized)

    bc = cv2.convertScaleAbs(img, alpha=1.2, beta=15)
    simpan_gambar(RESULTS / "A_Augmentation" / "brightness_contrast" / src.name, bc)

    noise = rng.normal(0, 10, img.shape).astype(np.float32)
    noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    simpan_gambar(RESULTS / "A_Augmentation" / "gaussian_noise" / src.name, noisy)

    blur = cv2.GaussianBlur(img, (3, 3), 1.0)
    simpan_gambar(RESULTS / "A_Augmentation" / "gaussian_blur" / src.name, blur)

print("Augmentasi selesai.")

sample = sorted(A_ORIGINAL.glob("gambar_01_*"))[0]
img0 = baca_gambar(sample)
noise_sample = baca_gambar(RESULTS / "A_Augmentation" / "gaussian_noise" / sample.name)
vars_ = {
    "Asli": img0,
    "Horizontal flip": cv2.flip(img0, 1),
    "Rotasi 10 derajat": cv2.warpAffine(img0, cv2.getRotationMatrix2D((img0.shape[1]/2, img0.shape[0]/2), 10, 1.0), (img0.shape[1], img0.shape[0]), borderMode=cv2.BORDER_REFLECT),
    "Crop 80% + resize": cv2.resize(img0[int(img0.shape[0]*0.1):int(img0.shape[0]*0.9), int(img0.shape[1]*0.1):int(img0.shape[1]*0.9)], (img0.shape[1], img0.shape[0])),
    "Brightness/contrast": cv2.convertScaleAbs(img0, alpha=1.2, beta=15),
    "Gaussian noise": noise_sample,
    "Gaussian blur": cv2.GaussianBlur(img0, (3, 3), 1.0),
}
fig, axes = plt.subplots(2, 4, figsize=(10, 6))
for ax, (title, im) in zip(axes.flat, vars_.items()):
    ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    ax.set_title(title, fontsize=9)
    ax.axis("off")
for ax in axes.flat[len(vars_):]:
    ax.set_facecolor("#f4f6f9")
    ax.text(
        0.07,
        0.82,
        "Parameter augmentasi\n\n"
        "Flip: horizontal\n"
        "Rotasi: 10 derajat, border reflect\n"
        "Crop: 80 persen area tengah\n"
        "Brightness: alpha 1.2, beta 15\n"
        "Noise: sigma 10\n"
        "Blur: kernel 3 x 3, sigma 1.0",
        va="top",
        ha="left",
        fontsize=9.5,
        linespacing=1.55,
        color="#1f2d3d",
        transform=ax.transAxes,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#c9d1da")
plt.tight_layout()
plt.savefig(RESULTS / "A_Augmentation" / "comparison_grid.png", dpi=150)
plt.close(fig)
print("Grid augmentasi disimpan.")

# %% [3] Kompresi citra
base_img_path = sorted(A_ORIGINAL.glob("gambar_01_*"))[0]
base_256 = siapkan_256(base_img_path)

cv2.imwrite(str(COMPRESSION_INPUT / "input.bmp"), base_256)
cv2.imwrite(str(COMPRESSION_INPUT / "input.png"), base_256)
cv2.imwrite(str(COMPRESSION_INPUT / "input.jpg"), base_256, [cv2.IMWRITE_JPEG_QUALITY, 95])

svg_text = '''<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="#f2f2f2"/>
  <circle cx="128" cy="128" r="90" fill="#8ecae6" stroke="#023047" stroke-width="4"/>
  <circle cx="95" cy="105" r="12" fill="#023047"/>
  <circle cx="161" cy="105" r="12" fill="#023047"/>
  <path d="M 90 165 Q 128 195 166 165" stroke="#023047" stroke-width="6" fill="none"/>
  <rect x="20" y="20" width="60" height="30" fill="#ffb703" stroke="#023047" stroke-width="2"/>
</svg>'''
(COMPRESSION_INPUT / "input.svg").write_text(svg_text, encoding="utf-8")

svg_raster_png = COMPRESSION_INPUT / "input_svg_raster.png"
if cairosvg is None:
    if not svg_raster_png.exists():
        raise RuntimeError(
            "CairoSVG tidak tersedia dan raster SVG belum ada. Setel GTK_RUNTIME "
            "ke folder yang memuat libcairo-2.dll, lalu jalankan ulang pipeline."
        )
    print("Memakai raster SVG yang sudah ada:", svg_raster_png.name)
else:
    cairosvg.svg2png(
        bytestring=svg_text.encode("utf-8"),
        write_to=str(svg_raster_png),
        output_width=256,
        output_height=256,
    )
    with Image.open(svg_raster_png) as svg_png:
        svg_png.convert("RGB").save(svg_raster_png)

inputs = {
    "BMP": COMPRESSION_INPUT / "input.bmp",
    "PNG": COMPRESSION_INPUT / "input.png",
    "JPEG": COMPRESSION_INPUT / "input.jpg",
    "SVG_raster": COMPRESSION_INPUT / "input_svg_raster.png",
}

def rle_encode(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        j = i
        while j < n and data[j] == data[i] and (j - i) < 255:
            j += 1
        run = j - i
        out.append(run)
        out.append(data[i])
        i = j
    return bytes(out)

def rle_decode(data: bytes, expected_len: int) -> bytes:
    if len(data) % 2 != 0:
        raise ValueError("Data RLE tidak valid: panjang byte ganjil.")
    out = bytearray()
    i = 0
    n = len(data)
    while i < n and len(out) < expected_len:
        if i + 1 >= n:
            raise ValueError("Data RLE terpotong: pasangan run/value tidak lengkap.")
        run = data[i]
        val = data[i + 1]
        if run == 0:
            raise ValueError("Data RLE tidak valid: run length 0.")
        out.extend([val] * run)
        i += 2
    if len(out) != expected_len:
        raise ValueError(f"Hasil dekompresi RLE tidak sesuai: {len(out)} != {expected_len}")
    return bytes(out[:expected_len])

def huffman_build(freqs):
    import heapq
    counter = 0
    h = []
    for sym, f in freqs.items():
        heapq.heappush(h, (f, counter, (sym, None, None)))
        counter += 1
    if len(h) == 1:
        f, c, node = heapq.heappop(h)
        return {node[0]: "0"}
    while len(h) > 1:
        f1, c1, n1 = heapq.heappop(h)
        f2, c2, n2 = heapq.heappop(h)
        heapq.heappush(h, (f1 + f2, counter, (None, n1, n2)))
        counter += 1
    codes = {}
    def traverse(node, prefix):
        sym, left, right = node
        if left is None and right is None:
            codes[sym] = prefix if prefix != "" else "0"
            return
        if left is not None:
            traverse(left, prefix + "0")
        if right is not None:
            traverse(right, prefix + "1")
    root = h[0][2]
    traverse(root, "")
    return codes

def huffman_encode(data: bytes):
    freqs = {}
    for b in data:
        freqs[b] = freqs.get(b, 0) + 1
    codes = huffman_build(freqs)
    bitstr = "".join(codes[b] for b in data)
    pad = (8 - len(bitstr) % 8) % 8
    bitstr += "0" * pad
    out = bytearray()
    for i in range(0, len(bitstr), 8):
        out.append(int(bitstr[i:i+8], 2))
    return bytes(out), codes, pad, freqs

def huffman_decode(encoded: bytes, codes, pad, expected_len: int) -> bytes:
    rev = {v: k for k, v in codes.items()}
    bitstr = "".join(f"{byte:08b}" for byte in encoded)
    if pad:
        bitstr = bitstr[:-pad]
    out = bytearray()
    cur = ""
    for ch in bitstr:
        cur += ch
        if cur in rev:
            out.append(rev[cur])
            cur = ""
            if len(out) >= expected_len:
                break
    if len(out) != expected_len:
        raise ValueError(f"Hasil dekompresi Huffman tidak sesuai: {len(out)} != {expected_len}")
    return bytes(out)

rows = []
for fmt, path in inputs.items():
    original_size = os.path.getsize(path)
    img = cv2.imread(str(path))
    if img is None:
        pil = Image.open(path).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    h, w, c = img.shape
    raw = img.flatten().tobytes()
    expected_len = len(raw)

    t0 = time.perf_counter()
    enc = rle_encode(raw)
    t_enc = time.perf_counter() - t0
    out_path = COMPRESSED / f"{fmt}_rle.bin"
    with open(out_path, "wb") as f:
        f.write(struct.pack("<4I", h, w, c, expected_len))
        f.write(enc)
    comp_size = os.path.getsize(out_path)
    with open(out_path, "rb") as f:
        hh, ww, cc, elen = struct.unpack("<4I", f.read(16))
        enc2 = f.read()
    t0 = time.perf_counter()
    dec = rle_decode(enc2, elen)
    t_dec = time.perf_counter() - t0
    rec = np.frombuffer(dec, dtype=np.uint8).reshape(h, w, c)
    if rec.shape != img.shape:
        raise ValueError("Dimensi gambar hasil decoding RLE tidak sesuai")
    psnr = hitung_psnr(img, rec)
    ssim = structural_similarity(img, rec, channel_axis=2, data_range=255)
    baseline_size = expected_len
    rows.append({
        "Format": fmt, "Metode": "RLE",
        "Ukuran berkas input (bytes)": original_size,
        "Ukuran baseline (bytes)": baseline_size,
        "Ukuran output (bytes)": comp_size,
        "Perbandingan input:output": f"{original_size}:{comp_size}",
        "Rasio berkas input:output": round(original_size / comp_size, 3),
        "Compression ratio": round(baseline_size / comp_size, 3),
        "Space saving (%)": round((1 - comp_size / original_size) * 100, 2),
        "Space saving baseline (%)": round((1 - comp_size / baseline_size) * 100, 2),
        "PSNR": round(float(psnr), 3),
        "SSIM": round(float(ssim), 4),
        "Waktu kompresi (s)": round(t_enc, 5),
        "Waktu dekompresi (s)": round(t_dec, 5),
    })

    t0 = time.perf_counter()
    enc, codes, pad, freqs = huffman_encode(raw)
    t_enc = time.perf_counter() - t0
    out_path = COMPRESSED / f"{fmt}_huffman.bin"
    import pickle
    with open(out_path, "wb") as f:
        pickle.dump({"h": h, "w": w, "c": c, "elen": expected_len, "pad": pad, "codes": codes, "data": enc}, f)
    comp_size = os.path.getsize(out_path)
    with open(out_path, "rb") as f:
        obj = pickle.load(f)
    t0 = time.perf_counter()
    dec = huffman_decode(obj["data"], obj["codes"], obj["pad"], obj["elen"])
    t_dec = time.perf_counter() - t0
    rec = np.frombuffer(dec, dtype=np.uint8).reshape(h, w, c)
    if rec.shape != img.shape:
        raise ValueError("Dimensi gambar hasil decoding Huffman tidak sesuai")
    psnr = hitung_psnr(img, rec)
    ssim = structural_similarity(img, rec, channel_axis=2, data_range=255)
    baseline_size = expected_len
    rows.append({
        "Format": fmt, "Metode": "Huffman",
        "Ukuran berkas input (bytes)": original_size,
        "Ukuran baseline (bytes)": baseline_size,
        "Ukuran output (bytes)": comp_size,
        "Perbandingan input:output": f"{original_size}:{comp_size}",
        "Rasio berkas input:output": round(original_size / comp_size, 3),
        "Compression ratio": round(baseline_size / comp_size, 3),
        "Space saving (%)": round((1 - comp_size / original_size) * 100, 2),
        "Space saving baseline (%)": round((1 - comp_size / baseline_size) * 100, 2),
        "PSNR": round(float(psnr), 3),
        "SSIM": round(float(ssim), 4),
        "Waktu kompresi (s)": round(t_enc, 5),
        "Waktu dekompresi (s)": round(t_dec, 5),
    })

    t0 = time.perf_counter()
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    t_enc = time.perf_counter() - t0
    if not ok:
        raise ValueError("Encoding JPEG gagal")
    out_path = COMPRESSED / f"{fmt}_jpeg.jpg"
    buf.tofile(str(out_path))
    comp_size = os.path.getsize(out_path)
    encoded_bytes = np.fromfile(str(out_path), dtype=np.uint8)
    t0 = time.perf_counter()
    rec = cv2.imdecode(encoded_bytes, cv2.IMREAD_COLOR)
    t_dec = time.perf_counter() - t0
    if rec is None or rec.shape != img.shape:
        raise ValueError("Dimensi gambar hasil decoding JPEG tidak sesuai")
    psnr = hitung_psnr(img, rec)
    ssim = structural_similarity(img, rec, channel_axis=2, data_range=255)
    baseline_size = original_size
    rows.append({
        "Format": fmt, "Metode": "JPEG/DCT",
        "Ukuran berkas input (bytes)": original_size,
        "Ukuran baseline (bytes)": baseline_size,
        "Ukuran output (bytes)": comp_size,
        "Perbandingan input:output": f"{original_size}:{comp_size}",
        "Rasio berkas input:output": round(original_size / comp_size, 3),
        "Compression ratio": round(baseline_size / comp_size, 3),
        "Space saving (%)": round((1 - comp_size / original_size) * 100, 2),
        "Space saving baseline (%)": round((1 - comp_size / baseline_size) * 100, 2),
        "PSNR": round(float(psnr), 3),
        "SSIM": round(float(ssim), 4),
        "Waktu kompresi (s)": round(t_enc, 5),
        "Waktu dekompresi (s)": round(t_dec, 5),
    })

    if fmt == "BMP":
        fig, axes = plt.subplots(1, 2, figsize=(7, 3.5))
        axes[0].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        axes[0].set_title("Asli")
        axes[1].imshow(cv2.cvtColor(rec, cv2.COLOR_BGR2RGB))
        axes[1].set_title("JPEG quality 85")
        for ax in axes:
            ax.axis("off")
        plt.tight_layout()
        plt.savefig(COMPARISON / "visual_comparison.png", dpi=150)
        plt.close(fig)

df = pd.DataFrame(rows)
df.to_csv(RESULTS / "B_Compression" / "compression_results.csv", index=False)
print(df.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5))
pivot = df.pivot(index="Format", columns="Metode", values="Compression ratio")
pivot.plot(kind="bar", ax=ax)
ax.set_ylabel("Rasio kompresi (baseline / output)")
ax.set_xlabel("Format")
ax.set_title("Perbandingan rasio kompresi terhadap baseline")
ax.tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.savefig(GRAPHS / "compression_ratio.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 5))
pivot2 = df.pivot(index="Format", columns="Metode", values="Space saving (%)")
pivot2.plot(kind="bar", ax=ax)
ax.set_ylabel("Penghematan ruang (%)")
ax.set_xlabel("Format")
ax.set_title("Perbandingan penghematan ruang")
ax.tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.savefig(GRAPHS / "space_saving.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 5))
pivot3 = df.pivot(index="Format", columns="Metode", values="Rasio berkas input:output")
pivot3.plot(kind="bar", ax=ax)
ax.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="Batas impas (1x)")
ax.set_ylabel("Rasio ukuran berkas input : output")
ax.set_xlabel("Format")
ax.set_title("Perbandingan rasio terhadap ukuran berkas input")
ax.tick_params(axis="x", rotation=0)
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(GRAPHS / "file_ratio.png", dpi=150)
plt.close(fig)

# %% [4] Watermarking
wm_base_path = sorted(A_ORIGINAL.glob("gambar_01_*"))[0]
wm_base = siapkan_256(wm_base_path)

visible = wm_base.copy()
overlay = visible.copy()
cv2.putText(overlay, "TUGAS 2 KOMUL", (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
visible = cv2.addWeighted(overlay, 0.6, visible, 0.4, 0)
cv2.imwrite(str(WM / "visible" / "visible_watermark.png"), visible)

wm_img = Image.new("L", (64, 64), 0)
d = ImageDraw.Draw(wm_img)
d.text((5, 5), "KOMUL", fill=255)
wm_bin = (np.array(wm_img) > 127).astype(np.uint8)
invisible = wm_base.copy()
blue = invisible[:, :, 0].copy()
flat_blue = blue.flatten()
wm_flat = wm_bin.flatten()
assert wm_flat.size <= flat_blue.size
for i in range(wm_flat.size):
    flat_blue[i] = (flat_blue[i] & 0xFE) | int(wm_flat[i])
invisible[:, :, 0] = flat_blue.reshape(blue.shape)
cv2.imwrite(str(WM / "invisible" / "invisible_watermark.png"), invisible)

extracted = np.zeros_like(wm_bin)
blue2 = cv2.imread(str(WM / "invisible" / "invisible_watermark.png"))[:, :, 0]
flat2 = blue2.flatten()
for i in range(wm_flat.size):
    extracted.flat[i] = flat2[i] & 1
extracted_img = (extracted * 255).astype(np.uint8)
Image.fromarray(extracted_img).save(WM / "extracted" / "extracted_watermark.png")

psnr_vis = hitung_psnr(wm_base, visible)
ssim_vis = structural_similarity(wm_base, visible, channel_axis=2, data_range=255)
psnr_inv = hitung_psnr(wm_base, invisible)
ssim_inv = structural_similarity(wm_base, invisible, channel_axis=2, data_range=255)

bit_acc = float(np.mean((extracted.flatten() == wm_flat))) * 100.0

SERANGAN = ("JPEG", "Resize", "Crop")
EKSTENSI = {"JPEG": ".jpg", "Resize": ".png", "Crop": ".png"}


def terapkan_serangan(citra, serangan):
    """Terapkan satu operasi robustness dan kembalikan array hasilnya."""
    if serangan == "JPEG":
        ok, buf = cv2.imencode(".jpg", citra, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ok:
            raise ValueError("Encoding JPEG untuk uji robustness gagal")
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if serangan == "Resize":
        return cv2.resize(cv2.resize(citra, (128, 128)), (256, 256))
    h, w = citra.shape[:2]
    ch, cw = int(h * 0.8), int(w * 0.8)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    return cv2.resize(citra[y0:y0 + ch, x0:x0 + cw], (w, h))


def extract_bits(img):
    b = img[:, :, 0].flatten()
    out = np.zeros(wm_flat.size, dtype=np.uint8)
    for i in range(wm_flat.size):
        out[i] = b[i] & 1
    return out


attacks = {}
for serangan in SERANGAN:
    hasil = terapkan_serangan(invisible, serangan)
    cv2.imwrite(
        str(WM / "robustness_test" / f"invisible_{serangan.lower()}{EKSTENSI[serangan]}"),
        hasil,
    )
    bits = extract_bits(hasil)
    attacks[serangan] = float(np.mean(bits == wm_flat)) * 100.0
    Image.fromarray((bits.reshape(wm_bin.shape) * 255).astype(np.uint8)).save(
        WM / "robustness_test" / f"extracted_{serangan}.png"
    )

# Visible watermark diuji dengan operasi yang sama. Residualnya terhadap citra
# dasar (visible - base) dipakai sebagai pola acuan, lalu dihitung korelasi NCC
# dan IoU antara pola itu dan residual citra setelah serangan.
mark_residual = visible.astype(np.int16) - wm_base.astype(np.int16)
mark_mask = np.abs(mark_residual).max(axis=2) > 0
acuan_residual = mark_residual[:, :, 2].ravel().astype(np.float64)

robust_visible = []
hasil_visible = {}
for serangan in SERANGAN:
    hasil = terapkan_serangan(visible, serangan)
    dasar = terapkan_serangan(wm_base, serangan)
    sisa = hasil.astype(np.int16) - dasar.astype(np.int16)
    ncc = float(np.corrcoef(acuan_residual, sisa[:, :, 2].ravel().astype(np.float64))[0, 1])
    kuat = np.abs(sisa).max(axis=2) > 3
    gabung = int((kuat | mark_mask).sum())
    iou = float((kuat & mark_mask).sum() / gabung) if gabung else 0.0
    hasil_visible[serangan] = hasil
    cv2.imwrite(
        str(WM / "robustness_test" / f"visible_{serangan.lower()}{EKSTENSI[serangan]}"),
        hasil,
    )
    robust_visible.append({"Serangan": serangan, "NCC": round(ncc, 4), "IoU": round(iou, 4)})

robust_visible_df = pd.DataFrame(robust_visible)
robust_visible_df.to_csv(WM / "robustness_visible.csv", index=False)
print(robust_visible_df.to_string(index=False))

wm_summary = pd.DataFrame([
    {"Teknik": "Visible", "PSNR": round(float(psnr_vis), 3), "SSIM": round(float(ssim_vis), 4)},
    {"Teknik": "Invisible (LSB)", "PSNR": round(float(psnr_inv), 3), "SSIM": round(float(ssim_inv), 4)},
])
wm_summary.to_csv(WM / "watermark_metrics.csv", index=False)
pd.DataFrame([{"Teknik": "Invisible (LSB)", "Bit accuracy (%)": round(bit_acc, 2)}]).to_csv(WM / "watermark_extraction.csv", index=False)

robust_df = pd.DataFrame([{"Serangan": k, "Bit accuracy (%)": round(v, 2)} for k, v in attacks.items()])
robust_df.to_csv(WM / "robustness_results.csv", index=False)
print("Bit accuracy ekstraksi awal:", round(bit_acc, 2))
print(robust_df.to_string(index=False))

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(robust_df["Serangan"], robust_df["Bit accuracy (%)"], color=["#4C72B0", "#DD8452", "#55A868"])
ax.axhline(50, color="gray", linestyle="--", linewidth=1, label="Tebakan acak (50%)")
ax.set_ylim(0, 100)
ax.set_ylabel("Bit accuracy (%)")
ax.set_title("Bit accuracy setelah serangan")
ax.legend()
plt.tight_layout()
plt.savefig(WM / "robustness_chart.png", dpi=150)
plt.close(fig)

fig, axes = plt.subplots(1, 4, figsize=(12, 3.2))
panel = [("Visible", visible)] + [(f"Visible + {s}", hasil_visible[s]) for s in SERANGAN]
for ax, (judul, im) in zip(axes, panel):
    ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
    ax.set_title(judul, fontsize=9)
    ax.axis("off")
plt.tight_layout()
plt.savefig(WM / "robustness_visible_grid.png", dpi=150)
plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(9, 3))
axes[0].imshow(cv2.cvtColor(wm_base, cv2.COLOR_BGR2RGB)); axes[0].set_title("Asli")
axes[1].imshow(cv2.cvtColor(visible, cv2.COLOR_BGR2RGB)); axes[1].set_title("Visible")
axes[2].imshow(cv2.cvtColor(invisible, cv2.COLOR_BGR2RGB)); axes[2].set_title("Invisible")
for ax in axes: ax.axis("off")
plt.tight_layout()
plt.savefig(WM / "comparison_before_after.png", dpi=150)
plt.close(fig)

print("PIPELINE SELESAI")
