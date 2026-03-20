import pandas as pd
import numpy as np


def generate_dirty_test_data(filename="test_data_dirty.csv"):
    # 1. Crear datos ficticios limpios primero
    data = {
        "ID_Producto": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        "Fecha_Venta": pd.date_range(start="2024-01-01", periods=10).strftime('%Y-%m-%d'),
        "Categoria": ["Electrónica", "Hogar", "Electrónica", "Ropa", "Hogar", "Ropa", "Juguetes", "Electrónica", "Juguetes", "Ropa"],
        "Ventas_USD": [1500.50, 200.00, 1200.00, 45.99, 300.25, 89.90, 120.00, 2500.00, 55.00, 110.00],
        "Stock_Disponible": [15, 40, 10, 100, 25, 60, 35, 5, 50, 80],
        "Promocion_Activa": [True, False, True, False, False, True, False, True, False, False]
    }

    df_clean = pd.DataFrame(data)

    # 2. "Ensuciar" el archivo para probar tus heurísticas (RF-01)
    # Creamos un encabezado de adorno (basura) que el sistema debe ignorar
    header_noise = [
        ["REPORTE DE VENTAS INTERNO - CONFIDENCIAL", "", "", "", "", ""],
        ["Generado por: Sistema Legacy v2.1", "", "", "", "", ""],
        ["Fecha de extraccion: 2026-03-19", "", "", "", "", ""],
        ["", "", "", "", "", ""],  # Fila vacía
    ]

    df_noise = pd.DataFrame(header_noise, columns=df_clean.columns)

    # 3. Concatenar: Ruido + Encabezados Reales + Datos
    df_final = pd.concat([df_noise, df_clean], ignore_index=True)

    # 4. Agregar columnas vacías a la izquierda (Offset de columna)
    df_final.insert(0, "Columna_Vacia_1", np.nan)

    # Guardar como CSV
    # Guardamos sin el header de pandas para simular el ruido
    df_final.to_csv(filename, index=False, header=False)
    print(f"✅ Archivo '{filename}' generado con éxito.")
    print("Simulación: 4 filas de ruido al inicio y 1 columna vacía a la izquierda.")


if __name__ == "__main__":
    generate_dirty_test_data()
