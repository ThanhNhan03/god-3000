# GOD-3000: Multi-Agent Legacy Migration Harness

**GOD-3000** là một hệ thống Multi-Agent IDE (Môi trường phát triển tích hợp dựa trên nhiều tác nhân AI) chuyên biệt, được thiết kế để tự động hoá quy trình chuyển đổi mã nguồn cũ (Legacy Code) sang các công nghệ hiện đại. Dự án tập trung giải quyết bài toán chuyển đổi hệ thống **VB6** (`.frm`, `.bas`, `.cls`) và **COBOL** (`.cbl`, `.cpy`) sang kiến trúc chuẩn **C# ASP.NET Core MVC** (.NET 8+).

Thay vì phụ thuộc vào một luồng AI đơn giản, GOD-3000 áp dụng cơ chế **Human-in-the-loop** kết hợp với một **Multi-Agent Pipeline** tinh vi. Hệ thống cho phép con người kiểm duyệt, phản hồi kế hoạch trước khi chạy, đồng thời các Agent nội bộ sẽ tự động kiểm tra chéo (QA) và sửa lỗi lẫn nhau cho đến khi đạt tiêu chuẩn đầu ra.

---

## 🌟 Tổng quan kiến trúc cốt lõi (Core Flow)

Quy trình hoạt động cốt lõi của GOD-3000 diễn ra theo chu trình tuần tự nhưng liên kết chặt chẽ:

1. **Ingest (Tiếp nhận dữ liệu)**: Người dùng tải lên mã nguồn (dưới dạng file lẻ hoặc file `.zip` chứa toàn bộ dự án). Hệ thống giải nén và đưa vào thư mục `/workspace/source/`.
2. **Discovery (Phân tích tĩnh)**: Khám phá mã nguồn, đánh giá độ phức tạp và gom nhóm các file liên quan thành các "Module" độc lập để chuyển đổi.
3. **Planning (Lập kế hoạch NLP)**: Từ yêu cầu của người dùng, AI lên kế hoạch chuyển đổi chi tiết và trình bày cho người dùng đánh giá (Verify/Refine).
4. **Conversion Pipeline (Chuyển đổi đa luồng)**: Từng module được đưa vào luồng dịch thuật. Code C# MVC được sinh ra và lưu vào `/workspace/new/`.
5. **QA Validation (Kiểm thử vòng lặp)**: Mã nguồn vừa sinh bị đưa vào máy quét QA. Nếu vi phạm quy chuẩn (sai namespace, sai chuẩn naming, lỗi cú pháp), QA từ chối (Fail) và ép luồng Conversion phải **Retry** để sửa lỗi dựa trên context lỗi.
6. **Reporting (Báo cáo)**: Sau khi hoàn thành hoặc đạt giới hạn retry, hệ thống chốt file C#, sinh file báo cáo HTML (Migration Report) và trả kết quả hiển thị lên giao diện IDE.

---

## 🤖 Hệ thống AI Agents (Multi-Agent Pipeline)

Hệ thống hoạt động nhờ sự phối hợp của 4 Agent chính, được quản lý bởi một Orchestrator.

### 1. Orchestrator (Người điều phối)
- **Nhiệm vụ**: Là "bộ não" trung tâm, tiếp nhận NLP prompt của người dùng, gọi tuần tự các Agent khác và quản lý vòng lặp Retry.
- **Tính năng nổi bật**:
  - Giao tiếp với LLM qua Server-Sent Events (SSE) để truyền trạng thái (Thinking, Generating) thời gian thực xuống giao diện.
  - Xử lý Human-in-the-loop: Tạm dừng tiến trình để chờ người dùng duyệt (Approve) hoặc phản hồi (Feedback) bản Kế hoạch triển khai.
  - Quản lý đồng thời các tác vụ để tránh đụng độ (Anti-Concurrency logic) trong trường hợp có nhiều request gửi đến.

