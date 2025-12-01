"""
Email Templates para BullAnalytics
Templates HTML para diferentes tipos de correos electrónicos
"""

from datetime import datetime
from typing import Dict, Optional


def get_onboarding_email_template(user_name: str, user_email: str) -> Dict[str, str]:
    """
    Template de email de bienvenida/onboarding
    
    Args:
        user_name: Nombre del usuario
        user_email: Email del usuario
    
    Returns:
        Dict con 'subject' y 'html_content'
    """
    subject = "¡Bienvenido a BullAnalytics! 🚀"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #28a745 0%, #218838 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .content h2 {{
                color: #28a745;
                margin-top: 0;
            }}
            .features {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .features ul {{
                list-style: none;
                padding: 0;
            }}
            .features li {{
                padding: 10px 0;
                border-bottom: 1px solid #e0e0e0;
            }}
            .features li:last-child {{
                border-bottom: none;
            }}
            .features li::before {{
                content: "✅ ";
                margin-right: 10px;
            }}
            .button {{
                display: inline-block;
                padding: 15px 40px;
                background: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
                text-align: center;
            }}
            .button:hover {{
                background: #218838;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            .footer a {{
                color: #28a745;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 BullAnalytics</h1>
                <p>Tu plataforma de análisis financiero</p>
            </div>
            <div class="content">
                <h2>¡Hola {user_name}! 👋</h2>
                <p>Nos complace darte la bienvenida a <strong>BullAnalytics</strong>, tu herramienta completa para el análisis y seguimiento de activos financieros.</p>
                
                <div class="features">
                    <h3>Con BullAnalytics puedes:</h3>
                    <ul>
                        <li>Crear listas personalizadas de seguimiento</li>
                        <li>Configurar alertas automáticas por email</li>
                        <li>Analizar métricas técnicas y fundamentales</li>
                        <li>Visualizar tus activos con gráficos interactivos</li>
                        <li>Recibir notificaciones en tiempo real</li>
                    </ul>
                </div>
                
                <p><strong>¿Listo para empezar?</strong></p>
                <p>Te recomendamos comenzar creando tu primera lista de seguimiento o configurando una alerta para estar al tanto de los movimientos del mercado.</p>
                
                <div style="text-align: center;">
                    <a href="http://localhost:8080/dashboard.html" class="button">Ir al Dashboard</a>
                </div>
                
                <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                    <small>Si tienes alguna pregunta, no dudes en contactarnos. Estamos aquí para ayudarte.</small>
                </p>
            </div>
            <div class="footer">
                <p>Este es un correo automático de BullAnalytics.</p>
                <p>© {datetime.now().year} BullAnalytics. Todos los derechos reservados.</p>
                <p>
                    <a href="#">Gestionar preferencias</a> | 
                    <a href="#">Soporte</a> | 
                    <a href="#">Política de Privacidad</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "html_content": html_content
    }


def get_alert_email_template(
    rule_name: str,
    ticker: str,
    alert_message: str,
    current_price: float,
    threshold: float,
    rule_type: str
) -> Dict[str, str]:
    """
    Template de email para alertas financieras
    
    Args:
        rule_name: Nombre de la regla
        ticker: Símbolo del activo
        alert_message: Mensaje de la alerta
        current_price: Precio actual
        threshold: Valor umbral
        rule_type: Tipo de regla (price_below, price_above, etc.)
    
    Returns:
        Dict con 'subject' y 'html_content'
    """
    # Determinar emoji y color según tipo de alerta
    if "below" in rule_type or "bajo" in alert_message.lower():
        emoji = "📉"
        color = "#dc3545"  # Rojo
        trend = "bajó"
    elif "above" in rule_type or "encima" in alert_message.lower():
        emoji = "📈"
        color = "#28a745"  # Verde
        trend = "subió"
    else:
        emoji = "🔔"
        color = "#ffc107"  # Amarillo
        trend = "cambió"
    
    subject = f"{emoji} Alerta: {ticker} - {alert_message}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 30px;
            }}
            .alert-box {{
                background: #fff3cd;
                border-left: 4px solid {color};
                padding: 20px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .alert-box h3 {{
                margin-top: 0;
                color: {color};
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
            }}
            .info-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
            }}
            .info-item strong {{
                display: block;
                color: #666;
                font-size: 12px;
                text-transform: uppercase;
                margin-bottom: 5px;
            }}
            .info-item span {{
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background: {color};
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{emoji} Alerta de BullAnalytics</h1>
            </div>
            <div class="content">
                <div class="alert-box">
                    <h3>{alert_message}</h3>
                    <p>Tu regla <strong>"{rule_name}"</strong> se ha activado.</p>
                </div>
                
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Activo</strong>
                        <span>{ticker}</span>
                    </div>
                    <div class="info-item">
                        <strong>Precio Actual</strong>
                        <span>${current_price:,.2f}</span>
                    </div>
                    <div class="info-item">
                        <strong>Umbral</strong>
                        <span>${threshold:,.2f}</span>
                    </div>
                    <div class="info-item">
                        <strong>Estado</strong>
                        <span>{trend.capitalize()}</span>
                    </div>
                </div>
                
                <p>Esta alerta se generó automáticamente cuando el precio {trend} por encima/debajo del umbral que configuraste.</p>
                
                <div style="text-align: center;">
                    <a href="http://localhost:8080/dashboard.html" class="button">Ver Dashboard</a>
                    <a href="http://localhost:8080/rules.html" class="button" style="background: #6c757d; margin-left: 10px;">Gestionar Alertas</a>
                </div>
            </div>
            <div class="footer">
                <p>Este es un correo automático de BullAnalytics.</p>
                <p>Puedes gestionar tus alertas en tu panel de control.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "html_content": html_content
    }


def get_password_reset_email_template(reset_link: str, user_name: str) -> Dict[str, str]:
    """
    Template de email para restablecimiento de contraseña
    
    Args:
        reset_link: Link para restablecer contraseña
        user_name: Nombre del usuario
    
    Returns:
        Dict con 'subject' y 'html_content'
    """
    subject = "Restablecer tu contraseña - BullAnalytics"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #28a745 0%, #218838 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .button {{
                display: inline-block;
                padding: 15px 40px;
                background: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 12px;
            }}
            .warning {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 BullAnalytics</h1>
            <p>Restablecer Contraseña</p>
        </div>
        <div class="content">
            <h2>Hola {user_name},</h2>
            <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en BullAnalytics.</p>
            
            <div style="text-align: center;">
                <a href="{reset_link}" class="button">Restablecer Contraseña</a>
            </div>
            
            <div class="warning">
                <p><strong>⚠️ Importante:</strong></p>
                <ul>
                    <li>Este link expirará en 1 hora</li>
                    <li>Si no solicitaste este cambio, ignora este correo</li>
                    <li>Nunca compartas este link con nadie</li>
                </ul>
            </div>
            
            <p>Si el botón no funciona, copia y pega este enlace en tu navegador:</p>
            <p style="word-break: break-all; color: #28a745;">{reset_link}</p>
        </div>
        <div class="footer">
            <p>Este es un correo automático de BullAnalytics.</p>
            <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "html_content": html_content
    }


