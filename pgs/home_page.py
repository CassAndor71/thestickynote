import streamlit as st
import json

def load_sp500_companies():
    """Load S&P 500 companies from the JSON file."""
    with open('sp500_companies.json', 'r') as file:
        companies = json.load(file)
    return companies

def show_home_page():
    st.title("📝 The Sticky Note")
    st.caption("For the people, by the people.")
    
    # Load and display company selection
    companies = load_sp500_companies()
    # Create a list of tuples (ticker, name) for the selectbox
    company_options = [(ticker, f"{ticker} - {name}") for ticker, name in companies.items()]
    company_options.sort(key=lambda x: x[1])  # Sort by the display string
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        selected_company = st.selectbox(
            "Select your company",
            options=[opt[0] for opt in company_options],
            format_func=lambda x: next(opt[1] for opt in company_options if opt[0] == x),
            index=None,
            placeholder="Choose a company..."
        )

    with col2:
        role = st.selectbox(
            "Select your role",
            options=["Contributor", "Viewer"],
            index=None,
            placeholder="Choose your role..."
        )

    if selected_company and role:
        verb = "Join" if role == "Contributor" else "View"
        if st.button(f"{verb} the revolution"):
            # Store the selected company and role in session state
            st.session_state['selected_company'] = selected_company
            st.session_state['company_name'] = companies[selected_company]
            st.session_state['role'] = role
            st.session_state['page'] = 'company_page'
            st.rerun() 