import streamlit as st
import pdfplumber
import pandas as pd
import json
import os
from pydantic import BaseModel, Field
from typing import List

# --- AI LIBRARIES ---
try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    import anthropic
except ImportError:
    anthropic = None
try:
    from groq import Groq
except ImportError:
    Groq = None

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="AI Invoice Auditor",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DEFINE STRUCTURED OUTPUT SCHEMA ---
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

class RiskAssessment(BaseModel):
    is_math_correct: bool = Field(description="True if sum of line items equals subtotal/total")
    flagged_issues: List[str] = Field(description="List of suspicious items, math errors, or missing dates")
    fraud_score: int = Field(description="0-100 score where 100 is likely fraud")

class InvoiceExtraction(BaseModel):
    vendor_name: str
    invoice_date: str
    invoice_number: str
    line_items: List[LineItem]
    subtotal: float
    tax_amount: float
    grand_total: float
    currency: str = Field(description="Currency code like USD, EUR")
    risk_assessment: RiskAssessment

# --- 3. CORE LOGIC (Multi-Provider) ---
def extract_text_from_pdf(uploaded_file):
    """Extracts raw text from the uploaded PDF file."""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def analyze_invoice(provider, api_key, text_content):
    """Sends text to selected AI provider and retrieves structured JSON."""
    
    # Universal System Prompt
    system_instruction = """
    You are an expert forensic accountant AI. 
    1. Extract invoice data from the text provided. 
    2. Strictly validate the math (Quantity * Unit Price = Total). 
    3. Flag any discrepancies, missing details, or suspicious formatting in the 'risk_assessment'.
    4. Calculate a 'fraud_score' (0-100).
    
    Return pure JSON strictly matching this schema:
    {
        "vendor_name": "...",
        "invoice_date": "YYYY-MM-DD",
        "invoice_number": "...",
        "line_items": [{"description": "...", "quantity": 0.0, "unit_price": 0.0, "total": 0.0}],
        "subtotal": 0.0,
        "tax_amount": 0.0,
        "grand_total": 0.0,
        "currency": "USD",
        "risk_assessment": {
            "is_math_correct": true,
            "flagged_issues": ["..."],
            "fraud_score": 0
        }
    }
    """

    try:
        # 1. GOOGLE GEMINI
        if provider == "Google Gemini":
            if not genai: st.error("Library `google-generativeai` not installed."); return None
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
            response = model.generate_content(f"{system_instruction}\n\nINVOICE TEXT:\n{text_content}")
            return InvoiceExtraction(**json.loads(response.text))

        # 2. OPENAI
        elif provider == "OpenAI":
            if not OpenAI: st.error("Library `openai` not installed."); return None
            client = OpenAI(api_key=api_key)
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": text_content}
                ],
                response_format=InvoiceExtraction
            )
            return completion.choices[0].message.parsed

        # 3. ANTHROPIC (Claude)
        elif provider == "Anthropic (Claude)":
            if not anthropic: st.error("Library `anthropic` not installed."); return None
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4096,
                system=system_instruction,
                messages=[{"role": "user", "content": text_content}]
            )
            return InvoiceExtraction(**json.loads(message.content[0].text))

        # 4. GROQ (Llama 3)
        elif provider == "Groq (Llama 3)":
            if not Groq: st.error("Library `groq` not installed."); return None
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": system_instruction + " RETURN ONLY JSON."},
                    {"role": "user", "content": text_content}
                ],
                response_format={"type": "json_object"}
            )
            return InvoiceExtraction(**json.loads(completion.choices[0].message.content))

    except Exception as e:
        st.error(f"Analysis Failed: {e}")
        return None

# --- 4. FRONTEND UI ---

# Sidebar for Setup
with st.sidebar:
    st.title("🕵️‍♂️ Invoice Auditor")
    st.caption("Forensic AI Analysis")
    st.divider()
    
    provider = st.radio("Select AI Model", ["OpenAI", "Google Gemini", "Anthropic (Claude)", "Groq (Llama 3)"])
    api_key = st.text_input(f"Enter {provider} API Key", type="password")

    st.info("💡 **How it works:**\n1. Upload a PDF Invoice.\n2. AI extracts data & checks math.\n3. Risk Score identifies fraud.")
    st.markdown("---")
    st.caption("Built by **Kwami Occansey**")

# Main Content
st.title("📄 Intelligent Invoice Extraction & Audit")
st.markdown(f"Transform unstructured PDF invoices into structured data with **automated risk detection** using **{provider}**.")

uploaded_file = st.file_uploader("Upload Invoice (PDF)", type=["pdf"])

if uploaded_file:
    # 1. Preview (Split View)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Document Preview")
        st.success(f"Filename: {uploaded_file.name}")
        
        # Extract Text
        with st.spinner("Reading PDF..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            
        with st.expander("View Raw Text Content"):
            st.text_area("Raw Text", raw_text, height=300)

    # 2. Analysis Action
    with col2:
        st.subheader("2. AI Analysis")
        
        if st.button("🚀 Analyze & Audit Document", type="primary"):
            if not api_key:
                st.warning(f"Please provide your {provider} API Key in the sidebar.")
            elif not raw_text:
                st.error("Could not read text from PDF. It might be a scanned image (OCR not supported in this demo).")
            else:
                with st.spinner(f"🤖 {provider} is analyzing logic, math, and entities..."):
                    result = analyze_invoice(provider, api_key, raw_text)
                    
                if result:
                    # --- DISPLAY RESULTS ---
                    
                    # A. Risk Score Card
                    score = result.risk_assessment.fraud_score
                    color = "#43a047" if score < 20 else "#fb8c00" if score < 60 else "#e53935"
                    
                    st.markdown(f"""
                    <div style="padding: 20px; border-radius: 10px; border: 2px solid {color}; background-color: rgba(0,0,0,0.05);">
                        <h3 style="margin:0; color:{color};">Risk Score: {score}/100</h3>
                        <p style="margin-top:5px;"><b>Math Check:</b> {"✅ Correct" if result.risk_assessment.is_math_correct else "❌ Math Error Detected"}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    if result.risk_assessment.flagged_issues:
                        st.warning("🚩 **Flagged Issues:**")
                        for issue in result.risk_assessment.flagged_issues:
                            st.write(f"- {issue}")
                    else:
                        st.success("✅ No obvious irregularities detected.")

                    # B. Header Data
                    st.divider()
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Vendor", result.vendor_name)
                    m2.metric("Date", result.invoice_date)
                    m3.metric("Total", f"{result.currency} {result.grand_total:,.2f}")

                    # C. Line Items Table
                    st.divider()
                    st.subheader("Line Items")
                    
                    # Convert Pydantic list to Pandas DataFrame
                    if result.line_items:
                        items_data = [item.model_dump() for item in result.line_items]
                        df = pd.DataFrame(items_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.write("No line items found.")

                    # D. JSON Export
                    st.divider()
                    with st.expander("🔌 Developer Mode (JSON Output)"):
                        st.json(result.model_dump_json())
else:
    # Empty State
    st.info("👆 Upload a PDF to begin the audit.")