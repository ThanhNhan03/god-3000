# BUILD SPEC: Legacy Migration Harness — Multi-Agent IDE cho VB4-COBOL → .NET MVC
> File này **kết hợp 2 tài liệu nguồn**: (1) `spec-hybrid-multi-agent-ide.md` (kiến trúc Orchestrator/Worker + IDE 2-pane + streaming) và (2) `Q9 x FUQN — Harness-Driven Migration` (đề bài hackathon MigrationOps, 4 track: Discovery / Conversion / Validation / Orchestrator). Viết cho AI code-gen agent đọc và triển khai trực tiếp.

---

## 0. Bài toán tổng hợp (tại sao gộp 2 tài liệu)

| Nguồn | Cho cái gì | Thiếu cái gì |
|---|---|---|
| **Spec IDE Hybrid Multi-Agent** | Kiến trúc Orchestrator (model mạnh) + N Worker (model rẻ), UI 2 khung, thinking stream, schema JSON chuẩn, 6 worker role generic (Plan/Code/Research/QA/Validation) | Worker generic, chưa gắn với domain migration cụ thể nào; `[MỨC 1]` Validation Worker chỉ "kiểm schema/lint", **không thực sự build & chạy test** |
| **Đề bài Harness-Driven Migration** | Domain cụ thể: VB4-COBOL → .NET MVC, 4 track rõ ràng (Discovery, Conversion, Validation, Orchestrator end-to-end), tiêu chí chấm điểm, input/output mẫu | Không có kiến trúc UI/streaming/chi tiết kỹ thuật triển khai — chỉ là đề bài, chưa phải spec code-gen |

**Kết luận thiết kế:** ta build **Track 4 (Orchestrator Agent — end-to-end pipeline)** làm sản phẩm chính, dùng nguyên khung kiến trúc IDE Hybrid Multi-Agent làm nền tảng kỹ thuật, nhưng **thay 6 worker generic bằng 5 worker chuyên biệt hoá cho migration** (Discovery / Conversion / Test-Gen / Build-Validate / QA-Review), trong đó **Build-Validate Worker bắt buộc phải nâng cấp lên `[MỨC 2]` (Code Execution)** — vì yêu cầu đầu bài là *"output chạy được, pass test case"*, không chỉ là JSON hợp lệ.

---

## 1. Input / Output Contract (yêu cầu cốt lõi của bạn)

### Input — 1 trong 2 dạng
- **Dạng A — single file:** người dùng upload 1 "main page" code — có thể là 1 file VB (`.frm` / `.bas` / `.cls`) hoặc 1 file COBOL (`.cbl` / `.cpy`).
- **Dạng B — zip project:** người dùng upload 1 file `.zip` chứa cả cụm: nhiều VB form + COBOL program + copybook liên quan tới nhau.
- Backend cần 1 bước **ingest & unzip** thống nhất, luôn quy về cùng 1 cấu trúc trong workspace ảo (`/workspace/source/**`) trước khi Discovery Worker chạy — để pipeline không cần biết input ban đầu là 1 file hay cả project.

### Output — bắt buộc đạt đủ 4 điều kiện, không phải chỉ "có code"
1. **Code .NET MVC mới** được sinh ra (`Controller` + `Razor View` + `ViewModel/DTO` + `COBOL Interop layer`).
2. **Build thành công** — `dotnet build` không lỗi compile.
3. **Chạy được** — project khởi động được (`dotnet run` hoặc smoke test HTTP request trả về 200).
4. **Test case PASS** — bộ test tự sinh (xUnit/NUnit) từ logic nghiệp vụ VB gốc phải chạy và pass, không phải test rỗng/giả.

> Nếu 1 trong 4 điều kiện trên không đạt sau số lần retry tối đa → hệ thống **không được báo "thành công"** — phải escalate rõ ràng cho người dùng kèm lý do fail cụ thể (xem mục 3).

---

## 2. Kiến trúc — Orchestrator + 5 Worker chuyên biệt hoá cho Migration

> Giữ nguyên toàn bộ hạ tầng streaming/UI của spec IDE gốc (SSE, thinking block, Monaco, 2-pane). Phần thay đổi chính nằm ở **vai trò worker** và **thêm 1 vòng lặp validation bắt buộc**.

