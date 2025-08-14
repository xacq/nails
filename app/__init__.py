from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_moment import Moment
from config import config
import os

# Inicializar extensiones
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
jwt = JWTManager()
csrf = CSRFProtect()
moment = Moment()

# Importar db desde models para que esté disponible
from app.models import db

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar la base de datos
    db.init_app(app)
    
    # Configurar extensiones
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    mail.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    csrf.init_app(app)
    moment.init_app(app)
    
    # Crear directorio de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Registrar Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.appointments import appointments_bp
    from app.routes.services import services_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(appointments_bp, url_prefix='/appointments')
    app.register_blueprint(services_bp, url_prefix='/services')
    
    # Configurar el cargador de usuarios para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Context processors
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        from datetime import datetime
        return dict(current_user=current_user, current_year=datetime.now().year)
    
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Filtros de plantilla personalizados
    @app.template_filter('currency')
    def currency_filter(amount):
        return f"${amount:,.2f}"
    
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%d/%m/%Y %H:%M'):
        return value.strftime(format) if value else ''
    
    @app.template_filter('date_format')
    def date_format(value, format='%d/%m/%Y'):
        return value.strftime(format) if value else ''
    
    return app
