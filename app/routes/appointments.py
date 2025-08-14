from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import db, Appointment, Service, User, AppointmentStatus, UserRole
from datetime import datetime, date, time, timedelta
import uuid

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/')
@login_required
def list_appointments():
    """Lista de citas según el rol del usuario"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    date_filter = request.args.get('date', '')
    
    # Construir query base según el rol
    if current_user.role == UserRole.CLIENT:
        query = Appointment.query.filter_by(client_id=current_user.id)
    elif current_user.role == UserRole.EMPLOYEE:
        query = Appointment.query.filter_by(employee_id=current_user.id)
    elif current_user.role == UserRole.ADMIN:
        query = Appointment.query
    else:
        flash('Acceso denegado', 'error')
        return redirect(url_for('main.index'))
    
    # Aplicar filtros
    if status_filter and status_filter in [status.value for status in AppointmentStatus]:
        query = query.filter_by(status=AppointmentStatus(status_filter))
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=filter_date)
        except ValueError:
            flash('Fecha inválida', 'error')
    
    # Paginación
    appointments = query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.start_time.desc()
    ).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('appointments/list.html', 
                         appointments=appointments,
                         status_filter=status_filter,
                         date_filter=date_filter,
                         AppointmentStatus=AppointmentStatus)

@appointments_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_appointment():
    """Crear nueva cita"""
    if request.method == 'GET':
        # Solo clientes pueden crear citas para sí mismos
        # Admins y empleados pueden crear citas para cualquier cliente
        if current_user.role == UserRole.CLIENT:
            clients = [current_user]
        else:
            clients = User.query.filter_by(role=UserRole.CLIENT, is_active=True).all()
        
        employees = User.query.filter_by(role=UserRole.EMPLOYEE, is_active=True).all()
        services = Service.query.filter_by(is_active=True).all()
        today = date.today()
        
        return render_template('appointments/create.html',
                             clients=clients,
                             employees=employees,
                             services=services,
                             today=today)
    
    # Procesar POST
    try:
        # Validar datos
        client_id = request.form.get('client_id', type=int)
        employee_id = request.form.get('employee_id', type=int)
        appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        service_ids = request.form.getlist('services', type=int)
        notes = request.form.get('notes', '').strip()
        
        # Validaciones
        if current_user.role == UserRole.CLIENT and client_id != current_user.id:
            flash('No puedes crear citas para otros clientes', 'error')
            return redirect(url_for('appointments.create_appointment'))
        
        if not service_ids:
            flash('Debes seleccionar al menos un servicio', 'error')
            return redirect(url_for('appointments.create_appointment'))
        
        if appointment_date < date.today():
            flash('No puedes reservar citas en fechas pasadas', 'error')
            return redirect(url_for('appointments.create_appointment'))
        
        # Verificar que los servicios existen
        services = Service.query.filter(Service.id.in_(service_ids)).all()
        if len(services) != len(service_ids):
            flash('Algunos servicios seleccionados no son válidos', 'error')
            return redirect(url_for('appointments.create_appointment'))
        
        # Calcular tiempo de fin y precio total
        total_duration = sum(service.duration_minutes for service in services)
        end_time = (datetime.combine(date.today(), start_time) + timedelta(minutes=total_duration)).time()
        total_price = sum(service.price for service in services)
        
        # Crear la cita
        appointment = Appointment(
            client_id=client_id,
            employee_id=employee_id,
            appointment_date=appointment_date,
            start_time=start_time,
            end_time=end_time,
            status=AppointmentStatus.PENDING,
            notes=notes,
            total_price=total_price,
            confirmation_code=str(uuid.uuid4())[:8].upper()
        )
        
        db.session.add(appointment)
        db.session.flush()  # Para obtener el ID
        
        # Asociar servicios
        appointment.services = services
        
        db.session.commit()
        
        flash(f'Cita creada exitosamente. Código de confirmación: {appointment.confirmation_code}', 'success')
        return redirect(url_for('appointments.view_appointment', id=appointment.id))
        
    except ValueError as e:
        flash('Datos inválidos en el formulario', 'error')
        return redirect(url_for('appointments.create_appointment'))
    except Exception as e:
        db.session.rollback()
        flash('Error al crear la cita. Inténtalo nuevamente.', 'error')
        return redirect(url_for('appointments.create_appointment'))

@appointments_bp.route('/<int:id>')
@login_required
def view_appointment(id):
    """Ver detalles de una cita"""
    appointment = Appointment.query.get_or_404(id)
    
    # Verificar permisos
    if (current_user.role == UserRole.CLIENT and appointment.client_id != current_user.id) or \
       (current_user.role == UserRole.EMPLOYEE and appointment.employee_id != current_user.id):
        if current_user.role != UserRole.ADMIN:
            flash('No tienes permiso para ver esta cita', 'error')
            return redirect(url_for('appointments.list_appointments'))
    
    return render_template('appointments/view.html', appointment=appointment)

@appointments_bp.route('/<int:id>/update_status', methods=['POST'])
@login_required
def update_status(id):
    """Actualizar estado de una cita"""
    appointment = Appointment.query.get_or_404(id)
    new_status = request.form.get('status')
    
    # Verificar permisos
    if current_user.role == UserRole.CLIENT:
        # Los clientes solo pueden cancelar sus propias citas
        if appointment.client_id != current_user.id or new_status != AppointmentStatus.CANCELLED.value:
            flash('No tienes permiso para realizar esta acción', 'error')
            return redirect(url_for('appointments.view_appointment', id=id))
    elif current_user.role == UserRole.EMPLOYEE:
        # Los empleados pueden actualizar sus propias citas
        if appointment.employee_id != current_user.id:
            flash('No tienes permiso para realizar esta acción', 'error')
            return redirect(url_for('appointments.view_appointment', id=id))
    
    # Validar nuevo estado
    try:
        status_enum = AppointmentStatus(new_status)
        appointment.status = status_enum
        
        # Agregar notas internas si es necesario
        internal_notes = request.form.get('internal_notes', '').strip()
        if internal_notes:
            current_notes = appointment.internal_notes or ''
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            new_note = f"\n[{timestamp} - {current_user.full_name}]: {internal_notes}"
            appointment.internal_notes = current_notes + new_note
        
        db.session.commit()
        flash('Estado de la cita actualizado exitosamente', 'success')
        
    except ValueError:
        flash('Estado inválido', 'error')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el estado', 'error')
    
    return redirect(url_for('appointments.view_appointment', id=id))

@appointments_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    """Cancelar una cita"""
    appointment = Appointment.query.get_or_404(id)
    
    # Verificar permisos
    if current_user.role == UserRole.CLIENT and appointment.client_id != current_user.id:
        flash('No puedes cancelar esta cita', 'error')
        return redirect(url_for('appointments.list_appointments'))
    
    if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
        flash('Esta cita no puede ser cancelada', 'error')
        return redirect(url_for('appointments.view_appointment', id=id))
    
    try:
        appointment.status = AppointmentStatus.CANCELLED
        
        # Agregar nota de cancelación
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        cancel_note = f"\n[{timestamp}]: Cita cancelada por {current_user.full_name}"
        appointment.internal_notes = (appointment.internal_notes or '') + cancel_note
        
        db.session.commit()
        flash('Cita cancelada exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error al cancelar la cita', 'error')
    
    return redirect(url_for('appointments.list_appointments'))

@appointments_bp.route('/calendar')
@login_required
def calendar():
    """Vista de calendario de citas"""
    # Obtener mes y año de los parámetros
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    # Validar mes y año
    if month < 1 or month > 12:
        month = datetime.now().month
    if year < 2020 or year > 2030:
        year = datetime.now().year
    
    # Construir query base según el rol
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    query = Appointment.query.filter(
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date <= end_date
    )
    
    if current_user.role == UserRole.CLIENT:
        query = query.filter_by(client_id=current_user.id)
    elif current_user.role == UserRole.EMPLOYEE:
        query = query.filter_by(employee_id=current_user.id)
    
    appointments = query.all()
    
    # Organizar citas por fecha
    appointments_by_date = {}
    for appointment in appointments:
        date_key = appointment.appointment_date.strftime('%Y-%m-%d')
        if date_key not in appointments_by_date:
            appointments_by_date[date_key] = []
        appointments_by_date[date_key].append(appointment)
    
    return render_template('appointments/calendar.html',
                         appointments_by_date=appointments_by_date,
                         current_month=month,
                         current_year=year)
