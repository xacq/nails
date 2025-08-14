#!/usr/bin/env python3
"""
Script de inicio para la aplicación Elegance Nails SaaS
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def check_environment():
    """Verificar que el entorno esté configurado correctamente"""
    required_vars = [
        'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE',
        'SECRET_KEY', 'MAPBOX_ACCESS_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Variables de entorno faltantes:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nConfigura estas variables en el archivo .env")
        return False
    
    print("✅ Variables de entorno configuradas correctamente")
    return True

def start_application():
    """Iniciar la aplicación"""
    from app import create_app
    
    app = create_app()
    
    print("🚀 Iniciando Elegance Nails SaaS Platform...")
    print(f"🌐 URL: http://localhost:5000")
    print(f"🗺️  Directorio: http://localhost:5000/directory")
    print("💡 Presiona Ctrl+C para detener el servidor")
    
    # Ejecutar en modo desarrollo
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    print("=" * 50)
    print("  ELEGANCE NAILS SAAS PLATFORM")
    print("=" * 50)
    
    if check_environment():
        try:
            start_application()
        except KeyboardInterrupt:
            print("\n👋 Servidor detenido")
        except Exception as e:
            print(f"❌ Error al iniciar la aplicación: {e}")
    else:
        print("🔧 Por favor, configura las variables de entorno antes de continuar")
