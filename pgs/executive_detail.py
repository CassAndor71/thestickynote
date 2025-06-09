import streamlit as st
from pgs.company_page import load_executive_data, create_org_chart, format_large_number
import os
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
import html

def load_exec_reviews():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    file_path = os.path.join(data_dir, 'exec_reviews.json')
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_exec_reviews(reviews):
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    file_path = os.path.join(data_dir, 'exec_reviews.json')
    with open(file_path, 'w') as f:
        json.dump(reviews, f, indent=2)

def show_executive_detail():
    
    if st.button("<- Company Page"):
        st.session_state['page'] = 'company'
        st.rerun()

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
        # 1. Basic stats
        exec_info = executives[selected_exec]
        num_direct_reports = len(exec_info.get('direct_reports', []))
        salary = exec_info.get('salary', None)
        stock = exec_info.get('shares', None)
        # Get current stock price
        ticker = st.session_state.get('selected_company', 'DIS')
        try:
            stock_price = yf.Ticker(ticker).info.get('regularMarketPrice', None)
        except Exception:
            stock_price = None
        stock_value = stock * stock_price if (stock is not None and stock_price is not None) else None
        # Calculate total reports (all levels)
        def count_total_reports(exec_name, executives):
            direct = executives[exec_name].get('direct_reports', [])
            total = len(direct)
            for dr in direct:
                if dr in executives:
                    total += count_total_reports(dr, executives)
            return total
        total_reports = count_total_reports(selected_exec, executives)
        st.markdown("### Executive Profile")
        colA, colB, colC, colD, colE = st.columns(5)
        colA.metric("Direct Reports", num_direct_reports)
        colB.metric("Total Reports", total_reports)
        if salary is not None:
            colC.metric("Annual Salary", format_large_number(salary), help=f"${salary:,.0f}")
        if stock is not None:
            colD.metric("DIS Stock Owned", format_large_number(stock), help=f"{stock:,}")
        if stock_value is not None:
            colE.metric("Total Stock Value", format_large_number(stock_value), help=f"${stock_value:,.0f}")

        # Executive history section
        history = exec_info.get('history', [])
        if history:
            with st.expander("Job History", expanded=False):
                # Prefer 'title', 'start', 'duration' if present
                ticker = st.session_state.get('selected_company', '')
                if all('start' in h and 'duration' in h for h in history):
                    df_hist = pd.DataFrame(history)[['title', 'company', 'start', 'duration']]
                    df_hist = df_hist.rename(columns={"title": "Role", "company": "Company", "start": "Start", "duration": "Duration"})
                    # Only show year in Start
                    def only_year(val):
                        try:
                            return str(pd.to_datetime(val, errors='coerce').year)
                        except Exception:
                            return str(val)[:4]
                    df_hist['Start'] = df_hist['Start'].apply(only_year)
                else:
                    df_hist = pd.DataFrame(history)
                    df_hist = df_hist.rename(columns={"title": "Role", "from": "From", "to": "To"})
                    df_hist.insert(1, 'Company', ticker)
                df_hist = df_hist.iloc[::-1].reset_index(drop=True)
                st.dataframe(df_hist, hide_index=True)

        # 2. Organization chart in expander
        with st.expander("Organization Chart", expanded=False):
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
            st.caption("💡 The selected executive is highlighted in blue. Their manager (if any) is shown above, and direct reports are shown below. Click on any node to view their information.")
    else:
        st.info("Executive information not available")

    # --- Executive Review Section ---
    st.markdown("---")
    st.subheader(f"Feedback for {selected_exec}")
    # Load reviews from file
    reviews_data = load_exec_reviews()
    reviews = reviews_data.get(selected_exec, [])
    # Scorecard: average rating as metric
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    if reviews:
        with col3:
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
            # Calculate review statistics
            unique_reviewers = len(set(r.get('reviewer', 'Anonymous') for r in reviews))
            positive_reviews = sum(1 for r in reviews if r['rating'] >= 4)
            neutral_reviews = sum(1 for r in reviews if r['rating'] == 3)
            negative_reviews = sum(1 for r in reviews if r['rating'] <= 2)

            st.metric(
                label="Average Rating",
                value=f"{avg_rating:.2f} / 5",
                delta=f"{len(reviews)} review{'s' if len(reviews)!=1 else ''}",
                help="Average of all user ratings"
            )
        with col4:
            st.metric(
                label="Unique Reviewers",
                value=f"{unique_reviewers} / {len(reviews)}",
                delta=f"{'high' if unique_reviewers/len(reviews) < 0.3 else 'moderate' if unique_reviewers/len(reviews) < 0.5 else 'low'} bias - {len(reviews)-unique_reviewers} repeats",
                delta_color="inverse" if unique_reviewers/len(reviews) < 0.5 else "normal",
                help="Number of different people who have reviewed"
            )
        with col1:
            st.metric(
                label="Review Sentiment",
                value=f"👍 {positive_reviews} | 😐 {neutral_reviews} | 👎 {negative_reviews}",
                delta=f"{'overwhelmingly positive' if positive_reviews > neutral_reviews + negative_reviews else 'generally positive' if positive_reviews > neutral_reviews else 'slightly positive' if positive_reviews > negative_reviews else 'overwhelmingly negative' if negative_reviews > neutral_reviews + positive_reviews else 'generally negative' if negative_reviews > neutral_reviews else 'slightly negative' if negative_reviews > positive_reviews else 'generally neutral' if neutral_reviews > positive_reviews + negative_reviews else 'slightly neutral'}",
                help="Positive (4-5) | Neutral (3) | Negative (1-2)"
            )
        
    else:
        st.metric(label="Average Rating", value="No ratings yet", delta="0 reviews")
        st.metric(label="Unique Reviewers", value="0")
        st.metric(label="Review Sentiment", value="No reviews yet")
    # with col2:
    @st.dialog(f"Add review for {selected_exec}")
    def vote(item):
        new_rating = st.feedback("stars", key=f"rating_{selected_exec}")
        is_current_employee = st.checkbox(f"I am a current {ticker} employee", key=f"employee_{selected_exec}")
        relationship = st.radio(
            "My relationship to this executive:",
            options=["Direct Report", "Indirect Report", "Peer", "Manager", "No Direct Relationship"],
            key=f"relationship_{selected_exec}"
        )
        new_review = st.text_area("Your Review", key=f"review_{selected_exec}")
        if st.button("Submit Review", key=f"submit_{selected_exec}", type="primary"):
            if new_review.strip() and new_rating:
                reviews_data.setdefault(selected_exec, []).append({
                    'rating': new_rating,
                    'review': new_review.strip(),
                    'timestamp': datetime.now().isoformat(sep=' ', timespec='minutes'),
                    'reviewer': reviewer,
                    'is_current_employee': is_current_employee,
                    'relationship': relationship
                })
                save_exec_reviews(reviews_data)
                st.success("Thank you for your feedback!")
                st.rerun()
            else:
                st.warning("Please enter a review and select a rating before submitting.")
        
    
    if "vote" not in st.session_state:
        if st.button("💬 Add Review", type="primary"):
            vote("A")

    st.markdown("**Reviews:**")
    # Pagination logic
    REVIEWS_PER_PAGE = 5
    total_reviews = len(reviews)
    total_pages = max(1, (total_reviews + REVIEWS_PER_PAGE - 1) // REVIEWS_PER_PAGE)
    page_key = f"review_page_{selected_exec}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1
    page = st.session_state[page_key]
    start_idx = (page - 1) * REVIEWS_PER_PAGE
    end_idx = start_idx + REVIEWS_PER_PAGE
    if reviews:
        for r in list(reversed(reviews))[start_idx:end_idx]:
            ts = r.get('timestamp', '')
            reviewer = r.get('reviewer', 'Anonymous')
            stars = ''.join([
                f'<span style="color:#FFD600;font-size:1.2em;">&#9733;</span>' if i < r['rating'] else
                f'<span style="color:#444;font-size:1.2em;">&#9733;</span>'
                for i in range(5)
            ])
            profile_img = "https://ui-avatars.com/api/?name=" + reviewer.replace(" ", "+") + "&background=0D8ABC&color=fff&size=64"
            # Count total reviews by this reviewer across all execs
            all_reviews = sum([len([rv for rv in rvlist if rv.get('reviewer') == reviewer]) for rvlist in reviews_data.values()], 0)
            subtitle = f"DIS at time of review · {all_reviews} review{'s' if all_reviews != 1 else ''}"
            review_html = f'''
            <div style="background:#1a2b38; color:#e6f0fa; border-radius:12px; padding:12px 16px; margin-bottom:12px; box-sizing:border-box;">
                <div style="display:flex; align-items:flex-start;">
                    <img src="{profile_img}" style="width:48px; height:48px; border-radius:50%; margin-right:14px; margin-top:2px;">
                    <div style="flex:1;">
                        <div style="font-size:1.1em; font-weight:bold;">{reviewer}</div>
                        <div style="font-size:0.97em; color:#b0b8c1; margin-bottom:2px;">{subtitle}</div>
                    </div>
                </div>
                <div style="display:inline-block;">{stars}</div>
                <span style="font-size:0.95em; color:#b0b8c1; margin-left:10px;">{ts}</span>
                <div style="font-size:1.08em; color:#e6f0fa; text-align:left; white-space:pre-line;">{html.escape(r['review'])}</div>
            </div>
            '''
            st.markdown(review_html, unsafe_allow_html=True)
        # Pagination controls
        col_prev, col_page, col_next = st.columns([1,2,1])
        with col_prev:
            if page > 1:
                if st.button("Previous", key=f"prev_{selected_exec}"):
                    st.session_state[page_key] -= 1
                    st.rerun()
        with col_page:
            st.markdown(f"Page {page} of {total_pages}")
        with col_next:
            if page < total_pages:
                if st.button("Next", key=f"next_{selected_exec}"):
                    st.session_state[page_key] += 1
                    st.rerun()
    else:
        st.markdown("No reviews yet.")