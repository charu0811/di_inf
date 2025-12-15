import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Fiscal Correlation Dashboard", layout="wide")
st.title("📊 Systemic Correlation & Multi-Spread Analyzer")

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
# 3. DATA LOADING
# ==========================================
@st.cache_data
def load_data(di_file, inf_file):
    try:
        di_df = pd.read_excel(di_file, index_col=0)
        inf_df = pd.read_excel(inf_file, index_col=0)
        
        for df in [di_df, inf_df]:
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)
            
        common_idx = di_df.index.intersection(inf_df.index)
        return di_df.loc[common_idx], inf_df.loc[common_idx]
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

def get_year(col):
    try: return 2000 + int(col[-2:])
    except: return None

# ==========================================
# 4. SIDEBAR CONFIG
# ==========================================
st.sidebar.header("📁 Data Input")
uploaded_di = st.sidebar.file_uploader("Upload DI Data (.xlsx)", type=['xlsx'])
uploaded_inf = st.sidebar.file_uploader("Upload Inflation Data (.xlsx)", type=['xlsx'])

if uploaded_di and uploaded_inf:
    di_df, inf_df = load_data(uploaded_di, uploaded_inf)
    
    if di_df is not None:
        # Generate Year Mapping
        di_map = {get_year(c): c for c in di_df.columns if get_year(c)}
        inf_map = {get_year(c): c for c in inf_df.columns if get_year(c)}
        years = sorted(list(set(di_map.keys()) & set(inf_map.keys())))

        st.sidebar.divider()
        st.sidebar.header("⚙️ Dashboard Mode")
        
        # --- MODE SELECTOR ---
        mode = st.sidebar.radio("Select Analysis Type:", 
                                ["Macro (DI vs Inflation)", 
                                 "Multi-Spread Correlation"])

        # ==========================================
        # MODE A: MACRO (DI vs INF) - Classic View
        # ==========================================
        if mode == "Macro (DI vs Inflation)":
            selected_year = st.sidebar.selectbox("Select Maturity Year", years)
            window_size = st.sidebar.slider("Rolling Window (Days)", 10, 120, 60, 5)
            
            if selected_year:
                di_col = di_map[selected_year]
                inf_col = inf_map[selected_year]
                
                s_di = di_df[di_col]
                s_inf = inf_df[inf_col]
                
                # Correlation
                roll_corr = s_di.diff().rolling(window_size).corr(s_inf.diff())
                
                # Filter Events
                min_d, max_d = roll_corr.index.min(), roll_corr.index.max()
                vis_events = events_df[(events_df['Date'] >= min_d) & (events_df['Date'] <= max_d)]
                
                # Plotting
                fig = make_subplots(
                    rows=3, cols=2, column_widths=[0.7, 0.3], vertical_spacing=0.1,
                    specs=[[{"colspan":2},None], [{"colspan":2},None], [{"type":"xy"}, {"type":"table"}]],
                    subplot_titles=(f"DI Nominal ({di_col})", f"Inflation Real ({inf_col})", f"Correlation (Rolling {window_size}d)", "Events")
                )
                
                fig.add_trace(go.Scatter(x=s_di.index, y=s_di, name="DI", line=dict(color='blue')), row=1, col=1)
                fig.add_trace(go.Scatter(x=s_inf.index, y=s_inf, name="Inflation", line=dict(color='orange')), row=2, col=1)
                fig.add_trace(go.Scatter(x=roll_corr.index, y=roll_corr, name="Corr", line=dict(color='purple'), fill='tozeroy'), row=3, col=1)
                
                # Table with FORECAST
                fig.add_trace(go.Table(
                    header=dict(values=["Date", "Event", "Actual", "Forecast"], fill_color='paleturquoise'),
                    cells=dict(values=[
                        vis_events['Date'].dt.date, 
                        vis_events['Event'], 
                        vis_events['Actual'],
                        vis_events['Forecast']
                    ], fill_color='lavender')
                ), row=3, col=2)
                
                # Event Lines
                for idx in [1, 2, 3]:
                    for _, r in vis_events.iterrows():
                        c = 'red' if 'Rate' in r['Event'] else 'purple'
                        fig.add_shape(type="line", x0=r['Date'], x1=r['Date'], y0=0, y1=1, xref=f'x{idx}', yref='paper', line=dict(color=c, dash='dot'), row=idx, col=1)

                fig.update_layout(height=1000, template="plotly_white", hovermode="closest", showlegend=True)
                fig.update_yaxes(title="Yield %", row=1, col=1)
                fig.update_yaxes(title="Yield %", row=2, col=1)
                fig.update_yaxes(range=[-1.1, 1.1], row=3, col=1)
                st.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # MODE B: MULTI-SPREAD CORRELATION
        # ==========================================
        elif mode == "Multi-Spread Correlation":
            st.sidebar.subheader("Build Spread X")
            col1, col2, col3 = st.sidebar.columns(3)
            asset_x = col1.selectbox("Asset X", ["DI (Nominal)", "Inflation (Real)"], key='ax')
            mat_x_long = col2.selectbox("Long", years, index=len(years)-1, key='xl')
            mat_x_short = col3.selectbox("Short", years, index=0, key='xs')

            st.sidebar.subheader("Build Spread Y")
            col4, col5, col6 = st.sidebar.columns(3)
            asset_y = col4.selectbox("Asset Y", ["DI (Nominal)", "Inflation (Real)"], index=1, key='ay')
            mat_y_long = col5.selectbox("Long", years, index=len(years)-1, key='yl')
            mat_y_short = col6.selectbox("Short", years, index=0, key='ys')
            
            window_size = st.sidebar.slider("Rolling Window", 10, 120, 60)

            # Calculation
            # Spread X
            df_x = di_df if "DI" in asset_x else inf_df
            map_x = di_map if "DI" in asset_x else inf_map
            spread_x = df_x[map_x[mat_x_long]] - df_x[map_x[mat_x_short]]
            name_x = f"{asset_x.split()[0]} {mat_x_long}s/{mat_x_short}s"

            # Spread Y
            df_y = di_df if "DI" in asset_y else inf_df
            map_y = di_map if "DI" in asset_y else inf_map
            spread_y = df_y[map_y[mat_y_long]] - df_y[map_y[mat_y_short]]
            name_y = f"{asset_y.split()[0]} {mat_y_long}s/{mat_y_short}s"

            # Correlation of Spread Changes
            roll_corr = spread_x.diff().rolling(window_size).corr(spread_y.diff())

            # Events
            min_d, max_d = roll_corr.index.min(), roll_corr.index.max()
            vis_events = events_df[(events_df['Date'] >= min_d) & (events_df['Date'] <= max_d)]

            # Plotting
            fig = make_subplots(
                rows=3, cols=2, column_widths=[0.7, 0.3], vertical_spacing=0.1,
                specs=[
                    [{"colspan": 2}, None], # Row 1: Spread X
                    [{"colspan": 2}, None], # Row 2: Spread Y
                    [{"type": "xy"}, {"type": "table"}] # Row 3: Correlation & Table
                ],
                subplot_titles=(f"Spread X: {name_x}", f"Spread Y: {name_y}", f"Correlation ({name_x} vs {name_y})", "Events")
            )

            # Traces
            fig.add_trace(go.Scatter(x=spread_x.index, y=spread_x, name=name_x, line=dict(color='blue')), row=1, col=1)
            fig.add_trace(go.Scatter(x=spread_y.index, y=spread_y, name=name_y, line=dict(color='green')), row=2, col=1)
            fig.add_trace(go.Scatter(x=roll_corr.index, y=roll_corr, name="Correlation", line=dict(color='purple'), fill='tozeroy'), row=3, col=1)

            # Table with FORECAST
            fig.add_trace(go.Table(
                header=dict(values=["Date", "Event", "Actual", "Forecast"], fill_color='paleturquoise'),
                cells=dict(values=[
                    vis_events['Date'].dt.date, 
                    vis_events['Event'], 
                    vis_events['Actual'],
                    vis_events['Forecast']
                ], fill_color='lavender')
            ), row=3, col=2)

            # Event Lines
            for idx in [1, 2, 3]:
                for _, r in vis_events.iterrows():
                    c = 'red' if 'Rate' in r['Event'] else 'purple'
                    fig.add_shape(type="line", x0=r['Date'], x1=r['Date'], y0=0, y1=1, xref=f'x{idx}', yref='paper', line=dict(color=c, dash='dot'), row=idx, col=1)

            # Dynamic Ranges
            fig.update_yaxes(range=[spread_x.min()-0.1, spread_x.max()+0.1], title="Spread %", row=1, col=1)
            fig.update_yaxes(range=[spread_y.min()-0.1, spread_y.max()+0.1], title="Spread %", row=2, col=1)
            fig.update_yaxes(range=[-1.1, 1.1], title="Correlation", row=3, col=1)

            fig.update_layout(height=1200, template="plotly_white", hovermode="closest", showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 Please upload both DI and Inflation Excel files in the sidebar.")
