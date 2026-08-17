# -*- coding: utf-8 -*-
"""
VERITAS · Deprem Kayıtlarının Seçimi ve Ölçeklendirilmesi (TBDY 2018 §2.5)
==========================================================================
Kullanıcının temin ettiği PEER NGA (.AT2) ivme kayıtlarını okur, %5 sönümlü
tepki spektrumlarını hesaplar ve TBDY 2018 Bölüm 2.5'e göre basit (genlik)
ölçeklendirme yapar:

  · 3B analiz : seçilen kayıtların SRSS spektrumlarının ortalaması,
                0.2·Tp – 1.5·Tp aralığında 1.3·Sae(T)'den küçük olamaz.
  · 2B analiz : bileşen spektrumlarının ortalaması Sae(T)'den küçük olamaz.

Varsayılan kayıt kütüphanesi: Tablo 11 (11 kayıt takımı, PEER NGA-West2).

Gereksinimler:  Python ≥ 3.10,  PyQt6,  numpy,  matplotlib
Çalıştırma:     python VERITAS_TBDY2018_Olcekleme.py
"""

from __future__ import annotations

import csv
import os
import re
import sys
from dataclasses import dataclass, field

import numpy as np

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import (QColor, QFont, QFontDatabase, QIcon, QPainter,
                         QPixmap, QAction, QKeySequence)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QToolButton, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QStackedWidget, QButtonGroup, QComboBox, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QFileDialog, QDialog,
    QDialogButtonBox, QLineEdit, QProgressBar, QTabWidget, QScrollArea,
    QSizePolicy, QMessageBox, QSpacerItem,
)

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import font_manager as _fm

APP_NAME = "VERITAS"
APP_SUB = "Deprem Kayıtları Seçimi ve Ölçeklendirme · TBDY 2018"
APP_VER = "v1.0"

# =============================================================================
# 1) TASARIM JETONLARI  (4 px ızgara · açık/koyu tema)
# =============================================================================
SP1, SP2, SP3, SP4, SP5, SP6, SP8 = 4, 8, 12, 16, 20, 24, 32
RAD_S, RAD_M, RAD_L = 6, 10, 14

FONT_HEAD = "Hanken Grotesk"
FONT_BODY = "Inter"
FONT_ICON = "Material Symbols Rounded"

LIGHT = dict(
    bg="#F1F5F9", surface="#FFFFFF", surface2="#F8FAFC", sunken="#EEF2F7",
    border="#E2E8F0", border2="#CBD5E1",
    text="#0F172A", text2="#475569", text3="#94A3B8",
    accent="#2563EB", accent_h="#1D4ED8", accent_p="#1E40AF",
    accent_soft="#DBEAFE", on_accent="#FFFFFF",
    ok="#16A34A", ok_soft="#DCFCE7", warn="#D97706", warn_soft="#FEF3C7",
    err="#DC2626", err_soft="#FEE2E2",
    sidebar="#0F172A", sidebar_txt="#CBD5E1", sidebar_mut="#64748B",
    sidebar_hov="#1E293B", sidebar_act="#2563EB", sidebar_on="#FFFFFF",
    grid="#D8DFE8", series="#94A3B8",
)
DARK = dict(
    bg="#0B1220", surface="#111A2C", surface2="#0E1626", sunken="#0B1322",
    border="#22304A", border2="#31415F",
    text="#E5EAF3", text2="#9FB0C9", text3="#5C6E8C",
    accent="#3B82F6", accent_h="#5A96F7", accent_p="#2F6FDD",
    accent_soft="#14263F", on_accent="#FFFFFF",
    ok="#22C55E", ok_soft="#0C2A18", warn="#F59E0B", warn_soft="#2B2008",
    err="#EF4444", err_soft="#2C1214",
    sidebar="#0A101D", sidebar_txt="#AEBBD1", sidebar_mut="#54617A",
    sidebar_hov="#131E33", sidebar_act="#3B82F6", sidebar_on="#FFFFFF",
    grid="#243450", series="#4C5E7E",
)

ICO = dict(  # Material Symbols Rounded kod noktaları
    logo=0xF64F, spectrum=0xEB66, records=0xF8EE, scale=0xE429, report=0xF071,
    dark=0xE51C, light=0xE518, folder=0xE2C8, add=0xE990, run=0xEA0B,
    export=0xF090, ok=0xF0BE, err=0xF8B6, warn=0xF083, stat=0xF190,
    doc=0xE873, trash=0xE92E, all=0xE877, none=0xE9D3,
)


# =============================================================================
# 2) TBDY 2018 MOTORU
# =============================================================================
_SS_PTS = np.array([0.25, 0.50, 0.75, 1.00, 1.25, 1.50])
_FS = {"ZA": [0.8]*6, "ZB": [0.9]*6,
       "ZC": [1.3, 1.3, 1.2, 1.2, 1.2, 1.2],
       "ZD": [1.6, 1.4, 1.2, 1.1, 1.0, 1.0],
       "ZE": [2.4, 1.7, 1.3, 1.1, 0.9, 0.8]}
_S1_PTS = np.array([0.10, 0.20, 0.30, 0.40, 0.50, 0.60])
_F1 = {"ZA": [0.8]*6, "ZB": [0.8]*6,
       "ZC": [1.5, 1.5, 1.5, 1.5, 1.5, 1.4],
       "ZD": [2.4, 2.2, 2.0, 1.9, 1.8, 1.7],
       "ZE": [4.2, 3.3, 2.8, 2.4, 2.2, 2.0]}
TL_DEFAULT = 6.0
SOIL_CLASSES = ["ZA", "ZB", "ZC", "ZD", "ZE"]


def site_coeffs(ss: float, s1: float, soil: str) -> tuple[float, float]:
    """TBDY 2018 Tablo 2.1–2.2 yerel zemin etki katsayıları (doğrusal ara değer)."""
    fs = float(np.interp(ss, _SS_PTS, _FS[soil]))
    f1 = float(np.interp(s1, _S1_PTS, _F1[soil]))
    return fs, f1


def design_spectrum(T: np.ndarray, sds: float, sd1: float,
                    tl: float = TL_DEFAULT) -> np.ndarray:
    """TBDY 2018 Denk. 2.2 yatay elastik tasarım spektrumu Sae(T) [g]."""
    ta, tb = 0.2 * sd1 / sds, sd1 / sds
    T = np.asarray(T, float)
    out = np.empty_like(T)
    m = T <= ta
    out[m] = (0.4 + 0.6 * T[m] / ta) * sds
    m = (T > ta) & (T <= tb)
    out[m] = sds
    m = (T > tb) & (T <= tl)
    out[m] = sd1 / T[m]
    m = T > tl
    out[m] = sd1 * tl / T[m] ** 2
    return out


def read_at2(path: str) -> tuple[float, np.ndarray]:
    """PEER NGA .AT2 dosyası okur → (dt [s], ivme [g])."""
    with open(path, "r", encoding="latin-1", errors="ignore") as f:
        lines = f.readlines()
    npts = dt = None
    start = 0
    for i, ln in enumerate(lines[:8]):
        m = re.search(r"NPTS\s*[=:]?\s*(\d+)\s*[,;]?\s*DT\s*[=:]?\s*([0-9.Ee+\-]+)",
                      ln, re.IGNORECASE)
        if m:
            npts, dt = int(m.group(1)), float(m.group(2))
            start = i + 1
            break
    if npts is None:  # eski biçim: "  4096   0.0050"
        for i, ln in enumerate(lines[:8]):
            p = ln.split()
            if len(p) == 2:
                try:
                    a, b = float(p[0]), float(p[1])
                    if a > 10 and 1e-5 < b < 1.0:
                        npts, dt, start = int(a), b, i + 1
                        break
                except ValueError:
                    pass
    if npts is None:
        raise ValueError("NPTS/DT başlığı bulunamadı (PEER .AT2 biçimi bekleniyor).")
    vals: list[float] = []
    for ln in lines[start:]:
        vals.extend(float(x) for x in ln.split())
        if len(vals) >= npts:
            break
    if len(vals) < npts:
        raise ValueError(f"Veri eksik: {len(vals)}/{npts} örnek.")
    return dt, np.asarray(vals[:npts], float)


# --- PEER dosya adı çözümleme -------------------------------------------------
# Düşey bileşen ekleri (hesaba KATILMAZ): ...-UP, ...DWN, ...UD, ...-V, ...-Z
_VERT_SUF = ("UP", "DWN", "DOWN", "UD", "VER", "VRT", "-V", "_V", "-Z", "_Z")
# Yatay bileşen harf ekleri → azimut (derece)
_AZ_SUF = (("NS", 0.0), ("EW", 90.0), ("LN", 0.0), ("TR", 90.0),
           ("L", 0.0), ("T", 90.0), ("N", 0.0), ("E", 90.0),
           ("W", 270.0), ("S", 180.0))
_RE_NSEW = re.compile(r"([NS])(\d{1,3})([EW])$")
_RE_AZ3 = re.compile(r"(\d{3})$")
_RE_AZ2 = re.compile(r"(\d{1,2})$")


def split_component(stem: str) -> tuple[str, str, float | None]:
    """Dosya adı gövdesini çözer → (taban, tür, azimut).

    tür: 'H' yatay, 'V' düşey, '?' belirsiz.  Sıra önemlidir: önce sayısal
    azimut, sonra düşey ekler (DLTDWN gibi 'N' ile biten düşeyler yanlışlıkla
    yatay sayılmasın), en son harf ekleri.
    """
    t = stem.upper()
    m = _RE_NSEW.search(t)                                   # N76W / S14E
    if m:
        d = float(m.group(2))
        az = {"NE": d, "NW": (360.0 - d) % 360.0,
              "SE": 180.0 - d, "SW": 180.0 + d}[m.group(1) + m.group(3)]
        return stem[:len(stem) - len(m.group(0))].rstrip("-_. "), "H", az % 360.0
    m = _RE_AZ3.search(t)                                    # 225 / 090 / 000
    if m:
        return (stem[:len(stem) - 3].rstrip("-_. "), "H",
                float(m.group(1)) % 360.0)
    for suf in _VERT_SUF:                                    # düşey bileşen
        if t.endswith(suf):
            return stem[:len(stem) - len(suf)].rstrip("-_. "), "V", None
    for suf, az in _AZ_SUF:                                  # NS / EW / L / T
        if t.endswith(suf):
            return stem[:len(stem) - len(suf)].rstrip("-_. "), "H", az
    m = _RE_AZ2.search(t)
    if m:
        return (stem[:len(stem) - len(m.group(1))].rstrip("-_. "), "H",
                float(m.group(1)) % 360.0)
    return stem, "?", None


def at2_meta(path: str) -> tuple[str, str]:
    """PEER .AT2 başlığının 2. satırından (deprem, istasyon) çıkarır."""
    try:
        with open(path, "r", encoding="latin-1", errors="ignore") as f:
            f.readline()
            ln = f.readline().strip()
    except OSError:
        return "", ""
    parts = [p.strip(" \t,") for p in ln.split(",") if p.strip(" \t,")]
    if not parts:
        return "", ""
    ev = re.sub(r"\d{1,2}[/.]\d{1,2}[/.]\d{2,4}.*$", "", parts[0]).strip(" ,-")
    ev = re.sub(r"\s{2,}", " ", ev)
    st = ""
    for cand in parts[1:]:
        # tarih/saat, salt sayı ya da bileşen kodu ise istasyon değildir
        if re.fullmatch(r"[\d:/\s.\-]+", cand):
            continue
        if re.fullmatch(r"(?i)[A-Z0-9]{1,4}[-_.]?[A-Z0-9]{0,6}\d{2,3}", cand):
            continue
        if re.fullmatch(r"(?i)(UP|DWN|DOWN|UD|V|Z|NS|EW|L|T)", cand):
            continue
        if len(re.findall(r"[A-Za-z]", cand)) >= 3:
            st = re.sub(r"\s{2,}", " ", cand)
            break
    return ev, st


