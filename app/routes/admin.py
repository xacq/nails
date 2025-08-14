from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import (db, User, Appointment, Service, Payment, Review, 
                       AppointmentStatus, PaymentStatus, UserRole, LoyaltyPoint, Inventory)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorador para requerir rol de admin"""
    def decorated_function(*args, **kwargs):
        if current_user.role != UserRole.ADMIN:
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard principal de administración"""
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Estadísticas generales
    stats = {
        'total_users': User.query.filter_by(is_active=True).count(),
        'total_clients': User.query.filter_by(role=UserRole.CLIENT, is_active=True).count(),
        'total_employees': User.query.filter_by(role=UserRole.EMPLOYEE, is_active=True).count(),
        'total_services': Service.query.filter_by(is_active=True).count(),
        'total_appointments': Appointment.query.count(),
        'completed_appointments': Appointment.query.filter_by(status=AppointmentStatus.COMPLETED).count(),
    }
    
    # Citas de hoy
    today_appointments = Appointment.query.filter_by(appointment_date=today).order_by(Appointment.start_time).all()
    
    # Ingresos del mes
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_status == PaymentStatus.PAID,
        Payment.created_at >= month_ago
    ).scalar() or 0
    
    # Citas pendientes
    pending_appointments = Appointment.query.filter_by(status=AppointmentStatus.PENDING).count()
    
    # Productos con stock bajo
    low_stock_items = Inventory.query.filter(
        Inventory.quantity <= Inventory.min_stock_level
    ).count()
    
    # Nuevos clientes esta semana
    new_clients_week = User.query.filter(
        User.role == UserRole.CLIENT,
        User.created_at >= week_ago
    ).count()
    
    # Gráfico de citas por estado
    appointment_stats = {}
    for status in AppointmentStatus:
        count = Appointment.query.filter_by(status=status).count()
        appointment_stats[status.value] = count
    
    # Servicios más populares
    popular_services = db.session.query(
        Service.name,
        func.count(Service.id).label('count')
    ).join(
        Service.appointments
    ).group_by(Service.id, Service.name).order_by(
        func.count(Service.id).desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         today_appointments=today_appointments,
                         monthly_revenue=monthly_revenue,
                         pending_appointments=pending_appointments,
                         low_stock_items=low_stock_items,
                         new_clients_week=new_clients_week,
                         appointment_stats=appointment_stats,
                         popular_services=popular_services)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """Gestión de usuarios"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    if role_filter and role_filter in [role.value for role in UserRole]:
        query = query.filter_by(role=UserRole(role_filter))
    
    if search:
        query = query.filter(
            or_(
                User.first_name.contains(search),
                User.last_name.contains(search),
                User.email.contains(search),
                User.phone.contains(search)
            )
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html',
                         users=users,
                         role_filter=role_filter,
                         search_term=search,
                         UserRole=UserRole)

@admin_bp.route('/users/<int:id>')
@login_required
@admin_required
def view_user(id):
    """Ver detalles de un usuario"""
    user = User.query.get_or_404(id)
    
    # Estadísticas del usuario
    user_stats = {
        'total_appointments': user.appointments_as_client.count(),
        'completed_appointments': user.appointments_as_client.filter_by(status=AppointmentStatus.COMPLETED).count(),
        'cancelled_appointments': user.appointments_as_client.filter_by(status=AppointmentStatus.CANCELLED).count(),
        'total_spent': db.session.query(func.sum(Payment.amount)).filter(
            Payment.client_id == user.id,
            Payment.payment_status == PaymentStatus.PAID
        ).scalar() or 0,
        'loyalty_points': user.total_loyalty_points
    }
    
    # Últimas citas
    recent_appointments = user.appointments_as_client.order_by(
        Appointment.appointment_date.desc()
    ).limit(5).all()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         user_stats=user_stats,
                         recent_appointments=recent_appointments)

@admin_bp.route('/users/<int:id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
    """Activar/desactivar usuario"""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta', 'error')
        return redirect(url_for('admin.view_user', id=id))
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activado" if user.is_active else "desactivado"
        flash(f'Usuario {status} exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al cambiar el estado del usuario', 'error')
    
    return redirect(url_for('admin.view_user', id=id))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Página de reportes"""
    # Rango de fechas por defecto (último mes)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    # Obtener parámetros de filtro
    start_date_param = request.args.get('start_date')
    end_date_param = request.args.get('end_date')
    
    if start_date_param:
        start_date = datetime.strptime(start_date_param, '%Y-%m-%d').date()
    if end_date_param:
        end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
    
    # Reporte de ingresos
    revenue_data = db.session.query(
        func.date(Payment.created_at).label('date'),
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.payment_status == PaymentStatus.PAID,
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date
    ).group_by(func.date(Payment.created_at)).order_by('date').all()
    
    # Reporte de citas por estado
    appointment_data = db.session.query(
        Appointment.status,
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date
    ).group_by(Appointment.status).all()
    
    # Servicios más populares
    service_data = db.session.query(
        Service.name,
        func.count(Service.id).label('count'),
        func.sum(Service.price).label('revenue')
    ).join(Service.appointments).join(Appointment).filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date,
        Appointment.status == AppointmentStatus.COMPLETED
    ).group_by(Service.id, Service.name).order_by(
        func.count(Service.id).desc()
    ).limit(10).all()
    
    # Empleados con más citas
    employee_data = db.session.query(
        User.first_name,
        User.last_name,
        func.count(Appointment.id).label('appointments'),
        func.sum(Appointment.total_price).label('revenue')
    ).join(Appointment, User.id == Appointment.employee_id).filter(
        User.role == UserRole.EMPLOYEE,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date,
        Appointment.status == AppointmentStatus.COMPLETED
    ).group_by(User.id, User.first_name, User.last_name).order_by(
        func.count(Appointment.id).desc()
    ).all()
    
    return render_template('admin/reports.html',
                         revenue_data=revenue_data,
                         appointment_data=appointment_data,
                         service_data=service_data,
                         employee_data=employee_data,
                         start_date=start_date,
                         end_date=end_date)