```
User: upload file/zip
     │
     ▼
┌─────────────────────┐
│   ORCHESTRATOR        │  model mạnh, thinking bật [MỨC 1]
│   - unzip/ingest        │
│   - gọi Discovery Worker │
└──────────┬───────────┘
           ▼
┌─────────────────────────┐
│  DISCOVERY WORKER          │  [MỨC 1] — Track 1
│  - parse VB (.frm/.bas/.cls)│
│  - parse COBOL (.cbl/.cpy)  │
│  - dependency graph          │
│  - complexity score/module   │
│  - migration order đề xuất    │
└──────────┬───────────────┘
           ▼  (lặp qua từng module theo thứ tự đề xuất)
┌─────────────────────────┐
│  CONVERSION WORKER          │  [MỨC 1] — Track 2
│  - sinh Controller/View/     │
│    ViewModel + Interop layer │
└──────────┬───────────────┘
           ▼
┌─────────────────────────┐
│  TEST-GEN WORKER             │  [MỨC 1] — Track 3 (phần sinh test)
│  - đọc logic nghiệp vụ VB gốc │
│  - sinh xUnit/NUnit test case  │
└──────────┬───────────────┘
           ▼
┌─────────────────────────┐
│  BUILD-VALIDATE WORKER       │  ★ [MỨC 2] — thực thi thật, KHÔNG chỉ trả JSON
│  - dotnet build trong sandbox │
│  - dotnet test trong sandbox   │
│  - trả lỗi compile / test log   │
└──────────┬───────────────┘
           │
     ┌─────┴─────┐
   FAIL         PASS
     │             │
     ▼             ▼
┌───────────────┐   ┌─────────────────┐
│ QA-REVIEW       │   │ Đánh dấu module   │
│ WORKER           │   │ DONE + confidence │
│ - behavioral diff│   │ score               │
│ - phân loại lỗi:  │   └────────┬────────┘
│   compile/logic/   │            │
│   edge-case         │            ▼
└────────┬────────┘    Orchestrator chuyển
         │              sang module tiếp theo
         ▼
  route lại cho Conversion/Test-Gen Worker
  kèm error context cụ thể (retry, xem mục 3)
```

### 2.1 Vai trò 5 worker (so với 6 worker gốc trong spec IDE)

| Worker mới | Thay thế cho worker gốc | Mức | Input | Output |
|---|---|---|---|---|
| `discovery_worker` | Plan Worker + Research Worker | `[MỨC 1]` | VB + COBOL source (đã unzip) | Inventory + dependency graph + complexity score + thứ tự migrate |
| `conversion_worker` | Code Worker | `[MỨC 1]` | 1 VB form + COBOL program liên quan + copybook + (nếu retry) error context từ Build-Validate/QA | .NET MVC code (Controller/View/ViewModel/Interop) |
| `test_gen_worker` | *(mới, tách riêng khỏi QA Worker gốc)* | `[MỨC 1]` | VB business logic gốc + .NET code vừa sinh | Bộ test xUnit/NUnit |
| `build_validate_worker` | Validation Worker (nâng cấp) | **`[MỨC 2]`** | .NET project + test suite | Build log, test log, pass/fail per test |
| `qa_review_worker` | QA Worker | `[MỨC 1]` | Build/test log fail + VB gốc + .NET sinh ra | Behavioral diff report, phân loại lỗi, confidence score |

> **Vì sao tách `test_gen_worker` riêng khỏi QA?** Trong đề bài gốc, Track 3 gộp cả "sinh test" và "so sánh hành vi". Nhưng nếu để 1 worker vừa tự sinh test vừa tự chấm test do chính nó sinh ra → dễ thiên lệch (cùng vấn đề đã nêu ở spec IDE mục "Vòng lặp QA": *"QA thường lồng trong 1 agent chung... giảm thiên lệch khi 1 agent tự chấm bài chính nó"*). Tách ra: `test_gen_worker` chỉ sinh test dựa trên logic VB gốc (không thấy code .NET), `build_validate_worker` chạy test một cách máy móc (không LLM), `qa_review_worker` mới là bên diễn giải kết quả fail.

---

## 3. Chu trình Validation chuẩn (Standard Validation Loop) — phần lõi bắt buộc

