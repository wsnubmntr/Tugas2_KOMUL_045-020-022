"""Ambil subset kecil DAiSEE untuk eksperimen augmentasi."""
from pathlib import Path
import argparse
import csv
import random
import tempfile

import cv2
import requests
from remotezip import RemoteZip

ROOT = Path(__file__).resolve().parent
DAISEE = ROOT / "dataset" / "DAiSEE"
FRAMES = DAISEE / "frames"
MANIFEST = DAISEE / "selected_clips.csv"
KAGGLE_URL = "https://www.kaggle.com/api/v1/datasets/download/olgaparfenova/daisee"
SPLIT = "Train"
SEED = 42
LABELS = ["Boredom", "Engagement", "Confusion", "Frustration"]
TARGET = {"Boredom": 3, "Engagement": 3, "Confusion": 2, "Frustration": 2}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}


def signed_archive_url():
    response = requests.get(
        KAGGLE_URL,
        headers=HEADERS,
        stream=True,
        timeout=60,
        allow_redirects=False,
    )
    if response.status_code != 302:
        raise RuntimeError(
            f"Kaggle tidak memberi tautan arsip, status {response.status_code}."
        )
    url = response.headers.get("Location")
    response.close()
    if not url:
        raise RuntimeError("Tautan arsip DAiSEE kosong.")
    return url


def baca_label(archive):
    data = archive.read("DAiSEE/Labels/TrainLabels.csv").decode("utf-8-sig")
    rows = []
    for row in csv.DictReader(data.splitlines(), skipinitialspace=True):
        bersih = {k.strip(): v.strip() for k, v in row.items()}
        bersih["ClipID"] = bersih["ClipID"].replace(".avi", "")
        for label in LABELS:
            bersih[label] = int(bersih[label])
        bersih["SubjectID"] = bersih["ClipID"][:6]
        bersih["Dominan"] = max(LABELS, key=lambda k: bersih[k])
        rows.append(bersih)
    return rows


def pilih_klip(rows):
    rng = random.Random(SEED)
    per_label = {label: {} for label in LABELS}
    for row in rows:
        per_label[row["Dominan"]].setdefault(row["SubjectID"], []).append(row)

    terpakai = set()
    terpilih = []
    for label in LABELS:
        subjek = sorted(per_label[label])
        rng.shuffle(subjek)
        for subject in subjek:
            if len([row for row in terpilih if row["Dominan"] == label]) >= TARGET[label]:
                break
            if subject in terpakai:
                continue
            kandidat = sorted(per_label[label][subject], key=lambda row: row["ClipID"])
            terpilih.append(rng.choice(kandidat))
            terpakai.add(subject)

    if len(terpilih) != sum(TARGET.values()):
        raise RuntimeError("Klip DAiSEE tidak cukup untuk komposisi label yang diminta.")

    urutan = []
    for label in LABELS:
        urutan.extend(row for row in terpilih if row["Dominan"] == label)
    return urutan


def ambil_frame(archive, row, nomor, kerja):
    clip = row["ClipID"]
    subject = row["SubjectID"]
    anggota = f"DAiSEE/DataSet/{SPLIT}/{subject}/{clip}/{clip}.avi"
    data = archive.read(anggota)
    video = kerja / f"{clip}.avi"
    video.write_bytes(data)

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Video tidak dapat dibuka: {clip}")
    jumlah = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if jumlah < 1:
        cap.release()
        raise RuntimeError(f"Video tidak memiliki frame: {clip}")
    posisi = jumlah // 2
    cap.set(cv2.CAP_PROP_POS_FRAMES, posisi)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Frame tengah tidak terbaca: {clip}")

    nama = f"gambar_{nomor:02d}_{clip}.png"
    cv2.imwrite(str(FRAMES / nama), frame)
    row["Frame"] = posisi
    row["Berkas"] = nama
    return row


def tulis_manifest(rows):
    kolom = [
        "Urutan",
        "ClipID",
        "SubjectID",
        "Boredom",
        "Engagement",
        "Confusion",
        "Frustration",
        "Dominan",
        "Frame",
        "Berkas",
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=kolom)
        writer.writeheader()
        for nomor, row in enumerate(rows, start=1):
            row["Urutan"] = nomor
            writer.writerow({k: row[k] for k in kolom})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Ambil ulang subset DAiSEE.")
    args = parser.parse_args()

    if MANIFEST.exists() and len(list(FRAMES.glob("*.png"))) == 10 and not args.force:
        print("Subset DAiSEE sudah ada. Pakai --force untuk mengambil ulang.")
        return

    FRAMES.mkdir(parents=True, exist_ok=True)
    for path in FRAMES.glob("*.png"):
        path.unlink()

    url = signed_archive_url()
    with tempfile.TemporaryDirectory(prefix="daisee_") as tmp:
        kerja = Path(tmp)
        with RemoteZip(url) as archive:
            rows = pilih_klip(baca_label(archive))
            hasil = [
                ambil_frame(archive, row, nomor, kerja)
                for nomor, row in enumerate(rows, start=1)
            ]
    tulis_manifest(hasil)

    print("Subset DAiSEE selesai.")
    for row in hasil:
        print(
            row["Urutan"],
            row["ClipID"],
            row["SubjectID"],
            row["Dominan"],
            row["Berkas"],
        )


if __name__ == "__main__":
    main()
