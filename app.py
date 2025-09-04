import streamlit as st
import yfinance as yf
import pandas as pd
import locale
from datetime import datetime

# --- Configuración de la página y localización ---
st.set_page_config(
    page_title="Análisis de Activos Financieros",
    page_icon="📊",
    layout="wide"
)
# Configurar locale para español para el nombre del mes
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
    except locale.Error:
        st.warning("No se pudo configurar la localización a español. La fecha podría mostrarse en inglés.")

# --- Título y Fecha ---
st.title("📊 Monitor de Activos Financieros")
today_str = datetime.now().strftime("Datos al %d de %B de %Y")
st.subheader(today_str)


# --- Definición de Listas de Activos ---

# Para la pestaña de Seguimiento General
tracking_assets = {
    "GOOGL": "Alphabet (Google)",
    "META": "Meta Platforms",
    "AMZN": "Amazon",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SOL-USD": "Solana"
}

# Para tu Portafolio Personal (¡Puedes agregar más aquí!)
portfolio_assets = {
    "YPF": "YPF",
    "GGAL": "Grupo Financiero Galicia",
    "MELI": "MercadoLibre"
}

# --- Funciones de Lógica de Datos ---

@st.cache_data(ttl=1800) # Cache por 30 minutos
def get_asset_data(ticker, assets_dict):
    """Obtiene el historial de precios, P/E y calcula los datos necesarios para un activo."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="max")

        if hist.empty:
            st.error(f"No se encontraron datos históricos para {ticker}.")
            return None

        all_time_high = hist['High'].max()
        current_price = hist['Close'].iloc[-1]
        diff_from_max = (current_price - all_time_high) / all_time_high
        pe_ratio = info.get('trailingPE') # Devuelve None si no está disponible (ej. para criptos)

        return {
            "Activo": f"{assets_dict.get(ticker, ticker)} ({ticker})",
            "Precio": current_price,
            "P/E": pe_ratio,
            "MaximoHistorico": all_time_high,
            "DiferenciaDelMax": diff_from_max
        }
    except Exception as e:
        st.error(f"Error obteniendo datos para {ticker}: {e}")
        return None

def create_and_display_table(assets_dict):
    """Crea y muestra una tabla de datos de activos para un diccionario dado."""
    data = []
    tickers = list(assets_dict.keys())
    progress_bar = st.progress(0, text="Obteniendo datos...")

    for i, ticker in enumerate(tickers):
        asset_data = get_asset_data(ticker, assets_dict)
        if asset_data:
            data.append(asset_data)
        progress_bar.progress((i + 1) / len(tickers), text=f"Obteniendo {assets_dict.get(ticker, ticker)}...")
    
    progress_bar.empty()

    if not data:
        st.warning("No se pudieron cargar datos para los activos seleccionados.")
        return

    df = pd.DataFrame(data)

    # --- Formato de Columnas ---
    def format_difference(diff):
        if diff >= -0.001: return "✅ ¡En Máximo Histórico!"
        else: return f"📉 {diff:.2%}"

    df["DiferenciaDelMax"] = df["DiferenciaDelMax"].apply(format_difference)
    df['Precio'] = df['Precio'].map('${:,.2f}'.format)
    df['MaximoHistorico'] = df['MaximoHistorico'].map('${:,.2f}'.format)

    # --- Visualización de la Tabla ---
    st.dataframe(
        df.set_index("Activo"),
        use_container_width=True,
        column_order=["Precio", "P/E", "MaximoHistorico", "DiferenciaDelMax"],
        column_config={
            "P/E": st.column_config.NumberColumn(
                "P/E Ratio",
                help="Price-to-Earnings ratio. N/A si no aplica (ej. criptomonedas).",
                format="%.2f",
                width="small"
            ),
            "DiferenciaDelMax": st.column_config.TextColumn("Diferencia vs. Máximo", width="medium"),
            "Precio": st.column_config.TextColumn("Precio Actual (USD)", width="small"),
            "MaximoHistorico": st.column_config.TextColumn("Máximo Histórico (USD)", width="small"),
        }
    )

# --- Creación de Pestañas ---
tab_seguimiento, tab_portafolio = st.tabs(["Seguimiento", "Portafolio"])

with tab_seguimiento:
    st.header("Seguimiento de Activos Populares")
    create_and_display_table(tracking_assets)

with tab_portafolio:
    st.header("Mi Portafolio Personal")
    st.info("Puedes agregar o quitar activos de esta tabla editando el diccionario `portfolio_assets` en el archivo `app.py`.")
    create_and_display_table(portfolio_assets)

st.caption("Datos obtenidos de Yahoo Finance.")
