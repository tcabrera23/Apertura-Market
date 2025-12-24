"""
Módulo de conexión con IOL (InvertirOnline)
Maneja autenticación y obtención de portfolio desde la API de IOL
"""
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConexionIOL:
    """Clase para manejar conexiones con IOL"""
    
    BASE_URL = "https://api.invertironline.com"
    
    def __init__(self, username: str, password: str):
        """
        Inicializa la conexión con IOL
        
        Args:
            username: Usuario de IOL
            password: Contraseña de IOL
        """
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
    
    async def autenticar(self) -> bool:
        """
        Autentica con la API de IOL y obtiene el access token
        
        Returns:
            True si la autenticación fue exitosa, False en caso contrario
        """
        try:
            url = f"{self.BASE_URL}/token"
            
            payload = {
                "username": self.username,
                "password": self.password,
                "grant_type": "password"
            }
            
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                
                if self.access_token:
                    logger.info(f"Autenticación exitosa con IOL para usuario: {self.username}")
                    return True
                else:
                    logger.error("IOL no retornó access_token en la respuesta")
                    return False
            else:
                logger.error(f"Error autenticando con IOL: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al autenticar con IOL")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al autenticar con IOL: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Excepción inesperada al autenticar con IOL: {str(e)}")
            return False
    
    async def obtener_portfolio(self) -> Optional[List[Dict]]:
        """
        Obtiene el portfolio desde IOL
        
        Returns:
            Lista de activos en formato estándar o None si hay error
        """
        if not self.access_token:
            # Intentar autenticar si no hay token
            auth_success = await self.autenticar()
            if not auth_success:
                logger.error("No se pudo autenticar con IOL para obtener portfolio")
                return None
        
        try:
            url = f"{self.BASE_URL}/api/v2/portafolio/argentina"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Transformar datos de IOL a formato estándar
                portfolio = []
                for item in data.get("activos", []):
                    portfolio.append({
                        "ticker": item.get("simbolo", ""),
                        "name": item.get("descripcion", ""),
                        "quantity": item.get("cantidad", 0),
                        "avg_price": item.get("precioCompra", 0),
                        "current_price": item.get("ultimoPrecio", 0),
                        "market_value": item.get("valorizado", 0),
                        "profit_loss": item.get("gananciaPerdida", 0),
                        "profit_loss_pct": item.get("gananciaPerdidaPorcentaje", 0),
                        "broker": "IOL",
                        "synced_at": datetime.now().isoformat()
                    })
                
                logger.info(f"Portfolio de IOL obtenido exitosamente: {len(portfolio)} activos")
                return portfolio
            elif response.status_code == 401:
                # Token expirado, intentar reautenticar
                logger.warning("Token de IOL expirado, reautenticando...")
                auth_success = await self.autenticar()
                if auth_success:
                    # Reintentar obtener portfolio
                    return await self.obtener_portfolio()
                else:
                    logger.error("No se pudo reautenticar con IOL")
                    return None
            else:
                logger.error(f"Error obteniendo portfolio de IOL: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al obtener portfolio de IOL")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión al obtener portfolio de IOL: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Excepción inesperada al obtener portfolio de IOL: {str(e)}")
            return None
    
    async def validar_credenciales(self) -> bool:
        """
        Valida que las credenciales sean correctas
        
        Returns:
            True si las credenciales son válidas, False en caso contrario
        """
        return await self.autenticar()
    
    def obtener_info(self) -> Dict:
        """
        Obtiene información sobre la conexión
        
        Returns:
            Diccionario con información de la conexión
        """
        return {
            "broker": "IOL",
            "username": self.username,
            "has_token": self.access_token is not None,
            "base_url": self.BASE_URL
        }


# Funciones de compatibilidad con el código existente
async def get_iol_access_token(username: str, password: str) -> Optional[str]:
    """
    Función de compatibilidad para obtener access token de IOL
    
    Args:
        username: Usuario de IOL
        password: Contraseña de IOL
    
    Returns:
        Access token o None si hay error
    """
    conexion = ConexionIOL(username, password)
    success = await conexion.autenticar()
    return conexion.access_token if success else None

async def get_iol_portfolio(access_token: str) -> Optional[List[Dict]]:
    """
    Función de compatibilidad para obtener portfolio de IOL
    
    Args:
        access_token: Token de acceso de IOL
    
    Returns:
        Lista de activos o None si hay error
    """
    # Nota: Esta función requiere token, pero la clase maneja autenticación automática
    # Por compatibilidad, creamos una conexión temporal
    # En producción, se recomienda usar la clase ConexionIOL directamente
    conexion = ConexionIOL("", "")
    conexion.access_token = access_token
    return await conexion.obtener_portfolio()

