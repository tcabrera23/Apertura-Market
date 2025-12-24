"""
Worker para ejecutar reglas automáticamente
Este worker verifica periódicamente las reglas activas y ejecuta órdenes cuando se cumplen
"""
import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict
from supabase import create_client, Client
from rule_execution import RuleEvaluator
from conexion_iol import ConexionIOL
from conexion_binance import ConexionBinance
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pwumamzbicapuiqkwrey.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is required")
ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
cipher_suite = Fernet(ENCRYPTION_KEY)

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key"""
    try:
        return cipher_suite.decrypt(encrypted_key.encode()).decode()
    except Exception as e:
        logger.error(f"Error decrypting key: {str(e)}")
        raise

async def check_and_execute_rules():
    """Check all active rules and execute if conditions are met"""
    try:
        # Get all active rules with execution enabled
        rules_response = supabase.table("rules") \
            .select("*") \
            .eq("is_active", True) \
            .eq("execution_enabled", True) \
            .neq("execution_type", "ALERT_ONLY") \
            .execute()
        
        rules = rules_response.data or []
        logger.info(f"Checking {len(rules)} active rules with execution enabled")
        
        evaluator = RuleEvaluator()
        executed_count = 0
        
        for rule in rules:
            try:
                # Evaluate rule
                condition_met, current_data = await evaluator.evaluate_rule(rule)
                
                if not condition_met:
                    continue
                
                # Check cooldown
                last_execution = rule.get("last_execution_at")
                cooldown_minutes = rule.get("cooldown_minutes", 60)
                
                if last_execution:
                    try:
                        last_exec = datetime.fromisoformat(last_execution.replace('Z', '+00:00'))
                        time_since = (datetime.now(timezone.utc) - last_exec).total_seconds()
                        if time_since < (cooldown_minutes * 60):
                            logger.info(f"Rule {rule.get('id')} is in cooldown period")
                            continue
                    except Exception as e:
                        logger.warning(f"Error parsing last_execution_at: {str(e)}")
                
                # Get broker connection
                broker_connection = None
                broker_connection_id = rule.get("broker_connection_id")
                if broker_connection_id:
                    broker_response = supabase.table("broker_connections") \
                        .select("*") \
                        .eq("id", broker_connection_id) \
                        .eq("is_active", True) \
                        .execute()
                    
                    if broker_response.data and len(broker_response.data) > 0:
                        broker_connection = broker_response.data[0]
                
                # Execute order
                execution_result = None
                
                if broker_connection and rule.get("execution_type") in ["BUY", "SELL"]:
                    broker_name = broker_connection.get("broker_name")
                    ticker = rule.get("ticker")
                    quantity = float(rule.get("quantity", 0))
                    execution_type = rule.get("execution_type")
                    
                    if quantity <= 0:
                        logger.warning(f"Rule {rule.get('id')} has invalid quantity: {quantity}")
                        continue
                    
                    try:
                        # Decrypt and execute
                        if broker_name == "IOL":
                            username = decrypt_api_key(broker_connection.get("username_encrypted"))
                            password = decrypt_api_key(broker_connection.get("password_encrypted"))
                            conexion = ConexionIOL(username, password)
                            execution_result = await conexion.ejecutar_orden(ticker, quantity, execution_type)
                            
                        elif broker_name == "BINANCE":
                            api_key = decrypt_api_key(broker_connection.get("api_key_encrypted"))
                            api_secret = decrypt_api_key(broker_connection.get("api_secret_encrypted"))
                            conexion = ConexionBinance(api_key, api_secret)
                            symbol = ticker if "USDT" in ticker else f"{ticker}USDT"
                            execution_result = await conexion.ejecutar_orden(symbol, quantity, execution_type)
                        
                        logger.info(f"Execution result for rule {rule.get('id')}: {execution_result}")
                        
                    except Exception as e:
                        logger.error(f"Error executing order for rule {rule.get('id')}: {str(e)}")
                        execution_result = {
                            "success": False,
                            "error": str(e),
                            "status": "FAILED"
                        }
                
                # Create execution record
                execution_data = {
                    "rule_id": rule.get("id"),
                    "user_id": rule.get("user_id"),
                    "broker_connection_id": broker_connection.get("id") if broker_connection else None,
                    "execution_type": rule.get("execution_type", "ALERT_ONLY"),
                    "ticker": rule.get("ticker"),
                    "quantity": rule.get("quantity"),
                    "price": current_data.get("current_price") if current_data else None,
                    "total_amount": (rule.get("quantity", 0) * current_data.get("current_price")) if current_data else None,
                    "status": "EXECUTED" if execution_result and execution_result.get("success") else "FAILED",
                    "error_message": execution_result.get("error") if execution_result and not execution_result.get("success") else None,
                    "broker_response": execution_result,
                    "broker_order_id": execution_result.get("order_id") if execution_result else None,
                    "triggered_at": datetime.now(timezone.utc).isoformat(),
                    "executed_at": datetime.now(timezone.utc).isoformat() if execution_result and execution_result.get("success") else None
                }
                
                supabase.table("rule_executions").insert(execution_data).execute()
                
                # Update rule's last_execution_at
                supabase.table("rules") \
                    .update({"last_execution_at": datetime.now(timezone.utc).isoformat()}) \
                    .eq("id", rule.get("id")) \
                    .execute()
                
                executed_count += 1
                logger.info(f"Rule {rule.get('id')} executed successfully")
                
                # Send email notification (if configured)
                # TODO: Implement email notification
                
            except Exception as e:
                logger.error(f"Error processing rule {rule.get('id')}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Worker cycle completed. Executed {executed_count} rules")
        
    except Exception as e:
        logger.error(f"Error in rule executor worker: {str(e)}", exc_info=True)

async def main():
    """Main worker loop"""
    check_interval = int(os.getenv("RULE_CHECK_INTERVAL", "60"))  # Default 60 seconds
    
    logger.info(f"Starting rule executor worker (check interval: {check_interval}s)")
    
    while True:
        try:
            await check_and_execute_rules()
            await asyncio.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in worker main loop: {str(e)}", exc_info=True)
            await asyncio.sleep(check_interval)

if __name__ == "__main__":
    asyncio.run(main())

