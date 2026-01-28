
import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import datetime

# --- Constants ---
DATA_FILE = "portfolio.json"
ACCOUNTS = ["Emerytura (IKE/IKZE)", "Poduszka Finansowa", "Obligacje", "Giełda"]

# --- Data Handling ---
def load_data():
    """Loads portfolio data from JSON or returns default structure."""
    if not os.path.exists(DATA_FILE):
        return {acc: {"invested": 0.0, "value": 0.0} for acc in ACCOUNTS}
    
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all accounts exist (migration support if we add accounts later)
            for acc in ACCOUNTS:
                if acc not in data:
                    data[acc] = {"invested": 0.0, "value": 0.0}
            return data
    except (json.JSONDecodeError, IOError):
         return {acc: {"invested": 0.0, "value": 0.0} for acc in ACCOUNTS}

def save_data(data):
    """Saves portfolio data to JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- Simulation Logic ---
def calculate_forecast(current_total_value, years=20, annual_return=0.07, monthly_contribution=1000):
    """
    Calculates future portfolio value based on:
    - current_total_value: Starting amount
    - years: Duration of simulation
    - annual_return: 7% default
    - monthly_contribution: 1000 PLN default
    """
    months = years * 12
    monthly_return = annual_return / 12
    
    forecast_dates = []
    forecast_values = []
    
    current_val = current_total_value
    start_date = datetime.date.today()
    
    for i in range(months + 1):
        # Date for x-axis
        date = start_date + datetime.timedelta(days=30*i) # Approx month
        forecast_dates.append(date)
        forecast_values.append(current_val)
        
        # Apply growth and contribution for next month
        current_val = current_val * (1 + monthly_return) + monthly_contribution
        
    return forecast_dates, forecast_values

# --- Main App ---
def main():
    st.set_page_config(page_title="Investment Tracker", page_icon="📈", layout="wide")

    # Load Data
    portfolio_data = load_data()

    # --- Sidebar: Operations ---
    st.sidebar.header("Operacje na portfelu")
    
    selected_account = st.sidebar.selectbox("Wybierz konto", ACCOUNTS)
    operation_type = st.sidebar.radio("Typ operacji", ["Wpłata", "Korekta Wyceny"])
    amount = st.sidebar.number_input("Kwota (PLN)", min_value=0.0, step=10.0, format="%.2f")
    
    if st.sidebar.button("Zatwierdź"):
        if amount > 0 or operation_type == "Korekta Wyceny": # Allow 0 for correction? Maybe not necessary, but safe check.
            if operation_type == "Wpłata":
                portfolio_data[selected_account]["invested"] += amount
                portfolio_data[selected_account]["value"] += amount
                st.sidebar.success(f"Wpłacono {amount:,.2f} PLN na {selected_account}")
            elif operation_type == "Korekta Wyceny":
                # Only update 'value', leave 'invested' alone
                old_val = portfolio_data[selected_account]["value"]
                portfolio_data[selected_account]["value"] = amount
                st.sidebar.info(f"Zaktualizowano wycenę {selected_account}: {old_val:,.2f} -> {amount:,.2f} PLN")
            
            save_data(portfolio_data)
            st.rerun() # Refresh to show new data immediately

    # --- Main Page ---
    st.title("💰 Investment Tracker & Simulator")

    # 1. Key Metrics Calculation
    total_value = sum(acc["value"] for acc in portfolio_data.values())
    total_invested = sum(acc["invested"] for acc in portfolio_data.values())
    total_profit = total_value - total_invested
    
    # Display Metrics
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Łączna Wartość", f"{total_value:,.2f} PLN")
    col2.metric("Łączny Wpłacony Kapitał", f"{total_invested:,.2f} PLN")
    
    # Color logic for profit
    profit_color = "normal"
    if total_profit > 0:
        profit_color = "normal" # Streamlit metric handles delta color, but here we format manually or use delta
    
    col3.metric(
        "Zysk / Strata", 
        f"{total_profit:,.2f} PLN", 
        delta=f"{total_profit:,.2f} PLN",
        delta_color="normal" # 'normal' means green for positive, red for negative automatically
    )

    st.markdown("---")

    # 2. Detailed Table
    st.subheader("Szczegóły Portfela")
    
    table_data = []
    for acc_name, data in portfolio_data.items():
        val = data["value"]
        inv = data["invested"]
        profit = val - inv
        profit_pct = (profit / inv * 100) if inv > 0 else 0.0
        
        table_data.append({
            "Konto": acc_name,
            "Aktualna Wartość": val,
            "Wpłacony Kapitał": inv,
            "Zysk (PLN)": profit,
            "Zysk (%)": profit_pct
        })
        
    df = pd.DataFrame(table_data)
    
    # Formatting for better display (optional, but requested 'nice table')
    # We can use st.dataframe with column configuration
    st.dataframe(
        df,
        column_config={
            "Aktualna Wartość": st.column_config.NumberColumn(format="%.2f PLN"),
            "Wpłacony Kapitał": st.column_config.NumberColumn(format="%.2f PLN"),
            "Zysk (PLN)": st.column_config.NumberColumn(format="%.2f PLN"),
            "Zysk (%)": st.column_config.NumberColumn(format="%.2f %%"),
        },
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # 3. Simulation Chart
    st.subheader("Symulacja Emerytalna (20 lat)")
    
    # --- Simulation Inputs ---
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        annual_return = st.slider("Oczekiwany roczny zwrot (%)", min_value=1.0, max_value=15.0, value=7.0, step=0.1)
    with col_sim2:
        monthly_contrib = st.number_input("Miesięczna dopłata (PLN)", min_value=0, max_value=5000, value=1000, step=100)

    st.caption(f"Założenia: Wzrost {annual_return}% rocznie, dopłaty {monthly_contrib} zł miesięcznie.")
    
    f_dates, f_values = calculate_forecast(total_value, years=20, annual_return=annual_return/100, monthly_contribution=monthly_contrib)
    
    # Plotly Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=f_dates, 
        y=f_values, 
        mode='lines', 
        name='Prognoza',
        line=dict(color='#00CC96', width=3),
        fill='tozeroy' # Area chart look
    ))
    
    fig.update_layout(
        title="Prognoza wartości portfela",
        xaxis_title="Rok",
        yaxis_title="Wartość (PLN)",
        hovermode="x unified",
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
