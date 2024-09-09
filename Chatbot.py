import streamlit as st
from transformers import pipeline

qa_model = pipeline("question-answering", model="deepset/xlm-roberta-large-squad2")

# Streamlit app
st.title("Multilingual Question Answering App")

# Upload text file
uploaded_file = st.file_uploader("Upload a text file", type=["txt"])
if uploaded_file is not None:
    # Read the file
    text = uploaded_file.read().decode("utf-8")
    st.write("Text content:")
    st.write(text)

    # Input question
    question = st.text_input("Ask a question based on the text:")

    # Generate answer when the user submits a question
    if st.button("Get Answer"):
        if question and text:
            result = qa_model(question=question, context=text)
            st.write(f"Answer: {result['answer']}")
        else:
            st.write("Please upload a file and enter a question.")