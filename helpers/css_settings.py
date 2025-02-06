import streamlit as st 


custom_css = f"""
    <style>
        /* Hide the Streamlit menu, header, and footer */
        #MainMenu {{ visibility: hidden; }}
        header {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        /* Style for the logo at the bottom left corner */
        .logo {{
            position: fixed;
            bottom: 10px;
            left: 10px;
            z-index: 1000;
            width: 50px; /* Adjust as needed */
            height: auto;
        }}
    </style>

    
"""
logo_file = "assets/logo.png"
st.logo(logo_file,size="large")
