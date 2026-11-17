# KAU NEKAT KAMI JERAT (JERAT)
# Aplikasi web berbasis Python + Streamlit.
# Jalankan lokal: streamlit run app.py

import streamlit as st

ZAT_AIR = {
    "1": {
        "nama": ["Ni (Nikel)", "Co (Kobalt)", "Cr6+ (Kromium heksavalen)", "Pb (Timbal)"],
        "batas": [0.1, 0.5, 0.2, 0.1],
    },
    "2": {
        "nama": ["Fe (Besi)", "Mn (Mangan)", "SO4 (Sulfat)", "Pb (Timbal)"],
        "batas": [0.3, 0.4, 250, 0.1],
    },
}

PU = [
    ("PM10", "Partikulat PM10", 50, 150, 350, 420),
    ("PM2.5", "Partikulat PM2.5", 15.5, 55.4, 150.4, 250.4),
    ("SO2", "Sulfur Dioksida (SO2)", 52, 180, 400, 800),
    ("CO", "Karbon Monoksida (CO)", 4000, 8000, 15000, 30000),
    ("O3", "Ozon Permukaan (O3)", 120, 235, 400, 800),
    ("NO2", "Nitrogen Dioksida (NO2)", 80, 200, 1130, 2260),
    ("HC", "Hidrokarbon (HC)", 45, 100, 215, 432),
]

def angka(data, nama, default=0.0):
    try:
        return float(data.get(nama, [str(default)])[0])
    except (ValueError, TypeError, IndexError):
        raise ValueError("Periksa kembali isian angka pada " + nama + ".")

def pilihan(data, nama):
    return data.get(nama, [""])[0].strip().lower()

def kategori_ispu(nilai):
    if nilai <= 50:
        return "Baik", "ok"
    if nilai <= 100:
        return "Sedang", "blue"
    if nilai <= 200:
        return "Tidak Sehat", "mid"
    if nilai <= 300:
        return "Sangat Tidak Sehat", "bad"
    return "Berbahaya", "dark"

