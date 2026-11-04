# Tugas 2 Komputasi Multimedia

Laporan ini membahas augmentasi data, kompresi citra, dan watermarking pada subset DAiSEE. Sepuluh klip dipilih dari split Train dengan seed 42 dan komposisi label 3 Boredom, 3 Engagement, 2 Confusion, dan 2 Frustration. Satu frame tengah diambil dari setiap klip sebagai citra uji.

## Identitas

- Ataqah Ramadhan Widiyana Putra (105224022)
- Wisnu Bimantoro (105224045)
- Paulus R.A.S (105224020)

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

1. Buat dan aktifkan virtual environment, lalu instal dependensi.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

2. Siapkan native Cairo untuk CairoSVG. Di Windows, CairoSVG membutuhkan `libcairo-2.dll`. Pipeline mencari DLL tersebut di `%GTK_RUNTIME%`, `%LOCALAPPDATA%\gtk3-runtime`, atau `.tools\gtk3-runtime`, lalu memakai subfolder `$_63_` atau `bin`. Jika `data/compression_input/input_svg_raster.png` sudah tersedia, pipeline tetap dapat berjalan tanpa CairoSVG dengan memakai ulang raster tersebut.

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

- Dataset: subset DAiSEE dari split Train, 10 klip dari 10 subjek berbeda, stratified per label afektif dengan seed 42. Pemilihan acak dilakukan pada tingkat klip, sedangkan posisi frame ditetapkan di tengah video agar reproducible. Populasi DAiSEE berisi 9.068 klip dan 112 pengguna.
- Augmentasi: horizontal flip, rotasi 10 derajat, crop 80% lalu resize, brightness/contrast, Gaussian noise, dan Gaussian blur. Semua transformasi diterapkan pada frame 640 x 480.
- Kompresi: RLE, Huffman, dan JPEG/DCT dengan kualitas 85. Citra uji 256 x 256 diperoleh dari crop persegi di tengah frame, lalu diperkecil dengan interpolasi area.
- Rasterisasi SVG: CairoSVG 2.9.1 menjadi PNG 256 x 256.
- Watermarking: visible watermark dan invisible LSB. Robustness diuji dengan JPEG kualitas 70, resize, dan crop.

## Keluaran eksperimen

- `results/B_Compression/compression_results.csv`: ukuran input, baseline, output, perbandingan input:output, compression ratio, dua bentuk space saving, PSNR, SSIM, waktu kompresi, dan waktu dekompresi.
- `results/C_Watermarking/watermark_metrics.csv`: PSNR dan SSIM visible serta invisible watermark.
- `results/C_Watermarking/watermark_extraction.csv`: bit accuracy ekstraksi awal.
- `results/C_Watermarking/robustness_results.csv`: bit accuracy LSB setelah JPEG, resize, dan crop.
- `results/C_Watermarking/robustness_visible.csv`: NCC dan IoU visible watermark setelah tiga serangan.
- `results/B_Compression/graphs`: grafik rasio baseline, rasio berkas input:output, dan penghematan ruang.
- `results/C_Watermarking/robustness_chart.png`: grafik bit accuracy setelah serangan.
- `results/C_Watermarking/robustness_visible_grid.png`: grid visible watermark sebelum dan sesudah serangan.
- `results/B_Compression/comparison/visual_comparison.png`: perbandingan visual frame asli dan hasil JPEG.
- `results/C_Watermarking/comparison_before_after.png`: perbandingan citra asli, visible watermark, dan invisible watermark.

Nilai PSNR `inf` pada CSV berarti rekonstruksi lossless. Laporan menampilkannya sebagai "tak hingga".

## Catatan metodologi

- Baseline ukuran RLE dan Huffman adalah byte piksel mentah `h x w x c`.
- Baseline JPEG/DCT adalah ukuran berkas input.
- `Space saving (%)` mengikuti rumus tugas, yaitu `(1 - ukuran output / ukuran berkas input) x 100`.
- `Space saving baseline (%)` memakai byte piksel mentah dan dipakai untuk membandingkan metode pada data yang sama.
- Perbedaan baseline disengaja dan dijelaskan pada laporan.
- Ukuran output RLE mencakup header 16 byte. Ukuran output Huffman mencakup codebook, metadata, padding, dan overhead pickle.
- PSNR dan SSIM dihitung antara citra asli dan citra hasil decoding.
- SVG dirasterisasi dengan CairoSVG sebelum dibandingkan dengan metode piksel.
- Baris `SVG_raster` memakai `input_svg_raster.png` berukuran 9.318 byte, bukan `input.svg` berukuran 523 byte.
- Payload LSB berisi 4.096 bit dan menempati 4.096 piksel biru pertama, yaitu 16 baris teratas citra.
- Kompresi dan watermarking memakai satu citra uji 256 x 256. Hasil berlaku untuk citra tersebut, bukan rata-rata populasi.
- Setiap klip diwakili satu frame pada posisi tengah. Frame pada posisi lain dapat menunjukkan ekspresi dan pose yang berbeda.
- Notebook memakai potongan kode yang sama dengan `pipeline.py`; jalankan dari folder `notebooks/`.

