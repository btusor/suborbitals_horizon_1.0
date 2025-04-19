import streamlit as st
import datetime
import matplotlib.pyplot as plt
from rocketpy import Environment, SolidMotor, Rocket, Flight
import io
import contextlib
import re
import base64


# --- Kép beolvasása és base64-re alakítása ---
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

background_base64 = get_base64_image("background.png")

#------ Read off ------
def read_off_thrust_from_bytes(file_bytes, start_line=31):
    try:
        lines = file_bytes.decode("utf-8").splitlines()
        lines = lines[start_line:]
        thrust_curve = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2:
                time, thrust = float(parts[0]), float(parts[1])
                thrust_curve.append((time, thrust))
        return thrust_curve
    except Exception as e:
        print(f"Error in read_off_thrust_from_bytes: {e}")
        return []



def read_off_value(file_path, text, unit=None):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Check if the line contains the specified text
                if text in line:
                    # Regular expression to extract the number(s) with or without the specified unit
                    if unit:
                        pattern = rf"; {re.escape(text)}\s+\({re.escape(unit)}\):\s+([\d.\s]+)"
                    else:
                        pattern = rf"; {re.escape(text)}\s*:\s+([\d.\s]+)"
                    
                    match = re.search(pattern, line)
                    if match:
                        values = match.group(1).strip().split()
                        # Convert the values to float or int
                        values = [round(float(value), 4) if '.' in value else int(value) for value in values]
                        # Return a single value if only one value is found
                        return values[0] if len(values) == 1 else values
        raise ValueError(f"Text '{text}' with unit '{unit}' not found in the file.")
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def read_grain_values(file_path, value_type):
    values = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Regular expression to extract the specified value for each grain
                if value_type == "length":
                    match = re.search(r"Grain #\d+:.*Length=([\d.]+) mm", line)
                elif value_type == "density":
                    match = re.search(r"Grain #\d+:.*Density=([\d.]+) kg/m\^3", line)
                elif value_type == "id":
                    match = re.search(r"Grain #\d+:.*ID=([\d.]+) mm", line)
                elif value_type == "od":
                    match = re.search(r"Grain #\d+:.*OD=([\d.]+) mm", line)
                elif value_type == "inhib":
                    match = re.search(r"Grain #\d+:.*Inhib=([\d.]+) mm", line)
                else:
                    raise ValueError("Invalid value type specified. Use 'length' or 'density'.")
                
                if match:
                    value = float(match.group(1))
                    values.append(round(value, 4))
        
        if not values:
            raise ValueError(f"No {value_type} values found in the file.")
        return values
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



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
st.markdown(
    """
    <h1 style='
        font-size: 45px;
        color: black;
        text-align: center;
        font-family: sans-serif;
    '>
        RocketPy Simulation Dashboard
    </h1>
    """,
    unsafe_allow_html=True
)

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

