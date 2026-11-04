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
jpg_jpg = row("JPEG", "JPEG/DCT")
svg_rle = row("SVG_raster", "RLE")
svg_huf = row("SVG_raster", "Huffman")
svg_jpg = row("SVG_raster", "JPEG/DCT")
wm_visible = wm_metrics[wm_metrics["Teknik"] == "Visible"].iloc[0]
wm_lsb = wm_metrics[wm_metrics["Teknik"] == "Invisible (LSB)"].iloc[0]
rob = {r["Serangan"]: r["Bit accuracy (%)"] for _, r in robust.iterrows()}



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
    ("Dataset uji", "DAiSEE, subset 10 klip latih, 4 label afektif"),
    ("Populasi DAiSEE", "9.068 klip video, 112 pengguna"),
    ("Seed augmentasi", "42, stratified per label"),
    ("Citra uji kompresi", "256 x 256 RGB dari frame DAiSEE"),
    ("Rasterisasi SVG", "CairoSVG 2.9.1"),
    ("Metode", "RLE, Huffman, JPEG/DCT, visible watermark, invisible LSB"),
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
    "DAiSEE dirancang untuk pengenalan tingkat keterlibatan pengguna [3]. Dataset ini berisi 9.068 klip video dari 112 "
    "pengguna dengan empat label afektif, yaitu Boredom, Engagement, Confusion, dan Frustration. Eksperimen ini memakai "
    "subset 10 klip dari split Train, bukan seluruh koleksi. Satu frame tengah diambil dari setiap klip, sehingga "
    "augmentasi bekerja pada citra 640 x 480 yang masih memuat wajah, latar, dan variasi pencahayaan alami."
)
paragraf(
    "Teori pengolahan citra digital mengikuti Gonzalez dan Woods [1]. Representasi citra, transformasi geometri, "
    "resampling, pemrosesan sinyal, dan warna mengikuti Hughes et al. [2], khususnya Bab 5 tentang persepsi visual, "
    "Bab 10 tentang transformasi dua dimensi, Bab 17 tentang representasi dan manipulasi citra, Bab 18 tentang citra "
    "sebagai sinyal, Bab 19 tentang pembesaran dan pengecilan citra, serta Bab 28 tentang warna. Bab 5 dan 28 dipakai "
    "untuk menjelaskan mengapa perubahan brightness, contrast, dan noise dinilai dari persepsi. Bab 10 dan 19 dipakai "
    "untuk menjelaskan rotasi, crop, dan resampling."
)
paragraf(
    "Cakupan laporan meliputi pipeline yang dapat dijalankan ulang, perbandingan baseline yang eksplisit, evaluasi "
    "kualitas rekonstruksi, ekstraksi watermark, dan uji ketahanan. Rasterisasi SVG memakai CairoSVG [12], bukan "
    "gambar ulang manual. Keterbatasan ukuran subset, pemilihan frame, dan jumlah citra uji dicatat pada bagian akhir "
    "agar hasil tidak dibaca melebihi cakupan eksperimen."
)

# Metodologi
judul1("2. Metodologi")
judul2("2.1 Augmentasi data")
paragraf(
    "Sepuluh klip dipilih dari split Train DAiSEE dengan random.Random(42). Pemilihan dilakukan secara stratified agar "
    "empat label afektif terwakili: 3 Boredom, 3 Engagement, 2 Confusion, dan 2 Frustration. Setiap klip berasal dari "
    "subjek berbeda. Frame diambil pada posisi tengah video, lalu disimpan sebagai PNG 640 x 480. Enam transformasi "
    "diterapkan pada setiap frame. Rotasi memakai sudut 10 derajat dan border reflect. Crop mengambil 80 persen area "
    "tengah, lalu diperbesar kembali ke ukuran asli. Brightness/contrast memakai alpha 1.2 dan beta 15. Gaussian noise "
    "memakai standar deviasi 10. Gaussian blur memakai kernel 3 x 3 dan sigma 1.0."
)
paragraf(
    "Parameter dijaga ringan agar area mata dan mulut tidak hilang. Bab 10 [2] membahas matriks transformasi dua "
    "dimensi yang dipakai untuk rotasi. Bab 19 [2] membahas pembesaran dan pengecilan citra, termasuk interpolasi yang "
    "dipakai saat crop dan resize. Bab 18 [2] membahas konvolusi dan filter, yang menjadi dasar Gaussian blur. Bab 5 "
    "dan 28 [2] memberi konteks persepsi terhadap perubahan cahaya dan warna."
)
tabel(
    ["No", "Teknik", "Parameter", "Efek yang diharapkan"],
    [
        ["1", "Horizontal flip", "Flip kode 1", "Variasi orientasi wajah"],
        ["2", "Rotasi", "10 derajat, border reflect", "Variasi sudut pandang"],
        ["3", "Crop dan resize", "Crop tengah 80 persen, resize ke ukuran asli", "Variasi skala dan framing"],
        ["4", "Brightness/contrast", "Alpha 1.2, beta 15", "Variasi pencahayaan"],
        ["5", "Gaussian noise", "Sigma 10", "Variasi noise sensor"],
        ["6", "Gaussian blur", "Kernel 3 x 3, sigma 1.0", "Variasi ketajaman"],
    ],
    [10, 38, 70, 52],
    size=8.2,
    align="LEFT",
)
caption("Tabel 1. Parameter enam transformasi augmentasi.")