Đây là phần trả lời trực tiếp yêu cầu *"cái đó nó sẽ có chu trình validation chuẩn"*.

```
Bước 0: Discovery Worker đã xác định thứ tự migrate module.
Với mỗi module (1 VB form + COBOL liên quan):

  retry_count = 0
  MAX_RETRY = 3   // cấu hình được, mặc định 3

  LOOP:
    1. conversion_worker sinh code .NET
       (nếu retry_count > 0: kèm theo error_context từ lần fail trước)

    2. Nếu chưa có test cho module này:
         test_gen_worker sinh test case từ VB logic gốc
       (chỉ sinh 1 lần/module, không sinh lại mỗi vòng lặp —
        tái dùng bộ test cũ để đảm bảo "target" ổn định giữa các lần retry)

    3. build_validate_worker  [MỨC 2 — chạy lệnh thật trong sandbox]:
         a. dotnet restore
         b. dotnet build
            -> NẾU LỖI COMPILE: gói lỗi thành error_context
               { stage: "build", errors: [...], retry_count } -> GOTO bước 5
         c. dotnet test
            -> ghi nhận per-test: { test_name, status: pass|fail, message }

    4. Nếu 100% test PASS:
         -> module = DONE, gán confidence_score (mục 3.1)
         -> BREAK LOOP, chuyển module tiếp theo

    5. Nếu build lỗi HOẶC có test FAIL:
         retry_count += 1
         NẾU retry_count > MAX_RETRY:
             -> module = ESCALATED (xem mục 3.2)
             -> BREAK LOOP, chuyển module tiếp theo (không chặn toàn pipeline)
         NGƯỢC LẠI:
             qa_review_worker phân tích log lỗi:
               - build error -> tóm tắt lỗi compile, dòng/cột, khả năng nguyên nhân
               - test fail   -> behavioral diff: input nào, VB trả gì, .NET trả gì,
                                phân loại: logic sai / edge case (null, date, EBCDIC,
                                numeric precision COMP-3) / thiếu field COPYBOOK
             error_context = kết quả phân tích trên
             GOTO bước 1 (retry conversion_worker với error_context)
```

### 3.1 Confidence score (yêu cầu bonus trong đề bài gốc)
Mỗi module PASS được gán `confidence_score` (0–1), tính từ tổ hợp:
- Số lần retry cần để pass (0 retry = confidence cao nhất)
- Tỷ lệ test coverage so với số nhánh logic phát hiện được ở bước Discovery
- Có xuất hiện các case rủi ro cao (COMP-3, REDEFINES, 88-level condition, EBCDIC↔UTF-8) trong module hay không — nếu có, giảm nhẹ confidence dù đã pass, để nhắc reviewer con người soát kỹ hơn.

### 3.2 Escalation (Human-in-the-loop checkpoint)
Khi 1 module vượt `MAX_RETRY` mà vẫn fail:
- Orchestrator **không dừng toàn bộ pipeline** — các module khác tiếp tục chạy song song/tuần tự bình thường.
- Module đó được đánh dấu `ESCALATED` trên **Validation Dashboard** (mục 5), kèm toàn bộ lịch sử: từng lần retry, error_context, diff report — để dev xem lại nhanh, không phải đọc log thô.
- Đây chính là "Human-in-the-loop checkpoint" mà đề bài yêu cầu ở Track 4.

---

## 4. Data Contract (mở rộng từ schema gốc của spec IDE)

### 4.1 Task assignment / Result — theo đúng khuôn schema JSON cố định gốc, chỉ đổi `worker_role` và `output_schema`

```json
// Discovery
{
  "task_id": "task_disc_001",
  "worker_role": "discovery_worker",
  "instruction": "Phân tích toàn bộ project VB4-COBOL đã unzip, sinh inventory + dependency graph",
  "input_data": { "workspace_path": "/workspace/source" },
  "output_schema": {
    "modules": [{ "form": "string", "cobol_programs": ["string"], "complexity_score": "number" }],
    "migration_order": ["string"]
  }
}
```

```json
// Conversion (kèm error_context khi retry)
{
  "task_id": "task_conv_004",
  "worker_role": "conversion_worker",
  "instruction": "Sinh .NET MVC cho form frmInvoice.frm + INVOICE.cbl",
  "input_data": {
    "vb_source": "...", "cobol_source": "...", "copybook": "...",
    "error_context": { "stage": "test", "retry_count": 1, "diff": "..." }
  },
  "output_schema": { "files": [{ "path": "string", "content": "string" }] }
}
```

