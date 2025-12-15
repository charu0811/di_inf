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
    {"Date": "2025-09-10", "Event": "CPI (Aug)", "Actual": "5.13%", "Forecast": "5.10%"},
    {"Date": "2025-09-16", "Event": "Unemployment Rate (Jul)", "Actual": "5.6%", "Forecast": "5.7%"},
    {"Date": "2025-09-17", "Event": "Copom Interest Rate Decision", "Actual": "15.00%", "Forecast": "15.00%"},
    {"Date": "2025-09-30", "Event": "Unemployment Rate (Aug)", "Actual": "5.6%", "Forecast": "5.6%"},
    {"Date": "2025-10-09", "Event": "CPI (YoY) (Sep)", "Actual": "5.17%", "Forecast": "5.22%"},
    {"Date": "2025-10-31", "Event": "Unemployment Rate (Sep)", "Actual": "5.6%", "Forecast": "5.5%"},
    {"Date": "2025-11-05", "Event": "Copom Interest Rate Decision", "Actual": "15.00%", "Forecast": "15.00%"},
    {"Date": "2025-11-11", "Event": "CPI (YoY) (Oct)", "Actual": "4.68%", "Forecast": "4.75%"},
    {"Date": "2025-11-28", "Event": "Unemployment Rate (Oct)", "Actual": "5.4%", "Forecast": "5.5%"},
    {"Date": "2025-12-10", "Event": "CPI (YoY) (Nov)", "Actual": "4.46%", "Forecast": "4.49%"},
    {"Date": "2025-12-10", "Event": "Copom Interest Rate Decision", "Actual": "15.00%", "Forecast": "15.00%"}
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
            
            # --- NEW: CALCULATE SPREAD (Inf - DI) ---
            # "Price of Spread A-B is Price of B - Price of A"
            # Here: B=Inflation, A=DI
            series_spread = series_inf - series_di

            # Calculate Rolling Correlation
            di_chg = series_di.diff()
            inf_chg = series_inf.diff()
            roll_corr = di_chg.rolling(window=window_size).corr(inf_chg)

            # Filter Events for Visible Range
            min_date, max_date = roll_corr.index.min(), roll_corr.index.max()
            visible_events = events_df[(events_df['Date'] >= min_date) & (events_df['Date'] <= max_date)]

            # 2. Dynamic Axis Ranges
            di_min, di_max = series_di.min() - 0.2, series_di.max() + 0.2
            inf_min, inf_max = series_inf.min() - 0.2, series_inf.max() + 0.2
            spr_min, spr_max = series_spread.min() - 0.2, series_spread.max() + 0.2

            # 3. Create Subplots Grid (4 Rows)
            # Row 1: DI
            # Row 2: Inflation
            # Row 3: Spread (New)
            # Row 4: Correlation | Table
            fig = make_subplots(
                rows=4, cols=2,
                column_widths=[0.7, 0.3],
                vertical_spacing=0.08,
                specs=[
                    [{"type": "xy", "colspan": 2}, None],  # Row 1
                    [{"type": "xy", "colspan": 2}, None],  # Row 2
                    [{"type": "xy", "colspan": 2}, None],  # Row 3 (Spread)
                    [{"type": "xy"}, {"type": "table"}]    # Row 4
                ],
                subplot_titles=(
                    f"DI Nominal Yields (Maturity {selected_year})", 
                    f"Inflation Real Yields (Maturity {selected_year})",
                    f"Spread (Inflation - DI) (Maturity {selected_year})",
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

            # --- ROW 3: SPREAD (Inf - DI) ---
            fig.add_trace(go.Scatter(
                x=series_spread.index, y=series_spread,
                name=f"Spread (Inf - DI)",
                line=dict(color='green', width=2),
                fill='tozeroy', fillcolor='rgba(0, 128, 0, 0.1)'
            ), row=3, col=1)

            # --- ROW 4: ROLLING CORRELATION ---
            fig.add_trace(go.Scatter(
                x=roll_corr.index, y=roll_corr,
                mode='lines', name='Correlation',
                line=dict(color='#636EFA', width=2),
                fill='tozeroy', fillcolor='rgba(99, 110, 250, 0.1)'
            ), row=4, col=1)

            # Reference Lines for Correlation
            fig.add_shape(type="line", x0=min_date, x1=max_date, y0=0, y1=0, line=dict(color="black", width=1), row=4, col=1)
            fig.add_shape(type="line", x0=min_date, x1=max_date, y0=0.8, y1=0.8, line=dict(color="red", dash="dot"), row=4, col=1)
            fig.add_shape(type="line", x0=min_date, x1=max_date, y0=-0.5, y1=-0.5, line=dict(color="green", dash="dot"), row=4, col=1)
            
            # --- ROW 4: DATA TABLE ---
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
            ), row=4, col=2)

            # --- ADD VERTICAL EVENT LINES TO PLOTS 1, 2, 3 ---
            for row_idx in [1, 2, 3, 4]:
                for _, row in visible_events.iterrows():
                    color = 'red' if 'Rate' in row['Event'] or 'Decision' in row['Event'] else 'purple'
                    line_style = 'solid' if 'Rate' in row['Event'] else 'dot'
                    
                    fig.add_shape(
                        type="line", x0=row['Date'], x1=row['Date'], y0=0, y1=1,
                        xref=f'x{row_idx}', yref=f'paper', 
                        line=dict(color=color, width=1, dash=line_style),
                        row=row_idx, col=1
                    )

            # --- LAYOUT UPDATE ---
            fig.update_layout(
                height=1400, # Increased height for 4 rows
                template="plotly_white",
                showlegend=True,
                hovermode="closest",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # Axis Titles & RANGES
            fig.update_yaxes(title_text="Yield (%)", range=[di_min, di_max], row=1, col=1)
            fig.update_yaxes(title_text="Yield (%)", range=[inf_min, inf_max], row=2, col=1)
            fig.update_yaxes(title_text="Spread (%)", range=[spr_min, spr_max], row=3, col=1)
            fig.update_yaxes(title_text="Correlation", range=[-1.1, 1.1], row=4, col=1)

            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 Please upload both DI and Inflation Excel files in the sidebar to begin.")
