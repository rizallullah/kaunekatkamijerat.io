# KAU NEKAT KAMI JERAT (JERAT)
# Streamlit implementation based on "New Fix Real 100% Final Project JERAT.py"
# Run: streamlit run app.py

import streamlit as st

st.set_page_config(page_title="JERAT | Audit Lingkungan", page_icon="⚖️", layout="wide")

# -----------------------------------------------------------------------------
# DATA ACUAN DARI PROGRAM PYTHON SUMBER
# -----------------------------------------------------------------------------
ZAT_AIR = {
    "Nikel": {
        "nama": ["Ni (Nikel)", "Co (Kobalt)", "Cr6+ (Kromium heksavalen)", "Pb (Timbal)"],
        "batas": [0.1, 0.5, 0.2, 0.1],
    },
    "Batu Bara": {
        "nama": ["Fe (Besi)", "Mn (Mangan)", "SO4 (Sulfat)", "Pb (Timbal)"],
        "batas": [0.3, 0.4, 250, 0.1],
    },
}

# Kode parameter, nama, dan empat batas konsentrasi sesuai program sumber.
PARAMETER_ISPU = [
    ("PM10", "Partikulat PM10", 50, 150, 350, 420),
    ("PM2.5", "Partikulat PM2.5", 15.5, 55.4, 150.4, 250.4),
    ("SO2", "Sulfur Dioksida (SO₂)", 52, 180, 400, 800),
    ("CO", "Karbon Monoksida (CO)", 4000, 8000, 15000, 30000),
    ("O3", "Ozon Permukaan (O₃)", 120, 235, 400, 800),
    ("NO2", "Nitrogen Dioksida (NO₂)", 80, 200, 1130, 2260),
    ("HC", "Hidrokarbon (HC)", 45, 100, 215, 432),
]

PARAMETER_TANAH = {
    "Nikel": [("Ni", "ni", 0.5, 2.1), ("Co", "co", 0.3, 2.4), ("Cr6+", "cr6", 0.075, 0.25)],
    "Batu Bara": [("Fe", "fe", 100, 250), ("Mn", "mn", 5, 18), ("SO₄", "so4", 1.5, 3)],
}


def nilai(d, key, default=0.0):
    """Ambil angka dari dictionary input Streamlit dan validasi nilainya."""
    try:
        result = float(d.get(key, default))
    except (TypeError, ValueError):
        raise ValueError(f"Nilai {key} harus berupa angka.")
    return result


def ya_tidak(d, key):
    value = str(d.get(key, "")).strip().lower()
    if value not in ("ya", "tidak"):
        raise ValueError("Lengkapi seluruh pertanyaan Ya/Tidak.")
    return value


def kategori_ispu(total):
    if total <= 50:
        return "Baik"
    if total <= 100:
        return "Sedang"
    if total <= 200:
        return "Tidak Sehat"
    if total <= 300:
        return "Sangat Tidak Sehat"
    return "Berbahaya"


