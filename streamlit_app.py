# -*- coding: utf-8 -*-
"""VERITAS tasarım dilinde Streamlit uygulaması.

Kabuk (kenar çubuğu · başlık şeridi · kartlar · rozetler · durum şeritleri)
ve gündüz/gece tema çifti, VERITAS masaüstü programının tasarım
jetonlarından türetilmiştir — bkz. `veritas_theme.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.figure import Figure

import veritas_theme as vt

APP_NAME = "VERITAS"
APP_SUB = "TBDY 2018 · Kayıt Ölçekleme"
APP_VER = "v1.0"

PAGES = [
    ("Genel Bakış", "Özet göstergeler, durum şeridi ve seri grafikleri"),
    ("Bileşenler", "Kart · rozet · düğme · girdi · sekme örnekleri"),
    ("Veri Tablosu", "Süzgeçli kayıt listesi ve ölçekleme katsayıları"),
    ("Renk & Tipografi", "Tasarım jetonları: palet, yazı tipi ölçeği, boşluk"),
]


# =============================================================================
# 1) BİLEŞENLER
# =============================================================================
def page_header(title: str, desc: str, chip: str) -> None:
    st.markdown(
        f"""<div class="vt-header">
          <div>
            <div class="vt-header-title">{title}</div>
            <div class="vt-header-desc">{desc}</div>
          </div>
          <div class="vt-verchip">{chip}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def card(title: str, body: str, hint: str = "") -> str:
    hint_html = f'<div class="vt-card-hint">{hint}</div>' if hint else ""
    return (f'<div class="vt-card"><div class="vt-card-head">'
            f'<div class="vt-card-title">{title}</div>{hint_html}</div>'
            f'<div class="vt-card-body">{body}</div></div>')


def stat(label: str, value: str, delta: str = "", up: bool | None = None) -> str:
    cls = "up" if up else ("down" if up is False else "")
    delta_html = (f'<div class="vt-stat-delta {cls}">{delta}</div>'
                  if delta else "")
    return (f'<div class="vt-stat"><div class="vt-stat-val">{value}</div>'
            f'<div class="vt-stat-lbl">{label}</div>{delta_html}</div>')


def chip(text: str, kind: str = "") -> str:
    return f'<span class="vt-chip {kind}">{text}</span>'


def banner(kind: str, title: str, sub: str = "") -> str:
    ico = {"ok": "✓", "err": "✕", "warn": "!", "info": "i"}[kind]
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    return (f'<div class="vt-banner {kind}"><div class="ico">{ico}</div>'
            f'<div><div class="ttl">{title}</div>{sub_html}</div></div>')


def kv(rows: list[tuple[str, str]]) -> str:
    items = "".join(f'<div class="vt-kv"><span class="k">{k}</span>'
                    f'<span class="v">{v}</span></div>' for k, v in rows)
    return f"<div>{items}</div>"


def swatch(name: str, hex_code: str) -> str:
    return (f'<div class="vt-swatch"><div class="box" '
            f'style="background:{hex_code}"></div><div class="meta">'
            f'<div class="name">{name}</div>'
            f'<div class="hex">{hex_code.upper()}</div></div></div>')


# =============================================================================
# 2) ÖRNEK VERİ
# =============================================================================
@st.cache_data
def sample_series() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    T = np.logspace(np.log10(0.02), np.log10(8.0), 160)
    rng = np.random.default_rng(7)
    target = np.where(T < 0.6, 0.9, 0.54 / T)
    a = target * (1.0 + 0.28 * np.sin(6 * np.log(T)) + 0.05 * rng.standard_normal(T.size))
    b = target * (1.0 + 0.22 * np.cos(5 * np.log(T)) + 0.05 * rng.standard_normal(T.size))
    return T, target, np.abs(a), np.abs(b)


