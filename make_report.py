"""Membangun laporan PDF dari hasil eksperimen di folder results."""
from pathlib import Path
import math

import pandas as pd
from PIL import Image
from fpdf import FPDF
from fpdf.fonts import FontFace

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
COMP = RESULTS / "B_Compression"
WM = RESULTS / "C_Watermarking"

PAGE_W = 210
MARGIN_L = 20
MARGIN_R = 20
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R
BOTTOM = 276

comp = pd.read_csv(COMP / "compression_results.csv")
wm_metrics = pd.read_csv(WM / "watermark_metrics.csv")
wm_extract = pd.read_csv(WM / "watermark_extraction.csv")
robust = pd.read_csv(WM / "robustness_results.csv")
robust_visible = pd.read_csv(WM / "robustness_visible.csv")
manifest = pd.read_csv(ROOT / "dataset" / "DAiSEE" / "selected_clips.csv")


def row(fmt, metode):
    data = comp[(comp["Format"] == fmt) & (comp["Metode"] == metode)]
    if data.empty:
        raise ValueError(f"Data tidak ditemukan: {fmt} {metode}")
    return data.iloc[0]


bmp_rle = row("BMP", "RLE")
bmp_huf = row("BMP", "Huffman")
bmp_jpg = row("BMP", "JPEG/DCT")
png_jpg = row("PNG", "JPEG/DCT")
png_rle = row("PNG", "RLE")
png_huf = row("PNG", "Huffman")
jpg_jpg = row("JPEG", "JPEG/DCT")
svg_rle = row("SVG_raster", "RLE")
svg_huf = row("SVG_raster", "Huffman")
svg_jpg = row("SVG_raster", "JPEG/DCT")
wm_visible = wm_metrics[wm_metrics["Teknik"] == "Visible"].iloc[0]
wm_lsb = wm_metrics[wm_metrics["Teknik"] == "Invisible (LSB)"].iloc[0]
rob = {r["Serangan"]: r["Bit accuracy (%)"] for _, r in robust.iterrows()}
robv = {r["Serangan"]: r for _, r in robust_visible.iterrows()}



def angka(value, digit=2):
    return f"{float(value):.{digit}f}"


def psnr_text(value):
    if math.isinf(float(value)):
        return "tak hingga"
    return angka(value, 3)


def ukuran(value):
    return f"{int(value)}"


class Laporan(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "", 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 6, "Tugas 2 Komputasi Multimedia", align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(205, 205, 205)
        self.set_line_width(0.3)
        self.line(MARGIN_L, self.get_y(), PAGE_W - MARGIN_R, self.get_y())
        self.ln(4)
        self.set_text_color(20, 20, 20)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, f"Halaman {self.page_no()} dari {{nb}}", align="C")


pdf = Laporan(orientation="P", unit="mm", format="A4")
pdf.set_margins(MARGIN_L, 20, MARGIN_R)
pdf.set_auto_page_break(auto=True, margin=18)
pdf.set_title("Transformasi Gambar, Kompresi Citra, dan Watermarking")
pdf.set_author("Tugas 2 Komputasi Multimedia")
pdf.set_subject("Laporan augmentasi, kompresi, dan watermarking pada subset DAiSEE")
pdf.set_creator("make_report.py")
pdf.alias_nb_pages()


def pastikan_ruang(tinggi):
    if pdf.get_y() + tinggi > BOTTOM:
        pdf.add_page()


def judul1(text):
    pastikan_ruang(24)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(25, 40, 65)
    pdf.multi_cell(0, 7, text, align="L")
    pdf.set_draw_color(25, 40, 65)
    pdf.set_line_width(0.6)
    y = pdf.get_y() + 1
    pdf.line(MARGIN_L, y, MARGIN_L + 45, y)
    pdf.ln(4)
    pdf.set_text_color(20, 20, 20)


def judul2(text):
    pastikan_ruang(18)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(25, 40, 65)
    pdf.multi_cell(0, 6, text, align="L")
    pdf.ln(1.5)
    pdf.set_text_color(20, 20, 20)


def paragraf(text, size=10.5):
    pdf.set_font("Times", "", size)
    pdf.multi_cell(0, 5.5, text, align="J")
    pdf.ln(1.5)


def butir(text, size=10.5):
    pdf.set_font("Times", "", size)
    pdf.set_x(MARGIN_L + 4)
    pdf.multi_cell(CONTENT_W - 4, 5.3, "- " + text, align="J")
    pdf.ln(0.8)


def tabel(headers, rows, widths, size=8, align="CENTER", tinggi_baris=4.8, padding=1.2):
    pdf.set_font("Helvetica", "", size)
    pdf.set_draw_color(160, 160, 160)
    pdf.set_line_width(0.2)
    with pdf.table(
        col_widths=widths,
        width=sum(widths),
        first_row_as_headings=True,
        text_align=align,
        line_height=tinggi_baris,
        padding=padding,
        headings_style=FontFace(emphasis="BOLD", size_pt=size, fill_color=(226, 232, 240)),
        repeat_headings=1,
    ) as table:
        head = table.row()
        for h in headers:
            head.cell(h, align="CENTER")
        for data in rows:
            baris = table.row()
            for value in data:
                baris.cell(str(value), align=align)


def caption(text):
    pdf.ln(1)
    pdf.set_font("Times", "I", 8.5)
    pdf.set_text_color(70, 70, 70)
    pdf.multi_cell(0, 4.4, text, align="L")
    pdf.set_text_color(20, 20, 20)
    pdf.ln(3)


def gambar(path, width, text):
    with Image.open(path) as img:
        w, h = img.size
    tinggi = width * h / w
    pastikan_ruang(tinggi + 12)
    x = (PAGE_W - width) / 2
    pdf.image(str(path), x=x, w=width)
    caption(text)


# Sampul
pdf.add_page()
pdf.set_y(42)
pdf.set_font("Helvetica", "B", 10)
pdf.set_text_color(90, 90, 90)
pdf.cell(0, 7, "TUGAS 2 KOMPUTASI MULTIMEDIA", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)
pdf.set_font("Helvetica", "B", 25)
pdf.set_text_color(25, 40, 65)
pdf.multi_cell(0, 11, "Transformasi Gambar, Kompresi Citra, dan Watermarking", align="C")
pdf.ln(3)
pdf.set_draw_color(25, 40, 65)
pdf.set_line_width(0.9)
pdf.line(65, pdf.get_y(), 145, pdf.get_y())
pdf.ln(8)
pdf.set_font("Times", "", 12)
pdf.set_text_color(50, 50, 50)
pdf.multi_cell(0, 6.2, "Laporan eksperimen augmentasi data, kompresi citra, dan watermarking pada subset DAiSEE", align="C")
pdf.ln(12)

pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(25, 40, 65)
pdf.cell(0, 5, "INFORMASI LAPORAN", align="L", new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)
info = [
    ("Nama / NIM", "________________ / ________________"),
    ("Dataset uji", "DAiSEE, subset 10 klip latih, 4 label afektif"),
    ("Populasi DAiSEE", "9.068 klip video, 112 pengguna"),
    ("Seed augmentasi", "42, stratified per label"),
    ("Citra uji kompresi", "256 x 256 RGB dari frame DAiSEE"),
    ("Rasterisasi SVG", "CairoSVG 2.9.1"),
    ("Metode", "RLE, Huffman, JPEG/DCT, visible watermark, invisible LSB"),
    ("Penggunaan AI", "Command Code: bantu koding, outline, README, referensi"),
    ("Sumber angka", "results/B_Compression dan results/C_Watermarking"),
]
pdf.set_font("Helvetica", "", 8.5)
pdf.set_draw_color(190, 190, 190)
for label, value in info:
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(38, 6, label, border="B", fill=True)
    pdf.set_font("Times", "", 9.5)
    pdf.cell(CONTENT_W - 38, 6, value, border="B", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)