def get_subscription_confirmation_email_template(
    plan_name: str,
    price: float,
    billing_period: str = "mensual"
) -> Dict[str, str]:
    """
    Template de email para confirmación de suscripción
    
    Args:
        plan_name: Nombre del plan
        price: Precio del plan
        billing_period: Período de facturación
    
    Returns:
        Dict con 'subject' y 'html_content'
    """
    subject = f"Confirmación de Suscripción - {plan_name}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #28a745 0%, #218838 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .success-box {{
                background: #d4edda;
                border-left: 4px solid #28a745;
                padding: 20px;
                margin: 20px 0;
            }}
            .info-box {{
                background: white;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✅ Suscripción Confirmada</h1>
        </div>
        <div class="content">
            <div class="success-box">
                <h2>¡Gracias por tu suscripción!</h2>
                <p>Tu suscripción a <strong>{plan_name}</strong> ha sido confirmada exitosamente.</p>
            </div>
            
            <div class="info-box">
                <h3>Detalles de tu suscripción:</h3>
                <p><strong>Plan:</strong> {plan_name}</p>
                <p><strong>Precio:</strong> ${price:.2f} / {billing_period}</p>
                <p><strong>Estado:</strong> Activa</p>
            </div>
            
            <p>Ahora tienes acceso completo a todas las funcionalidades de tu plan. ¡Disfruta de BullAnalytics!</p>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "html_content": html_content
    }