@st.cache_data
def sample_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Deprem": ["Chuetsu-oki", "Cape Mendocino", "Darfield", "Duzce",
                       "Hector Mine", "Imperial Valley", "Kobe", "Kocaeli",
                       "Landers", "Loma Prieta", "Manjil"],
            "Mw": [6.8, 7.0, 7.0, 7.1, 7.1, 6.5, 6.9, 7.5, 7.3, 6.9, 7.4],
            "İstasyon": ["Matsushiro", "Fortuna Blvd", "Christchurch", "Bolu",
                         "Hector", "El Centro", "Nishi-Akashi", "Arcelik",
                         "Yermo", "Gilroy #3", "Abbar"],
            "Rjb (km)": [25.0, 15.9, 13.4, 12.0, 10.4, 12.9, 7.1, 13.5,
                         23.6, 12.2, 12.6],
            "Vs30 (m/s)": [640, 457, 344, 294, 726, 213, 609, 523,
                           354, 350, 724],
            "F (DD-2)": [2.10, 1.42, 1.09, 0.88, 1.63, 1.21, 0.97, 1.35,
                         1.18, 1.04, 0.91],
            "F (DD-1)": [3.58, 2.31, 1.77, 1.44, 2.66, 1.98, 1.58, 2.20,
                         1.92, 1.70, 1.49],
            "Durum": ["Uygun", "Uygun", "Uygun", "Sınırda", "Uygun", "Uygun",
                      "Uygun", "Uygun", "Sınırda", "Uygun", "Uygun"],
        }
    )