def hitung_air(d):
    jenis = pilihan(d, "tambang")
    if jenis not in ("1", "2"):
        raise ValueError("Pilih jenis tambang terlebih dahulu.")
    nama_tambang = "Nikel" if jenis == "1" else "Batu Bara"

    keruh, warna, bau = (pilihan(d, x) for x in ("keruh", "warna", "bau"))
    if any(x not in ("ya", "tidak") for x in (keruh, warna, bau)):
        raise ValueError("Lengkapi pengamatan awal dengan pilihan Ya atau Tidak.")
    poin = sum(x == "ya" for x in (keruh, warna, bau))
    hasil_awal = [
        "Air Layak Guna", "Air Cukup Layak Guna",
        "Air Kurang Layak Guna", "Air Tidak Layak Guna"
    ][poin]

    lanjut = pilihan(d, "lanjut")
    if lanjut not in ("ya", "tidak"):
        raise ValueError("Pilih apakah ingin melakukan observasi lebih lanjut.")
    hasil = {"jenis": nama_tambang, "awal": hasil_awal}
    if lanjut == "tidak":
        hasil.update({"sum": hasil_awal, "awal_saja": True})
        return hasil

    jarak = angka(d, "jarak")
    volume = angka(d, "volume")
    ph = angka(d, "ph")
    ntu = angka(d, "ntu")
    tcu = angka(d, "tcu")
    if jarak < 0 or volume <= 0 or not 0 <= ph <= 14 or ntu < 0 or tcu <= 0:
        raise ValueError("Jarak harus ≥ 0, volume > 0, pH 0–14, NTU ≥ 0, dan TCU > 0.")

    ika = -20 if jarak <= 0.5 else (-10 if jarak <= 1 else 10)
    if 6.5 < ph < 8.5:
        status_ph, skor = "pH Ideal, Layak Guna", 20
    elif (5.5 < ph <= 6.5) or (8.5 <= ph < 9.5):
        status_ph, skor = "Sedikit Asam/Basa, Masih Layak", 20
    elif (3.5 < ph <= 5.5) or (9.5 <= ph < 11.5):
        status_ph, skor = "Asam/Basa, Kurang Layak", 10
    elif (2 < ph <= 3.5) or (11.5 <= ph < 13):
        status_ph, skor = "Asam/Basa Kuat, Tidak Layak", -10
    else:
        status_ph, skor = "Sangat Asam/Basa, Berbahaya", -20
    ika += skor
    ph_bahaya = ph <= 3.5 or ph >= 11.5

    if ntu <= 1:
        status_ntu, skor_ntu = "Air Sangat Jernih", 20
    elif ntu <= 5:
        status_ntu, skor_ntu = "Sedikit Keruh, Masih Layak", 20
    elif ntu <= 25:
        status_ntu, skor_ntu = "Layak guna, tak layak minum", 10
    else:
        status_ntu, skor_ntu = "Tidak layak guna", 0
    ika += skor_ntu

    if tcu <= 5:
        status_tcu, skor_tcu = "Air Jernih/Tak Berwarna", 10
    elif tcu <= 15:
        status_tcu, skor_tcu = "Sedikit Berwarna, Masih Layak", 10
    elif tcu <= 50:
        status_tcu, skor_tcu = "Berwarna Sedang, Tak Layak Minum", 0
    else:
        status_tcu, skor_tcu = "Tidak Layak Guna", 0
    ika += skor_tcu

    zat = ZAT_AIR[jenis]
    daftar_zat = []
    total_massa = 0
    ada_melebihi = False
    for i, nama in enumerate(zat["nama"]):
        massa = angka(d, "massa" + str(i))
        if massa < 0:
            raise ValueError("Massa zat tidak boleh negatif.")
        total_massa += massa
        kons = massa / volume
        layak = kons <= zat["batas"][i]
        daftar_zat.append({
            "nama": nama, "kons": kons, "batas": zat["batas"][i], "layak": layak
        })
        if layak:
            ika += 10
        else:
            ada_melebihi = True

    skor_awal = ika
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

    if ph_bahaya:
        kategori = "AIR TIDAK LAYAK GUNA (pH berbahaya)"
        kelas = "bad"
    elif ntu > 25:
        kategori, kelas = "AIR TIDAK LAYAK GUNA (NTU > 25)", "bad"
    elif tcu > 50:
        kategori, kelas = "AIR TIDAK LAYAK GUNA (TCU > 50)", "bad"
    elif ada_melebihi:
        kategori, kelas = "AIR TIDAK LAYAK GUNA (ada zat melebihi batas)", "bad"
    elif ika >= 100:
        kategori, kelas = "AIR LAYAK DIGUNAKAN", "ok"
    elif ika >= 80:
        kategori, kelas = "AIR CUKUP LAYAK DIGUNAKAN", "ok"
    elif ika >= 60:
        kategori, kelas = "AIR KURANG LAYAK GUNA", "mid"
    else:
        kategori, kelas = "AIR TIDAK LAYAK GUNA", "bad"

    hasil.update({
        "sum": "IKA " + str(ika) + " / 100 · " + kategori,
        "awal_saja": False, "volume": volume, "jarak": jarak,
        "ph": ph, "ntu": ntu, "tcu": tcu, "status_ph": status_ph,
        "status_ntu": status_ntu, "status_tcu": status_tcu,
        "zat": daftar_zat, "tds": tds, "status_tds": status_tds,
        "ika": ika, "kategori": kategori, "kelas": kelas,
        "skor_awal": skor_awal, "ada_melebihi": ada_melebihi,
    })
    return hasil

def hitung_udara(d):
    hasil_parameter = []
    for kode, nama, b1, b2, b3, b4 in PU:
        nilai = angka(d, "u_" + kode)
        if nilai < 0:
            raise ValueError("Konsentrasi " + kode + " tidak boleh negatif.")
        if nilai <= b1:
            skor = 0
        elif nilai <= b2:
            skor = 15
        elif nilai <= b3:
            skor = 30
        elif nilai <= b4:
            skor = 50
        else:
            skor = 100
        hasil_parameter.append({"kode": kode, "nama": nama, "nilai": nilai, "skor": skor})
    # Mengikuti struktur penilaian program: jumlah skor parameter, bukan rata-rata.
    total = sum(x["skor"] for x in hasil_parameter)
    kategori, kelas = kategori_ispu(total)
    kritis = max(hasil_parameter, key=lambda x: x["skor"])
    return {
        "sum": "ISPU " + str(total) + " · " + kategori,
        "total": total, "kategori": kategori, "kelas": kelas,
        "kritis": kritis, "parameter": hasil_parameter,
    }

