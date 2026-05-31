import streamlit as st
from supabase import create_client, Client
from datetime import date
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="DANIMALITOS App", page_icon="🐾", layout="centered")

# === SISTEMA DE SEGURIDAD (CANDADO) ===
def check_password():
    """Verifica si el usuario ingresó la contraseña correcta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.warning("🔒 Aplicación Privada")
        st.text_input("Ingresa la contraseña de acceso:", type="password", key="password")
        
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        elif st.session_state["password"] != "":
            st.error("Contraseña incorrecta.")
        return False
    return True

if not check_password():
    st.stop()  # Detiene la aplicación aquí si no hay clave
# =======================================

# Conexión a Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

st.title("🐾 Panel DANIMALITOS")
st.markdown("---")

# === CREACIÓN DE PESTAÑAS (3 Pestañas ahora) ===
tab_ingreso, tab_dashboard, tab_edicion = st.tabs(["📝 Ingresar Datos", "📊 Resumen Financiero", "🔧 Editar / Eliminar"])

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
                st.rerun()

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
                st.rerun()

# ==========================================
# PESTAÑA 2: DASHBOARD FINANCIERO MENSUAL
# ==========================================
with tab_dashboard:
    st.subheader("Rendimiento del Negocio por Mes")
    
    res_servicios = supabase.table("servicios").select("*").execute()
    res_gastos = supabase.table("gastos").select("*").execute()
    
    df_serv = pd.DataFrame(res_servicios.data)
    df_gast = pd.DataFrame(res_gastos.data)
    
    if not df_serv.empty or not df_gast.empty:
        if not df_serv.empty:
            df_serv['fecha'] = pd.to_datetime(df_serv['fecha'])
            df_serv['Periodo'] = df_serv['fecha'].dt.strftime('%Y-%m')
        
        if not df_gast.empty:
            df_gast['fecha'] = pd.to_datetime(df_gast['fecha'])
            df_gast['Periodo'] = df_gast['fecha'].dt.strftime('%Y-%m')

        periodos_serv = df_serv['Periodo'].unique().tolist() if not df_serv.empty else []
        periodos_gast = df_gast['Periodo'].unique().tolist() if not df_gast.empty else []
        todos_los_periodos = sorted(list(set(periodos_serv + periodos_gast)), reverse=True)

        if todos_los_periodos:
            mes_seleccionado = st.selectbox("📅 Selecciona el mes a visualizar:", todos_los_periodos)

            df_serv_filtrado = df_serv[df_serv['Periodo'] == mes_seleccionado] if not df_serv.empty else pd.DataFrame()
            df_gast_filtrado = df_gast[df_gast['Periodo'] == mes_seleccionado] if not df_gast.empty else pd.DataFrame()

            ingresos_mes = df_serv_filtrado['monto_cobrado'].sum() if not df_serv_filtrado.empty else 0
            gastos_mes = df_gast_filtrado['monto_gastado'].sum() if not df_gast_filtrado.empty else 0
            ganancia_mes = ingresos_mes - gastos_mes
            
            col_ing, col_gas, col_neto = st.columns(3)
            col_ing.metric("Ingresos", f"${ingresos_mes:,.0f}".replace(",", "."))
            col_gas.metric("Gastos Operativos", f"${gastos_mes:,.0f}".replace(",", "."))
            col_neto.metric("Ganancia Neta", f"${ganancia_mes:,.0f}".replace(",", "."))
            
            st.markdown("---")
            
            if not df_serv_filtrado.empty:
                st.write(f"**Detalle de Servicios - {mes_seleccionado}**")
                df_mostrar = df_serv_filtrado[['fecha', 'paciente', 'tipo_servicio', 'monto_cobrado', 'metodo_pago']].sort_values(by="fecha", ascending=False)
                df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime('%d-%m-%Y')
                st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
            else:
                st.info("No hay servicios registrados en este mes.")
        else:
            st.info("No hay fechas válidas para armar el filtro.")
    else:
        st.info("Aún no hay datos en el sistema.")

# ==========================================
# PESTAÑA 3: MODIFICAR / ELIMINAR REGISTROS
# ==========================================
with tab_edicion:
    st.subheader("Administración de Registros")
    tipo_gestion = st.radio("¿Qué tipo de registro deseas modificar?", ["Servicios / Ingresos", "Gastos"], horizontal=True)

    if tipo_gestion == "Servicios / Ingresos":
        res_s = supabase.table("servicios").select("*").execute()
        df_s = pd.DataFrame(res_s.data)
        
        if not df_s.empty:
            # Opción visual limpia para escoger la fila exacta
            df_s['opcion_busqueda'] = df_s['fecha'].astype(str) + " | " + df_s['paciente'] + " ($" + df_s['monto_cobrado'].astype(str) + ")"
            lista_opciones = df_s['opcion_busqueda'].tolist()
            seleccionado = st.selectbox("Busca y selecciona el registro a cambiar:", lista_opciones)
            
            # Extraer la información actual de la fila elegida
            fila_s = df_s[df_s['opcion_busqueda'] == seleccionado].iloc[0]
            id_registro = fila_s['id']
            
            with st.form("form_editar_servicio"):
                st.write("✏️ **Modifica los campos necesarios:**")
                edit_fecha = st.date_input("Fecha", pd.to_datetime(fila_s['fecha']))
                edit_paciente = st.text_input("Paciente / Tutor", value=fila_s['paciente'])
                edit_servicio = st.text_input("Tipo de Servicio", value=fila_s['tipo_servicio'])
                edit_monto = st.number_input("Monto Cobrado ($)", min_value=0, step=1000, value=int(fila_s['monto_cobrado']))
                edit_pago = st.selectbox("Método de Pago", ["Transferencia", "Efectivo", "Tarjeta", "Otro"], index=["Transferencia", "Efectivo", "Tarjeta", "Otro"].index(fila_s['metodo_pago']) if fila_s['metodo_pago'] in ["Transferencia", "Efectivo", "Tarjeta", "Otro"] else 0)
                
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    guardar_cambios = st.form_submit_button("💾 Actualizar Registro", use_container_width=True)
                with col_btn2:
                    eliminar_registro = st.form_submit_button("🗑️ Eliminar por Completo", use_container_width=True)
                
                if guardar_cambios:
                    supabase.table("servicios").update({
                        "fecha": str(edit_fecha),
                        "paciente": edit_paciente.upper(),
                        "tipo_servicio": edit_servicio,
                        "monto_cobrado": edit_monto,
                        "metodo_pago": edit_pago
                    }).eq("id", id_registro).execute()
                    st.success("¡Registro actualizado con éxito!")
                    st.rerun()
                    
                if eliminar_registro:
                    supabase.table("servicios").delete().eq("id", id_registro).execute()
                    st.warning("El registro ha sido eliminado.")
                    st.rerun()
        else:
            st.info("No hay servicios disponibles para editar.")

    else:
        res_g = supabase.table("gastos").select("*").execute()
        df_g = pd.DataFrame(res_g.data)
        
        if not df_g.empty:
            df_g['opcion_busqueda'] = df_g['fecha'].astype(str) + " | " + df_g['descripcion'] + " ($" + df_g['monto_gastado'].astype(str) + ")"
            lista_opciones_g = df_g['opcion_busqueda'].tolist()
            seleccionado_g = st.selectbox("Busca y selecciona el gasto a cambiar:", lista_opciones_g)
            
            fila_g = df_g[df_g['opcion_busqueda'] == seleccionado_g].iloc[0]
            id_gasto = fila_g['id']
            
            with st.form("form_editar_gasto"):
                st.write("✏️ **Modifica los campos necesarios:**")
                edit_fecha_g = st.date_input("Fecha", pd.to_datetime(fila_g['fecha']))
                edit_desc_g = st.text_input("Descripción", value=fila_g['descripcion'])
                edit_cat_g = st.selectbox("Categoría", ["Insumo", "Transporte"], index=["Insumo", "Transporte"].index(fila_g['categoria']) if fila_g['categoria'] in ["Insumo", "Transporte"] else 0)
                edit_monto_g = st.number_input("Monto Gastado ($)", min_value=0, step=1000, value=int(fila_g['monto_gastado']))
                
                st.markdown("---")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    guardar_cambios_g = st.form_submit_button("💾 Actualizar Gasto", use_container_width=True)
                with col_g2:
                    eliminar_gasto = st.form_submit_button("🗑️ Eliminar Gasto", use_container_width=True)
                
                if guardar_cambios_g:
                    supabase.table("gastos").update({
                        "fecha": str(edit_fecha_g),
                        "descripcion": edit_desc_g.upper(),
                        "categoria": edit_cat_g,
                        "monto_gastado": edit_monto_g
                    }).eq("id", id_gasto).execute()
                    st.success("¡Gasto actualizado con éxito!")
                    st.rerun()
                    
                if eliminar_gasto:
                    supabase.table("gastos").delete().eq("id", id_gasto).execute()
                    st.warning("El gasto ha sido eliminado.")
                    st.rerun()
        else:
            st.info("No hay gastos disponibles para editar.")