## Penggunaan AI

Sesuai ketentuan tugas, penggunaan alat bantu AI dicantumkan secara terbuka.

- Alat: Command Code, asisten koding berbasis model bahasa besar yang berjalan di terminal.
- Peran: membantu menulis dan men-debug kode pipeline, menata outline dan struktur laporan, menyusun README, serta membantu mencari dan merangkum sumber referensi.
- Batas: seluruh kode dijalankan dan diperiksa penulis; angka laporan berasal dari eksekusi pipeline; setiap referensi diverifikasi terhadap sumber asli. Keputusan metodologi dan interpretasi hasil tetap menjadi tanggung jawab penulis.
- Orisinalitas: karya ini disusun secara orisinal dan penulis memahami seluruh bagian yang dibantu AI. Isi nama dan NIM pada cover laporan sebelum dikumpulkan.

## Referensi utama

Semua referensi di bawah dapat dibuka online; tautan PDF disertakan bila tersedia.

1. A. Gupta et al., "DAiSEE: Towards User Engagement Recognition in the Wild," arXiv:1609.01885, 2016. https://arxiv.org/pdf/1609.01885
2. S. Porcu, A. Floris, and L. Atzori, "Evaluation of Data Augmentation Techniques for Facial Expression Recognition Systems," *Electronics*, vol. 9, no. 11, art. 1892, 2020. https://www.mdpi.com/2079-9292/9/11/1892
3. G. K. Wallace, "The JPEG Still Picture Compression Standard," *IEEE Transactions on Consumer Electronics*, vol. 38, no. 1, 1992. https://www.ijg.org/files/Wallace.JPEG.pdf
4. W. Bender et al., "Techniques for Data Hiding," *IBM Systems Journal*, vol. 35, no. 3.4, pp. 313-336, 1996. https://people.sugarlabs.org/walter/techniques-for-data-hiding.pdf
5. Google, "WebP Compression," https://developers.google.com/speed/webp/docs/compression
6. Z. Wang et al., "Image Quality Assessment: From Error Visibility to Structural Similarity," *IEEE Transactions on Image Processing*, vol. 13, no. 4, pp. 600-612, 2004. https://ece.uwaterloo.ca/~z70wang/publications/ssim.pdf
7. D. A. Huffman, "A Method for the Construction of Minimum-Redundancy Codes," *Proceedings of the IRE*, vol. 40, no. 9, pp. 1098-1101, 1952. https://compression.ru/download/articles/huff/huffman_1952_minimum-redundancy-codes.pdf
8. CairoSVG, "CairoSVG: SVG to PDF and PNG converter," version 2.9.1, https://cairosvg.org/
9. J. J. Rissanen and G. G. Langdon, "Arithmetic Coding," *IBM Journal of Research and Development*, vol. 23, no. 2, pp. 149-162, 1979. http://bitsavers.informatik.uni-stuttgart.de/pdf/ibm/IBM_Journal_of_Research_and_Development/232/ibmrd2302G.pdf
10. T. A. Welch, "A Technique for High-Performance Data Compression," *Computer*, vol. 17, no. 6, pp. 8-19, 1984. https://courses.cs.duke.edu/spring03/cps296.5/papers/welch_1984_technique_for.pdf
11. P. Deutsch, "DEFLATE Compressed Data Format Specification version 1.3," RFC 1951, 1996. https://www.rfc-editor.org/info/rfc1951/
12. A. Skodras et al., "The JPEG 2000 Still Image Compression Standard," *IEEE Signal Processing Magazine*, vol. 18, no. 5, pp. 36-58, 2001. https://infoscience.epfl.ch/record/111813
13. R. M. Gray, "Vector Quantization," *IEEE ASSP Magazine*, vol. 1, no. 2, pp. 4-29, 1984. https://ntrs.nasa.gov/api/citations/19890012969/downloads/19890012969.pdf
14. M. Mahoney, *Data Compression Explained*, 2013. https://mattmahoney.net/dc/dce.html
15. F. A. P. Petitcolas et al., "Information Hiding: A Survey," *Proceedings of the IEEE*, vol. 87, no. 7, pp. 1062-1078, 1999. https://www.petitcolas.net/fabien/publications/ieee99-infohiding.pdf
16. N. Pourshab and M. Bagheritabar, "Accelerating Fractal Image Compression Using Search Pruning and Fractal Dimension Gating," arXiv:2507.06325, 2025. doi: 10.48550/arXiv.2507.06325. https://arxiv.org/pdf/2507.06325