judul2("2.2 Kompresi citra")
paragraf(
    "RLE menggabungkan byte berulang dengan panjang run maksimal 255 dan header 16 byte. Huffman memberi kode lebih "
    "pendek untuk byte yang sering muncul; ukuran output mencakup codebook, metadata, padding, dan overhead pickle. "
    "JPEG/DCT memakai encoder JPEG OpenCV dengan kualitas 85 dan transformasi DCT internal. RLE dan Huffman adalah "
    "implementasi algoritma sendiri, sedangkan JPEG/DCT memakai library. Dasar algoritma Huffman mengikuti Huffman [11], "
    "standar JPEG mengikuti Wallace [5], dan teori kompresi data mengikuti Salomon [8]."
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
    "SVG dirasterisasi dengan CairoSVG [12] menjadi PNG 256 x 256, lalu PNG hasil rasterisasi dipakai sebagai input "
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
    "resize. Setiap hasil serangan diekstrak dan dihitung bit accuracy-nya. Dasar watermarking mengikuti Cox et al. [6] "
    "dan teknik data hiding mengikuti Bender et al. [7]."
)

judul2("2.4 Metrik")
paragraf(
    "Rasio kompresi dihitung sebagai ukuran baseline dibagi ukuran output. Space saving dihitung sebagai "
    "(1 - ukuran output / ukuran baseline) x 100 persen. PSNR dihitung sebagai 10 log10(255^2 / MSE). SSIM mengikuti "
    "Wang et al. [10]. Bit accuracy dihitung sebagai jumlah bit yang sama dibagi jumlah bit total, lalu dikali 100 persen. "
    "PSNR dan SSIM dihitung antara citra asli dan citra hasil decoding."
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
    "tanpa mengubah ekspresi dasar. Rotasi 10 derajat masih mempertahankan area wajah. Crop 80 persen memperbesar wajah "
    "dan mengurangi konteks di tepi citra. Brightness/contrast membuat sebagian area terang dan gelap. Gaussian noise "
    "menambah variasi warna pada piksel. Gaussian blur menurunkan ketajaman tepi. Latar ruangan ikut berubah pada "
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
    "pernah dilakukan Porcu et al. [4], tetapi berada di luar cakupan tugas ini."
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
            angka(r["Space saving (%)"], 2),
            psnr_text(r["PSNR"]),
            angka(r["SSIM"], 4),
        ]
    )
