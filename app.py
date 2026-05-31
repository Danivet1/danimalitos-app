import streamlit as st
from supabase import create_client, Client
from datetime import date

# Configuración de la página para que se adapte perfectamente al celular
st.set_page_config(page_title="DANIMALITOS App", page_icon="🐾", layout="centered")

# Conexión automática a Supabase usando el archivo secrets.toml
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# Diseño de la Interfaz
st.title("🐾 Panel DANIMALITOS")
st.markdown("---")

# Memoria de la app para saber qué formulario mostrar
if 'modo' not in st.session_state:
    st.session_state.modo = None

# Botones principales interactivos
col1, col2 = st.columns(2)
with col1:
    if st.button("➕ AÑADIR SERVICIO", use_container_width=True):
        st.session_state.modo = "servicio"
with col2:
    if st.button("📉 AÑADIR GASTO", use_container_width=True):
        st.session_state.modo = "gasto"

# FORMULARIO 1: SERVICIOS CON INGRESO DE INSUMO AUTOMÁTICO
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
            # 1. Guarda el ingreso en la tabla servicios
            data_serv = {"fecha": str(fecha), "paciente": paciente.upper(), "tipo_servicio": servicio, "monto_cobrado": monto, "metodo_pago": pago}
            supabase.table("servicios").insert(data_serv).execute()
            
            # 2. Si hubo gasto de insumo, lo guarda automáticamente en la tabla gastos
            if monto_insumo > 0:
                data_gasto = {"fecha": str(fecha), "descripcion": f"INSUMO ATENCIÓN: {paciente.upper()}", "categoria": "Insumo", "monto_gastado": monto_insumo}
                supabase.table("gastos").insert(data_gasto).execute()
                
            st.success("¡Registro guardado exitosamente!")
            st.session_state.modo = None

# FORMULARIO 2: GASTOS SUELTOS (Transporte, compras generales)
elif st.session_state.modo == "gasto":
    st.subheader("Nuevo Gasto Operativo")
    with st.form("form_gasto"):
        fecha = st.date_input("Fecha", date.today())
        descripcion = st.text_input("Descripción (Ej: Bencina, Compra de guantes)")
        categoria = st.selectbox("Categoría", ["Insumo", "Transporte"])
        monto = st.number_input("Monto Gastado ($)", min_value=0, step=1000)
        
        submit = st.form_submit_button("Guardar Gasto")
        
        if submit and descripcion and monto > 0:
            data_gasto = {"fecha": str(fecha), "descripcion": descripcion.upper(), "categoria": categoria, "monto_gastado": monto}
            supabase.table("gastos").insert(data_gasto).execute()
            
            st.success("¡Gasto guardado exitosamente!")
            st.session_state.modo = None