```json
// Build-Validate — [MỨC 2], Worker thực sự chạy lệnh
{
  "task_id": "task_bv_004",
  "worker_role": "build_validate_worker",
  "instruction": "Build và chạy test cho project vừa sinh",
  "input_data": { "project_path": "/workspace/output/InvoiceModule" },
  "output_schema": {
    "build_status": "success | fail",
    "build_errors": ["string"],
    "tests": [{ "name": "string", "status": "pass | fail", "message": "string" }]
  }
}
```

### 4.2 SSE Event — thêm event mới cho vòng lặp validation (giữ nguyên toàn bộ event gốc của spec IDE, chỉ bổ sung)

```ts
type MigrationEvent =
  | AgentEvent  // toàn bộ event gốc: thinking_delta, tool_use, tool_result, file_update, text_delta, done...
  | { type: "module_status"; module: string; status: "pending" | "converting" | "validating" | "done" | "escalated"; retry_count: number }
  | { type: "build_result"; module: string; status: "success" | "fail"; errors?: string[] }         // [MỨC 2]
  | { type: "test_result"; module: string; test_name: string; status: "pass" | "fail"; message?: string } // [MỨC 2]
  | { type: "diff_report"; module: string; category: "compile" | "logic" | "edge_case"; summary: string }
  | { type: "confidence_score"; module: string; score: number };
```

---

## 5. UI — mở rộng IDE 2-pane gốc

- **Workspace Pane (trái):** thêm chế độ xem **song song source ↔ output** (VB/COBOL gốc bên trái file tree, .NET sinh ra bên phải), có thể toggle diff view.
- **Agent Chat Pane (phải):** giữ nguyên thinking block + worker status chip, nhưng chip giờ theo **5 worker mới**, không phải 6 worker gốc.
- **[MỚI] Validation Dashboard tab** (đặt cạnh tab "Remote Screen" của `[MỨC 3]` nếu có dùng):
  - Bảng modules × trạng thái (pending/converting/validating/done/escalated), retry_count, confidence_score.
  - Click 1 module `escalated` → mở panel chi tiết: toàn bộ lịch sử retry, build log, test log, diff report — đúng tinh thần *"Summary dashboard: modules processed, success rate, issues found"* trong đề bài gốc.

---

## 6. Tech stack (gộp — Approach C "Hybrid" trong đề bài + hạ tầng IDE spec)

| Layer | Công nghệ | Mức |
|---|---|---|
| Frontend | React + Vite + TS + Tailwind + Monaco + `react-resizable-panels` + Zustand | — (giữ nguyên spec IDE gốc) |
| Streaming | SSE | — |
| Backend | Node.js (Express/Fastify) — Orchestrator + routing worker | `[MỨC 1]` |
| **Parser VB** | tree-sitter-vb hoặc ANTLR VB4 grammar (deterministic, không dùng LLM để parse) | Discovery |
| **Parser COBOL/COPYBOOK** | GnuCOBOL parser / tree-sitter-cobol / custom copybook parser (deterministic) | Discovery |
| **Code generation** | LLM (Anthropic API) — sáng tạo, xử lý edge case, không dùng thuần template | Conversion, Test-Gen |
| **Build/Test execution** | ★ Sandbox container có sẵn **.NET SDK** — chạy `dotnet build`/`dotnet test` thật, cô lập mạng | ★ `[MỨC 2]` (dùng tính năng Code Execution/sandbox, không tự dựng hạ tầng phức tạp — theo đúng nguyên tắc mục 0.c của spec IDE gốc) |
| AI Provider | Anthropic API — model mạnh cho Orchestrator + Conversion Worker (cần reasoning tốt để xử lý logic COBOL phức tạp); model rẻ hơn cho Discovery/Test-Gen/QA-Review nếu muốn tối ưu chi phí | — |
| Storage | SQLite (dependency graph, module status, retry history), filesystem (source + output project) | — |

---

## 7. Cấu trúc thư mục dự kiến