# -----------------------------------------------------------------------------
# 1. PEMERIKSAAN KUALITAS AIR — IKA
# -----------------------------------------------------------------------------
def hitung_air(d):
    tambang = d["tambang"]
    if tambang not in ZAT_AIR:
        raise ValueError("Pilih jenis tambang Nikel atau Batu Bara.")

    keruh, warna, bau = (ya_tidak(d, k) for k in ("keruh", "warna", "bau"))
    poin = sum(x == "ya" for x in (keruh, warna, bau))
    pengamatan = ["Air Layak Guna", "Air Cukup Layak Guna", "Air Kurang Layak Guna", "Air Tidak Layak Guna"][poin]
    lanjut = ya_tidak(d, "lanjut")

    hasil = {"tambang": tambang, "pengamatan": pengamatan, "lanjut": lanjut}
    if lanjut == "tidak":
        hasil.update({"ika": None, "kategori": pengamatan, "awal_saja": True})
        return hasil

    jarak = nilai(d, "jarak")
    volume = nilai(d, "volume")
    ph = nilai(d, "ph")
    ntu = nilai(d, "ntu")
    tcu = nilai(d, "tcu")
    if jarak < 0 or volume <= 0 or not 0 <= ph <= 14 or ntu < 0 or tcu <= 0:
        raise ValueError("Jarak harus ≥ 0, volume > 0, pH 0–14, NTU ≥ 0, dan TCU > 0.")

    ika = -20 if jarak <= 0.5 else (-10 if jarak <= 1 else 10)
    if 6.5 < ph < 8.5:
        status_ph, skor_ph = "pH Ideal, Layak Guna", 20
    elif 5.5 < ph <= 6.5 or 8.5 <= ph < 9.5:
        status_ph, skor_ph = "Sedikit Asam/Basa, Masih Layak", 20
    elif 3.5 < ph <= 5.5 or 9.5 <= ph < 11.5:
        status_ph, skor_ph = "Asam/Basa, Kurang Layak", 10
    elif 2 < ph <= 3.5 or 11.5 <= ph < 13:
        status_ph, skor_ph = "Asam/Basa Kuat, Tidak Layak", -10
    else:
        status_ph, skor_ph = "Sangat Asam/Basa, Berbahaya", -20
    ika += skor_ph
    ph_berbahaya = ph <= 3.5 or ph >= 11.5

    if ntu <= 1:
        status_ntu, skor_ntu = "Air Sangat Jernih", 20
    elif ntu <= 5:
        status_ntu, skor_ntu = "Sedikit Keruh, Masih Layak", 20
    elif ntu <= 25:
        status_ntu, skor_ntu = "Layak guna, tak layak minum", 10
    else:
        status_ntu, skor_ntu = "Tidak layak guna", 0
    ika += skor_ntu

    # Skor TCU mengikuti algoritma aktual pada file sumber (+10, +10, 0, 0).
    if tcu <= 5:
        status_tcu, skor_tcu = "Air Jernih/Tak Berwarna", 10
    elif tcu <= 15:
        status_tcu, skor_tcu = "Sedikit Berwarna, Masih Layak", 10
    elif tcu <= 50:
        status_tcu, skor_tcu = "Berwarna Sedang, Tak Layak Minum", 0
    else:
        status_tcu, skor_tcu = "Tidak Layak Guna", 0
    ika += skor_tcu

    daftar_zat, total_massa, ada_melebihi = [], 0.0, False
    acuan = ZAT_AIR[tambang]
    for i, nama in enumerate(acuan["nama"]):
        massa = nilai(d, f"massa{i}")
        if massa < 0:
            raise ValueError("Massa zat terlarut tidak boleh negatif.")
        total_massa += massa
        konsentrasi = massa / volume
        layak = konsentrasi <= acuan["batas"][i]
        daftar_zat.append({"Zat": nama, "Konsentrasi (mg/L)": round(konsentrasi, 4), "Batas (mg/L)": acuan["batas"][i], "Status": "Layak Guna" if layak else "Melebihi Batas"})
        if layak:
            ika += 10
        else:
            ada_melebihi = True

    skor_sebelum_nol = ika
    if ada_melebihi:
        ika = 0

    tds = total_massa / volume
    if tds < 100:
        status_tds = "Sangat Rendah"
    elif tds < 300:
        status_tds = "Sangat Baik (Ideal)"
    elif tds < 600:
        status_tds = "Baik"
    elif tds < 1000:
        status_tds = "Sedang"
    elif tds <= 3000:
        status_tds = "Buruk"
    else:
        status_tds = "Sangat Buruk"

    if ph_berbahaya:
        kategori = "AIR TIDAK LAYAK GUNA (pH berbahaya)"
    elif ntu > 25:
        kategori = "AIR TIDAK LAYAK GUNA (NTU > 25)"
    elif tcu > 50:
        kategori = "AIR TIDAK LAYAK GUNA (TCU > 50)"
    elif ada_melebihi:
        kategori = "AIR TIDAK LAYAK GUNA (ada zat melebihi batas)"
    elif ika >= 100:
        kategori = "AIR LAYAK DIGUNAKAN"
    elif ika >= 80:
        kategori = "AIR CUKUP LAYAK DIGUNAKAN"
    elif ika >= 60:
        kategori = "AIR KURANG LAYAK GUNA"
    else:
        kategori = "AIR TIDAK LAYAK GUNA"

    hasil.update({
        "awal_saja": False, "jarak": jarak, "volume": volume, "ph": ph, "ntu": ntu, "tcu": tcu,
        "status_ph": status_ph, "status_ntu": status_ntu, "status_tcu": status_tcu,
        "zat": daftar_zat, "tds": tds, "status_tds": status_tds, "ika": ika,
        "skor_sebelum_nol": skor_sebelum_nol, "ada_melebihi": ada_melebihi,
        "ph_berbahaya": ph_berbahaya, "kategori": kategori,
    })
    return hasil


