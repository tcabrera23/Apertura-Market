"""
Script de Migración de Datos JSON a Supabase
Migra datos de rules.json y watchlists.json a la base de datos de Supabase
"""
import json
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
    exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def migrate_rules(user_id: str):
    """
    Migrate rules from rules.json to Supabase
    """
    try:
        with open('rules.json', 'r') as f:
            rules = json.load(f)
        
        print(f"\n📋 Migrando {len(rules)} reglas...")
        
        for rule in rules:
            rule_data = {
                "user_id": user_id,
                "name": rule.get("name"),
                "rule_type": rule.get("type"),
                "ticker": rule.get("ticker"),
                "value_threshold": float(rule.get("value", 0)),
                "email": rule.get("email"),
                "is_active": True,
                "created_at": rule.get("created_at", datetime.now().isoformat())
            }
            
            if rule.get("last_triggered"):
                rule_data["last_triggered"] = rule["last_triggered"]
            
            response = supabase.table("rules").insert(rule_data).execute()
            print(f"  ✅ Migrada regla: {rule.get('name')}")
        
        print(f"\n✨ {len(rules)} reglas migradas exitosamente!")
        return len(rules)
    
    except FileNotFoundError:
        print("⚠️  Archivo rules.json no encontrado. Saltando migración de reglas.")
        return 0
    except Exception as e:
        print(f"❌ Error migrando reglas: {e}")
        return 0

def migrate_watchlists(user_id: str):
    """
    Migrate watchlists from watchlists.json to Supabase
    """
    try:
        with open('watchlists.json', 'r') as f:
            watchlists = json.load(f)
        
        print(f"\n📊 Migrando {len(watchlists)} watchlists...")
        
        total_assets = 0
        
        for watchlist_name, assets in watchlists.items():
            # Create watchlist
            watchlist_data = {
                "user_id": user_id,
                "name": watchlist_name,
                "description": f"Migrated from watchlists.json"
            }
            
            watchlist_response = supabase.table("watchlists") \
                .insert(watchlist_data) \
                .execute()
            
            watchlist_id = watchlist_response.data[0]["id"]
            print(f"  ✅ Creada watchlist: {watchlist_name}")
            
            # Add assets to watchlist
            for ticker, asset_name in assets.items():
                asset_data = {
                    "watchlist_id": watchlist_id,
                    "ticker": ticker,
                    "asset_name": asset_name
                }
                
                supabase.table("watchlist_assets").insert(asset_data).execute()
                total_assets += 1
                print(f"    ↳ Agregado: {ticker} - {asset_name}")
        
        print(f"\n✨ {len(watchlists)} watchlists migradas con {total_assets} activos!")
        return len(watchlists), total_assets
    
    except FileNotFoundError:
        print("⚠️  Archivo watchlists.json no encontrado. Saltando migración de watchlists.")
        return 0, 0
    except Exception as e:
        print(f"❌ Error migrando watchlists: {e}")
        return 0, 0

def main():
    """
    Main migration function
    """
    print("=" * 60)
    print("🚀 SCRIPT DE MIGRACIÓN - JSON → SUPABASE")
    print("=" * 60)
    
    # Get user ID
    print("\n📌 Necesitas el UUID de tu usuario de Supabase.")
    print("   Encuéntralo en: Supabase Dashboard → Authentication → Users")
    print("   O créalo primero si no tienes un usuario.")
    
    user_id = input("\n👤 Ingresa tu User ID (UUID): ").strip()
    
    if not user_id:
        print("❌ User ID es requerido. Abortando migración.")
        return
    
    # Confirm
    print(f"\n⚠️  Se migrarán los datos a la cuenta del usuario: {user_id}")
    confirm = input("¿Continuar? (s/n): ").strip().lower()
    
    if confirm != 's':
        print("❌ Migración cancelada.")
        return
    
    # Run migrations
    rules_count = migrate_rules(user_id)
    watchlists_count, assets_count = migrate_watchlists(user_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 60)
    print(f"📋 Reglas migradas: {rules_count}")
    print(f"📊 Watchlists migradas: {watchlists_count}")
    print(f"📈 Activos migrados: {assets_count}")
    print("\n💡 Ahora puedes eliminar los archivos JSON si quieres:")
    print("   - rules.json")
    print("   - watchlists.json")
    print("\n🎉 ¡Todo listo! Prueba la nueva API con autenticación.")

if __name__ == "__main__":
    main()