pastikan_ruang(38)
tabel(
    ["Format", "Metode", "Baseline (byte)", "Output (byte)", "Rasio", "Saving (%)", "PSNR (dB)", "SSIM"],
    rows,
    [22, 22, 28, 26, 15, 17, 18, 14],
    size=7.8,
    align="CENTER",
    tinggi_baris=4.5,
)
caption(
    "Tabel 2. Ukuran baseline, ukuran output, rasio, space saving, PSNR, dan SSIM. Baseline RLE/Huffman adalah byte "
    "piksel mentah; baseline JPEG/DCT adalah ukuran berkas input."
)
paragraf(
    f"Pada input BMP, RLE memberi rasio {angka(bmp_rle['Compression ratio'], 3)} dan space saving "
    f"{angka(bmp_rle['Space saving (%)'], 2)} persen. Nilai negatif berarti output RLE lebih besar daripada byte piksel "
    f"mentah. Huffman memberi rasio {angka(bmp_huf['Compression ratio'], 3)} dan space saving "
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
    "Gambar 2. Perbandingan rasio kompresi antar format dan metode.",
)
gambar(
    COMP / "graphs" / "space_saving.png",
    115,
    "Gambar 3. Perbandingan space saving antar format dan metode.",
)
paragraf(
    "Gambar 2 dan 3 menunjukkan pola yang sama. Rasio dan penghematan tertinggi berada pada JPEG/DCT untuk BMP. "
    "Pada SVG_raster, JPEG/DCT masih menghemat 19.95 persen, tetapi PSNR-nya paling rendah. RLE dan Huffman relatif "
    "stabil untuk BMP, PNG, dan JPEG karena baseline-nya sama, sedangkan JPEG/DCT berubah mengikuti ukuran berkas "
    "input. Grafik ini memperjelas bahwa perbandingan antar metode harus dibaca per kelompok baseline."
)
gambar(
    COMP / "comparison" / "visual_comparison.png",
    78,
    "Gambar 4. Perbandingan frame DAiSEE asli dan hasil JPEG quality 85.",
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
    "DAiSEE menunjukkan hal ini: output RLE mencapai 382.652 byte, lebih besar daripada 196.608 byte piksel mentah. "
    "Huffman paling sesuai ketika distribusi byte tidak merata. Huffman membutuhkan codebook, sehingga overhead-nya "
    "lebih besar pada citra kecil. Pada frame ini Huffman hanya menghemat 4.71 persen. JPEG/DCT paling sesuai untuk foto "
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
    "Tabel 5 merangkum sepuluh teknik kompresi sebagai pembanding konseptual. Kolom rasio, kualitas, dan kompleksitas "
    "berisi kategori kualitatif, bukan hasil pengukuran. Tabel ini menempatkan RLE, Huffman, dan JPEG/DCT dalam "
    "kelompok metode yang lebih luas."
)
pastikan_ruang(58)
tabel(
    ["No", "Teknik", "Cara kerja", "Rasio", "Kualitas", "Kompleksitas"],
    [
        ["1", "RLE", "Menyimpan run byte berulang", "Rendah", "Sempurna", "Rendah"],
        ["2", "Huffman", "Kode variabel berdasarkan frekuensi byte", "Sedang", "Sempurna", "Sedang"],
        ["3", "Arithmetic coding", "Interval probabilitas simbol", "Tinggi", "Sempurna", "Tinggi"],
        ["4", "LZW", "Kamus adaptif untuk pola berulang", "Sedang", "Sempurna", "Sedang"],
        ["5", "DEFLATE", "LZ77 dan Huffman", "Sedang", "Sempurna", "Sedang"],
        ["6", "JPEG/DCT", "DCT, kuantisasi, entropy coding", "Tinggi", "Baik", "Sedang"],
        ["7", "JPEG 2000", "Wavelet dan bit-plane coding", "Tinggi", "Sangat baik", "Tinggi"],
        ["8", "WebP [9]", "Prediksi blok dan entropy coding", "Tinggi", "Baik", "Sedang"],
        ["9", "VQ", "Codebook vektor", "Sedang", "Cukup", "Tinggi"],
        ["10", "Fractal", "Self-similarity blok", "Tinggi", "Cukup", "Sangat tinggi"],
    ],
    [10, 30, 58, 18, 26, 28],
    size=7.4,
    align="CENTER",
    tinggi_baris=3.2,
    padding=0.7,
)
caption("Tabel 5. Rangkuman sepuluh teknik kompresi citra.")

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
    "Gambar 5. Perbandingan citra asli, visible watermark, dan invisible watermark.",
)
paragraf(
    "Visible watermark terbaca jelas pada bagian bawah citra. Invisible watermark tidak terlihat pada tampilan biasa, "
    "tetapi tetap dapat diekstrak karena disimpan pada bit terendah kanal biru. Gambar 6 memperlihatkan pola 64 x 64 "
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
    "Gambar 6. Pola watermark 64 x 64 hasil ekstraksi, diperbesar 4 kali.",
)

judul2("4.2 Robustness")
paragraf(
    f"Tabel 7 menunjukkan bit accuracy setelah tiga operasi. Kompresi JPEG menurunkan akurasi menjadi "
    f"{angka(rob['JPEG'], 2)} persen. Resize menurunkan akurasi menjadi {angka(rob['Resize'], 2)} persen. Crop "
    f"menurunkan akurasi menjadi {angka(rob['Crop'], 2)} persen. Tebakan acak pada watermark biner menghasilkan sekitar "
    "50 persen. JPEG dan crop berada di bawah batas itu, sehingga bit watermark tidak lagi dapat dipulihkan dengan "
    "benar. Resize masih di atas 50 persen, tetapi belum cukup untuk ekstraksi yang andal."
)
rows = []
for _, r in robust.iterrows():
    if r["Serangan"] == "JPEG":
        operasi = "JPEG quality 70"
        tafsir = "Di bawah tebakan acak"
    elif r["Serangan"] == "Resize":
        operasi = "Resize 128 x 128 lalu 256 x 256"
        tafsir = "Sebagian bit masih terbaca"
    else:
        operasi = "Crop tengah 80 persen lalu resize"
        tafsir = "Di bawah tebakan acak"
    rows.append([operasi, f"{angka(r['Bit accuracy (%)'], 2)} persen", tafsir])
