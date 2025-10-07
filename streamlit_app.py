import streamlit as st
import fitz  # PyMuPDF
import requests
import json
from typing import Optional
import time
import re
import os

from logs import logger

logger.setLevel("INFO")
from datamodels import ResponseItem

# API Configuration
API_URL = os.environ.get("API_URL")


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


def extract_questions(text: str) -> list[ResponseItem]:
    """
    Extracts numbered questions from text and returns them as ResponseItem objects.
    """
    pattern = r"\d+\.\s*(.+?\?)"
    matches = re.findall(pattern, text, flags=re.DOTALL)

    responses = []
    for i, q in enumerate(matches, start=1):
        cleaned_q = " ".join(q.split())  # normalize whitespace
        responses.append(ResponseItem(id=i, requirement=cleaned_q))
    return responses


def format_questions(questions: list[ResponseItem]) -> str:
    """Formats a list of ResponseItem questions into a readable string."""
    formatted = "\n\n".join([f"{q.id}. {q.requirement}" for q in questions])
    return formatted


def call_api(text_content: str) -> Optional[dict]:
    """Make POST request to the API with extracted text."""
    try:
        payload = {"text": text_content}
        headers = {"Content-Type": "application/json"}

        response = requests.post(f"{API_URL}/audit", json=payload, headers=headers)
        logger.debug(f"API response: {response.status_code} - {response.text}")
        response.raise_for_status()  # Raise an exception for bad status codes

        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {str(e)}")
        return None


def call_api_one(req: ResponseItem) -> Optional[dict]:
    try:
        payload = {
            "id": req.id,
            "requirement": req.requirement,
            "top_k": req.top_k,
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(f"{API_URL}/audit_one", json=payload, headers=headers)
        logger.debug(f"API response: {response.status_code} - {response.text}")
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

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    # ✅ Slider for top_k selection (placed before extract button)
    top_k = st.slider(
        "Select number of top policies to search (top_k)",
        min_value=1,
        max_value=10,
        value=3,
        help="Controls how many top policy matches to retrieve from the database for each question.",
    )

    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")

        if st.button("🚀 Extract Text and Process", type="primary"):
            with st.spinner("📖 Extracting text from PDF..."):
                text_content = extract_text_from_pdf(uploaded_file)
                questions = extract_questions(text_content)
                logger.info(f"Extracted {len(questions)} questions from PDF.")
                formatted_questions = format_questions(questions)

            if formatted_questions:
                st.subheader("📝 Extracted Questions")
                st.text_area(
                    "Extracted Questions",
                    formatted_questions,
                    height=200,
                    disabled=True,
                )

                st.subheader("🔗 API Processing")

                # Dynamic placeholders
                status_area = st.empty()
                question_area = st.empty()
                responses_area = st.empty()

                all_responses = []
                total = len(questions)
                status_area.info(f"⏳ Processing {total} questions with the API...")

                # Loop over each question progressively
                for i, question in enumerate(questions, start=1):
                    with st.spinner(f"Processing Question {i}/{total}..."):
                        # Assign user-selected top_k
                        question.top_k = top_k

                        # Show current question temporarily
                        question_area.markdown(
                            f"📡 **Sending Question {i}/{total}:** {question.requirement}"
                        )
                        response = call_api_one(question)

                        # Append and update progress
                        if response:
                            all_responses.append(response)
                            status_area.info(f"✅ Processed {i}/{total} questions")
                        else:
                            all_responses.append({"error": f"Failed at question {i}"})
                            status_area.warning(f"⚠️ Failed at Question {i}/{total}")

                        # Update responses progressively with expandable cards
                        responses_area.empty()  # clear the previous display
                        with responses_area.container():
                            st.subheader("📋 API Responses")
                            for i, res in enumerate(all_responses, start=1):
                                res = res.get("response")
                                if res:
                                    with st.expander(
                                        f"Question {i}: {res.get('requirement', '')[:100]}..."
                                    ):
                                        st.markdown(
                                            f"**📝 Requirement:** {res.get('requirement', '—')}"
                                        )
                                        st.markdown(
                                            f"**✅ Requirement Met:** {'Yes' if res.get('is_met') else 'No'}"
                                        )
                                        st.markdown(
                                            f"**📄 Citation:** {res.get('citation', '—')}"
                                        )
                                        if res.get("explanation"):
                                            st.markdown(
                                                f"**🧩 Explanation:** {res['explanation']}"
                                            )
                                        if res.get("file_name"):
                                            st.caption(f"📁 Source: {res['file_name']}")

                        # Clear the temporary question display
                        question_area.empty()

                status_area.success("🎉 All questions processed successfully!")

            else:
                st.error("❌ No text content could be extracted from the PDF.")
    else:
        st.info("👆 Please upload a PDF file to get started.")
        st.markdown(
            """
        ### How to use:
        1. **Upload PDF**  
        2. **Select your desired `top_k` value**  
        3. **Click Extract & Process**  
        4. **Watch responses appear one by one!**
        """
        )


if __name__ == "__main__":
    main()
