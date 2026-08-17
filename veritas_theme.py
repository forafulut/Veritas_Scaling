# -*- coding: utf-8 -*-
"""VERITAS tasarım dili — Streamlit uyarlaması.

Renk jetonları, boşluk ızgarası ve bileşen biçimleri VERITAS
(TBDY 2018 Kayıt Ölçekleme) masaüstü programından birebir alınmıştır:
4 px ızgara, Inter gövde yazı tipi, koyu lacivert kenar çubuğu,
mavi vurgu rengi ve açık/koyu (gündüz/gece) tema çifti.
"""

from __future__ import annotations

import os

import matplotlib

# =============================================================================
# 1) TASARIM JETONLARI  (4 px ızgara · açık/koyu tema)
# =============================================================================
SP1, SP2, SP3, SP4, SP5, SP6, SP8 = 4, 8, 12, 16, 20, 24, 32
RAD_S, RAD_M, RAD_L = 6, 10, 14

FONT_HEAD = "'Hanken Grotesk', 'Inter', 'Segoe UI', system-ui, sans-serif"
FONT_BODY = "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif"

SIDEBAR_W = 240

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

# Grafik serileri için vurgu rengiyle uyumlu palet
SERIES_LIGHT = ["#2563EB", "#16A34A", "#D97706", "#DC2626", "#7C3AED", "#0891B2"]
SERIES_DARK = ["#3B82F6", "#22C55E", "#F59E0B", "#EF4444", "#A78BFA", "#22D3EE"]


def theme(dark: bool) -> dict:
    return DARK if dark else LIGHT


def series_colors(dark: bool) -> list[str]:
    return SERIES_DARK if dark else SERIES_LIGHT


# =============================================================================
# 2) YAZI TİPLERİ
# =============================================================================
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "static", "fonts")
_FONT_FILES = (("Inter-Regular.ttf", 400), ("Inter-Medium.ttf", 500),
               ("Inter-Bold.ttf", 700))


def font_face_css() -> str:
    """Yerel Inter dosyalarını @font-face olarak tanımlar.

    Dosyalar `static/` altından sunulur (config.toml → enableStaticServing).
    Klasör yoksa sistem yazı tipleriyle çalışmaya devam edilir.
    """
    if not os.path.isdir(_FONT_DIR):
        return ""
    out = []
    for fn, weight in _FONT_FILES:
        if os.path.exists(os.path.join(_FONT_DIR, fn)):
            out.append(f"""
@font-face {{
  font-family:'Inter'; font-style:normal; font-weight:{weight};
  font-display:swap; src:url('app/static/fonts/{fn}') format('truetype');
}}""")
    return "".join(out)


def apply_matplotlib_font() -> None:
    """Grafiklerde de aynı gövde yazı tipini kullan."""
    path = os.path.join(_FONT_DIR, "Inter-Regular.ttf")
    if os.path.exists(path):
        try:
            from matplotlib import font_manager as _fm
            _fm.fontManager.addfont(path)
            matplotlib.rcParams["font.family"] = "Inter"
        except Exception:                       # yazı tipi zorunlu değil
            pass
    matplotlib.rcParams["axes.unicode_minus"] = False