def hitung_tanah(d):
    pn = 0.0
    pht = angka(d, "pht")
    ec = angka(d, "ec")
    corg = angka(d, "corg")
    ktk = angka(d, "ktk")
    pb = angka(d, "pb")
    if not 0 <= pht <= 14 or min(ec, corg, ktk, pb) < 0:
        raise ValueError("Periksa rentang pH tanah dan pastikan semua nilai lainnya tidak negatif.")
    pn += 0.7 if pht <= 4.5 or pht > 9.5 else (0.2 if pht <= 5.5 or pht <= 9.5 and pht > 8.5 else 0)
    pn += 0 if ec <= 2 else (0.2 if ec <= 4 else 0.7)
    pn += 0.7 if corg <= 2 else (0.2 if corg <= 5 else 0)
    pn += 0.7 if ktk <= 5 else (0.2 if ktk <= 20 else 0)
    pn += 0 if pb <= 1.5 else (0.2 if pb <= 6 else 0.7)

    jenis = pilihan(d, "tambang")
    tambahan = []
    if jenis == "2":
        parameter = [
            ("Fe", "fe", 100, 250), ("Mn", "mn", 5, 18), ("SO4", "so4", 1.5, 3)
        ]
    elif jenis == "1":
        parameter = [
            ("Ni", "ni", 0.5, 2.1), ("Co", "co", 0.3, 2.4), ("Cr6+", "cr6", 0.075, 0.25)
        ]
    else:
        raise ValueError("Pilih jenis tambang untuk menentukan parameter logam tanah.")
    for nama, kunci, batas1, batas2 in parameter:
        nilai = angka(d, kunci)
        if nilai < 0:
            raise ValueError("Nilai " + nama + " tidak boleh negatif.")
        skor = 0 if nilai <= batas1 else (0.2 if nilai <= batas2 else 0.7)
        pn += skor
        tambahan.append((nama, nilai, skor))
    if pn <= 0.7:
        kategori, kelas = "Bersih", "ok"
    elif pn <= 1:
        kategori, kelas = "Cukup Bersih", "blue"
    elif pn <= 2:
        kategori, kelas = "Tercemar Ringan", "mid"
    elif pn <= 3:
        kategori, kelas = "Tercemar Sedang", "bad"
    else:
        kategori, kelas = "Tercemar Berat", "dark"
    return {
        "sum": "Pn " + format(pn, ".2f") + " · " + kategori,
        "pn": pn, "kategori": kategori, "kelas": kelas,
        "pht": pht, "ec": ec, "corg": corg, "ktk": ktk, "pb": pb,
        "tambahan": tambahan,
    }

def hitung_audit(d):
    izin = pilihan(d, "izin")
    limbah = pilihan(d, "limbah")
    suap = pilihan(d, "suap")
    if any(x not in ("ya", "tidak") for x in (izin, limbah, suap)):
        raise ValueError("Jawab seluruh pertanyaan audit dengan Ya atau Tidak.")
    hektare = angka(d, "hektare")
    korban = angka(d, "korban")
    if hektare < 0 or korban < 0:
        raise ValueError("Luas hutan dan jumlah korban tidak boleh negatif.")
    dmin = dmax = pmin = pmaks = 0
    if izin == "tidak":
        dmin += 5; dmax += 100; pmin += 2; pmaks += 5
    if hektare > 1:
        dmin += 1.5; dmax += 5; pmin += 3; pmaks += 10
    if korban > 0:
        dmin += 2 * korban; dmax += 9 * korban
    if limbah == "ya":
        dmin += 1; dmax += 5; pmin += 1; pmaks += 5
    if suap == "ya":
        dmin += 1; dmax += 5; pmin += 1; pmaks += 5
    return {
        "sum": "Audit selesai", "dmin": dmin, "dmax": dmax,
        "pmin": pmin, "pmaks": pmaks,
    }


st.set_page_config(page_title="JERAT | Audit Lingkungan", page_icon="⚖️", layout="wide")


if "modul" not in st.session_state:
    st.session_state.modul = ""
if "hasil" not in st.session_state:
    st.session_state.hasil = None

st.caption("JARINGAN EVALUASI REGULASI DAN ATURAN TAMBANG")
st.title("⚖️ KAU NEKAT KAMI JERAT")
st.header("JERAT — Evaluasi Dampak dan Kepatuhan Kegiatan Pertambangan")
st.text("Platform evaluasi lingkungan untuk membantu pemeriksaan kualitas air, kualitas udara, pencemaran tanah, serta aspek kepatuhan kegiatan pertambangan.")
st.write("Pilih jenis pemeriksaan yang ingin dilakukan. Masukkan data sesuai parameter untuk memperoleh hasil evaluasi.")

