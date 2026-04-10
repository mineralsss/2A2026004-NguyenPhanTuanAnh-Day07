# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Phan Tuấn Anh
**Nhóm:** Z1
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:* High cosine similarity có nghĩa là hai vector (đại diện cho văn bản) chỉ theo cùng hướng, tức là chúng có ý nghĩa hoặc chủ đề tương tự nhau. Sim cao (gần 1) = văn bản liên quan, sim thấp (gần 0) = văn bản khác biệt hoặc không liên quan. 

**Ví dụ HIGH similarity:**
- Sentence A: Machine learning is a powerful tool for data analysis.
- Sentence B: Data science uses machine learning to extract insights from data.
- Tại sao tương đồng: Cả hai câu đều nói về machine learning và data analysis, có nhiều từ khóa giống nhau (machine learning, data), nên embedding của chúng sẽ chỉ theo cùng hướng.

**Ví dụ LOW similarity:**
- Sentence A: The cat is sleeping on the couch.
- Sentence B: Python is a popular programming language.
- Tại sao khác: Hai câu hoàn toàn nói về các chủ đề khác nhau (động vật vs lập trình), không có từ khóa chung, nên embedding chỉ theo các hướng khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:* Cosine similarity đo lường hướng của vector (góc giữa hai vector), không phụ thuộc vào độ dài, nên nó phản ánh ý nghĩa ngữ nghĩa của văn bản tốt hơn Euclidean distance. Vì các embedding có độ dài khác nhau tùy theo độ dài văn bản, cosine similarity cho phép so sánh công bằng giữa các tài liệu dài ngắn khác nhau, trong khi Euclidean distance sẽ bị ảnh hưởng bởi sự chênh lệch magnitude này. 

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Sử dụng công thức: `num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))` = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunk
> *Đáp án:* 23 chunk

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Viết 1-2 câu:* Sử dụng công thức: `num_chunks = ceil((10000 - 100) / (500 - 100))` = ceil(9900 / 400) = ceil(24.75) = 25 chunk. Chunk count tăng từ 23 lên 25 vì overlap nhiều hơn (100 thay vì 50). Overlap nhiều hơn giúp bảo toàn ngữ cảnh ở ranh giới chunk—thông tin quan trọng ở cuối chunk này sẽ được lặp lại ở đầu chunk tiếp theo, giúp tìm kiếm không mất ý nghĩa khi câu bị cắt ngang. 

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Luật

**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:* Domain luật có cấu trúc rõ ràng với các điều luật, khoản, chữ được tổ chức theo hệ thống hierarchical, giúp dễ gán metadata như mã số điều luật, loại hình pháp lý, và năm hiệu lực. Ngoài ra, retrieval chính xác trong lĩnh vực pháp lý là rất quan trọng vì một câu sai lệch có thể dẫn đến hậu quả lớn, nên đây là domain tốt để học về tối ưu hóa vector search và metadata filtering.

### Data Inventory

