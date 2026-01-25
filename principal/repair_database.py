# repair_database.py
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from principal.models import Inscripcion, Iglesia
from django.db import connection
import sqlite3

def repair_foreign_keys():
    print("🔧 Reparando base de datos...")
    
    # Conectar directamente a SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Encontrar iglesias faltantes
    cursor.execute("""
        SELECT DISTINCT i.iglesia_id 
        FROM principal_inscripcion i
        LEFT JOIN principal_iglesia ig ON i.iglesia_id = ig.id
        WHERE ig.id IS NULL
    """)
    
    missing_church_ids = [row[0] for row in cursor.fetchall()]
    
    if missing_church_ids:
        print(f"📋 Iglesias faltantes encontradas: {missing_church_ids}")
        
        # 2. Crear iglesias faltantes
        for church_id in missing_church_ids:
            cursor.execute("""
                INSERT INTO principal_iglesia 
                (id, nombre, ubicacion, fecha_creacion)
                VALUES (?, ?, ?, datetime('now'))
            """, (church_id, f'Iglesia {church_id}', 'Desconocida'))
            print(f"  ✅ Creada iglesia ID {church_id}")
        
        conn.commit()
    
    # 3. Verificar que no haya más problemas
    cursor.execute("""
        SELECT COUNT(*) 
        FROM principal_inscripcion i
        LEFT JOIN principal_iglesia ig ON i.iglesia_id = ig.id
        WHERE ig.id IS NULL
    """)
    
    remaining_problems = cursor.fetchone()[0]
    
    if remaining_problems == 0:
        print("✅ ¡Todas las foreign keys reparadas!")
    else:
        print(f"⚠️  Aún hay {remaining_problems} problemas sin resolver")
        
        # Asignar todas a una iglesia por defecto
        cursor.execute("SELECT MIN(id) FROM principal_iglesia")
        default_church_id = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE principal_inscripcion 
            SET iglesia_id = ?
            WHERE iglesia_id NOT IN (SELECT id FROM principal_iglesia)
        """, (default_church_id,))
        
        conn.commit()
        print(f"  ↪️  Todas las inscripciones asignadas a iglesia ID {default_church_id}")
    
    conn.close()
    
    # 4. Verificar desde Django
    print("\n📊 Verificación final desde Django:")
    for insc in Inscripcion.objects.all():
        try:
            church = insc.iglesia
            print(f"  ✓ Inscripción {insc.id}: {insc.nombre_persona} → {church.nombre}")
        except:
            print(f"  ✗ Inscripción {insc.id}: ERROR - aún tiene problema")

if __name__ == "__main__":
    repair_foreign_keys()