pdf.ln(10)
pdf.set_fill_color(232, 238, 246)
pdf.set_draw_color(25, 40, 65)
pdf.set_line_width(0.4)
pdf.set_font("Helvetica", "B", 9)
pdf.set_text_color(25, 40, 65)
pdf.cell(CONTENT_W, 7, "HASIL UTAMA", border="LTR", fill=True, align="L", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Times", "", 9.5)
pdf.set_text_color(20, 20, 20)
pdf.multi_cell(
    CONTENT_W,
    5.2,
    f"JPEG/DCT pada input BMP memberi rasio {angka(bmp_jpg['Compression ratio'], 3)} dan penghematan "
    f"{angka(bmp_jpg['Space saving (%)'], 2)} persen.\n"
    f"RLE pada frame DAiSEE justru memperbesar berkas: rasio {angka(bmp_rle['Compression ratio'], 3)}.\n"
    f"Invisible LSB memberi PSNR {angka(wm_lsb['PSNR'], 3)} dB dan SSIM {angka(wm_lsb['SSIM'], 4)}.\n"
    f"Bit accuracy LSB setelah serangan: JPEG {angka(rob['JPEG'], 2)} persen, resize {angka(rob['Resize'], 2)} "
    f"persen, crop {angka(rob['Crop'], 2)} persen.",
    border="LRB",
    fill=True,
    align="L",
)
pdf.ln(10)
pdf.set_font("Times", "I", 9)
pdf.set_text_color(80, 80, 80)
pdf.multi_cell(0, 4.6, "Seluruh angka dihitung dari hasil eksekusi pipeline. Tidak ada nilai yang diisi manual.", align="C")

# Ringkasan dan pendahuluan
pdf.add_page()
judul1("Ringkasan")
paragraf(
    "Laporan ini menguji tiga kelompok transformasi citra digital pada subset DAiSEE: augmentasi data, kompresi citra, "
    "dan watermarking. Subset berisi 10 klip dari 10 subjek berbeda, dipilih dengan seed 42 dan komposisi 3 Boredom, "
    "3 Engagement, 2 Confusion, dan 2 Frustration. Kompresi diuji dengan RLE, Huffman, dan JPEG/DCT pada input BMP, "
    "PNG, JPEG, dan SVG yang dirasterisasi dengan CairoSVG. Watermarking diuji dengan visible watermark dan invisible "
    "LSB, lalu dievaluasi dengan PSNR, SSIM, ekstraksi pola, dan tiga operasi robustness."
)
paragraf(
    f"RLE dan Huffman bersifat lossless. Pada frame DAiSEE, RLE tidak memberi penghematan: rasio "
    f"{angka(bmp_rle['Compression ratio'], 3)} dan space saving {angka(bmp_rle['Space saving (%)'], 2)} persen. "
    f"Huffman hanya memberi rasio {angka(bmp_huf['Compression ratio'], 3)}. JPEG/DCT memberi rasio "
    f"{angka(bmp_jpg['Compression ratio'], 3)} dengan penghematan {angka(bmp_jpg['Space saving (%)'], 2)} persen, "
    f"tetapi menurunkan kualitas ke PSNR {angka(bmp_jpg['PSNR'], 3)} dB dan SSIM {angka(bmp_jpg['SSIM'], 4)}. "
    f"LSB memberi imperceptibility tinggi dengan PSNR {angka(wm_lsb['PSNR'], 3)} dB dan SSIM "
    f"{angka(wm_lsb['SSIM'], 4)}, tetapi bit accuracy turun menjadi {angka(rob['JPEG'], 2)} persen setelah JPEG, "
    f"{angka(rob['Resize'], 2)} persen setelah resize, dan {angka(rob['Crop'], 2)} persen setelah crop. Hasil ini "
    "menunjukkan pertukaran antara imperceptibility dan ketahanan watermark."
)
judul1("1. Pendahuluan")
paragraf(
    "Transformasi citra dipakai untuk memperluas variasi data, mengurangi ukuran penyimpanan, dan menyisipkan informasi "
    "kepemilikan. Ketiga tujuan tersebut memiliki metrik yang berbeda. Augmentasi dinilai dari kesesuaian transformasi "
    "dengan objek, kompresi dinilai dari rasio dan kualitas, sedangkan watermarking dinilai dari imperceptibility dan "
    "ketahanan terhadap operasi pengolahan citra."
)
paragraf(
    "DAiSEE dirancang untuk pengenalan tingkat keterlibatan pengguna [1]. Dataset ini berisi 9.068 klip video dari 112 "
    "pengguna dengan empat label afektif, yaitu Boredom, Engagement, Confusion, dan Frustration. Eksperimen ini memakai "
    "subset 10 klip dari split Train, bukan seluruh koleksi. Satu frame tengah diambil dari setiap klip, sehingga "
    "augmentasi bekerja pada citra 640 x 480 yang masih memuat wajah, latar, dan variasi pencahayaan alami."
)
paragraf(
    "Teori dasar pengolahan citra, transformasi geometri, resampling, filtering, dan persepsi warna mengikuti literatur "
    "pengolahan citra yang lazim dipakai. Perubahan brightness, contrast, dan noise dinilai dari persepsi visual, "
    "sedangkan rotasi, crop, dan resampling dijelaskan melalui transformasi geometri dan interpolasi."
)
paragraf(
    "Cakupan laporan meliputi pipeline yang dapat dijalankan ulang, perbandingan baseline yang eksplisit, evaluasi "
    "kualitas rekonstruksi, ekstraksi watermark, dan uji ketahanan. Rasterisasi SVG memakai CairoSVG [8], bukan "
    "gambar ulang manual. Keterbatasan ukuran subset, pemilihan frame, dan jumlah citra uji dicatat pada bagian akhir "
    "agar hasil tidak dibaca melebihi cakupan eksperimen."
)

# Metodologi
judul1("2. Metodologi")
judul2("2.1 Augmentasi data")
paragraf(
    "Sepuluh klip dipilih dari split Train DAiSEE dengan random.Random(42). Pemilihan dilakukan secara stratified agar "
    "empat label afektif terwakili: 3 Boredom, 3 Engagement, 2 Confusion, dan 2 Frustration. Setiap klip berasal dari "
    "subjek berbeda. Pemilihan acak dilakukan pada tingkat klip, bukan pada tingkat frame; posisi frame tengah "
    "ditetapkan agar hasil dapat direproduksi. Dengan demikian, seed 42 menentukan sepuluh gambar yang dipakai. Frame "
    "disimpan sebagai PNG 640 x 480. Enam transformasi "
    "diterapkan pada setiap frame. Rotasi memakai sudut 10 derajat dan border reflect. Crop mengambil 80 persen area "
    "tengah, lalu diperbesar kembali ke ukuran asli. Brightness/contrast memakai alpha 1.2 dan beta 15. Gaussian noise "
    "memakai standar deviasi 10. Gaussian blur memakai kernel 3 x 3 dan sigma 1.0."
)
paragraf(
    "Parameter dijaga ringan agar area mata dan mulut tidak hilang. Rotasi memakai matriks transformasi dua dimensi, "
    "crop dan resize memakai interpolasi, sedangkan Gaussian blur memakai konvolusi. Perubahan cahaya dan warna "
    "dinilai dari persepsi visual."
)
tabel(
    ["No", "Teknik", "Parameter", "Efek yang diharapkan", "Justifikasi untuk DAiSEE"],
    [
        [
            "1",
            "Horizontal flip",
            "Flip kode 1",
            "Variasi orientasi wajah",
            "Aman karena ekspresi wajah hampir simetris terhadap sumbu vertikal, sehingga AU mata dan mulut tetap "
            "terbaca; yang berubah hanya arah pose kepala [2]",
        ],
        [
            "2",
            "Rotasi",
            "10 derajat, border reflect",
            "Variasi sudut pandang",
            "Sudut kecil meniru variasi posisi duduk peserta di depan webcam; rotasi besar memotong sudut mata dan "
            "mulut yang menjadi penanda engagement",
        ],
        [
            "3",
            "Crop dan resize",
            "Crop tengah 80 persen, resize ke ukuran asli",
            "Variasi skala dan framing",
            "Meniru perbedaan jarak peserta ke kamera; crop agresif membuang konteks bahu dan gerak tubuh yang ikut "
            "menandai keterlibatan [1]",
        ],
        [
            "4",
            "Brightness/contrast",
            "Alpha 1.2, beta 15",
            "Variasi pencahayaan",
            "Meniru variasi pencahayaan ruangan belajar tanpa mengubah struktur wajah; kontras berlebih menutup "
            "detail bayangan di sekitar mata",
        ],
        [
            "5",
            "Gaussian noise",
            "Sigma 10",
            "Variasi noise sensor",
            "Meniru sensor webcam beresolusi rendah pada rekaman DAiSEE; noise berlebih menutupi tekstur halus yang "
            "dipakai menilai kebosanan",
        ],
        [
            "6",
            "Gaussian blur",
            "Kernel 3 x 3, sigma 1.0",
            "Variasi ketajaman",
            "Meniru fokus lembut dan kompresi video; blur kuat menghapus kerutan halus di sekitar mata yang menjadi "
            "isyarat engagement [2]",
        ],
    ],
    [8, 26, 34, 42, 60],
    size=7.6,
    align="LEFT",
    tinggi_baris=6.4,
)
caption(
    "Tabel 1. Parameter enam transformasi augmentasi beserta justifikasi kesesuaiannya untuk data DAiSEE."
)

judul2("2.2 Kompresi citra")
paragraf(
    "RLE menggabungkan byte berulang dengan panjang run maksimal 255 dan header 16 byte. Huffman memberi kode lebih "
    "pendek untuk byte yang sering muncul; ukuran output mencakup codebook, metadata, padding, dan overhead pickle. "
    "JPEG/DCT memakai encoder JPEG OpenCV dengan kualitas 85 dan transformasi DCT internal. RLE dan Huffman adalah "
    "implementasi algoritma sendiri, sedangkan JPEG/DCT memakai library. Dasar algoritma Huffman mengikuti Huffman [7], "
    "standar JPEG mengikuti Wallace [3], dan teori kompresi data mengikuti Mahoney [14]."
)
paragraf(
    "Baseline ukuran RLE dan Huffman adalah h x w x c byte piksel mentah. Baseline JPEG/DCT adalah ukuran berkas input. "
    "Perbedaan ini disengaja: RLE dan Huffman mengukur efisiensi encoding data mentah, sedangkan JPEG/DCT mengukur "
    "penghematan terhadap berkas awal. Karena itu, rasio RLE dan Huffman tidak dapat dibandingkan langsung dengan rasio "
    "JPEG/DCT. Perbandingan yang adil dilakukan dalam kelompok baseline yang sama."
)
paragraf(
    "Citra uji kompresi berasal dari frame pertama subset. Frame 640 x 480 dipotong persegi di tengah, lalu diperkecil "
    "ke 256 x 256 dengan interpolasi area agar rasio aspek tidak berubah. Citra SVG diperlakukan sebagai data vektor. "
    "SVG dirasterisasi dengan CairoSVG [8] menjadi PNG 256 x 256, lalu PNG hasil rasterisasi dipakai sebagai input "
    f"pembanding. Baris SVG_raster memakai berkas input_svg_raster.png berukuran "
    f"{ukuran(svg_jpg['Ukuran baseline (bytes)'])} byte, bukan berkas input.svg berukuran 523 byte."
)

judul2("2.3 Watermarking")
paragraf(
    "Visible watermark ditambahkan sebagai teks semi-transparan berwarna merah bertuliskan TUGAS 2 KOMUL pada bagian "
    "bawah citra. Invisible watermark disisipkan pada bit paling rendah kanal biru. Pola biner berukuran 64 x 64 berisi "
    "4.096 bit dan ditempatkan berurutan pada 4.096 piksel pertama kanal biru, yaitu 16 baris teratas citra. Ekstraksi "
    "membaca posisi yang sama, lalu membandingkan bit hasil ekstraksi dengan pola asli."
)
paragraf(
    "Imperceptibility diukur dengan PSNR dan SSIM antara citra asli dan citra ber-watermark. Ketahanan diuji dengan tiga "
    "operasi: kompresi JPEG kualitas 70, resize ke 128 x 128 lalu kembali ke 256 x 256, dan crop tengah 80 persen lalu "
    "resize. Setiap hasil serangan diekstrak dan dihitung bit accuracy-nya. Visible watermark diuji dengan operasi yang "
    "sama: residual visible dikurangi citra dasar menjadi pola acuan, operasi diterapkan pada kedua citra, lalu residual "
    "hasil serangan dibandingkan dengan pola acuan melalui korelasi NCC dan IoU. Dasar watermarking mengikuti Petitcolas "
    "et al. [15] dan teknik data hiding mengikuti Bender et al. [4]."
)

judul2("2.4 Metrik")
paragraf(
    "Rasio kompresi dihitung sebagai ukuran baseline dibagi ukuran output, dan rasio berkas dihitung sebagai ukuran "
    "berkas input dibagi ukuran output. Space saving mengikuti rumus tugas, yaitu (1 - ukuran output / ukuran berkas "
    "input) x 100 persen. Untuk perbandingan metode, CSV juga menyimpan space saving baseline yang memakai byte piksel "
    "mentah. PSNR dihitung sebagai 10 log10(255^2 / MSE). SSIM mengikuti Wang et al. [6]. Bit accuracy dihitung "
    "sebagai jumlah bit yang sama dibagi jumlah bit total, lalu dikali 100 persen. NCC adalah korelasi Pearson antara "
    "residual acuan dan residual hasil serangan; IoU adalah irisian piksel bertanda dibagi gabungannya dengan ambang 3 "
    "level. PSNR dan SSIM dihitung antara citra asli dan citra hasil decoding."
)
paragraf(
    "Waktu encoding dan decoding dicatat dengan time.perf_counter di sekitar proses kompresi dan dekompresi. Pembacaan "
    "berkas dan perhitungan metrik tidak termasuk dalam waktu tersebut. Pengukuran dilakukan satu kali pada mesin uji, "
    "sehingga angka waktu dipakai untuk perbandingan relatif, bukan sebagai benchmark perangkat keras."
)

# Hasil augmentasi
judul1("3. Hasil dan Pembahasan")
judul2("3.1 Augmentasi")
paragraf(
    "Gambar 1 memperlihatkan frame asli dan enam hasil augmentasi dari sampel pertama. Horizontal flip membalik wajah "
    "tanpa mengubah ekspresi dasar karena ekspresi dominan pada DAiSEE terbentuk dari konfigurasi mata dan mulut yang "
    "hampir simetris, bukan dari arah hadap wajah; Porcu et al. [2] memakai flip pada data ekspresi wajah dengan alasan "
    "yang sama, sedangkan pencerminan adalah transformasi isometrik yang tidak mengubah jarak antar titik. Rotasi 10 "
    "derajat masih mempertahankan area wajah karena sudut kecil hanya menggeser beberapa piksel di tepi; rotasi besar "
    "tidak dipakai karena memotong sudut mata dan mulut yang menjadi penanda engagement pada anotasi DAiSEE [1]. Crop 80 "
    "persen memperbesar wajah dan mengurangi konteks di tepi citra, sehingga variasi skala terbentuk tanpa menghilangkan "
    "wajah. Brightness/contrast membuat sebagian area terang dan gelap, meniru variasi pencahayaan ruangan yang lazim "
    "pada rekaman peserta e-learning [1]. Gaussian noise menambah variasi warna pada piksel seperti sensor webcam "
    "beresolusi rendah, dan Gaussian blur menurunkan ketajaman tepi seperti fokus lembut. Konvolusi menjadi dasar blur "
    "dan noise. Latar ruangan ikut berubah pada "
    "beberapa transformasi, sehingga augmentasi tidak hanya menguji wajah tetapi juga konteks di sekitarnya."
)
gambar(
    RESULTS / "A_Augmentation" / "comparison_grid.png",
    158,
    "Gambar 1. Frame DAiSEE asli dan enam hasil augmentasi dari sampel pertama. Panel terakhir merangkum parameter "
    "augmentasi. Sumber frame: DAiSEE, copyright Vineeth Balasubramanian.",
)
paragraf(
    "Secara kualitatif, keenam transformasi masih mempertahankan ekspresi pada sampel ini. Rotasi dan crop berpotensi "
    "menghilangkan informasi jika parameternya diperbesar. Noise dan blur berpotensi menghapus detail halus jika levelnya "
    "dinaikkan. Evaluasi augmentasi pada laporan ini bersifat kualitatif karena tidak ada model klasifikasi yang dilatih. "
    "Klaim akurasi model tidak dibuat tanpa pengukuran. Evaluasi kuantitatif augmentasi untuk pengenalan ekspresi wajah "
    "pernah dilakukan Porcu et al. [2], tetapi berada di luar cakupan tugas ini."
)

# Hasil kompresi
judul2("3.2 Kompresi")
paragraf(
    "Tabel 2 merangkum ukuran dan kualitas hasil kompresi untuk empat jenis input dan tiga metode. RLE dan Huffman "
    "menghasilkan rekonstruksi identik, sehingga PSNR bernilai tak hingga dan SSIM 1.0000. JPEG/DCT menghasilkan "
    f"rekonstruksi lossy dengan PSNR {angka(svg_jpg['PSNR'], 3)} sampai {angka(jpg_jpg['PSNR'], 3)} dB dan SSIM "
    f"{angka(bmp_jpg['SSIM'], 4)} sampai {angka(svg_jpg['SSIM'], 4)}."
)
rows = []
for _, r in comp.iterrows():
    rows.append(
        [
            r["Format"],
            r["Metode"],
            ukuran(r["Ukuran baseline (bytes)"]),
            ukuran(r["Ukuran output (bytes)"]),
            angka(r["Compression ratio"], 3),
            angka(r["Rasio berkas input:output"], 3),
            angka(r["Space saving (%)"], 2),
            psnr_text(r["PSNR"]),
            angka(r["SSIM"], 4),
        ]
    )
pastikan_ruang(38)
tabel(
    [
        "Format",
        "Metode",
        "Baseline (byte)",
        "Output (byte)",
        "Rasio baseline",
        "Rasio berkas",
        "Saving berkas (%)",
        "PSNR (dB)",
        "SSIM",
    ],
    rows,
    [19, 19, 22, 21, 17, 17, 23, 20, 12],
    size=7.2,
    align="CENTER",
    tinggi_baris=4.5,
)
caption(
    "Tabel 2. Ukuran baseline, ukuran output, kedua bentuk rasio, space saving, PSNR, dan SSIM. Rasio baseline = "
    "ukuran baseline / ukuran output; rasio berkas = ukuran berkas input / ukuran output sesuai rumus tugas. Saving "
    "berkas = (1 - ukuran output / ukuran berkas input) x 100 persen. Baseline RLE/Huffman adalah byte piksel mentah; "
    "baseline JPEG/DCT adalah ukuran berkas input. Space saving baseline tersedia pada CSV."
)
paragraf(
    f"Rumus tugas menetapkan rasio sebagai ukuran asli : ukuran terkompresi. Nilai itu ada pada kolom rasio berkas. "
    f"Pada input PNG, RLE memberi {angka(png_rle['Rasio berkas input:output'], 3)} dan Huffman "
    f"{angka(png_huf['Rasio berkas input:output'], 3)}, karena berkas "
    f"{ukuran(png_rle['Ukuran berkas input (bytes)'])} byte dibandingkan dengan output "
    f"{ukuran(png_rle['Ukuran output (bytes)'])} byte, yaitu pembesaran berkas. Kolom rasio baseline dipakai untuk "
    "membandingkan metode secara adil pada data piksel yang sama, sedangkan kolom rasio berkas menjawab pertanyaan "
    "berapa besar berkas awal menyusut. Keduanya disajikan agar tidak ada satu angka pun yang perlu ditebak pembaca."
)
paragraf(
    f"Pada input BMP, RLE memberi rasio {angka(bmp_rle['Compression ratio'], 3)} dan space saving "
    f"{angka(bmp_rle['Space saving (%)'], 2)} persen. Nilai negatif berarti output RLE lebih besar daripada berkas "
    f"input. Huffman memberi rasio {angka(bmp_huf['Compression ratio'], 3)} dan space saving "
    f"{angka(bmp_huf['Space saving (%)'], 2)} persen. JPEG/DCT memberi rasio {angka(bmp_jpg['Compression ratio'], 3)} "
    f"dan space saving {angka(bmp_jpg['Space saving (%)'], 2)} persen, dengan PSNR {angka(bmp_jpg['PSNR'], 3)} dB dan "
    f"SSIM {angka(bmp_jpg['SSIM'], 4)}."
)
paragraf(
    "RLE dan Huffman memberi rasio yang sama untuk BMP dan PNG karena keduanya bekerja pada byte piksel mentah yang "
    "sama. Pada input JPEG, rasio RLE dan Huffman sedikit berbeda karena piksel hasil decoding JPEG sudah berubah. "
    "Baseline JPEG/DCT mengikuti ukuran berkas input, sehingga rasionya berubah antar format. JPEG/DCT pada PNG memberi "
    f"rasio {angka(png_jpg['Compression ratio'], 3)} dan pada input JPEG memberi rasio "
    f"{angka(jpg_jpg['Compression ratio'], 3)}."
)
paragraf(
    f"Pada SVG_raster, RLE memberi rasio {angka(svg_rle['Compression ratio'], 3)} dan Huffman memberi rasio "
    f"{angka(svg_huf['Compression ratio'], 3)}. JPEG/DCT memberi rasio {angka(svg_jpg['Compression ratio'], 3)} dan "
    f"space saving {angka(svg_jpg['Space saving (%)'], 2)} persen, dengan output "
    f"{ukuran(svg_jpg['Ukuran output (bytes)'])} byte dari input {ukuran(svg_jpg['Ukuran baseline (bytes)'])} byte. "
    f"PSNR {angka(svg_jpg['PSNR'], 3)} dB dan SSIM {angka(svg_jpg['SSIM'], 4)}. Kualitas SVG_raster paling rendah "
    "menurut PSNR karena bidang warna datar dan tepi tajam lebih sensitif terhadap kuantisasi JPEG, meskipun SSIM "
    "tetap tinggi karena struktur global tidak banyak berubah."
)

paragraf(
    "Tabel 3 mencatat waktu encoding dan decoding. Huffman membutuhkan waktu paling lama karena pembentukan bitstring dan "
    "codebook. RLE berada di antara Huffman dan JPEG/DCT. JPEG/DCT paling cepat karena proses inti dijalankan oleh "
    "library OpenCV. Angka waktu bergantung pada mesin uji dan implementasi Python, sehingga tidak dapat dipakai sebagai "
    "patokan perangkat keras. Nilai pada Tabel 3 berasal dari eksekusi pipeline.py. Eksekusi notebook memakai kode yang "
    "sama, tetapi waktu dapat berbeda sedikit karena dijalankan sebagai proses terpisah."
)
rows = []
for _, r in comp.iterrows():
    total = float(r["Waktu kompresi (s)"]) + float(r["Waktu dekompresi (s)"])
    rows.append(
        [
            r["Format"],
            r["Metode"],
            angka(r["Waktu kompresi (s)"], 5),
            angka(r["Waktu dekompresi (s)"], 5),
            angka(total, 5),
        ]
    )
tabel(
    ["Format", "Metode", "Kompresi (s)", "Dekompresi (s)", "Total (s)"],
    rows,
    [28, 30, 38, 38, 36],
    size=8,
    align="CENTER",
    tinggi_baris=4.5,
)
caption("Tabel 3. Waktu encoding dan decoding untuk setiap format dan metode.")

gambar(
    COMP / "graphs" / "compression_ratio.png",
    115,
    "Gambar 2. Perbandingan rasio kompresi terhadap baseline antar format dan metode.",
)
gambar(
    COMP / "graphs" / "file_ratio.png",
    115,
    "Gambar 3. Perbandingan rasio ukuran berkas input : output. Garis putus-putus menandai batas impas 1x.",
)
gambar(
    COMP / "graphs" / "space_saving.png",
    115,
    "Gambar 4. Perbandingan space saving antar format dan metode.",
)
paragraf(
    "Gambar 2 sampai 4 menunjukkan pola yang sama. Rasio dan penghematan tertinggi berada pada JPEG/DCT untuk BMP. "
    "Pada SVG_raster, JPEG/DCT masih menghemat 19.95 persen, tetapi PSNR-nya paling rendah. RLE dan Huffman relatif "
    "stabil untuk BMP, PNG, dan JPEG karena baseline-nya sama, sedangkan JPEG/DCT berubah mengikuti ukuran berkas "
    "input. Pada Gambar 3, dari RLE dan Huffman hanya Huffman pada input BMP yang melewati batas impas, karena berkas "
    "BMP belum dimampatkan; pada input PNG dan JPEG kedua metode tetap memperbesar berkas meski rasio baseline-nya di "
    "atas 1. Grafik ini memperjelas bahwa perbandingan antar metode harus dibaca per kelompok "
    "baseline, sedangkan penyusutan berkas nyata dibaca dari rasio berkas."
)
gambar(
    COMP / "comparison" / "visual_comparison.png",
    78,
    "Gambar 5. Perbandingan frame DAiSEE asli dan hasil JPEG quality 85.",
)
paragraf(
    f"Pada quality 85, perbedaan visual sulit dilihat pada ukuran tampilan biasa, tetapi metrik menunjukkan adanya "
    f"kehilangan informasi. SSIM {angka(bmp_jpg['SSIM'], 4)} pada input BMP berarti struktur citra masih sangat mirip. "
    f"Penurunan PSNR paling terlihat pada SVG_raster, dengan PSNR {angka(svg_jpg['PSNR'], 3)} dB dan SSIM "
    f"{angka(svg_jpg['SSIM'], 4)}."
)

# Analisis dan tabel teknik
judul2("3.3 Analisis efektivitas metode")
paragraf(
    "RLE paling sesuai untuk citra dengan banyak byte berulang, misalnya bidang warna datar atau ikon sederhana. RLE "
    "kurang efektif pada citra fotografis karena perubahan nilai antar piksel kecil tetapi jarang berulang. Frame "
    f"DAiSEE menunjukkan hal ini: output RLE mencapai {ukuran(bmp_rle['Ukuran output (bytes)'])} byte, lebih besar "
    f"daripada {ukuran(bmp_rle['Ukuran baseline (bytes)'])} byte piksel mentah. Huffman paling sesuai ketika distribusi "
    "byte tidak merata. Huffman membutuhkan codebook, sehingga overhead-nya lebih besar pada citra kecil. Pada frame "
    f"ini Huffman hanya menghemat {angka(bmp_huf['Space saving (%)'], 2)} persen. JPEG/DCT paling sesuai untuk foto "
    "dan citra dengan variasi warna karena mengurangi detail visual yang kurang terlihat oleh mata."
)
tabel(
    ["Metode", "Citra yang cocok", "Penjelasan"],
    [
        ["RLE", "Citra dengan banyak byte berulang", "Efektif saat nilai yang sama muncul berurutan"],
        ["Huffman", "Citra dengan distribusi byte tidak merata", "Byte yang sering muncul mendapat kode lebih pendek"],
        ["JPEG/DCT", "Foto dan citra dengan variasi warna", "Mengurangi detail visual melalui kompresi lossy"],
    ],
    [28, 62, 78],
    size=8.4,
    align="LEFT",
    tinggi_baris=5.2,
)
caption("Tabel 4. Karakteristik citra yang cocok untuk setiap metode.")

paragraf(
    "Tabel 5a merangkum sepuluh teknik kompresi. Kolom jenis, cara kerja, kualitas, dan kompleksitas berisi kategori "
    "kualitatif, sedangkan rasio tipikal berisi kisaran literatur, bukan hasil pengukuran pada tugas ini. Hasil "
    "pengukuran ada pada Tabel 2. Tabel 5b merangkum kelebihan dan kekurangan setiap teknik. Sitasi menyertai teknik "
    "yang bersangkutan."
)
pastikan_ruang(62)
tabel(
    [
        "No",
        "Teknik",
        "Jenis",
        "Cara kerja",
        "Rasio tipikal",
        "Kualitas",
        "Kompleksitas",
        "Contoh penggunaan",
    ],
    [
        [
            "1",
            "RLE [14]",
            "Lossless",
            "Run byte berulang disimpan sebagai pasangan (panjang, nilai)",
            "1-3x pada citra bitmap sederhana",
            "Sempurna",
            "Rendah",
            "TIFF-G3 faksimili, ikon, BMP",
        ],
        [
            "2",
            "Huffman [7]",
            "Lossless",
            "Kode panjang variabel menurut frekuensi simbol",
            "1,5-2x",
            "Sempurna",
            "Sedang",
            "Tahap entropy JPEG, PNG, MP3",
        ],
        [
            "3",
            "Arithmetic coding [9]",
            "Lossless",
            "Interval probabilitas pada bilangan pecahan",
            "2-4x",
            "Sempurna",
            "Tinggi",
            "JPEG 2000 (MQ coder), JBIG",
        ],
        [
            "4",
            "LZW [10]",
            "Lossless",
            "Kamus frasa berulang dibangun adaptif",
            "2-3x",
            "Sempurna",
            "Sedang",
            "GIF, TIFF-LZW, PDF",
        ],
        [
            "5",
            "DEFLATE [11]",
            "Lossless",
            "LZ77 digabung Huffman",
            "2-3x",
            "Sempurna",
            "Sedang",
            "PNG, ZIP, gzip, HTTP",
        ],
        [
            "6",
            "JPEG/DCT [3]",
            "Lossy",
            "DCT 8 x 8, kuantisasi, entropy coding",
            "10-20x",
            "Baik",
            "Sedang",
            "Foto kamera dan web",
        ],
        [
            "7",
            "JPEG 2000 [12]",
            "Lossy dan lossless",
            "Wavelet dan bit-plane coding",
            "20-40x",
            "Sangat baik",
            "Tinggi",
            "Arsip medis, sinema digital",
        ],
        [
            "8",
            "WebP [5]",
            "Lossy dan lossless",
            "Prediksi blok intra dan entropy coding",
            "2-10x",
            "Baik",
            "Sedang",
            "Web dan aplikasi seluler",
        ],
        [
            "9",
            "VQ [13]",
            "Lossy",
            "Codebook vektor, indeks vektor terdekat",
            "8-16x",
            "Cukup",
            "Tinggi",
            "Kompresi awal, citra satelit",
        ],
        [
            "10",
            "Fractal [16]",
            "Lossy",
            "Self-similarity blok dan iterated function system",
            "10-30x",
            "Cukup",
            "Sangat tinggi",
            "Arsip eksperimental, tekstur",
        ],
    ],
    [7, 27, 16, 37, 24, 15, 18, 26],
    size=6.7,
    align="LEFT",
    tinggi_baris=7.2,
    padding=0.7,
)
caption("Tabel 5a. Rangkuman sepuluh teknik kompresi citra: jenis, cara kerja, rasio tipikal, dan penggunaan.")

pastikan_ruang(80)
tabel(
    ["No", "Teknik", "Kelebihan", "Kekurangan"],
    [
        [
            "1",
            "RLE",
            "Sangat sederhana, lossless, cepat pada data dengan run panjang",
            "Membesar pada citra fotografis; pada uji ini output 1,95x data mentah",
        ],
        [
            "2",
            "Huffman",
            "Optimal untuk distribusi simbol yang diketahui dan lossless",
            "Perlu tabel kode; tidak menangkap pola berulang; minimum 1 bit per simbol",
        ],
        [
            "3",
            "Arithmetic coding",
            "Mendekati entropi, umumnya lebih padat daripada Huffman",
            "Implementasi kompleks, lebih lambat, satu galat bit dapat merusak aliran",
        ],
        [
            "4",
            "LZW",
            "Adaptif tanpa perlu mengirim tabel kode",
            "Kinerja turun pada data hampir acak; riwayat paten pada GIF",
        ],
        [
            "5",
            "DEFLATE",
            "Rasio baik dengan kecepatan tinggi dan dukungan sangat luas",
            "Bukan untuk lossy; rasio di bawah codec citra modern",
        ],
        [
            "6",
            "JPEG/DCT",
            "Rasio tinggi untuk foto, didukung hampir semua perangkat",
            "Blocking dan ringing pada rasio tinggi; informasi hilang permanen",
        ],
        [
            "7",
            "JPEG 2000",
            "Satu codec untuk lossy dan lossless, progresif dan skalabel",
            "Kompleks, encoder lambat, dukungan peramban terbatas",
        ],
        [
            "8",
            "WebP",
            "Rasio lebih baik daripada JPEG pada ukuran serupa dan mendukung alpha",
            "Dukungan perangkat lama terbatas; lossy tetap lossy",
        ],
        [
            "9",
            "VQ",
            "Dekompresi sangat cepat karena hanya lookup indeks",
            "Artefak blok, codebook mahal, kualitas menurun tajam pada rasio tinggi",
        ],
        [
            "10",
            "Fractal",
            "Rasio sangat tinggi dan resolusi independen",
            "Encoding sangat lambat, kualitas sulit diprediksi, adopsi terbatas",
        ],
    ],
    [7, 27, 68, 68],
    size=7.0,
    align="LEFT",
    tinggi_baris=6.6,
    padding=0.8,
)
caption("Tabel 5b. Kelebihan dan kekurangan setiap teknik kompresi.")

# Watermarking
judul1("4. Watermarking")
judul2("4.1 Imperceptibility dan ekstraksi")
paragraf(
    "Tabel 6 menunjukkan hasil pengukuran PSNR dan SSIM. Visible watermark menurunkan kualitas visual secara terukur "
    f"dengan PSNR {angka(wm_visible['PSNR'], 3)} dB dan SSIM {angka(wm_visible['SSIM'], 4)}. Invisible LSB hampir tidak "
    f"mengubah tampilan dengan PSNR {angka(wm_lsb['PSNR'], 3)} dB dan SSIM {angka(wm_lsb['SSIM'], 4)}. Perbedaan ini "
    "sesuai dengan sifat kedua metode: visible watermark mengubah piksel secara sengaja, sedangkan LSB hanya mengubah "
    "bit terendah."
)
rows = []
for _, r in wm_metrics.iterrows():
    if r["Teknik"] == "Visible":
        akurasi = "Tidak diekstrak"
    else:
        akurasi = f"{angka(wm_extract.iloc[0]['Bit accuracy (%)'], 2)} persen"
    rows.append([r["Teknik"], angka(r["PSNR"], 3), angka(r["SSIM"], 4), akurasi])
tabel(
    ["Teknik", "PSNR (dB)", "SSIM", "Bit accuracy awal"],
    rows,
    [50, 33, 28, 45],
    size=8.6,
    align="CENTER",
    tinggi_baris=5,
)
caption("Tabel 6. Imperceptibility dan akurasi ekstraksi watermark.")

gambar(
    WM / "comparison_before_after.png",
    165,
    "Gambar 6. Perbandingan citra asli, visible watermark, dan invisible watermark.",
)
paragraf(
    "Visible watermark terbaca jelas pada bagian bawah citra. Invisible watermark tidak terlihat pada tampilan biasa, "
    "tetapi tetap dapat diekstrak karena disimpan pada bit terendah kanal biru. Gambar 7 memperlihatkan pola 64 x 64 "
    "hasil ekstraksi yang diperbesar 4 kali dengan interpolasi nearest. Pola terbaca utuh dan bit accuracy mencapai "
    "100 persen pada kondisi tanpa serangan."
)
paragraf(
    "Payload 4.096 bit hanya menempati 16 baris teratas. Baris 17 sampai 256 tidak membawa watermark. Penempatan ini "
    "dipilih agar loop penulisan sederhana dan posisi bit mudah dilacak. Konsekuensinya, operasi crop yang memotong "
    "bagian atas citra langsung menghilangkan sebagian payload. Resize juga menggeser posisi piksel, sehingga bit "
    "watermark tidak lagi berada pada indeks yang sama."
)

extracted_path = WM / "extracted" / "extracted_watermark_4x.png"
with Image.open(WM / "extracted" / "extracted_watermark.png") as im:
    im.convert("L").resize((256, 256), Image.Resampling.NEAREST).save(extracted_path)
gambar(
    extracted_path,
    48,
    "Gambar 7. Pola watermark 64 x 64 hasil ekstraksi, diperbesar 4 kali.",
)

judul2("4.2 Robustness")
paragraf(
    "Tabel 7 membandingkan kedua teknik pada tiga operasi yang sama. Untuk LSB, metriknya bit accuracy. Untuk visible "
    "watermark, polanya adalah residual antara citra ber-watermark dan citra dasar; operasi yang sama diterapkan pada "
    "keduanya, lalu residual hasil serangan dibandingkan dengan residual acuan melalui korelasi NCC dan tumpang tindih "
    f"IoU. Pada LSB, akurasi menjadi {angka(rob['JPEG'], 2)} persen setelah JPEG, {angka(rob['Resize'], 2)} persen "
    f"setelah resize, dan {angka(rob['Crop'], 2)} persen setelah crop. Tebakan acak untuk watermark biner berada di "
    "sekitar 50 persen."
)
rows = []
for serangan in ("JPEG", "Resize", "Crop"):
    if serangan == "JPEG":
        operasi = "JPEG quality 70"
    elif serangan == "Resize":
        operasi = "Resize 128 x 128 lalu 256 x 256"
    else:
        operasi = "Crop tengah 80 persen lalu resize"
    akurasi = float(rob[serangan])
    tafsir = "Di bawah tebakan acak" if akurasi < 50 else "Sebagian bit masih terbaca"
    rows.append(
        [
            operasi,
            f"{angka(akurasi, 2)} persen",
            angka(robv[serangan]["NCC"], 3),
            angka(robv[serangan]["IoU"], 3),
            tafsir,
        ]
    )
tabel(
    ["Operasi", "LSB: bit accuracy", "Visible: NCC", "Visible: IoU", "Interpretasi LSB"],
    rows,
    [54, 28, 20, 18, 50],
    size=8.2,
    align="LEFT",
    tinggi_baris=5,
)
caption(
    "Tabel 7. Hasil uji robustness kedua teknik. NCC dan IoU mengukur ketahanan pola visible watermark, sedangkan bit "
    "accuracy mengukur ketahanan payload LSB."
)
gambar(
    WM / "robustness_chart.png",
    108,
    "Gambar 8. Bit accuracy watermark LSB setelah tiga operasi serangan.",
)
gambar(
    WM / "robustness_visible_grid.png",
    168,
    "Gambar 9. Visible watermark sebelum dan sesudah tiga operasi serangan.",
)
paragraf(
    "Hasil ini menunjukkan kelemahan LSB. LSB menyimpan informasi pada bit yang mudah berubah ketika citra dikompresi, "
    "diperkecil, atau dipotong. Pola juga ditempatkan pada 16 baris teratas, sehingga crop dan resize menggeser "
    "sinkronisasi posisi bit. Metode domain frekuensi seperti DCT atau DWT lebih tahan terhadap operasi tersebut, tetapi "
    "biaya komputasinya lebih tinggi dan distorsi pada citra juga lebih besar [15]. Visible watermark tidak bergantung "
    "pada bit individual, sehingga tidak runtuh oleh satu galat bit; deteksinya bergantung pada korelasi pola teks yang "
    "tersisa. Perbandingan kelebihan dan kekurangan kedua teknik dirangkum pada Tabel 7a."
)
tabel(
    ["Aspek", "Visible watermark", "Invisible LSB"],
    [
        [
            "Imperceptibility",
            f"PSNR {angka(wm_visible['PSNR'], 3)} dB, SSIM {angka(wm_visible['SSIM'], 4)}; teks terlihat",
            f"PSNR {angka(wm_lsb['PSNR'], 3)} dB, SSIM {angka(wm_lsb['SSIM'], 4)}; tidak terlihat",
        ],
        [
            "Ketahanan",
            f"NCC {angka(robv['JPEG']['NCC'], 3)} setelah JPEG dan {angka(robv['Crop']['NCC'], 3)} setelah crop",
            f"Bit accuracy {angka(rob['JPEG'], 2)} persen setelah JPEG dan {angka(rob['Crop'], 2)} persen setelah crop",
        ],
        [
            "Ekstraksi",
            "Tanpa ekstraksi; teks terbaca langsung dari citra",
            "Perlu posisi bit dan citra ber-watermark sebagai acuan",
        ],
        [
            "Kapasitas",
            "Terbatas pada teks atau logo yang tidak menutupi wajah",
            "4.096 bit pada 16 baris teratas kanal biru",
        ],
        [
            "Biaya komputasi",
            "Rendah: putText dan addWeighted",
            "Rendah: loop 4.096 piksel tanpa transformasi",
        ],
        [
            "Kelebihan utama",
            "Langsung terlihat, tidak butuh dekoder, pola tidak bergantung pada satu bit",
            "Tidak mengganggu tampilan; payload diekstrak utuh tanpa serangan",
        ],
        [
            "Kekurangan utama",
            "Mengubah tampilan dan menurunkan PSNR; mudah dihapus dengan crop atau penutupan area",
            "Rapuh: satu galat bit per posisi merusak payload; tidak tahan JPEG, resize, atau crop",
        ],
    ],
    [30, 70, 70],
    size=7.6,
    align="LEFT",
    tinggi_baris=6.2,
)
caption("Tabel 7a. Kelebihan dan kekurangan visible watermark dan invisible LSB.")

# Kesimpulan dan referensi
judul1("5. Kesimpulan")
paragraf(
    "Augmentasi dengan enam transformasi ringan dapat memperluas variasi data tanpa menghilangkan ekspresi wajah secara "
    "nyata pada sampel yang diuji. Pemilihan parameter yang konservatif penting untuk menjaga ciri wajah. Evaluasi "
    "augmentasi pada laporan ini bersifat kualitatif karena tidak ada model klasifikasi yang dilatih."
)
paragraf(
    f"RLE dan Huffman memberi rekonstruksi lossless. Pada citra uji 256 x 256, RLE memberi rasio "
    f"{angka(bmp_rle['Compression ratio'], 3)} dan space saving {angka(bmp_rle['Space saving (%)'], 2)} persen pada BMP. "
    f"Huffman memberi rasio {angka(bmp_huf['Compression ratio'], 3)} dan space saving "
    f"{angka(bmp_huf['Space saving (%)'], 2)} persen. JPEG/DCT memberi rasio "
    f"{angka(bmp_jpg['Compression ratio'], 3)} dan space saving {angka(bmp_jpg['Space saving (%)'], 2)} persen pada BMP, "
    f"dengan PSNR {angka(bmp_jpg['PSNR'], 3)} dB dan SSIM {angka(bmp_jpg['SSIM'], 4)}."
)
paragraf(
    "Visible watermark mudah dilihat tetapi menurunkan kualitas visual. Invisible LSB memiliki imperceptibility tinggi, "
    "tetapi rapuh terhadap kompresi JPEG, resize, dan crop. Bit accuracy setelah serangan adalah "
    f"{angka(rob['JPEG'], 2)} persen untuk JPEG, {angka(rob['Resize'], 2)} persen untuk resize, dan "
    f"{angka(rob['Crop'], 2)} persen untuk crop. Untuk kebutuhan ketahanan, metode domain frekuensi perlu "
    "dipertimbangkan."
)
judul2("Keterbatasan")
butir(
    "Eksperimen memakai subset 10 klip dari 5.358 klip berlabel pada split Train DAiSEE, bukan seluruh 9.068 klip. "
    "Hasil augmentasi belum mewakili populasi pengguna DAiSEE."
)
butir(
    "Setiap klip diwakili satu frame pada posisi tengah video. Frame pada posisi lain dapat menunjukkan ekspresi dan "
    "pose yang berbeda."
)
butir(
    f"Rasterisasi SVG memakai CairoSVG 2.9.1. Baseline SVG_raster adalah PNG hasil rasterisasi berukuran "
    f"{ukuran(svg_jpg['Ukuran baseline (bytes)'])} byte, bukan berkas SVG 523 byte."
)
butir(
    "Hasil kompresi berasal dari satu citra uji 256 x 256. Angka tersebut berlaku untuk citra itu, bukan rata-rata "
    "populasi."
)
butir(
    "Waktu encoding dan decoding diukur satu kali pada mesin uji. Angka waktu dipakai untuk perbandingan relatif, bukan "
    "benchmark perangkat keras."
)
butir(
    "Tidak ada model klasifikasi yang dilatih, sehingga augmentasi tidak dievaluasi dengan akurasi model."
)

judul1("Pernyataan Penggunaan AI")
paragraf(
    "Sesuai ketentuan tugas, penggunaan alat bantu AI dicantumkan secara terbuka. Alat yang dipakai adalah Command "
    "Code, asisten koding berbasis model bahasa besar yang berjalan di terminal. AI dipakai sebagai alat bantu, bukan "
    "sebagai pengganti pemahaman penulis."
)
paragraf(
    "Peran AI dalam tugas ini meliputi: (1) membantu menulis dan men-debug kode pipeline Python untuk augmentasi, "
    "kompresi, dan watermarking; (2) menata outline dan struktur laporan; (3) menyusun README dan dokumentasi cara "
    "menjalankan program; serta (4) membantu mencari dan merangkum sumber referensi. AI tidak mengambil keputusan "
    "metodologi secara mandiri."
)
paragraf(
    "Seluruh kode dijalankan dan diperiksa oleh penulis. Angka pada laporan berasal dari eksekusi pipeline, bukan dari "
    "keluaran AI. Setiap referensi diverifikasi terhadap sumber aslinya, dan interpretasi hasil serta tanggung jawab "
    "akhir atas karya ini berada pada penulis. Penulis menyatakan bahwa karya ini disusun secara orisinal dan memahami "
    "seluruh bagian yang dibantu AI."
)

judul1("Referensi")
refs = [
    "[1] A. Gupta, A. D'Cunha, K. Awasthi, and V. Balasubramanian, \"DAiSEE: Towards User Engagement Recognition in the "
    "Wild,\" arXiv:1609.01885, 2016. doi: 10.48550/arXiv.1609.01885. "
    "PDF: https://arxiv.org/pdf/1609.01885.",
    "[2] S. Porcu, A. Floris, and L. Atzori, \"Evaluation of Data Augmentation Techniques for Facial Expression "
    "Recognition Systems,\" Electronics, vol. 9, no. 11, art. 1892, 2020. doi: 10.3390/electronics9111892. "
    "PDF: https://www.mdpi.com/2079-9292/9/11/1892.",
    "[3] G. K. Wallace, \"The JPEG Still Picture Compression Standard,\" IEEE Transactions on Consumer Electronics, "
    "vol. 38, no. 1, pp. xviii-xxxiv, 1992. doi: 10.1109/30.125072. "
    "PDF: https://www.ijg.org/files/Wallace.JPEG.pdf.",
    "[4] W. Bender, D. Gruhl, N. Morimoto, and A. Lu, \"Techniques for Data Hiding,\" IBM Systems Journal, vol. 35, "
    "no. 3.4, pp. 313-336, 1996. doi: 10.1147/sj.353.0313. "
    "PDF: https://people.sugarlabs.org/walter/techniques-for-data-hiding.pdf.",
    "[5] Google, \"WebP Compression,\" https://developers.google.com/speed/webp/docs/compression.",
    "[6] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, \"Image Quality Assessment: From Error Visibility to "
    "Structural Similarity,\" IEEE Transactions on Image Processing, vol. 13, no. 4, pp. 600-612, 2004. "
    "doi: 10.1109/TIP.2003.819861. PDF: https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf.",
    "[7] D. A. Huffman, \"A Method for the Construction of Minimum-Redundancy Codes,\" Proceedings of the IRE, vol. 40, "
    "no. 9, pp. 1098-1101, 1952. doi: 10.1109/JRPROC.1952.273898. "
    "PDF: https://compression.ru/download/articles/huff/huffman_1952_minimum-redundancy-codes.pdf.",
    "[8] CairoSVG, \"CairoSVG: SVG to PDF and PNG converter,\" version 2.9.1, https://cairosvg.org/.",
    "[9] J. J. Rissanen and G. G. Langdon, \"Arithmetic Coding,\" IBM Journal of Research and Development, vol. 23, "
    "no. 2, pp. 149-162, 1979. doi: 10.1147/rd.232.0149. "
    "PDF: http://bitsavers.informatik.uni-stuttgart.de/pdf/ibm/IBM_Journal_of_Research_and_Development/232/ibmrd2302G.pdf.",
    "[10] T. A. Welch, \"A Technique for High-Performance Data Compression,\" Computer, vol. 17, no. 6, pp. 8-19, 1984. "
    "doi: 10.1109/MC.1984.1659158. "
    "PDF: https://courses.cs.duke.edu/spring03/cps296.5/papers/welch_1984_technique_for.pdf.",
    "[11] P. Deutsch, \"DEFLATE Compressed Data Format Specification version 1.3,\" RFC 1951, 1996. "
    "doi: 10.17487/RFC1951. https://www.rfc-editor.org/info/rfc1951/.",
    "[12] A. Skodras, C. Christopoulos, and T. Ebrahimi, \"The JPEG 2000 Still Image Compression Standard,\" IEEE Signal "
    "Processing Magazine, vol. 18, no. 5, pp. 36-58, 2001. doi: 10.1109/79.952804. "
    "PDF: https://infoscience.epfl.ch/record/111813.",
    "[13] R. M. Gray, \"Vector Quantization,\" IEEE ASSP Magazine, vol. 1, no. 2, pp. 4-29, 1984. "
    "doi: 10.1109/MASSP.1984.1162229. "
    "PDF: https://ntrs.nasa.gov/api/citations/19890012969/downloads/19890012969.pdf.",
    "[14] M. Mahoney, Data Compression Explained, 2013. https://mattmahoney.net/dc/dce.html.",
    "[15] F. A. P. Petitcolas, R. J. Anderson, and M. G. Kuhn, \"Information Hiding: A Survey,\" Proceedings of the "
    "IEEE, vol. 87, no. 7, pp. 1062-1078, 1999. doi: 10.1109/5.771065. "
    "PDF: https://www.petitcolas.net/fabien/publications/ieee99-infohiding.pdf.",
    "[16] N. Pourshab and M. Bagheritabar, \"Accelerating Fractal Image Compression Using Search Pruning and Fractal "
    "Dimension Gating,\" arXiv:2507.06325, 2025. doi: 10.48550/arXiv.2507.06325. "
    "PDF: https://arxiv.org/pdf/2507.06325.",
]
for ref in refs:
    pdf.set_font("Times", "", 9.0)
    pdf.multi_cell(0, 4.35, ref, align="L", wrapmode="WORD")
    pdf.ln(0.6)

pdf.add_page()
judul2("Lampiran. Berkas hasil")
tabel(
    ["Berkas", "Isi"],
    [
        [
            "results/B_Compression/compression_results.csv",
            "Ukuran, rasio, dua bentuk space saving, PSNR, SSIM, dan waktu 12 baris",
        ],
        ["results/C_Watermarking/watermark_metrics.csv", "PSNR dan SSIM visible serta invisible LSB"],
        ["results/C_Watermarking/watermark_extraction.csv", "Bit accuracy ekstraksi awal"],
        ["results/C_Watermarking/robustness_results.csv", "Bit accuracy LSB setelah JPEG, resize, dan crop"],
        ["results/C_Watermarking/robustness_visible.csv", "NCC dan IoU visible setelah tiga serangan"],
        ["results/A_Augmentation/comparison_grid.png", "Grid citra asli dan enam augmentasi"],
        ["results/B_Compression/comparison/visual_comparison.png", "Perbandingan visual citra asli dan JPEG"],
        ["results/B_Compression/graphs", "Grafik rasio kompresi, rasio berkas, dan penghematan ruang"],
        ["results/C_Watermarking/robustness_chart.png", "Grafik bit accuracy setelah serangan"],
        [
            "results/C_Watermarking/robustness_visible_grid.png",
            "Grid visible watermark sebelum dan sesudah serangan",
        ],
        ["dataset/DAiSEE/selected_clips.csv", "Daftar 10 klip, label afektif, dan frame yang dipakai"],
        ["notebooks/Tugas_2_Komputasi_Multimedia.ipynb", "Notebook eksperimen yang dapat dijalankan ulang"],
        ["prepare_daisee.py", "Pengambil subset DAiSEE dan pengekstrak frame tengah"],
    ],
    [82, 88],
    size=7.8,
    align="LEFT",
    tinggi_baris=4.5,
)
caption("Tabel 8. Berkas hasil yang dipakai laporan.")

judul2("Klip DAiSEE terpilih")
paragraf(
    "Tabel 9 mendaftar sepuluh klip yang dipakai pada eksperimen augmentasi. Setiap klip berasal dari subjek berbeda dan "
    "diwakili satu frame pada posisi tengah video. Label dominan adalah label dengan skor tertinggi pada TrainLabels.csv."
)
rows = []
for _, r in manifest.iterrows():
    rows.append(
        [
            int(r["Urutan"]),
            str(r["ClipID"]),
            str(r["SubjectID"]),
            str(r["Dominan"]),
            int(r["Frame"]),
        ]
    )
tabel(
    ["No", "ClipID", "Subjek", "Label dominan", "Frame tengah"],
    rows,
    [12, 34, 28, 40, 26],
    size=8,
    align="CENTER",
    tinggi_baris=4.2,
)
caption("Tabel 9. Sepuluh klip DAiSEE yang dipakai pada eksperimen augmentasi.")

out = RESULTS / "laporan_tugas2.pdf"
pdf.output(str(out))
print(f"Laporan ditulis ke {out}")
