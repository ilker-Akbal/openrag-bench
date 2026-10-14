# OpenRAG Bench — Türkçe Hızlı Başlangıç

[English README](../README.md) ·
[GitHub v0.6.0 alfa ön sürümü](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0)

**OpenRAG Bench**, RAG sistemlerinin *belge erişim (retrieval) kalitesini*
ölçen, iki retrieval sürümünü karşılaştırabilen ve performans gerilemelerini
CI testlerinde yakalamaya yardımcı olan MIT lisanslı bir Python aracıdır.

Yalnızca belge arama sonuçlarını değerlendirir; üretilen cevapların
doğruluğunu, halüsinasyon oranını veya bilgiye dayandırılmasını doğrudan
ölçmez.

## Neler yapabilir?

- Precision@k, Recall@k, Hit@k, MRR@k, MAP@k; ikili ve dereceli NDCG@k
- JSON, JSONL ve TREC run/qrels dosyalarıyla değerlendirme
- Baseline/candidate karşılaştırması; JSON, HTML ve CSV raporları
- OpenRAG Guard ile kritik sorgu/kategori kuralları ve CI gerileme kontrolü
- Golden Dataset Studio ile çevrimdışı elle etiketleme; Capture & Replay
- İsteğe bağlı FAISS, BM25, MiniLM, LangChain ve LlamaIndex entegrasyon örnekleri

## Hızlı kurulum

Python 3.10–3.13 desteklenir. GitHub ön sürümü için:

```bash
python -m pip install https://github.com/ilker-Akbal/openrag-bench/releases/download/v0.6.0/openrag_bench-0.6.0-py3-none-any.whl
openrag-bench --help
```

Kodları ve örnekleri de kullanmak için:

```bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python -m unittest discover -s tests -v
python -m openrag_bench.cli examples/retrieval_results.json --k 2 --html report.html
```

## Kısa Capture & Replay demosu

Gerçek sıralı retrieval sonuçlarının kaydedilip Guard tarafından değerlendirildiği
küçük **sentetik** örneği denemek için kaynak kodu klonladıktan sonra:

~~~powershell
python examples/quickstart_capture_replay.py --output-dir reports/first-demo
Start-Process .\reports\first-demo\guard.html
~~~

Küçük kelime eşleştirme retriever'ları, genel NDCG@1 değeri yükselirken
kritik bir gizlilik belgesinin kaybolduğu örneği üretir. Raporun **BLOCKED**
göstermesi burada beklenen sonuçtur; test betiği doğru engellemeyi algıladığı
için çıkış kodu 0 olur. Örnek **güncel `main` kaynak dalındadır**,
yayımlanan v0.6.0 wheel paketinin içinde değildir.

Adım adım açıklama: [Kısa demo](DEMO_60_SECONDS.md).
Gerçek RAG sistemine bağlama: [Entegrasyon rehberi](OWN_RAG_QUICKSTART.md).

## Bağımsız kullanıcı geri bildirimi