# -----------------------------------------------------------------------------
# 2. AUDIT PERUSAHAAN DAN PERHITUNGAN AKUMULASI SANKSI
# -----------------------------------------------------------------------------
def hitung_audit(d):
    izin, limbah, suap = (ya_tidak(d, k) for k in ("izin", "limbah", "suap"))
    hektare = nilai(d, "hektare")
    korban = nilai(d, "korban")
    if hektare < 0 or korban < 0 or not korban.is_integer():
        raise ValueError("Luas kawasan tidak boleh negatif dan jumlah korban harus bilangan bulat ≥ 0.")
    hektare, korban = float(hektare), int(korban)

    dmin = dmax = pmin = pmaks = 0.0
    if izin == "tidak":
        dmin += 5; dmax += 100; pmin += 2; pmaks += 5
    if hektare > 1:
        dmin += 1.5; dmax += 5; pmin += 3; pmaks += 10
    # Koreksi salah rujuk variabel di kode sumber: kondisi kecelakaan memakai jumlah korban.
    if korban >= 1:
        dmin += 2 * korban; dmax += 9 * korban
    if limbah == "ya":
        dmin += 1; dmax += 5; pmin += 1; pmaks += 5
    if suap == "ya":
        dmin += 1; dmax += 5; pmin += 1; pmaks += 5
    return {"izin": izin, "hektare": hektare, "korban": korban, "limbah": limbah, "suap": suap,
            "dmin": dmin, "dmax": dmax, "pmin": pmin, "pmaks": pmaks}


def tentukan_pasal(audit, kategori_pencemaran):
    pasal = []
    if audit["izin"] == "tidak":
        pasal.append(("Izin usaha pertambangan", "Pasal 158 dan 161A UU Minerba — kegiatan pertambangan tanpa izin"))
    if audit["hektare"] > 1:
        pasal.append(("Pembukaan kawasan hutan", "Pasal 89 ayat (1) huruf a jo. Pasal 17 ayat (1) huruf b UU No. 18 Tahun 2013"))
    if audit["korban"] >= 1:
        pasal.append(("Kecelakaan kerja", "UU No. 4 Tahun 2009 jo. UU No. 3 Tahun 2020 tentang Pertambangan Mineral dan Batubara — perlu telaah ketentuan spesifik berdasarkan fakta kejadian"))
    if kategori_pencemaran == "Pelanggaran Berat":
        pasal.append(("Pencemaran lingkungan", "Pasal 98 ayat (1) dan/atau Pasal 99 ayat (1) UU No. 32 Tahun 2009 — perlu pembuktian unsur delik"))
    if audit["limbah"] == "ya":
        pasal.append(("Pengelolaan limbah", "Pasal 102–103 UU No. 32 Tahun 2009 sebagaimana diubah — perlu verifikasi ketentuan yang berlaku dan jenis pelanggaran"))
    if audit["suap"] == "ya":
        pasal.append(("Praktik suap/laporan fiktif", "Pasal 5 ayat (1) UU Tipikor — penerapan pasal bergantung pada unsur dan peran pihak terkait"))
    return pasal


# -----------------------------------------------------------------------------
# 3. PEMERIKSAAN KUALITAS UDARA — SKOR ISPU SIMULASI SESUAI PROGRAM SUMBER
# -----------------------------------------------------------------------------
def hitung_udara(d):
    rincian, total = [], 0
    for kode, nama, b1, b2, b3, b4 in PARAMETER_ISPU:
        konsentrasi = nilai(d, "u_" + kode)
        if konsentrasi < 0:
            raise ValueError(f"Konsentrasi {kode} tidak boleh negatif.")
        if konsentrasi <= b1:
            skor, rentang = 0, f"≤ {b1}"
        elif konsentrasi <= b2:
            skor, rentang = 15, f"> {b1} – {b2}"
        elif konsentrasi <= b3:
            skor, rentang = 30, f"> {b2} – {b3}"
        elif konsentrasi <= b4:
            skor, rentang = 50, f"> {b3} – {b4}"
        else:
            skor, rentang = 100, f"> {b4}"
        total += skor
        rincian.append({"Parameter": nama, "Konsentrasi (µg/m³)": konsentrasi, "Rentang skor": rentang, "Skor": skor})
    return {"total": total, "kategori": kategori_ispu(total), "rincian": rincian,
            "kritis": max(rincian, key=lambda x: x["Skor"])}


