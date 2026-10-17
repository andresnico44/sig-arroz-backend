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
        from decimal import Decimal
        costos = self.ciclo.costos.all()
        total_egresos = sum((c.monto_total for c in costos), Decimal('0.00'))
        ingreso_neto = Decimal(str(self.ciclo.liquidacion.ingreso_neto_cop))
        balance = ingreso_neto - total_egresos
        area = Decimal(str(self.ciclo.lote.area_hectareas))
        
        balance_por_ha = balance / area
        costo_por_ha = total_egresos / area
        ingreso_por_ha = ingreso_neto / area
        
        self.assertEqual(total_egresos, Decimal('7500000.00'))
        self.assertEqual(ingreso_neto, Decimal('12500000.00'))
        self.assertEqual(balance, Decimal('5000000.00'))
        self.assertEqual(costo_por_ha, Decimal('1500000.00'))
        self.assertEqual(ingreso_por_ha, Decimal('2500000.00'))
        self.assertEqual(balance_por_ha, Decimal('1000000.00'))
        self.assertTrue(balance > Decimal('0.00'))


from rest_framework.test import APITestCase
from rest_framework import status

class AuthAndPermissionsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='productor1', email='prod1@sig-arroz.com', password='Password123!')
        self.perfil = Perfil.objects.create(user=self.user, rol='PRODUCTOR')
        
    def test_unauthenticated_access_denied(self):
        """Verifica que peticiones sin JWT sean rechazadas con 401."""
        response = self.client.get('/api/fincas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_obtain_pair_success(self):
        """Verifica que las credenciales correctas devuelvan access y refresh token con claims de rol."""
        from rest_framework_simplejwt.tokens import AccessToken
        response = self.client.post('/api/token/', {
            'username': 'productor1',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Validar que el token JWT contiene el rol PRODUCTOR
        token_data = AccessToken(response.data['access'])
        self.assertEqual(token_data.get('rol'), 'PRODUCTOR')

    def test_jwt_obtain_pair_invalid_credentials(self):
        """Verifica que credenciales inválidas retornen 401."""
        response = self.client.post('/api/token/', {
            'username': 'productor1',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FincaAndLoteAPITestCase(APITestCase):
    def setUp(self):
        self.productor1 = User.objects.create_user(username='prod_alpha', email='alpha@test.com', password='Password123!')
        self.perfil1 = Perfil.objects.create(user=self.productor1, rol='PRODUCTOR')
        
        self.productor2 = User.objects.create_user(username='prod_beta', email='beta@test.com', password='Password123!')
        self.perfil2 = Perfil.objects.create(user=self.productor2, rol='PRODUCTOR')
        
        # Finca del Productor 1
        self.finca1 = Finca.objects.create(
            productor=self.productor1,
            nombre='Finca San Jose',
            ubicacion_departamento='Norte de Santander',
            ubicacion_municipio='Zulia',
            area_total_ha=20.0
        )

    def test_productor_crud_finca(self):
        """Verifica que un productor autenticado pueda crear y consultar sus fincas."""
        self.client.force_authenticate(user=self.productor1)
        
        # 1. Listar fincas
        response = self.client.get('/api/fincas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nombre'], 'Finca San Jose')
        
        # 2. Crear nueva finca
        payload = {
            'nombre': 'Finca Buena Vista',
            'ubicacion_departamento': 'Casanare',
            'ubicacion_municipio': 'Yopal',
            'area_total_ha': '15.50'
        }
        res_create = self.client.post('/api/fincas/', payload)
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Finca.objects.filter(productor=self.productor1).count(), 2)

    def test_productor_data_isolation(self):
        """Verifica el aislamiento: el productor 2 no ve las fincas del productor 1."""
        self.client.force_authenticate(user=self.productor2)
        response = self.client.get('/api/fincas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No tiene fincas creadas aún

