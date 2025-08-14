from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    CLIENT = "client"

class AppointmentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    REFUNDED = "refunded"

# Tabla de asociación para servicios en citas
appointment_services = db.Table('appointment_services',
    db.Column('appointment_id', db.Integer, db.ForeignKey('appointments.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('services.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.CLIENT)
    profile_picture = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relaciones
    appointments_as_client = db.relationship('Appointment', foreign_keys='Appointment.client_id', backref='client', lazy='dynamic')
    appointments_as_employee = db.relationship('Appointment', foreign_keys='Appointment.employee_id', backref='employee', lazy='dynamic')
    payments = db.relationship('Payment', foreign_keys='Payment.client_id', backref='client', lazy='dynamic')
    payments_processed = db.relationship('Payment', foreign_keys='Payment.processed_by', backref='processor', lazy='dynamic')
    loyalty_points = db.relationship('LoyaltyPoint', backref='user', lazy='dynamic')
    reviews = db.relationship('Review', foreign_keys='Review.client_id', backref='client', lazy='dynamic')
    reviews_received = db.relationship('Review', foreign_keys='Review.employee_id', backref='employee_reviewed', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_loyalty_points(self):
        return sum(point.points for point in self.loyalty_points if not point.used)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Service(db.Model):
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)  # Duración en minutos
    category_id = db.Column(db.Integer, db.ForeignKey('service_categories.id'))
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    loyalty_points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    appointments = db.relationship('Appointment', secondary=appointment_services, back_populates='services')
    
    def __repr__(self):
        return f'<Service {self.name}>'

class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color_code = db.Column(db.String(7))  # Para códigos hex de colores
    icon = db.Column(db.String(50))  # Para iconos de Font Awesome
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    services = db.relationship('Service', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ServiceCategory {self.name}>'

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    appointment_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)  # Solo para staff
    total_price = db.Column(db.Numeric(10, 2))
    confirmation_code = db.Column(db.String(20), unique=True)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    services = db.relationship('Service', secondary=appointment_services, back_populates='appointments')
    payments = db.relationship('Payment', backref='appointment', lazy='dynamic')
    
    @property
    def duration_minutes(self):
        return sum(service.duration_minutes for service in self.services)
    
    @property
    def is_past(self):
        appointment_datetime = datetime.combine(self.appointment_date, self.start_time)
        return appointment_datetime < datetime.now()
    
    def __repr__(self):
        return f'<Appointment {self.id} - {self.appointment_date}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50))  # cash, card, transfer, etc.
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = db.Column(db.String(100))  # Para pagos online
    notes = db.Column(db.Text)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.id} - ${self.amount}>'

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    break_start = db.Column(db.Time)
    break_end = db.Column(db.Time)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación
    employee = db.relationship('User', backref='schedules')
    
    def __repr__(self):
        return f'<Schedule {self.employee_id} - Day {self.day_of_week}>'

class LoyaltyPoint(db.Model):
    __tablename__ = 'loyalty_points'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255))  # appointment, referral, birthday, etc.
    reference_id = db.Column(db.Integer)  # ID de cita o promoción
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LoyaltyPoint {self.user_id} - {self.points}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    appointment = db.relationship('Appointment', backref='reviews')
    # Nota: Las relaciones con User se definen en el modelo User para evitar conflictos de backref
    
    def __repr__(self):
        return f'<Review {self.id} - {self.rating} stars>'

class Promotion(db.Model):
    __tablename__ = 'promotions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    discount_type = db.Column(db.String(20))  # percentage, fixed_amount, loyalty_points
    discount_value = db.Column(db.Numeric(10, 2))
    min_purchase_amount = db.Column(db.Numeric(10, 2))
    max_uses = db.Column(db.Integer)
    current_uses = db.Column(db.Integer, default=0)
    code = db.Column(db.String(50), unique=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self):
        now = datetime.utcnow()
        return (self.is_active and 
                self.start_date <= now <= self.end_date and
                (self.max_uses is None or self.current_uses < self.max_uses))
    
    def __repr__(self):
        return f'<Promotion {self.name}>'

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))  # nail_polish, tools, supplies, etc.
    brand = db.Column(db.String(50))
    color = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=5)
    unit_cost = db.Column(db.Numeric(10, 2))
    supplier = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.min_stock_level
    
    @property
    def is_expired(self):
        return self.expiry_date and self.expiry_date < date.today()
    
    def __repr__(self):
        return f'<Inventory {self.product_name}>'


# ========== MODELO BUSINESS PARA DIRECTORIO MULTI-TENANT ==========

class BusinessType(Enum):
    NAIL_SALON = "NAIL_SALON"
    BEAUTY_SALON = "BEAUTY_SALON"
    SPA = "SPA"
    BARBERSHOP = "BARBERSHOP"
    STUDIO = "STUDIO"

class BusinessStatus(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"

class Business(db.Model):
    __tablename__ = 'businesses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    business_type = db.Column(db.Enum(BusinessType), default=BusinessType.NAIL_SALON)
    
    # Información de contacto
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    website = db.Column(db.String(255))
    
    # Ubicación
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20))
    latitude = db.Column(db.Numeric(10, 8))
    longitude = db.Column(db.Numeric(11, 8))
    location_verified = db.Column(db.Boolean, default=False)
    
    # Configuración
    timezone = db.Column(db.String(50), default='America/Mexico_City')
    currency = db.Column(db.String(3), default='MXN')
    language = db.Column(db.String(5), default='es')
    
    # Redes sociales
    instagram_handle = db.Column(db.String(100))
    facebook_url = db.Column(db.String(255))
    whatsapp_number = db.Column(db.String(20))
    
    # Imágenes
    logo_url = db.Column(db.String(255))
    cover_image_url = db.Column(db.String(255))
    gallery_images = db.Column(db.JSON)  # Array de URLs
    
    # Horarios (JSON)
    operating_hours = db.Column(db.JSON)
    business_hours = db.Column(db.JSON)
    
    # Configuración de negocio
    allow_online_booking = db.Column(db.Boolean, default=True)
    require_deposit = db.Column(db.Boolean, default=False)
    deposit_percentage = db.Column(db.Numeric(5, 2), default=0)
    booking_advance_days = db.Column(db.Integer, default=30)
    booking_advance_hours = db.Column(db.Integer, default=2)
    
    # Métricas
    rating_average = db.Column(db.Numeric(3, 2), default=0)
    reviews_count = db.Column(db.Integer, default=0)
    appointments_total = db.Column(db.Integer, default=0)
    
    # Personalización
    primary_color = db.Column(db.String(7))  # Hex color
    secondary_color = db.Column(db.String(7))  # Hex color
    
    # Estado y timestamps
    status = db.Column(db.Enum(BusinessStatus), default=BusinessStatus.PENDING, index=True)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Índices para búsquedas
    __table_args__ = (
        db.Index('idx_business_location', latitude, longitude),
        db.Index('idx_business_type_status', business_type, status),
        db.Index('idx_business_city_type', city, business_type),
    )
    
    def __repr__(self):
        return f'<Business {self.name}>'
