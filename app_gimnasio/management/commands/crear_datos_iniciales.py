from django.core.management.base import BaseCommand
from app_gimnasio.models import MetodoPago, Banco

class Command(BaseCommand):
    help = 'Crea datos iniciales para el sistema de gimnasio'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creando datos iniciales para el sistema...')
        
        # Crear métodos de pago
        self.crear_metodos_pago()
        
        # Crear bancos
        self.crear_bancos()
        
        self.stdout.write(self.style.SUCCESS('Datos iniciales creados exitosamente!'))
    
    def crear_metodos_pago(self):
        metodos_pago = [
            {
                'nombre': 'Efectivo',
                'descripcion': 'Pago en efectivo en la recepción',
                'requiere_banco': False,
            },
            {
                'nombre': 'Tarjeta de Crédito',
                'descripcion': 'Pago con tarjeta de crédito',
                'requiere_banco': True,
            },
            {
                'nombre': 'Tarjeta de Débito',
                'descripcion': 'Pago con tarjeta de débito',
                'requiere_banco': True,
            },
            {
                'nombre': 'Transferencia Bancaria',
                'descripcion': 'Pago mediante transferencia bancaria',
                'requiere_banco': True,
            },
            {
                'nombre': 'Pago Móvil',
                'descripcion': 'Pago a través de aplicación móvil',
                'requiere_banco': True,
            },
        ]
        
        for metodo in metodos_pago:
            MetodoPago.objects.get_or_create(
                nombre=metodo['nombre'],
                defaults={
                    'descripcion': metodo['descripcion'],
                    'requiere_banco': metodo['requiere_banco'],
                    'activo': True,
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Se crearon {len(metodos_pago)} métodos de pago'))
    
    def crear_bancos(self):
        bancos = [
            {'nombre': 'Banco Nacional', 'codigo': 'BN'},
            {'nombre': 'Banco Popular', 'codigo': 'BP'},
            {'nombre': 'Banco de Venezuela', 'codigo': 'BDV'},
            {'nombre': 'Banesco', 'codigo': 'BAN'},
            {'nombre': 'Banco Mercantil', 'codigo': 'BM'},
            {'nombre': 'BBVA Provincial', 'codigo': 'BBVA'},
            {'nombre': 'Banco Exterior', 'codigo': 'BE'},
            {'nombre': 'Banco Occidental de Descuento', 'codigo': 'BOD'},
            {'nombre': 'Banco Venezolano de Crédito', 'codigo': 'BVC'},
            {'nombre': 'Banco Caroní', 'codigo': 'BC'},
        ]
        
        for banco in bancos:
            Banco.objects.get_or_create(
                nombre=banco['nombre'],
                defaults={
                    'codigo': banco['codigo'],
                    'activo': True,
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Se crearon {len(bancos)} bancos'))
