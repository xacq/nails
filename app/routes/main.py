from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import db, User, Appointment, Service, ServiceCategory, AppointmentStatus, UserRole
from datetime import datetime, date, timedelta
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/test')
def test():
    """Página de prueba para verificar funcionamiento"""
    try:
        # Obtener servicios destacados
        featured_services = Service.query.filter_by(is_active=True).limit(6).all()
        return render_template('main/test.html', featured_services=featured_services)
    except Exception as e:
        # Si hay error, mostrar página básica
        return render_template('main/test.html', featured_services=[])

@main_bp.route('/')
def index():
    """Página principal del sitio"""
    try:
        # Obtener servicios destacados
        featured_services = Service.query.filter_by(is_active=True).limit(6).all()
        
        # Obtener categorías de servicios
        categories = ServiceCategory.query.filter_by(is_active=True).all()
        
        return render_template('main/index.html', 
                             featured_services=featured_services,
                             categories=categories)
    except Exception as e:
        # Si hay error (ej: tablas no existen), crear base de datos
        from app.models import db
        try:
            db.create_all()
            # Crear datos básicos si no existen
            if not Service.query.first():
                create_sample_data()
            return redirect(url_for('main.index'))
        except Exception as init_error:
            flash(f'Error inicializando base de datos: {init_error}', 'error')
            return render_template('main/index.html', 
                                 featured_services=[],
                                 categories=[])

def create_sample_data():
    """Crear datos de ejemplo"""
    from app.models import ServiceCategory, Service, User, UserRole
    from werkzeug.security import generate_password_hash
    
    # Crear categoría
    category = ServiceCategory(
        name="Manicure",
        description="Servicios de manicure",
        is_active=True
    )
    db.session.add(category)
    db.session.flush()
    
    # Crear servicios
    services = [
        Service(name="Manicure Clásico", description="Manicure básico", 
               price=25.00, duration_minutes=60, category_id=category.id, is_active=True),
        Service(name="Manicure Francés", description="Manicure francés", 
               price=35.00, duration_minutes=75, category_id=category.id, is_active=True),
        Service(name="Uñas Gel", description="Uñas con gel", 
               price=45.00, duration_minutes=90, category_id=category.id, is_active=True),
    ]
    
    for service in services:
        db.session.add(service)
    
    # Crear usuario admin si no existe
    if not User.query.filter_by(email='admin@elegancenails.com').first():
        admin = User(
            username='admin',
            email='admin@elegancenails.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='Sistema',
            role=UserRole.ADMIN,
            is_active=True
        )
        db.session.add(admin)
    
    db.session.commit()

@main_bp.route('/about')
def about():
    """Página sobre nosotros"""
    return render_template('main/about.html')

@main_bp.route('/contact')
def contact():
    """Página de contacto"""
    return render_template('main/contact.html')

@main_bp.route('/services')
def services():
    """Página de servicios"""
    category_id = request.args.get('category', type=int)
    
    if category_id:
        services = Service.query.filter_by(category_id=category_id, is_active=True).all()
        category = ServiceCategory.query.get_or_404(category_id)
    else:
        services = Service.query.filter_by(is_active=True).all()
        category = None
    
    categories = ServiceCategory.query.filter_by(is_active=True).all()
    
    return render_template('main/services.html', 
                         services=services, 
                         categories=categories,
                         selected_category=category)

