import os
import tempfile
import streamlit as st
import fitz  # PyMuPDF for PDFs
import together
from fpdf import FPDF
from dotenv import load_dotenv
from unidecode import unidecode


# Load API key
load_dotenv()
together_api_key = os.getenv("TOGETHER_API_KEY")
os.environ["TOGETHER_API_KEY"] = together_api_key

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text

def summarize_with_llama(text):
    prompt = f"""
    Summarize the following study notes **strictly** based on the provided material.  

    ### **Guidelines:**
    1. **Do not** add any external examples, explanations, or interpretations beyond what is explicitly stated in the text.  
    2. **Ensure the summary contains only essential details** while preserving the original meaning and structure.  
    3. **Do not introduce new concepts, paraphrase inaccurately, or infer missing information.**    
    4. If the tokens to be used exceed the max tokens povided, which is 5000, you are allowed to summarize it even further
    \n{text}"""


    response = together.Completion.create(
        model="mistralai/Mistral-7B-Instruct-v0.1",  # Use a serverless model
        prompt=prompt,
        max_tokens=5000,
        temperature=0.7
    )
    return response.choices[0].text.strip()  # Correct way to access the output

def clean_text(text):
    return unidecode(text)  # Converts fancy quotes, bullets, etc. into ASCII equivalents

def generate_pdf(summary_text):
    summary_text = clean_text(summary_text)  # Ensure ASCII-only text

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, summary_text)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name, "F")

    return temp_file.name
# Streamlit UI
st.title("Study Note Summarizer")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.read())
        pdf_path = temp_pdf.name
    
    extracted_text = extract_text_from_pdf(pdf_path)
    st.text_area("Extracted Text", extracted_text, height=200)
    
    if st.button("Summarize Notes"):
        summary = summarize_with_llama(extracted_text)
        st.text_area("Summarized Notes", summary, height=200)
        
        summary_pdf_path = generate_pdf(summary)
        with open(summary_pdf_path, "rb") as file:
            st.download_button("Download Summary PDF", file, file_name="summary.pdf", mime="application/pdf")