# -----------------------------------------------------------------------------
# 4. PEMERIKSAAN KUALITAS TANAH — INDEKS NEMEROW (Pn) SESUAI PROGRAM SUMBER
# -----------------------------------------------------------------------------
def hitung_tanah(d):
    pht, ec, corg, ktk, pb = (nilai(d, k) for k in ("pht", "ec", "corg", "ktk", "pb"))
    if not 0 <= pht <= 14 or min(ec, corg, ktk, pb) < 0 or corg > 100:
        raise ValueError("pH tanah harus 0–14, C-Organik 0–100%, dan parameter lain tidak boleh negatif.")
    pn = 0.0
    pn += 0.7 if pht <= 4.5 or pht > 9.5 else (0.2 if pht <= 5.5 or pht > 8.5 else 0)
    pn += 0 if ec <= 2 else (0.2 if ec <= 4 else 0.7)
    pn += 0.7 if corg <= 2 else (0.2 if corg <= 5 else 0)
    pn += 0.7 if ktk <= 5 else (0.2 if ktk <= 20 else 0)
    pn += 0 if pb <= 1.5 else (0.2 if pb <= 6 else 0.7)

    rincian = [
        {"Parameter": "pH tanah", "Nilai": pht, "Skor": 0.7 if pht <= 4.5 or pht > 9.5 else (0.2 if pht <= 5.5 or pht > 8.5 else 0)},
        {"Parameter": "Daya Hantar Listrik (dS/m)", "Nilai": ec, "Skor": 0 if ec <= 2 else (0.2 if ec <= 4 else 0.7)},
        {"Parameter": "C-Organik (%)", "Nilai": corg, "Skor": 0.7 if corg <= 2 else (0.2 if corg <= 5 else 0)},
        {"Parameter": "Kapasitas Tukar Kation (cmol/kg)", "Nilai": ktk, "Skor": 0.7 if ktk <= 5 else (0.2 if ktk <= 20 else 0)},
        {"Parameter": "Pb (g/kg)", "Nilai": pb, "Skor": 0 if pb <= 1.5 else (0.2 if pb <= 6 else 0.7)},
    ]
    for nama, key, batas1, batas2 in PARAMETER_TANAH[d["tambang"]]:
        val = nilai(d, key)
        if val < 0:
            raise ValueError(f"Nilai {nama} tidak boleh negatif.")
        skor = 0 if val <= batas1 else (0.2 if val <= batas2 else 0.7)
        pn += skor
        rincian.append({"Parameter": f"{nama} (g/kg)", "Nilai": val, "Skor": skor})

    if pn <= 0.7:
        kategori = "Bersih"
    elif pn <= 1:
        kategori = "Cukup Bersih"
    elif pn <= 2:
        kategori = "Tercemar Ringan"
    elif pn <= 3:
        kategori = "Tercemar Sedang"
    else:
        kategori = "Tercemar Berat"
    return {"pn": pn, "kategori": kategori, "rincian": rincian}


# -----------------------------------------------------------------------------
# TAMPILAN STREAMLIT
# -----------------------------------------------------------------------------
st.title("⚖️ KAU NEKAT KAMI JERAT")
st.caption("JARINGAN EVALUASI REGULASI DAN ATURAN TAMBANG")
st.subheader("JERAT — Evaluasi Dampak dan Kepatuhan Kegiatan Pertambangan")
st.write("Platform simulasi pemeriksaan kualitas air, kualitas udara, pencemaran tanah, serta kepatuhan perusahaan pertambangan.")
st.info("Isi data berdasarkan hasil pengamatan atau pengujian. Hasil aplikasi merupakan simulasi berbasis algoritma pada program sumber, bukan pengganti pengujian laboratorium atau penetapan hukum oleh pihak berwenang.")

menu = st.radio("Pilih jenis pemeriksaan", ["Pemeriksaan Terpadu", "Kualitas Air", "Kualitas Udara", "Kualitas Tanah", "Audit Perusahaan"], horizontal=True)


