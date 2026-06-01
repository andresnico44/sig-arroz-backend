from django.test import TestCase
from django.contrib.auth.models import User
from arroz.models import Finca, Lote, CicloProductivo, Cosecha, Liquidacion, Perfil, RegistroCosto
from arroz.serializers import LiquidacionSerializer
from rest_framework.exceptions import ValidationError
import datetime

class LiquidacionModelAndTrazabilidadTestCase(TestCase):
    def setUp(self):
        # 1. Crear usuario de prueba
        self.user = User.objects.create_user(username='testproductor', email='productor@test.com', password='password123')
        self.perfil = Perfil.objects.create(user=self.user, rol='PRODUCTOR')
        
        # 2. Crear Finca
        self.finca = Finca.objects.create(productor=self.user, nombre='Finca La Esmeralda', ubicacion_departamento='Tolima', ubicacion_municipio='Espinal', area_total_ha=10.0)
        
        # 3. Crear Lote
        self.lote = Lote.objects.create(finca=self.finca, nombre='Lote A1', area_hectareas=5.0, tipo_suelo='FRANCO', sistema_produccion='RIEGO', estado='ACTIVO')
        
        # 4. Crear Ciclo Productivo
        self.ciclo = CicloProductivo.objects.create(lote=self.lote, nombre_ciclo='Ciclo Arroz 2026-A', anio=2026, semestre='1', variedad_arroz='FEDEARROZ_67', presupuesto_estimado=15000000.0, estado='PLANIFICADO')

    def test_liquidacion_save_transitions_states(self):
        # Primero registrar la cosecha física
        cosecha = Cosecha.objects.create(
            ciclo=self.ciclo,
            fecha=datetime.date(2026, 5, 20),
            produccion_obtenida_kg=30000.0,  # 30 Toneladas
            humedad_grano_porcentaje=22.0,
            impurezas_porcentaje=2.0
        )
        
        # Verificar que el ciclo pasó a COSECHADO y el lote a COSECHADO
        self.ciclo.refresh_from_db()
        self.lote.refresh_from_db()
        self.assertEqual(self.ciclo.estado, 'COSECHADO')
        self.assertEqual(self.lote.estado, 'COSECHADO')
        
        # Registrar la liquidación económica del molino
        liquidacion = Liquidacion.objects.create(
            ciclo=self.ciclo,
            fecha=datetime.date(2026, 5, 25),
            humedad_final_porcentaje=14.0,
            porcentaje_grano_entero=62.0,
            porcentaje_grano_quebrado=8.0,
            precio_tonelada_cop=1800000.0,
            descuentos_aplicados_cop=500000.0,
            ingreso_neto_cop=53500000.0,  # 30 Ton * 1.8M = 54M brutos - 500k = 53.5M netos
            observaciones='Pago completo del molino'
        )
        
        # Verificar transiciones de estado automáticas
        self.ciclo.refresh_from_db()
        self.lote.refresh_from_db()
        self.assertEqual(self.ciclo.estado, 'FINALIZADO')
        self.assertEqual(self.lote.estado, 'DESCANSO')

    def test_liquidacion_serializer_validation(self):
        # 1. Validar que trilla entero + quebrado > 100% lanza error
        data_invalid_trilla = {
            'ciclo': self.ciclo.id,
            'fecha': '2026-05-25',
            'humedad_final_porcentaje': 14.0,
            'porcentaje_grano_entero': 70.0,
            'porcentaje_grano_quebrado': 35.0,  # Suma = 105% > 100%
            'precio_tonelada_cop': 1800000.0,
            'descuentos_aplicados_cop': 100000.0,
            'ingreso_neto_cop': 5000000.0
        }
        serializer = LiquidacionSerializer(data=data_invalid_trilla)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
        # 2. Validar que porcentajes fuera de rango lanzen error
        data_invalid_porcentaje = {
            'ciclo': self.ciclo.id,
            'fecha': '2026-05-25',
            'humedad_final_porcentaje': 120.0,  # > 100%
            'porcentaje_grano_entero': 60.0,
            'porcentaje_grano_quebrado': 10.0,
            'precio_tonelada_cop': 1800000.0,
            'descuentos_aplicados_cop': 100000.0,
            'ingreso_neto_cop': 5000000.0
        }
        serializer = LiquidacionSerializer(data=data_invalid_porcentaje)
        self.assertFalse(serializer.is_valid())
        self.assertIn('humedad_final_porcentaje', serializer.errors)

    def test_trazabilidad_y_rentabilidad_calculo(self):
        # 1. Registrar costos
        RegistroCosto.objects.create(ciclo=self.ciclo, fecha=datetime.date(2026, 4, 10), categoria='INSUMOS_AGROQUIMICOS', descripcion='Abonos NPK', monto_total=5000000.0)
        RegistroCosto.objects.create(ciclo=self.ciclo, fecha=datetime.date(2026, 4, 20), categoria='MANO_DE_OBRA', descripcion='Jornales siembra', monto_total=2500000.0)
        
        # 2. Registrar Cosecha
        Cosecha.objects.create(
            ciclo=self.ciclo,
            fecha=datetime.date(2026, 5, 20),
            produccion_obtenida_kg=30000.0,
            humedad_grano_porcentaje=22.0,
            impurezas_porcentaje=2.0
        )
        
        # 3. Registrar Liquidacion
        Liquidacion.objects.create(
            ciclo=self.ciclo,
            fecha=datetime.date(2026, 5, 25),
            humedad_final_porcentaje=14.0,
            porcentaje_grano_entero=60.0,
            porcentaje_grano_quebrado=10.0,
            precio_tonelada_cop=1800000.0,
            descuentos_aplicados_cop=500000.0,
            ingreso_neto_cop=12500000.0  # Para forzar un balance específico
        )
        
        # Total egresos = 5M (NPK) + 2.5M (Mano de obra) = 7.5M
        # Ingreso Neto = 12.5M
        # Balance = 12.5M - 7.5M = 5.0M
        # Area = 5.0 Ha
        # Costo por ha = 7.5M / 5 = 1.5M
        # Ingreso por ha = 12.5M / 5 = 2.5M
        # Balance por ha = 5.0M / 5 = 1.0M
        # Rentable = True (5.0M > 0)
        
        # Simular lo que calcula la vista del backend en la acción trazabilidad
        costos = self.ciclo.costos.all()
        total_egresos = sum(float(c.monto_total) for c in costos)
        ingreso_neto = float(self.ciclo.liquidacion.ingreso_neto_cop)
        balance = ingreso_neto - total_egresos
        area = float(self.ciclo.lote.area_hectareas)
        
        balance_por_ha = balance / area
        costo_por_ha = total_egresos / area
        ingreso_por_ha = ingreso_neto / area
        
        self.assertEqual(total_egresos, 7500000.0)
        self.assertEqual(ingreso_neto, 12500000.0)
        self.assertEqual(balance, 5000000.0)
        self.assertEqual(costo_por_ha, 1500000.0)
        self.assertEqual(ingreso_por_ha, 2500000.0)
        self.assertEqual(balance_por_ha, 1000000.0)
        self.assertTrue(balance > 0)