tabel(
    ["Operasi", "Bit accuracy", "Interpretasi"],
    rows,
    [70, 40, 58],
    size=8.6,
    align="LEFT",
    tinggi_baris=5,
)
caption("Tabel 7. Hasil uji robustness watermark LSB.")
gambar(
    WM / "robustness_chart.png",
    118,
    "Gambar 7. Bit accuracy watermark LSB setelah tiga operasi serangan.",
)
paragraf(
    "Hasil ini menunjukkan kelemahan LSB. LSB menyimpan informasi pada bit yang mudah berubah ketika citra dikompresi, "
    "diperkecil, atau dipotong. Pola juga ditempatkan pada 16 baris teratas, sehingga crop dan resize menggeser "
    "sinkronisasi posisi bit. Metode domain frekuensi seperti DCT atau DWT lebih tahan terhadap operasi tersebut, tetapi "
    "biaya komputasinya lebih tinggi dan distorsi pada citra juga lebih besar [6]."
)

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

judul1("Referensi")
refs = [
    "[1] R. C. Gonzalez and R. E. Woods, Digital Image Processing, 4th ed. Pearson, 2018.",
    "[2] J. F. Hughes, A. van Dam, M. McGuire, D. F. Sklar, J. D. Foley, S. K. Feiner, and K. Akeley, Computer Graphics: "
    "Principles and Practice, 3rd ed. Addison-Wesley, 2014.",
    "[3] A. Gupta, A. D'Cunha, K. Awasthi, and V. Balasubramanian, \"DAiSEE: Towards User Engagement Recognition in the "
    "Wild,\" arXiv:1609.01885, 2016. doi: 10.48550/arXiv.1609.01885.",
    "[4] S. Porcu, A. Floris, and L. Atzori, \"Evaluation of Data Augmentation Techniques for Facial Expression "
    "Recognition Systems,\" Electronics, vol. 9, no. 11, art. 1892, 2020. doi: 10.3390/electronics9111892.",
    "[5] G. K. Wallace, \"The JPEG Still Picture Compression Standard,\" IEEE Transactions on Consumer Electronics, "
    "vol. 38, no. 1, pp. xviii-xxxiv, 1992. doi: 10.1109/30.125072.",
    "[6] I. Cox, M. Miller, J. Bloom, J. Fridrich, and T. Kalker, Digital Watermarking and Steganography, 2nd ed. "
    "Morgan Kaufmann, 2007.",
    "[7] W. Bender, D. Gruhl, N. Morimoto, and A. Lu, \"Techniques for Data Hiding,\" IBM Systems Journal, vol. 35, "
    "no. 3.4, pp. 313-336, 1996. doi: 10.1147/sj.353.0313.",
    "[8] D. Salomon, Data Compression: The Complete Reference, 4th ed. Springer, 2007.",
    "[9] Google, \"WebP Compression,\" https://developers.google.com/speed/webp/docs/compression.",
    "[10] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, \"Image Quality Assessment: From Error Visibility to "
    "Structural Similarity,\" IEEE Transactions on Image Processing, vol. 13, no. 4, pp. 600-612, 2004. "
    "doi: 10.1109/TIP.2003.819861.",
    "[11] D. A. Huffman, \"A Method for the Construction of Minimum-Redundancy Codes,\" Proceedings of the IRE, vol. 40, "
    "no. 9, pp. 1098-1101, 1952. doi: 10.1109/JRPROC.1952.273898.",
    "[12] CairoSVG, \"CairoSVG: SVG to PDF and PNG converter,\" version 2.9.1, https://cairosvg.org/.",
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
        ["results/B_Compression/compression_results.csv", "Ukuran, rasio, PSNR, SSIM, dan waktu 12 baris"],
        ["results/C_Watermarking/watermark_metrics.csv", "PSNR dan SSIM visible serta invisible LSB"],
        ["results/C_Watermarking/watermark_extraction.csv", "Bit accuracy ekstraksi awal"],
        ["results/C_Watermarking/robustness_results.csv", "Bit accuracy setelah JPEG, resize, dan crop"],
        ["results/A_Augmentation/comparison_grid.png", "Grid citra asli dan enam augmentasi"],
        ["results/B_Compression/comparison/visual_comparison.png", "Perbandingan visual citra asli dan JPEG"],
        ["results/B_Compression/graphs", "Grafik rasio kompresi dan penghematan ruang"],
        ["results/C_Watermarking/robustness_chart.png", "Grafik bit accuracy setelah serangan"],
        ["dataset/DAiSEE/selected_clips.csv", "Daftar 10 klip, label afektif, dan frame yang dipakai"],
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