### 2. Discovery Agent (Quét & Đánh giá)
- **Nhiệm vụ**: Đọc toàn bộ thư mục `workspace/source/` để lập hồ sơ dự án.
- **Tính năng nổi bật**:
  - Tự động gom nhóm các file `.frm` (Giao diện VB), `.bas` (Logic VB) và `.cbl` (Logic COBOL) thành các Module logic.
  - Chấm điểm **Complexity Score** dựa trên số lượng dòng code và độ phức tạp cấu trúc.
  - Đề xuất thứ tự chuyển đổi (Migration Order) hợp lý nhất.

### 3. Conversion Agent (Thợ dịch thuật)
- **Nhiệm vụ**: Nhận mã nguồn cũ của một Module và sinh ra bộ mã C# MVC tương ứng.
- **Tính năng nổi bật**:
  - Phân tích mã nguồn và sinh ra cấu trúc chuẩn: **Controllers**, **Models (DTO, ViewModels)**, và **Views (Razor .cshtml)**.
  - Trả về dữ liệu dưới định dạng chuỗi JSON Markdown (```json ... ```) để hệ thống tự động trích xuất thành nhiều file riêng biệt.
  - Tự động tiếp nhận **Error Context** từ QA Agent để sửa lại chính lỗi của mình ở những lần Retry tiếp theo.

### 4. QA Validator (Người kiểm duyệt nghiêm ngặt)
- **Nhiệm vụ**: Đảm bảo toàn bộ mã C# được sinh ra tuân thủ tuyệt đối các chuẩn mực coding guidelines của dự án.
- **Các quy tắc kiểm thử cứng (Strict Rules)**:
  - Bắt buộc phải khai báo `using [Namespace].Models;` trong các file Controller/Service.
  - Chuẩn hoá **camelCase** toàn diện: Mọi thuộc tính (property) và tên class bên trong Models bắt buộc phải dùng `camelCase` (ví dụ: `customerId` thay vì `CustomerID` hay `customer_id`).
  - Kiểm tra dấu ngoặc nhọn `{ }` để đảm bảo không bị lỗi cú pháp chưa đóng ngoặc.
  - Nếu bất kỳ file nào vi phạm, QA trả về danh sách lỗi cụ thể, kích hoạt vòng lặp Retry cho đến khi đạt (hoặc chạm ngưỡng Max Retries).

---

## 🎨 Giao diện IDE (Frontend Core Features)

Không chỉ là một CLI tool, GOD-3000 mang đến trải nghiệm phát triển tích hợp (IDE) ngay trên trình duyệt:

- **Layout 2-Pane**: Lấy cảm hứng từ VS Code với khu vực File Explorer bên trái và Editor bên phải.
- **Monaco Editor**: Cung cấp trình soạn thảo code mạnh mẽ với Syntax Highlighting, cho phép đọc source code cũ và chỉnh sửa code mới sinh ra ngay lập tức.
- **Agent Chat & Streaming**: Khung chat bên phải hiển thị "suy nghĩ" (Thinking Output) của các Agent theo thời gian thực (ví dụ: *🔍 Phân tích cấu trúc module VB6*, *⚙️ Tạo Controller*...).
- **Dynamic API Key Configuration**: Người dùng có thể điền và **Test** trực tiếp API Key (ShopAI / OpenAI tương thích) ngay trên giao diện mà không cần chỉnh sửa code hay khởi động lại Backend.
- **Implementation Plan Viewer**: Một màn hình pop-up đẹp mắt để Review kế hoạch trước khi Agent được phép chạm vào code.
- **Báo cáo HTML Tự sinh**: Click mở trực tiếp các báo cáo chi tiết về kết quả dịch thuật (Module nào thành công, bị lỗi ở đâu) với UI trực quan.

---

## 🔄 Luồng xử lý Migration & Cơ chế giải quyết vấn đề (Execution Flow)

Dự án không đơn thuần là gửi source code cũ lên LLM và mong chờ kết quả hoàn hảo. Quy trình được thiết kế bài bản để **tự động sửa sai** như sau:

