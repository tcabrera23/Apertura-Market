"""
Script para actualizar los paypal_plan_id en Supabase
Úsalo si ya tienes los Plan IDs de PayPal creados manualmente
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pwumamzbicapuiqkwrey.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_SERVICE_KEY debe estar en .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def update_plan_ids():
    """Actualiza los paypal_plan_id en Supabase"""
    print("🔧 Actualizar Plan IDs de PayPal en Supabase")
    print("=" * 60)
    
    # Obtener planes actuales
    plans_response = supabase.table("subscription_plans") \
        .select("*") \
        .in_("name", ["plus", "pro"]) \
        .execute()
    
    if not plans_response.data:
        print("❌ No se encontraron planes 'plus' o 'pro'")
        return
    
    print("\n📋 Planes encontrados:")
    for plan in plans_response.data:
        current_id = plan.get('paypal_plan_id') or 'NULL'
        print(f"   - {plan['name']}: {plan['display_name']} (${plan['price']}/mes)")
        print(f"     PayPal Plan ID actual: {current_id}")
    
    print("\n💳 Ingresa los Plan IDs de PayPal:")
    print("   (Puedes encontrarlos en: https://developer.paypal.com/dashboard/products)")
    print("   (Formato: P-XXXXXXXXXX)")
    
    updates = {}
    for plan in plans_response.data:
        plan_name = plan['name']
        if plan.get('paypal_plan_id'):
            print(f"\n   Plan '{plan_name}' ya tiene ID: {plan['paypal_plan_id']}")
            update = input(f"   ¿Actualizar? (s/N): ").strip().lower()
            if update != 's':
                continue
        
        plan_id = input(f"\n   PayPal Plan ID para '{plan_name}' (o Enter para omitir): ").strip()
        if plan_id:
            updates[plan_name] = plan_id
    
    if not updates:
        print("\n⏭️  No se actualizó ningún plan")
        return
    
    print("\n💾 Actualizando Supabase...")
    for plan_name, paypal_plan_id in updates.items():
        try:
            response = supabase.table("subscription_plans") \
                .update({"paypal_plan_id": paypal_plan_id}) \
                .eq("name", plan_name) \
                .execute()
            
            if response.data:
                print(f"   ✅ Plan '{plan_name}' actualizado: {paypal_plan_id}")
            else:
                print(f"   ❌ Error actualizando plan '{plan_name}'")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Proceso completado!")
    print("\n📝 Verifica en Supabase:")
    print("   SELECT name, display_name, price, paypal_plan_id FROM subscription_plans;")

if __name__ == "__main__":
    update_plan_ids()

