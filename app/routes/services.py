from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import db, Service, ServiceCategory, UserRole
from werkzeug.utils import secure_filename
import os

services_bp = Blueprint('services', __name__)

@services_bp.route('/')
def list_services():
    """Lista pública de servicios"""
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '').strip()
    
    query = Service.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Service.name.contains(search))
    
    services = query.order_by(Service.name).all()
    categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.name).all()
    
    return render_template('services/list.html', 
                         services=services, 
                         categories=categories,
                         selected_category=category_id,
                         search_term=search)

@services_bp.route('/<int:id>')
def view_service(id):
    """Ver detalles de un servicio"""
    service = Service.query.get_or_404(id)
    
    if not service.is_active:
        flash('Este servicio no está disponible', 'error')
        return redirect(url_for('services.list_services'))
    
    # Servicios relacionados de la misma categoría
    related_services = Service.query.filter(
        Service.category_id == service.category_id,
        Service.id != service.id,
        Service.is_active == True
    ).limit(4).all()
    
    return render_template('services/view.html', 
                         service=service,
                         related_services=related_services)

@services_bp.route('/manage')
@login_required
def manage_services():
    """Gestión de servicios (solo admin/empleados)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EMPLOYEE]:
        flash('Acceso denegado', 'error')
        return redirect(url_for('services.list_services'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category', type=int)
    
    query = Service.query
    
    if search:
        query = query.filter(Service.name.contains(search))
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    services = query.order_by(Service.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    
    return render_template('services/manage.html', 
                         services=services,
                         categories=categories,
                         search_term=search,
                         selected_category=category_id)

@services_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_service():
    """Crear nuevo servicio (solo admin)"""
    if current_user.role != UserRole.ADMIN:
        flash('Solo los administradores pueden crear servicios', 'error')
        return redirect(url_for('services.manage_services'))
    
    if request.method == 'GET':
        categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.name).all()
        return render_template('services/create.html', categories=categories)
    
    # Procesar POST
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = float(request.form.get('price', 0))
        duration_minutes = int(request.form.get('duration_minutes', 0))
        category_id = request.form.get('category_id', type=int)
        loyalty_points_earned = int(request.form.get('loyalty_points_earned', 0))
        
        # Validaciones
        if not name:
            flash('El nombre del servicio es requerido', 'error')
            return redirect(url_for('services.create_service'))
        
        if price <= 0:
            flash('El precio debe ser mayor a 0', 'error')
            return redirect(url_for('services.create_service'))
        
        if duration_minutes <= 0:
            flash('La duración debe ser mayor a 0 minutos', 'error')
            return redirect(url_for('services.create_service'))
        
        # Verificar que la categoría existe
        if category_id:
            category = ServiceCategory.query.get(category_id)
            if not category:
                flash('Categoría inválida', 'error')
                return redirect(url_for('services.create_service'))
        
        # Crear servicio
        service = Service(
            name=name,
            description=description,
            price=price,
            duration_minutes=duration_minutes,
            category_id=category_id,
            loyalty_points_earned=loyalty_points_earned
        )
        
        # Manejar imagen si se subió
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Agregar timestamp para evitar duplicados
                import time
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                service.image_url = f"uploads/{filename}"
        
        db.session.add(service)
        db.session.commit()
        
        flash('Servicio creado exitosamente', 'success')
        return redirect(url_for('services.manage_services'))
        
    except ValueError:
        flash('Datos numéricos inválidos', 'error')
        return redirect(url_for('services.create_service'))
    except Exception as e:
        db.session.rollback()
        flash('Error al crear el servicio', 'error')
        return redirect(url_for('services.create_service'))

@services_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_service(id):
    """Editar servicio (solo admin)"""
    if current_user.role != UserRole.ADMIN:
        flash('Solo los administradores pueden editar servicios', 'error')
        return redirect(url_for('services.manage_services'))
    
    service = Service.query.get_or_404(id)
    
    if request.method == 'GET':
        categories = ServiceCategory.query.filter_by(is_active=True).order_by(ServiceCategory.name).all()
        return render_template('services/edit.html', service=service, categories=categories)
    
    # Procesar POST
    try:
        service.name = request.form.get('name', '').strip()
        service.description = request.form.get('description', '').strip()
        service.price = float(request.form.get('price', 0))
        service.duration_minutes = int(request.form.get('duration_minutes', 0))
        service.category_id = request.form.get('category_id', type=int)
        service.loyalty_points_earned = int(request.form.get('loyalty_points_earned', 0))
        service.is_active = bool(request.form.get('is_active'))
        
        # Validaciones
        if not service.name:
            flash('El nombre del servicio es requerido', 'error')
            return redirect(url_for('services.edit_service', id=id))
        
        if service.price <= 0:
            flash('El precio debe ser mayor a 0', 'error')
            return redirect(url_for('services.edit_service', id=id))
        
        if service.duration_minutes <= 0:
            flash('La duración debe ser mayor a 0 minutos', 'error')
            return redirect(url_for('services.edit_service', id=id))
        
        # Manejar nueva imagen si se subió
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                service.image_url = f"uploads/{filename}"
        
        db.session.commit()
        
        flash('Servicio actualizado exitosamente', 'success')
        return redirect(url_for('services.manage_services'))
        
    except ValueError:
        flash('Datos numéricos inválidos', 'error')
        return redirect(url_for('services.edit_service', id=id))
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el servicio', 'error')
        return redirect(url_for('services.edit_service', id=id))

@services_bp.route('/<int:id>/toggle_status', methods=['POST'])
@login_required
def toggle_service_status(id):
    """Activar/desactivar servicio (solo admin)"""
    if current_user.role != UserRole.ADMIN:
        flash('Solo los administradores pueden cambiar el estado de servicios', 'error')
        return redirect(url_for('services.manage_services'))
    
    service = Service.query.get_or_404(id)
    
    try:
        service.is_active = not service.is_active
        db.session.commit()
        
        status = "activado" if service.is_active else "desactivado"
        flash(f'Servicio {status} exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al cambiar el estado del servicio', 'error')
    
    return redirect(url_for('services.manage_services'))

@services_bp.route('/categories/manage')
@login_required
def manage_categories():
    """Gestión de categorías de servicios (solo admin)"""
    if current_user.role != UserRole.ADMIN:
        flash('Acceso denegado', 'error')
        return redirect(url_for('services.list_services'))
    
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    return render_template('services/manage_categories.html', categories=categories)

@services_bp.route('/categories/create', methods=['POST'])
@login_required
def create_category():
    """Crear nueva categoría (solo admin)"""
    if current_user.role != UserRole.ADMIN:
        flash('Solo los administradores pueden crear categorías', 'error')
        return redirect(url_for('services.manage_categories'))
    
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        color_code = request.form.get('color_code', '').strip()
        icon = request.form.get('icon', '').strip()
        
        if not name:
            flash('El nombre de la categoría es requerido', 'error')
            return redirect(url_for('services.manage_categories'))
        
        # Verificar que no exista una categoría con el mismo nombre
        if ServiceCategory.query.filter_by(name=name).first():
            flash('Ya existe una categoría con este nombre', 'error')
            return redirect(url_for('services.manage_categories'))
        
        category = ServiceCategory(
            name=name,
            description=description,
            color_code=color_code,
            icon=icon
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Categoría creada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al crear la categoría', 'error')
    
    return redirect(url_for('services.manage_categories'))

def allowed_file(filename):
    """Verificar si la extensión del archivo está permitida"""
    from flask import current_app
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
