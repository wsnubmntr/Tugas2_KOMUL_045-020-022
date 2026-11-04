# Tugas 2 Komputasi Multimedia

Laporan ini membahas augmentasi data, kompresi citra, dan watermarking pada subset DAiSEE. Sepuluh klip dipilih dari split Train dengan seed 42 dan komposisi label 3 Boredom, 3 Engagement, 2 Confusion, dan 2 Frustration. Satu frame tengah diambil dari setiap klip sebagai citra uji.

## Isi folder

- `dataset/DAiSEE/frames`: sepuluh frame DAiSEE berukuran 640 x 480.
- `dataset/DAiSEE/selected_clips.csv`: daftar klip, subjek, label afektif, posisi frame, dan nama berkas.
- `data/compression_input`: input kompresi BMP, PNG, JPEG, dan SVG.
- `notebooks/Tugas_2_Komputasi_Multimedia.ipynb`: notebook utama.
- `prepare_daisee.py`: pengambil subset DAiSEE dan pengekstrak frame tengah.
- `pipeline.py`: skrip pipeline yang menjalankan seluruh eksperimen.
- `make_report.py`: pembuat laporan PDF dari berkas CSV dan gambar hasil pipeline.
- `results/laporan_tugas2.pdf`: laporan lengkap.
- `results/A_Augmentation`: frame asli, enam hasil augmentasi, dan grid perbandingan.
- `results/B_Compression`: berkas terkompresi, tabel CSV, grafik, dan perbandingan visual.
- `results/C_Watermarking`: citra ber-watermark, watermark hasil ekstraksi, grafik robustness, dan hasil uji robustness.
- `requirements.txt`: dependensi Python.

## Cara menjalankan

1. Aktifkan virtual environment.

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

2. Siapkan native Cairo untuk CairoSVG. Di Windows, CairoSVG membutuhkan `libcairo-2.dll`. Pipeline mencari DLL tersebut di `%GTK_RUNTIME%`, `%LOCALAPPDATA%\gtk3-runtime`, atau `.tools\gtk3-runtime`, lalu memakai subfolder `$_63_` atau `bin`.

   ```powershell
   $env:GTK_RUNTIME = "$env:LOCALAPPDATA\gtk3-runtime"
   ```

   Runtime GTK3 dapat berasal dari installer GTK3 resmi atau dari arsip yang diekstrak. Yang penting adalah keberadaan `libcairo-2.dll` dan folder `etc\fonts`.

3. Ambil subset DAiSEE. Arsip resmi berukuran sekitar 15 GB, sehingga skrip membaca hanya anggota arsip yang dibutuhkan dengan HTTP range.

   ```powershell
   .\.venv\Scripts\python.exe prepare_daisee.py
   ```

   Gunakan `--force` untuk mengambil ulang subset. Hasilnya sepuluh frame dan `dataset/DAiSEE/selected_clips.csv`.

4. Jalankan notebook dan pilih kernel `.venv (3.14.10)`.

   ```powershell
   jupyter notebook notebooks/Tugas_2_Komputasi_Multimedia.ipynb
   ```

5. Jalankan semua cell dari atas ke bawah.

Pipeline juga dapat dijalankan tanpa notebook.

```powershell
.\.venv\Scripts\python.exe pipeline.py
```

Setelah pipeline selesai, laporan PDF dapat dibangun ulang.

```powershell
.\.venv\Scripts\python.exe make_report.py
```

`make_report.py` membaca `compression_results.csv`, `watermark_metrics.csv`, `watermark_extraction.csv`, `robustness_results.csv`, dan `selected_clips.csv`. Jalankan pipeline terlebih dahulu agar angka dan gambar yang dipakai laporan sesuai.

## Metode

- Dataset: subset DAiSEE dari split Train, 10 klip dari 10 subjek berbeda, stratified per label afektif dengan seed 42. Populasi DAiSEE berisi 9.068 klip dan 112 pengguna.
- Augmentasi: horizontal flip, rotasi 10 derajat, crop 80% lalu resize, brightness/contrast, Gaussian noise, dan Gaussian blur. Semua transformasi diterapkan pada frame 640 x 480.
- Kompresi: RLE, Huffman, dan JPEG/DCT dengan kualitas 85. Citra uji 256 x 256 diperoleh dari crop persegi di tengah frame, lalu diperkecil dengan interpolasi area.
- Rasterisasi SVG: CairoSVG 2.9.1 menjadi PNG 256 x 256.
- Watermarking: visible watermark dan invisible LSB. Robustness diuji dengan JPEG kualitas 70, resize, dan crop.

## Keluaran eksperimen

- `results/B_Compression/compression_results.csv`: ukuran input, baseline, output, perbandingan input:output, compression ratio, space saving, PSNR, SSIM, waktu kompresi, dan waktu dekompresi.
- `results/C_Watermarking/watermark_metrics.csv`: PSNR dan SSIM visible serta invisible watermark.
- `results/C_Watermarking/watermark_extraction.csv`: bit accuracy ekstraksi awal.
- `results/C_Watermarking/robustness_results.csv`: bit accuracy setelah JPEG, resize, dan crop.
- `results/B_Compression/graphs`: grafik rasio kompresi dan penghematan ruang.
- `results/C_Watermarking/robustness_chart.png`: grafik bit accuracy setelah serangan.
- `results/B_Compression/comparison/visual_comparison.png`: perbandingan visual frame asli dan hasil JPEG.
- `results/C_Watermarking/comparison_before_after.png`: perbandingan citra asli, visible watermark, dan invisible watermark.

Nilai PSNR `inf` pada CSV berarti rekonstruksi lossless. Laporan menampilkannya sebagai "tak hingga".

## Catatan metodologi

- Baseline ukuran RLE dan Huffman adalah byte piksel mentah `h x w x c`.
- Baseline JPEG/DCT adalah ukuran berkas input.
- Perbedaan baseline disengaja dan dijelaskan pada laporan.
- Ukuran output RLE mencakup header 16 byte. Ukuran output Huffman mencakup codebook, metadata, padding, dan overhead pickle.
- PSNR dan SSIM dihitung antara citra asli dan citra hasil decoding.
- SVG dirasterisasi dengan CairoSVG sebelum dibandingkan dengan metode piksel.
- Baris `SVG_raster` memakai `input_svg_raster.png` berukuran 9.318 byte, bukan `input.svg` berukuran 523 byte.
- Payload LSB berisi 4.096 bit dan menempati 4.096 piksel biru pertama, yaitu 16 baris teratas citra.
- Kompresi dan watermarking memakai satu citra uji 256 x 256. Hasil berlaku untuk citra tersebut, bukan rata-rata populasi.
- Setiap klip diwakili satu frame pada posisi tengah. Frame pada posisi lain dapat menunjukkan ekspresi dan pose yang berbeda.

## Referensi utama

1. R. C. Gonzalez and R. E. Woods, *Digital Image Processing*, 4th ed. Pearson, 2018.
2. J. F. Hughes et al., *Computer Graphics: Principles and Practice*, 3rd ed. Addison-Wesley, 2014.
3. A. Gupta et al., "DAiSEE: Towards User Engagement Recognition in the Wild," arXiv:1609.01885, 2016.
4. S. Porcu, A. Floris, and L. Atzori, "Evaluation of Data Augmentation Techniques for Facial Expression Recognition Systems," *Electronics*, vol. 9, no. 11, art. 1892, 2020.
5. CairoSVG, "CairoSVG: SVG to PDF and PNG converter," version 2.9.1, https://cairosvg.org/.
