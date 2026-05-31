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
# PESTAÑA 2: DASHBOARD FINANCIERO MENSUAL
# ==========================================
with tab_dashboard:
    st.subheader("Rendimiento del Negocio por Mes")
    
    # Extraer los datos de la base de datos
    res_servicios = supabase.table("servicios").select("*").execute()
    res_gastos = supabase.table("gastos").select("*").execute()
    
    # Convertir a DataFrames de Pandas
    df_serv = pd.DataFrame(res_servicios.data)
    df_gast = pd.DataFrame(res_gastos.data)
    
    # Verificar si hay al menos un dato en alguna tabla
    if not df_serv.empty or not df_gast.empty:
        
        # 1. Preparar las fechas (Lógica de Tabla Dinámica)
        if not df_serv.empty:
            df_serv['fecha'] = pd.to_datetime(df_serv['fecha'])
            df_serv['Periodo'] = df_serv['fecha'].dt.strftime('%Y-%m') # Formato: 2026-05
        
        if not df_gast.empty:
            df_gast['fecha'] = pd.to_datetime(df_gast['fecha'])
            df_gast['Periodo'] = df_gast['fecha'].dt.strftime('%Y-%m')

        # 2. Consolidar una lista única de todos los meses existentes
        periodos_serv = df_serv['Periodo'].unique().tolist() if not df_serv.empty else []
        periodos_gast = df_gast['Periodo'].unique().tolist() if not df_gast.empty else []
        todos_los_periodos = sorted(list(set(periodos_serv + periodos_gast)), reverse=True)

        if todos_los_periodos:
            # 3. Crear el Segmentador (Filtro desplegable)
            mes_seleccionado = st.selectbox("📅 Selecciona el mes a visualizar:", todos_los_periodos)

            # 4. Filtrar las tablas según el mes elegido
            df_serv_filtrado = df_serv[df_serv['Periodo'] == mes_seleccionado] if not df_serv.empty else pd.DataFrame()
            df_gast_filtrado = df_gast[df_gast['Periodo'] == mes_seleccionado] if not df_gast.empty else pd.DataFrame()

            # 5. Calcular los totales del mes
            ingresos_mes = df_serv_filtrado['monto_cobrado'].sum() if not df_serv_filtrado.empty else 0
            gastos_mes = df_gast_filtrado['monto_gastado'].sum() if not df_gast_filtrado.empty else 0
            ganancia_mes = ingresos_mes - gastos_mes
            
            # Mostrar las métricas
            col_ing, col_gas, col_neto = st.columns(3)
            col_ing.metric("Ingresos", f"${ingresos_mes:,.0f}".replace(",", "."))
            col_gas.metric("Gastos Operativos", f"${gastos_mes:,.0f}".replace(",", "."))
            col_neto.metric("Ganancia Neta", f"${ganancia_mes:,.0f}".replace(",", "."))
            
            st.markdown("---")
            
            # Mostrar el detalle de atenciones solo de ese mes
            if not df_serv_filtrado.empty:
                st.write(f"**Detalle de Servicios - {mes_seleccionado}**")
                # Ocultar columnas técnicas y ordenar por fecha
                df_mostrar = df_serv_filtrado[['fecha', 'paciente', 'tipo_servicio', 'monto_cobrado', 'metodo_pago']].sort_values(by="fecha", ascending=False)
                # Formatear la fecha para que se vea bonita en la tabla sin la hora
                df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime('%d-%m-%Y')
                st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            else:
                st.info("No hay servicios registrados en este mes.")
        else:
            st.info("No hay fechas válidas para armar el filtro.")
    else:
        st.info("Aún no hay datos en el sistema. ¡Ingresa el primer registro para ver el panel mensual!")