@main_bp.route('/client_dashboard')
@login_required
def client_dashboard():
    """Dashboard para clientes"""
    if current_user.role != UserRole.CLIENT:
        flash('Acceso denegado', 'error')
        return redirect(url_for('main.index'))
    
    # Obtener próximas citas
    upcoming_appointments = Appointment.query.filter(
        Appointment.client_id == current_user.id,
        Appointment.appointment_date >= date.today(),
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
    ).order_by(Appointment.appointment_date, Appointment.start_time).limit(5).all()
    
    # Obtener historial de citas recientes
    recent_appointments = Appointment.query.filter(
        Appointment.client_id == current_user.id,
        Appointment.status == AppointmentStatus.COMPLETED
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()
    
    # Estadísticas del cliente
    total_appointments = Appointment.query.filter_by(
        client_id=current_user.id,
        status=AppointmentStatus.COMPLETED
    ).count()
    
    return render_template('main/client_dashboard.html',
                         upcoming_appointments=upcoming_appointments,
                         recent_appointments=recent_appointments,
                         total_appointments=total_appointments,
                         loyalty_points=current_user.total_loyalty_points)

@main_bp.route('/employee_dashboard')
@login_required
def employee_dashboard():
    """Dashboard para empleados"""
    if current_user.role != UserRole.EMPLOYEE:
        flash('Acceso denegado', 'error')
        return redirect(url_for('main.index'))
    
    today = date.today()
    
    # Citas de hoy
    today_appointments = Appointment.query.filter(
        Appointment.employee_id == current_user.id,
        Appointment.appointment_date == today
    ).order_by(Appointment.start_time).all()
    
    # Próximas citas esta semana
    week_end = today + timedelta(days=7)
    upcoming_appointments = Appointment.query.filter(
        Appointment.employee_id == current_user.id,
        Appointment.appointment_date > today,
        Appointment.appointment_date <= week_end,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
    ).order_by(Appointment.appointment_date, Appointment.start_time).all()
    
    # Estadísticas del empleado
    completed_today = len([apt for apt in today_appointments if apt.status == AppointmentStatus.COMPLETED])
    pending_today = len([apt for apt in today_appointments if apt.status in [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]])
    
    return render_template('main/employee_dashboard.html',
                         today_appointments=today_appointments,
                         upcoming_appointments=upcoming_appointments,
                         completed_today=completed_today,
                         pending_today=pending_today)

@main_bp.route('/book_appointment')
@login_required
def book_appointment():
    """Página para reservar cita (solo clientes)"""
    if current_user.role != UserRole.CLIENT:
        flash('Solo los clientes pueden reservar citas', 'error')
        return redirect(url_for('main.index'))
    
    services = Service.query.filter_by(is_active=True).all()
    categories = ServiceCategory.query.filter_by(is_active=True).all()
    
    return render_template('main/book_appointment.html',
                         services=services,
                         categories=categories)

@main_bp.route('/api/available_slots')
@login_required
def available_slots():
    """API para obtener horarios disponibles"""
    date_str = request.args.get('date')
    service_ids = request.args.getlist('services', type=int)
    
    if not date_str or not service_ids:
        return jsonify({'error': 'Fecha y servicios son requeridos'}), 400
    
    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Calcular duración total de servicios seleccionados
    services = Service.query.filter(Service.id.in_(service_ids)).all()
    total_duration = sum(service.duration_minutes for service in services)
    
    # Obtener empleados disponibles (simplificado)
    employees = User.query.filter_by(role=UserRole.EMPLOYEE, is_active=True).all()
    
    # Generar slots disponibles (ejemplo simple: 9 AM a 6 PM)
    available_slots = []
    start_hour = 9
    end_hour = 18
    slot_duration = 30  # slots de 30 minutos
    
    for hour in range(start_hour, end_hour):
        for minute in [0, 30]:
            slot_time = f"{hour:02d}:{minute:02d}"
            # Aquí se debería verificar disponibilidad real
            # Por ahora retornamos todos los slots como disponibles
            available_slots.append(slot_time)
    
    return jsonify({'slots': available_slots})

@main_bp.route('/gallery')
def gallery():
    """Galería de trabajos"""
    return render_template('main/gallery.html')

@main_bp.route('/pricing')
def pricing():
    """Página de precios"""
    categories = ServiceCategory.query.filter_by(is_active=True).all()
    services_by_category = {}
    
    for category in categories:
        services_by_category[category] = Service.query.filter_by(
            category_id=category.id, 
            is_active=True
        ).all()
    
    return render_template('main/pricing.html', 
                         services_by_category=services_by_category)

@main_bp.route('/terms')
def terms():
    """Términos y condiciones"""
    return render_template('main/terms.html')

@main_bp.route('/privacy')
def privacy():
    """Política de privacidad"""
    return render_template('main/privacy.html')

@main_bp.route('/directory')
def business_directory():
    """Directorio de negocios con mapa interactivo"""
    import os
    return render_template('business_directory.html', 
                         mapbox_token=os.getenv('MAPBOX_ACCESS_TOKEN'))
