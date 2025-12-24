"""
Sistema de Ejecución Automática y Backtesting de Reglas
Maneja la verificación de reglas, ejecución automática y backtesting
"""
import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import asyncio

logger = logging.getLogger(__name__)

class RuleEvaluator:
    """Evalúa si una regla se cumple con los datos actuales del mercado"""
    
    @staticmethod
    async def evaluate_rule(rule: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Evalúa si una regla se cumple
        
        Args:
            rule: Diccionario con datos de la regla
        
        Returns:
            Tuple (se_cumple, datos_actuales)
        """
        try:
            ticker = rule.get("ticker")
            rule_type = rule.get("rule_type")
            value_threshold = float(rule.get("value_threshold", 0))
            
            if not ticker or not rule_type:
                return False, None
            
            # Obtener datos del activo
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or len(info) == 0:
                logger.warning(f"No se pudieron obtener datos para {ticker}")
                return False, None
            
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            if not current_price:
                logger.warning(f"No se pudo obtener precio actual para {ticker}")
                return False, None
            
            # Evaluar según tipo de regla
            condition_met = False
            
            if rule_type == "price_below":
                condition_met = current_price < value_threshold
                
            elif rule_type == "price_above":
                condition_met = current_price > value_threshold
                
            elif rule_type == "pe_below":
                pe_ratio = info.get("trailingPE") or info.get("forwardPE")
                if pe_ratio:
                    condition_met = pe_ratio < value_threshold
                    
            elif rule_type == "pe_above":
                pe_ratio = info.get("trailingPE") or info.get("forwardPE")
                if pe_ratio:
                    condition_met = pe_ratio > value_threshold
                    
            elif rule_type == "max_distance":
                # Obtener máximo histórico (52 semanas)
                high_52w = info.get("fiftyTwoWeekHigh")
                if high_52w:
                    distance = ((current_price - high_52w) / high_52w) * 100
                    # value_threshold es negativo para "debajo del máximo"
                    condition_met = distance <= value_threshold
            
            current_data = {
                "ticker": ticker,
                "current_price": current_price,
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
                "high_52w": info.get("fiftyTwoWeekHigh"),
                "evaluated_at": datetime.now().isoformat()
            }
            
            return condition_met, current_data
            
        except Exception as e:
            logger.error(f"Error evaluando regla {rule.get('id')}: {str(e)}")
            return False, None


class BacktestEngine:
    """Motor de backtesting para reglas"""
    
    @staticmethod
    async def run_backtest(rule: Dict, start_date: str, end_date: str, initial_capital: float = 10000) -> Dict:
        """
        Ejecuta un backtest de una regla
        
        Args:
            rule: Diccionario con datos de la regla
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            initial_capital: Capital inicial para simulación
        
        Returns:
            Diccionario con resultados del backtest
        """
        try:
            ticker = rule.get("ticker")
            rule_type = rule.get("rule_type")
            value_threshold = float(rule.get("value_threshold", 0))
            execution_type = rule.get("execution_type", "ALERT_ONLY")
            
            if not ticker or not rule_type:
                return {
                    "success": False,
                    "error": "Ticker o tipo de regla no especificado"
                }
            
            # Obtener datos históricos
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                return {
                    "success": False,
                    "error": "No se pudieron obtener datos históricos"
                }
            
            # Inicializar variables de backtest
            capital = initial_capital
            positions = []  # Lista de posiciones abiertas
            executions = []
            daily_equity = []
            max_capital = initial_capital
            max_drawdown = 0
            
            wins = 0
            losses = 0
            total_profit = 0
            total_loss = 0
            
            # Iterar sobre cada día
            for date, row in hist.iterrows():
                current_price = float(row["Close"])
                current_date = date.strftime("%Y-%m-%d")
                
                # Evaluar condición de la regla
                condition_met = False
                
                if rule_type == "price_below":
                    condition_met = current_price < value_threshold
                elif rule_type == "price_above":
                    condition_met = current_price > value_threshold
                elif rule_type == "pe_below":
                    # Para backtesting, usar precio como proxy (en producción se usaría P/E real)
                    # Esto es una simplificación
                    condition_met = False  # P/E requiere datos fundamentales diarios
                elif rule_type == "pe_above":
                    condition_met = False
                elif rule_type == "max_distance":
                    high_so_far = float(hist.loc[:date, "High"].max())
                    distance = ((current_price - high_so_far) / high_so_far) * 100
                    condition_met = distance <= value_threshold
                
                # Si la condición se cumple y hay ejecución automática
                if condition_met and execution_type in ["BUY", "SELL"]:
                    quantity = rule.get("quantity", 0)
                    if quantity > 0:
                        execution = {
                            "date": current_date,
                            "price": current_price,
                            "type": execution_type,
                            "quantity": quantity,
                            "amount": current_price * quantity
                        }
                        
                        if execution_type == "BUY":
                            if capital >= execution["amount"]:
                                capital -= execution["amount"]
                                positions.append({
                                    "entry_price": current_price,
                                    "quantity": quantity,
                                    "entry_date": current_date
                                })
                                execution["status"] = "EXECUTED"
                            else:
                                execution["status"] = "INSUFFICIENT_FUNDS"
                        elif execution_type == "SELL":
                            if positions:
                                # Vender primera posición
                                position = positions.pop(0)
                                profit = (current_price - position["entry_price"]) * quantity
                                capital += execution["amount"]
                                
                                if profit > 0:
                                    wins += 1
                                    total_profit += profit
                                else:
                                    losses += 1
                                    total_loss += abs(profit)
                                
                                execution["status"] = "EXECUTED"
                                execution["profit_loss"] = profit
                            else:
                                execution["status"] = "NO_POSITION"
                        
                        executions.append(execution)
                
                # Calcular equity actual (capital + valor de posiciones)
                positions_value = sum(p["entry_price"] * p["quantity"] for p in positions)
                current_equity = capital + positions_value
                
                # Actualizar máximo y drawdown
                if current_equity > max_capital:
                    max_capital = current_equity
                drawdown = ((max_capital - current_equity) / max_capital) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                daily_equity.append({
                    "date": current_date,
                    "equity": current_equity,
                    "capital": capital,
                    "positions_value": positions_value
                })
            
            # Cerrar posiciones abiertas al final
            final_price = float(hist.iloc[-1]["Close"])
            for position in positions:
                profit = (final_price - position["entry_price"]) * position["quantity"]
                capital += final_price * position["quantity"]
                
                if profit > 0:
                    wins += 1
                    total_profit += profit
                else:
                    losses += 1
                    total_loss += abs(profit)
            
            final_capital = capital
            total_return = ((final_capital - initial_capital) / initial_capital) * 100
            total_pl = final_capital - initial_capital
            
            # Calcular métricas
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.get("status") == "EXECUTED"])
            failed_executions = total_executions - successful_executions
            
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
            profit_factor = (total_profit / total_loss) if total_loss > 0 else (total_profit if total_profit > 0 else 0)
            
            # Calcular Sharpe ratio simplificado (requiere más datos)
            sharpe_ratio = 0  # Placeholder, requiere cálculo de volatilidad
            
            return {
                "success": True,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "final_capital": final_capital,
                "total_return": total_return,
                "total_profit_loss": total_pl,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "sharpe_ratio": sharpe_ratio,
                "execution_details": executions,
                "daily_equity_curve": daily_equity
            }
            
        except Exception as e:
            logger.error(f"Error en backtest: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

