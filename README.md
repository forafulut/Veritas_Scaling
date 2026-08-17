# VERITAS tasarım dilinde Streamlit uygulaması

Bu Streamlit uygulamasının kabuğu, renkleri, yazı tipleri ve gündüz/gece
teması VERITAS (TBDY 2018 · Deprem Kayıtlarının Seçimi ve Ölçeklendirilmesi)
masaüstü programının tasarım jetonlarından türetilmiştir.

## Çalıştırma

1. Gerekli paketler

   ```
   $ pip install -r requirements.txt
   ```

2. Uygulama

   ```
   $ streamlit run streamlit_app.py
   ```

## Tasarım sistemi

Tüm jetonlar `veritas_theme.py` içindedir; VERITAS'taki `LIGHT` / `DARK`
sözlükleri ve `build_qss()` biçimleri birebir karşılanır.

| Jeton | Gündüz | Gece |
|---|---|---|
| `bg` (sayfa) | `#F1F5F9` | `#0B1220` |
| `surface` (kart) | `#FFFFFF` | `#111A2C` |
| `text` / `text2` / `text3` | `#0F172A` · `#475569` · `#94A3B8` | `#E5EAF3` · `#9FB0C9` · `#5C6E8C` |
| `accent` | `#2563EB` | `#3B82F6` |
| `ok` / `warn` / `err` | `#16A34A` · `#D97706` · `#DC2626` | `#22C55E` · `#F59E0B` · `#EF4444` |
| `sidebar` | `#0F172A` | `#0A101D` |

* **Izgara:** 4 px (`SP1…SP8` = 4·8·12·16·20·24·32 px)
* **Köşe yarıçapı:** 6 (S) · 10 (M) · 14 (L) px
* **Yazı tipi:** Inter (Regular/Medium/Bold) — `static/fonts/` altından
  `@font-face` ile yüklenir; başlıklarda sistemde varsa Hanken Grotesk,
  yoksa Inter Bold kullanılır. Yazı tipi dosyaları yoksa uygulama sistem
  yazı tipleriyle çalışmaya devam eder.
* **Gece/Gündüz:** kenar çubuğunun altındaki düğmeden değiştirilir
  (VERITAS'taki `ThemeBtn` karşılığı); seçim `st.session_state` içinde tutulur.
* **Grafikler:** matplotlib tuvalleri `vt.style_axes()` / `vt.style_legend()`
  ile aynı palete bağlanır — VERITAS'taki `Plot.style()` karşılığı.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `streamlit_app.py` | Uygulama kabuğu (kenar çubuğu · başlık şeridi · 4 sayfa) ve kart/rozet/durum şeridi bileşenleri |
| `veritas_theme.py` | Tasarım jetonları, `@font-face` tanımları, CSS teması, matplotlib biçimleri |
| `.streamlit/config.toml` | Taban tema renkleri ve `static/` sunumu (`enableStaticServing`) |
| `static/fonts/` | Inter Regular · Medium · Bold |

## Sayfalar

1. **Genel Bakış** — durum şeridi, sayısal kutular, spektrum grafiği, özet kartları
2. **Bileşenler** — kart, rozet, durum şeritleri, düğmeler, girdiler, sekmeler, ilerleme
3. **Veri Tablosu** — süzgeçli tablo ve katsayı çubukları
4. **Renk & Tipografi** — palet örnekleri, yazı tipi ölçeği, boşluk jetonları

Sayfalardaki veriler örnek amaçlıdır; tasarım kabuğu kendi içeriğinizle
doldurulmak üzere hazırdır.
