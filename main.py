import streamlit as st
import datetime
import matplotlib.pyplot as plt
from rocketpy import Environment, SolidMotor, Rocket, Flight
import io
import contextlib
import base64


# --- Kép beolvasása és base64-re alakítása ---
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

background_base64 = get_base64_image("background.png")

# --- CSS injektálása ---
def inject_css():
    st.markdown(f"""
    <style>
    /* Sidebar háttérkép */
    [data-testid="stSidebar"] {{
        background-image: url("data:image/png;base64,{background_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}

    [data-testid="stSidebar"] * {{
        color: white;
    }}

    /* Navigációs gombok */
    .nav-container {{
        display: flex;
        justify-content: space-between;
        margin-top: 2rem;
    }}
    .nav-button button {{
        background-color: #ccc !important;
        color: black !important;
        font-size: 12px !important;
        padding: 0.25em 1em !important;
        border-radius: 4px !important;
        border: 1px solid #aaa !important;
    }}
    .nav-button button:hover {{
        background-color: #bbb !important;
        border-color: #888 !important;
    }}

    /* Alap gombstílus (burgundi) */
    button[kind="primary"] {{
        background-color: #800020 !important;
        color: white !important;
        border: 1px solid #800020 !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 0.5em 2em !important;
    }}
    button[kind="primary"]:hover {{
        background-color: #660018 !important;
        border-color: #660018 !important;
    }}

    .stButton>button, .stTextInput>div>input {{
        background-color: #660033;
        color: white;
        border: 1px solid #660033;
    }}
    .stButton>button:hover, .stTextInput>div>input:hover {{
        background-color: #4d002a;
        border-color: #4d002a;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- CSS betöltése ---
inject_css()

    
# --- Sidebar ---
with st.sidebar:
    st.image("logo.png", width=200)
    st.markdown("### Rocket Configuration Tool")
    st.markdown("Created by Balint Tusor")

# --- Title ---
st.title("RocketPy Simulation Dashboard")

# --- Session state setup ---
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "env" not in st.session_state:
    st.session_state.env = None
    st.session_state.env_info = ""

# --- Page 0: Environment ---
if st.session_state.current_page == 0:
    st.header("1. Launch Environment")

    col1, col2, col3 = st.columns(3)
    with col1:
        site_lat = st.number_input("Latitude [°]", value=47.117819)
    with col2:
        site_long = st.number_input("Longitude [°]", value=19.341037)
    with col3:
        site_elev = st.number_input("Elevation [m]", value=0)

    col1, col2 = st.columns(2)
    with col1:
        launch_date = st.date_input("Select launch date", datetime.date.today() + datetime.timedelta(days=1))
    with col2:
        launch_time = st.time_input("Select launch time", value=datetime.time(hour=12, minute=0))

    def setup_environment():
        env = Environment(latitude=site_lat, longitude=site_long, elevation=site_elev)
        env.set_date((launch_date.year, launch_date.month, launch_date.day, launch_time.hour, launch_time.minute))
        env.set_atmospheric_model(type="Forecast", file="GFS")
        return env

    if st.button("Get GFS Weather info"):
        with st.spinner("Getting weather data..."):
            env = setup_environment()
            st.session_state.env = env

            info_buffer = io.StringIO()
            plt.close("all")
            with contextlib.redirect_stdout(info_buffer):
                env.info()
            st.session_state.env_info = info_buffer.getvalue()

    if st.session_state.env:
        st.download_button(
            label="📄 Download environment info (.txt)",
            data=st.session_state.env_info,
            file_name="environment_info.txt",
            mime="text/plain"
        )

        figs = [plt.figure(n) for n in plt.get_fignums()]
        for fig in figs:
            st.pyplot(fig)

# --- Page 1: Geometry ---
elif st.session_state.current_page == 1:
    st.header("2. Geometry Setup")
    st.markdown("Geometry configuration section coming soon...")

# --- Page 2: Motor ---
elif st.session_state.current_page == 2:
    st.header("3. Motor Configuration")
    st.markdown("Upload your motor thrust curve file in `.eng` format.")
    file = st.file_uploader("Upload .eng file", type=["eng"])
    if file:
        st.success("File uploaded successfully.")

# --- Navigation ---
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.session_state.current_page > 0:
        if st.button("Back", key="back_button"):
            st.session_state.current_page -= 1
            st.rerun()
with col2:
    if st.session_state.current_page < 2:
        if st.button("Next", key="next_button"):
            st.session_state.current_page += 1
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