# =============================================================================
# 3) SAYFALAR
# =============================================================================
def page_overview(t: dict, dark: bool) -> None:
    st.markdown(
        banner("ok", "Ölçekleme ölçütü sağlandı",
               "Ortalama SRSS spektrumu, 0.2·Tp – 1.5·Tp bandının tamamında "
               "1.3·Sae(T) hedefinin üzerinde kalıyor."),
        unsafe_allow_html=True,
    )

    cols = st.columns(4, gap="small")
    stats = [
        ("Seçili kayıt takımı", "11", "TBDY alt sınırı 11", True),
        ("En düşük oran", "1.04", "+4% pay", True),
        ("Kritik periyot", "0.86 s", "band içi", None),
        ("Ortalama katsayı F", "1.62", "DD-2", None),
    ]
    for col, (lbl, val, delta, up) in zip(cols, stats):
        col.markdown(stat(lbl, val, delta, up), unsafe_allow_html=True)

    st.markdown('<div class="vt-sep"></div>', unsafe_allow_html=True)

    left, right = st.columns([2, 1], gap="medium")

    with left:
        T, target, a, b = sample_series()
        colors = vt.series_colors(dark)
        fig = Figure(figsize=(7.6, 4.1), dpi=110, layout="constrained")
        ax = fig.add_subplot(111)
        ax.plot(T, a, lw=1.2, color=t["series"], label="Kayıt takımı 1")
        ax.plot(T, b, lw=1.2, color=colors[3], alpha=0.75,
                label="Kayıt takımı 2")
        ax.plot(T, target, lw=2.2, color=colors[0], label="Hedef 1.3·Sae(T)")
        ax.set_xscale("log")
        vt.style_axes(fig, ax, t, "Periyot T (s)", "Sa (g)")
        vt.style_legend(ax, t, loc="upper right")
        st.pyplot(fig, use_container_width=True)

    with right:
        st.markdown(
            card(
                "Analiz özeti",
                kv([("Analiz türü", "3B · SRSS"),
                    ("Zemin sınıfı", "ZD"),
                    ("Tp", "0.62 s"),
                    ("SDS / SD1", "1.12 / 0.48"),
                    ("TA / TB", "0.086 / 0.429 s"),
                    ("Sönüm", "%5")]),
                hint="DD-2",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="height:{vt.SP3}px"></div>'
            + card(
                "Denetimler",
                f'<div class="vt-row">{chip("11 kayıt takımı", "ok")}'
                f'{chip("Aynı depremden ≤ 3", "ok")}'
                f'{chip("2 sınırda kayıt", "warn")}'
                f'{chip("Düşey bileşen yok", "accent")}</div>',
                hint="TBDY §2.5.1",
            ),
            unsafe_allow_html=True,
        )


def page_components(t: dict, dark: bool) -> None:
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        st.markdown(card(
            "Kart",
            "Yüzey rengi <strong>surface</strong>, 1 px <strong>border</strong> "
            "çerçeve ve 14 px köşe yarıçapı. Başlık Hanken Grotesk / Inter "
            "Bold, gövde Inter Regular 12.5 px.",
            hint="RAD_L · 14 px",
        ), unsafe_allow_html=True)

        st.markdown(f'<div style="height:{vt.SP3}px"></div>', unsafe_allow_html=True)
        st.markdown(card(
            "Rozetler",
            f'<div class="vt-row">{chip("nötr")}{chip("vurgu", "accent")}'
            f'{chip("uygun", "ok")}{chip("uyarı", "warn")}{chip("hata", "err")}'
            f"</div>",
            hint="Chip",
        ), unsafe_allow_html=True)

        st.markdown(f'<div style="height:{vt.SP3}px"></div>', unsafe_allow_html=True)
        st.markdown("##### Durum şeritleri")
        for kind, ttl, sub in [
            ("info", "Bilgi", "Kayıt klasörü taraması alt klasörleri de kapsar."),
            ("ok", "Başarılı", "Ölçekleme katsayıları hesaplandı."),
            ("warn", "Uyarı", "Aynı depremden 3'ten fazla kayıt seçildi."),
            ("err", "Hata", "NPTS/DT başlığı bulunamadı (.AT2 biçimi bekleniyor)."),
        ]:
            st.markdown(banner(kind, ttl, sub), unsafe_allow_html=True)

    with c2:
        st.markdown("##### Düğmeler")
        b1, b2, b3 = st.columns(3)
        b1.button("Hesapla", type="primary", use_container_width=True)
        b2.button("Klasör Seç", use_container_width=True)
        b3.button("Dışa Aktar", use_container_width=True, disabled=True)

        st.markdown('<div class="vt-sep"></div>', unsafe_allow_html=True)
        st.markdown("##### Girdiler")
        i1, i2 = st.columns(2)
        i1.selectbox("Yerel zemin sınıfı", ["ZA", "ZB", "ZC", "ZD", "ZE"], index=3)
        i2.number_input("Yapı periyodu Tp (s)", 0.05, 5.0, 0.62, 0.01)
        st.slider("Sönüm oranı ξ (%)", 1, 20, 5)
        st.text_input("Kayıt klasörü", placeholder="…/PEER_NGA_West2/records")
        st.checkbox("Tablo 11 varsayılan kayıtlarını dâhil et", value=True)

        st.markdown('<div class="vt-sep"></div>', unsafe_allow_html=True)
        st.markdown("##### Sekmeler ve ilerleme")
        tab1, tab2 = st.tabs(["Ölçeksiz", "Ölçekli"])
        with tab1:
            st.markdown('<div class="vt-card-body">Ham tepki spektrumları — '
                        "genlik düzeltmesi uygulanmadan.</div>",
                        unsafe_allow_html=True)
        with tab2:
            st.markdown('<div class="vt-card-body">F = f × g katsayılarıyla '
                        "ölçeklenmiş spektrumlar.</div>",
                        unsafe_allow_html=True)
        st.progress(0.72, text="Tepki spektrumu hesabı · 8/11")


def page_table(t: dict, dark: bool) -> None:
    df = sample_table()

    f1, f2, f3 = st.columns([2, 1, 1], gap="small")
    q = f1.text_input("Ara", placeholder="Deprem veya istasyon adı",
                      label_visibility="collapsed")
    mw_min = f2.number_input("En küçük Mw", 6.0, 8.0, 6.0, 0.1)
    only_ok = f3.checkbox("Yalnız uygun kayıtlar")

    view = df[df["Mw"] >= mw_min]
    if q:
        # düz metin araması: "[" gibi girdiler düzenli ifade hatası vermesin
        mask = (view["Deprem"].str.contains(q, case=False, na=False, regex=False)
                | view["İstasyon"].str.contains(q, case=False, na=False,
                                                regex=False))
        view = view[mask]
    if only_ok:
        view = view[view["Durum"] == "Uygun"]

    mean_txt = ("Ortalama F(DD-2) = %.2f" % view["F (DD-2)"].mean()
                if len(view) else "Eşleşen kayıt yok")
    st.markdown(
        f'<div class="vt-row" style="margin:{vt.SP2}px 0 {vt.SP3}px">'
        + chip(f"{len(view)} / {len(df)} kayıt takımı", "accent")
        + chip(mean_txt)
        + "</div>",
        unsafe_allow_html=True,
    )

    st.table(view.set_index("Deprem").style.format(
        {"Mw": "{:.1f}", "Rjb (km)": "{:.1f}",
         "F (DD-2)": "{:.2f}", "F (DD-1)": "{:.2f}"}))

    if len(view):
        colors = vt.series_colors(dark)
        fig = Figure(figsize=(12.4, 3.6), dpi=110, layout="constrained")
        ax = fig.add_subplot(111)
        x = np.arange(len(view))
        ax.bar(x - 0.2, view["F (DD-2)"], 0.4, color=colors[0], label="DD-2")
        ax.bar(x + 0.2, view["F (DD-1)"], 0.4, color=t["series"], label="DD-1")
        ax.set_xticks(x)
        ax.set_xticklabels(view["Deprem"], rotation=35, ha="right", fontsize=8)
        vt.style_axes(fig, ax, t, "", "Ölçek katsayısı F")
        vt.style_legend(ax, t, loc="upper left", ncols=2)
        st.pyplot(fig, use_container_width=True)


def page_tokens(t: dict, dark: bool) -> None:
    groups = [
        ("Yüzeyler", ["bg", "surface", "surface2", "sunken", "border", "border2"]),
        ("Metin", ["text", "text2", "text3"]),
        ("Vurgu", ["accent", "accent_h", "accent_p", "accent_soft"]),
        ("Durum", ["ok", "ok_soft", "warn", "warn_soft", "err", "err_soft"]),
        ("Kenar çubuğu", ["sidebar", "sidebar_hov", "sidebar_txt",
                          "sidebar_mut", "sidebar_act", "sidebar_on"]),
    ]
    for name, keys in groups:
        st.markdown(f"##### {name}")
        cols = st.columns(6, gap="small")
        for col, key in zip(cols, keys):
            col.markdown(swatch(key, t[key]), unsafe_allow_html=True)
        st.markdown(f'<div style="height:{vt.SP3}px"></div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="vt-sep"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown(card(
            "Yazı tipi ölçeği",
            '<div style="font-family:var(--font-head);font-size:22px;'
            'font-weight:700;color:var(--text)">Sayfa başlığı · 22/700</div>'
            '<div style="font-family:var(--font-head);font-size:18px;'
            'font-weight:700;color:var(--text)">Bölüm başlığı · 18/700</div>'
            '<div style="font-family:var(--font-head);font-size:14px;'
            'font-weight:700;color:var(--text)">Kart başlığı · 14/700</div>'
            '<div style="font-size:13px;color:var(--text)">Gövde · Inter '
            "Regular 13</div>"
            '<div style="font-size:12px;font-weight:600;color:var(--text2)">'
            "Etiket · Inter Medium 12</div>"
            '<div style="font-size:11px;color:var(--text3)">İpucu · Inter '
            "Regular 11</div>",
            hint="Inter",
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(card(
            "Boşluk ve yarıçap",
            kv([("Izgara", "4 px"),
                ("SP1 – SP8", "4 · 8 · 12 · 16 · 20 · 24 · 32 px"),
                ("Köşe yarıçapı", "6 (S) · 10 (M) · 14 (L) px"),
                ("Kenar çubuğu genişliği", f"{vt.SIDEBAR_W} px"),
                ("Kart iç boşluğu", "20 / 16 px"),
                ("Gövde satır yüksekliği", "1.55")]),
            hint="4 px ızgara",
        ), unsafe_allow_html=True)


# =============================================================================
# 4) UYGULAMA KABUĞU
# =============================================================================
def main() -> None:
    st.set_page_config(
        page_title=f"{APP_NAME} — {APP_SUB}",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.session_state.setdefault("dark", False)
    dark = st.session_state["dark"]
    t = vt.theme(dark)

    vt.apply_matplotlib_font()
    st.markdown(vt.build_css(t), unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            f"""<div class="vt-brand">
              <div class="vt-brand-mark">V</div>
              <div>
                <div class="vt-brand-name">{APP_NAME}</div>
                <div class="vt-brand-sub">{APP_SUB}</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
        page = st.radio("Sayfalar", [p[0] for p in PAGES],
                        label_visibility="collapsed")
        st.markdown('<div style="height:180px"></div>', unsafe_allow_html=True)
        if st.button("☀  Gündüz Modu" if dark else "🌙  Gece Modu",
                     use_container_width=True):
            st.session_state["dark"] = not dark
            st.rerun()
        st.markdown(
            f'<div class="vt-side-foot">{APP_NAME} {APP_VER} · TBDY 2018 §2.5</div>',
            unsafe_allow_html=True,
        )

    idx = [p[0] for p in PAGES].index(page)
    page_header(PAGES[idx][0], PAGES[idx][1],
                f"Basit ölçeklendirme · en az 11 kayıt · {APP_VER}")

    (page_overview, page_components, page_table, page_tokens)[idx](t, dark)


if __name__ == "__main__":
    main()