def discover_sets(folder: str) -> tuple[list[dict], int, list[str]]:
    """Klasörü (alt klasörler dâhil) tarar, PEER kayıt takımlarını kurar.

    Aynı kayıt numarası (RSN) altındaki yatay bileşenlerden aralarındaki açı
    90°'ye en yakın olan çift seçilir; düşey (UP/DWN) bileşenler atılır.
    → (takım listesi, atılan düşey dosya sayısı, eşlenemeyen dosyalar)
    """
    groups: dict[str, list[dict]] = {}
    n_vert = 0
    orphan: list[str] = []
    for root, _dirs, files in os.walk(folder):
        for fn in sorted(files):
            if not fn.lower().endswith(".at2"):
                continue
            stem = os.path.splitext(fn)[0]
            base, kind, az = split_component(stem)
            if kind == "V":
                n_vert += 1
                continue
            if kind == "?":
                orphan.append(fn)
                continue
            m = re.search(r"RSN\s*(\d+)", stem, re.IGNORECASE)
            key = f"RSN{int(m.group(1))}" if m else base
            groups.setdefault(key, []).append(
                {"fn": fn, "path": os.path.join(root, fn), "az": az,
                 "stem": stem, "base": base})

    sets: list[dict] = []
    for key, comps in groups.items():
        if len(comps) < 2:
            orphan.extend(c["fn"] for c in comps)
            continue
        # aralarındaki açı 90°'ye en yakın ikili (180° modunda)
        best, best_err = None, 1e9
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                a, b = comps[i], comps[j]
                if a["az"] is None or b["az"] is None:
                    err = 90.0
                else:
                    err = abs(((a["az"] - b["az"]) % 180.0) - 90.0)
                if err < best_err:
                    best, best_err = (a, b), err
        a, b = best
        if (a["az"] or 0.0) > (b["az"] or 0.0):
            a, b = b, a
        ev, st = at2_meta(a["path"])
        if not ev:
            m = re.match(r"(?i)^RSN\d+[_-]+([^_]+)", a["stem"])
            ev = (m.group(1).split(".")[0] if m else a["base"]) or key
        if not st:
            st = re.split(r"[-_.]", a["base"])[-1] or key
        sets.append({
            "key": key, "event": ev.title() if ev.isupper() else ev,
            "station": f"{key} · {st}" if key.startswith("RSN") else st,
            "h1": a["fn"], "h2": b["fn"],
            "h1_path": a["path"], "h2_path": b["path"],
            "az1": a["az"], "az2": b["az"], "angle_err": best_err,
            "extra": len(comps) - 2})
        if len(comps) > 2:
            used = {a["fn"], b["fn"]}
            orphan.extend(c["fn"] for c in comps if c["fn"] not in used)
    sets.sort(key=lambda s: (len(s["key"]), s["key"]))
    return sets, n_vert, orphan


def response_spectrum(acc_g: np.ndarray, dt: float, periods: np.ndarray,
                      xi: float = 0.05) -> np.ndarray:
    """%xi sönümlü SDOF sözde-ivme spektrumu [g] (frekans ortamı, kesin çözüm)."""
    a = np.asarray(acc_g, float)
    a = a - a.mean()                            # DC/temel çizgi sapmasına karşı
    n = a.size
    w_min = 2.0 * np.pi / periods.max()
    pad = int(8.0 / (xi * w_min) / dt)          # serbest titreşim sönümü payı
    nfft = 1 << int(n + pad - 1).bit_length()
    Ag = np.fft.rfft(a, nfft)
    Om = 2.0 * np.pi * np.fft.rfftfreq(nfft, dt)
    sa = np.empty(periods.size)
    for i, T in enumerate(periods):
        w = 2.0 * np.pi / T
        H = -1.0 / ((w * w - Om * Om) + 2j * xi * w * Om)   # U(Ω)/Ag(Ω)
        u = np.fft.irfft(Ag * H, nfft)[:n + pad]
        sa[i] = w * w * np.max(np.abs(u))
    return sa


def period_grid(n: int = 160, t0: float = 0.02, t1: float = 8.0) -> np.ndarray:
    return np.logspace(np.log10(t0), np.log10(t1), n)


def scale_set(periods: np.ndarray, basis: list[np.ndarray], sae: np.ndarray,
              tp: float, k: float) -> dict:
    """
    TBDY 2018 §2.5.2.5 basit ölçeklendirme.
      1) Her kayıt için EKK bireysel katsayı f  (hedef k·Sae'ye uydurma)
      2) Ortak grup katsayısı g: ortalama spektrum bandın her noktasında
         k·Sae'nin altına düşmeyecek biçimde.
      Nihai katsayı F = f · g
    """
    band = (periods >= 0.2 * tp) & (periods <= 1.5 * tp)
    tgt = k * sae
    tb = tgt[band]
    f = np.array([float(b[band] @ tb / (b[band] @ b[band])) for b in basis])
    mean_scaled = np.mean([fi * b for fi, b in zip(f, basis)], axis=0)
    g = float(np.max(tb / mean_scaled[band]))
    F = f * g
    mean_final = mean_scaled * g
    ratio = mean_final[band] / tb
    i_min = int(np.argmin(ratio))
    return dict(band=band, target=tgt, k=k, f=f, g=g, F=F,
                mean_unscaled=np.mean(basis, axis=0),
                mean_scaled=mean_final,
                min_ratio=float(ratio[i_min]),
                t_crit=float(periods[band][i_min]),
                passed=bool(ratio.min() >= 1.0 - 1e-9))


# =============================================================================
# 3) VARSAYILAN KAYIT KÜTÜPHANESİ — Tablo 11
# =============================================================================
@dataclass
class GMRecord:
    event: str
    mag: float
    mech: str
    station: str
    h1: str
    h2: str
    repi: float
    rjb: float
    vs30: int
    ref_dd2: float | None = None      # Tablo 11 referans katsayıları
    ref_dd1: float | None = None
    default: bool = True
    checked: bool = True
    h1_path: str | None = None
    h2_path: str | None = None
    dt1: float | None = None
    dt2: float | None = None
    acc1: np.ndarray | None = None
    acc2: np.ndarray | None = None
    sa1: np.ndarray | None = None
    sa2: np.ndarray | None = None

    @property
    def label(self) -> str:
        return f"{self.event} · {self.station}"

    @property
    def ready(self) -> bool:
        return bool(self.h1_path and self.h2_path)


def default_records() -> list[GMRecord]:
    T = [
        ("Chuetsu-oki, Japan", 6.8, "Reverse",    "MatsushiroTokamachi",
         "CHUETSU_65006NS.AT2",  "CHUETSU_65006EW.AT2",  18.2, 25.0, 640, 2.10, 3.58),
        ("CapeMendocino",      7.0, "Reverse",    "Fortuna-FortunaBlvd",
         "CAPEMEND_FOR000.AT2", "CAPEMEND_FOR090.AT2",  16.0, 20.0, 457, 1.24, 2.12),
        ("Chuetsu-oki, Japan", 6.8, "Reverse",    "SawaMizugutiTokamachi",
         "CHUETSU_65053NS.AT2", "CHUETSU_65053EW.AT2",  21.2, 27.3, 640, 1.65, 2.83),
        ("Manjil, Iran",       7.4, "strikeslip", "Abbar",
         "MANJIL_ABBAR--L.AT2", "MANJIL_ABBAR--T.AT2",  12.6, 12.6, 724, 0.60, 1.03),
        ("Landers",            7.3, "strikeslip", "NorthPalmSpringsFireSta#36",
         "LANDERS_NPF090.AT2",  "LANDERS_NPF180.AT2",   27.0, 27.0, 368, 1.48, 2.54),
        ("Iwate, Japan",       6.9, "Reverse",    "MYGH06",
         "IWATE_MYGH06NS.AT2",  "IWATE_MYGH06EW.AT2",   34.5, 34.5, 593, 2.04, 3.39),
        ("Darfield, NewZealand", 7.0, "strikeslip", "CSHS",
         "DARFIELD_CSHSN76W.AT2", "DARFIELD_CSHSS14W.AT2", 43.6, 43.6, 638, 2.01, 3.45),
        ("Darfield, NewZealand", 7.0, "strikeslip", "HeathcoteValleyPrimarySchool",
         "DARFIELD_HVSCS26W.AT2", "DARFIELD_HVSCS64E.AT2", 24.4, 24.5, 422, 1.81, 3.02),
        ("Iwate, Japan",       6.9, "Reverse",    "TamatiOno",
         "IWATE_54009NS.AT2",   "IWATE_54009EW.AT2",    28.9, 28.9, 562, 1.27, 2.03),
        ("Landers",            7.3, "strikeslip", "FunValley",
         "LANDERS_FVR045.AT2",  "LANDERS_FVR135.AT2",   25.0, 25.0, 389, 2.25, 3.86),
        ("Kocaeli, Turkey",    7.5, "strikeslip", "Iznik",
         "KOCAELI_IZN180.AT2",  "KOCAELI_IZN090.AT2",   30.7, 30.7, 477, 0.95, 1.64),
    ]
    return [GMRecord(*row) for row in T]


# =============================================================================
# 4) UYGULAMA DURUMU
# =============================================================================
@dataclass
class Params:
    ss_dd2: float = 1.20
    s1_dd2: float = 0.30
    ss_dd1: float = 2.00
    s1_dd1: float = 0.55
    soil: str = "ZC"
    tp: float = 1.00
    mode3d: bool = True     # True: SRSS·1.3   False: 2B bileşen ort.·1.0

    def sds_sd1(self, level: str) -> tuple[float, float, float, float]:
        ss, s1 = (self.ss_dd2, self.s1_dd2) if level == "DD-2" else (self.ss_dd1, self.s1_dd1)
        fs, f1 = site_coeffs(ss, s1, self.soil)
        return ss * fs, s1 * f1, fs, f1


@dataclass
class AppState:
    params: Params = field(default_factory=Params)
    records: list[GMRecord] = field(default_factory=default_records)
    periods: np.ndarray = field(default_factory=period_grid)
    results: dict | None = None          # {'levels': {...}, 'ids': [...], 'snap': Params}


# =============================================================================
# 5) HESAP İŞ PARÇACIĞI
# =============================================================================
class ComputeWorker(QThread):
    progress = pyqtSignal(int, int, str)
    done = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, records: list[GMRecord], periods: np.ndarray):
        super().__init__()
        self.records, self.periods = records, periods

    def run(self):
        try:
            total = 2 * len(self.records)
            step = 0
            out = {}
            for r in self.records:
                for comp, path in (("H1", r.h1_path), ("H2", r.h2_path)):
                    step += 1
                    self.progress.emit(step, total, f"{r.station} · {comp}")
                    dt, acc = read_at2(path)
                    sa = response_spectrum(acc, dt, self.periods)
                    out.setdefault(id(r), {})[comp] = (dt, acc, sa)
            self.done.emit(out)
        except Exception as ex:                      # noqa: BLE001
            self.failed.emit(str(ex))


