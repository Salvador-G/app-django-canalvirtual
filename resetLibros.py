import sqlite3

DB_PATH = "db.sqlite3"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Eliminar reclamaciones primero (dependientes)
    cursor.execute("DELETE FROM reclamaciones_reclamacion;")
    
    # Luego los libros
    cursor.execute("DELETE FROM reclamaciones_libroreclamacion;")

    conn.commit()
    print("Reclamaciones y libros eliminados correctamente.")
except sqlite3.Error as e:
    print("Error:", e)
finally:
    conn.close()
