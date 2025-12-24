"""
Módulo de conexión con Binance
Maneja autenticación y obtención de portfolio desde la API de Binance
"""
import requests
import hmac
import hashlib
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConexionBinance:
    """Clase para manejar conexiones con Binance"""
    
    BASE_URL = "https://api.binance.com"
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Inicializa la conexión con Binance
        
        Args:
            api_key: API Key de Binance
            api_secret: API Secret de Binance
        """
        self.api_key = api_key
        self.api_secret = api_secret
    
    def _generar_firma(self, query_string: str) -> str:
        """
        Genera la firma HMAC para autenticación con Binance
        
        Args:
            query_string: String de consulta para firmar
        
        Returns:
            Firma hexadecimal
        """
        return hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _obtener_precios(self) -> Dict[str, float]:
        """
        Obtiene los precios actuales de todos los símbolos en Binance
        
        Returns:
            Diccionario con símbolo como clave y precio como valor
        """
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/price"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                prices_data = response.json()
                return {item["symbol"]: float(item["price"]) for item in prices_data}
            else:
                logger.error(f"Error obteniendo precios de Binance: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Excepción al obtener precios de Binance: {str(e)}")
            return {}
    
    async def validar_credenciales(self) -> bool:
        """
        Valida que las credenciales sean correctas haciendo una petición a la API
        
        Returns:
            True si las credenciales son válidas, False en caso contrario
        """
        try:
            endpoint = "/api/v3/account"
            timestamp = int(datetime.now().timestamp() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = self._generar_firma(query_string)
            
            url = f"{self.BASE_URL}{endpoint}?{query_string}&signature={signature}"
            headers = {
                "X-MBX-APIKEY": self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("Credenciales de Binance validadas exitosamente")
                return True
            elif response.status_code == 401:
                logger.error("Credenciales de Binance inválidas")
                return False
            else:
                logger.error(f"Error validando credenciales de Binance: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al validar credenciales de Binance")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al validar credenciales de Binance: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Excepción inesperada al validar credenciales de Binance: {str(e)}")
            return False
    
    async def obtener_portfolio(self) -> Optional[List[Dict]]:
        """
        Obtiene el portfolio desde Binance
        
        Returns:
            Lista de activos en formato estándar o None si hay error
        """
        try:
            endpoint = "/api/v3/account"
            timestamp = int(datetime.now().timestamp() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = self._generar_firma(query_string)
            
            url = f"{self.BASE_URL}{endpoint}?{query_string}&signature={signature}"
            headers = {
                "X-MBX-APIKEY": self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Obtener precios actuales
                prices_dict = self._obtener_precios()
                
                # Transformar datos de Binance a formato estándar
                portfolio = []
                for balance in data.get("balances", []):
                    free = float(balance.get("free", 0))
                    locked = float(balance.get("locked", 0))
                    total = free + locked
                    
                    if total > 0:  # Solo incluir activos con balance
                        asset = balance.get("asset", "")
                        symbol = f"{asset}USDT"
                        current_price = prices_dict.get(symbol, 0)
                        
                        # Si el activo es USDT, el precio es 1
                        if asset == "USDT":
                            current_price = 1.0
                        # Si no encontramos precio en USDT, intentar con otros pares comunes
                        elif current_price == 0:
                            # Intentar con BTC
                            symbol_btc = f"{asset}BTC"
                            btc_price = prices_dict.get(symbol_btc, 0)
                            if btc_price > 0:
                                btc_usdt = prices_dict.get("BTCUSDT", 0)
                                current_price = btc_price * btc_usdt if btc_usdt > 0 else 0
                        
                        market_value = total * current_price if current_price > 0 else 0
                        
                        portfolio.append({
                            "ticker": asset,
                            "name": asset,
                            "quantity": total,
                            "avg_price": 0,  # Binance no proporciona precio de compra
                            "current_price": current_price,
                            "market_value": market_value,
                            "profit_loss": 0,  # No se puede calcular sin precio de compra
                            "profit_loss_pct": 0,
                            "broker": "BINANCE",
                            "synced_at": datetime.now().isoformat()
                        })
                
                logger.info(f"Portfolio de Binance obtenido exitosamente: {len(portfolio)} activos")
                return portfolio
            elif response.status_code == 401:
                logger.error("Credenciales de Binance inválidas o expiradas")
                return None
            else:
                logger.error(f"Error obteniendo portfolio de Binance: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al obtener portfolio de Binance")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al obtener portfolio de Binance: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Excepción inesperada al obtener portfolio de Binance: {str(e)}")
            return None
    
    async def ejecutar_orden(self, symbol: str, quantity: float, side: str, order_type: str = "MARKET", price: Optional[float] = None) -> Optional[Dict]:
        """
        Ejecuta una orden de compra o venta en Binance
        
        Args:
            symbol: Par de trading (ej: "BTCUSDT", "ETHUSDT")
            quantity: Cantidad a comprar/vender
            side: "BUY" o "SELL"
            order_type: Tipo de orden ("MARKET" o "LIMIT")
            price: Precio límite (requerido si order_type es "LIMIT")
        
        Returns:
            Diccionario con información de la orden ejecutada o None si hay error
        """
        try:
            endpoint = "/api/v3/order"
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # Construir parámetros
            params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": order_type.upper(),
                "quantity": quantity,
                "timestamp": timestamp
            }
            
            if order_type.upper() == "LIMIT":
                if not price:
                    logger.error("Precio requerido para orden LIMIT")
                    return {
                        "success": False,
                        "error": "Precio requerido para orden LIMIT",
                        "status": "FAILED"
                    }
                params["price"] = price
                params["timeInForce"] = "GTC"  # Good Till Cancel
            
            # Crear query string y firmar
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._generar_firma(query_string)
            query_string += f"&signature={signature}"
            
            url = f"{self.BASE_URL}{endpoint}?{query_string}"
            headers = {
                "X-MBX-APIKEY": self.api_key
            }
            
            response = requests.post(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Orden {side} ejecutada exitosamente en Binance: {quantity} {symbol}")
                return {
                    "success": True,
                    "order_id": str(data.get("orderId", "")),
                    "ticker": symbol,
                    "quantity": quantity,
                    "type": side,
                    "price": float(data.get("price", 0)) or float(data.get("executedQty", 0) * data.get("price", 0)),
                    "status": data.get("status", "FILLED"),
                    "broker_response": data
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"msg": response.text}
                logger.error(f"Error ejecutando orden en Binance: {response.status_code} - {error_data}")
                return {
                    "success": False,
                    "error": error_data.get("msg", f"Error {response.status_code}"),
                    "status": "FAILED",
                    "broker_response": error_data
                }
                
        except Exception as e:
            logger.error(f"Excepción al ejecutar orden en Binance: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status": "FAILED"
            }
    
    def obtener_info(self) -> Dict:
        """
        Obtiene información sobre la conexión
        
        Returns:
            Diccionario con información de la conexión
        """
        return {
            "broker": "BINANCE",
            "api_key": self.api_key[:8] + "..." if self.api_key else None,  # Solo primeros 8 caracteres
            "base_url": self.BASE_URL
        }


# Funciones de compatibilidad con el código existente
async def get_binance_portfolio(api_key: str, api_secret: str) -> Optional[List[Dict]]:
    """
    Función de compatibilidad para obtener portfolio de Binance
    
    Args:
        api_key: API Key de Binance
        api_secret: API Secret de Binance
    
    Returns:
        Lista de activos o None si hay error
    """
    conexion = ConexionBinance(api_key, api_secret)
    return await conexion.obtener_portfolio()