if not st.session_state.modul:
    st.divider()
    cols = st.columns(4)
    menu = [
        ("air", "💧 Indeks Air", "IKA — Indeks Kelayakan Air tambang"),
        ("udara", "🌫️ Indeks Udara", "ISPU — 7 parameter pencemar udara"),
        ("tanah", "🌱 Indeks Tanah", "Indeks Pencemaran Nemerow (Pn)"),
        ("audit", "⚖️ Audit Perusahaan", "Izin, kawasan hutan, kecelakaan, limbah, dan suap"),
    ]
    for col, (kode, judul, deskripsi) in zip(cols, menu):
        with col:
            st.markdown(f"### {judul}")
            st.write(deskripsi)
            if st.button("Mulai pemeriksaan", key=f"mulai_{kode}", use_container_width=True):
                st.session_state.modul = kode
                st.session_state.hasil = None
                st.rerun()
else:
    modul = st.session_state.modul
    judul = {"air":"Indeks Kelayakan Air", "udara":"Indeks Pencemar Udara", "tanah":"Indeks Pencemaran Tanah", "audit":"Audit Perusahaan"}[modul]
    st.divider()
    st.subheader("Formulir Pemeriksaan — " + judul)
    d = {}
    def simpan(k, v):
        d[k] = [str(v)]

    with st.form("form_pemeriksaan"):
        if modul == "air":
            st.markdown("#### Pengamatan awal")
            simpan("tambang", st.selectbox("Jenis tambang", [("1","Nikel"),("2","Batu Bara")], format_func=lambda x:x[1])[0])
            for k, label in [("keruh","Apakah air terlihat keruh?"),("warna","Apakah air berwarna?"),("bau","Apakah air berbau?")]:
                simpan(k, st.radio(label, ["tidak","ya"], format_func=lambda x:"Ya" if x=="ya" else "Tidak", horizontal=True))
            simpan("lanjut", st.radio("Lakukan observasi lebih lanjut?", ["ya","tidak"], format_func=lambda x:"Ya" if x=="ya" else "Tidak", horizontal=True))
            st.markdown("#### Parameter lanjutan air")
            c1,c2,c3 = st.columns(3)
            with c1: simpan("jarak", st.number_input("Jarak sumber air dari area tambang (km)", min_value=0.0, value=2.0))
            with c2: simpan("volume", st.number_input("Jumlah air yang diobservasi (liter)", min_value=0.000001, value=10.0))
            with c3: simpan("ph", st.number_input("Nilai pH air", min_value=0.0, max_value=14.0, value=7.0))
            c1,c2,c3 = st.columns(3)
            with c1: simpan("ntu", st.number_input("Kekeruhan air (NTU)", min_value=0.0, value=1.0))
            with c2: simpan("tcu", st.number_input("Warna air (TCU)", min_value=0.000001, value=5.0))
            with c3: st.caption("Massa zat terlarut diisi dalam mg.")
            st.markdown("#### Massa zat terlarut")
            c1,c2,c3,c4 = st.columns(4)
            for i,col in enumerate([c1,c2,c3,c4]):
                with col: simpan("massa"+str(i), st.number_input(f"Massa zat ke-{i+1} (mg)", min_value=0.0, value=0.0, key=f"massa_{i}"))
        elif modul == "udara":
            st.markdown("Masukkan konsentrasi dalam µg/m³.")
            cols = st.columns(2)
            for i,(kode,nama,*_) in enumerate(PU):
                with cols[i%2]: simpan("u_"+kode, st.number_input(nama+" (µg/m³)", min_value=0.0, value=0.0, key="udara_"+kode))
        elif modul == "tanah":
            pilihan_tambang = st.selectbox("Jenis tambang", [("1","Nikel"),("2","Batu Bara")], format_func=lambda x:x[1])
            simpan("tambang", pilihan_tambang[0])
            cols=st.columns(2)
            dasar=[("pht","pH tanah",7.0),("ec","Daya Hantar Listrik (dS/m)",1.0),("corg","C-Organik (%)",3.0),("ktk","Kapasitas Tukar Kation (cmol/Kg)",10.0),("pb","Logam berat Pb (g/kg)",1.0)]
            for i,(k,label,val) in enumerate(dasar):
                with cols[i%2]: simpan(k,st.number_input(label,min_value=0.0,max_value=14.0 if k=="pht" else None,value=val,key="tanah_"+k))
            st.markdown("#### Parameter logam tambahan")
            cols=st.columns(3)
            tambahan=[("fe","Fe (Batu Bara)",50.0),("mn","Mn (Batu Bara)",2.0),("so4","SO4 (Batu Bara)",1.0),("ni","Ni (Nikel)",0.2),("co","Co (Nikel)",0.2),("cr6","Cr6+ (Nikel)",0.05)]
            for i,(k,label,val) in enumerate(tambahan):
                with cols[i%3]: simpan(k,st.number_input(label+" (g/kg)",min_value=0.0,value=val,key="logam_"+k))
        else:
            st.markdown("Jawab pertanyaan audit berikut.")
            for k,label in [("izin","Apakah perusahaan memiliki izin usaha pertambangan?"),("limbah","Adakah limbah yang dikelola tanpa izin?"),("suap","Adakah praktik suap atau laporan keuangan fiktif?")]:
                simpan(k,st.radio(label,["tidak","ya"],format_func=lambda x:"Ya" if x=="ya" else "Tidak",horizontal=True))
            c1,c2=st.columns(2)
            with c1: simpan("hektare",st.number_input("Luas kawasan hutan (hektare)",min_value=0.0,value=0.0))
            with c2: simpan("korban",st.number_input("Jumlah korban kecelakaan kerja",min_value=0.0,value=0.0,step=1.0))
        submitted = st.form_submit_button("Hitung hasil evaluasi", use_container_width=True)

    if submitted:
        try:
            fungsi = {"air":hitung_air,"udara":hitung_udara,"tanah":hitung_tanah,"audit":hitung_audit}[modul]
            st.session_state.hasil = fungsi(d)
        except ValueError as e:
            st.error(str(e))

    if st.session_state.hasil is not None:
        r=st.session_state.hasil
        st.divider()
        st.subheader("Hasil Evaluasi JERAT")
        if modul == "air" and r.get("awal_saja"):
            st.info(r["awal"] + " — Jenis tambang: " + r["jenis"] + ". Pengamatan visual belum menggantikan pengujian laboratorium.")
        elif modul == "air":
            st.metric("Indeks Kelayakan Air (IKA)", f"{r['ika']} / 100")
            st.success(r["kategori"] if r["kelas"] in ("ok","blue") else r["kategori"])
            st.dataframe([{ "Parameter":"pH", "Nilai":r["ph"], "Status":r["status_ph"]},{"Parameter":"Kekeruhan (NTU)","Nilai":r["ntu"],"Status":r["status_ntu"]},{"Parameter":"Warna (TCU)","Nilai":r["tcu"],"Status":r["status_tcu"]}] + [{"Parameter":z["nama"],"Nilai":z["kons"],"Status":"Layak guna" if z["layak"] else "Melebihi batas"} for z in r["zat"]] + [{"Parameter":"TDS","Nilai":r["tds"],"Status":r["status_tds"]}],use_container_width=True)
        elif modul == "udara":
            st.metric("Indeks Standar Pencemar Udara",r["total"])
            st.info("Kategori: "+r["kategori"]+" · Parameter dengan skor tertinggi: "+r["kritis"]["nama"])
            st.dataframe(r["parameter"],use_container_width=True)
        elif modul == "tanah":
            st.metric("Indeks Pencemaran Nemerow (Pn)",f"{r['pn']:.2f}")
            st.info("Kategori: "+r["kategori"])
            st.dataframe([{ "Parameter":x[0],"Nilai":x[1],"Skor":x[2]} for x in r["tambahan"]] + [{"Parameter":"pH tanah","Nilai":r["pht"],"Skor":"—"},{"Parameter":"DHL","Nilai":r["ec"],"Skor":"—"},{"Parameter":"C-Organik","Nilai":r["corg"],"Skor":"—"},{"Parameter":"KTK","Nilai":r["ktk"],"Skor":"—"},{"Parameter":"Pb","Nilai":r["pb"],"Skor":"—"}],use_container_width=True)
        else:
            c1,c2=st.columns(2)
            c1.metric("Denda minimum",f"Rp {r['dmin']:,.2f} miliar")
            c2.metric("Denda maksimum",f"Rp {r['dmax']:,.2f} miliar")
            c1,c2=st.columns(2)
            c1.metric("Pidana minimum",f"{r['pmin']} tahun")
            c2.metric("Pidana maksimum",f"{r['pmaks']} tahun")
            st.caption("Angka merupakan akumulasi berdasarkan aturan perhitungan yang dimasukkan ke program, bukan penetapan sanksi hukum resmi.")

    if st.button("← Kembali ke menu utama"):
        st.session_state.modul = ""
        st.session_state.hasil = None
        st.rerun()

st.divider()
st.caption("KAU NEKAT KAMI JERAT · JERAT | Hasil merupakan simulasi berdasarkan parameter dan aturan yang dimasukkan ke aplikasi.")
