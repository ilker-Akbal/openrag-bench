# OpenRAG Bench — Türkçe Hızlı Başlangıç

[English README](../README.md) ·
[GitHub v0.2.0 ön sürümü](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.2.0)

**OpenRAG Bench**, RAG sistemlerinin *belge erişim (retrieval) kalitesini*
ölçen, iki retrieval sürümünü karşılaştırabilen ve performans gerilemelerini
CI testlerinde yakalamaya yardımcı olan MIT lisanslı bir Python aracıdır.

Yalnızca belge arama sonuçlarını değerlendirir; üretilen cevapların
doğruluğunu, halüsinasyon oranını veya bilgiye dayandırılmasını doğrudan
ölçmez.

## Neler yapabilir?

- Precision@k, Recall@k, Hit@k, MRR@k ve ikili NDCG@k
- JSON ve TREC run/qrels dosyalarıyla değerlendirme
- Baseline/candidate karşılaştırması ve JSON/HTML raporu
- CI'da metrik gerilemesi için başarısız çıkış kodu
- İsteğe bağlı FAISS, BM25 ve MiniLM entegrasyon örnekleri

## Hızlı kurulum

Python 3.10–3.13 desteklenir. GitHub ön sürümü için:

```bash
python -m pip install https://github.com/ilker-Akbal/openrag-bench/releases/download/v0.2.0/openrag_bench-0.2.0-py3-none-any.whl
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
