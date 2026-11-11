# 💰 Mi Bolsillo

Aplicación Streamlit conectada a Oracle Database para registrar y consultar ingresos y gastos de estudiantes y jóvenes profesionales. Proyecto basado en el Taller 2 de Introducción al BI.

## Modelo entidad-relación

Modelo estrella: `DIM_USUARIO`, `DIM_CATEGORIA` y `DIM_TIEMPO` se relacionan 1:N con `FACT_TRANSACCION` mediante `tr_id_usuario`, `tr_id_categoria` y `tr_id_tiempo`. El diagrama original se incluye en `diagrama_original.png`.

## Estructura

- `sql/01_estructura.sql`: DDL con tablas, claves primarias, foráneas, restricciones e índices.
- `sql/02_datos.sql`: DML con un usuario de demostración, cinco categorías y tres transacciones.
- `app.py`: interfaz Streamlit y consultas SQL parametrizadas.
- `requirements.txt`: dependencias Python.
- `.streamlit/secrets.toml.example`: plantilla de conexión Oracle (sin credenciales).

## Instalación

1. Crear o usar una base Oracle existente (por ejemplo, Oracle Autonomous Database) y una conexión funcional en SQL Developer.
2. Abrir `sql/01_estructura.sql` en SQL Developer y ejecutar como script (F5). Hacerlo **solo una vez**.
3. Ejecutar `sql/02_datos.sql` (F5), **solo una vez**.
4. Abrir esta carpeta en PyCharm. Crear un entorno virtual Python 3.11 o 3.12.
5. Instalar: `python -m pip install -r requirements.txt`.
6. Copiar `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y completar credenciales, DSN y ruta del wallet. Para una conexión Oracle local sin wallet, eliminar las tres claves relacionadas con wallet.
7. Ejecutar: `python -m streamlit run app.py`.
8. Abrir la dirección local que muestra Streamlit (normalmente http://localhost:8501).

**Nota:** el DSN, el usuario, la contraseña y la ruta del wallet dependen de tu propia conexión. Nunca subir `secrets.toml` ni el wallet a GitHub.

## Funciones

- Alta de usuarios y categorías mediante `INSERT`.
- Registro de transacciones con validación de monto positivo y fecha vinculada a `DIM_TIEMPO`.
- Consulta de movimientos por usuario y tipo con `JOIN` y `WHERE`.
- Indicadores de ingresos, gastos y saldo con `SUM` y `CASE`.
- Reportes por categoría, método de pago y mes con `GROUP BY`.
- Consultas ejecutadas directamente en Oracle; **no se utiliza pandas**.
- `COMMIT` en escritura y `ROLLBACK` si ocurre un error.

## Evidencia sugerida para entrega

Capturas de SQL Developer mostrando las cuatro tablas (`DIM_USUARIO`, `DIM_CATEGORIA`, `DIM_TIEMPO`, `FACT_TRANSACCION`) y capturas de Streamlit registrando un gasto y mostrando el saldo actualizado.

## Publicación en GitHub

Crear repositorio `mi-bolsillo`, subir los archivos de esta carpeta (excepto `secrets.toml` y wallet), y comprobar que el README y el diagrama sean visibles. La aplicación necesita acceso a una base Oracle configurada para ejecutarse; subir el código no crea ni publica la base de datos.