def form_air(prefix="air"):
    data = {}
    st.markdown("#### Identitas dan pengamatan awal")
    data["tambang"] = st.selectbox("Jenis tambang", ["Nikel", "Batu Bara"], key=prefix+"_tambang")
    c1, c2, c3 = st.columns(3)
    with c1: data["keruh"] = st.radio("Air terlihat keruh?", ["tidak", "ya"], format_func=lambda x: x.title(), key=prefix+"_keruh")
    with c2: data["warna"] = st.radio("Air terlihat berwarna?", ["tidak", "ya"], format_func=lambda x: x.title(), key=prefix+"_warna")
    with c3: data["bau"] = st.radio("Air berbau?", ["tidak", "ya"], format_func=lambda x: x.title(), key=prefix+"_bau")
    data["lanjut"] = st.radio("Lakukan observasi parameter lanjutan?", ["ya", "tidak"], format_func=lambda x: "Ya" if x == "ya" else "Tidak", horizontal=True, key=prefix+"_lanjut")
    if data["lanjut"] == "ya":
        st.markdown("#### Parameter fisik dan kimia air")
        c1, c2, c3 = st.columns(3)
        with c1: data["jarak"] = st.number_input("Jarak sumber air dari area tambang (km)", min_value=0.0, value=2.0, key=prefix+"_jarak")
        with c2: data["volume"] = st.number_input("Jumlah air observasi (liter)", min_value=0.000001, value=10.0, key=prefix+"_volume")
        with c3: data["ph"] = st.number_input("pH air", min_value=0.0, max_value=14.0, value=7.0, key=prefix+"_ph")
        c1, c2 = st.columns(2)
        with c1: data["ntu"] = st.number_input("Kekeruhan (NTU)", min_value=0.0, value=1.0, key=prefix+"_ntu")
        with c2: data["tcu"] = st.number_input("Warna (TCU)", min_value=0.000001, value=5.0, key=prefix+"_tcu")
        st.markdown("#### Massa zat terlarut")
        st.caption("Masukkan massa setiap zat dalam mg. Konsentrasi dihitung otomatis dalam mg/L = massa ÷ volume air.")
        cols = st.columns(4)
        for i, col in enumerate(cols):
            with col:
                nama = ZAT_AIR[data["tambang"]]["nama"][i]
                data[f"massa{i}"] = st.number_input(f"{nama} (mg)", min_value=0.0, value=0.0, key=f"{prefix}_massa{i}")
    return data


def form_udara(prefix="udara"):
    data = {}
    st.caption("Satuan konsentrasi: µg/m³. Skor total mengikuti penjumlahan skor parameter pada algoritma sumber.")
    cols = st.columns(2)
    for i, (kode, nama, *_batas) in enumerate(PARAMETER_ISPU):
        with cols[i % 2]:
            data["u_" + kode] = st.number_input(f"{nama} (µg/m³)", min_value=0.0, value=0.0, key=f"{prefix}_{kode}")
    return data


def form_tanah(tambang, prefix="tanah"):
    data = {"tambang": tambang}
    st.markdown("#### Parameter dasar tanah")
    cols = st.columns(2)
    dasar = [("pht", "pH tanah", 7.0, 14.0), ("ec", "Daya Hantar Listrik (dS/m)", 1.0, None),
             ("corg", "C-Organik (%)", 3.0, 100.0), ("ktk", "Kapasitas Tukar Kation (cmol/kg)", 10.0, None),
             ("pb", "Logam berat Pb (g/kg)", 1.0, None)]
    for i, (key, label, default, maximum) in enumerate(dasar):
        with cols[i % 2]:
            kwargs = {"min_value": 0.0, "value": default, "key": f"{prefix}_{key}"}
            if maximum is not None: kwargs["max_value"] = maximum
            data[key] = st.number_input(label, **kwargs)
    st.markdown("#### Logam tambahan berdasarkan jenis tambang")
    cols = st.columns(3)
    defaults = {"fe": 50.0, "mn": 2.0, "so4": 1.0, "ni": 0.2, "co": 0.2, "cr6": 0.05}
    for i, (nama, key, _b1, _b2) in enumerate(PARAMETER_TANAH[tambang]):
        with cols[i % 3]:
            data[key] = st.number_input(f"{nama} (g/kg)", min_value=0.0, value=defaults[key], key=f"{prefix}_{key}")
    return data