```
project/
├── src/                              # Frontend (giữ nguyên spec IDE gốc)
│   ├── components/
│   │   ├── WorkspacePane/
│   │   │   ├── FileTree.tsx
│   │   │   ├── CodeEditor.tsx
│   │   │   ├── DiffView.tsx            # [MỚI] source ↔ output song song
│   │   │   └── Tabs.tsx
│   │   ├── ChatPane/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ThinkingBlock.tsx
│   │   │   ├── WorkerStatusChip.tsx
│   │   │   └── MessageBubble.tsx
│   │   └── ValidationDashboard/        # [MỚI]
│   │       ├── ModuleTable.tsx
│   │       └── EscalationDetail.tsx
│   ├── store/useAgentStore.ts
│   └── App.tsx
├── server/
│   ├── routes/
│   │   ├── agent.stream.ts
│   │   └── ingest.ts                   # [MỚI] nhận file/zip upload, unzip vào workspace
│   ├── agents/
│   │   ├── orchestrator.ts
│   │   └── workers/
│   │       ├── discoveryWorker.ts      # [MỚI]
│   │       ├── conversionWorker.ts     # [MỚI]
│   │       ├── testGenWorker.ts        # [MỚI]
│   │       ├── buildValidateWorker.ts  # [MỚI] [MỨC 2]
│   │       └── qaReviewWorker.ts       # [MỚI]
│   ├── parsers/                        # [MỚI]
│   │   ├── vbParser.ts                 # tree-sitter-vb / ANTLR
│   │   └── copybookParser.ts
│   ├── sandbox/                        # [MỚI] [MỨC 2]
│   │   ├── dotnetSandbox.ts            # chạy dotnet build/test trong container
│   │   └── resultParser.ts             # parse output build/test thành JSON
│   └── index.ts
└── package.json
```

---

## 8. Thứ tự triển khai đề xuất (task list cho AI code-gen)

### Giai đoạn A — Nền tảng IDE (tái dùng gần như nguyên vẹn từ spec gốc)
1. Scaffold Vite + React + TS + Tailwind, layout 2-pane resizable.
2. Monaco + File Tree (mock data), Chat Pane tĩnh (thinking block, worker chip).
3. Backend `/api/agent/stream` — Orchestrator gọi Anthropic API, `thinking: enabled`, SSE thô.
4. Nối SSE thật, `dispatch_worker` tool cho Orchestrator.

### Giai đoạn B — Ingest & Discovery
5. Endpoint upload — nhận 1 file hoặc `.zip`, unzip vào `/workspace/source`, chuẩn hoá cấu trúc.
6. `discoveryWorker.ts` — tích hợp `vbParser`/`copybookParser`, sinh inventory + dependency graph + complexity score + migration order. Hiển thị kết quả lên Workspace Pane (file tree gắn nhãn thứ tự migrate).

### Giai đoạn C — Conversion + Test-Gen
7. `conversionWorker.ts` — prompt sinh Controller/View/ViewModel/Interop từ 1 module (VB + COBOL + copybook).
8. `testGenWorker.ts` — prompt sinh xUnit/NUnit test từ VB logic gốc (chạy 1 lần/module, cache lại).
9. Emit `file_update` — Workspace Pane hiển thị code .NET vừa sinh, diff với source gốc.

### Giai đoạn D — ★ Build-Validate (`[MỨC 2]`, phần bắt buộc để đạt "chạy được, pass test")
10. Dựng sandbox container có sẵn .NET SDK (Docker image `mcr.microsoft.com/dotnet/sdk`), cô lập mạng, không quyền truy cập file hệ thống thật ngoài `/workspace/output/<module>`.
11. `dotnetSandbox.ts` — chạy `dotnet restore && dotnet build && dotnet test`, capture stdout/stderr, parse thành JSON kết quả (build_status, build_errors, tests[]).
12. Emit `build_result` / `test_result` event → Validation Dashboard cập nhật real-time.

### Giai đoạn E — Vòng lặp Retry + QA Review
13. Implement state machine mục 3 (retry_count, MAX_RETRY, error_context truyền ngược lại conversionWorker).
14. `qaReviewWorker.ts` — phân loại lỗi (compile/logic/edge_case), sinh behavioral diff report, emit `diff_report`.
15. Confidence score (mục 3.1), escalation flow (mục 3.2) khi vượt MAX_RETRY.

