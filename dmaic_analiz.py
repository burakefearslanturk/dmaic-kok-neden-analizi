"""
Proje 2: Six Sigma DMAIC - Kok Neden Analizi (Pareto + Trend + 6M Kategori)

SENARYO:
Bir montaj hattinda son 8 haftada tespit edilen hatali parcalarin kayitlari
tutuluyor. Her hatanin bir turu (defect type) ve bu hatanin hangi ana
nedene (6M: Insan, Makine, Metod, Malzeme, Olcum, Cevre) bagli oldugu
kaydediliyor. Amac: en cok soruna yol acan hata turlerini (Pareto -
"onemli azinlik" ilkesi) ve zaman icindeki hata oranindaki egilimi
bulup kok neden analizine baslangic noktasi olusturmak.

KULLANILAN KUTUPHANELER:
- numpy   : rastgele veri uretimi
- pandas  : veri isleme ve gruplama (groupby)
- matplotlib : Pareto grafigi, trend grafigi ve kategori grafigi
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# 1. ADIM: Hata verisini uret
# ----------------------------------------------------------------------
# Gercek bir projede bu veri MES/ERP sisteminden veya bir CSV'den gelir.
# Biz burada, gercekci bir dagilima sahip sentetik hata kaydi uretiyoruz.

np.random.seed(7)

# Hata turleri ve bunlarin GORECELI SIKLIGI (bazi hatalar digerlerinden
# cok daha sik gorulecek sekilde agirliklandirildi -> gercek Pareto
# etkisini simule etmek icin)
defect_types = ["Olcu Hatasi", "Yuzey Cizigi", "Montaj Hatasi",
                 "Renk Farkliligi", "Etiket Hatasi", "Diger"]
defect_weights = [0.40, 0.27, 0.15, 0.10, 0.05, 0.03]  # toplami 1.0

# Her hata turunun hangi 6M kategorisine (ana kok neden grubuna) ait oldugu
defect_to_category = {
    "Olcu Hatasi": "Makine",
    "Yuzey Cizigi": "Malzeme",
    "Montaj Hatasi": "Insan",
    "Renk Farkliligi": "Malzeme",
    "Etiket Hatasi": "Metod",
    "Diger": "Cevre",
}

n_defects = 480          # toplam kaydedilen hatali parca sayisi
n_weeks = 8               # analiz edilen hafta sayisi
haftalik_uretim = 1500    # her hafta uretilen toplam parca sayisi (sabit varsayim)

# her hataya rastgele bir hafta (1-8 arasi) ata; son haftalarda hata
# oraninin hafifce ARTTIGI bir egilim ekliyoruz (surec kotulesiyor
# senaryosu -> DMAIC'in "Analyze" asamasinda boyle bir sinyal aranir)
hafta_agirliklari = np.array([0.08, 0.09, 0.10, 0.11, 0.12, 0.15, 0.16, 0.19])
hafta_agirliklari = hafta_agirliklari / hafta_agirliklari.sum()

df = pd.DataFrame({
    "Hata_Turu": np.random.choice(defect_types, size=n_defects, p=defect_weights),
    "Hafta": np.random.choice(np.arange(1, n_weeks + 1), size=n_defects, p=hafta_agirliklari),
})
df["Kok_Neden_Kategorisi"] = df["Hata_Turu"].map(defect_to_category)


# ----------------------------------------------------------------------
# 2. ADIM: Pareto analizi (hangi hata turleri en cok soruna yol aciyor?)
# ----------------------------------------------------------------------
pareto = df["Hata_Turu"].value_counts().reset_index()
pareto.columns = ["Hata_Turu", "Adet"]
pareto = pareto.sort_values("Adet", ascending=False).reset_index(drop=True)

pareto["Kumulatif_Adet"] = pareto["Adet"].cumsum()
pareto["Kumulatif_Yuzde"] = 100 * pareto["Kumulatif_Adet"] / pareto["Adet"].sum()

# "onemli azinlik" -> kumulatif yuzde ilk kez %80'i astigi hata turleri
onemli_hatalar = pareto[pareto["Kumulatif_Yuzde"] <= 80]["Hata_Turu"].tolist()
if len(onemli_hatalar) < len(pareto):
    # %80 sinirini asan ilk hatayi da dahil et (Pareto kuralinin standart uygulamasi)
    onemli_hatalar.append(pareto.iloc[len(onemli_hatalar)]["Hata_Turu"])


# ----------------------------------------------------------------------
# 3. ADIM: Haftalik hata oranı trendi
# ----------------------------------------------------------------------
haftalik = df.groupby("Hafta").size().reset_index(name="Hata_Adedi")
haftalik["Hata_Orani_Yuzde"] = 100 * haftalik["Hata_Adedi"] / haftalik_uretim

# basit bir dogrusal trend (egim) hesapla -> hata orani artiyor mu azaliyor mu?
egim, kesisim = np.polyfit(haftalik["Hafta"], haftalik["Hata_Orani_Yuzde"], 1)


# ----------------------------------------------------------------------
# 4. ADIM: 6M kok neden kategorisi dagilimi
# ----------------------------------------------------------------------
kategori_dagilimi = df["Kok_Neden_Kategorisi"].value_counts().reset_index()
kategori_dagilimi.columns = ["Kategori", "Adet"]
kategori_dagilimi = kategori_dagilimi.sort_values("Adet", ascending=False)


# ----------------------------------------------------------------------
# 5. ADIM: Grafikleri ciz
# ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(13, 9))

# --- (a) Pareto grafigi ---
ax1 = axes[0, 0]
bars = ax1.bar(pareto["Hata_Turu"], pareto["Adet"], color='#4C72B0')
ax1.set_ylabel("Hata Adedi")
ax1.set_title("Pareto Grafigi - Hata Turleri")
ax1.tick_params(axis='x', rotation=30)

ax1b = ax1.twinx()
ax1b.plot(pareto["Hata_Turu"], pareto["Kumulatif_Yuzde"], color='red', marker='o')
ax1b.axhline(80, color='gray', linestyle='--', linewidth=1)
ax1b.set_ylabel("Kumulatif Yuzde (%)")
ax1b.set_ylim(0, 110)

# %80 cizgisinin uzerindeki hatalari renkli isaretle (onemli azinlik)
for i, bar in enumerate(bars):
    if pareto.loc[i, "Hata_Turu"] in onemli_hatalar:
        bar.set_color('#C44E52')

# --- (b) Haftalik hata orani trendi ---
ax2 = axes[0, 1]
ax2.plot(haftalik["Hafta"], haftalik["Hata_Orani_Yuzde"], marker='o', color='#DD8452')
trend_line = egim * haftalik["Hafta"] + kesisim
ax2.plot(haftalik["Hafta"], trend_line, linestyle='--', color='gray', label=f"Trend (egim={egim:+.2f}/hafta)")
ax2.set_xlabel("Hafta")
ax2.set_ylabel("Hata Orani (%)")
ax2.set_title("Haftalik Hata Orani Trendi")
ax2.legend(fontsize=8)
ax2.grid(alpha=0.3)

# --- (c) 6M kok neden kategori dagilimi ---
ax3 = axes[1, 0]
ax3.barh(kategori_dagilimi["Kategori"], kategori_dagilimi["Adet"], color='#55A868')
ax3.set_xlabel("Hata Adedi")
ax3.set_title("Kok Neden Kategorisi Dagilimi (6M)")
ax3.invert_yaxis()

# --- (d) Ozet metin paneli ---
ax4 = axes[1, 1]
ax4.axis('off')
ozet_metin = (
    f"TOPLAM HATA SAYISI: {n_defects}\n\n"
    f"ONEMLI AZINLIK (Pareto %80):\n"
    + "\n".join(f"  - {h}" for h in onemli_hatalar) + "\n\n"
    f"EN BUYUK KOK NEDEN KATEGORISI:\n  {kategori_dagilimi.iloc[0]['Kategori']} "
    f"({kategori_dagilimi.iloc[0]['Adet']} hata)\n\n"
    f"HAFTALIK TREND EGIMI: {egim:+.3f} puan/hafta\n"
    f"({'Kotulesiyor' if egim > 0 else 'Iyilesiyor'})"
)
ax4.text(0.02, 0.98, ozet_metin, va='top', ha='left', fontsize=10, family='monospace')

plt.tight_layout()
plt.savefig("dmaic_analiz.png", dpi=150)
plt.close()


# ----------------------------------------------------------------------
# 6. ADIM: Ozet raporu yazdir ve verileri CSV'ye kaydet
# ----------------------------------------------------------------------
print("=" * 60)
print("SIX SIGMA DMAIC - KOK NEDEN ANALIZI RAPORU")
print("=" * 60)
print(f"Toplam hata sayisi: {n_defects}  |  Analiz edilen hafta: {n_weeks}")
print("-" * 60)
print("PARETO TABLOSU:")
print(pareto.to_string(index=False))
print("-" * 60)
print(f"Onemli azinlik (kumulatif %80'i olusturan hata turleri):")
for h in onemli_hatalar:
    print(f"  - {h}")
print("-" * 60)
print("6M KOK NEDEN KATEGORISI DAGILIMI:")
print(kategori_dagilimi.to_string(index=False))
print("-" * 60)
print(f"Haftalik hata orani trend egimi: {egim:+.3f} puan/hafta")
if egim > 0:
    print("Yorum: Hata orani zamanla ARTIYOR - acil kok neden incelemesi onerilir.")
else:
    print("Yorum: Hata orani zamanla AZALIYOR - mevcut iyilestirmeler etkili gorunuyor.")
print("=" * 60)

pareto.to_csv("pareto_tablosu.csv", index=False)
haftalik.to_csv("haftalik_trend.csv", index=False)
df.to_csv("ham_hata_verisi.csv", index=False)
print("\nSonuclar 'dmaic_analiz.png' ve CSV dosyalarina kaydedildi.")
