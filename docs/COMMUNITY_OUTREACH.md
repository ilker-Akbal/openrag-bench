# OpenRAG Bench — community introduction and independent test invitation

These are **ready-to-review outreach drafts**, not evidence that posts have
been published to Reddit, LinkedIn, Hacker News, Discord or any other platform.
Respect each community's self-promotion and link policies; only post where
feedback requests are permitted. Personalize each post and avoid mass posting,
vote requests, manufactured testimonials, or claims of independent adoption.

Project: https://github.com/ilker-Akbal/openrag-bench

Current latest public GitHub **alpha**: v0.6.0 (MIT, Python 3.10–3.13,
not published on PyPI). The newer synthetic quickstart example is on
\`main\` and is **not bundled in the v0.6.0 wheel**.

## English — short introduction

**Subject: OpenRAG Bench — offline retrieval regression checks for RAG (MIT, feedback welcome)**

I'm building OpenRAG Bench, an MIT-licensed Python tool for checking whether
changes to a RAG retriever make important document matches worse.

It compares ranked document IDs with human-reviewed relevance judgments,
produces offline HTML reports, and can block a candidate that improves the
overall NDCG while losing a critical result.

No LLM service or API key is required for the core. v0.6.0 includes a
local labeling Studio plus Capture & Replay. We've independently scored
TF-IDF and BM25 against the BEIR SciFact evaluation format (5,183 documents,
300 labeled queries), but that is **not** a claim of general superiority.

Repository: https://github.com/ilker-Akbal/openrag-bench

Quick source-checkout demo:
\`python examples/quickstart_capture_replay.py --output-dir reports/first-demo\`
(after cloning and \`pip install -e .\`).

I'm looking for genuinely independent install/reproduction feedback:
environment, time to first report, confusing steps or bugs, and whether
the evaluation contract fits your own LangChain/LlamaIndex/custom retriever.
Please report synthetic/redacted examples in issue #4:
https://github.com/ilker-Akbal/openrag-bench/issues/4

## English — short social post

A RAG retriever can improve overall NDCG and still lose an essential
privacy-document hit.

OpenRAG Bench (MIT, Python 3.10–3.13) evaluates ranked retrieval outputs,
compares baseline vs candidate and uses configurable Guard policies to
block regressions. Offline reports, Studio labels and Capture & Replay;
no core LLM/API requirement.

New public v0.6.0 alpha; independent user feedback welcome. Synthetic
1-minute demonstration and issue template:
https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DEMO_60_SECONDS.md
https://github.com/ilker-Akbal/openrag-bench/issues/4

It measures retrieval relevance, **not** generated-answer correctness.

## Türkçe — geliştirici toplulukları için tanıtım

**Başlık: OpenRAG Bench — RAG sistemleri için çevrimdışı retrieval kalite ve regresyon testleri (MIT)**

RAG sistemlerinde embedding modeli, indeksleme veya retriever değiştiğinde
ortalama metrikler iyileşse bile önemli bir soru için gereken belge artık
bulunamayabiliyor. Bu sorunu daha erken yakalamak için **OpenRAG Bench**
adında açık kaynak bir Python aracı geliştiriyorum.

Araç; etiketlenmiş sorgularla sıralı belge sonuçlarını karşılaştırıyor,
HTML/JSON rapor oluşturuyor ve belirlenen kritik sorgu kuralları bozulursa
sürüm geçişini engelleyebiliyor. Golden Dataset Studio ile elle etiketleme,
Capture & Replay ile kayıtlı retrieval sonuçlarını yeniden değerlendirme
desteği bulunuyor. Temel değerlendirme için API anahtarı veya bulut modeli
gerekmiyor.

**v0.6.0 GitHub alfa sürümü yayımlandı.** SciFact veri kümesindeki 5.183
belge/300 sorguyla TF-IDF ve BM25 testleri doğrulandı; bu tek deney genel
model üstünlüğü veya harici kullanıcı benimsenmesi kanıtı değildir.

GitHub: https://github.com/ilker-Akbal/openrag-bench
Türkçe hızlı başlangıç:
https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/README_TR.md
Kısa çalıştırılabilir demo:
https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DEMO_60_SECONDS.md

RAG, LangChain veya LlamaIndex kullanan geliştiricilerden özellikle **gerçek
kurulum deneyimi**, hata raporu ve entegrasyon zorlukları hakkında yorum
bekliyorum. Lütfen özel verileri paylaşmadan, sentetik/anonimleştirilmiş
örneklerle şu konuya yazın:
https://github.com/ilker-Akbal/openrag-bench/issues/4

## Türkçe — kısa sosyal medya paylaşımı

RAG sisteminizin ortalama retrieval metriği artsa bile kritik bir belgenin
artık bulunamadığını nasıl fark ediyorsunuz?

Geliştirdiğim açık kaynak **OpenRAG Bench**, baseline/candidate sonuçlarını
karşılaştırıyor ve Guard kurallarıyla kritik retrieval gerilemelerini
engelleyebiliyor. Golden Dataset Studio + Capture & Replay, çevrimdışı
HTML raporlar, MIT lisansı. v0.6.0 GitHub alfa yayında.

GitHub: https://github.com/ilker-Akbal/openrag-bench
Demo: https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DEMO_60_SECONDS.md

Bağımsız kurulum yapan geliştiricilerden geri bildirim bekliyorum.
Not: Üretilen LLM cevaplarının doğruluğunu değil, belge erişim kalitesini ölçüyor.

## Independent reproduction request

If you have not worked on the project, would you try one of these paths?

1. **Quick local smoke:** clean clone, \`pip install -e .\`,
   \`python examples/quickstart_capture_replay.py --output-dir reports/first-demo\`,
   open the generated \`guard.html\`. Report whether you see a **BLOCKED**
   critical policy despite positive overall NDCG delta. This is
   an **original synthetic integration demo**.
2. **Real-data benchmark (optional):** follow
   [SciFact](BENCHMARK_SCIFACT.md), respecting external corpus licenses and
   checksum validation. Report the measured metrics and full environment.
3. **Your own RAG integration (optional):** follow
   [your-retriever setup](OWN_RAG_QUICKSTART.md). Do not share customer
   queries or corpus texts; include only redacted behavior and stable-ID
   compatibility findings.

### What would help us improve it

Please report: OS, Python version, installation method, exact commit
(\`git rev-parse HEAD\`) or wheel version, command used, **measured** time
to first report, whether it worked, what was confusing, and any reproducible
bug with **synthetic** inputs. If you did not complete a step, indicate
\`BLOCKED\` with the specific reason. We welcome negative feedback.

[Independent use and reproduction issue #4](https://github.com/ilker-Akbal/openrag-bench/issues/4) ·
[Bug report template](../.github/ISSUE_TEMPLATE/bug_report.yml) ·
[Security disclosures](../SECURITY.md)

A maintainer's own CI run and this project's synthetic demo do **not** count
as independent developer adoption. Do not report API tokens, private
retrieved IDs, unlicensed third-party text or internal screenshots.

## Responsible publishing checklist for the maintainer

- [ ] Choose a community where a feedback request fits the rules.
- [ ] Read that community's current self-promotion, links and disclosure rules.
- [ ] Use the appropriate English/Turkish draft and edit to fit its audience.
- [ ] Disclose that you're the maintainer; avoid vote/engagement requests.
- [ ] Publish **once** through your own authorized account.
- [ ] Record the public link and date, without collecting personal details.
- [ ] Reply to genuine feedback, create technical issues with permission, and
      do not count replies as confirmed installs unless reproducible evidence
      is provided.

**Status:** Drafts prepared for sharing. No external community publication
has occurred merely by committing this file.
