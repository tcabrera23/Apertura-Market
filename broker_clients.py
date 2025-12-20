"""
Broker API clients for IOL and Binance
"""
import requests
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

async def get_iol_access_token(username: str, password: str) -> Optional[str]:
    """
    Authenticate with IOL API and get access token
    https://api.invertironline.com
    """
    try:
        url = "https://api.invertironline.com/token"
        
        payload = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }
        
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            logger.error(f"Error authenticating with IOL: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception in IOL authentication: {str(e)}")
        return None

async def get_iol_portfolio(access_token: str) -> Optional[List[Dict]]:
    """
    Get portfolio from IOL API
    """
    try:
        url = "https://api.invertironline.com/api/v2/portafolio/argentina"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Transform IOL data to our standard format
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
                    "broker": "IOL"
                })
            
            return portfolio
        else:
            logger.error(f"Error fetching IOL portfolio: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception in IOL portfolio fetch: {str(e)}")
        return None

async def get_binance_portfolio(api_key: str, api_secret: str) -> Optional[List[Dict]]:
    """
    Get portfolio from Binance API
    https://binance-docs.github.io/apidocs/spot/en/#account-information-user_data
    """
    try:
        base_url = "https://api.binance.com"
        endpoint = "/api/v3/account"
        
        # Generate signature
        timestamp = int(datetime.now().timestamp() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        headers = {
            "X-MBX-APIKEY": api_key
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Get current prices for all assets
            prices_url = f"{base_url}/api/v3/ticker/price"
            prices_response = requests.get(prices_url)
            prices_data = prices_response.json() if prices_response.status_code == 200 else []
            prices_dict = {item["symbol"]: float(item["price"]) for item in prices_data}
            
            # Transform Binance data to our standard format
            portfolio = []
            for balance in data.get("balances", []):
                free = float(balance.get("free", 0))
                locked = float(balance.get("locked", 0))
                total = free + locked
                
                if total > 0:  # Only include assets with balance
                    asset = balance.get("asset", "")
                    symbol = f"{asset}USDT"
                    current_price = prices_dict.get(symbol, 0)
                    
                    # If asset is USDT, price is 1
                    if asset == "USDT":
                        current_price = 1.0
                    
                    market_value = total * current_price
                    
                    portfolio.append({
                        "ticker": asset,
                        "name": asset,
                        "quantity": total,
                        "avg_price": 0,  # Binance doesn't provide purchase price
                        "current_price": current_price,
                        "market_value": market_value,
                        "profit_loss": 0,  # Can't calculate without purchase price
                        "profit_loss_pct": 0,
                        "broker": "BINANCE"
                    })
            
            return portfolio
        else:
            logger.error(f"Error fetching Binance portfolio: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception in Binance portfolio fetch: {str(e)}")
        return None

