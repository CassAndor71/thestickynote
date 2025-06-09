import streamlit as st
from pgs.company_page import load_executive_data, create_org_chart

def show_executive_detail():
    st.subheader("Executive Team")
    ticker = st.session_state['selected_company']
    executives = load_executive_data(ticker)
    if executives:
        selected_exec = st.session_state.get('selected_exec', list(executives.keys())[0])
        # Add executive dropdown
        new_selected_exec = st.selectbox(
            "Select Executive to View Reporting Structure",
            options=list(executives.keys()),
            index=list(executives.keys()).index(selected_exec),
            format_func=lambda x: f"{x} - {executives[x]['title']}"
        )
        if new_selected_exec != selected_exec:
            st.session_state['selected_exec'] = new_selected_exec
            st.rerun()
        selected_exec = st.session_state['selected_exec']
        # Create and display org chart
        org_chart = create_org_chart(executives, selected_exec)
        selected_points = st.plotly_chart(org_chart, use_container_width=True)
        # Handle click events
        if selected_points:
            try:
                clicked_data = selected_points.get("points", [])
                if clicked_data and len(clicked_data) > 0:
                    clicked_node = clicked_data[0].get("customdata")
                    if clicked_node and clicked_node != st.session_state['selected_exec']:
                        st.session_state['selected_exec'] = clicked_node
                        st.rerun()
            except:
                pass
        # Add explanation
        st.caption("💡 The selected executive is highlighted in blue. Their manager (if any) is shown above, and direct reports are shown below. Click on any node to view their information.")
    else:
        st.info("Executive information not available")
    if st.button("Back to Company Page"):
        st.session_state['page'] = 'company'
        st.rerun() 