@admin_bp.route('/inventory')
@login_required
@admin_required
def manage_inventory():
    """Gestión de inventario"""
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    search = request.args.get('search', '').strip()
    low_stock_only = request.args.get('low_stock', False, type=bool)
    
    query = Inventory.query
    
    if category_filter:
        query = query.filter_by(category=category_filter)
    
    if search:
        query = query.filter(
            or_(
                Inventory.product_name.contains(search),
                Inventory.brand.contains(search),
                Inventory.supplier.contains(search)
            )
        )
    
    if low_stock_only:
        query = query.filter(Inventory.quantity <= Inventory.min_stock_level)
    
    inventory = query.order_by(Inventory.product_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Obtener categorías únicas
    categories = db.session.query(Inventory.category).distinct().filter(
        Inventory.category.isnot(None)
    ).all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('admin/inventory.html',
                         inventory=inventory,
                         categories=categories,
                         category_filter=category_filter,
                         search_term=search,
                         low_stock_only=low_stock_only)

@admin_bp.route('/inventory/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_inventory_item():
    """Crear nuevo item de inventario"""
    if request.method == 'GET':
        return render_template('admin/create_inventory.html')
    
    try:
        item = Inventory(
            product_name=request.form.get('product_name', '').strip(),
            category=request.form.get('category', '').strip(),
            brand=request.form.get('brand', '').strip(),
            color=request.form.get('color', '').strip(),
            quantity=int(request.form.get('quantity', 0)),
            min_stock_level=int(request.form.get('min_stock_level', 5)),
            unit_cost=float(request.form.get('unit_cost', 0)) if request.form.get('unit_cost') else None,
            supplier=request.form.get('supplier', '').strip(),
            notes=request.form.get('notes', '').strip()
        )
        
        # Manejar fecha de vencimiento
        expiry_date = request.form.get('expiry_date')
        if expiry_date:
            item.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        
        if not item.product_name:
            flash('El nombre del producto es requerido', 'error')
            return redirect(url_for('admin.create_inventory_item'))
        
        db.session.add(item)
        db.session.commit()
        
        flash('Item de inventario creado exitosamente', 'success')
        return redirect(url_for('admin.manage_inventory'))
        
    except ValueError:
        flash('Datos numéricos inválidos', 'error')
        return redirect(url_for('admin.create_inventory_item'))
    except Exception as e:
        db.session.rollback()
        flash('Error al crear el item de inventario', 'error')
        return redirect(url_for('admin.create_inventory_item'))

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Configuraciones del sistema"""
    return render_template('admin/settings.html')
