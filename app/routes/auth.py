from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import db, User, UserRole
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)

def validate_password(password):
    """Validar que la contraseña cumpla con los requisitos mínimos"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una letra mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una letra minúscula"
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"
    return True, "Contraseña válida"

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Función de login mejorada con mejor manejo de errores"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember = bool(request.form.get('remember'))
            
            # Validación básica
            if not email or not password:
                flash('Por favor completa todos los campos', 'error')
                return render_template('auth/login.html')
            
            # Validar formato de email
            try:
                validate_email(email)
            except EmailNotValidError:
                flash('Por favor ingresa un email válido', 'error')
                return render_template('auth/login.html')
            
            # Buscar usuario en la base de datos
            user = User.query.filter_by(email=email).first()
            
            if not user:
                flash('Email o contraseña incorrectos', 'error')
                return render_template('auth/login.html')
            
            # Verificar contraseña
            if not user.check_password(password):
                flash('Email o contraseña incorrectos', 'error')
                return render_template('auth/login.html')
            
            # Verificar si la cuenta está activa
            if not user.is_active:
                flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'error')
                return render_template('auth/login.html')
            
            # Login exitoso
            login_user(user, remember=remember)
            
            # Actualizar último login
            try:
                user.last_login = datetime.now()
                user.updated_at = datetime.now()
                db.session.commit()
            except Exception as e:
                print(f"Error actualizando last_login: {e}")
                db.session.rollback()
                # No fallar el login por esto
            
            # Mensaje de bienvenida
            flash(f'¡Bienvenida {user.first_name}!', 'success')
            
            # Redirigir según el rol del usuario
            next_page = request.args.get('next')
            
            try:
                if user.role == UserRole.ADMIN:
                    redirect_url = next_page or url_for('admin.dashboard')
                elif user.role == UserRole.EMPLOYEE:
                    redirect_url = next_page or url_for('main.employee_dashboard')
                else:
                    redirect_url = next_page or url_for('main.client_dashboard')
                
                return redirect(redirect_url)
            
            except Exception as e:
                print(f"Error en redirección: {e}")
                # Fallback a página principal
                return redirect(next_page or url_for('main.index'))
        
        except Exception as e:
            print(f"Error inesperado en login: {e}")
            flash('Error interno del servidor. Inténtalo de nuevo.', 'error')
            return render_template('auth/login.html')
    
    # GET request - mostrar formulario
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        data = request.form
        
        # Validar datos requeridos
        required_fields = ['first_name', 'last_name', 'email', 'password', 'phone']
        for field in required_fields:
            if not data.get(field, '').strip():
                flash(f'El campo {field.replace("_", " ")} es requerido', 'error')
                return render_template('auth/register.html')
        
        email = data.get('email').strip().lower()
        password = data.get('password')
        
        # Validar email
        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Por favor ingresa un email válido', 'error')
            return render_template('auth/register.html')
        
        # Verificar si el email ya existe
        if User.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con este email', 'error')
            return render_template('auth/register.html')
        
        # Validar contraseña
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return render_template('auth/register.html')
        
        # Crear nuevo usuario
        user = User(
            first_name=data.get('first_name').strip(),
            last_name=data.get('last_name').strip(),
            email=email,
            phone=data.get('phone').strip(),
            role=UserRole.CLIENT
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            flash('Cuenta creada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la cuenta. Inténtalo nuevamente.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    data = request.form
    
    try:
        current_user.first_name = data.get('first_name', '').strip()
        current_user.last_name = data.get('last_name', '').strip()
        current_user.phone = data.get('phone', '').strip()
        current_user.address = data.get('address', '').strip()
        current_user.emergency_contact = data.get('emergency_contact', '').strip()
        current_user.emergency_phone = data.get('emergency_phone', '').strip()
        
        # Si se proporciona fecha de nacimiento
        date_of_birth = data.get('date_of_birth')
        if date_of_birth:
            from datetime import datetime
            current_user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        db.session.commit()
        flash('Perfil actualizado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar el perfil', 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('Todos los campos son requeridos', 'error')
        return redirect(url_for('auth.profile'))
    
    if not current_user.check_password(current_password):
        flash('La contraseña actual es incorrecta', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('Las contraseñas no coinciden', 'error')
        return redirect(url_for('auth.profile'))
    
    # Validar nueva contraseña
    is_valid, message = validate_password(new_password)
    if not is_valid:
        flash(message, 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Contraseña cambiada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al cambiar la contraseña', 'error')
    
    return redirect(url_for('auth.profile'))
