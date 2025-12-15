import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Fiscal Correlation Dashboard", layout="wide")
st.title("📊 Systemic Correlation Analyzer: DI vs. Inflation")

# ==========================================
# 2. HARDCODED FISCAL EVENTS
# ==========================================
fiscal_events_data = [
    {"Date": "2025-01-10", "Event": "CPI (Dec)", "Actual": "4.83%", "Forecast": "4.87%"},
    {"Date": "2025-01-29", "Event": "Copom Rate Decision", "Actual": "13.25%", "Forecast": "13.25%"},
    {"Date": "2025-02-11", "Event": "CPI (Jan)", "Actual": "4.56%", "Forecast": "4.57%"},
    {"Date": "2025-03-12", "Event": "CPI (Feb)", "Actual": "5.06%", "Forecast": "5.00%"},
    {"Date": "2025-03-19", "Event": "Copom Rate Decision", "Actual": "14.25%", "Forecast": "14.25%"},
    {"Date": "2025-04-11", "Event": "CPI (Mar)", "Actual": "5.48%", "Forecast": "5.48%"},
    {"Date": "2025-05-07", "Event": "Copom Rate Decision", "Actual": "14.75%", "Forecast": "14.75%"},
    {"Date": "2025-05-09", "Event": "CPI (Apr)", "Actual": "5.53%", "Forecast": "5.48%"},
    {"Date": "2025-06-10", "Event": "CPI (May)", "Actual": "5.32%", "Forecast": "5.53%"},
    {"Date": "2025-06-18", "Event": "Copom Rate Decision", "Actual": "15.00%", "Forecast": "14.75%"},
    {"Date": "2025-07-10", "Event": "CPI (Jun)", "Actual": "5.35%", "Forecast": "5.32%"},
    {"Date": "2025-07-30", "Event": "Copom Rate Decision", "Actual": "15.00%", "Forecast": "15.00%"},
    {"Date": "2025-08-12", "Event": "CPI (Jul)", "Actual": "5.23%", "Forecast": "5.34%"},
    {"Date": "2025-09-10", "Event": "CPI (Aug)", "Actual": "5.13%", "Forecast": "5.10%"}
]
events_df = pd.DataFrame(fiscal_events_data)
events_df['Date'] = pd.to_datetime(events_df['Date'])

# ==========================================
# 3. DATA LOADING FUNCTION
# ==========================================
@st.cache_data
def load_data(di_file, inf_file):
    try:
        di_df = pd.read_excel(di_file, index_col=0)
        inf_df = pd.read_excel(inf_file, index_col=0)

        # Clean Dates & Sort
        for df in [di_df, inf_df]:
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)

        # Align Data
        common_idx = di_df.index.intersection(inf_df.index)
        di_df = di_df.loc[common_idx]
        inf_df = inf_df.loc[common_idx]

        return di_df, inf_df
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return None, None

def get_year(col):
    try: return 2000 + int(col[-2:])
    except: return None

# ==========================================
# 4. SIDEBAR: FILE UPLOAD & SETTINGS
# ==========================================
st.sidebar.header("📁 Data Input")
uploaded_di = st.sidebar.file_uploader("Upload DI Data (.xlsx)", type=['xlsx'])
uploaded_inf = st.sidebar.file_uploader("Upload Inflation Data (.xlsx)", type=['xlsx'])