| # | Tên / Mô tả tài liệu | Nguồn | Số ký tự (ước tính) | Metadata đã gán |
|---|----------------------|-------|---------------------|-----------------|
| 1 | Xử phạt vượt đèn đỏ — xe ô tô, xe máy, xe đạp, người đi bộ (Nghị định 168/2024/NĐ-CP, Điều 6, 7, 9, 10) | legal_documents.md | ~900 | doc_id=1, category=giao_thông, law=NĐ168/2024 |
| 2 | Thu hồi đất do vi phạm pháp luật đất đai (Luật Đất đai 2024, Điều 81) | legal_documents.md | ~1200 | doc_id=2, category=đất_đai, law=LĐĐ2024 |
| 3 | Phạt không có giải pháp ngăn cháy khu vực sạc xe điện (Nghị định 106/2025/NĐ-CP, Điều 12) | legal_documents.md | ~700 | doc_id=3, category=phòng_cháy, law=NĐ106/2025 |
| 4 | Vi phạm Luật Bảo hiểm xã hội 2024 — xử phạt hành chính, kỷ luật, hình sự (Điều 132) | legal_documents.md | ~400 | doc_id=4, category=bảo_hiểm_xã_hội, law=LBHXH2024 |
| 5 | Nguyên tắc bảo vệ môi trường (Luật BVMT 2020, Điều 4) | legal_documents.md | ~1100 | doc_id=5, category=môi_trường, law=LBVMT2020 |
| 6 | Điều kiện chào bán trái phiếu ra công chúng (Luật Chứng khoán 2019, Điều 15) | legal_documents.md | ~900 | doc_id=6, category=chứng_khoán, law=LCK2019 |
| 7 | Chuyển người lao động làm công việc khác so với hợp đồng (BLLĐ 2019, Điều 29) | legal_documents.md | ~500 | doc_id=7, category=lao_động, law=BLLĐ2019 |
| 8 | Mức lương tối thiểu vùng 2024 theo Nghị định 74/2024/NĐ-CP | legal_documents.md | ~700 | doc_id=8, category=lao_động, law=NĐ74/2024 |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| doc_id | string / int | 4 | Giúp lọc hoặc xóa toàn bộ chunk thuộc cùng một văn bản nguồn khi cần kiểm soát theo tài liệu. |
| category | string | bảo_hiểm_xã_hội | Hỗ trợ `search_with_filter` theo chủ đề pháp lý, giảm nhiễu khi query thuộc domain cụ thể. |
| law | string | LBHXH2024 | Cho phép truy xuất chính xác theo tên/mã luật, rất hữu ích với câu hỏi viện dẫn văn bản pháp luật. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Độc lập | FixedSizeChunker (`fixed_size`) | 1 | 768.0 | Không, vì cắt theo size cố định không quan tâm ranh giới câu |
| Độc lập | SentenceChunker (`by_sentences`) | 2 | 383.5 | Có phần, vì tìm cố gắng giữ trọn câu nhưng không xử lý ranh giới paragraph |
| Độc lập | RecursiveChunker (`recursive`) | 1 | 768.0 | Có, vì tôn trọng cấu trúc tự nhiên của văn bản (paragraph, dòng, câu)

### Strategy Của Tôi

**Loại:** Recursive Chunker

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: Recursive Chunker sẽ chunk dựa trên các dấu câu theo thứ tự ưu tiên đã định sẵn từ "\n\n", "\n", ". ", " ", ""

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu:* Domain luật thường có cấu trúc theo điều, khoản, mục và nhiều đoạn văn dài nên Recursive Chunker giúp tách theo ranh giới tự nhiên trước khi phải cắt nhỏ. Cách này giữ được ngữ nghĩa của từng quy định tốt hơn so với cắt cố định, đồng thời vẫn tạo chunk đủ ngắn để retrieval chính xác hơn.