# =============================================================================
# 6) QSS TEMA
# =============================================================================
def build_qss(t: dict) -> str:
    return f"""
* {{ font-family:'{FONT_BODY}'; font-size:13px; color:{t['text']}; }}
QMainWindow, #Content, QDialog {{ background:{t['bg']}; }}
QMessageBox {{ background:{t['bg']}; }}
QFormLayout QLabel, QDialog QLabel {{ color:{t['text2']}; font-size:12.5px; font-weight:600; }}
QToolTip {{ background:{t['surface']}; color:{t['text']}; border:1px solid {t['border2']};
            border-radius:{RAD_S}px; padding:{SP1}px {SP2}px; }}

/* ---- Kenar çubuğu ---- */
#Sidebar {{ background:{t['sidebar']}; border:none; }}
#Brand {{ color:{t['sidebar_on']}; font-family:'{FONT_HEAD}'; font-size:20px;
          font-weight:700; letter-spacing:1px; }}
#BrandSub {{ color:{t['sidebar_mut']}; font-size:10px; letter-spacing:0.4px; }}
#NavBtn {{ color:{t['sidebar_txt']}; background:transparent; border:none;
           border-radius:{RAD_M}px; padding:0 {SP3}px; text-align:left;
           font-size:13px; font-weight:500; }}
#NavBtn:hover {{ background:{t['sidebar_hov']}; color:{t['sidebar_on']}; }}
#NavBtn:pressed {{ background:{t['sidebar_hov']}; }}
#NavBtn:checked {{ background:{t['sidebar_act']}; color:{t['sidebar_on']}; font-weight:600; }}
#SideFoot {{ color:{t['sidebar_mut']}; font-size:11px; }}
#ThemeBtn {{ color:{t['sidebar_txt']}; background:{t['sidebar_hov']};
             border:1px solid {t['sidebar_hov']}; border-radius:{RAD_M}px; }}
#ThemeBtn:hover {{ color:{t['sidebar_on']}; border-color:{t['sidebar_mut']}; }}
#ThemeBtn:pressed {{ background:{t['sidebar']}; }}

/* ---- Başlık ---- */
#Header {{ background:{t['surface']}; border-bottom:1px solid {t['border']}; }}
#PageTitle {{ font-family:'{FONT_HEAD}'; font-size:18px; font-weight:700; }}
#PageDesc {{ color:{t['text2']}; font-size:12px; }}
#VerChip {{ color:{t['text3']}; background:{t['sunken']}; border-radius:{RAD_S}px;
            padding:2px {SP2}px; font-size:11px; }}

/* ---- Kartlar ---- */
#Card {{ background:{t['surface']}; border:1px solid {t['border']};
         border-radius:{RAD_L}px; }}
#CardTitle {{ font-family:'{FONT_HEAD}'; font-size:14px; font-weight:700; }}
#CardHint  {{ color:{t['text3']}; font-size:11px; }}
#StatCard {{ background:{t['surface2']}; border:1px solid {t['border']};
             border-radius:{RAD_M}px; }}
#StatVal  {{ font-family:'{FONT_HEAD}'; font-size:17px; font-weight:700; }}
#StatLbl  {{ color:{t['text2']}; font-size:11px; }}
#Chip {{ background:{t['sunken']}; color:{t['text2']}; border-radius:{RAD_S}px;
         padding:3px {SP2}px; font-size:11px; font-weight:600; }}
#Chip[kind="accent"] {{ background:{t['accent_soft']}; color:{t['accent']}; }}
#Chip[kind="ok"]     {{ background:{t['ok_soft']};  color:{t['ok']}; }}
#Chip[kind="warn"]   {{ background:{t['warn_soft']};color:{t['warn']}; }}
#Chip[kind="err"]    {{ background:{t['err_soft']}; color:{t['err']}; }}

/* ---- Durum şeridi ---- */
#Banner {{ border-radius:{RAD_M}px; border:1px solid transparent; }}
#Banner[kind="info"] {{ background:{t['accent_soft']}; border-color:{t['accent']}44; }}
#Banner[kind="ok"]   {{ background:{t['ok_soft']};   border-color:{t['ok']}55; }}
#Banner[kind="warn"] {{ background:{t['warn_soft']}; border-color:{t['warn']}55; }}
#Banner[kind="err"]  {{ background:{t['err_soft']};  border-color:{t['err']}55; }}
#BannerText {{ font-size:12.5px; font-weight:600; }}
#BannerSub  {{ color:{t['text2']}; font-size:11.5px; font-weight:400; }}

/* ---- Düğmeler ---- */
QPushButton {{ background:{t['surface']}; border:1px solid {t['border2']};
               border-radius:{RAD_M}px; padding:{SP2}px {SP4}px; font-weight:600; }}
QPushButton:hover  {{ background:{t['surface2']}; border-color:{t['accent']}; }}
QPushButton:pressed{{ background:{t['sunken']}; }}
QPushButton:focus  {{ border-color:{t['accent']}; }}
QPushButton:disabled {{ color:{t['text3']}; background:{t['sunken']};
                        border-color:{t['border']}; }}
QPushButton#Primary {{ background:{t['accent']}; color:{t['on_accent']};
                       border:1px solid {t['accent']}; }}
QPushButton#Primary:hover  {{ background:{t['accent_h']}; }}
QPushButton#Primary:pressed{{ background:{t['accent_p']}; }}
QPushButton#Primary:disabled {{ background:{t['border2']}; border-color:{t['border2']};
                                color:{t['surface']}; }}
QPushButton#Seg {{ background:transparent; border:none; border-radius:{RAD_S}px;
                   padding:{SP1}px {SP4}px; color:{t['text2']}; }}
QPushButton#Seg:hover   {{ color:{t['text']}; }}
QPushButton#Seg:checked {{ background:{t['surface']}; color:{t['accent']};
                           font-weight:700; border:1px solid {t['border']}; }}
#SegWrap {{ background:{t['sunken']}; border-radius:{RAD_M}px; }}

/* ---- Girdiler ---- */
QLineEdit, QDoubleSpinBox, QComboBox {{
    background:{t['surface']}; border:1px solid {t['border2']};
    border-radius:{RAD_S+2}px; padding:{SP1+2}px {SP2}px;
    selection-background-color:{t['accent']}; selection-color:{t['on_accent']}; }}
QLineEdit:hover, QDoubleSpinBox:hover, QComboBox:hover {{ border-color:{t['accent']}; }}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border:2px solid {t['accent']}; padding:{SP1+1}px {SP2-1}px; }}
QLineEdit:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
    color:{t['text3']}; background:{t['sunken']}; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width:16px; border:none; background:transparent; }}
QDoubleSpinBox::up-arrow {{ image:none; border-left:4px solid transparent;
    border-right:4px solid transparent; border-bottom:5px solid {t['text2']};
    width:0; height:0; }}
QDoubleSpinBox::down-arrow {{ image:none; border-left:4px solid transparent;
    border-right:4px solid transparent; border-top:5px solid {t['text2']};
    width:0; height:0; }}
QComboBox::drop-down {{ border:none; width:22px; }}
QComboBox::down-arrow {{ image:none; border-left:4px solid transparent;
    border-right:4px solid transparent; border-top:5px solid {t['text2']};
    width:0; height:0; margin-right:6px; }}
QComboBox QAbstractItemView {{ background:{t['surface']}; border:1px solid {t['border2']};
    border-radius:{RAD_S}px; selection-background-color:{t['accent_soft']};
    selection-color:{t['accent']}; outline:none; }}
QLabel#FormLbl {{ color:{t['text2']}; font-size:12px; font-weight:600; }}

/* ---- Tablo ---- */
QTableWidget {{ background:{t['surface']}; alternate-background-color:{t['surface2']};
    border:1px solid {t['border']}; border-radius:{RAD_M}px;
    gridline-color:{t['border']}; selection-background-color:{t['accent_soft']};
    selection-color:{t['text']}; }}
QTableWidget::item {{ padding:2px 6px; border:none; }}
QTableWidget::item:selected {{ background:{t['accent_soft']}; }}
QHeaderView::section {{ background:{t['surface2']}; color:{t['text2']};
    border:none; border-bottom:1px solid {t['border2']};
    padding:{SP2}px {SP2}px; font-weight:700; font-size:11.5px; }}
QTableCornerButton::section {{ background:{t['surface2']}; border:none; }}

/* ---- Sekmeler (grafik) ---- */
QTabWidget::pane {{ border:none; top:{SP2}px; }}
QTabBar::tab {{ background:transparent; color:{t['text2']}; padding:{SP2}px {SP4}px;
    border:1px solid transparent; border-radius:{RAD_M}px; margin-right:{SP1}px;
    font-weight:600; }}
QTabBar::tab:hover {{ color:{t['text']}; background:{t['sunken']}; }}
QTabBar::tab:selected {{ background:{t['accent_soft']}; color:{t['accent']};
    border-color:{t['accent']}33; }}

/* ---- İlerleme / kaydırma ---- */
QProgressBar {{ background:{t['sunken']}; border:none; border-radius:{RAD_S}px;
    height:8px; text-align:center; color:transparent; }}
QProgressBar::chunk {{ background:{t['accent']}; border-radius:{RAD_S}px; }}
QScrollBar:vertical {{ background:transparent; width:10px; margin:2px; }}
QScrollBar::handle:vertical {{ background:{t['border2']}; border-radius:4px;
    min-height:28px; }}
QScrollBar::handle:vertical:hover {{ background:{t['text3']}; }}
QScrollBar:horizontal {{ background:transparent; height:10px; margin:2px; }}
QScrollBar::handle:horizontal {{ background:{t['border2']}; border-radius:4px;
    min-width:28px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
QScrollArea {{ border:none; background:transparent; }}
#Scroller, #Scroller > QWidget > QWidget {{ background:transparent; }}
"""


def char_icon(cp: int, color: str, px: int = 20) -> QIcon:
    pm = QPixmap(px * 2, px * 2)
    pm.setDevicePixelRatio(2)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    f = QFont(FONT_ICON)
    f.setPixelSize(px)
    p.setFont(f)
    p.setPen(QColor(color))
    p.drawText(pm.rect().adjusted(0, 0, -px, -px), Qt.AlignmentFlag.AlignCenter, chr(cp))
    p.end()
    return QIcon(pm)


def icon_label(cp: int, color: str, px: int = 18) -> QLabel:
    lb = QLabel(chr(cp))
    f = QFont(FONT_ICON)
    f.setPixelSize(px)
    lb.setFont(f)
    lb.setStyleSheet(f"color:{color}; background:transparent;")
    return lb


def hline(t: dict) -> QFrame:
    ln = QFrame()
    ln.setFixedHeight(1)
    ln.setStyleSheet(f"background:{t['border']};")
    return ln


def theme_of(w: QWidget) -> dict:
    win = w.window()
    return getattr(win, "theme", LIGHT)


def repolish(w: QWidget):
    w.style().unpolish(w)
    w.style().polish(w)