if uploaded_di and uploaded_inf:
    di_df, inf_df = load_data(uploaded_di, uploaded_inf)

    if di_df is not None:
        # Map Columns
        di_map = {get_year(c): c for c in di_df.columns if get_year(c)}
        inf_map = {get_year(c): c for c in inf_df.columns if get_year(c)}
        years = sorted(list(set(di_map.keys()) & set(inf_map.keys())))

        # Widgets
        st.sidebar.divider()
        st.sidebar.header("⚙️ Analysis Settings")
        selected_year = st.sidebar.selectbox("Select Maturity Year", years)
        window_size = st.sidebar.slider("Rolling Window (Days)", 10, 120, 60, 5)

        # ==========================================
        # 5. MAIN PLOT LOGIC
        # ==========================================
        if selected_year:
            di_col = di_map[selected_year]
            inf_col = inf_map[selected_year]

            # 1. Prepare Data
            series_di = di_df[di_col]
            series_inf = inf_df[inf_col]

            # Calculate Rolling Correlation
            di_chg = series_di.diff()
            inf_chg = series_inf.diff()
            roll_corr = di_chg.rolling(window=window_size).corr(inf_chg)

            # Filter Events for Visible Range
            min_date, max_date = roll_corr.index.min(), roll_corr.index.max()
            visible_events = events_df[(events_df['Date'] >= min_date) & (events_df['Date'] <= max_date)]

            # 2. Create Subplots Grid (3 Rows)
            # Row 1: DI Yields
            # Row 2: Inflation Yields
            # Row 3: Correlation (Left) + Event Table (Right)
            fig = make_subplots(
                rows=3, cols=2,
                column_widths=[0.7, 0.3],
                vertical_spacing=0.1,
                specs=[
                    [{"type": "xy", "colspan": 2}, None],  # Row 1: DI (Full Width)
                    [{"type": "xy", "colspan": 2}, None],  # Row 2: Inf (Full Width)
                    [{"type": "xy"}, {"type": "table"}]    # Row 3: Corr | Table
                ],
                subplot_titles=(
                    f"DI Nominal Yields (Maturity {selected_year})", 
                    f"Inflation Real Yields (Maturity {selected_year})",
                    f"Rolling Correlation (Window: {window_size}d)", 
                    "Fiscal Events Log"
                )
            )

            # --- ROW 1: DI NOMINAL YIELDS ---
            fig.add_trace(go.Scatter(
                x=series_di.index, y=series_di,
                name=f"DI {di_col}",
                line=dict(color='blue', width=2)
            ), row=1, col=1)

            # --- ROW 2: INFLATION REAL YIELDS ---
            fig.add_trace(go.Scatter(
                x=series_inf.index, y=series_inf,
                name=f"Inf {inf_col}",
                line=dict(color='orange', width=2)
            ), row=2, col=1)

            # --- ROW 3: ROLLING CORRELATION ---
            fig.add_trace(go.Scatter(
                x=roll_corr.index, y=roll_corr,
                mode='lines', name='Correlation',
                line=dict(color='#636EFA', width=2),
                fill='tozeroy', fillcolor='rgba(99, 110, 250, 0.1)'
            ), row=3, col=1)

            # Reference Lines for Correlation
            fig.add_shape(type="line", x0=min_date, x1=max_date, y0=0, y1=0, line=dict(color="black", width=1), row=3, col=1)
            fig.add_shape(type="line", x0=min_date, x1=max_date, y0=0.8, y1=0.8, line=dict(color="red", dash="dot"), row=3, col=1)
            fig.add_shape(type="line", x0=min_date, x1=max_date, y0=-0.5, y1=-0.5, line=dict(color="green", dash="dot"), row=3, col=1)
            
            # --- ROW 3: DATA TABLE ---
            fig.add_trace(go.Table(
                header=dict(
                    values=["Date", "Event", "Actual", "Forecast"],
                    fill_color='paleturquoise', align='left', font=dict(size=12, weight='bold')
                ),
                cells=dict(
                    values=[
                        visible_events['Date'].dt.strftime('%Y-%m-%d'),
                        visible_events['Event'],
                        visible_events['Actual'],
                        visible_events['Forecast']
                    ],
                    fill_color='lavender', align='left', height=25
                )
            ), row=3, col=2)

            # --- ADD VERTICAL EVENT LINES TO ALL PLOTS ---
            # We loop through Rows 1, 2, and 3 (Col 1)
            for row_idx in [1, 2, 3]:
                for _, row in visible_events.iterrows():
                    color = 'red' if 'Rate' in row['Event'] or 'Decision' in row['Event'] else 'purple'
                    line_style = 'solid' if 'Rate' in row['Event'] else 'dot'
                    
                    # Add line
                    fig.add_shape(
                        type="line", x0=row['Date'], x1=row['Date'], y0=0, y1=1,
                        xref=f'x{row_idx}', yref=f'paper', # Relative to subplot height
                        line=dict(color=color, width=1, dash=line_style),
                        row=row_idx, col=1
                    )

            # --- LAYOUT UPDATE ---
            fig.update_layout(
                height=1200, # Increased height for 3 rows
                template="plotly_white",
                showlegend=True,
                hovermode="closest",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # Axis Titles
            fig.update_yaxes(title_text="Yield (%)", row=1, col=1)
            fig.update_yaxes(title_text="Yield (%)", row=2, col=1)
            fig.update_yaxes(title_text="Correlation", range=[-1.1, 1.1], row=3, col=1)

            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 Please upload both DI and Inflation Excel files in the sidebar to begin.")
