# TuringLab — Mini Rapor

**Öğrenci:** İlayda Nur YILMAZ  
**Ders:** Otomata Teorisi ve Biçimsel Diller — Bilgisayar Mühendisliği  
**Tarih:** 22 Mayıs 2026  
**GitHub:** https://github.com/ilaydayda/turinglab-ilaydanuryilmaz

---

## 1. Giriş

TuringLab, deterministik tek-şeritli Turing makinelerini YAML formatında tanımlamayı ve Python üzerinde çalıştırmayı sağlayan bir kütüphanedir. Proje; teorik bilgisayar biliminin temel modeli olan Turing makinesini somut, çalıştırılabilir bir yazılım artefaktına dönüştürme amacıyla geliştirilmiştir.

Kütüphane üç zorunlu bölümden oluşmaktadır: `tm_engine.py` ile tek-şeritli deterministik TM motoru, dört farklı problemi çözen YAML tanımlı makineler ve bunları doğrulayan pytest test paketi. Bunlara ek olarak üç bonus bölüm tamamlanmıştır: çok-şeritli TM motoru (`multi_tape.py`), non-deterministik TM motoru (`ntm.py`) ve karşılaştırmalı performans analizi (`comparison.py`).

---

## 2. Mimari

### 2.1 Modül Organizasyonu

```
turinglab-projesi/
├── turinglab/
│   ├── tm_engine.py      # Bölüm 1: Tek-şeritli DTM motoru
│   ├── multi_tape.py     # Bonus A: Çok-şeritli TM motoru
│   ├── ntm.py            # Bonus B: Non-deterministik TM motoru
│   └── comparison.py     # Bonus C: Karşılaştırmalı analiz
├── machines/             # YAML makine tanımları
├── tests/                # pytest test dosyaları
└── demo.py               # Canlı demo scripti
```

### 2.2 Temel Tasarım Kararları

**Şerit Temsili — `dict[int, str]` Sparse Yapı**

En kritik tasarım kararı şeridin nasıl tutulacağıydı. İlk akla gelen yaklaşım Python `list` veya `str` kullanmaktı; ancak ikisi de ciddi sorunlar yaratırdı:

- `str` immutable'dır: her yazma işlemi `O(n)` maliyetle yeni bir nesne yaratır.
- `list` ile negatif indeks sorunu çözümsüz kalır: `tape[-1]` Python'da listenin sonunu gösterir, sola taşmayı değil.

Bu nedenle `dict[int, str]` sparse yapısı seçildi. Yalnızca yazılan hücreler bellekte yer kaplar; okunmayan hücreler `get(pos, blank)` ile otomatik olarak blank döndürür. Negatif pozisyon tamamen güvenlidir çünkü dict'te `-1` gerçekten eksi birinci hücreyi ifade eder.


**Geçiş Tablosu Yapısı**

Geçişler `dict[state, dict[read_sym, (write, move, next)]]` olarak iç içe sözlük şeklinde tutulur. Bu yapı `O(1)` erişim sağlar ve YAML'dan ayrıştırma sırasında bir kez inşa edilir. Çok-şeritli motorda anahtar `tuple(reads)` olur (k uzunluklu demet), NTM'de ise değer liste olur: `list[(write, move, next)]`.


## 3. Tasarlanan Turing Makineleri

### TM-1 · Unary → Binary Çevirici

Girdi `1^n` biçiminde n adet `1`; çıktı n'in ikili gösterimi. Strateji: `1`'ler teker teker `X` ile işaretlenir, her işaretlemede `#` ile ayrılmış bir ikili sayaç bir artırılır. Tüm `1`'ler işaretlenince `X` ve `#` silindi, sayacın kendisi kalır. 45 geçiş kuralı gerekti; en karmaşık makineydi.

### TM-2 · İkili Sayı Karşılaştırıcı

Girdi `A#B` biçiminde; `A > B` ise kabul. Strateji: A'nın her biti `Y` ile işaretlenir, `#` geçilip B'nin karşılık gelen biti `X` ile işaretlenir. A erken biterse B büyüktür (ret); B erken biterse A büyüktür (kabul). Tek şeritte ileriye-geriye sürekli tarama gerektirdi — çok-şeritli TM'in motivasyonunu bizzat yaşattı.

### TM-3 · Dizgi Kopyalayıcı

Girdi `w ∈ {a,b}*`; çıktı `w#w`. Strateji: her karakter `A`/`Y` ile işaretlenir, `#` geçilerek kopya bölgesinin sonuna yazılır, geri dönülür, bir sonraki karakter alınır. Tüm karakterler işaretlenince `A→a`, `Y→b` geri çevrimi yapılır. 26 kural ile temiz bir tasarım ortaya çıktı.

### TM-4 · Bit Flipper (Öğrenci Seçimi)

