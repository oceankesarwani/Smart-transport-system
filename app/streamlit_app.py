"""
Smart Public Transport Route and Crowd Prediction System
Interactive Web Dashboard & Command Center (Streamlit)
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
from PIL import Image

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.transport.network import TransitNetwork
from src.transport.model import CrowdModelManager
from src.transport.routing import DijkstraRouter
from src.transport.utils import load_config

st.set_page_config(
    page_title="Smart Transit Crowd & Route Optimization",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #2563eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 12px;
    }
    .badge-low {
        background-color: #dcfce7;
        color: #15803d;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-medium {
        background-color: #fef9c3;
        color: #a16207;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-high {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_system_core():
    config = load_config()
    network = TransitNetwork()
    # Check if model exists, if not train quick fallback
    model_path = PROJECT_ROOT / config["model"]["artifact_path"]
    if not os.path.exists(model_path):
        from src.transport.data_gen import generate_ridership_dataset
        df = generate_ridership_dataset(config)
        mgr = CrowdModelManager(config)
        mgr.train_and_benchmark(df)
        mgr.save(str(model_path))
    else:
        mgr = CrowdModelManager.load(str(model_path))
    router = DijkstraRouter(network=network, model_mgr=mgr, config=config)
    return config, network, mgr, router

config, network, model_mgr, router = load_system_core()

# Header
st.title("🚌 Smart Public Transport Route & Crowd Prediction System")
st.markdown("**Empowering Urban Commuters with Proactive Crowd-Aware Multi-Objective Route Optimization**")

# Sidebar Controls
st.sidebar.header("🕹️ Route Planning Controls")

all_stops = network.get_all_stop_ids()
stop_name_map = {s: f"{network.get_stop_name(s)} ({s})" for s in all_stops}

col1, col2 = st.sidebar.columns(2)
with col1:
    src_stop = st.selectbox("Source Stop", all_stops, index=0, format_func=lambda s: stop_name_map[s])
with col2:
    dst_stop = st.selectbox("Destination Stop", all_stops, index=15, format_func=lambda s: stop_name_map[s])

st.sidebar.markdown("---")
st.sidebar.subheader("🕒 Travel Conditions & Timing")
travel_date = st.sidebar.date_input("Travel Date", datetime(2026, 11, 25))
travel_hour = st.sidebar.slider("Departure Hour", 6, 22, 9, format="%d:00")
weather = st.sidebar.selectbox("Weather Condition", ["Clear", "Rain"])
is_event = st.sidebar.checkbox("Special Event / Exam Surge", value=False)
lam = st.sidebar.slider(
    "Lambda Trade-off (Crowd Penalty vs. Speed)",
    min_value=0.0, max_value=5.0, value=1.5, step=0.1,
    help="Higher lambda penalizes crowded buses, favoring less congested alternative corridors."
)

tab1, tab2, tab3 = st.tabs([
    "🔀 Route Decision & Comparison",
    "📈 Hourly Stop Crowd Forecast",
    "📊 ML Performance & Publication Figures"
])

# ----------------- TAB 1: Route Decision & Comparison -----------------
with tab1:
    if src_stop == dst_stop:
        st.warning("⚠️ Source and destination stops are identical. Please choose distinct stops.")
    else:
        base_route = router.baseline_route(src_stop, dst_stop)
        smart_route = router.best_route(
            src=src_stop,
            dst=dst_stop,
            when=travel_hour,
            weather=weather.lower(),
            is_event=1 if is_event else 0,
            lam=lam
        )

        if not base_route or not smart_route:
            st.error("❌ No viable transit path could be computed between the selected stops.")
        else:
            time_delta = round(smart_route["total_travel_time"] - base_route["total_travel_time"], 1)
            penalty_delta = base_route["total_crowd_penalty"] - smart_route["total_crowd_penalty"]
            pct_penalty_red = round((penalty_delta / max(1, base_route["total_crowd_penalty"])) * 100.0, 1) if base_route["total_crowd_penalty"] > 0 else 0.0

            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
            with col_kpi1:
                st.metric("Crowd Penalty Score", f"{smart_route['total_crowd_penalty']} pts", delta=f"{pct_penalty_red}% Less Crowd")
            with col_kpi2:
                st.metric("High-Crowd Segments", f"{smart_route['high_crowd_segments']}", delta=f"{smart_route['high_crowd_segments'] - base_route['high_crowd_segments']} Segments")
            with col_kpi3:
                st.metric("Crowd-Aware Travel Time", f"{smart_route['total_travel_time']} mins", delta=f"{time_delta:+} mins vs Baseline")
            with col_kpi4:
                st.metric("Transfers Required", f"{smart_route['transfers']}", delta=f"{smart_route['transfers'] - base_route['transfers']} line switches")

            st.markdown("---")

            col_route_left, col_route_right = st.columns(2)

            with col_route_left:
                st.markdown("### ⚠️ Baseline Route (Shortest Time Only, $\\lambda=0$)")
                st.caption("Ignores crowd congestion; commuters are funneled into crowded peak vehicles.")
                st.write(f"**Travel Time:** {base_route['total_travel_time']} mins | **Crowd Penalty:** {base_route['total_crowd_penalty']} pts")
                st.write(f"**High-Crowd Segments Encountered:** {base_route['high_crowd_segments']}")
                st.markdown("**Path Itinerary:**")
                for idx, stop in enumerate(base_route["path_names"]):
                    st.markdown(f"**{idx+1}.** {stop}")

            with col_route_right:
                st.markdown("### 🛡️ Crowd-Aware Route (Ours, $\\lambda=" + f"{lam:.1f}" + "$)")
                st.caption("Dynamically diverts around congested hubs, balancing travel duration with passenger comfort.")
                st.write(f"**Travel Time:** {smart_route['total_travel_time']} mins | **Crowd Penalty:** {smart_route['total_crowd_penalty']} pts")
                st.write(f"**High-Crowd Segments Encountered:** {smart_route['high_crowd_segments']}")
                st.markdown("**Optimized Itinerary with Live Predicted Crowd Badges:**")

                for idx, seg in enumerate(smart_route["segments"]):
                    lvl = seg["crowd_level"]
                    badge_class = f"badge-{lvl.lower()}"
                    badge_html = f"<span class='{badge_class}'>{lvl.upper()} CROWD</span>"
                    st.markdown(
                        f"**Step {idx+1}:** Take **{seg['route_id']}** from `{seg['from_name']}` → `{seg['to_name']}` ({seg['travel_time']}m) — {badge_html}",
                        unsafe_allow_html=True
                    )

            # Display Network Topology Figure if present
            net_fig_path = PROJECT_ROOT / "results" / "figures" / "network_graph_sample_route.png"
            if net_fig_path.exists():
                st.markdown("---")
                st.markdown("#### 🗺️ Network Route Topology Visualization")
                st.image(str(net_fig_path), use_container_width=True)

# ----------------- TAB 2: Hourly Stop Forecast -----------------
with tab2:
    st.subheader("📈 24-Hour Station Predictive Load Curve")
    selected_stop = st.selectbox("Select Station to Inspect", all_stops, format_func=lambda s: stop_name_map[s])

    hours = list(range(6, 23))
    forecast_rows = []
    for h in hours:
        lvl = model_mgr.predict_crowd(
            route_id="R1",
            stop_id=selected_stop,
            dt_or_hour=h,
            weather=weather.lower(),
            is_event=1 if is_event else 0
        )
        score_val = 0.25 if lvl == "Low" else (0.60 if lvl == "Medium" else 0.90)
        forecast_rows.append({"Hour": f"{h:02d}:00", "Predicted Crowd Level": lvl, "Crowd Index": score_val})

    f_df = pd.DataFrame(forecast_rows)
    st.bar_chart(f_df.set_index("Hour")["Crowd Index"])
    st.caption("Relative crowding levels across the day illustrating rush hour morning and evening peaks.")

# ----------------- TAB 3: Model Metrics & Figures -----------------
with tab3:
    st.subheader("⚙️ Machine Learning Benchmarks & System Evaluation Figures")

    col_fig1, col_fig2 = st.columns(2)
    fig_dir = PROJECT_ROOT / "results" / "figures"

    with col_fig1:
        if (fig_dir / "confusion_matrix.png").exists():
            st.image(str(fig_dir / "confusion_matrix.png"), caption="Figure 1: Random Forest Confusion Matrix")
        if (fig_dir / "baseline_vs_ours_barchart.png").exists():
            st.image(str(fig_dir / "baseline_vs_ours_barchart.png"), caption="Figure 2: Baseline vs. Ours Performance")

    with col_fig2:
        if (fig_dir / "feature_importance.png").exists():
            st.image(str(fig_dir / "feature_importance.png"), caption="Figure 3: Feature Importance Analysis")
        if (fig_dir / "lambda_tradeoff_curve.png").exists():
            st.image(str(fig_dir / "lambda_tradeoff_curve.png"), caption="Figure 4: Lambda Trade-off Sensitivity")
