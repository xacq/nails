#!/usr/bin/env python3
"""
Script para insertar datos de ejemplo en la base de datos
"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Agregar el directorio raíz al path para importar la app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models import db, Business, BusinessType, BusinessStatus

def insert_sample_businesses():
    """Insertar negocios de ejemplo para México"""
    
    businesses_data = [
        {
            'name': 'Nails Studio Roma',
            'slug': 'nails-studio-roma',
            'description': 'Salón de uñas y spa en la Colonia Roma Norte. Especialistas en nail art, manicure y pedicure con productos de alta calidad.',
            'business_type': BusinessType.NAIL_SALON,
            'phone': '5551234567',
            'email': 'contacto@nailsroma.mx',
            'website': 'https://nailsroma.mx',
            'address': 'Av. Álvaro Obregón 123, Col. Roma Norte',
            'city': 'Ciudad de México',
            'state': 'CDMX',
            'country': 'México',
            'postal_code': '06700',
            'latitude': 19.417309,
            'longitude': -99.162037,
            'location_verified': True,
            'timezone': 'America/Mexico_City',
            'currency': 'MXN',
            'language': 'es',
            'instagram_handle': '@nailsroma',
            'facebook_url': 'https://facebook.com/nailsroma',
            'whatsapp_number': '525551234567',
            'business_hours': {
                "monday": {"open": "09:00", "close": "19:00"},
                "tuesday": {"open": "09:00", "close": "19:00"},
                "wednesday": {"open": "09:00", "close": "19:00"},
                "thursday": {"open": "09:00", "close": "19:00"},
                "friday": {"open": "09:00", "close": "20:00"},
                "saturday": {"open": "08:00", "close": "18:00"},
                "sunday": {"closed": True}
            },
            'status': BusinessStatus.ACTIVE,
            'rating_average': 4.8,
            'reviews_count': 25,
            'primary_color': '#e75480',
            'secondary_color': '#f8bbd0'
        },
        {
            'name': 'Beauty Nails Polanco',
            'slug': 'beauty-nails-polanco',
            'description': 'Salón de belleza y uñas de lujo en Polanco. Servicios premium de spa, manicure, pedicure y tratamientos de belleza integral.',
            'business_type': BusinessType.BEAUTY_SALON,
            'phone': '5559876543',
            'email': 'info@beautynailspolanco.mx',
            'website': 'https://beautynailspolanco.mx',
            'address': 'Av. Presidente Masaryk 350, Col. Polanco',
            'city': 'Ciudad de México',
            'state': 'CDMX',
            'country': 'México',
            'postal_code': '11560',
            'latitude': 19.432601,
            'longitude': -99.197222,
            'location_verified': True,
            'timezone': 'America/Mexico_City',
            'currency': 'MXN',
            'language': 'es',
            'instagram_handle': '@beautynailspolanco',
            'facebook_url': 'https://facebook.com/beautynailspolanco',
            'whatsapp_number': '525559876543',
            'business_hours': {
                "monday": {"open": "10:00", "close": "20:00"},
                "tuesday": {"open": "10:00", "close": "20:00"},
                "wednesday": {"open": "10:00", "close": "20:00"},
                "thursday": {"open": "10:00", "close": "20:00"},
                "friday": {"open": "10:00", "close": "21:00"},
                "saturday": {"open": "09:00", "close": "18:00"},
                "sunday": {"closed": True}
            },
            'status': BusinessStatus.ACTIVE,
            'rating_average': 4.9,
            'reviews_count': 40,
            'primary_color': '#6a1b9a',
            'secondary_color': '#ce93d8'
        },
        {
            'name': 'Spa Uñas Guadalajara',
            'slug': 'spa-unas-gdl',
            'description': 'Spa y centro de relajación especializado en uñas en el corazón de Guadalajara. Ambiente tranquilo y servicios profesionales.',
            'business_type': BusinessType.SPA,
            'phone': '3331234567',
            'email': 'hola@spaunasgjd.mx',
            'website': 'https://spaunasgjd.mx',
            'address': 'Av. Vallarta 2345, Col. Americana',
            'city': 'Guadalajara',
            'state': 'Jalisco',
            'country': 'México',
            'postal_code': '44130',
            'latitude': 20.673590,
            'longitude': -103.370433,
            'location_verified': True,
            'timezone': 'America/Mexico_City',
            'currency': 'MXN',
            'language': 'es',
            'instagram_handle': '@spaunasgdl',
            'facebook_url': 'https://facebook.com/spaunasgdl',
            'whatsapp_number': '523331234567',
            'business_hours': {
                "monday": {"open": "09:00", "close": "19:00"},
                "tuesday": {"open": "09:00", "close": "19:00"},
                "wednesday": {"open": "09:00", "close": "19:00"},
                "thursday": {"open": "09:00", "close": "19:00"},
                "friday": {"open": "09:00", "close": "20:00"},
                "saturday": {"open": "08:00", "close": "18:00"},
                "sunday": {"closed": True}
            },
            'status': BusinessStatus.ACTIVE,
            'rating_average': 4.7,
            'reviews_count': 18,
            'primary_color': '#43a047',
            'secondary_color': '#a5d6a7'
        },
        {
            'name': 'Nails Express Condesa',
            'slug': 'nails-express-condesa',
            'description': 'Servicio rápido y profesional de uñas en la Condesa. Ideal para personas ocupadas que buscan calidad y rapidez.',
            'business_type': BusinessType.NAIL_SALON,
            'phone': '5557654321',
            'email': 'contacto@nailsexpresscondesa.mx',
            'address': 'Av. Amsterdam 120, Col. Condesa',
            'city': 'Ciudad de México',
            'state': 'CDMX',
            'country': 'México',
            'postal_code': '06140',
            'latitude': 19.413477,
            'longitude': -99.168826,
            'location_verified': True,
            'timezone': 'America/Mexico_City',
            'currency': 'MXN',
            'language': 'es',
            'instagram_handle': '@nailsexpresscondesa',
            'whatsapp_number': '525557654321',
            'business_hours': {
                "monday": {"open": "08:00", "close": "20:00"},
                "tuesday": {"open": "08:00", "close": "20:00"},
                "wednesday": {"open": "08:00", "close": "20:00"},
                "thursday": {"open": "08:00", "close": "20:00"},
                "friday": {"open": "08:00", "close": "21:00"},
                "saturday": {"open": "07:00", "close": "19:00"},
                "sunday": {"open": "09:00", "close": "17:00"}
            },
            'status': BusinessStatus.ACTIVE,
            'rating_average': 4.6,
            'reviews_count': 32,
            'primary_color': '#ff6b6b',
            'secondary_color': '#ffb3b3'
        },
        {
            'name': 'Studio de Uñas Monterrey',
            'slug': 'studio-unas-monterrey',
            'description': 'Estudio especializado en nail art y diseños únicos en Monterrey. Certificados en las últimas tendencias internacionales.',
            'business_type': BusinessType.STUDIO,
            'phone': '8181234567',
            'email': 'info@studiounasmonterrey.mx',
            'website': 'https://studiounasmonterrey.mx',
            'address': 'Av. Constitución 456, Col. Centro',
            'city': 'Monterrey',
            'state': 'Nuevo León',
            'country': 'México',
            'postal_code': '64000',
            'latitude': 25.686614,
            'longitude': -100.316113,
            'location_verified': True,
            'timezone': 'America/Mexico_City',
            'currency': 'MXN',
            'language': 'es',
            'instagram_handle': '@studiounasmonterrey',
            'facebook_url': 'https://facebook.com/studiounasmonterrey',
            'whatsapp_number': '528181234567',
            'business_hours': {
                "monday": {"open": "10:00", "close": "19:00"},
                "tuesday": {"open": "10:00", "close": "19:00"},
                "wednesday": {"open": "10:00", "close": "19:00"},
                "thursday": {"open": "10:00", "close": "19:00"},
                "friday": {"open": "10:00", "close": "20:00"},
                "saturday": {"open": "09:00", "close": "18:00"},
                "sunday": {"closed": True}
            },
            'status': BusinessStatus.ACTIVE,
            'rating_average': 4.5,
            'reviews_count': 15,
            'primary_color': '#9c27b0',
            'secondary_color': '#e1bee7'
        }
    ]
    
    print("Insertando negocios de ejemplo...")
    
    for business_data in businesses_data:
        # Verificar si ya existe
        existing = Business.query.filter_by(slug=business_data['slug']).first()
        if existing:
            print(f"El negocio {business_data['name']} ya existe, saltando...")
            continue
            
        business = Business(**business_data)
        db.session.add(business)
        print(f"Agregando: {business_data['name']}")
    
    try:
        db.session.commit()
        print("✅ Negocios de ejemplo insertados correctamente")
        
        # Verificar
        total_businesses = Business.query.count()
        print(f"Total de negocios en la base de datos: {total_businesses}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error al insertar negocios: {e}")

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        print("🚀 Iniciando inserción de datos de ejemplo...")
        insert_sample_businesses()
        print("✅ Proceso completado!")
