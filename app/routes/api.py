from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from app.models import db, User, Appointment, Service, AppointmentStatus, UserRole
from datetime import datetime, date, timedelta
import json
import os
from math import radians, cos, sin, asin, sqrt

api_bp = Blueprint('api', __name__)

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API de autenticación"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email y contraseña son requeridos'}), 400
    
    email = data.get('email').strip().lower()
    password = data.get('password')
    
    user = User.query.filter_by(email=email, is_active=True).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.full_name,
                'role': user.role.value
            }
        })
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@api_bp.route('/appointments', methods=['GET'])
@jwt_required()
def api_get_appointments():
    """Obtener citas del usuario autenticado"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    # Filtros
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Appointment.query
    
    if user.role == UserRole.CLIENT:
        query = query.filter_by(client_id=user.id)
    elif user.role == UserRole.EMPLOYEE:
        query = query.filter_by(employee_id=user.id)
    elif user.role != UserRole.ADMIN:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    if status:
        try:
            status_enum = AppointmentStatus(status)
            query = query.filter_by(status=status_enum)
        except ValueError:
            return jsonify({'error': 'Estado inválido'}), 400
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Appointment.appointment_date >= date_from)
        except ValueError:
            return jsonify({'error': 'Formato de fecha_desde inválido'}), 400
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Appointment.appointment_date <= date_to)
        except ValueError:
            return jsonify({'error': 'Formato de fecha_hasta inválido'}), 400
    
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.start_time.desc()
    ).all()
    
    return jsonify({
        'appointments': [{
            'id': apt.id,
            'client_name': apt.client.full_name,
            'employee_name': apt.employee.full_name if apt.employee else None,
            'date': apt.appointment_date.isoformat(),
            'start_time': apt.start_time.strftime('%H:%M'),
            'end_time': apt.end_time.strftime('%H:%M') if apt.end_time else None,
            'status': apt.status.value,
            'total_price': float(apt.total_price) if apt.total_price else None,
            'services': [service.name for service in apt.services],
            'notes': apt.notes,
            'confirmation_code': apt.confirmation_code
        } for apt in appointments]
    })

@api_bp.route('/appointments', methods=['POST'])
@jwt_required()
def api_create_appointment():
    """Crear nueva cita"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos JSON requeridos'}), 400
    
    try:
        # Validar datos requeridos
        required_fields = ['appointment_date', 'start_time', 'services']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} es requerido'}), 400
        
        appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        service_ids = data['services']
        
        # Para clientes, la cita es para ellos mismos
        if user.role == UserRole.CLIENT:
            client_id = user.id
        else:
            client_id = data.get('client_id')
            if not client_id:
                return jsonify({'error': 'client_id es requerido'}), 400
        
        employee_id = data.get('employee_id')
        notes = data.get('notes', '')
        
        # Validaciones
        if appointment_date < date.today():
            return jsonify({'error': 'No se pueden crear citas en fechas pasadas'}), 400
        
        if not service_ids:
            return jsonify({'error': 'Debe seleccionar al menos un servicio'}), 400
        
        # Verificar servicios
        services = Service.query.filter(Service.id.in_(service_ids), Service.is_active == True).all()
        if len(services) != len(service_ids):
            return jsonify({'error': 'Algunos servicios no son válidos'}), 400
        
        # Calcular duración y precio
        total_duration = sum(service.duration_minutes for service in services)
        end_time = (datetime.combine(date.today(), start_time) + timedelta(minutes=total_duration)).time()
        total_price = sum(service.price for service in services)
        
        # Crear cita
        appointment = Appointment(
            client_id=client_id,
            employee_id=employee_id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status=AppointmentStatus.PENDING,
            notes=notes,
            total_price=total_price,
            confirmation_code=f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        db.session.add(appointment)
        db.session.flush()
        
        appointment.services = services
        db.session.commit()
        
        return jsonify({
            'id': appointment.id,
            'confirmation_code': appointment.confirmation_code,
            'message': 'Cita creada exitosamente'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Formato de datos inválido'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_bp.route('/appointments/<int:id>/status', methods=['PUT'])
@jwt_required()
def api_update_appointment_status(id):
    """Actualizar estado de una cita"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    appointment = Appointment.query.get(id)
    if not appointment:
        return jsonify({'error': 'Cita no encontrada'}), 404
    
    # Verificar permisos
    if user.role == UserRole.CLIENT and appointment.client_id != user.id:
        return jsonify({'error': 'No tienes permiso para modificar esta cita'}), 403
    elif user.role == UserRole.EMPLOYEE and appointment.employee_id != user.id:
        return jsonify({'error': 'No tienes permiso para modificar esta cita'}), 403
    
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Campo status es requerido'}), 400
    
    try:
        new_status = AppointmentStatus(data['status'])
        
        # Los clientes solo pueden cancelar
        if user.role == UserRole.CLIENT and new_status != AppointmentStatus.CANCELLED:
            return jsonify({'error': 'Los clientes solo pueden cancelar citas'}), 403
        
        appointment.status = new_status
        db.session.commit()
        
        return jsonify({'message': 'Estado actualizado exitosamente'})
        
    except ValueError:
        return jsonify({'error': 'Estado inválido'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@api_bp.route('/services', methods=['GET'])
def api_get_services():
    """Obtener lista de servicios activos"""
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '').strip()
    
    query = Service.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Service.name.contains(search))
    
    services = query.order_by(Service.name).all()
    
    return jsonify({
        'services': [{
            'id': service.id,
            'name': service.name,
            'description': service.description,
            'price': float(service.price),
            'duration_minutes': service.duration_minutes,
            'category': service.category.name if service.category else None,
            'image_url': service.image_url,
            'loyalty_points_earned': service.loyalty_points_earned
        } for service in services]
    })

@api_bp.route('/available_slots', methods=['GET'])
def api_get_available_slots():
    """Obtener horarios disponibles para una fecha"""
    date_str = request.args.get('date')
    employee_id = request.args.get('employee_id', type=int)
    service_ids = request.args.getlist('services', type=int)
    
    if not date_str:
        return jsonify({'error': 'Parámetro date es requerido'}), 400
    
    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    if appointment_date < date.today():
        return jsonify({'error': 'No se pueden consultar fechas pasadas'}), 400
    
    # Calcular duración total si se proporcionan servicios
    total_duration = 30  # duración por defecto
    if service_ids:
        services = Service.query.filter(Service.id.in_(service_ids)).all()
        if services:
            total_duration = sum(service.duration_minutes for service in services)
    
    # Obtener citas existentes para la fecha
    existing_appointments = Appointment.query.filter(
        Appointment.appointment_date == appointment_date,
        Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
    )
    
    if employee_id:
        existing_appointments = existing_appointments.filter_by(employee_id=employee_id)
    
    existing_appointments = existing_appointments.all()
    
    # Generar slots disponibles (9 AM a 6 PM)
    available_slots = []
    start_hour = 9
    end_hour = 18
    slot_interval = 30  # intervalos de 30 minutos
    
    current_time = datetime.combine(appointment_date, datetime.min.time().replace(hour=start_hour))
    end_time = datetime.combine(appointment_date, datetime.min.time().replace(hour=end_hour))
    
    while current_time < end_time:
        slot_end = current_time + timedelta(minutes=total_duration)
        
        # Verificar si el slot está disponible
        is_available = True
        for appointment in existing_appointments:
            apt_start = datetime.combine(appointment_date, appointment.start_time)
            apt_end = datetime.combine(appointment_date, appointment.end_time) if appointment.end_time else apt_start + timedelta(minutes=60)
            
            # Verificar superposición
            if (current_time < apt_end and slot_end > apt_start):
                is_available = False
                break
        
        if is_available and slot_end.time() <= datetime.min.time().replace(hour=end_hour):
            available_slots.append(current_time.strftime('%H:%M'))
        
        current_time += timedelta(minutes=slot_interval)
    
    return jsonify({'available_slots': available_slots})

@api_bp.route('/employees', methods=['GET'])
def api_get_employees():
    """Obtener lista de empleados activos"""
    employees = User.query.filter_by(role=UserRole.EMPLOYEE, is_active=True).all()
    
    return jsonify({
        'employees': [{
            'id': employee.id,
            'name': employee.full_name,
            'email': employee.email,
            'phone': employee.phone
        } for employee in employees]
    })

@api_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def api_get_user_profile():
    """Obtener perfil del usuario autenticado"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'role': user.role.value,
        'address': user.address,
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'emergency_contact': user.emergency_contact,
        'emergency_phone': user.emergency_phone,
        'loyalty_points': user.total_loyalty_points,
        'created_at': user.created_at.isoformat()
    })

# ========== RUTAS API PARA DIRECTORIO DE NEGOCIOS ==========

def haversine(lon1, lat1, lon2, lat2):
    """
    Calcular la distancia entre dos puntos en la Tierra usando la fórmula de Haversine
    """
    # Convertir coordenadas decimales a radianes
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Fórmula de Haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radio de la Tierra en kilómetros
    return c * r

@api_bp.route('/config/mapbox', methods=['GET'])
def get_mapbox_config():
    """Obtener configuración de Mapbox"""
    return jsonify({
        'accessToken': os.getenv('MAPBOX_ACCESS_TOKEN'),
        'style': 'mapbox://styles/mapbox/streets-v12',
        'center': [-99.1332, 19.4326],  # Ciudad de México
        'zoom': 11
    })

@api_bp.route('/businesses/search', methods=['GET'])
def search_businesses():
    """Buscar negocios por ubicación y filtros"""
    try:
        # Obtener parámetros de la consulta
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', default=10, type=float)  # km
        business_type = request.args.get('type')
        query = request.args.get('q', '').strip()
        
        # Importar modelo Business
        from app.models import Business
        
        # Construir consulta base
        businesses_query = Business.query.filter(Business.status == 'ACTIVE')
        
        # Filtrar por tipo de negocio si se especifica
        if business_type:
            businesses_query = businesses_query.filter(Business.business_type == business_type)
        
        # Filtrar por texto de búsqueda
        if query:
            businesses_query = businesses_query.filter(
                db.or_(
                    Business.name.ilike(f'%{query}%'),
                    Business.description.ilike(f'%{query}%'),
                    Business.city.ilike(f'%{query}%'),
                    Business.address.ilike(f'%{query}%')
                )
            )
        
        # Obtener todos los negocios que coinciden con los filtros
        businesses = businesses_query.all()
        
        # Filtrar por proximidad si se proporcionan coordenadas
        if lat and lng:
            filtered_businesses = []
            for business in businesses:
                if business.latitude and business.longitude:
                    distance = haversine(lng, lat, float(business.longitude), float(business.latitude))
                    if distance <= radius:
                        filtered_businesses.append({
                            'business': business,
                            'distance': round(distance, 2)
                        })
            
            # Ordenar por distancia
            filtered_businesses.sort(key=lambda x: x['distance'])
            businesses = [item['business'] for item in filtered_businesses]
            distances = {item['business'].id: item['distance'] for item in filtered_businesses}
        else:
            distances = {}
        
        # Formatear respuesta
        result = []
        for business in businesses:
            business_data = {
                'id': business.id,
                'name': business.name,
                'slug': business.slug,
                'description': business.description,
                'business_type': business.business_type,
                'phone': business.phone,
                'email': business.email,
                'website': business.website,
                'address': business.address,
                'city': business.city,
                'state': business.state,
                'country': business.country,
                'postal_code': business.postal_code,
                'latitude': float(business.latitude) if business.latitude else None,
                'longitude': float(business.longitude) if business.longitude else None,
                'rating_average': float(business.rating_average) if business.rating_average else 0,
                'reviews_count': business.reviews_count,
                'allow_online_booking': business.allow_online_booking,
                'primary_color': business.primary_color,
                'secondary_color': business.secondary_color,
                'logo_url': business.logo_url,
                'cover_image_url': business.cover_image_url,
                'instagram_handle': business.instagram_handle,
                'facebook_url': business.facebook_url,
                'whatsapp_number': business.whatsapp_number,
                'business_hours': json.loads(business.business_hours) if business.business_hours else {},
                'verified': business.location_verified,
                'status': business.status
            }
            
            # Agregar distancia si está disponible
            if business.id in distances:
                business_data['distance'] = distances[business.id]
            
            result.append(business_data)
        
        return jsonify({
            'businesses': result,
            'total': len(result),
            'center': {'lat': lat, 'lng': lng} if lat and lng else None,
            'radius': radius
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/businesses/<int:business_id>', methods=['GET'])
def get_business_detail(business_id):
    """Obtener detalles de un negocio específico"""
    try:
        from app.models import Business
        
        business = Business.query.filter_by(id=business_id, status='ACTIVE').first()
        
        if not business:
            return jsonify({'error': 'Negocio no encontrado'}), 404
        
        return jsonify({
            'id': business.id,
            'name': business.name,
            'slug': business.slug,
            'description': business.description,
            'business_type': business.business_type,
            'phone': business.phone,
            'email': business.email,
            'website': business.website,
            'address': business.address,
            'city': business.city,
            'state': business.state,
            'country': business.country,
            'postal_code': business.postal_code,
            'latitude': float(business.latitude) if business.latitude else None,
            'longitude': float(business.longitude) if business.longitude else None,
            'rating_average': float(business.rating_average) if business.rating_average else 0,
            'reviews_count': business.reviews_count,
            'allow_online_booking': business.allow_online_booking,
            'primary_color': business.primary_color,
            'secondary_color': business.secondary_color,
            'logo_url': business.logo_url,
            'cover_image_url': business.cover_image_url,
            'gallery_images': json.loads(business.gallery_images) if business.gallery_images else [],
            'instagram_handle': business.instagram_handle,
            'facebook_url': business.facebook_url,
            'whatsapp_number': business.whatsapp_number,
            'business_hours': json.loads(business.business_hours) if business.business_hours else {},
            'verified': business.location_verified,
            'status': business.status,
            'timezone': business.timezone,
            'currency': business.currency,
            'language': business.language,
            'created_at': business.created_at.isoformat(),
            'updated_at': business.updated_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/businesses/types', methods=['GET'])
def get_business_types():
    """Obtener tipos de negocios disponibles"""
    return jsonify({
        'types': [
            {'value': 'NAIL_SALON', 'label': 'Salón de Uñas'},
            {'value': 'BEAUTY_SALON', 'label': 'Salón de Belleza'},
            {'value': 'SPA', 'label': 'Spa'},
            {'value': 'BARBERSHOP', 'label': 'Barbería'},
            {'value': 'STUDIO', 'label': 'Studio'}
        ]
    })