### Giai đoạn F — Dashboard & Deliverables
16. `ValidationDashboard` — bảng module × status × retry × confidence, panel chi tiết khi click escalated module.
17. Tổng hợp Summary Report cuối pipeline: modules processed, success rate, danh sách escalated + lý do — export được ra file (Markdown/JSON) để làm "Evaluation sheet" theo yêu cầu deliverables của đề bài gốc.
18. README.md tự sinh: setup instructions, kiến trúc, cách chạy demo trên sample data.

---

## 9. Rủi ro & lưu ý kỹ thuật đặc thù COBOL/VB (bonus criteria từ đề bài gốc)

- **COMP-3 (packed decimal), REDEFINES, 88-level condition** — đây là các construct COBOL dễ bị dịch sai sang kiểu .NET tương ứng nếu chỉ dựa vào LLM thuần suy đoán; `copybookParser` nên trích xuất chính xác kiểu/size/precision bằng parser xác định (deterministic), LLM chỉ dùng để sinh code từ thông tin đã trích xuất chính xác đó, không tự đoán.
- **EBCDIC vs UTF-8** — nếu COBOL gốc xử lý dữ liệu EBCDIC, `test_gen_worker` cần sinh test case riêng cho encoding, không chỉ test logic thuần.
- **Numeric precision / date formats / null handling** — đây là nhóm lỗi phổ biến nhất khi convert VB→.NET; nên có 1 checklist cứng trong prompt của `test_gen_worker` để luôn sinh ít nhất 1 test case cho mỗi nhóm này per module, không phụ thuộc hoàn toàn vào LLM tự nhận ra.
- **Không gửi code khách hàng thật ra API công khai** — nếu môi trường thật có dữ liệu nhạy cảm, cần cấu hình dùng model tự host/VPC riêng thay vì Anthropic API công khai (đúng lưu ý "Not Allowed" trong đề bài gốc).
- **Giới hạn retry (MAX_RETRY)** — bắt buộc, tránh vòng lặp vô hạn đốt token khi 1 module quá phức tạp; escalate sớm cho người thay vì cố "ép" LLM sửa mãi.

---

## 10. Deliverables (theo yêu cầu đề bài gốc)

- [ ] Source code trên Git repo nội bộ.
- [ ] `README.md` tự sinh cuối pipeline — setup, kiến trúc, cách chạy trên sample data.
- [ ] Demo video ≤ 5 phút (dự phòng nếu live demo lỗi).
- [ ] Evaluation sheet — chạy agent trên sample data, ghi lại kết quả (xuất trực tiếp từ Validation Dashboard, mục 8.17).
- [ ] Khai báo rõ phần nào dùng pre-built component có sẵn (nếu có), theo đúng "Technical Rules — Allowed" của đề bài gốc.

Hoàn toàn ĐƯỢC và thậm chí là RẤT HỢP LÝ, đặc biệt khi dự án của bạn làm về AI Agents!

Mặc dù bạn làm Frontend (thường quen với JS/TS hơn), nhưng nếu chọn Python để làm "lẹ lẹ", bạn có thể dùng FastAPI.

Dưới đây là ưu/nhược điểm nếu bạn đổi sang xài Python (cụ thể là FastAPI) cho hệ thống này:

👍 Ưu điểm (Tại sao Python rất ngon cho dự án này):
Hệ sinh thái AI "Bá đạo": Python là "vua" trong mảng AI. Các thư viện như Anthropic SDK, OpenAI, hay các framework làm Agent (như LangChain, LangGraph) đều hỗ trợ Python tốt nhất và tài liệu xịn nhất.
FastAPI code siêu nhanh và sạch: FastAPI sử dụng type hints (gần giống như cách bạn dùng TypeScript), tự động sinh ra file tài liệu API (Swagger UI), code cực kỳ ngắn gọn và dễ hiểu.
Pydantic (Quản lý Schema cực mạnh): Trong readme.md, bạn có yêu cầu trả về các output_schema JSON chuẩn xác. Python có thư viện Pydantic chuyên dùng để parse và validate dữ liệu JSON, kết hợp với AI trả về structured output cực kỳ mượt.
Hỗ trợ Streaming tốt: FastAPI là framework xử lý bất đồng bộ (Async) hiện đại, việc setup Server-Sent Events (SSE) để stream log/thinking của AI về cho Frontend cũng rất dễ dàng thông qua các thư viện như sse-starlette.
👎 Nhược điểm nhỏ (Với Frontend dev):
Chuyển đổi ngữ cảnh (Context Switch): Bạn sẽ phải gõ TypeScript ở Frontend và gõ Python ở Backend, đôi khi hơi nhầm lẫn cú pháp.
Quản lý môi trường: Cài đặt package bằng pip và quản lý môi trường ảo (venv hoặc conda) sẽ hơi khác biệt một chút so với quen thuộc của npm/yarn.
Tóm lại:
Nếu bạn muốn làm cực lẹ mà không phải học thêm ngôn ngữ, hãy giữ Node.js (Express).

