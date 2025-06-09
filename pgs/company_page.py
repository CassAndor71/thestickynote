import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import plotly.graph_objects as go
import networkx as nx
import json
import os
import pandas as pd

def format_large_number(num):
    """Format large numbers into K, M, B format."""
    if num >= 1e9:
        return f"${num/1e9:.1f}B"
    elif num >= 1e6:
        return f"${num/1e6:.1f}M"
    elif num >= 1e3:
        return f"${num/1e3:.1f}K"
    else:
        return f"${num:,.2f}"

def load_executive_data(company_ticker):
    """Load executive data from JSON file."""
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    file_path = os.path.join(data_dir, f'{company_ticker.lower()}_executives.json')
    
    # st.write(f"Looking for executive data at: {file_path}")  # Debug line
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # st.write("Successfully loaded executive data")  # Debug line
            return data
    except FileNotFoundError:
        # st.write(f"File not found: {file_path}")  # Debug line
        return None
    except json.JSONDecodeError:
        # st.write("Error: Invalid JSON file")  # Debug line
        return None
    except Exception as e:
        # st.write(f"Error loading executive data: {str(e)}")  # Debug line
        return None

def create_org_chart(executives, selected_exec):
    """Create an interactive org chart showing manager and direct reports for selected executive, with improved layout and styling, and a badge for role_tag."""
    G = nx.DiGraph()
    
    # Add selected executive (full name, no title)
    G.add_node(selected_exec, 
               label=selected_exec,  # for node label
               hover=f"{selected_exec}<br>{executives[selected_exec]['title']}",
               level=1,
               role_tag=executives[selected_exec].get('role_tag', 'E'))
    
    # Add manager (full name, no title)
    has_manager = False
    if executives[selected_exec]['reports_to']:
        manager = executives[selected_exec]['reports_to']
        G.add_node(manager, 
                  label=manager,
                  hover=f"{manager}<br>{executives[manager]['title']}",
                  level=0,
                  role_tag=executives[manager].get('role_tag', 'E'))
        G.add_edge(manager, selected_exec)
        has_manager = True
    
    # Add direct reports (first name only, no title)
    direct_reports = [r for r in executives[selected_exec]['direct_reports'] if r in executives]
    for i, report in enumerate(direct_reports):
        first_name = report.split()[0]
        G.add_node(report, 
                  label=first_name,
                  hover=f"{report}<br>{executives[report]['title']}",
                  level=2,
                  role_tag=executives[report].get('role_tag', 'E'))
        G.add_edge(selected_exec, report)

    # Custom layout: center and space horizontally, 8 per row
    pos = {}
    y_gap = 1.5
    x_gap = 2
    max_per_row = 8
    n_reports = len(direct_reports)
    
    # Manager (if any) at top center
    if has_manager:
        pos[manager] = (0, y_gap)
    # Selected exec in center
    pos[selected_exec] = (0, 0)
    # Direct reports spaced horizontally below, 8 per row
    for i, report in enumerate(direct_reports):
        row = i // max_per_row
        col = i % max_per_row
        # Center the row
        reports_in_this_row = min(max_per_row, n_reports - row * max_per_row)
        x = (col - (reports_in_this_row - 1) / 2) * x_gap if reports_in_this_row > 1 else 0
        y = -y_gap * (row + 1)
        pos[report] = (x, y)

    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node trace
    node_x = []
    node_y = []
    node_text = []  # label for node
    node_hover = [] # hover text for node
    node_colors = []
    node_names = []
    node_tags = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(G.nodes[node]['label'])
        node_hover.append(G.nodes[node]['hover'])
        node_names.append(node)
        node_colors.append('rgb(31, 119, 180)' if node == selected_exec else 'rgb(158, 202, 225)')
        node_tags.append(G.nodes[node].get('role_tag', 'E'))
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="bottom center",
        marker=dict(
            showscale=False,
            color=node_colors,
            size=40,
            line_width=2,
            line_color='white',
            symbol='square'  # Use squares for nodes
        ),
        customdata=node_names,
        textfont=dict(color='black', size=14),  # Make all text black
        hovertext=node_hover,
        hoverlabel=dict(font=dict(color='black'))
    )

    # Add badge trace for role_tag (E, C, M)
    badge_x = []
    badge_y = []
    badge_text = []
    badge_offset = x_gap * 0  # Offset scales with node spacing
    for i, (x, y, tag) in enumerate(zip(node_x, node_y, node_tags)):
        # Place badge at top-right of each square
        badge_x.append(x + badge_offset)
        badge_y.append(y + badge_offset)
        badge_text.append(tag)
    badge_trace = go.Scatter(
        x=badge_x,
        y=badge_y,
        mode='text',
        text=badge_text,
        textposition='middle center',
        textfont=dict(color='black', size=16, family='Arial Black'),
        marker=dict(color='white', size=24, line=dict(width=1, color='black')),
        showlegend=False,
        hoverinfo='none'
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace, badge_trace],
                   layout=go.Layout(
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=40,l=40,r=40,t=80),
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       height=400,
                       plot_bgcolor='white',
                       clickmode='event+select',
                       hoverlabel=dict(bgcolor="white", font_size=16, font_family="Rockwell", font_color='black')
                   ))
    return fig

