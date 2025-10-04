import streamlit as st
import fitz  # PyMuPDF
import requests
import json
from typing import Optional
import time

# API Configuration
API_URL = "https://readily-494772444195.europe-west1.run.app/audit"


def extract_text_from_pdf(pdf_file) -> str:
    """Extract text content from uploaded PDF file."""
    try:
        # Read the PDF file
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")

        text_content = ""
        # Extract text from each page
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text_content += page.get_text()

        pdf_document.close()
        return text_content.strip()

    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""


def call_api(text_content: str) -> Optional[dict]:
    """Make POST request to the API with extracted text."""
    try:
        payload = {"text": text_content}
        headers = {"Content-Type": "application/json"}

        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {str(e)}")
        return None


def main():
    st.set_page_config(page_title="PDF Text Extractor", page_icon="📄", layout="wide")

    st.title("📄 PDF Text Extractor & API Processor")
    st.markdown(
        "Upload a PDF file to extract text and send it to the API for processing."
    )

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Select a PDF file to extract text content",
    )

    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        # Extract text button
        if st.button("🚀 Extract Text and Process", type="primary"):
            with st.spinner("📖 Extracting text from PDF..."):
                text_content = extract_text_from_pdf(uploaded_file)

            if text_content:
                st.subheader("📝 Extracted Text")
                st.text_area(
                    "Extracted Content", text_content, height=200, disabled=True
                )

                # API call section
                st.subheader("🔗 API Processing")

                # Show running status
                with st.status("⏳ Processing with API...", expanded=True) as status:
                    st.write("📡 Sending request to API...")
                    time.sleep(0.5)  # Brief pause for UX

                    st.write("🔄 Waiting for response...")
                    response = call_api(text_content)

                    if response:
                        status.update(
                            label="✅ API Response Received",
                            state="complete",
                            expanded=True,
                        )

                        # Display response
                        st.subheader("📤 API Response")
                        st.json(response)
                    else:
                        status.update(
                            label="❌ API Request Failed", state="error", expanded=True
                        )
            else:
                st.error("❌ No text content could be extracted from the PDF.")
    else:
        st.info("👆 Please upload a PDF file to get started.")

        # Instructions
        st.markdown(
            """
        ### How to use:
        1. **Upload PDF**: Click the file uploader above and select a PDF file
        2. **Extract & Process**: Click the "Extract Text and Process" button
        3. **View Results**: See the extracted text and API response below

        The app will show the progress and final results in real-time.
        """
        )


if __name__ == "__main__":
    main()
