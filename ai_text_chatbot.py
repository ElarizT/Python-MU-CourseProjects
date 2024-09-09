import streamlit as st
import spacy
from transformers import pipeline

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# Basic preprocessing: lowercasing, removing special characters
def preprocess_text(text):
    doc = nlp(text.lower())  # Tokenize and lowercase the text
    tokens = [token.text for token in doc if not token.is_punct]  # Remove punctuation
    return tokens

# Load pre-trained question-answering model
qa_model = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")

# Function to answer question
def answer_question(question, context):
    result = qa_model(question=question, context=context)
    return result['answer']

# Streamlit App Layout
st.title("Question Answering App")
st.write("Upload a text file, ask a question, and get an answer from the text!")

# File uploader
uploaded_file = st.file_uploader("Upload a text file", type=["txt"])

if uploaded_file is not None:
    # Read file
    data = uploaded_file.read().decode('utf-8')

    # Show the content of the file
    st.write("### File Content")
    st.write(data)

    # Preprocess the text data
    processed_data = preprocess_text(data)

    # Ask question
    question = st.text_input("Enter your question")

    if st.button("Get Answer"):
        if question:
            # Get the answer from the QA model
            answer = answer_question(question, data)
            st.write(f"**Answer:** {answer}")
        else:
            st.write("Please enter a question.")