# =============================================================================
# 7) ORTAK BİLEŞENLER
# =============================================================================
class Card(QFrame):
    def __init__(self, title: str = "", hint: str = ""):
        super().__init__()
        self.setObjectName("Card")
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(SP5, SP4, SP5, SP5)
        self.v.setSpacing(SP3)
        if title:
            row = QHBoxLayout()
            self.title_lb = QLabel(title)
            self.title_lb.setObjectName("CardTitle")
            row.addWidget(self.title_lb)
            row.addStretch(1)
            if hint:
                h = QLabel(hint)
                h.setObjectName("CardHint")
                row.addWidget(h)
            self.v.addLayout(row)


class Chip(QLabel):
    def __init__(self, text: str = "", kind: str = ""):
        super().__init__(text)
        self.setObjectName("Chip")
        self.set_kind(kind)

    def set_kind(self, kind: str):
        self.setProperty("kind", kind)
        repolish(self)


class StatCard(QFrame):
    def __init__(self, label: str, value: str = "—"):
        super().__init__()
        self.setObjectName("StatCard")
        v = QVBoxLayout(self)
        v.setContentsMargins(SP3, SP2 + 2, SP3, SP2 + 2)
        v.setSpacing(2)
        self.val = QLabel(value)
        self.val.setObjectName("StatVal")
        self.lbl = QLabel(label)
        self.lbl.setObjectName("StatLbl")
        v.addWidget(self.val)
        v.addWidget(self.lbl)


