import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Rocket Launch", layout="wide")
st.title("🚀 Rocket Launch Simulation")

# Rakéta feltöltése
rocket_file = st.file_uploader("Upload your rocket PNG", type=["png"])

if rocket_file is not None:
    # Base64 konvertálás
    rocket_base64 = base64.b64encode(rocket_file.read()).decode()

    # HTML + CSS + JS animáció
    html_string = f"""
    <style>
    body {{
        margin: 0;
        overflow: hidden;
    }}

    #rocket {{
        width: 100px;
        position: absolute;
        top: 40vh;
        left: 0;
        transition: transform 3s ease-in-out;
        z-index: 10;
    }}

    #rocket.launch {{
        transform: translateX(90vw);
    }}

    #trail {{
        width: 60px;
        height: 20px;
        background: radial-gradient(circle, orange, red);
        position: absolute;
        top: 60vh;
        left: 20px;
        opacity: 0.6;
        filter: blur(4px);
        border-radius: 50%;
        animation: pulse 0.2s infinite;
        z-index: 5;
    }}

    @keyframes pulse {{
        0% {{ transform: scale(1); opacity: 0.5; }}
        50% {{ transform: scale(1.2); opacity: 1; }}
        100% {{ transform: scale(1); opacity: 0.5; }}
    }}
    </style>

    <div id="rocket-container">
        <img id="rocket" src="data:image/png;base64,{rocket_base64}">
        <div id="trail"></div>
    </div>

    <script>
    const rocket = document.getElementById("rocket");
    function launchRocket() {{
        rocket.classList.add("launch");
    }}
    </script>

    <button onclick="launchRocket()" style="
        margin-top: 20px;
        padding: 10px 20px;
        font-size: 16px;
        background-color: #550000;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;">
        Launch Rocket
    </button>
    """

    components.html(html_string, height=400)
else:
    st.info("Please upload a PNG image of your rocket to begin.")
