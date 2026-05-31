import streamlit as st
from supabase import create_client, Client
from datetime import date
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="DANIMALITOS App", page_icon="🐾", layout="centered")

# Conexión a Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("🐾 Panel DANIMALITOS")
st.markdown("---")

# === CREACIÓN DE PESTAÑAS ===
tab_ingreso, tab_dashboard = st.tabs(["📝 Ingresar Datos", "📊 Resumen Financiero"])

# ==========================================
# PESTAÑA 1: INGRESO DE DATOS
# ==========================================
with tab_ingreso:
    if 'modo' not in st.session_state:
        st.session_state.modo = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ AÑADIR SERVICIO", use_container_width=True):
            st.session_state.modo = "servicio"
    with col2:
        if st.button("📉 AÑADIR GASTO", use_container_width=True):
            st.session_state.modo = "gasto"

    if st.session_state.modo == "servicio":
        st.subheader("Nuevo Servicio / Ecografía")
        with st.form("form_servicio"):
            fecha = st.date_input("Fecha", date.today())
            paciente = st.text_input("Paciente / Tutor")
            servicio = st.text_input("Tipo de Servicio")
            monto = st.number_input("Monto Cobrado ($)", min_value=0, step=1000)
            pago = st.selectbox("Método de Pago", ["Transferencia", "Efectivo", "Tarjeta", "Otro"])
            
            st.markdown("---")
            st.write("¿Hubo gasto de insumo en esta atención?")
            monto_insumo = st.number_input("Ingresa el valor ($). Deja en 0 si no hubo.", min_value=0, step=1000, value=0)
            
            submit = st.form_submit_button("Guardar Registro")
            
            if submit and paciente and servicio and monto > 0:
                data_serv = {"fecha": str(fecha), "paciente": paciente.upper(), "tipo_servicio": servicio, "monto_cobrado": monto, "metodo_pago": pago}
                supabase.table("servicios").insert(data_serv).execute()
                
                if monto_insumo > 0:
                    data_gasto = {"fecha": str(fecha), "descripcion": f"INSUMO ATENCIÓN: {paciente.upper()}", "categoria": "Insumo", "monto_gastado": monto_insumo}
                    supabase.table("gastos").insert(data_gasto).execute()
                    
                st.success("¡Registro guardado exitosamente!")
                st.session_state.modo = None

    elif st.session_state.modo == "gasto":
        st.subheader("Nuevo Gasto Operativo")
        with st.form("form_gasto"):
            fecha = st.date_input("Fecha", date.today())
            descripcion = st.text_input("Descripción")
            categoria = st.selectbox("Categoría", ["Insumo", "Transporte"])
            monto = st.number_input("Monto Gastado ($)", min_value=0, step=1000)
            
            submit = st.form_submit_button("Guardar Gasto")
            
            if submit and descripcion and monto > 0:
                data_gasto = {"fecha": str(fecha), "descripcion": descripcion.upper(), "categoria": categoria, "monto_gastado": monto}
                supabase.table("gastos").insert(data_gasto).execute()
                
                st.success("¡Gasto guardado exitosamente!")
                st.session_state.modo = None

# ==========================================
# PESTAÑA 2: DASHBOARD FINANCIERO
# ==========================================
with tab_dashboard:
    st.subheader("Rendimiento del Negocio")
    
    # Extraer los datos directamente de tu base de datos
    res_servicios = supabase.table("servicios").select("*").execute()
    res_gastos = supabase.table("gastos").select("*").execute()
    
    # Convertir los datos a tablas de Pandas (como si fueran hojas de Excel)
    df_serv = pd.DataFrame(res_servicios.data)
    df_gast = pd.DataFrame(res_gastos.data)
    
    # Calcular los totales
    total_ingresos = df_serv['monto_cobrado'].sum() if not df_serv.empty else 0
    total_gastos = df_gast['monto_gastado'].sum() if not df_gast.empty else 0
    ganancia = total_ingresos - total_gastos
    
    # Mostrar las métricas en grande
    col_ing, col_gas, col_neto = st.columns(3)
    col_ing.metric("Ingresos Totales", f"${total_ingresos:,.0f}".replace(",", "."))
    col_gas.metric("Gastos Totales", f"${total_gastos:,.0f}".replace(",", "."))
    col_neto.metric("Ganancia Neta", f"${ganancia:,.0f}".replace(",", "."))
    
    st.markdown("---")
    
    # Mostrar una pequeña tabla con los últimos servicios ingresados
    if not df_serv.empty:
        st.write("**Últimos Servicios Registrados**")
        df_mostrar = df_serv.sort_values(by="creado_en", ascending=False).head(5) # Muestra los últimos 5
        st.dataframe(df_mostrar[['fecha', 'paciente', 'tipo_servicio', 'monto_cobrado']], use_container_width=True)
    else:
        st.info("Aún no hay datos de servicios para mostrar.")