### 1. Tiền xử lý & Lên kế hoạch (Pre-processing & Planning)
- Khi người dùng gửi lệnh, **Discovery Agent** sẽ nhóm các file VB/COBOL có liên quan với nhau thành một module (để có đầy đủ ngữ cảnh giao diện lẫn logic).
- Lên một bản **Implementation Plan** và trình bày qua UI. Chỉ khi con người bấm **Verify & Execute**, quá trình convert mới bắt đầu. 

### 2. Dịch thuật & Định dạng (Conversion & Formatting)
- Code cũ được nén vào Prompt cùng với các hướng dẫn khắt khe về cấu trúc C# MVC (Yêu cầu tách Controller, Models, Views).
- Thay vì trả về text lộn xộn, hệ thống ép LLM phải trả về định dạng **JSON Array** bên trong Markdown block (Ví dụ: `[{"filename": "...", "code": "..."}]`).
- Backend sẽ sử dụng regex để parse block JSON này, trích xuất ra code thô.

### 3. Đối mặt vấn đề & Cách giải quyết (The QA & Retry Mechanism)
Trong quá trình LLM sinh code, thường xuyên xảy ra các **vấn đề nhức nhối (Hallucinations/Lỗi vặt)** như:
- Quên khai báo thư viện (`using ...Models;`).
- Đặt tên biến/class sai chuẩn hệ thống (dùng `PascalCase` hoặc `snake_case` thay vì `camelCase` được yêu cầu).
- Syntax bị lủng (thiếu dấu ngoặc nhọn `{ }`).

**Cách GOD-3000 giải quyết:**
- Mọi file code được sinh ra không được lưu thẳng vào ổ cứng mà phải đi qua **QA Validator**.
- QA dùng Regex và bộ rules cứng để quét. Nếu phát hiện lỗi:
  1. QA **chặn** không cho lưu code.
  2. Tạo ra một **Error Context** cực kỳ rõ ràng (VD: *"Thuộc tính User_ID sai chuẩn, phải dùng userId"*).
  3. **Auto-Retry**: Hệ thống mang nguyên Error Context này gửi ngược lại cho LLM (cùng lịch sử chat cũ) với yêu cầu "Bạn làm sai rồi, hãy sửa lại đoạn này".
  4. Quá trình này lặp lại hoàn toàn tự động (lên đến `MAX_QA_RETRIES` lần) cho đến khi LLM "bị ép" phải sinh ra code chuẩn xác 100% với QA.

### 4. Kết xuất (Output & Report)
- Khi một module pass toàn bộ bài test QA, mã nguồn mới chính thức được ghi ra đĩa cứng tại `workspace/new/`.
- Một báo cáo HTML được sinh ra ghi nhận lại toàn bộ: Hệ thống đã tốn bao nhiêu lần retry để sửa lỗi cho module này, kết quả các file là gì.

---

## ⚙️ Công nghệ sử dụng (Tech Stack)

### Backend (Python)
- **FastAPI**: Xây dựng các REST APIs và Streaming Endpoints (SSE) với hiệu suất cao và hỗ trợ Async toàn diện.
- **AsyncOpenAI**: Thư viện kết nối với LLM. Dễ dàng đổi Base URL để tương thích với các mô hình OpenAI-like (ShopAI).
- **Pydantic**: Validate dữ liệu vào/ra chuẩn xác.
- **Python `asyncio`**: Quản lý các task ngầm (Background Tasks), huỷ (cancel) các pipeline trùng lặp một cách mượt mà.

### Frontend (React)
- **React.js + Vite**: Hệ thống Component và môi trường build cực nhanh.
- **Tailwind CSS**: Dựng UI dạng IDE chuyên nghiệp (Dark theme, Glassmorphism, Animations) mà không cần viết quá nhiều file CSS.
- **Zustand**: Quản lý State nhẹ nhàng, cực kỳ hiệu quả để lưu trữ trạng thái Streaming của Agent.
- **@monaco-editor/react**: Trình soạn thảo code tích hợp.
- **Lucide-react**: Thư viện Icon hiện đại.