Her `0` → `1`, her `1` → `0` dönüştürür. Strateji son derece basit: `q_start` tek geçiş durumu, iki yazma kuralı ve bir blank kuralı yeterli. Sadece 3 durum ve 4 geçiş kuralı kullanıldı — bu nedenle en kolay tasarlandı. Karmaşıklık analizi: girdi uzunluğu n için tam olarak `n + 1` adım sürer, yani `O(n)`.

**En zorlu makine TM-1'di.** İkili sayacı tek şerit üzerinde tutmak, her artırma işleminde sağa taşıma mantığını (carry) sola hareketle birleştirmek çok sayıda durum gerektirdi. Başlangıçta sayacı ayrı bir konumda tutmayı unutup üzerine yazdım; bu yüzden şerit yapısına `#` ayracını ekleyerek tasarımı yeniden kurdum.

---

## 4. Kavramsal Tartışma

### Halting Problemi TuringLab İçinde "Çözülebilir" mi?

Halting problemi şu soruyu sormaktadır: Verilen herhangi bir TM `M` ve girdi `w` için `M`'nin `w` üzerinde sonlanıp sonlanmayacağını her zaman doğru biçimde yanıtlayan bir TM `H` var mıdır? Turing'in 1936'daki kanıtı, böyle bir `H`'nin var olamayacağını göstermiştir.

TuringLab'da `run()` fonksiyonu `max_steps` parametresiyle çalışır. Bu parametre sayesinde sonsuz döngüye giren makineler `reason="timeout"` ile durdurulur. Bir bakışta bu bir "çözüm" gibi görünebilir; ancak değildir.

`max_steps` yalnızca **kaynağı tükenince** durduran pratik bir sınır koyar. `timeout` döndürmek "bu makine sonlanmaz" anlamına gelmez; yalnızca "bu kadar adımda sonlanmadı" demektir. Gerçek bir halting oracle'ı, sınır koymaksızın, her girdi için kesin bir evet/hayır kararı üretmek zorundadır.

Bunu TuringLab içinde "uygulamaya" çalışalım: tüm olası `SingleTapeTM` nesnelerini `from_yaml()` ile yükleyip her birini sonsuz adımla çalıştıran bir fonksiyon yazarsak, bu fonksiyon ya sonsuza kadar çalışır ya da yanlış karar verir. Çözümsüzlük, fonksiyonun Python'da yazılmasından değil, hesaplamanın kendisinin doğasından kaynaklanır.

Sonuç olarak TuringLab `timeout` mekanizması bir karar prosedürü değil, pratik bir erken durdurma mekanizmasıdır. Halting problemi, TuringLab'ın kaç satır koddan oluştuğundan bağımsız olarak, hiçbir hesaplama modeli içinde çözülemez.

---

## 5. Sınırlar ve İleri Çalışma

Mevcut motorda aşağıdaki eksiklikler ve geliştirme fırsatları mevcuttur:

**Kafa sola taşması:** `head_position < 0` olduğunda motor hata vermez, sadece negatif pozisyonda çalışmaya devam eder. Standart TM tanımı şerit solunun sınırlı olduğunu varsayar; bu durum için açık bir kontrol ve `README`'de belgelenmiş bir davranış politikası eklenmeliydi.

**Görselleştirici (Bonus D):** Kabul yolunun PNG/GIF olarak animasyonu tamamlanmadı. NTM'in BFS ağacını dal dal görselleştiren bir grafik, hesaplama ağacının nasıl yayıldığını somut biçimde gösterirdi.

**YAML doğrulama:** Geçiş kurallarındaki semboller `tape_alphabet` ile karşılaştırılmıyor. Yanlış sembol içeren bir kural sessizce ekleniyor; daha zengin bir `from_yaml()` bu tutarsızlıkları yükleme aşamasında yakalardı.

Bir hafta daha olsaydı önceliğim **Evrensel Turing Makinesi (UTM)** simülasyonu olurdu: mevcut `SingleTapeTM`'i kodlayıp başka bir TM'i çalıştıran üst-düzey bir makine yazmak, hem pedagojik açıdan çok değerli hem de TuringLab'ın en doğal uzantısı olurdu.

---

## 6. Kaynakça

1. Sipser, M. (2013). *Introduction to the Theory of Computation* (3rd ed.). Cengage Learning.
2. Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). *Introduction to Automata Theory, Languages, and Computation* (3rd ed.). Pearson.
3. Turing, A. M. (1936). On Computable Numbers, with an Application to the Entscheidungsproblem. *Proceedings of the London Mathematical Society*, 42(1), 230–265.
4. Python Software Foundation. (2024). *Python 3 Documentation — Data Structures*. https://docs.python.org/3/
5. YAML Ain't Markup Language (YAML™) Version 1.2. (2021). https://yaml.org/spec/1.2/