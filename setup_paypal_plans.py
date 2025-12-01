"""
Script para crear planes de suscripción en PayPal y actualizar Supabase
Ejecuta este script después de configurar tus credenciales de PayPal
"""
import os
import requests
import base64
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Configuración
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "live")  # 'sandbox' o 'live'
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pwumamzbicapuiqkwrey.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
    print("❌ Error: PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET deben estar en .env")
    exit(1)

if not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_SERVICE_KEY debe estar en .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_paypal_access_token():
    """Obtiene token de acceso de PayPal"""
    auth = base64.b64encode(
        f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()
    ).decode()
    
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            headers=headers,
            data={"grant_type": "client_credentials"}
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                raise Exception(f"Error obteniendo token: {error_data}")
            except ValueError:
                # Si no es JSON, mostrar el texto de la respuesta
                raise Exception(f"Error obteniendo token (status {response.status_code}): {response.text[:200]}")
        
        token_data = response.json()
        if "access_token" not in token_data:
            raise Exception(f"Respuesta inesperada: {token_data}")
        
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión con PayPal: {str(e)}")

def create_paypal_product():
    """Crea un producto en PayPal (requerido antes de crear planes)"""
    access_token = get_paypal_access_token()
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    payload = {
        "name": "BullAnalytics Subscription",
        "description": "Suscripciones mensuales de BullAnalytics",
        "type": "SERVICE",
        "category": "SOFTWARE"
    }
    
    try:
        # Intentar primero listar productos existentes
        list_response = requests.get(
            f"{PAYPAL_BASE_URL}/v1/catalog/products",
            headers=headers,
            params={"page_size": 10, "page": 1}
        )
        
        if list_response.status_code == 200:
            try:
                data = list_response.json()
                products = data.get('products', [])
                # Buscar producto existente con el mismo nombre
                for product in products:
                    if product.get('name') == "BullAnalytics Subscription":
                        product_id = product['id']
                        print(f"✅ Usando producto existente: {product_id}")
                        return product_id
            except ValueError:
                pass
        
        # Si no existe, crear nuevo producto
        # Nota: PayPal requiere crear el producto primero desde el Dashboard o usar un producto existente
        print("   ⚠️  PayPal requiere crear productos desde el Dashboard")
        print("   📝 Pasos manuales:")
        print("      1. Ve a https://developer.paypal.com/dashboard/")
        print("      2. Products → Create Product")
        print("      3. Tipo: Service, Nombre: BullAnalytics Subscription")
        print("      4. Copia el Product ID (ej: PROD-XXXXX)")
        print("   ")
        print("   O ingresa el Product ID manualmente:")
        product_id = input("   Product ID (o presiona Enter para usar uno existente): ").strip()
        
        if product_id:
            print(f"✅ Usando Product ID: {product_id}")
            return product_id
        
        # Si no se ingresó, intentar buscar productos existentes
        print("   Buscando productos existentes...")
        response = requests.get(
            f"{PAYPAL_BASE_URL}/v1/catalog/products",
            headers=headers,
            params={"page_size": 10, "page": 1}
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                products = data.get('products', [])
                if products:
                    print(f"   📋 Productos encontrados: {len(products)}")
                    for i, p in enumerate(products, 1):
                        print(f"      {i}. {p.get('name', 'N/A')} - ID: {p.get('id', 'N/A')}")
                    product_id = products[0]['id']
                    print(f"✅ Usando primer producto: {product_id}")
                    return product_id
                else:
                    raise Exception("No se encontraron productos. Crea uno desde el Dashboard primero.")
            except ValueError:
                raise Exception(f"Error parseando respuesta: {response.text[:200]}")
        else:
            raise Exception(f"No se pudieron listar productos (status {response.status_code}): {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {str(e)}")

def create_paypal_plan(product_id, plan_name, display_name, price):
    """Crea un plan de suscripción en PayPal"""
    access_token = get_paypal_access_token()
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    payload = {
        "product_id": product_id,
        "name": display_name,
        "description": f"Suscripción mensual {display_name}",
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0,  # Infinito
                "pricing_scheme": {
                    "fixed_price": {
                        "value": str(price),
                        "currency_code": "USD"
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        },
        "taxes": {
            "percentage": "0",
            "inclusive": False
        }
    }
    
    try:
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/billing/plans",
            headers=headers,
            json=payload
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code != 201:
            try:
                error_data = response.json()
                raise Exception(f"Error creando plan: {error_data}")
            except ValueError:
                raise Exception(f"Error creando plan (status {response.status_code}): {response.text[:200]}")
        
        try:
            plan = response.json()
            if 'id' not in plan:
                raise Exception(f"Respuesta inesperada: {plan}")
            return plan['id']
        except ValueError:
            raise Exception(f"Respuesta no es JSON válido: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de conexión: {str(e)}")

def update_supabase_plan(plan_name, paypal_plan_id):
    """Actualiza el paypal_plan_id en Supabase"""
    response = supabase.table("subscription_plans") \
        .update({"paypal_plan_id": paypal_plan_id}) \
        .eq("name", plan_name) \
        .execute()
    
    if response.data:
        print(f"✅ Plan '{plan_name}' actualizado en Supabase con paypal_plan_id: {paypal_plan_id}")
        return True
    else:
        print(f"❌ Error actualizando plan '{plan_name}' en Supabase")
        return False

def main():
    print(f"🚀 Configurando planes de PayPal en modo: {PAYPAL_MODE}")
    print(f"📍 URL Base: {PAYPAL_BASE_URL}")
    print("=" * 60)
    
    # Verificar credenciales
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        print("❌ Error: PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET deben estar en .env")
        return
    
    print(f"✅ Client ID configurado: {PAYPAL_CLIENT_ID[:10]}...")
    
    # 1. Crear producto en PayPal
    print("\n📦 Paso 1: Creando producto en PayPal...")
    try:
        product_id = create_paypal_product()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Tips:")
        print("   - Verifica que PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET sean correctos")
        print("   - Si estás en modo 'live', asegúrate de usar credenciales de producción")
        print("   - Si estás en modo 'sandbox', usa credenciales de sandbox")
        return
    
    # 2. Obtener planes de Supabase que necesitan paypal_plan_id
    print("\n📋 Paso 2: Obteniendo planes de Supabase...")
    plans_response = supabase.table("subscription_plans") \
        .select("*") \
        .in_("name", ["plus", "pro"]) \
        .execute()
    
    if not plans_response.data:
        print("❌ No se encontraron planes 'plus' o 'pro' en Supabase")
        return
    
    # 3. Crear planes en PayPal y actualizar Supabase
    print("\n💳 Paso 3: Creando planes en PayPal y actualizando Supabase...")
    for plan in plans_response.data:
        plan_name = plan['name']
        display_name = plan['display_name']
        price = float(plan['price'])
        
        if plan.get('paypal_plan_id'):
            print(f"⏭️  Plan '{plan_name}' ya tiene paypal_plan_id: {plan['paypal_plan_id']}")
            continue
        
        if price == 0:
            print(f"⏭️  Plan '{plan_name}' es gratuito, no necesita PayPal")
            continue
        
        print(f"\n   Creando plan '{display_name}' (${price}/mes)...")
        try:
            paypal_plan_id = create_paypal_plan(product_id, plan_name, display_name, price)
            print(f"   ✅ Plan creado en PayPal: {paypal_plan_id}")
            
            # Actualizar Supabase
            update_supabase_plan(plan_name, paypal_plan_id)
            
        except Exception as e:
            print(f"   ❌ Error creando plan '{plan_name}': {e}")
    
    print("\n" + "=" * 60)
    print("✅ Proceso completado!")
    print("\n📝 Verifica los planes en Supabase:")
    print("   SELECT name, display_name, price, paypal_plan_id FROM subscription_plans;")

if __name__ == "__main__":
    main()

