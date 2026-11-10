
import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
import datetime

# --- Constants ---
DATA_FILE = "portfolio.json"

# --- Data Handling ---
def load_data():
    """Loads portfolio data from JSON. Missing or empty file yields an empty dict."""
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                return {}
            data = json.loads(raw)
            if not isinstance(data, dict):
                return {}
            return data
    except (json.JSONDecodeError, IOError):
        return {}

def save_data(data):
    """Saves portfolio data to JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- Simulation Logic ---
def calculate_forecast(current_total_value, current_invested_value, years=20, annual_return=0.07, monthly_contribution=1000):
    """
    Calculates future portfolio value split by Invested vs Interest.
    """
    months = years * 12
    monthly_return = annual_return / 12
    
    forecast_dates = []
    forecast_total = []
    forecast_invested = []
    
    current_val = current_total_value
    current_inv = current_invested_value
    
    start_date = datetime.date.today()
    
    for i in range(months + 1):
        # Date for x-axis
        date = start_date + datetime.timedelta(days=30*i) # Approx month
        forecast_dates.append(date)
        forecast_total.append(current_val)
        forecast_invested.append(current_inv)
        
        # Apply growth and contribution for next month
        current_val = current_val * (1 + monthly_return) + monthly_contribution
        current_inv = current_inv + monthly_contribution
        
    return forecast_dates, forecast_total, forecast_invested

# --- Main App ---
def main():
    st.set_page_config(page_title="Investment Tracker", page_icon="📈", layout="wide")

    # Load Data
    portfolio_data = load_data()

    # --- Sidebar: Operations ---
    st.sidebar.header("Operacje na portfelu")

    account_names = list(portfolio_data.keys())
    if account_names:
        selected_account = st.sidebar.selectbox("Wybierz konto", account_names)
        operation_type = st.sidebar.radio("Typ operacji", ["Wpłata", "Korekta Wyceny"])
        amount = st.sidebar.number_input("Kwota (PLN)", min_value=0.0, step=10.0, format="%.2f")

        if st.sidebar.button("Zatwierdź"):
            if amount > 0 or operation_type == "Korekta Wyceny":
                if operation_type == "Wpłata":
                    portfolio_data[selected_account]["invested"] += amount
                    portfolio_data[selected_account]["value"] += amount
                    st.sidebar.success(f"Wpłacono {amount:,.2f} PLN na {selected_account}")
                elif operation_type == "Korekta Wyceny":
                    old_val = portfolio_data[selected_account]["value"]
                    portfolio_data[selected_account]["value"] = amount
                    st.sidebar.info(
                        f"Zaktualizowano wycenę {selected_account}: {old_val:,.2f} -> {amount:,.2f} PLN"
                    )

                save_data(portfolio_data)
                st.rerun()
    else:
        st.sidebar.info("Brak kont. Dodaj pierwsze konto poniżej.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Nowe konto")
    new_account_name = st.sidebar.text_input("Nazwa nowego konta")

    if st.sidebar.button("Dodaj konto"):
        name = new_account_name.strip()
        if not name:
            st.sidebar.error("Nazwa konta nie może być pusta.")
        elif name in portfolio_data:
            st.sidebar.warning(f"Konto „{name}” już istnieje.")
        else:
            portfolio_data[name] = {"invested": 0.0, "value": 0.0}
            save_data(portfolio_data)
            st.rerun()

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
    
    f_dates, f_total, f_invested = calculate_forecast(total_value, total_invested, years=20, annual_return=annual_return/100, monthly_contribution=monthly_contrib)
    
    # Calculate Interest (Top Layer)
    # We want to stack: Bottom = Invested, Top = Interest.
    # Stacked Total = Invested + Interest = Total Value.
    # So Interest = Total - Invested.
    f_interest = [t - i for t, i in zip(f_total, f_invested)]
    
    # Plotly Chart
    fig = go.Figure()
    
    # 1. Invested Capital (Bottom Layer)
    fig.add_trace(go.Scatter(
        x=f_dates, 
        y=f_invested, 
        mode='lines', 
        name='Wpłaty Własne',
        stackgroup='one', # Enable stacking
        line=dict(width=0, color='gray'), # No line width for area look, or keep it. Let's use gray.
        fillcolor='rgba(128, 128, 128, 0.5)' # Semi-transparent gray
    ))
    
    # 2. Interest (Top Layer)
    fig.add_trace(go.Scatter(
        x=f_dates, 
        y=f_interest, 
        mode='lines', 
        name='Odsetki',
        stackgroup='one',
        line=dict(width=0, color='green'),
        fillcolor='rgba(0, 204, 150, 0.6)' # Semi-transparent green
    ))
    
    fig.update_layout(
        title="Prognoza wartości portfela (Wpłaty vs Odsetki)",
        xaxis_title="Rok",
        yaxis_title="Wartość (PLN)",
        hovermode="x unified",
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
