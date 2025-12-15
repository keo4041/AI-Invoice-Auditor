# 🕵️‍♂️ AI Invoice Auditor

**AI Invoice Auditor** is a forensic accounting tool that uses Large Language Models (LLMs) to extract structured data from PDF invoices and automatically detect fraud or errors.

---

## 🚀 Features

* **Multi-Model Support:** Plug-and-play with OpenAI, Google Gemini, Anthropic (Claude), or Groq (Llama 3).
* **Math Validation:** Automatically recalculates line items (`Qty * Price = Total`) to ensure the invoice adds up.
* **Risk Scoring:** Assigns a 0-100 "Fraud Score" based on missing details, math errors, or suspicious vendor names.
* **Structured Data Extraction:** Converts PDF text into clean JSON and Tables (Vendor, Date, Line Items).

---

## ⚙️ Setup

1.  **Clone Repo:**
    ```bash
    git clone [https://github.com/your-username/invoice-auditor.git](https://github.com/your-username/invoice-auditor.git)
    cd invoice-auditor
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run App:**
    ```bash
    streamlit run app.py
    ```

---

## 📖 Usage

1.  Select your **AI Provider** in the sidebar.
2.  Enter your **API Key**.
3.  Upload a **PDF Invoice**.
4.  Click **"Analyze & Audit Document"**.
5.  Review the **Risk Score**, **Flagged Issues**, and extracted **Line Items**.

**Note:** This tool uses `pdfplumber` for text extraction. It works best on digital-native PDFs. Scanned images may require an OCR library (like Tesseract) which is not included in this lightweight demo.