# =============================================================================
# 3) CSS TEMA  (VERITAS QSS karşılığı)
# =============================================================================
def build_css(t: dict) -> str:
    """VERITAS `build_qss()` fonksiyonunun Streamlit/CSS karşılığı."""
    return f"""<style>
{font_face_css()}

:root {{
  --bg:{t['bg']}; --surface:{t['surface']}; --surface2:{t['surface2']};
  --sunken:{t['sunken']}; --border:{t['border']}; --border2:{t['border2']};
  --text:{t['text']}; --text2:{t['text2']}; --text3:{t['text3']};
  --accent:{t['accent']}; --accent-h:{t['accent_h']}; --accent-p:{t['accent_p']};
  --accent-soft:{t['accent_soft']}; --on-accent:{t['on_accent']};
  --ok:{t['ok']}; --ok-soft:{t['ok_soft']}; --warn:{t['warn']};
  --warn-soft:{t['warn_soft']}; --err:{t['err']}; --err-soft:{t['err_soft']};
  --sidebar:{t['sidebar']}; --sidebar-txt:{t['sidebar_txt']};
  --sidebar-mut:{t['sidebar_mut']}; --sidebar-hov:{t['sidebar_hov']};
  --sidebar-act:{t['sidebar_act']}; --sidebar-on:{t['sidebar_on']};
  --rad-s:{RAD_S}px; --rad-m:{RAD_M}px; --rad-l:{RAD_L}px;
  --sp1:{SP1}px; --sp2:{SP2}px; --sp3:{SP3}px; --sp4:{SP4}px;
  --sp5:{SP5}px; --sp6:{SP6}px; --sp8:{SP8}px;
  --font-head:{FONT_HEAD}; --font-body:{FONT_BODY};
}}

/* ---- Genel ---- */
html, body, [class*="st-"], button, input, select, textarea,
[data-testid="stAppViewContainer"], [data-testid="stSidebar"] {{
  font-family:var(--font-body);
}}
/* simge yazı tipleri gövde yazı tipinden etkilenmemeli */
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons,
span[class*="material-symbols"] {{
  font-family:'Material Symbols Rounded' !important;
}}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  background:var(--bg); color:var(--text);
}}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stAppDeployButton"], [data-testid="stStatusWidget"] {{ display:none; }}
[data-testid="stMainMenu"] svg {{ color:var(--text3); }}
[data-testid="stMain"] .block-container {{
  padding:var(--sp5) var(--sp6) var(--sp8); max-width:1360px;
}}
[data-testid="stMain"] p, [data-testid="stMain"] li,
[data-testid="stMain"] label, [data-testid="stMain"] span {{
  color:var(--text); font-size:13px;
}}
[data-testid="stMain"] h1, [data-testid="stMain"] h2,
[data-testid="stMain"] h3, [data-testid="stMain"] h4 {{
  font-family:var(--font-head); color:var(--text); font-weight:700;
  letter-spacing:-0.2px;
}}
[data-testid="stMain"] h1 {{ font-size:22px; }}
[data-testid="stMain"] h2 {{ font-size:18px; }}
[data-testid="stMain"] h3 {{ font-size:15px; }}
[data-testid="stMain"] h5, [data-testid="stMain"] h6 {{
  font-family:var(--font-head); color:var(--text2); font-weight:700;
  font-size:12px; letter-spacing:0.8px; text-transform:uppercase;
}}
[data-testid="stMain"] a {{ color:var(--accent); text-decoration:none; }}
[data-testid="stMain"] a:hover {{ text-decoration:underline; }}
hr, [data-testid="stMain"] hr {{ border-color:var(--border); }}
[data-testid="stMain"] code {{
  background:var(--sunken); color:var(--accent); border-radius:var(--rad-s);
  padding:1px 6px; font-size:12px;
}}
[data-testid="stTooltipContent"] {{
  background:var(--surface); color:var(--text);
  border:1px solid var(--border2); border-radius:var(--rad-s);
}}

/* ---- Kenar çubuğu ---- */
[data-testid="stSidebar"] {{
  background:var(--sidebar); border-right:none; width:{SIDEBAR_W}px !important;
  min-width:{SIDEBAR_W}px !important;
}}
[data-testid="stSidebar"] > div {{ background:var(--sidebar); }}
[data-testid="stSidebarContent"] {{ padding-top:var(--sp5); }}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap:var(--sp2); }}
[data-testid="stSidebar"] * {{ color:var(--sidebar-txt); }}
[data-testid="stSidebarCollapseButton"] svg {{ color:var(--sidebar-mut); }}
.vt-brand {{ display:flex; align-items:center; gap:var(--sp3);
  padding:0 var(--sp1) var(--sp4); }}
.vt-brand-mark {{
  width:38px; height:38px; border-radius:var(--rad-m); flex:0 0 38px;
  background:linear-gradient(140deg, var(--sidebar-act), var(--accent-p));
  display:flex; align-items:center; justify-content:center;
  color:var(--sidebar-on); font-family:var(--font-head); font-weight:700;
  font-size:17px; letter-spacing:0.5px;
}}
.vt-brand-name {{
  color:var(--sidebar-on); font-family:var(--font-head); font-size:20px;
  font-weight:700; letter-spacing:1px; line-height:1.1;
}}
.vt-brand-sub {{
  color:var(--sidebar-mut); font-size:10px; letter-spacing:0.4px;
  white-space:nowrap;
}}
.vt-side-foot {{
  color:var(--sidebar-mut); font-size:11px; text-align:center;
  padding:var(--sp3) 0 var(--sp2);
}}
.vt-side-cap {{
  color:var(--sidebar-mut); font-size:10px; font-weight:700;
  letter-spacing:1.2px; text-transform:uppercase; padding:var(--sp2) var(--sp1) 0;
}}

/* Kenar çubuğu gezinme düğmeleri (radio → NavBtn) */
[data-testid="stSidebar"] [role="radiogroup"] {{ gap:var(--sp1); }}
[data-testid="stSidebar"] [role="radiogroup"] label {{
  display:flex; align-items:center; width:100%; height:40px; margin:0;
  padding:0 var(--sp3); border-radius:var(--rad-m); cursor:pointer;
  background:transparent; transition:background .12s ease, color .12s ease;
}}
/* radyo göstergesi gizli — etiketin tamamı tıklanabilir kalır */
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div > div:first-child {{
  display:none;
}}
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div,
[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div {{
  width:100%;
}}
[data-testid="stSidebar"] [role="radiogroup"] label p {{
  color:var(--sidebar-txt); font-size:13px; font-weight:500;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
  background:var(--sidebar-hov);
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover p {{
  color:var(--sidebar-on);
}}
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"],
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
  background:var(--sidebar-act);
}}
[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] p,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{
  color:var(--sidebar-on); font-weight:600;
}}

/* Gece/Gündüz düğmesi */
[data-testid="stSidebar"] .stButton > button {{
  width:100%; height:38px; background:var(--sidebar-hov);
  border:1px solid var(--sidebar-hov); border-radius:var(--rad-m);
  color:var(--sidebar-txt); font-weight:600; font-size:13px;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
  color:var(--sidebar-on); border-color:var(--sidebar-mut);
  background:var(--sidebar-hov);
}}
[data-testid="stSidebar"] .stButton > button:active,
[data-testid="stSidebar"] .stButton > button:focus:not(:active) {{
  color:var(--sidebar-on); background:var(--sidebar); border-color:var(--sidebar-mut);
}}

/* ---- Başlık şeridi ---- */
.vt-header {{
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--rad-l); padding:var(--sp3) var(--sp5);
  display:flex; align-items:center; gap:var(--sp4);
  margin-bottom:var(--sp5);
}}
.vt-header-title {{
  font-family:var(--font-head); font-size:18px; font-weight:700;
  color:var(--text); line-height:1.25;
}}
.vt-header-desc {{ color:var(--text2); font-size:12px; }}
.vt-verchip {{
  margin-left:auto; color:var(--text3); background:var(--sunken);
  border-radius:var(--rad-s); padding:3px var(--sp2); font-size:11px;
  white-space:nowrap;
}}

/* ---- Kartlar ---- */
.vt-card {{
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--rad-l); padding:var(--sp4) var(--sp5) var(--sp5);
  height:100%;
}}
.vt-card-head {{
  display:flex; align-items:baseline; gap:var(--sp3); margin-bottom:var(--sp3);
}}
.vt-card-title {{
  font-family:var(--font-head); font-size:14px; font-weight:700; color:var(--text);
}}
.vt-card-hint {{ margin-left:auto; color:var(--text3); font-size:11px; }}
.vt-card-body {{ color:var(--text2); font-size:12.5px; line-height:1.55; }}
.vt-card-body strong {{ color:var(--text); font-weight:600; }}

/* Streamlit kapsayıcısını kart gibi göster (border=True) */
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]:has(
  > div > [data-testid="stVerticalBlock"]) {{
  border-radius:var(--rad-l);
}}
[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] {{
  background:var(--surface); border-color:var(--border);
}}

/* ---- Sayısal kutular ---- */
.vt-stat {{
  background:var(--surface2); border:1px solid var(--border);
  border-radius:var(--rad-m); padding:10px var(--sp3);
}}
.vt-stat-val {{
  font-family:var(--font-head); font-size:17px; font-weight:700; color:var(--text);
  line-height:1.3;
}}
.vt-stat-lbl {{ color:var(--text2); font-size:11px; }}
.vt-stat-delta {{ font-size:11px; font-weight:600; }}
.vt-stat-delta.up {{ color:var(--ok); }}
.vt-stat-delta.down {{ color:var(--err); }}

[data-testid="stMetric"] {{
  background:var(--surface2); border:1px solid var(--border);
  border-radius:var(--rad-m); padding:10px var(--sp3);
}}
[data-testid="stMetricLabel"] p {{ color:var(--text2) !important; font-size:11px; }}
[data-testid="stMetricValue"] {{
  font-family:var(--font-head); font-size:17px; font-weight:700; color:var(--text);
}}

/* ---- Rozetler ---- */
.vt-chip {{
  display:inline-block; background:var(--sunken); color:var(--text2);
  border-radius:var(--rad-s); padding:3px var(--sp2); font-size:11px;
  font-weight:600; margin:0 var(--sp1) var(--sp1) 0;
}}
.vt-chip.accent {{ background:var(--accent-soft); color:var(--accent); }}
.vt-chip.ok     {{ background:var(--ok-soft);     color:var(--ok); }}
.vt-chip.warn   {{ background:var(--warn-soft);   color:var(--warn); }}
.vt-chip.err    {{ background:var(--err-soft);    color:var(--err); }}

/* ---- Durum şeridi ---- */
.vt-banner {{
  border-radius:var(--rad-m); border:1px solid transparent;
  padding:var(--sp3) var(--sp4); display:flex; gap:var(--sp3);
  align-items:flex-start; margin-bottom:var(--sp3);
}}
.vt-banner .ico {{ font-size:16px; line-height:1.35; }}
.vt-banner .ttl {{ font-size:12.5px; font-weight:700; }}
.vt-banner .sub {{ color:var(--text2); font-size:11.5px; font-weight:400; }}
.vt-banner.info {{ background:var(--accent-soft); border-color:{t['accent']}44; }}
.vt-banner.info .ttl, .vt-banner.info .ico {{ color:var(--accent); }}
.vt-banner.ok {{ background:var(--ok-soft); border-color:{t['ok']}55; }}
.vt-banner.ok .ttl, .vt-banner.ok .ico {{ color:var(--ok); }}
.vt-banner.warn {{ background:var(--warn-soft); border-color:{t['warn']}55; }}
.vt-banner.warn .ttl, .vt-banner.warn .ico {{ color:var(--warn); }}
.vt-banner.err {{ background:var(--err-soft); border-color:{t['err']}55; }}
.vt-banner.err .ttl, .vt-banner.err .ico {{ color:var(--err); }}

/* ---- Düğmeler ---- */
[data-testid="stMain"] .stButton > button,
[data-testid="stMain"] .stDownloadButton > button,
[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button {{
  background:var(--surface); color:var(--text);
  border:1px solid var(--border2); border-radius:var(--rad-m);
  padding:var(--sp2) var(--sp4); font-weight:600; font-size:13px;
  transition:background .12s ease, border-color .12s ease;
}}
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stMain"] .stDownloadButton > button:hover,
[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button:hover {{
  background:var(--surface2); border-color:var(--accent); color:var(--text);
}}
[data-testid="stMain"] .stButton > button:active {{ background:var(--sunken); }}
[data-testid="stMain"] .stButton > button:focus:not(:active) {{
  border-color:var(--accent); color:var(--text);
}}
[data-testid="stMain"] .stButton > button:disabled {{
  color:var(--text3); background:var(--sunken); border-color:var(--border);
}}
[data-testid="stMain"] .stButton > button[kind="primary"],
[data-testid="stMain"] .stDownloadButton > button[kind="primary"],
[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button[kind="primary"] {{
  background:var(--accent); border-color:var(--accent); color:var(--on-accent);
}}
[data-testid="stMain"] .stButton > button[kind="primary"]:hover,
[data-testid="stMain"] .stDownloadButton > button[kind="primary"]:hover,
[data-testid="stMain"] [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {{
  background:var(--accent-h); border-color:var(--accent-h); color:var(--on-accent);
}}
[data-testid="stMain"] .stButton > button[kind="primary"]:active {{
  background:var(--accent-p); border-color:var(--accent-p);
}}

/* ---- Girdiler ---- */
[data-testid="stMain"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="textarea"] {{
  background:var(--surface); border:1px solid var(--border2);
  border-radius:{RAD_S + 2}px; color:var(--text);
}}
/* Streamlit ≥ 1.5x react-aria girdileri */
[data-testid="stMain"] [data-testid="stTextInputRootElement"],
[data-testid="stMain"] [data-testid="stNumberInputContainer"],
[data-testid="stMain"] [data-testid="stTextAreaRootElement"],
[data-testid="stMain"] .react-aria-ComboBox > [role="group"],
[data-testid="stMain"] .react-aria-Select > [role="group"] {{
  background:var(--surface); border:1px solid var(--border2);
  border-radius:{RAD_S + 2}px; color:var(--text);
}}
[data-testid="stMain"] [data-baseweb="input"]:hover,
[data-testid="stMain"] [data-baseweb="select"] > div:hover,
[data-testid="stMain"] [data-baseweb="textarea"]:hover,
[data-testid="stMain"] [data-testid="stTextInputRootElement"]:hover,
[data-testid="stMain"] [data-testid="stNumberInputContainer"]:hover,
[data-testid="stMain"] [data-testid="stTextAreaRootElement"]:hover,
[data-testid="stMain"] .react-aria-ComboBox > [role="group"]:hover {{
  border-color:var(--accent);
}}
[data-testid="stMain"] [data-baseweb="input"]:focus-within,
[data-testid="stMain"] [data-baseweb="select"] > div:focus-within,
[data-testid="stMain"] [data-baseweb="textarea"]:focus-within,
[data-testid="stMain"] [data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stMain"] [data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stMain"] [data-testid="stTextAreaRootElement"]:focus-within,
[data-testid="stMain"] .react-aria-ComboBox > [role="group"]:focus-within {{
  border:2px solid var(--accent);
}}
[data-testid="stMain"] [data-testid="stNumberInputStepUp"],
[data-testid="stMain"] [data-testid="stNumberInputStepDown"] {{
  background:transparent; color:var(--text2); border:none;
}}
[data-testid="stMain"] [data-testid="stNumberInputStepUp"]:hover,
[data-testid="stMain"] [data-testid="stNumberInputStepDown"]:hover {{
  color:var(--accent); background:var(--sunken);
}}
[data-testid="stMain"] input, [data-testid="stMain"] textarea {{
  color:var(--text) !important; background:transparent !important;
  font-size:13px;
}}
[data-testid="stMain"] input::placeholder,
[data-testid="stMain"] textarea::placeholder {{
  color:var(--text3) !important; opacity:1;
}}
[data-testid="stMain"] [data-testid="stWidgetLabel"] p {{
  color:var(--text2); font-size:12px; font-weight:600;
}}
[data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"],
.react-aria-Popover, [role="listbox"] {{
  background:var(--surface); border:1px solid var(--border2);
  border-radius:var(--rad-s); color:var(--text);
}}
[data-baseweb="menu"] li, [role="listbox"] [role="option"] {{
  color:var(--text); font-size:13px;
}}
[data-baseweb="menu"] li:hover, [role="listbox"] [role="option"]:hover,
[data-baseweb="menu"] li[aria-selected="true"],
[role="listbox"] [role="option"][aria-selected="true"],
[role="listbox"] [role="option"][data-focused="true"] {{
  background:var(--accent-soft); color:var(--accent);
}}
[data-testid="stMain"] [data-baseweb="slider"] [role="slider"],
[data-testid="stMain"] [data-testid="stSlider"] [role="slider"] {{
  background:var(--accent);
}}
[data-testid="stMain"] [data-testid="stSliderThumbValue"] {{
  color:var(--text2); font-size:11px; font-weight:600;
}}
[data-testid="stMain"] [data-testid="stSliderTickBarMin"],
[data-testid="stMain"] [data-testid="stSliderTickBarMax"] {{
  color:var(--text3); font-size:11px;
}}
[data-testid="stMain"] [data-baseweb="checkbox"] span[aria-hidden="true"],
[data-testid="stMain"] [data-baseweb="radio"] div[aria-hidden="true"] {{
  border-color:var(--border2);
}}

/* ---- Bölümlendirilmiş denetim (segmented / radio-yatay) ---- */
[data-testid="stMain"] [data-testid="stButtonGroup"] button {{
  background:transparent; border:none; border-radius:var(--rad-s);
  color:var(--text2); font-weight:600; padding:var(--sp1) var(--sp4);
}}
[data-testid="stMain"] [data-testid="stButtonGroup"] button:hover {{
  color:var(--text); background:var(--sunken);
}}
[data-testid="stMain"] [data-testid="stButtonGroup"] button[aria-pressed="true"],
[data-testid="stMain"] [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {{
  background:var(--surface); color:var(--accent); font-weight:700;
  border:1px solid var(--border);
}}

/* ---- Tablo ---- */
[data-testid="stMain"] [data-testid="stDataFrame"],
[data-testid="stMain"] [data-testid="stTable"] {{
  border:1px solid var(--border); border-radius:var(--rad-m); overflow:hidden;
}}
[data-testid="stMain"] [data-testid="stTable"] table {{
  background:var(--surface); color:var(--text); font-size:12.5px;
  border-collapse:collapse; width:100%;
}}
[data-testid="stMain"] [data-testid="stTable"] thead th {{
  background:var(--surface2); color:var(--text2); font-weight:700;
  font-size:11.5px; text-align:left; padding:var(--sp2) var(--sp3);
  border:none; border-bottom:1px solid var(--border2);
}}
[data-testid="stMain"] [data-testid="stTable"] tbody th {{
  background:var(--surface); color:var(--text3); font-weight:500;
  border-bottom:1px solid var(--border); padding:var(--sp2) var(--sp3);
}}
[data-testid="stMain"] [data-testid="stTable"] tbody td {{
  border-bottom:1px solid var(--border); padding:var(--sp2) var(--sp3);
  color:var(--text);
}}
[data-testid="stMain"] [data-testid="stTable"] tbody tr:nth-child(even) td,
[data-testid="stMain"] [data-testid="stTable"] tbody tr:nth-child(even) th {{
  background:var(--surface2);
}}
[data-testid="stMain"] [data-testid="stTable"] tbody tr:hover td {{
  background:var(--accent-soft);
}}

/* ---- Sekmeler ---- */
[data-testid="stMain"] [data-baseweb="tab-list"],
[data-testid="stMain"] [role="tablist"] {{
  gap:var(--sp1); background:transparent; border-bottom:none;
}}
[data-testid="stMain"] [data-baseweb="tab"],
[data-testid="stMain"] [data-testid="stTab"] {{
  background:transparent; color:var(--text2); font-weight:600; font-size:13px;
  padding:var(--sp2) var(--sp4); border-radius:var(--rad-m);
  border:1px solid transparent;
}}
[data-testid="stMain"] [data-testid="stTab"] p {{
  color:var(--text2); font-size:13px; font-weight:600;
}}
[data-testid="stMain"] [data-baseweb="tab"]:hover,
[data-testid="stMain"] [data-testid="stTab"]:hover {{
  color:var(--text); background:var(--sunken);
}}
[data-testid="stMain"] [data-testid="stTab"]:hover p {{ color:var(--text); }}
[data-testid="stMain"] [data-baseweb="tab"][aria-selected="true"],
[data-testid="stMain"] [data-testid="stTab"][aria-selected="true"] {{
  background:var(--accent-soft); color:var(--accent); border-color:{t['accent']}33;
}}
[data-testid="stMain"] [data-testid="stTab"][aria-selected="true"] p {{
  color:var(--accent); font-weight:700;
}}
[data-testid="stMain"] [data-baseweb="tab-highlight"],
[data-testid="stMain"] [data-baseweb="tab-border"] {{ background:transparent; }}
[data-testid="stMain"] .react-aria-SelectionIndicator {{ display:none; }}

/* ---- Genişletici ---- */
[data-testid="stMain"] [data-testid="stExpander"] details {{
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--rad-l);
}}
[data-testid="stMain"] [data-testid="stExpander"] summary {{
  font-family:var(--font-head); font-weight:700; font-size:13.5px;
  color:var(--text);
}}
[data-testid="stMain"] [data-testid="stExpander"] summary:hover {{
  color:var(--accent);
}}

/* ---- İlerleme / uyarı kutuları ---- */
[data-testid="stMain"] [data-testid="stProgressBarTrack"] {{
  background:var(--sunken); border-radius:var(--rad-s); height:8px;
  overflow:hidden;
}}
[data-testid="stMain"] [data-testid="stProgressBarTrack"] > div {{
  background:var(--accent); border-radius:var(--rad-s); height:8px;
}}
[data-testid="stMain"] [data-testid="stProgress"] p {{
  color:var(--text2); font-size:11.5px; margin-bottom:6px;
}}
[data-testid="stMain"] [data-testid="stProgress"] > div > div > div > div {{
  background:var(--accent); border-radius:var(--rad-s);
}}
[data-testid="stMain"] [data-testid="stAlert"] {{
  border-radius:var(--rad-m); border:1px solid var(--border);
  background:var(--surface2); color:var(--text);
}}

/* ---- Kaydırma çubuğu ---- */
::-webkit-scrollbar {{ width:10px; height:10px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:var(--border2); border-radius:4px; }}
::-webkit-scrollbar-thumb:hover {{ background:var(--text3); }}

/* ---- Yardımcılar ---- */
.vt-row {{ display:flex; flex-wrap:wrap; gap:var(--sp2); align-items:center; }}
.vt-kv {{ display:flex; justify-content:space-between; gap:var(--sp3);
  padding:6px 0; border-bottom:1px solid var(--border); font-size:12.5px; }}
.vt-kv:last-child {{ border-bottom:none; }}
.vt-kv .k {{ color:var(--text2); }}
.vt-kv .v {{ color:var(--text); font-weight:600; font-variant-numeric:tabular-nums; }}
.vt-sep {{ height:1px; background:var(--border); margin:var(--sp4) 0; }}
.vt-swatch {{
  border:1px solid var(--border); border-radius:var(--rad-m);
  overflow:hidden; background:var(--surface);
}}
.vt-swatch .box {{ height:46px; }}
.vt-swatch .meta {{ padding:6px var(--sp2); }}
.vt-swatch .name {{ font-size:11.5px; font-weight:600; color:var(--text); }}
.vt-swatch .hex {{
  font-size:10.5px; color:var(--text3); font-variant-numeric:tabular-nums;
}}
</style>"""


# =============================================================================
# 4) GRAFİK BİÇİMİ  (VERITAS `Plot.style()` karşılığı)
# =============================================================================
def style_axes(fig, ax, t: dict, xlab: str = "", ylab: str = "") -> None:
    ax.set_facecolor(t["surface"])
    fig.set_facecolor(t["surface"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(t["border2"])
    ax.tick_params(colors=t["text2"], labelsize=9)
    if xlab:
        ax.set_xlabel(xlab, color=t["text2"], fontsize=10)
    if ylab:
        ax.set_ylabel(ylab, color=t["text2"], fontsize=10)
    ax.grid(True, color=t["grid"], lw=0.7, alpha=0.6)
    ax.margins(x=0)


def style_legend(ax, t: dict, **kw):
    return ax.legend(frameon=False, fontsize=9, labelcolor=t["text"], **kw)