def show_company_page():
    # st.title("Company Page")
    # Defensive: check session state
    if 'company_name' not in st.session_state or 'selected_company' not in st.session_state:
        st.error("Company not selected. Please return to the home page.")
        return
    if 'role' not in st.session_state:
        st.error("Role not selected. Please return to the home page.")
        return
    if st.button("<- Company Selection"):
        st.session_state['page'] = 'home'
        st.rerun()
    st.title(f"📝 {st.session_state['company_name']} ({st.session_state['selected_company']})")
    # st.caption(f"Role: {st.session_state['role']}")
    
    # Get stock data
    ticker = st.session_state['selected_company']
    stock = yf.Ticker(ticker)
    
    # Company Overview Metrics
    with st.expander("Company Overview", expanded=True):
        info = stock.info
        executives = load_executive_data(ticker)
        
        # Company Structure
        st.subheader("Company Structure")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if 'firstTradeDateEpochUtc' in info:
                founding_date = datetime.fromtimestamp(info['firstTradeDateEpochUtc'])
                company_age = datetime.now().year - founding_date.year
                st.metric("Years Public", company_age)
        with col2:
            if executives:
                st.metric("Number of Executives", len(executives))
        with col3:
            if 'fullTimeEmployees' in info:
                st.metric("Total Employees", f"{info['fullTimeEmployees']:,}")
        with col4:
            if executives and 'fullTimeEmployees' in info:
                exec_ratio = (len(executives) / info['fullTimeEmployees']) * 100
                st.metric("Executive Ratio", f"{exec_ratio:.2f}%")
        
        # Financial Performance
        st.subheader("Financial Performance")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if 'totalRevenue' in info:
                st.metric("Annual Revenue", format_large_number(info['totalRevenue']))
        with col2:
            if 'profitMargins' in info:
                st.metric("Profit Margin", f"{info['profitMargins'] * 100:.2f}%")
        with col3:
            if 'operatingMargins' in info:
                st.metric("Operating Margin", f"{info['operatingMargins'] * 100:.2f}%")
        with col4:
            if 'totalRevenue' in info and 'fullTimeEmployees' in info:
                rev_per_emp = info['totalRevenue'] / info['fullTimeEmployees']
                st.metric("Revenue/Employee", format_large_number(rev_per_emp))
        
        # Shareholder Metrics
        st.subheader("Shareholder Metrics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if 'sharesOutstanding' in info:
                st.metric("Outstanding Shares", format_large_number(info['sharesOutstanding']))
        with col2:
            if 'dividendRate' in info:
                st.metric("Annual Dividend", f"${info['dividendRate']:.2f}")
        with col3:
            if 'enterpriseValue' in info:
                st.metric("Enterprise Value", format_large_number(info['enterpriseValue']))
        with col4:
            if 'totalCash' in info and executives:
                avg_exec_comp = info['totalCash'] / len(executives)
                st.metric("Avg Exec Comp", format_large_number(avg_exec_comp))
    
    # Stock Overview
    with st.expander("Stock Overview", expanded=False):
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                datetime.now() - timedelta(days=365),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                datetime.now(),
                max_value=datetime.now()
            )
        
        # Get historical data
        hist = stock.history(start=start_date, end=end_date)
        if hist.empty:
            st.warning("No stock data available for this period.")
            return
        
        # Stock metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Price", f"${hist['Close'].iloc[-1]:.2f}")
        with col2:
            daily_change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
            daily_change_pct = (daily_change / hist['Close'].iloc[-2]) * 100
            st.metric("Daily Change", f"${daily_change:.2f}", f"{daily_change_pct:.2f}%")
        with col3:
            st.metric("52 Week High", f"${hist['High'].max():.2f}")
        with col4:
            st.metric("52 Week Low", f"${hist['Low'].min():.2f}")
        
        # Create interactive chart
        fig = go.Figure()
        
        # Add candlestick chart
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='OHLC'
        ))
        
        # Add volume bar chart
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['Volume'],
            name='Volume',
            yaxis='y2',
            opacity=0.3
        ))
        
        # Update layout
        fig.update_layout(
            title=f'{st.session_state["company_name"]} Stock Price',
            yaxis_title='Stock Price (USD)',
            yaxis2=dict(
                title='Volume',
                overlaying='y',
                side='right'
            ),
            xaxis_rangeslider_visible=False,
            height=300,
            template='plotly_white'
        )
        
        # Show the chart
        st.plotly_chart(fig, use_container_width=True)
    
    # Executive bio and jump button
    ticker = st.session_state['selected_company']
    executives = load_executive_data(ticker)
    if not executives:
        st.info("Executive information not available for this company.")
        return
    if 'selected_exec' not in st.session_state:
        st.session_state['selected_exec'] = list(executives.keys())[0]
    selected_exec = st.selectbox(
        "Select Executive to View Reporting Structure",
        options=list(executives.keys()),
        index=list(executives.keys()).index(st.session_state['selected_exec']),
        format_func=lambda x: f"{x} - {executives[x]['title']}"
    )
    if selected_exec != st.session_state['selected_exec']:
        st.session_state['selected_exec'] = selected_exec
        st.rerun()
    st.markdown(f"**{selected_exec}** - {executives[selected_exec]['title']}")
    st.markdown(executives[selected_exec]['bio'])
    # Add button to jump to executive_detail.py
    if st.button("View Executive Team Details"):
        st.session_state['page'] = 'executive_detail'
        st.rerun()