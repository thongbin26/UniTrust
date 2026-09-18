import streamlit as st

def apply_global_styles():
    st.markdown("""
    <style>
        /* Global typography and colors */
        
        html, body, [class*="css"]  {
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #f8fafc;
            color: #1f2937;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #1e3a8a; /* Navy blue headings */
            font-weight: 700;
        }
        
        /* Consistent Card System */
        .stCard {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            border: 1px solid #e5e7eb;
            margin-bottom: 20px;
        }
        
        /* Modern Buttons */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Primary Button (Product Blue) */
        .stButton>button[kind="primary"] {
            background-color: #2563eb;
            color: white;
            border: none;
        }
        
        .stButton>button[kind="primary"]:hover {
            background-color: #1d4ed8;
        }
        
        /* Info/Warning Boxes */
        .stAlert {
            border-radius: 8px;
            border: 1px solid transparent;
        }
        
        /* Custom spacing */
        .spacer-sm { margin-top: 10px; margin-bottom: 10px; }
        .spacer-md { margin-top: 20px; margin-bottom: 20px; }
        .spacer-lg { margin-top: 40px; margin-bottom: 40px; }
        
        /* Badges */
        .badge {
            display: inline-block;
            padding: 0.25em 0.6em;
            font-size: 0.85rem;
            font-weight: 600;
            border-radius: 9999px;
            text-align: center;
        }
        
        .badge-verified { background-color: #d1fae5; color: #065f46; }
        .badge-conflict { background-color: #fee2e2; color: #991b1b; }
        .badge-partial { background-color: #fef3c7; color: #92400e; }
        .badge-insufficient { background-color: #f3f4f6; color: #374151; }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e5e7eb;
        }
        
    </style>
    """, unsafe_allow_html=True)