Projeyi daha önce geliştirmemiş kişilerden temiz kurulum, ilk rapora ulaşma
süresi ve kendi retriever'ına bağlama hakkındaki **gerçek** geri bildirimleri
bekliyoruz. Komut, Python/işletim sistemi sürümü, commit SHA ve hatayı
yeniden üreten sentetik örnekleri
[GitHub geri bildirim konusuna](https://github.com/ilker-Akbal/openrag-bench/issues/4)
ekleyebilirsiniz. API anahtarı, özel veri veya gizli belge göndermeyin.

[İngilizce ve Türkçe paylaşım/geri bildirim çağrıları](COMMUNITY_OUTREACH.md).

## İki yöntemi karşılaştırma

```bash
openrag-bench examples/comparison_candidate.json --baseline examples/comparison_baseline.json --k 2 --metric ndcg_at_k --min-delta 0
```

Aday yöntemin seçilen metrikteki farkı belirlenen eşiğin altına düşerse araç
`2` çıkış kodu verir. Bu eşik istatistiksel anlamlılık testi değildir.

## Doğrulanmış SciFact sonuçları

BEIR SciFact test kümesindeki **5.183 doküman ve 300 test sorgusu** ile
iki gerçek çalışma yapıldı. NDCG@10 sonuçları:

| Yöntem | NDCG@10 |
| --- | ---: |
| TF-IDF | 0,6329 |
| BM25 | **0,6605** |
| MiniLM + FAISS | 0,6451 |

Bu değerler tek bir veri kümesinde, belirli yöntem ve ayarlarla ölçülmüştür.
Genel model üstünlüğü veya istatistiksel anlamlılık kanıtı değildir.

Kaynak ve çalışma kayıtları:
[SciFact açıklaması](BENCHMARK_SCIFACT.md) ·
[MiniLM + FAISS açıklaması](DENSE_SCIFACT.md) ·
[ölçüm verileri](../benchmarks/).

## Katkı ve destek

- [Katkı rehberi](../CONTRIBUTING.md)
- [Sorun ve özellik bildirimleri](https://github.com/ilker-Akbal/openrag-bench/issues)
- [Geliştirici katılımı](GET_INVOLVED.md)
- [Yardım sayfası](../SUPPORT.md)
- [Güvenlik bildirimleri](../SECURITY.md)

**Not:** Proje yenidir; dış kullanıcı sayısı, yaygın kullanım veya başka
projelerce benimsenme hakkında doğrulanmamış iddialar bulunmaz. Örnek test
girdileri sentetiktir, ancak yukarıdaki SciFact sonuçları gerçek verilerle
doğrulanmıştır. Harici veri kümeleri ve model ağırlıkları bu depoda yer almaz.

## LangChain ve LlamaIndex kullanımı

Mevcut LangChain veya LlamaIndex retriever nesnelerini, uygulamanızdaki
sabit doküman kimliklerini koruyarak değerlendirmeye bağlayabilirsiniz.
Temel paket bu framework'leri kendisi kurmaz. Ayrıntılar:
[Entegrasyon rehberi](FRAMEWORK_INTEGRATIONS.md).


## Gerçek Türkçe etiketli retrieval benchmark'ı

Türkçe Vikipedi'den **54 makale ve insan tarafından etiketlenmiş 58 sorgu**
üzerinde iki farklı metin normalizasyonunu **aynı BM25 algoritmasıyla**
karşılaştırabilirsiniz:

~~~bash
python examples/turkish_real_benchmark.py --download --k 10 --output turkish_summary.json
~~~

Veri, üçüncü taraf [Turkish RAG Eval](https://huggingface.co/datasets/RizgarOzan/turkish-rag-eval)
projesinden belirli commit ile yalnızca çalıştırma sırasında indirilir.
Korpus ve etiketler CC BY-SA 4.0 lisanslıdır; bu depoya veya MIT pakete
kopyalanmaz. Çıktı yalnızca sayısal metrikleri ve SHA-256 özetlerini içerir.
Tek bir sağlık alanındaki 58 soru, genel Türkçe RAG doğruluğunu kanıtlamaz.
Ayrıntılar: [Veri ve yöntem belgesi](TURKISH_BENCHMARK.md).


## OpenRAG Guard (v0.5.0)

Genel retrieval metriği artsa dahi kritik bir soru bozuluyorsa sürümü
engellemek için kurallar tanımlar. Veri ve politikayı internetsiz doğrular:

~~~powershell
openrag-bench init --directory demo
openrag-bench doctor demo/candidate.json --baseline demo/baseline.json --policy demo/guard-policy.json --k 1
openrag-bench guard demo/candidate.json --baseline demo/baseline.json --policy demo/guard-policy.json --k 1 --html guard.html
openrag-bench guard demo/candidate-regression.json --baseline demo/baseline.json --policy demo/guard-policy.json --k 1
~~~

Son komut örnek kritik soruda hatayı yakalar ve çıkış kodu 2 olur. Belgeler
sentetiktir; [ayrıntılı politika sözleşmesi](GUARD.md).


## Golden Dataset Studio — v0.5.0 alfa sürümü

Tek komutla internetsiz, tek HTML dosyalı bir etiketleme editörü oluştur:

    openrag-bench studio --output golden-dataset-studio.html
    Start-Process .\golden-dataset-studio.html

Soru ve belge kimliği ekle, doğru belgeleri 1–3 dereceyle elle işaretle,
kritik sorguları seç ve bir taslak olarak yerel JSON kaydet. Etiket ve
Guard politikası dosyalarını ayrıca dışa aktar.

Dışa aktarılan retrieved_ids alanı kasıtlı olarak boştur; bu veriyi gerçek
RAG retriever çıktılarıyla birleştirmeden kalite sonucu saymayın.
Kılavuz: [Golden Dataset Studio](STUDIO.md).
