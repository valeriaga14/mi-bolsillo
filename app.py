import datetime as dt
from contextlib import contextmanager
from decimal import Decimal

import oracledb
import streamlit as st

st.set_page_config(page_title='Mi Bolsillo', page_icon='💰', layout='wide')
st.title('💰 Mi Bolsillo')
st.caption('Control de ingresos y gastos · Datos almacenados y consultados en Oracle SQL')

@st.cache_resource
def pool():
    c = st.secrets['oracle']
    kw = {}
    if c.get('config_dir'):
        kw['config_dir'] = c['config_dir']
    if c.get('wallet_location'):
        kw['wallet_location'] = c['wallet_location']
    if c.get('wallet_password'):
        kw['wallet_password'] = c['wallet_password']
    return oracledb.create_pool(user=c['user'], password=c['password'], dsn=c['dsn'], min=1, max=3, **kw)

@contextmanager
def conexion(escritura=False):
    con = pool().acquire()
    try:
        yield con
        if escritura:
            con.commit()
    except Exception:
        if escritura:
            con.rollback()
        raise
    finally:
        con.close()

def consulta(sql, **params):
    with conexion() as con:
        with con.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0].lower() for d in cur.description]
            return [dict(zip(cols, fila)) for fila in cur.fetchmany(500)]

def ejecutar(sql, **params):
    with conexion(escritura=True) as con:
        with con.cursor() as cur:
            cur.execute(sql, params)

def pesos(valor):
    return '$' + f'{Decimal(valor or 0):,.0f}'.replace(',', '.')

