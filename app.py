import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Fiscal Correlation Dashboard", layout="wide")
st.title("📊 Systemic Correlation & Curve Analyzer")

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
                                ["Macro (DI vs Inflation)", "Curve Spreads (Intra-Curve)"])

        # ==========================================
        # MODE A: MACRO (DI vs INF) - The Original View
        # ==========================================
        if mode == "Macro (DI vs Inflation)":
            selected_year = st.sidebar.selectbox("Select Maturity Year", years)
            window_size = st.sidebar.slider("Rolling Window (Days)", 10, 120, 60, 5)
            
            if selected_year:
                # [Previous Logic for DI vs Inf]
                di_col = di_map[selected_year]
                inf_col = inf_map[selected_year]
                
                s_di = di_df[di_col]
                s_inf = inf_df[inf_col]
                s_spread = s_inf - s_di # Spread Calculation
                
                # Correlation
                roll_corr = s_di.diff().rolling(window_size).corr(s_inf.diff())
                
                # Filter Events
                min_d, max_d = roll_corr.index.min(), roll_corr.index.max()
                vis_events = events_df[(events_df['Date'] >= min_d) & (events_df['Date'] <= max_d)]
                
                # Axis Ranges
                di_range = [s_di.min()-0.2, s_di.max()+0.2]
                inf_range = [s_inf.min()-0.2, s_inf.max()+0.2]
                spr_range = [s_spread.min()-0.2, s_spread.max()+0.2]

                # Plotting
                fig = make_subplots(
                    rows=4, cols=2, column_widths=[0.7, 0.3], vertical_spacing=0.08,
                    specs=[[{"colspan":2},None], [{"colspan":2},None], [{"colspan":2},None], [{"type":"xy"}, {"type":"table"}]],
                    subplot_titles=(f"DI {di_col}", f"Inflation {inf_col}", "Spread (Inf - DI)", "Rolling Correlation", "Events")
                )
                
                # Traces
                fig.add_trace(go.Scatter(x=s_di.index, y=s_di, name="DI", line=dict(color='blue')), row=1, col=1)
                fig.add_trace(go.Scatter(x=s_inf.index, y=s_inf, name="Inflation", line=dict(color='orange')), row=2, col=1)
                fig.add_trace(go.Scatter(x=s_spread.index, y=s_spread, name="Spread", line=dict(color='green')), row=3, col=1)
                fig.add_trace(go.Scatter(x=roll_corr.index, y=roll_corr, name="Corr", line=dict(color='purple'), fill='tozeroy'), row=4, col=1)
                
                # Table
                fig.add_trace(go.Table(
                    header=dict(values=["Date","Event","Actual"], fill_color='paleturquoise'),
                    cells=dict(values=[vis_events['Date'].dt.date, vis_events['Event'], vis_events['Actual']], fill_color='lavender')
                ), row=4, col=2)
                
                # Add Vertical Lines
                for idx in [1, 2, 3, 4]:
                    for _, r in vis_events.iterrows():
                        c = 'red' if 'Rate' in r['Event'] else 'purple'
                        fig.add_shape(type="line", x0=r['Date'], x1=r['Date'], y0=0, y1=1, xref=f'x{idx}', yref='paper', line=dict(color=c, dash='dot'), row=idx, col=1)

                fig.update_layout(height=1400, showlegend=True, hovermode="closest", template="plotly_white")
                fig.update_yaxes(range=di_range, row=1, col=1)
                fig.update_yaxes(range=inf_range, row=2, col=1)
                fig.update_yaxes(range=spr_range, row=3, col=1)
                fig.update_yaxes(range=[-1.1, 1.1], row=4, col=1)
                
                st.plotly_chart(fig, use_container_width=True)

        # ==========================================
        # MODE B: CURVE SPREADS (INTRA-CURVE) - New!
        # ==========================================
        elif mode == "Curve Spreads (Intra-Curve)":
            st.sidebar.subheader("Build Your Spread")
            
            # 1. Select Asset Class
            curve_type = st.sidebar.radio("Select Curve:", ["DI (Nominal)", "Inflation (Real)"])
            
            # 2. Select Contracts (A - B)
            col1, col2 = st.sidebar.columns(2)
            mat_a = col1.selectbox("Contract A (Long)", years, index=len(years)-1) # Default to Longest
            mat_b = col2.selectbox("Contract B (Short)", years, index=0)           # Default to Shortest
            
            if mat_a and mat_b:
                # Prepare Data
                if curve_type == "DI (Nominal)":
                    col_a, col_b = di_map[mat_a], di_map[mat_b]
                    df_target = di_df
                    color_line = 'blue'
                else:
                    col_a, col_b = inf_map[mat_a], inf_map[mat_b]
                    df_target = inf_df
                    color_line = 'orange'
                
                series_a = df_target[col_a]
                series_b = df_target[col_b]
                
                # Calculate Spread (A - B)
                curve_spread = series_a - series_b
                
                # Filter Events
                min_d, max_d = curve_spread.index.min(), curve_spread.index.max()
                vis_events = events_df[(events_df['Date'] >= min_d) & (events_df['Date'] <= max_d)]
                
                # Dynamic Ranges
                yield_min = min(series_a.min(), series_b.min()) - 0.2
                yield_max = max(series_a.max(), series_b.max()) + 0.2
                spr_min, spr_max = curve_spread.min() - 0.2, curve_spread.max() + 0.2

                # PLOTTING
                fig = make_subplots(
                    rows=3, cols=2, 
                    column_widths=[0.7, 0.3], vertical_spacing=0.1,
                    specs=[
                        [{"colspan": 2}, None], # Row 1: Raw Yields
                        [{"colspan": 2}, None], # Row 2: Spread
                        [None, {"type": "table", "rowspan": 1}] # Row 3: Just Table (or empty left)
                    ],
                    subplot_titles=(
                        f"{curve_type} Yields: {col_a} vs {col_b}", 
                        f"Curve Spread: {col_a} - {col_b} (Steepener/Flattener)",
                        "Fiscal Events Log"
                    )
                )
                
                # Row 1: Raw Yields (Comparison)
                fig.add_trace(go.Scatter(x=series_a.index, y=series_a, name=f"{col_a}", line=dict(color=color_line, width=2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=series_b.index, y=series_b, name=f"{col_b}", line=dict(color='gray', width=2, dash='dot')), row=1, col=1)
                
                # Row 2: The Spread
                fig.add_trace(go.Scatter(
                    x=curve_spread.index, y=curve_spread, 
                    name=f"Spread ({col_a}-{col_b})", 
                    line=dict(color='green', width=2),
                    fill='tozeroy', fillcolor='rgba(0, 128, 0, 0.1)'
                ), row=2, col=1)
                
                # Row 3: Table (Right side, Left side empty for spacing)
                fig.add_trace(go.Table(
                    header=dict(values=["Date", "Event", "Actual"], fill_color='paleturquoise'),
                    cells=dict(values=[vis_events['Date'].dt.date, vis_events['Event'], vis_events['Actual']], fill_color='lavender')
                ), row=3, col=2)

                # Add Vertical Lines (Rows 1 & 2)
                for idx in [1, 2]:
                    for _, r in vis_events.iterrows():
                        c = 'red' if 'Rate' in r['Event'] else 'purple'
                        fig.add_shape(type="line", x0=r['Date'], x1=r['Date'], y0=0, y1=1, xref=f'x{idx}', yref='paper', line=dict(color=c, dash='dot', width=1), row=idx, col=1)

                fig.update_layout(height=1000, template="plotly_white", hovermode="closest", showlegend=True)
                
                # Axis Updates
                fig.update_yaxes(title_text="Yield (%)", range=[yield_min, yield_max], row=1, col=1)
                fig.update_yaxes(title_text="Spread (bps/%)", range=[spr_min, spr_max], row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 Please upload both DI and Inflation Excel files in the sidebar.")
