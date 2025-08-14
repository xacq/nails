#!/usr/bin/env python3
"""
Script de prueba rápida para verificar que todo funcione
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_imports():
    """Probar que todas las importaciones funcionen"""
    try:
        print("🔍 Probando importaciones...")
        
        from app import create_app
        print("✅ create_app importado exitosamente")
        
        from app.models import db, Business, BusinessType, BusinessStatus
        print("✅ Modelos importados exitosamente")
        
        app = create_app()
        print("✅ Aplicación creada exitosamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def test_database_connection():
    """Probar conexión a la base de datos"""
    try:
        print("🔍 Probando conexión a la base de datos...")
        
        from app import create_app
        from app.models import db
        
        app = create_app()
        
        with app.app_context():
            # Probar conexión
            db.engine.execute('SELECT 1')
            print("✅ Conexión a la base de datos exitosa")
            return True
            
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("=" * 50)
    print("  PRUEBA RÁPIDA - ELEGANCE NAILS SAAS")
    print("=" * 50)
    
    success = True
    
    # Prueba 1: Importaciones
    if not test_imports():
        success = False
    
    print()
    
    # Prueba 2: Base de datos
    if not test_database_connection():
        success = False
    
    print()
    
    if success:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("📍 Tu aplicación está lista para funcionar")
        print("🚀 Puedes ejecutar: python app.py")
        print("🗺️  URL del directorio: http://localhost:5000/directory")
    else:
        print("⚠️  Hay algunos problemas que necesitan resolverse")
    
    return success

if __name__ == "__main__":
    main()