---

## 📂 Cấu trúc dự án (Folder Structure)

```text
god-3000/
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py    # Điều phối tổng thể các Agent, Retry loop, Streaming logic
│   │   ├── discovery.py       # Quét & tính toán Complexity Score
│   │   ├── conversion.py      # Module phụ tạo Prompt chuyển đổi
│   │   ├── qa.py              # Strict QA Rules (camelCase, using Models, syntax checks...)
│   │   └── report.py          # Sinh mã HTML cho báo cáo Migration
│   ├── routes/
│   │   ├── stream.py          # API SSE Streaming & API Test Key
│   │   ├── ingest.py          # Xử lý File/ZIP upload và giải nén
│   │   └── workspace.py       # API thao tác thư mục ảo (Đọc/Ghi/Tạo/Xoá)
│   ├── llm_client.py          # Cấu hình gọi LLM, lưu trữ và đổi API Key động
│   ├── main.py                # Điểm khởi chạy FastAPI Server, cấu hình CORS
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Layout IDE chính (Monaco, File Tree, Chat, Plan View)
│   │   ├── index.css          # Global CSS & Animations
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── workspace/                 # Nơi lưu trữ mã nguồn thao tác của IDE
    ├── source/                # File Legacy Code người dùng upload
    └── new/                   # File C# MVC và Reports sinh ra sau khi chạy
```

---

## 🚀 Hướng dẫn cài đặt và sử dụng

### 1. Yêu cầu hệ thống
- **Node.js** (Phiên bản >= 18)
- **Python** (Phiên bản >= 3.10)

### 2. Cài đặt Dependencies

**Backend**:
```bash
cd backend
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

### 3. Chạy hệ thống

Bạn cần 2 Terminal để chạy song song:

**Terminal 1 (Backend - FastAPI)**:
```bash
cd backend
python main.py
# (FastAPI sẽ chạy trên cổng http://localhost:8000)
```

**Terminal 2 (Frontend - React/Vite)**:
```bash
cd frontend
npm run dev
# (Truy cập IDE tại http://localhost:5173)
```

### 4. Quy trình sử dụng (Luồng cơ bản)
1. Truy cập vào `http://localhost:5173`.
2. Ở khung Agent Chat bên phải, nhập **API Key** của bạn (chuẩn OpenAI/ShopAI) vào ô input trên cùng. Bấm **Test** (nếu chuyển xanh OK là kết nối thành công).
3. Bấm vào nút **Upload file / zip** để tải mã nguồn cũ lên (ví dụ một file `.frm` hoặc `.cbl`). Source sẽ hiện bên File Explorer bên trái.
4. Gõ prompt yêu cầu vào thanh Chat (ví dụ: `Migrate cho tôi toàn bộ code này sang C# MVC chuẩn`).
5. Agent sẽ chạy và hiện popup **Implementation Plan**.
6. Đọc kỹ Plan. Nếu đồng ý, bấm **Verify & Execute**.
7. Ngồi xem quá trình **Agent Thinking** (Streaming UI). Hệ thống sẽ tự động convert, tự động QA Validation, và tự động Retry nếu có lỗi.
8. Khi báo `Done!`, bấm vào thư mục `workspace/new/` bên trái để xem source code mới, hoặc click trực tiếp vào file **Report** được ghim trong khung chat.

---

> **Lưu ý quan trọng**: Dự án sử dụng mô hình AI LLM, vui lòng đảm bảo Base URL và cấu hình Model trong `backend/llm_client.py` trỏ đúng vào Endpoint của mô hình bạn đang sở hữu. Giao diện IDE hiện tại tự quản lý trạng thái, do đó tránh double-click liên tục vào nút Gửi prompt để đảm bảo luồng SSE hoạt động trơn tru.