**Code snippet (nếu custom):**
```python
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


MARKDOWN_PATH = Path("/home/minerals/Day-07-Lab-Data-Foundations/legal_documents (1).md")


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _slugify_vi(text: str) -> str:
    base = _strip_accents(text).lower()
    base = re.sub(r"[^a-z0-9]+", "_", base)
    return base.strip("_")


def _abbr_from_title(title: str) -> str:
    cleaned = _strip_accents(title)
    words = re.findall(r"[A-Za-z0-9]+", cleaned)
    stop_words = {"va", "cua", "mot", "so", "bo", "luat"}
    letters = [w[0].upper() for w in words if w.lower() not in stop_words]
    return "".join(letters)


def _extract_metadata(content: str, doc_id: int) -> dict[str, str]:
    law_title_match = re.search(r"Luật\s+([A-Za-zÀ-ỹ0-9,\-\s]+?)\s+(\d{4})", content)
    if law_title_match:
        law_title = law_title_match.group(1).strip()
        law_year = law_title_match.group(2)
        category = _slugify_vi(law_title)
        law_code = f"L{_abbr_from_title(law_title)}{law_year}"
        return {
            "doc_id": str(doc_id),
            "category": category,
            "law": law_code,
        }

    decree_match = re.search(r"Nghị định\s+(\d+)/(\d{4})/NĐ-CP", content)
    if decree_match:
        number, year = decree_match.groups()
        return {
            "doc_id": str(doc_id),
            "category": "nghi_dinh",
            "law": f"ND{number}{year}",
        }

    return {
        "doc_id": str(doc_id),
        "category": "phap_luat_khac",
        "law": "UNKNOWN",
    }


def load_legal_documents(markdown_path: Path) -> list[Document]:
    raw = markdown_path.read_text(encoding="utf-8")
    heading_pattern = re.compile(r"^#\s+Document\s+(\d+)\s*$", re.MULTILINE)
    matches = list(heading_pattern.finditer(raw))

    documents: list[Document] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
        content = raw[start:end].replace("---", "").strip()
        if not content:
            continue

        doc_id = int(match.group(1))
        metadata = _extract_metadata(content, doc_id)
        metadata["source"] = str(markdown_path)

        documents.append(
            Document(
                page_content=content,
                metadata=metadata,
            )
        )
    return documents


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True,
)

docs = load_legal_documents(MARKDOWN_PATH)
all_splits = text_splitter.split_documents(docs)
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Tài liệu luật | SentenceChunker (`by_sentences`) | Trung bình | Trung bình | Khá tốt, vì giữ trọn câu và dễ đọc |
| Tài liệu luật | **RecursiveChunker (`recursive`)** | Thấp hơn baseline | Dài hơn baseline một chút | Tốt nhất cho domain này, vì giữ được ranh giới điều/khoản và ngữ cảnh tự nhiên |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | Recursive | 9 | Giữ ngữ cảnh tốt theo ranh giới tự nhiên điều/khoản, chunk coherent | Một số chunk còn dài, dễ kéo theo thông tin dư |
| Bảo | Sliding Window | 0 | Dễ triển khai, kích thước chunk ổn định | Cắt ngang ý nhiều, khó bám cấu trúc pháp lý nên retrieval thấp |
| Đức | Parent-Child | 2 | Kết hợp tổng quan và chi tiết, hỗ trợ truy hồi đa mức | Tăng độ phức tạp pipeline, mapping parent-child chưa luôn tối ưu |
| Nguyên | Document-structure | 3 | Bám sát heading/điều/khoản nên precision cao với truy vấn viện dẫn | Phụ thuộc mạnh vào chất lượng định dạng tài liệu đầu vào |
| Huân | Semantic | 3 | Nhóm các đoạn cùng ý nghĩa tốt, kết quả top-k liên quan cao | Tốn chi phí tính toán và nhạy với chất lượng embedding |
| Thắng | Agentic | 2 | Có thể rewrite query và tự chọn bước truy xuất linh hoạt | Độ ổn định chưa cao, đôi lúc over-reasoning gây lệch trọng tâm |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:* Recursive Chunker là chiến lược tốt nhất cho domain luật vì nó tôn trọng cấu trúc tự nhiên của văn bản pháp lý—tách theo đoạn (paragraph), dòng, và câu trước khi phải cắt nhỏ, giúp giữ ngữ cảnh và ngữ nghĩa của từng điều khoản một cách toàn vẹn. Phương pháp này cho điểm retrieval cao nhất (9/10) vì các chunk được tạo ra là coherent và dễ phù hợp với các truy vấn pháp lý, đặc biệt là những câu hỏi yêu cầu viện dẫn điều luật cụ thể.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng regex tìm xuống dòng "\n" và các dấu câu như ". ", "! ", "? "

**`RecursiveChunker.chunk` / `_split`** — approach:
> Algorithm hoạt động bằng cách tìm các dấu phân cách câu theo các thứ tự ưu tiên từ "\n\n", "\n", ". ", " ", ""

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add document` lưu mỗi record gồm id, content embedding và metadata rồi đưa vào bộ nhớ collection. khi `search`  store embeded query bằng cùng embedding function đó, tính cosine similarity giữa vectore query và emdding của từng record bằng compute_similarity trong file `chunking.py` rồi sắp xếp giảm dần theo `score` để trả về top-k kết quả

**`search_with_filter` + `delete_document`** — approach:
> *Viết 2-3 câu:* `search_with_filter` lọc các record theo metadata trước, rồi mới tính similarity trên tập đã lọc để kết quả không bị nhiễu bởi tài liệu ngoài điều kiện. `delete_document` xóa tất cả record có `metadata['doc_id']` khớp với document cần xóa; nếu dùng ChromaDB thì xóa theo `ids`, còn in-memory thì lọc lại danh sách `self._store`.

### KnowledgeBaseAgent

