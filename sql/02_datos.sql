-- Ejecutar después de 01_estructura.sql, una sola vez.
INSERT INTO dim_usuario (u_nombre,u_correo,u_ciudad) VALUES ('Usuario Demo','demo@mibolsillo.com','Medellín');
INSERT INTO dim_categoria (c_nombre,c_tipo,c_descripcion) VALUES ('Salario','Ingreso','Ingresos laborales');
INSERT INTO dim_categoria (c_nombre,c_tipo,c_descripcion) VALUES ('Beca','Ingreso','Apoyos académicos');
INSERT INTO dim_categoria (c_nombre,c_tipo,c_descripcion) VALUES ('Alimentación','Gasto','Comidas y mercado');
INSERT INTO dim_categoria (c_nombre,c_tipo,c_descripcion) VALUES ('Transporte','Gasto','Desplazamientos');
INSERT INTO dim_categoria (c_nombre,c_tipo,c_descripcion) VALUES ('Entretenimiento','Gasto','Ocio y diversión');
INSERT INTO dim_tiempo (t_fecha,t_dia,t_mes,"T_AÑO",t_trimestre,t_dia_semana)
SELECT DATE '2026-11-01',1,11,2026,4,'Domingo' FROM dual;
INSERT INTO dim_tiempo (t_fecha,t_dia,t_mes,"T_AÑO",t_trimestre,t_dia_semana)
SELECT DATE '2026-11-05',5,11,2026,4,'Jueves' FROM dual;
INSERT INTO dim_tiempo (t_fecha,t_dia,t_mes,"T_AÑO",t_trimestre,t_dia_semana)
SELECT DATE '2026-11-08',8,11,2026,4,'Domingo' FROM dual;
INSERT INTO fact_transaccion (tr_id_usuario,tr_id_categoria,tr_id_tiempo,tr_monto,tr_metodo_pago,tr_descripcion)
SELECT u.u_id_usuario,c.c_id_categoria,t.t_id_tiempo,1800000,'Transferencia','Pago mensual' FROM dim_usuario u CROSS JOIN dim_categoria c CROSS JOIN dim_tiempo t WHERE u.u_correo='demo@mibolsillo.com' AND c.c_nombre='Salario' AND t.t_fecha=DATE '2026-11-01';
INSERT INTO fact_transaccion (tr_id_usuario,tr_id_categoria,tr_id_tiempo,tr_monto,tr_metodo_pago,tr_descripcion)
SELECT u.u_id_usuario,c.c_id_categoria,t.t_id_tiempo,85000,'Tarjeta débito','Mercado semanal' FROM dim_usuario u CROSS JOIN dim_categoria c CROSS JOIN dim_tiempo t WHERE u.u_correo='demo@mibolsillo.com' AND c.c_nombre='Alimentación' AND t.t_fecha=DATE '2026-11-05';
INSERT INTO fact_transaccion (tr_id_usuario,tr_id_categoria,tr_id_tiempo,tr_monto,tr_metodo_pago,tr_descripcion)
SELECT u.u_id_usuario,c.c_id_categoria,t.t_id_tiempo,18000,'Efectivo','Transporte urbano' FROM dim_usuario u CROSS JOIN dim_categoria c CROSS JOIN dim_tiempo t WHERE u.u_correo='demo@mibolsillo.com' AND c.c_nombre='Transporte' AND t.t_fecha=DATE '2026-11-08';
COMMIT;