class Banner(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Banner")
        h = QHBoxLayout(self)
        h.setContentsMargins(SP4, SP3, SP4, SP3)
        h.setSpacing(SP3)
        self.ico = QLabel()
        self.txt = QLabel()
        self.txt.setObjectName("BannerText")
        self.sub = QLabel()
        self.sub.setObjectName("BannerSub")
        self.sub.setWordWrap(True)
        box = QVBoxLayout()
        box.setSpacing(1)
        box.addWidget(self.txt)
        box.addWidget(self.sub)
        h.addWidget(self.ico, 0, Qt.AlignmentFlag.AlignTop)
        h.addLayout(box, 1)
        self.hide()

    def show_msg(self, kind: str, title: str, sub: str, theme: dict):
        cp = dict(ok=ICO["ok"], err=ICO["err"], warn=ICO["warn"], info=ICO["stat"])[kind]
        col = dict(ok=theme["ok"], err=theme["err"], warn=theme["warn"],
                   info=theme["accent"])[kind]
        f = QFont(FONT_ICON)
        f.setPixelSize(20)
        self.ico.setFont(f)
        self.ico.setText(chr(cp))
        self.ico.setStyleSheet(f"color:{col}; background:transparent;")
        self.txt.setText(title)
        self.txt.setStyleSheet(f"color:{col};")
        self.sub.setText(sub)
        self.sub.setVisible(bool(sub))
        self.setProperty("kind", kind)
        repolish(self)
        self.show()


class Plot(FigureCanvas):
    """Tema uyumlu matplotlib tuvali."""
    def __init__(self, height: float = 4.2):
        self.fig = Figure(figsize=(6.4, height), dpi=100, layout="constrained")
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(int(height * 78))

    def style(self, ax, th: dict, xlab: str, ylab: str):
        ax.set_facecolor(th["surface"])
        self.fig.set_facecolor(th["surface"])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(th["border2"])
        ax.tick_params(colors=th["text2"], labelsize=9)
        ax.set_xlabel(xlab, color=th["text2"], fontsize=10)
        ax.set_ylabel(ylab, color=th["text2"], fontsize=10)
        ax.grid(True, color=th["grid"], lw=0.7, alpha=0.6)
        ax.margins(x=0)

    def legend(self, ax, th: dict, **kw):
        lg = ax.legend(frameon=False, fontsize=9, labelcolor=th["text"], **kw)
        return lg


# =============================================================================
# 8) SAYFA 1 — SPEKTRUM PARAMETRELERİ
# =============================================================================
class SpectrumPage(QWidget):
    changed = pyqtSignal()

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        root = QHBoxLayout(self)
        root.setContentsMargins(SP6, SP6, SP6, SP6)
        root.setSpacing(SP5)

        # ---- Sol sütun: parametreler ----
        left = QVBoxLayout()
        left.setSpacing(SP4)

        self.card_afad = Card("Deprem Düzeyi Parametreleri",
                              "AFAD Deprem Tehlike Haritası")
        g = QGridLayout()
        g.setHorizontalSpacing(SP4)
        g.setVerticalSpacing(SP2)
        for col, lvl in ((1, "DD-2"), (2, "DD-1")):
            lb = QLabel(lvl)
            lb.setObjectName("FormLbl")
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            g.addWidget(lb, 0, col)
        self.sp = {}
        for row, (key, txt, rng, dec) in enumerate((
                ("ss", "Kısa periyot Sₛ", (0.10, 3.00), 3),
                ("s1", "1.0 s periyot S₁", (0.02, 1.50), 3)), start=1):
            lab = QLabel(txt)
            lab.setObjectName("FormLbl")
            g.addWidget(lab, row, 0)
            for col, lvl in ((1, "dd2"), (2, "dd1")):
                sb = QDoubleSpinBox()
                sb.setRange(*rng)
                sb.setDecimals(dec)
                sb.setSingleStep(0.01)
                sb.setValue(getattr(self.state.params, f"{key}_{lvl}"))
                sb.valueChanged.connect(self._on_change)
                self.sp[f"{key}_{lvl}"] = sb
                g.addWidget(sb, row, col)
        self.card_afad.v.addLayout(g)
        left.addWidget(self.card_afad)

        self.card_site = Card("Zemin ve Yapı Bilgileri")
        fg = QGridLayout()
        fg.setHorizontalSpacing(SP4)
        fg.setVerticalSpacing(SP2)
        lb1 = QLabel("Yerel zemin sınıfı")
        lb1.setObjectName("FormLbl")
        self.cb_soil = QComboBox()
        self.cb_soil.addItems(SOIL_CLASSES)
        self.cb_soil.setCurrentText(self.state.params.soil)
        self.cb_soil.currentTextChanged.connect(self._on_change)
        lb2 = QLabel("Doğal titreşim periyodu Tp")
        lb2.setObjectName("FormLbl")
        self.sb_tp = QDoubleSpinBox()
        self.sb_tp.setRange(0.10, 5.00)
        self.sb_tp.setDecimals(2)
        self.sb_tp.setSingleStep(0.05)
        self.sb_tp.setSuffix(" s")
        self.sb_tp.setValue(self.state.params.tp)
        self.sb_tp.valueChanged.connect(self._on_change)
        lb3 = QLabel("Analiz türü")
        lb3.setObjectName("FormLbl")
        self.cb_mode = QComboBox()
        self.cb_mode.addItems([
            "3B — SRSS ort. ≥ 1.3·Sae",
            "2B — bileşen ort. ≥ 1.0·Sae"])
        self.cb_mode.currentIndexChanged.connect(self._on_change)
        fg.addWidget(lb1, 0, 0); fg.addWidget(self.cb_soil, 0, 1)
        fg.addWidget(lb2, 1, 0); fg.addWidget(self.sb_tp, 1, 1)
        fg.addWidget(lb3, 2, 0); fg.addWidget(self.cb_mode, 2, 1)
        self.card_site.v.addLayout(fg)
        self.band_chip = Chip("", "accent")
        self.card_site.v.addWidget(self.band_chip, 0, Qt.AlignmentFlag.AlignLeft)
        left.addWidget(self.card_site)

        self.card_der = Card("Türetilen Spektrum Büyüklükleri", "TBDY 2018 Denk. 2.1–2.3")
        self.der_grid = QGridLayout()
        self.der_grid.setHorizontalSpacing(SP3)
        self.der_grid.setVerticalSpacing(SP3)
        self.stats: dict[str, StatCard] = {}
        for i, (key, lbl) in enumerate((
                ("sds2", "SDS · DD-2"), ("sd12", "SD1 · DD-2"),
                ("ta2", "TA · DD-2"),  ("tb2", "TB · DD-2"),
                ("sds1", "SDS · DD-1"), ("sd11", "SD1 · DD-1"),
                ("ta1", "TA · DD-1"),  ("tb1", "TB · DD-1"))):
            sc = StatCard(lbl)
            self.stats[key] = sc
            self.der_grid.addWidget(sc, i // 4, i % 4)
        self.card_der.v.addLayout(self.der_grid)
        left.addWidget(self.card_der)
        left.addStretch(1)

        lw = QWidget()
        lw.setLayout(left)
        lw.setFixedWidth(470)
        root.addWidget(lw)

        # ---- Sağ: spektrum grafiği ----
        self.card_plot = Card("Yatay Elastik Tasarım Spektrumları  Sae(T)")
        self.plot = Plot(5.2)
        self.card_plot.v.addWidget(self.plot, 1)
        root.addWidget(self.card_plot, 1)

    # ---------------------------------------------------------------
    def _on_change(self, *_):
        p = self.state.params
        p.ss_dd2 = self.sp["ss_dd2"].value(); p.s1_dd2 = self.sp["s1_dd2"].value()
        p.ss_dd1 = self.sp["ss_dd1"].value(); p.s1_dd1 = self.sp["s1_dd1"].value()
        p.soil = self.cb_soil.currentText()
        p.tp = self.sb_tp.value()
        p.mode3d = self.cb_mode.currentIndex() == 0
        self.refresh(self.window().theme)
        self.changed.emit()

    def refresh(self, th: dict):
        p = self.state.params
        vals = {}
        for lvl, sfx in (("DD-2", "2"), ("DD-1", "1")):
            sds, sd1, fs, f1 = p.sds_sd1(lvl)
            ta, tb = 0.2 * sd1 / sds, sd1 / sds
            vals[lvl] = (sds, sd1, ta, tb)
            self.stats[f"sds{sfx}"].val.setText(f"{sds:.3f} g")
            self.stats[f"sd1{sfx}"].val.setText(f"{sd1:.3f} g")
            self.stats[f"ta{sfx}"].val.setText(f"{ta:.3f} s")
            self.stats[f"tb{sfx}"].val.setText(f"{tb:.3f} s")
            self.stats[f"sds{sfx}"].setToolTip(f"Fs = {fs:.3f}")
            self.stats[f"sd1{sfx}"].setToolTip(f"F1 = {f1:.3f}")
        self.band_chip.setText(
            f"Ölçeklendirme bandı  0.2·Tp – 1.5·Tp  =  "
            f"{0.2*p.tp:.2f} s – {1.5*p.tp:.2f} s")

        T = np.linspace(0.0, 8.0, 500)
        self.plot.fig.clear()
        ax = self.plot.fig.add_subplot(111)
        band = (T >= 0.2 * p.tp) & (T <= 1.5 * p.tp)
        ax.axvspan(0.2 * p.tp, 1.5 * p.tp, color=th["accent"], alpha=0.08, lw=0)
        for lvl, color, ls in (("DD-1", th["err"], "-"), ("DD-2", th["accent"], "-")):
            sds, sd1, *_ = vals[lvl]
            ax.plot(T, design_spectrum(np.maximum(T, 1e-4), sds, sd1),
                    color=color, ls=ls, lw=2.2, label=f"Sae(T) · {lvl}")
        ax.set_xlim(0, 8)
        ax.set_ylim(bottom=0)
        self.plot.style(ax, th, "Periyot T (s)", "Sae (g)")
        ax.annotate("0.2Tp–1.5Tp", xy=(0.85 * p.tp, ax.get_ylim()[1] * 0.94),
                    color=th["accent"], fontsize=9, ha="center")
        self.plot.legend(ax, th, loc="upper right")
        self.plot.draw_idle()


# =============================================================================
# 9) SAYFA 2 — KAYIT KÜTÜPHANESİ
# =============================================================================
COLS = ["", "No", "Deprem", "Mw", "Fay\nMek.", "İstasyon", "Bileşen H1",
        "Bileşen H2", "Epi\n(km)", "EnK\n(km)", "Vs30", "Tablo 11\nF·DD-2",
        "Tablo 11\nF·DD-1", "Durum"]
COL_W = [28, 34, 140, 42, 72, 144, 166, 166, 48, 48, 46, 72, 72, 90]


class RecordDialog(QDialog):
    def __init__(self, parent=None, rec: "GMRecord | None" = None):
        super().__init__(parent)
        self.setWindowTitle("Kayıt Takımını Düzenle" if rec
                            else "Yeni Kayıt Takımı Ekle")
        self.setMinimumWidth(460)
        v = QVBoxLayout(self)
        v.setSpacing(SP3)
        form = QFormLayout()
        form.setSpacing(SP2)
        self.ed_event = QLineEdit()
        self.ed_stat = QLineEdit()
        self.sb_mag = QDoubleSpinBox(); self.sb_mag.setRange(3, 9); self.sb_mag.setDecimals(1); self.sb_mag.setValue(7.0)
        self.cb_mech = QComboBox(); self.cb_mech.addItems(["strikeslip", "Reverse", "Normal", "Oblique"])
        self.sb_repi = QDoubleSpinBox(); self.sb_repi.setRange(0, 500); self.sb_repi.setDecimals(1)
        self.sb_rjb = QDoubleSpinBox(); self.sb_rjb.setRange(0, 500); self.sb_rjb.setDecimals(1)
        self.sb_vs = QDoubleSpinBox(); self.sb_vs.setRange(100, 2000); self.sb_vs.setDecimals(0); self.sb_vs.setValue(400)
        self.h1 = QLineEdit(); self.h1.setReadOnly(True)
        self.h2 = QLineEdit(); self.h2.setReadOnly(True)
        b1 = QPushButton("Seç…"); b1.clicked.connect(lambda: self._pick(self.h1))
        b2 = QPushButton("Seç…"); b2.clicked.connect(lambda: self._pick(self.h2))
        r1 = QHBoxLayout(); r1.addWidget(self.h1, 1); r1.addWidget(b1)
        r2 = QHBoxLayout(); r2.addWidget(self.h2, 1); r2.addWidget(b2)
        form.addRow("Deprem adı", self.ed_event)
        form.addRow("İstasyon", self.ed_stat)
        form.addRow("Moment büyüklüğü Mw", self.sb_mag)
        form.addRow("Fay mekanizması", self.cb_mech)
        form.addRow("Episantr uzaklığı (km)", self.sb_repi)
        form.addRow("En kısa uzaklık (km)", self.sb_rjb)
        form.addRow("Vs30 (m/s)", self.sb_vs)
        form.addRow("H1 dosyası (.AT2)", r1)
        form.addRow("H2 dosyası (.AT2)", r2)
        v.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                              QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)
        if rec is not None:
            self.ed_event.setText(rec.event)
            self.ed_stat.setText("" if rec.station == "—" else rec.station)
            if rec.mag:
                self.sb_mag.setValue(rec.mag)
            k = self.cb_mech.findText(rec.mech, Qt.MatchFlag.MatchFixedString)
            if k >= 0:
                self.cb_mech.setCurrentIndex(k)
            self.sb_repi.setValue(rec.repi)
            self.sb_rjb.setValue(rec.rjb)
            if rec.vs30:
                self.sb_vs.setValue(rec.vs30)
            self.h1.setText(rec.h1_path or rec.h1)
            self.h2.setText(rec.h2_path or rec.h2)

    def _pick(self, target: QLineEdit):
        p, _ = QFileDialog.getOpenFileName(self, "İvme kaydı seç", "",
                                           "PEER kayıtları (*.AT2 *.at2);;Tümü (*)")
        if p:
            target.setText(p)

    def _ok(self):
        if not (self.ed_event.text().strip() and self.h1.text() and self.h2.text()):
            QMessageBox.warning(self, APP_NAME,
                                "Deprem adı ile H1 ve H2 dosyaları zorunludur.")
            return
        self.accept()

    def apply_to(self, rec: GMRecord):
        """Var olan kaydın üstyapı bilgilerini günceller (dosyalar dâhil)."""
        rec.event = self.ed_event.text().strip()
        rec.station = self.ed_stat.text().strip() or "—"
        rec.mag = self.sb_mag.value()
        rec.mech = self.cb_mech.currentText()
        rec.repi = self.sb_repi.value()
        rec.rjb = self.sb_rjb.value()
        rec.vs30 = int(self.sb_vs.value())
        p1, p2 = self.h1.text(), self.h2.text()
        if os.path.isfile(p1) and os.path.isfile(p2):
            if (p1, p2) != (rec.h1_path, rec.h2_path):
                rec.h1, rec.h2 = os.path.basename(p1), os.path.basename(p2)
                rec.h1_path, rec.h2_path = p1, p2
                rec.sa1 = rec.sa2 = rec.acc1 = rec.acc2 = None

    def record(self) -> GMRecord:
        return GMRecord(
            event=self.ed_event.text().strip(), mag=self.sb_mag.value(),
            mech=self.cb_mech.currentText(), station=self.ed_stat.text().strip() or "—",
            h1=os.path.basename(self.h1.text()), h2=os.path.basename(self.h2.text()),
            repi=self.sb_repi.value(), rjb=self.sb_rjb.value(),
            vs30=int(self.sb_vs.value()), ref_dd2=None, ref_dd1=None,
            default=False, checked=True,
            h1_path=self.h1.text(), h2_path=self.h2.text())


class RecordsPage(QWidget):
    changed = pyqtSignal()

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self._mut = False
        root = QVBoxLayout(self)
        root.setContentsMargins(SP6, SP6, SP6, SP6)
        root.setSpacing(SP4)

        bar = QHBoxLayout()
        bar.setSpacing(SP2)
        self.bt_folder = QPushButton("  Kayıt Klasörünü Tara")
        self.bt_folder.setObjectName("Primary")
        self.bt_folder.clicked.connect(self.scan_folder)
        self.bt_add = QPushButton("  Kayıt Ekle")
        self.bt_add.clicked.connect(self.add_record)
        self.bt_del = QPushButton("  Kaldır")
        self.bt_del.clicked.connect(self.remove_selected)
        self.bt_all = QPushButton("  Tümünü Seç")
        self.bt_all.clicked.connect(lambda: self._set_all(True))
        self.bt_none = QPushButton("  Seçimi Kaldır")
        self.bt_none.clicked.connect(lambda: self._set_all(False))
        for b in (self.bt_folder, self.bt_add, self.bt_del, self.bt_all, self.bt_none):
            bar.addWidget(b)
        bar.addStretch(1)
        self.chip_n = Chip("", "accent")
        self.chip_evt = Chip("", "ok")
        self.chip_ready = Chip("")
        for c in (self.chip_ready, self.chip_evt, self.chip_n):
            bar.addWidget(c)
        root.addLayout(bar)

        card = Card("Kayıt Kütüphanesi",
                    "Tablo 11 varsayılanları her açılışta seçili gelir · "
                    ".AT2 dosyaları PEER NGA biçimindedir")
        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(COLS)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        hh = self.table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft |
                               Qt.AlignmentFlag.AlignVCenter)
        hh.setMinimumSectionSize(26)
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for col, w in enumerate(COL_W):
            self.table.setColumnWidth(col, w)
        hh.setStretchLastSection(True)
        self.table.itemChanged.connect(self._item_changed)
        self.table.itemDoubleClicked.connect(self._edit_item)
        card.v.addWidget(self.table, 1)
        root.addWidget(card, 1)

        self.hint = Banner()
        root.addWidget(self.hint)
        self.populate()

    # ---------------------------------------------------------------
    def populate(self):
        th = theme_of(self)
        self._mut = True
        recs = self.state.records
        self.table.setRowCount(len(recs))
        for i, r in enumerate(recs):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Checked if r.checked
                              else Qt.CheckState.Unchecked)
            self.table.setItem(i, 0, chk)
            cells = [str(i + 1), r.event, f"{r.mag:.1f}" if r.mag else "—",
                     r.mech, r.station, r.h1, r.h2,
                     f"{r.repi:.1f}" if r.repi else "—",
                     f"{r.rjb:.1f}" if r.rjb else "—",
                     str(r.vs30) if r.vs30 else "—",
                     f"{r.ref_dd2:.2f}" if r.ref_dd2 else "—",
                     f"{r.ref_dd1:.2f}" if r.ref_dd1 else "—"]
            for j, txt in enumerate(cells, start=1):
                it = QTableWidgetItem(txt)
                it.setToolTip(txt)
                if j in (3, 8, 9, 10, 11, 12):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight |
                                        Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, j, it)
            st = QTableWidgetItem(("●  Hazır" if r.ready else "○  Dosya bekleniyor"))
            st.setForeground(QColor(th["ok"] if r.ready else th["text3"]))
            self.table.setItem(i, 13, st)
        self._mut = False
        self._update_chips()

    def _update_chips(self):
        th = theme_of(self)
        recs = self.state.records
        n_sel = sum(r.checked for r in recs)
        n_rdy = sum(r.checked and r.ready for r in recs)
        self.chip_n.setText(f"Seçili {n_sel} / min 11 (TBDY §2.5.1)")
        self.chip_n.set_kind("ok" if n_sel >= 11 else "warn")
        ev: dict[str, int] = {}
        for r in recs:
            if r.checked:
                ev[r.event] = ev.get(r.event, 0) + 1
        bad = [e for e, c in ev.items() if c > 3]
        self.chip_evt.setText("Aynı depremden ≤ 3 kayıt ✓" if not bad
                              else f"‘{bad[0]}’ > 3 kayıt!")
        self.chip_evt.set_kind("ok" if not bad else "err")
        self.chip_ready.setText(f"Dosyası hazır {n_rdy}/{n_sel}")
        self.chip_ready.set_kind("accent" if n_rdy == n_sel and n_sel else "")
        if not any(r.ready for r in recs):
            self.hint.show_msg(
                "info", "AT2 dosyalarını eşleştirmek için klasörü tarayın.",
                "“Kayıt Klasörünü Tara” ile Tablo 11 dosya adları alt klasörler dahil "
                "aranır ve otomatik eşleştirilir.", th)
        else:
            self.hint.hide()

    def _item_changed(self, it: QTableWidgetItem):
        if self._mut or it.column() != 0:
            return
        self.state.records[it.row()].checked = it.checkState() == Qt.CheckState.Checked
        self._update_chips()
        self.changed.emit()

    def _set_all(self, val: bool):
        for r in self.state.records:
            r.checked = val
        self.populate()
        self.changed.emit()

    def scan_folder(self):
        d = QFileDialog.getExistingDirectory(self, "AT2 kayıtlarının bulunduğu klasör")
        if not d:
            return
        index: dict[str, str] = {}
        for root, _dirs, files in os.walk(d):
            for fn in files:
                index.setdefault(fn.lower(), os.path.join(root, fn))
        # 1) Kütüphanedeki kayıtları dosya adına göre eşleştir
        hit = 0
        for r in self.state.records:
            p1, p2 = index.get(r.h1.lower()), index.get(r.h2.lower())
            if p1 and p2:
                r.h1_path, r.h2_path = p1, p2
                hit += 1

        # 2) Kalan dosyalardan PEER kayıt takımlarını otomatik kur
        used = {n for r in self.state.records if r.ready
                for n in (r.h1.lower(), r.h2.lower())}
        sets, n_vert, orphan = discover_sets(d)
        fresh = [s for s in sets
                 if s["h1"].lower() not in used and s["h2"].lower() not in used]

        added = 0
        if fresh:
            sel = QMessageBox.question(
                self, APP_NAME,
                f"Klasörde {len(fresh)} yeni kayıt takımı bulundu "
                f"(yatay bileşen çiftleri).\n"
                f"Düşey (UP/DWN) bileşenler hesaba katılmadı: {n_vert} dosya.\n\n"
                "Bu takımlar kütüphaneye eklensin ve ölçeklendirme için "
                "SEÇİLİ hale getirilsin mi?\n"
                "(Hayır → eklenir ama seçilmez)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes)
            if sel != QMessageBox.StandardButton.Cancel:
                mark = sel == QMessageBox.StandardButton.Yes
                for s in fresh:
                    self.state.records.append(GMRecord(
                        event=s["event"], mag=0.0, mech="—", station=s["station"],
                        h1=s["h1"], h2=s["h2"], repi=0.0, rjb=0.0, vs30=0,
                        ref_dd2=None, ref_dd1=None, default=False, checked=mark,
                        h1_path=s["h1_path"], h2_path=s["h2_path"]))
                    added += 1

        self.populate()
        self.changed.emit()

        th = theme_of(self)
        miss = [r for r in self.state.records if r.checked and not r.ready]
        sub = []
        if added:
            sub.append(f"{added} takım otomatik kuruldu")
        if n_vert:
            sub.append(f"{n_vert} düşey bileşen atlandı")
        if orphan:
            sub.append(f"{len(orphan)} dosya eşlenemedi")
        detail = " · ".join(sub) if sub else \
            "Ölçeklendirme sayfasından hesaplamayı başlatabilirsiniz."
        if miss:
            self.hint.show_msg(
                "warn",
                f"{hit + added} kayıt takımı hazır, {len(miss)} seçili kaydın "
                "dosyası bulunamadı.",
                "Eksik: " + ", ".join(r.h1 for r in miss[:3]) +
                (" …" if len(miss) > 3 else "") +
                ((" · " + detail) if sub else ""), th)
        else:
            self.hint.show_msg(
                "ok", f"{hit + added} kayıt takımının tamamı hazır.", detail, th)

    def add_record(self):
        dlg = RecordDialog(self)
        if dlg.exec():
            self.state.records.append(dlg.record())
            self.populate()
            self.changed.emit()

    def _edit_item(self, item: QTableWidgetItem):
        row = item.row()
        if not (0 <= row < len(self.state.records)) or item.column() == 0:
            return
        rec = self.state.records[row]
        dlg = RecordDialog(self, rec)
        if dlg.exec():
            dlg.apply_to(rec)
            self.populate()
            self.changed.emit()

    def remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        kept_default = False
        for row in rows:
            if self.state.records[row].default:
                kept_default = True
            else:
                del self.state.records[row]
        self.populate()
        self.changed.emit()
        if kept_default:
            QMessageBox.information(
                self, APP_NAME,
                "Tablo 11 varsayılan kayıtları kütüphaneden silinemez;\n"
                "hesaba katmamak için onay kutusunu kaldırmanız yeterlidir.")


# =============================================================================
# 10) SAYFA 3 — ÖLÇEKLENDİRME & GRAFİKLER
# =============================================================================
class ScalingPage(QWidget):
    computed = pyqtSignal()

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.worker: ComputeWorker | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(SP6, SP6, SP6, SP6)
        root.setSpacing(SP4)

        bar = QHBoxLayout()
        bar.setSpacing(SP3)
        self.bt_run = QPushButton("  TBDY 2018 Ölçeklendirmesini Hesapla")
        self.bt_run.setObjectName("Primary")
        self.bt_run.clicked.connect(self.compute)
        bar.addWidget(self.bt_run)

        seg = QFrame()
        seg.setObjectName("SegWrap")
        sl = QHBoxLayout(seg)
        sl.setContentsMargins(SP1, SP1, SP1, SP1)
        sl.setSpacing(0)
        self.bt_dd2 = QPushButton("DD-2")
        self.bt_dd1 = QPushButton("DD-1")
        grp = QButtonGroup(self)
        for b in (self.bt_dd2, self.bt_dd1):
            b.setObjectName("Seg")
            b.setCheckable(True)
            grp.addButton(b)
            sl.addWidget(b)
        self.bt_dd2.setChecked(True)
        grp.buttonClicked.connect(lambda *_: self.render())
        bar.addWidget(seg)

        self.progress = QProgressBar()
        self.progress.setFixedWidth(220)
        self.progress.hide()
        self.lbl_prog = QLabel("")
        self.lbl_prog.setObjectName("CardHint")
        bar.addWidget(self.progress)
        bar.addWidget(self.lbl_prog)
        bar.addStretch(1)
        root.addLayout(bar)

        self.banner = Banner()
        root.addWidget(self.banner)

        self.tabs = QTabWidget()
        self.tab_uns = QWidget(); self.tab_sc = QWidget()
        self.tab_f = QWidget();  self.tab_ts = QWidget()
        for w, name in ((self.tab_uns, "Ölçeksiz Spektrumlar"),
                        (self.tab_sc, "Ölçekli Spektrumlar"),
                        (self.tab_f, "Ölçek Katsayıları"),
                        (self.tab_ts, "İvme Serileri")):
            self.tabs.addTab(w, name)
        root.addWidget(self.tabs, 1)

        for tab, attr in ((self.tab_uns, "plot_uns"), (self.tab_sc, "plot_sc"),
                          (self.tab_f, "plot_f")):
            lay = QVBoxLayout(tab)
            lay.setContentsMargins(0, SP2, 0, 0)
            card = Card()
            pl = Plot(4.6)
            setattr(self, attr, pl)
            card.v.addWidget(pl, 1)
            lay.addWidget(card)

        lay = QVBoxLayout(self.tab_ts)
        lay.setContentsMargins(0, SP2, 0, 0)
        card = Card()
        top = QHBoxLayout()
        lb = QLabel("Kayıt")
        lb.setObjectName("FormLbl")
        self.cb_rec = QComboBox()
        self.cb_rec.currentIndexChanged.connect(lambda *_: self.render_ts())
        top.addWidget(lb)
        top.addWidget(self.cb_rec, 1)
        card.v.addLayout(top)
        self.plot_ts = Plot(4.2)
        card.v.addWidget(self.plot_ts, 1)
        lay.addWidget(card)

        self.empty = QLabel("Hesaplama henüz yapılmadı.\n"
                            "Kayıt kütüphanesinde dosyaları eşleştirin ve "
                            "“Hesapla” düğmesine basın.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setObjectName("PageDesc")
        root.addWidget(self.empty)
        self.tabs.hide()

    # ---------------------------------------------------------------
    def level(self) -> str:
        return "DD-2" if self.bt_dd2.isChecked() else "DD-1"

    def invalidate(self):
        if self.state.results is not None:
            self.state.results = None
            self.tabs.hide()
            self.empty.show()
            self.banner.show_msg(
                "warn", "Girdi verileri değişti — sonuçlar geçersiz.",
                "Güncel parametrelerle yeniden “Hesapla” çalıştırın.",
                self.window().theme)
            self.computed.emit()

    def compute(self):
        th = self.window().theme
        recs = [r for r in self.state.records if r.checked]
        missing = [r for r in recs if not r.ready]
        if not recs:
            self.banner.show_msg("err", "Seçili kayıt yok.",
                                 "Kayıt kütüphanesinden en az bir kayıt seçin.", th)
            return
        if missing:
            self.banner.show_msg(
                "err", f"{len(missing)} seçili kaydın .AT2 dosyası eksik.",
                "Kayıt kütüphanesinde “Kayıt Klasörünü Tara” ile dosyaları "
                "eşleştirin: " + ", ".join(r.h1 for r in missing[:3]) +
                (" …" if len(missing) > 3 else ""), th)
            return
        self.bt_run.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.lbl_prog.setText("Başlıyor…")
        self.worker = ComputeWorker(recs, self.state.periods)
        self.worker.progress.connect(self._on_prog)
        self.worker.done.connect(lambda data: self._on_done(recs, data))
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _on_prog(self, i: int, n: int, msg: str):
        self.progress.setMaximum(n)
        self.progress.setValue(i)
        self.lbl_prog.setText(f"Tepki spektrumu · {msg}  ({i}/{n})")

    def _on_fail(self, msg: str):
        self.bt_run.setEnabled(True)
        self.progress.hide()
        self.lbl_prog.setText("")
        self.banner.show_msg("err", "Hesaplama hatası", msg, self.window().theme)

    def _on_done(self, recs: list[GMRecord], data: dict):
        self.bt_run.setEnabled(True)
        self.progress.hide()
        self.lbl_prog.setText("")
        p, per = self.state.params, self.state.periods
        for r in recs:
            (r.dt1, r.acc1, r.sa1) = data[id(r)]["H1"]
            (r.dt2, r.acc2, r.sa2) = data[id(r)]["H2"]
        if p.mode3d:
            basis = [np.sqrt(r.sa1 ** 2 + r.sa2 ** 2) for r in recs]
            k = 1.3
        else:
            basis = [0.5 * (r.sa1 + r.sa2) for r in recs]
            k = 1.0
        levels = {}
        for lvl in ("DD-2", "DD-1"):
            sds, sd1, *_ = p.sds_sd1(lvl)
            sae = design_spectrum(per, sds, sd1)
            levels[lvl] = scale_set(per, basis, sae, p.tp, k) | dict(
                sae=sae, sds=sds, sd1=sd1)
        warns = []
        if len(recs) < 11:
            warns.append(f"Seçili kayıt sayısı {len(recs)} < 11 (TBDY §2.5.1.1).")
        ev: dict[str, int] = {}
        for r in recs:
            ev[r.event] = ev.get(r.event, 0) + 1
        for e, c in ev.items():
            if c > 3:
                warns.append(f"“{e}” depreminden {c} kayıt (> 3, TBDY §2.5.1.2).")
        self.state.results = dict(recs=recs, basis=basis, levels=levels,
                                  warns=warns, mode3d=p.mode3d,
                                  tp=p.tp, periods=per)
        self.cb_rec.blockSignals(True)
        self.cb_rec.clear()
        self.cb_rec.addItems([r.label for r in recs])
        self.cb_rec.blockSignals(False)
        self.empty.hide()
        self.tabs.show()
        self.render()
        self.computed.emit()

    # ---------------------------------------------------------------
    def render(self):
        if not self.state.results:
            return
        th = self.window().theme
        R = self.state.results
        lvl = self.level()
        L = R["levels"][lvl]
        per, tp = R["periods"], R["tp"]
        k = L["k"]

        head = (f"Ortalama / hedef en düşük oranı "
                f"{L['min_ratio']:.3f}  (T = {L['t_crit']:.2f} s) · "
                f"grup katsayısı g = {L['g']:.3f}")
        if L["passed"] and not R["warns"]:
            self.banner.show_msg(
                "ok", f"TBDY 2018 §2.5 koşulu sağlandı — {lvl}", head, th)
        elif L["passed"]:
            self.banner.show_msg(
                "warn", f"Spektrum koşulu sağlandı ({lvl}) — seçim uyarıları var",
                head + "  ·  " + "  ".join(R["warns"]), th)
        else:
            self.banner.show_msg("err", f"Koşul sağlanamadı — {lvl}", head, th)

        x0, x1 = 0.05 * tp, min(3.0 * tp, per.max())

        # -- Ölçeksiz --
        pl = self.plot_uns
        pl.fig.clear()
        ax = pl.fig.add_subplot(111)
        ax.axvspan(0.2 * tp, 1.5 * tp, color=th["accent"], alpha=0.08, lw=0)
        for b in R["basis"]:
            ax.plot(per, b, color=th["series"], lw=0.9, alpha=0.75)
        ax.plot([], [], color=th["series"], lw=0.9,
                label="Kayıt spektrumları" + (" (SRSS)" if R["mode3d"] else ""))
        ax.plot(per, L["mean_unscaled"], color=th["text"], lw=2.4, label="Ortalama")
        ax.plot(per, L["sae"], color=th["err"], lw=1.6, ls="--", label=f"Sae · {lvl}")
        if k != 1.0:
            ax.plot(per, L["target"], color=th["err"], lw=2.2,
                    label=f"{k:.1f}·Sae (hedef)")
        ax.set_xlim(x0, x1)
        ax.set_ylim(bottom=0)
        pl.style(ax, th, "Periyot T (s)", "Sa (g)")
        pl.legend(ax, th, loc="upper right")
        pl.draw_idle()

        # -- Ölçekli --
        pl = self.plot_sc
        pl.fig.clear()
        ax = pl.fig.add_subplot(111)
        ax.axvspan(0.2 * tp, 1.5 * tp, color=th["accent"], alpha=0.08, lw=0)
        for f, b in zip(L["F"], R["basis"]):
            ax.plot(per, f * b, color=th["series"], lw=0.9, alpha=0.75)
        ax.plot([], [], color=th["series"], lw=0.9, label="Ölçekli kayıtlar")
        ax.plot(per, L["mean_scaled"], color=th["accent"], lw=2.6,
                label="Ölçekli ortalama")
        ax.plot(per, L["target"], color=th["err"], lw=2.2, ls="--",
                label=f"{k:.1f}·Sae · {lvl}")
        ax.plot(L["t_crit"],
                np.interp(L["t_crit"], per, L["mean_scaled"]), "o",
                color=th["err"], ms=6,
                label=f"Kritik nokta (oran {L['min_ratio']:.3f})")
        ax.set_xlim(x0, x1)
        ax.set_ylim(bottom=0)
        pl.style(ax, th, "Periyot T (s)", "Sa (g)")
        pl.legend(ax, th, loc="upper right")
        pl.draw_idle()

        # -- Katsayılar --
        pl = self.plot_f
        pl.fig.clear()
        ax = pl.fig.add_subplot(111)
        recs = R["recs"]
        xs = np.arange(len(recs))
        ax.bar(xs, L["F"], 0.62, color=th["accent"], alpha=0.9,
               label=f"VERITAS F = f·g · {lvl}")
        refs = [(i, (r.ref_dd2 if lvl == "DD-2" else r.ref_dd1))
                for i, r in enumerate(recs) if r.default]
        if refs:
            ax.plot([i for i, _ in refs], [v for _, v in refs], "D",
                    color=th["warn"], ms=6, ls="", label="Tablo 11 referansı")
        for x, v in zip(xs, L["F"]):
            ax.annotate(f"{v:.2f}", (x, v), textcoords="offset points",
                        xytext=(0, 4), ha="center", fontsize=8, color=th["text2"])
        ax.set_xticks(xs, [r.station[:14] for r in recs], rotation=35,
                      ha="right", fontsize=8)
        ax.set_ylim(bottom=0)
        pl.style(ax, th, "", "Ölçek katsayısı F")
        pl.legend(ax, th, loc="upper left")
        pl.draw_idle()

        self.render_ts()

    def render_ts(self):
        if not self.state.results or self.cb_rec.currentIndex() < 0:
            return
        th = self.window().theme
        R = self.state.results
        L = R["levels"][self.level()]
        r = R["recs"][self.cb_rec.currentIndex()]
        F = L["F"][self.cb_rec.currentIndex()]
        pl = self.plot_ts
        pl.fig.clear()
        axs = pl.fig.subplots(2, 1, sharex=True)
        for ax, acc, dt, name in ((axs[0], r.acc1, r.dt1, "H1 · " + r.h1),
                                  (axs[1], r.acc2, r.dt2, "H2 · " + r.h2)):
            t = np.arange(acc.size) * dt
            a = F * acc
            ax.plot(t, a, color=th["accent"], lw=0.8)
            pga = float(np.max(np.abs(a)))
            ax.set_title(f"{name}   ·   F = {F:.3f}   ·   PGA = {pga:.3f} g",
                         color=th["text2"], fontsize=9, loc="left")
            pl.style(ax, th, "", "a (g)")
            ax.set_xlim(0, t[-1])
        axs[1].set_xlabel("Zaman (s)", color=th["text2"], fontsize=10)
        pl.draw_idle()


# =============================================================================
# 11) SAYFA 4 — RAPOR & DIŞA AKTARIM
# =============================================================================
class ReportPage(QWidget):
    def __init__(self, state: AppState, scaling: ScalingPage):
        super().__init__()
        self.state = state
        self.scaling = scaling

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("Scroller")
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(SP6, SP6, SP6, SP6)
        root.setSpacing(SP4)

        row = QHBoxLayout()
        row.setSpacing(SP3)
        self.sc_n = StatCard("Seçili kayıt takımı")
        self.sc_m = StatCard("Yöntem")
        self.sc_g2 = StatCard("Grup katsayısı g · DD-2")
        self.sc_g1 = StatCard("Grup katsayısı g · DD-1")
        for c in (self.sc_n, self.sc_m, self.sc_g2, self.sc_g1):
            row.addWidget(c, 1)
        root.addLayout(row)

        self.banner = Banner()
        root.addWidget(self.banner)

        self.card_tbl = Card("Ölçek Katsayıları Özeti",
                             "F = f (bireysel, EKK) × g (grup)")
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["No", "Deprem", "İstasyon", "Mw",
             "F · DD-2", "Tablo 11 · DD-2", "F · DD-1", "Tablo 11 · DD-1", "Durum"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setShowGrid(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(392)
        self.card_tbl.v.addWidget(self.table, 1)
        root.addWidget(self.card_tbl, 1)

        exp = Card("Dışa Aktarım", "Tez ve rapor kullanımı için")
        eb = QHBoxLayout()
        eb.setSpacing(SP2)
        self.bt_csv = QPushButton("  Katsayılar (CSV)")
        self.bt_spc = QPushButton("  Spektrumlar (CSV)")
        self.bt_png = QPushButton("  Grafikler (PNG · 300 dpi)")
        self.bt_ts = QPushButton("  Ölçekli İvme Serileri (TXT)")
        self.bt_csv.clicked.connect(self.exp_csv)
        self.bt_spc.clicked.connect(self.exp_spectra)
        self.bt_png.clicked.connect(self.exp_png)
        self.bt_ts.clicked.connect(self.exp_series)
        for b in (self.bt_csv, self.bt_spc, self.bt_png, self.bt_ts):
            eb.addWidget(b)
        eb.addStretch(1)
        exp.v.addLayout(eb)
        root.addWidget(exp)
        root.addStretch(1)

    # ---------------------------------------------------------------
    def refresh(self):
        th = self.window().theme
        R = self.state.results
        if not R:
            self.sc_n.val.setText("—")
            self.sc_m.val.setText("—")
            self.sc_g2.val.setText("—")
            self.sc_g1.val.setText("—")
            self.table.setRowCount(0)
            for b in (self.bt_csv, self.bt_spc, self.bt_png, self.bt_ts):
                b.setEnabled(False)
            self.banner.show_msg(
                "info", "Rapor için önce ölçeklendirmeyi hesaplayın.",
                "Sonuçlar hesaplandığında katsayı tablosu ve dışa aktarım "
                "burada etkinleşir.", th)
            return
        for b in (self.bt_csv, self.bt_spc, self.bt_png, self.bt_ts):
            b.setEnabled(True)
        recs = R["recs"]
        L2, L1 = R["levels"]["DD-2"], R["levels"]["DD-1"]
        self.sc_n.val.setText(f"{len(recs)}  /  min 11")
        self.sc_m.val.setText("SRSS · 1.3·Sae" if R["mode3d"] else "2B · 1.0·Sae")
        self.sc_g2.val.setText(f"{L2['g']:.3f}")
        self.sc_g1.val.setText(f"{L1['g']:.3f}")
        ok = L2["passed"] and L1["passed"]
        if ok and not R["warns"]:
            self.banner.show_msg(
                "ok", "TBDY 2018 §2.5 — her iki deprem düzeyi için sağlandı.",
                f"DD-2: en düşük oran {L2['min_ratio']:.3f} (T={L2['t_crit']:.2f} s) · "
                f"DD-1: {L1['min_ratio']:.3f} (T={L1['t_crit']:.2f} s) · "
                f"Bant {0.2*R['tp']:.2f}–{1.5*R['tp']:.2f} s", th)
        else:
            self.banner.show_msg(
                "warn" if ok else "err",
                "Sonuçları kontrol ediniz.",
                "  ".join(R["warns"]) if R["warns"] else "Spektrum koşulu sağlanamadı.",
                th)
        self.table.setRowCount(len(recs))
        for i, r in enumerate(recs):
            vals = [str(i + 1), r.event, r.station, f"{r.mag:.1f}",
                    f"{L2['F'][i]:.3f}",
                    f"{r.ref_dd2:.2f}" if r.ref_dd2 else "—",
                    f"{L1['F'][i]:.3f}",
                    f"{r.ref_dd1:.2f}" if r.ref_dd1 else "—"]
            for j, txt in enumerate(vals):
                it = QTableWidgetItem(txt)
                if j >= 3:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight |
                                        Qt.AlignmentFlag.AlignVCenter)
                if j in (4, 6):
                    f = it.font(); f.setBold(True); it.setFont(f)
                    it.setForeground(QColor(th["accent"]))
                self.table.setItem(i, j, it)
            st = QTableWidgetItem("✓")
            st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            st.setForeground(QColor(th["ok"]))
            self.table.setItem(i, 8, st)

    # ---------------------------------------------------------------
    def _save(self, caption: str, default: str, filt: str) -> str:
        p, _ = QFileDialog.getSaveFileName(self, caption, default, filt)
        return p

    def exp_csv(self):
        R = self.state.results
        p = self._save("Katsayıları kaydet", "veritas_katsayilar.csv", "CSV (*.csv)")
        if not p:
            return
        L2, L1 = R["levels"]["DD-2"], R["levels"]["DD-1"]
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["No", "Deprem", "Mw", "Fay Mekanizmasi", "Istasyon",
                        "H1", "H2", "Episantr (km)", "En Kisa (km)", "Vs30",
                        "f_DD2", "g_DD2", "F_DD2", "Tablo11_DD2",
                        "f_DD1", "g_DD1", "F_DD1", "Tablo11_DD1"])
            for i, r in enumerate(R["recs"]):
                w.writerow([i + 1, r.event, r.mag, r.mech, r.station, r.h1, r.h2,
                            r.repi, r.rjb, r.vs30,
                            f"{L2['f'][i]:.4f}", f"{L2['g']:.4f}", f"{L2['F'][i]:.4f}",
                            r.ref_dd2 or "",
                            f"{L1['f'][i]:.4f}", f"{L1['g']:.4f}", f"{L1['F'][i]:.4f}",
                            r.ref_dd1 or ""])
        QMessageBox.information(self, APP_NAME, f"Kaydedildi:\n{p}")

    def exp_spectra(self):
        R = self.state.results
        p = self._save("Spektrumları kaydet", "veritas_spektrumlar.csv", "CSV (*.csv)")
        if not p:
            return
        per = R["periods"]
        L2, L1 = R["levels"]["DD-2"], R["levels"]["DD-1"]
        cols = [("T_s", per),
                ("Sae_DD2_g", L2["sae"]), ("Hedef_DD2_g", L2["target"]),
                ("OlcekliOrt_DD2_g", L2["mean_scaled"]),
                ("Sae_DD1_g", L1["sae"]), ("Hedef_DD1_g", L1["target"]),
                ("OlcekliOrt_DD1_g", L1["mean_scaled"])]
        for i, r in enumerate(R["recs"]):
            cols.append((f"SRSS_{i+1:02d}_g", R["basis"][i]))
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow([c for c, _ in cols])
            for k in range(per.size):
                w.writerow([f"{arr[k]:.6f}" for _, arr in cols])
        QMessageBox.information(self, APP_NAME, f"Kaydedildi:\n{p}")

    def exp_png(self):
        d = QFileDialog.getExistingDirectory(self, "PNG klasörü seç")
        if not d:
            return
        pairs = [(self.scaling.plot_uns, "olceksiz_spektrumlar"),
                 (self.scaling.plot_sc, "olcekli_spektrumlar"),
                 (self.scaling.plot_f, "olcek_katsayilari"),
                 (self.scaling.plot_ts, "ivme_serisi")]
        lvl = self.scaling.level()
        for pl, name in pairs:
            pl.fig.savefig(os.path.join(d, f"veritas_{name}_{lvl}.png"),
                           dpi=300, facecolor=pl.fig.get_facecolor(),
                           bbox_inches="tight")
        QMessageBox.information(self, APP_NAME,
                                f"{len(pairs)} grafik kaydedildi ({lvl}):\n{d}")

    def exp_series(self):
        R = self.state.results
        d = QFileDialog.getExistingDirectory(self, "Ölçekli seriler için klasör seç")
        if not d:
            return
        n = 0
        for lvl in ("DD-2", "DD-1"):
            F = R["levels"][lvl]["F"]
            sub = os.path.join(d, lvl.replace("-", ""))
            os.makedirs(sub, exist_ok=True)
            for i, r in enumerate(R["recs"]):
                for comp, dt, acc, fn in (("H1", r.dt1, r.acc1, r.h1),
                                          ("H2", r.dt2, r.acc2, r.h2)):
                    t = np.arange(acc.size) * dt
                    out = os.path.join(
                        sub, os.path.splitext(fn)[0] + f"_F{F[i]:.3f}.txt")
                    header = (f"VERITAS TBDY2018 olcekli kayit  {lvl}  "
                              f"{r.event} {r.station} {comp}\n"
                              f"F={F[i]:.5f}  NPTS={acc.size}  DT={dt:.6f} s  "
                              f"birim: g\n t(s)\t a(g)")
                    np.savetxt(out, np.column_stack([t, F[i] * acc]),
                               fmt="%.6f\t%.7e", header=header)
                    n += 1
        QMessageBox.information(self, APP_NAME,
                                f"{n} ölçekli seri kaydedildi:\n{d}")


# =============================================================================
# 12) ANA PENCERE
# =============================================================================
PAGES = [
    ("spectrum", "Spektrum Parametreleri", "Hedef tasarım spektrumları (DD-2 · DD-1)"),
    ("records",  "Kayıt Kütüphanesi",      "Tablo 11 varsayılanları + kullanıcı kayıtları"),
    ("scale",    "Ölçeklendirme",          "TBDY 2018 §2.5 basit ölçeklendirme ve grafikler"),
    ("report",   "Rapor & Dışa Aktarım",   "Katsayı özeti · CSV / PNG / TXT çıktıları"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark = False
        self.theme = LIGHT
        self.state = AppState()
        self.setWindowTitle(f"{APP_NAME} — {APP_SUB}")
        self.resize(1440, 880)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Kenar çubuğu ----
        side = QFrame()
        side.setObjectName("Sidebar")
        side.setFixedWidth(240)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(SP4, SP5, SP4, SP4)
        sv.setSpacing(SP2)
        brand_row = QHBoxLayout()
        brand_row.setSpacing(SP2)
        self.logo = icon_label(ICO["logo"], LIGHT["sidebar_act"], 26)
        bx = QVBoxLayout()
        bx.setSpacing(0)
        b1 = QLabel(APP_NAME)
        b1.setObjectName("Brand")
        b2 = QLabel("TBDY 2018 · Kayıt Ölçekleme")
        b2.setObjectName("BrandSub")
        bx.addWidget(b1)
        bx.addWidget(b2)
        brand_row.addWidget(self.logo)
        brand_row.addLayout(bx)
        brand_row.addStretch(1)
        sv.addLayout(brand_row)
        sv.addSpacing(SP4)

        self.nav_group = QButtonGroup(self)
        self.nav_btns: list[QToolButton] = []
        for i, (key, title, _desc) in enumerate(PAGES):
            bt = QToolButton()
            bt.setObjectName("NavBtn")
            bt.setText("  " + title.replace("&", "&&"))
            bt.setCheckable(True)
            bt.setFixedHeight(40)
            bt.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            bt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            bt.setIconSize(QSize(20, 20))
            self.nav_group.addButton(bt, i)
            self.nav_btns.append(bt)
            sv.addWidget(bt)
        self.nav_group.idClicked.connect(self.goto)
        sv.addStretch(1)

        self.bt_theme = QToolButton()
        self.bt_theme.setObjectName("ThemeBtn")
        self.bt_theme.setFixedHeight(38)
        self.bt_theme.setSizePolicy(QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Fixed)
        self.bt_theme.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.bt_theme.setIconSize(QSize(18, 18))
        self.bt_theme.clicked.connect(self.toggle_theme)
        sv.addWidget(self.bt_theme)
        foot = QLabel(f"{APP_NAME} {APP_VER} · TBDY 2018 §2.5")
        foot.setObjectName("SideFoot")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sv.addWidget(foot)
        root.addWidget(side)

        # ---- İçerik ----
        content = QWidget()
        content.setObjectName("Content")
        cv = QVBoxLayout(content)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(64)
        hv = QHBoxLayout(header)
        hv.setContentsMargins(SP6, 0, SP6, 0)
        tb = QVBoxLayout()
        tb.setSpacing(0)
        self.lb_title = QLabel()
        self.lb_title.setObjectName("PageTitle")
        self.lb_desc = QLabel()
        self.lb_desc.setObjectName("PageDesc")
        tb.addWidget(self.lb_title)
        tb.addWidget(self.lb_desc)
        hv.addLayout(tb)
        hv.addStretch(1)
        ver = QLabel(f"Basit ölçeklendirme · en az 11 kayıt · {APP_VER}")
        ver.setObjectName("VerChip")
        hv.addWidget(ver, 0, Qt.AlignmentFlag.AlignVCenter)
        cv.addWidget(header)

        self.stack = QStackedWidget()
        self.page_spec = SpectrumPage(self.state)
        self.page_recs = RecordsPage(self.state)
        self.page_scale = ScalingPage(self.state)
        self.page_rep = ReportPage(self.state, self.page_scale)
        for w in (self.page_spec, self.page_recs, self.page_scale, self.page_rep):
            self.stack.addWidget(w)
        cv.addWidget(self.stack, 1)
        root.addWidget(content, 1)

        self.page_spec.changed.connect(self.page_scale.invalidate)
        self.page_recs.changed.connect(self.page_scale.invalidate)
        self.page_scale.computed.connect(self.page_rep.refresh)

        act = QAction(self)
        act.setShortcut(QKeySequence("F5"))
        act.triggered.connect(self.page_scale.compute)
        self.addAction(act)

        self.apply_theme()
        self.nav_btns[0].setChecked(True)
        self.goto(0)

    # ---------------------------------------------------------------
    def goto(self, i: int):
        self.stack.setCurrentIndex(i)
        self.lb_title.setText(PAGES[i][1])
        self.lb_desc.setText(PAGES[i][2])
        if i == 3:
            self.page_rep.refresh()

    def toggle_theme(self):
        self.dark = not self.dark
        self.apply_theme()

    def apply_theme(self):
        th = DARK if self.dark else LIGHT
        self.theme = th
        QApplication.instance().setStyleSheet(build_qss(th))
        nav_icons = ("spectrum", "records", "scale", "report")
        for bt, key in zip(self.nav_btns, nav_icons):
            bt.setIcon(char_icon(ICO[key], th["sidebar_txt"]))
        self.logo.setStyleSheet(f"color:{th['sidebar_act']}; background:transparent;")
        self.bt_theme.setText("  Gündüz Modu" if self.dark else "  Gece Modu")
        self.bt_theme.setIcon(char_icon(ICO["light" if self.dark else "dark"],
                                        th["sidebar_txt"], 18))
        self.page_recs.bt_folder.setIcon(char_icon(ICO["folder"], th["on_accent"], 18))
        self.page_recs.bt_add.setIcon(char_icon(ICO["add"], th["text2"], 18))
        self.page_recs.bt_del.setIcon(char_icon(ICO["trash"], th["text2"], 18))
        self.page_recs.bt_all.setIcon(char_icon(ICO["all"], th["text2"], 18))
        self.page_recs.bt_none.setIcon(char_icon(ICO["none"], th["text2"], 18))
        self.page_scale.bt_run.setIcon(char_icon(ICO["run"], th["on_accent"], 18))
        for b in (self.page_rep.bt_csv, self.page_rep.bt_spc,
                  self.page_rep.bt_png, self.page_rep.bt_ts):
            b.setIcon(char_icon(ICO["export"], th["text2"], 18))
        self.page_spec.refresh(th)
        self.page_recs.populate()
        if self.state.results:
            self.page_scale.render()
        self.page_rep.refresh()


# =============================================================================
# 13) GİRİŞ NOKTASI
# =============================================================================
def load_fonts():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    if os.path.isdir(base):
        for fn in os.listdir(base):
            if fn.lower().endswith((".ttf", ".otf")):
                QFontDatabase.addApplicationFont(os.path.join(base, fn))
        for fn in ("Inter-Regular.ttf",):
            p = os.path.join(base, fn)
            if os.path.exists(p):
                _fm.fontManager.addfont(p)
    fams = QFontDatabase.families()
    global FONT_HEAD, FONT_BODY
    if FONT_HEAD not in fams:
        FONT_HEAD = "Segoe UI"
    if FONT_BODY not in fams:
        FONT_BODY = "Segoe UI"
    matplotlib.rcParams["font.family"] = ("Inter" if "Inter" in fams
                                          else "DejaVu Sans")
    matplotlib.rcParams["axes.unicode_minus"] = False


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    load_fonts()
    app.setFont(QFont(FONT_BODY, 10))
    win = MainWindow()
    win.setWindowIcon(char_icon(ICO["logo"], LIGHT["accent"], 48))
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
