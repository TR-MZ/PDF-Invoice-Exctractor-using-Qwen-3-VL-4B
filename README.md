# 🧾 Receipt Info Extractor

Extract dates and amounts from receipts using **Qwen3-VL** vision model — 100% locally, no cloud APIs.

## ✨ Features

- **🔒 100% Private** — All processing happens on your local GPU. No data ever leaves your machine.
- **📄 Batch Processing** — Upload multiple PDF receipts at once
- **📋 Copy to Clipboard** — One-click copy as rows or tables, ready to paste into Excel, Google Sheets, or any editor
- **🤖 Powered by Qwen3-VL-4B** — State-of-the-art vision-language model running locally

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- NVIDIA GPU with CUDA support
- ~8GB VRAM

### Installation

#### 1. System Dependencies (Linux)
The application requires `poppler` for PDF to Image conversion.
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

#### 2. Python Setup
```bash
# Clone and enter directory
cd PdfTotable

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Run the App
```bash
python app.py
```

Open http://localhost:8080 in your browser.

## 📖 Usage

1. **Upload** — Drag & drop your PDF receipts
2. **Extract** — AI automatically finds dates and amounts
3. **Copy** — Click to copy as row or table format
4. **Paste** — Paste directly into Excel, Sheets, or any spreadsheet

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| AI Model | Qwen3-VL-4B-Instruct |
| Backend | Flask + PyTorch |
| PDF Processing | pdf2image |
| Inference | Local GPU (CUDA) |

## 📝 License

MIT