# --- Page 1: Motor ---
elif st.session_state.current_page == 1:
    st.header("2. Motor Configuration")
    st.markdown("Choose a data file, which contains data regarding the grains and thrust curve.")

    file = st.file_uploader("Upload `.eng` file", type=["eng"])

    if file:
        try:
            file_bytes = file.getvalue()
            thrust_data = read_off_thrust_from_bytes(file_bytes, 31)
            st.write("THRUST DATA:", thrust_data)

            #Plot
            times, thrusts = zip(*thrust_data)
            plt.figure()
            plt.plot(times, thrusts)
            plt.xlabel("Time [s]")
            plt.ylabel("Thrust [N]")
            plt.title("Thrust Curve")
            st.pyplot(plt)

            st.write("Grain number:", read_off_value("uploaded_motor.eng", "Number of Grains"))
            st.write("Grain length:", read_grain_values("uploaded_motor.eng", "length"))
            st.write("Grain OD:", read_grain_values("uploaded_motor.eng", "od"))
            st.write("Grain ID:", read_grain_values("uploaded_motor.eng", "id"))
            st.write("Grain density:", read_grain_values("uploaded_motor.eng", "density"))
            st.write("Grain Inhib:", read_grain_values("uploaded_motor.eng", "inhib"))


            st.write("THRUST DATA:", thrust_data)
            if not thrust_data or not isinstance(thrust_data, list):
                st.error("❌ Error in thrust data!")
            else:
                Kratos = SolidMotor(
                    thrust_source=thrust_data,
                    dry_mass=read_off_value("uploaded_motor.eng", "Hardware Mass", "kg"),
                    dry_inertia=(1.138, 1.138, 0.012),
                    nozzle_radius=read_off_value("uploaded_motor.eng", "Nozzle Exit Diameter") / 2000,
                    grain_number=read_off_value("uploaded_motor.eng", "Number of Grains"),
                    grain_density=read_grain_values("uploaded_motor.eng", "density")[0],
                    grain_outer_radius=read_grain_values("uploaded_motor.eng", "od")[0] / 2000,
                    grain_initial_inner_radius=read_grain_values("uploaded_motor.eng", "id")[0] / 2000,
                    grain_initial_height=read_off_value("uploaded_motor.eng", "Total Propellant Length", "mm") / 1000 / read_off_value("uploaded_motor.eng", "Number of Grains"),
                    grain_separation=0.007,
                    grains_center_of_mass_position=read_off_value("uploaded_motor.eng", "Total Propellant Length", "mm") / 2000,
                    center_of_dry_mass_position=read_off_value("uploaded_motor.eng", "Total Motor Length", "mm") / 2000,
                    nozzle_position=-14/100,
                    throat_radius=read_off_value("uploaded_motor.eng", "Nozzle Throat Diameter") / 2000,
                    coordinate_system_orientation="nozzle_to_combustion_chamber",
                    interpolation_method='linear'
                )
                st.success("✅ Success in reading the motor data!")

                # Ide irányítjuk a kimenetet, hogy elérjük a printelt szöveget
                grain_info_buffer = io.StringIO()

                with contextlib.redirect_stdout(grain_info_buffer):
                    Kratos.prints.grain_details()
                    print("\n\n--- Motor Info ---\n")
                    Kratos.info()

                # Kivesszük a kimenetet és kezeljük az inf és NaN értékeket
                grain_info_text = grain_info_buffer.getvalue()

                # Cseréljük az 'inf' és 'NaN' értékeket
                grain_info_text = grain_info_text.replace("inf", "infinity").replace("NaN", "Not_a_Number")

                # Most letöltési gombot generálunk
                st.download_button(
                    label="📄 Grain details download (.txt)",
                    data=grain_info_text,
                    file_name="grain_details.txt",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"❌ Error in reading the file: {e}")

    st.write("Dry mass:", read_off_value("uploaded_motor.eng", "Hardware Mass", "kg"))
    st.write("Nozzle exit radius:", read_off_value("uploaded_motor.eng", "Nozzle Exit Diameter") / 2000)
    st.write("Grain number:", read_off_value("uploaded_motor.eng", "Number of Grains"))
    st.write("Grain density:", read_grain_values("uploaded_motor.eng", "density")[0])
    st.write("Grain OD:", read_grain_values("uploaded_motor.eng", "od")[0] / 2000)
    st.write("Grain ID:", read_grain_values("uploaded_motor.eng", "id")[0] / 2000)
    st.write("Grain height:", read_off_value("uploaded_motor.eng", "Total Propellant Length", "mm") / 1000 / read_off_value("uploaded_motor.eng", "Number of Grains"))
    st.write("Grains CG:", read_off_value("uploaded_motor.eng", "Total Propellant Length", "mm") / 2000)
    st.write("Dry CG:", read_off_value("uploaded_motor.eng", "Total Motor Length", "mm") / 2000)
    st.write("Throat radius:", read_off_value("uploaded_motor.eng", "Nozzle Throat Diameter") / 2000)



            


# --- Page 2: Geometry ---
elif st.session_state.current_page == 2:
    st.header("3. Geometry setup")
    

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
