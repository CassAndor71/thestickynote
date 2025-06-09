import streamlit as st
from pgs.home_page import show_home_page
from pgs.company_page import show_company_page
from pgs.executive_detail import show_executive_detail
import json
st.set_page_config(layout="wide")

def load_sp500_companies():
    """Load S&P 500 companies from the JSON file."""
    with open('sp500_companies.json', 'r') as file:
        companies = json.load(file)
    return companies

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["app"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    # Initialize page in session state if not present
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'
    
    # Show appropriate page based on session state
    if st.session_state['page'] == 'home':
        show_home_page()
    elif st.session_state['page'] == 'executive_detail':
        show_executive_detail()
    else:
        show_company_page()