def form_audit(prefix="audit"):
    data = {}
    st.markdown("#### Kepatuhan dan pelanggaran perusahaan")
    c1, c2 = st.columns(2)
    with c1:
        data["izin"] = st.radio("Apakah perusahaan memiliki izin usaha pertambangan?", ["ya", "tidak"], format_func=lambda x: x.title(), key=prefix+"_izin")
        data["hektare"] = st.number_input("Luas kawasan hutan yang dibuka (hektare)", min_value=0.0, value=0.0, key=prefix+"_hektare")
        data["korban"] = st.number_input("Jumlah korban kecelakaan kerja", min_value=0, value=0, step=1, key=prefix+"_korban")
    with c2:
        data["limbah"] = st.radio("Adakah limbah yang dikelola tanpa izin?", ["tidak", "ya"], format_func=lambda x: x.title(), key=prefix+"_limbah")
        data["suap"] = st.radio("Adakah praktik suap/laporan keuangan fiktif?", ["tidak", "ya"], format_func=lambda x: x.title(), key=prefix+"_suap")
    return data


def tampilkan_air(r):
    st.markdown("### Hasil pemeriksaan kualitas air")
    if r["awal_saja"]:
        st.warning(f"{r['pengamatan']}. Pemeriksaan hanya berdasarkan pengamatan visual; belum termasuk uji laboratorium.")
        return
    st.metric("Indeks Kelayakan Air (IKA)", f"{r['ika']} / 100")
    st.write("**Kesimpulan:**", r["kategori"])
    st.write(f"Pengamatan awal: {r['pengamatan']} · Jenis tambang: {r['tambang']}")
    st.dataframe([
        {"Parameter": "pH", "Nilai": r["ph"], "Status": r["status_ph"]},
        {"Parameter": "Kekeruhan (NTU)", "Nilai": r["ntu"], "Status": r["status_ntu"]},
        {"Parameter": "Warna (TCU)", "Nilai": r["tcu"], "Status": r["status_tcu"]},
    ] + r["zat"] + [{"Parameter": "TDS total (mg/L)", "Nilai": round(r["tds"], 2), "Status": r["status_tds"]}], use_container_width=True, hide_index=True)


def tampilkan_udara(r):
    st.markdown("### Hasil pemeriksaan kualitas udara")
    st.metric("Skor ISPU simulasi", r["total"])
    st.write("**Kategori:**", r["kategori"])
    st.dataframe(r["rincian"], use_container_width=True, hide_index=True)


def tampilkan_tanah(r):
    st.markdown("### Hasil pemeriksaan kualitas tanah")
    st.metric("Indeks Pencemaran Nemerow (Pn)", f"{r['pn']:.2f}")
    st.write("**Kategori:**", r["kategori"])
    st.dataframe(r["rincian"], use_container_width=True, hide_index=True)


def tampilkan_audit(r):
    st.markdown("### Hasil audit perusahaan")
    c1, c2 = st.columns(2)
    c1.metric("Denda minimum", f"Rp {r['dmin']:,.2f} miliar")
    c2.metric("Denda maksimum", f"Rp {r['dmax']:,.2f} miliar")
    c1, c2 = st.columns(2)
    c1.metric("Pidana minimum", f"{r['pmin']:g} tahun")
    c2.metric("Pidana maksimum", f"{r['pmaks']:g} tahun")
    st.caption("Akumulasi ini mengikuti angka dan aturan hitung pada program sumber; bukan penetapan sanksi resmi. Penerapan pasal dan sanksi harus diverifikasi berdasarkan peraturan terbaru serta fakta hukum.")


