import streamlit as st
import plotly.express as px
from PDFtoSQL import *

st.set_page_config(page_title="Finace", page_icon="💰", layout="wide")

def load_transactions(uploaded_file):
    PDFtoSQL.main(uploaded_file)

def main():
    st.title("Test 1")

    uploaded_file = st.file_uploader("Upload your transaction PDF file",type=["pdf", "csv"])

    if uploaded_file is not None:
        df = load_transactions(uploaded_file)

main()