**`answer`** — approach:
> *Viết 2-3 câu:* `answer` gọi `store.search()` để lấy các chunk liên quan, rồi ghép phần `content` của chúng thành một khối `Context` ở đầu prompt. Sau đó prompt đặt câu hỏi ngay sau context theo format `Context -> Question -> Answer`, để LLM trả lời dựa trực tiếp trên các đoạn đã truy xuất thay vì đoán từ kiến thức chung.

### Test Results

```
(Vinai) minerals@DESKTOP-5NUPH1M:~/Day-07-Lab-Data-Foundations$ pytest tests/ -v
=============================================== test session starts ===============================================
platform linux -- Python 3.11.15, pytest-9.0.2, pluggy-1.6.0 -- /home/minerals/anaconda3/envs/Vinai/bin/python3.11
cachedir: .pytest_cache
rootdir: /home/minerals/Day-07-Lab-Data-Foundations
plugins: anyio-4.13.0, langsmith-0.7.25
collected 42 items                                                                                                

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                       [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                         [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                          [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                               [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED               [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                     [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                      [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                    [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                      [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                      [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                 [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                             [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                       [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED              [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                  [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED            [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                  [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                      [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                        [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                          [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                     [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                       [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED           [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                        [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                 [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                           [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                       [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                  [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                      [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                            [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                      [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED   [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                 [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED    [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED               [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED        [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED  [100%]

=============================================== 42 passed in 1.48s ================================================
```

**Số tests pass:** 42/42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Machine learning helps computers learn from data. | AI models can learn patterns from large datasets. | high | 0.047 | Không |
| 2 | The contract is valid under Article 15. | Điều 15 quy định hợp đồng có hiệu lực pháp lý. | high | 0.107 | Đúng |
| 3 | The cat is sleeping on the sofa. | Python supports object-oriented programming. | low | -0.016 | Đúng |
| 4 | The court accepted the evidence. | The judge admitted the proof in court. | high | 0.021 | Không |
| 5 | Hợp đồng lao động phải có thời hạn rõ ràng. | Employees should receive clear contract terms and duration. | high | 0.156 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Cặp bất ngờ nhất là Pair 1 và Pair 4 vì về mặt ngữ nghĩa khá gần nhau nhưng điểm similarity vẫn thấp. Điều này cho thấy với mock embedding (hash-based), vector không phản ánh đầy đủ ngữ nghĩa như embedding model thật, nên score có thể lệch trực giác. Vì vậy khi đánh giá hệ thống retrieval thực tế, cần dùng embedding backend phù hợp domain thay vì chỉ dựa vào mock backend.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)


| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Xe máy vượt đèn đỏ bị phạt bao nhiêu tiền? | Phạt tiền từ 4.000.000 đồng đến 6.000.000 đồng, bị trừ 04 điểm giấy phép lái xe. Nếu gây tai nạn giao thông thì phạt từ 10.000.000 đồng đến 14.000.000 đồng và trừ 10 điểm (Nghị định 168/2024/NĐ-CP, Điều 7) |
| 2 | Nhà nước thu hồi đất trong trường hợp nào? | Thu hồi đất khi người sử dụng đất vi phạm pháp luật đất đai như: sử dụng đất không đúng mục đích, hủy hoại đất, không thực hiện nghĩa vụ tài chính, không đưa đất vào sử dụng theo thời hạn quy định (Luật Đất đai 2024, Điều 81) |
| 3 | Khu vực sạc xe điện tập trung trong nhà cần có gì về phòng cháy? | Phải có giải pháp ngăn cháy đối với khu vực sạc điện cho xe động cơ điện tập trung trong nhà. Nếu không có sẽ bị phạt từ 40-50 triệu đồng (cá nhân) hoặc 80-100 triệu đồng (tổ chức) (Nghị định 106/2025/NĐ-CP, Điều 12) |
| 4 | Vi phạm luật bảo hiểm xã hội bị xử lý như thế nào? | Tùy theo tính chất, mức độ vi phạm mà bị xử phạt vi phạm hành chính, xử lý kỷ luật hoặc bị truy cứu trách nhiệm hình sự. Nếu gây thiệt hại thì phải bồi thường theo quy định của pháp luật (Luật Bảo hiểm xã hội 2024, Điều 132) |
| 5 | Nguyên tắc bảo vệ môi trường theo luật là gì? | Bảo vệ môi trường là quyền, nghĩa vụ và trách nhiệm của mọi người; là điều kiện, nền tảng cho phát triển bền vững; ưu tiên phòng ngừa ô nhiễm; người gây ô nhiễm phải chi trả, bồi thường; hoạt động phải công khai, minh bạch (Luật Bảo vệ môi trường 2020, Điều 4) |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Xe máy vượt đèn đỏ bị phạt bao nhiêu tiền? | Top-1 trả về đoạn xử phạt vượt đèn đỏ theo Nghị định 168/2024, có mức phạt tiền và trừ điểm GPLX | 0.705 | Có | Xe máy vượt đèn đỏ bị xử phạt tiền và trừ điểm GPLX theo Nghị định 168/2024; mức phạt cụ thể phụ thuộc hành vi và hậu quả |
| 2 | Nhà nước thu hồi đất trong trường hợp nào? | Điều 81 Luật Đất đai 2024: thu hồi khi đất được giao/cho thuê sai đối tượng, sai thẩm quyền hoặc vi phạm pháp luật đất đai | 0.530 | Có | Nhà nước thu hồi đất khi người sử dụng đất vi phạm quy định tại Điều 81 Luật Đất đai 2024 |
| 3 | Khu vực sạc xe điện tập trung trong nhà cần có gì về phòng cháy? | Điều 12 Nghị định 106/2025: phải có giải pháp ngăn cháy cho khu vực sạc xe điện tập trung trong nhà, nếu không sẽ bị phạt | 0.548 | Có | Khu vực sạc xe điện trong nhà bắt buộc có giải pháp ngăn cháy; vi phạm có thể bị phạt hành chính mức cao |
| 4 | Vi phạm luật bảo hiểm xã hội bị xử lý như thế nào? | Điều 132 Luật BHXH 2024: tùy mức độ có thể bị xử phạt hành chính, kỷ luật hoặc truy cứu trách nhiệm hình sự | 0.668 | Có | Vi phạm BHXH có thể bị xử phạt hành chính, kỷ luật hoặc truy cứu hình sự, và phải bồi thường nếu gây thiệt hại |
| 5 | Nguyên tắc bảo vệ môi trường theo luật là gì? | Điều 4 Luật BVMT 2020: nêu các nguyên tắc bảo vệ môi trường (trách nhiệm toàn xã hội, phòng ngừa, minh bạch, người gây ô nhiễm phải trả) | 0.777 | Có | Nguyên tắc cốt lõi gồm phòng ngừa ô nhiễm, trách nhiệm của mọi chủ thể và nguyên tắc người gây ô nhiễm phải chi trả |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Từ Nguyên, em học được tầm quan trọng của việc bám sát cấu trúc tài liệu đầu vào—chiến lược Document-structure của anh cho thấy dù retrieval score không cao nhất (3/10), nhưng precision với các truy vấn viện dẫn cụ thể lại rất tốt, điều mà Recursive Chunker của em chưa xử lý tốt. Từ Huân, em thấy giá trị của Semantic Chunking trong việc nhóm các đoạn cùng ý nghĩa, mặc dù tốn chi phí nhưng có thể cải thiện relevance của top-k kết quả cho những domain phức tạp.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Buổi chiều nay em cảm thấy ấn tượng khi thấy team demo sử dụng cách prompt vừa hỏi vừa kèm cả gold answer (đáp án) vào, tuy nhiên nó cũng sẽ làm bài học cho em để nhớ rằng bản thân sẽ không mắc sai lầm này trong quá trình làm dự án sau này.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Em sẽ thêm một metadata field cho "importance level" hay "section_type" (định nghĩa, xử phạt, điều kiện, v.v.) để có thể áp dụng các chunk_size và overlap khác nhau cho từng loại section, thay vì dùng cố định 1000/200. Ngoài ra, em sẽ preprocessing tài liệu luật để chuẩn hóa format các điều/khoản trước khi chunking, nhằm tăng consistency và giảm lỗi cắt ngang ở ranh giới.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 15 / 15 |
| My approach | Cá nhân | 10 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **90 / 100** |