Nhưng nếu bạn muốn tận dụng sức mạnh hỗ trợ AI tốt nhất, validate JSON dễ nhất và code API cực nhanh, hãy chọn Python + FastAPI. Đây cũng là combo phổ biến nhất hiện nay cho các hệ thống Generative AI.

Nếu bạn chốt Python, cấu trúc thư mục backend của bạn (bằng FastAPI) trông sẽ rất gọn như thế này:

python
backend/
├── main.py              # File chạy server FastAPI (nhận requests, stream SSE)
├── agents/              # Chứa logic 5 con worker (orchestrator, discovery, conversion...)
├── parsers/             # Code parse COBOL/VB
└── sandbox/             # Chạy các lệnh dotnet
9:44 AM
tech backend python còn FE thì nên gì
9:45 AM
Nếu Backend đã chốt Python (FastAPI), thì Frontend vẫn nên giữ nguyên Tech Stack như trong bản thiết kế readme.md của bạn (Phần 6). Đây là combo nhanh, nhẹ và mạnh nhất hiện nay để build một giao diện dạng IDE đa luồng.

Cụ thể, bạn nên chốt combo này cho Frontend:

1. Framework cốt lõi: React + Vite + TypeScript
Vite: Khởi tạo project chỉ trong 1 giây, hot-reload tức thời. Chạy lẹ hơn Create React App hay Next.js rất nhiều nếu bạn chỉ cần build một app Single Page Application (SPA).
React: Hệ sinh thái đồ sộ nhất. Các thư viện làm editor, resizable layout đều tối ưu cho React.
2. Styling: Tailwind CSS
Cực kỳ lẹ cho FE dev. Bạn không cần phải suy nghĩ đặt tên class CSS hay nhảy qua nhảy lại giữa các file. Gõ thẳng class vào component, làm giao diện Dark Mode cho IDE cũng rất dễ.
3. State Management (Quản lý trạng thái): Zustand
Tại sao không phải Redux? Redux quá cồng kềnh và setup lâu.
Zustand siêu nhẹ, không cần boilerplate code, rất dễ để quản lý các state chạy liên tục như: luồng chat của AI (SSE stream), trạng thái của 5 con Worker, và nội dung file đang mở.
4. Các thư viện "Vũ khí hạng nặng" cho IDE:
Để build giao diện giống VS Code 2 khung (Workspace + Agent Chat) như yêu cầu của bài toán, bạn "ốp" ngay 2 thư viện này vào là xong 80% phần khung:

@monaco-editor/react: Mang nguyên cái bộ gõ code (editor) của VS Code lên web. Hỗ trợ syntax highlight cho VB, COBOL, C# sẵn luôn.
react-resizable-panels: Thư viện xịn nhất hiện tại để làm UI kéo thả, co giãn các khung (pane) bên trái và bên phải y hệt như VS Code.
Tổng kết kiến trúc hoàn hảo và "lẹ nhất" cho dự án của bạn:
Backend: Python + FastAPI (Nhanh, hỗ trợ AI/LLM cực mạnh, parse JSON schema siêu chuẩn với Pydantic).
Frontend: React + Vite + Tailwind + Zustand + Monaco Editor (Build UI kéo thả nhanh, mượt, hệ sinh thái IDE ngon nhất).
Hai bên (Frontend - Backend) sẽ giao tiếp với nhau qua chuẩn REST API và Server-Sent Events (SSE) để stream text AI.