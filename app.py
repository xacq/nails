#!/usr/bin/env python3
"""
Aplicación de Gestión de Salón de Uñas
Desarrollada con Flask, SQLAlchemy y MySQL
"""

from app import create_app
from app.models import db
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear la aplicación
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Contexto para flask shell"""
    from app.models import (User, Service, ServiceCategory, Appointment, 
                           Payment, Schedule, LoyaltyPoint, Review, 
                           Promotion, Inventory)
    return {
        'db': db, 
        'User': User, 
        'Service': Service,
        'ServiceCategory': ServiceCategory,
        'Appointment': Appointment,
        'Payment': Payment,
        'Schedule': Schedule,
        'LoyaltyPoint': LoyaltyPoint,
        'Review': Review,
        'Promotion': Promotion,
        'Inventory': Inventory
    }

@app.cli.command()
def init_db():
    """Inicializar la base de datos"""
    db.create_all()
    print("Base de datos inicializada.")

@app.cli.command()
def create_admin():
    """Crear usuario administrador"""
    from app.models import User, UserRole
    
    admin_email = input("Email del administrador: ")
    admin_password = input("Contraseña del administrador: ")
    admin_first_name = input("Nombre: ")
    admin_last_name = input("Apellido: ")
    
    # Verificar si ya existe
    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        print("Ya existe un usuario con este email.")
        return
    
    # Crear administrador
    admin = User(
        email=admin_email,
        first_name=admin_first_name,
        last_name=admin_last_name,
        role=UserRole.ADMIN,
        is_active=True,
        email_verified=True
    )
    admin.set_password(admin_password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Administrador creado: {admin_email}")

@app.cli.command()
def seed_data():
    """Poblar la base de datos con datos de ejemplo"""
    from app.models import (User, Service, ServiceCategory, UserRole, 
                           Appointment, AppointmentStatus, Inventory)
    from datetime import date, time, datetime
    
    # Crear categorías de servicios
    categories = [
        ServiceCategory(name="Manicura", description="Servicios de cuidado de uñas de manos", 
                       color_code="#FF6B6B", icon="fas fa-hand-paper"),
        ServiceCategory(name="Pedicura", description="Servicios de cuidado de uñas de pies", 
                       color_code="#4ECDC4", icon="fas fa-foot"),
        ServiceCategory(name="Nail Art", description="Arte y decoración de uñas", 
                       color_code="#45B7D1", icon="fas fa-paint-brush"),
        ServiceCategory(name="Tratamientos", description="Tratamientos especiales y cuidados", 
                       color_code="#96CEB4", icon="fas fa-spa"),
        ServiceCategory(name="Extensiones", description="Extensiones y uñas artificiales", 
                       color_code="#FFEAA7", icon="fas fa-magic")
    ]
    
    for category in categories:
        existing = ServiceCategory.query.filter_by(name=category.name).first()
        if not existing:
            db.session.add(category)
    
    db.session.commit()
    
    # Crear servicios
    services_data = [
        # Manicura
        ("Manicura Básica", "Limado, cutícula y esmaltado básico", 25.00, 45, 1),
        ("Manicura Semipermanente", "Manicura con esmalte semipermanente", 35.00, 60, 1),
        ("Manicura Francesa", "Manicura clásica francesa", 30.00, 50, 1),
        ("Manicura Spa", "Manicura con tratamiento hidratante y masaje", 40.00, 75, 1),
        
        # Pedicura  
        ("Pedicura Básica", "Limado, cutícula y esmaltado básico", 30.00, 60, 2),
        ("Pedicura Spa", "Pedicura completa con exfoliación y masaje", 45.00, 90, 2),
        ("Pedicura Médica", "Tratamiento especializado para pies", 50.00, 75, 2),
        
        # Nail Art
        ("Nail Art Básico", "Diseños simples y decoraciones", 15.00, 30, 3),
        ("Nail Art Avanzado", "Diseños complejos y detallados", 25.00, 45, 3),
        ("Decoración con Piedras", "Aplicación de cristales y piedras", 20.00, 30, 3),
        
        # Tratamientos
        ("Tratamiento Hidratante", "Mascarilla hidratante para manos", 20.00, 30, 4),
        ("Tratamiento Anti-edad", "Tratamiento rejuvenecedor", 35.00, 45, 4),
        ("Parafina Terapéutica", "Tratamiento con parafina caliente", 25.00, 30, 4),
        
        # Extensiones
        ("Extensiones de Gel", "Uñas artificiales con gel", 55.00, 120, 5),
        ("Extensiones de Acrílico", "Uñas artificiales con acrílico", 50.00, 110, 5),
        ("Relleno de Extensiones", "Mantenimiento de extensiones", 35.00, 75, 5),
    ]
    
    for name, desc, price, duration, cat_id in services_data:
        existing = Service.query.filter_by(name=name).first()
        if not existing:
            service = Service(
                name=name,
                description=desc,
                price=price,
                duration_minutes=duration,
                category_id=cat_id,
                loyalty_points_earned=int(price // 5)  # 1 punto por cada $5
            )
            db.session.add(service)
    
    db.session.commit()
    
    # Crear usuarios de ejemplo
    users_data = [
        ("María", "García", "maria@ejemplo.com", "cliente123", UserRole.CLIENT),
        ("Ana", "López", "ana@ejemplo.com", "cliente123", UserRole.CLIENT),
        ("Sofia", "Martínez", "sofia@ejemplo.com", "empleado123", UserRole.EMPLOYEE),
        ("Carla", "Rodríguez", "carla@ejemplo.com", "empleado123", UserRole.EMPLOYEE),
    ]
    
    for first_name, last_name, email, password, role in users_data:
        existing = User.query.filter_by(email=email).first()
        if not existing:
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
                is_active=True,
                phone=f"555-{datetime.now().microsecond % 10000:04d}"
            )
            user.set_password(password)
            db.session.add(user)
    
    db.session.commit()
    
    # Crear inventario de ejemplo
    inventory_data = [
        ("Esmalte Rojo Clásico", "nail_polish", "OPI", "Rojo", 24, 5, 8.50),
        ("Esmalte Rosa Nude", "nail_polish", "Essie", "Rosa", 18, 5, 9.00),
        ("Esmalte Negro", "nail_polish", "Sally Hansen", "Negro", 15, 3, 7.75),
        ("Lima de Uñas 180/240", "tools", "Generic", None, 50, 10, 1.25),
        ("Aceite para Cutículas", "supplies", "CND", None, 12, 3, 15.00),
        ("Algodón", "supplies", "Generic", None, 100, 20, 2.50),
        ("Alcohol Isopropílico", "supplies", "Generic", None, 8, 2, 3.00),
        ("Cristales para Decorar", "decorations", "Swarovski", "Varios", 200, 50, 0.25),
    ]
    
    for product_name, category, brand, color, qty, min_stock, cost in inventory_data:
        existing = Inventory.query.filter_by(product_name=product_name, brand=brand).first()
        if not existing:
            item = Inventory(
                product_name=product_name,
                category=category,
                brand=brand,
                color=color,
                quantity=qty,
                min_stock_level=min_stock,
                unit_cost=cost,
                supplier="Proveedor Ejemplo"
            )
            db.session.add(item)
    
    db.session.commit()
    print("Datos de ejemplo creados exitosamente!")

if __name__ == '__main__':
    app.run(debug=True)