if menu == "Pemeriksaan Terpadu":
    st.write("Lakukan seluruh pemeriksaan dalam satu formulir. Hasil air, udara, tanah, audit, dan identifikasi pasal akan dirangkum bersama.")
    with st.form("form_terpadu"):
        st.header("1. Kualitas Air")
        air_data = form_air("terpadu_air")
        st.divider(); st.header("2. Audit Perusahaan")
        audit_data = form_audit("terpadu_audit")
        st.divider(); st.header("3. Kualitas Udara")
        udara_data = form_udara("terpadu_udara")
        st.divider(); st.header("4. Kualitas Tanah")
        tanah_data = form_tanah(air_data["tambang"], "terpadu_tanah")
        submit = st.form_submit_button("Jalankan pemeriksaan terpadu", use_container_width=True, type="primary")
    if submit:
        try:
            air = hitung_air(air_data)
            audit = hitung_audit(audit_data)
            udara = hitung_udara(udara_data)
            tanah = hitung_tanah(tanah_data)
            air_tidak_layak = (not air["awal_saja"] and air["kategori"].startswith("AIR TIDAK LAYAK GUNA"))
            pencemaran_berat = tanah["kategori"] == "Tercemar Berat" or udara["kategori"] == "Berbahaya" or air_tidak_layak
            kategori_pencemaran = "Pelanggaran Berat" if pencemaran_berat else "Pelanggaran Ringan"
            pasal = tentukan_pasal(audit, kategori_pencemaran)
            st.session_state["hasil_terpadu"] = {"air": air, "audit": audit, "udara": udara, "tanah": tanah,
                                                   "kategori_pencemaran": kategori_pencemaran, "pasal": pasal}
        except (ValueError, KeyError) as e:
            st.error(str(e))

    if st.session_state.get("hasil_terpadu"):
        r = st.session_state["hasil_terpadu"]
        st.divider(); st.header("Laporan Hasil Pemeriksaan Terpadu")
        if r["kategori_pencemaran"] == "Pelanggaran Berat": st.error("Status lingkungan: PELANGGARAN BERAT")
        else: st.success("Status lingkungan: PELANGGARAN RINGAN berdasarkan kriteria program")
        with st.expander("Hasil kualitas air", expanded=True): tampilkan_air(r["air"])
        with st.expander("Hasil audit perusahaan", expanded=True):
            tampilkan_audit(r["audit"])
            if r["pasal"]:
                st.markdown("**Indikasi pasal yang perlu ditelaah:**")
                for nama, uraian in r["pasal"]: st.markdown(f"- **{nama}:** {uraian}")
            else: st.write("Tidak ada indikasi pasal berdasarkan jawaban audit yang dimasukkan.")
        with st.expander("Hasil kualitas udara", expanded=True): tampilkan_udara(r["udara"])
        with st.expander("Hasil kualitas tanah", expanded=True): tampilkan_tanah(r["tanah"])
        st.caption("Catatan: kategori pelanggaran berat mengikuti logika program sumber, yaitu air tidak layak guna, udara berbahaya, atau tanah tercemar berat. Jika pengamatan air hanya visual, data tersebut belum cukup untuk menyimpulkan kelayakan laboratorium.")

elif menu == "Kualitas Air":
    with st.form("form_air_individu"):
        data = form_air("ind_air")
        submit = st.form_submit_button("Hitung IKA", use_container_width=True, type="primary")
    if submit:
        try: st.session_state["hasil_air"] = hitung_air(data)
        except ValueError as e: st.error(str(e))
    if st.session_state.get("hasil_air"): tampilkan_air(st.session_state["hasil_air"])

elif menu == "Kualitas Udara":
    with st.form("form_udara_individu"):
        data = form_udara("ind_udara")
        submit = st.form_submit_button("Hitung skor ISPU", use_container_width=True, type="primary")
    if submit:
        try: st.session_state["hasil_udara"] = hitung_udara(data)
        except ValueError as e: st.error(str(e))
    if st.session_state.get("hasil_udara"): tampilkan_udara(st.session_state["hasil_udara"])

elif menu == "Kualitas Tanah":
    with st.form("form_tanah_individu"):
        tambang = st.selectbox("Jenis tambang", ["Nikel", "Batu Bara"], key="ind_tanah_tambang")
        data = form_tanah(tambang, "ind_tanah")
        submit = st.form_submit_button("Hitung indeks Pn", use_container_width=True, type="primary")
    if submit:
        try: st.session_state["hasil_tanah"] = hitung_tanah(data)
        except ValueError as e: st.error(str(e))
    if st.session_state.get("hasil_tanah"): tampilkan_tanah(st.session_state["hasil_tanah"])

else:
    with st.form("form_audit_individu"):
        data = form_audit("ind_audit")
        submit = st.form_submit_button("Hitung hasil audit", use_container_width=True, type="primary")
    if submit:
        try: st.session_state["hasil_audit"] = hitung_audit(data)
        except ValueError as e: st.error(str(e))
    if st.session_state.get("hasil_audit"):
        hasil = st.session_state["hasil_audit"]
        tampilkan_audit(hasil)
        st.markdown("**Pasal berdasarkan data audit saja:**")
        for nama, uraian in tentukan_pasal(hasil, "Pelanggaran Ringan"):
            st.markdown(f"- **{nama}:** {uraian}")

st.divider()
st.caption("KAU NEKAT KAMI JERAT · JERAT | Sistem simulasi evaluasi pertambangan berbasis parameter yang dimasukkan pengguna.")