def fecha_id(fecha):
    dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    with conexion(escritura=True) as con:
        with con.cursor() as cur:
            cur.execute('SELECT t_id_tiempo FROM dim_tiempo WHERE t_fecha = :f', f=fecha)
            fila = cur.fetchone()
            if fila:
                return int(fila[0])
            cur.execute('''INSERT INTO dim_tiempo(t_fecha,t_dia,t_mes,"T_AÑO",t_trimestre,t_dia_semana)
                VALUES (:f,:dia,:mes,:anio,:trim,:sem)''', f=fecha, dia=fecha.day, mes=fecha.month,
                anio=fecha.year, trim=(fecha.month-1)//3+1, sem=dias[fecha.weekday()])
            cur.execute('SELECT t_id_tiempo FROM dim_tiempo WHERE t_fecha=:f', f=fecha)
            return int(cur.fetchone()[0])

try:
    usuarios = consulta("SELECT u_id_usuario AS id, u_nombre AS nombre FROM dim_usuario WHERE u_estado='Activo' ORDER BY u_nombre")
except Exception as e:
    st.error(f'No fue posible conectar con Oracle: {e}')
    st.info('Verifica secrets.toml y ejecuta los scripts SQL 01 y 02.')
    st.stop()

seccion = st.sidebar.radio('Menú', ['📊 Resumen','➕ Registrar movimiento','📋 Movimientos','👤 Usuarios','🏷️ Categorías'])
if usuarios:
    etiquetas = {int(x['id']):x['nombre'] for x in usuarios}
    usuario = st.sidebar.selectbox('Usuario', list(etiquetas), format_func=lambda x: etiquetas[x])
else:
    usuario = None
    st.sidebar.info('Primero registra un usuario.')

if seccion == '👤 Usuarios':
    st.subheader('Registrar usuario')
    with st.form('usuario'):
        nombre = st.text_input('Nombre')
        correo = st.text_input('Correo electrónico')
        ciudad = st.text_input('Ciudad (opcional)')
        guardar = st.form_submit_button('Guardar usuario')
    if guardar:
        if not nombre.strip() or '@' not in correo:
            st.warning('Ingresa nombre y correo válido.')
        else:
            try:
                ejecutar('INSERT INTO dim_usuario(u_nombre,u_correo,u_ciudad,u_fecha_registro,u_estado) VALUES (:n,:c,:ci,SYSDATE,\'Activo\')', n=nombre.strip(),c=correo.strip(),ci=ciudad.strip() or None)
                st.success('Usuario registrado. Actualiza la página para seleccionarlo.')
            except oracledb.IntegrityError:
                st.error('El correo ya está registrado.')
    st.dataframe(consulta('SELECT u_nombre AS nombre,u_correo AS correo,u_ciudad AS ciudad,u_estado AS estado FROM dim_usuario ORDER BY u_id_usuario DESC'),hide_index=True)

elif seccion == '🏷️ Categorías':
    st.subheader('Crear categoría')
    with st.form('categoria'):
        nombre = st.text_input('Nombre de categoría')
        tipo = st.selectbox('Tipo',['Gasto','Ingreso'])
        descripcion = st.text_input('Descripción (opcional)')
        guardar = st.form_submit_button('Guardar categoría')
    if guardar:
        if not nombre.strip():
            st.warning('Escribe el nombre.')
        else:
            try:
                ejecutar('INSERT INTO dim_categoria(c_nombre,c_tipo,c_descripcion) VALUES (:n,:t,:d)',n=nombre.strip(),t=tipo,d=descripcion.strip() or None)
                st.success('Categoría guardada.')
            except oracledb.IntegrityError:
                st.error('Ya existe una categoría con ese nombre.')
    st.dataframe(consulta('SELECT c_nombre AS nombre,c_tipo AS tipo,c_descripcion AS descripcion FROM dim_categoria ORDER BY c_tipo,c_nombre'),hide_index=True)

elif usuario is None:
    st.warning('Registra un usuario en la sección Usuarios.')

elif seccion == '➕ Registrar movimiento':
    st.subheader('Nuevo ingreso o gasto')
    categorias = consulta('SELECT c_id_categoria AS id,c_nombre AS nombre,c_tipo AS tipo FROM dim_categoria ORDER BY c_tipo,c_nombre')
    if not categorias:
        st.warning('Primero crea una categoría.')
    else:
        opciones = {int(x['id']):f"{x['tipo']} · {x['nombre']}" for x in categorias}
        with st.form('movimiento',clear_on_submit=True):
            categoria = st.selectbox('Categoría',list(opciones),format_func=lambda x: opciones[x])
            monto = st.number_input('Monto (COP)',min_value=1.0,step=1000.0)
            fecha = st.date_input('Fecha',dt.date.today())
            metodo = st.selectbox('Método de pago',['Efectivo','Tarjeta débito','Tarjeta crédito','Transferencia'])
            descripcion = st.text_input('Descripción (opcional)')
            guardar = st.form_submit_button('Registrar movimiento')
        if guardar:
            try:
                tid = fecha_id(fecha)
                ejecutar('''INSERT INTO fact_transaccion(tr_id_usuario,tr_id_categoria,tr_id_tiempo,tr_monto,tr_metodo_pago,tr_descripcion)
                    VALUES (:u,:c,:t,:m,:p,:d)''',u=usuario,c=categoria,t=tid,m=Decimal(str(monto)),p=metodo,d=descripcion.strip() or None)
                st.success('Movimiento guardado en Oracle.')
            except Exception as e:
                st.error(f'No se pudo guardar: {e}')

elif seccion == '📋 Movimientos':
    st.subheader('Consultar movimientos')
    tipos = st.selectbox('Tipo',['Todos','Ingreso','Gasto'])
    filas = consulta('''SELECT t.t_fecha AS fecha,c.c_tipo AS tipo,c.c_nombre AS categoria,
        f.tr_monto AS monto,f.tr_metodo_pago AS metodo,f.tr_descripcion AS descripcion
        FROM fact_transaccion f JOIN dim_categoria c ON c.c_id_categoria=f.tr_id_categoria
        JOIN dim_tiempo t ON t.t_id_tiempo=f.tr_id_tiempo
        WHERE f.tr_id_usuario=:u AND (:tipo='Todos' OR c.c_tipo=:tipo)
        ORDER BY t.t_fecha DESC,f.tr_id_transaccion DESC FETCH FIRST 200 ROWS ONLY''',u=usuario,tipo=tipos)
    st.dataframe(filas,hide_index=True)

elif seccion == '📊 Resumen':
    st.subheader('Tu resumen financiero')
    totales = consulta('''SELECT NVL(SUM(CASE WHEN c.c_tipo='Ingreso' THEN f.tr_monto ELSE 0 END),0) AS ingresos,
        NVL(SUM(CASE WHEN c.c_tipo='Gasto' THEN f.tr_monto ELSE 0 END),0) AS gastos
        FROM fact_transaccion f JOIN dim_categoria c ON c.c_id_categoria=f.tr_id_categoria
        WHERE f.tr_id_usuario=:u''',u=usuario)[0]
    ingresos,gastos = totales['ingresos'],totales['gastos']
    a,b,c = st.columns(3)
    a.metric('Ingresos',pesos(ingresos))
    b.metric('Gastos',pesos(gastos))
    c.metric('Saldo disponible',pesos(ingresos-gastos))
    st.subheader('Gastos por categoría')
    filas = consulta('''SELECT c.c_nombre AS categoria,SUM(f.tr_monto) AS total
        FROM fact_transaccion f JOIN dim_categoria c ON c.c_id_categoria=f.tr_id_categoria
        WHERE f.tr_id_usuario=:u AND c.c_tipo='Gasto' GROUP BY c.c_nombre ORDER BY total DESC''',u=usuario)
    if filas:
        st.bar_chart({x['categoria']:float(x['total']) for x in filas})
    else:
        st.info('Aún no hay gastos registrados.')
    st.subheader('Gastos por método de pago')
    st.dataframe(consulta('''SELECT f.tr_metodo_pago AS metodo,SUM(f.tr_monto) AS total
        FROM fact_transaccion f JOIN dim_categoria c ON c.c_id_categoria=f.tr_id_categoria
        WHERE f.tr_id_usuario=:u AND c.c_tipo='Gasto'
        GROUP BY f.tr_metodo_pago ORDER BY total DESC''',u=usuario),hide_index=True)
    st.subheader('Evolución mensual de ingresos y gastos')
    meses = consulta('''SELECT t."T_AÑO" AS anio,t.t_mes AS mes,
        SUM(CASE WHEN c.c_tipo='Ingreso' THEN f.tr_monto ELSE 0 END) AS ingresos,
        SUM(CASE WHEN c.c_tipo='Gasto' THEN f.tr_monto ELSE 0 END) AS gastos
        FROM fact_transaccion f JOIN dim_categoria c ON c.c_id_categoria=f.tr_id_categoria
        JOIN dim_tiempo t ON t.t_id_tiempo=f.tr_id_tiempo
        WHERE f.tr_id_usuario=:u GROUP BY t."T_AÑO",t.t_mes ORDER BY anio,mes''',u=usuario)
    if meses:
        st.line_chart({f"{x['anio']}-{x['mes']:02d}":{'Ingresos':float(x['ingresos']),'Gastos':float(x['gastos'])} for x in meses})
    st.subheader('Gastos por mes')
    st.dataframe(consulta('''SELECT t."T_AÑO" AS anio,t.t_mes AS mes,SUM(f.tr_monto) AS total_gastos
        FROM fact_transaccion f JOIN dim_categoria c ON c.c_id_categoria=f.tr_id_categoria
        JOIN dim_tiempo t ON t.t_id_tiempo=f.tr_id_tiempo
        WHERE f.tr_id_usuario=:u AND c.c_tipo='Gasto'
        GROUP BY t."T_AÑO",t.t_mes ORDER BY anio DESC,mes DESC''',u=usuario),hide_index=True)
