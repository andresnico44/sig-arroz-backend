import socket
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.urls import reverse
# pyrefly: ignore [missing-import]
from django_rest_passwordreset.signals import reset_password_token_created
from django.conf import settings

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Envía un correo real con el enlace de recuperación y un diseño HTML espectacular
    """
    # Establecer un tiempo límite de conexión de 5 segundos para evitar cuelgues del servidor Gunicorn
    socket.setdefaulttimeout(5)

    # Enlace dinámico según el entorno (Local o Producción)
    if settings.DEBUG:
        reset_url = f"http://localhost:5173/reset-password?token={reset_password_token.key}"
    else:
        reset_url = f"https://sig-arroz-frontend.vercel.app/reset-password?token={reset_password_token.key}"

    # Detalles del Correo
    subject = "Recuperación de Contraseña - SIG-ARROZ 🌾"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@sig-arroz.com')
    to_email = reset_password_token.user.email

    # Contenido en Texto Plano (para bandejas antiguas)
    text_content = (
        f"Hola {reset_password_token.user.username},\n\n"
        f"Hemos recibido una solicitud para restablecer tu contraseña en la plataforma SIG-ARROZ.\n"
        f"Por favor, haz clic en el siguiente enlace para crear una nueva clave (el token es de un solo uso):\n\n"
        f"{reset_url}\n\n"
        f"Si tú no solicitaste esto, puedes ignorar este correo.\n\n"
        f"Atentamente,\nEl Equipo de SIG-ARROZ."
    )

    # HTML Corporativo Premium (Verde Agrícola y detalles profesionales)
    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f7f4; padding: 40px 20px; color: #112d18;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 40px rgba(30, 86, 49, 0.1); overflow: hidden; border: 1px solid #e1ebe6;">
            <!-- Cabecera -->
            <div style="background-color: #1e5631; padding: 30px; text-align: center;">
                <span style="font-size: 28px; font-weight: bold; color: #ffffff; letter-spacing: 1px; display: inline-flex; align-items: center; gap: 8px;">
                    🌾 SIG-ARROZ
                </span>
            </div>
            
            <!-- Cuerpo -->
            <div style="padding: 40px 30px; line-height: 1.6;">
                <h2 style="color: #1e5631; margin-top: 0; font-size: 22px; font-weight: 700;">¡Hola, {reset_password_token.user.username}!</h2>
                <p style="font-size: 15px; color: #4a5a4e; margin-bottom: 20px;">
                    Hemos recibido una solicitud para restablecer tu contraseña de acceso en la plataforma de monitoreo y control del cultivo de arroz <strong>SIG-ARROZ</strong>.
                </p>
                <p style="font-size: 15px; color: #4a5a4e; margin-bottom: 30px;">
                    Para establecer una nueva contraseña, haz clic en el botón de abajo. Ten en cuenta que este enlace expira en un periodo de 24 horas y es válido para un único uso.
                </p>
                
                <!-- Botón -->
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{reset_url}" style="background-color: #4c9a2a; color: #ffffff; text-decoration: none; font-weight: bold; padding: 15px 35px; border-radius: 12px; font-size: 16px; box-shadow: 0 6px 20px rgba(76, 154, 42, 0.25); display: inline-block;">
                        Restablecer Contraseña
                    </a>
                </div>
                
                <p style="font-size: 12px; color: #889988; text-align: center; margin-top: 25px;">
                    Si el botón de arriba no responde, copia y pega este enlace en tu navegador:<br>
                    <a href="{reset_url}" style="color: #4c9a2a; text-decoration: underline;">{reset_url}</a>
                </p>
                
                <hr style="border: 0; border-top: 1px solid #e2ece6; margin: 30px 0;">
                
                <p style="font-size: 13px; color: #6a7a6e;">
                    Si no has realizado esta solicitud, puedes ignorar este correo de forma segura. Tu contraseña actual no sufrirá ningún cambio.
                </p>
            </div>
            
            <!-- Pie de página -->
            <div style="background-color: #f8faf9; padding: 20px; text-align: center; font-size: 12px; color: #8a9a8d; border-top: 1px solid #eef2f0;">
                Plataforma SIG-ARROZ &copy; 2026. Todos los derechos reservados.
            </div>
        </div>
    </div>
    """

    # ---------------------------------------------------------
    # COMPORTAMIENTO HÍBRIDO DEFINITIVO: CORREOS REALES EN AMBOS
    # ---------------------------------------------------------
    import logging
    logger = logging.getLogger(__name__)
    
    # Este log se imprimirá AL INSTANTE en Railway y nos confirmará si la señal arrancó
    logger.info(f"🟢 [SIGNAL TRIGGERED] Iniciando proceso de envío para: {to_email} (DEBUG={settings.DEBUG})")

    if settings.DEBUG:
        # En LOCAL: Envía el correo real usando el SMTP tradicional de Django
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
            logger.info(f"📧 [EMAIL SUCCESS] Correo SMTP local enviado a: {to_email}")
        except Exception as e:
            logger.error(f"❌ [EMAIL ERROR] No se pudo enviar el correo SMTP en local: {e}")
    else:
        # En PRODUCCIÓN (Railway): Envía el correo real usando la API HTTP de Brevo (Bypass de bloqueo)
        import requests
        api_key = getattr(settings, 'BREVO_API_KEY', getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
        url = "https://api.brevo.com/v3/smtp/email"
        
        payload = {
            "sender": {"email": from_email, "name": "SIG-ARROZ 🌾"},
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": text_content,
            "htmlContent": html_content
        }
        
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }
        
        logger.info(f"📧 [API BREVO] Enviando petición HTTP a Brevo. Remitente: {from_email}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in [200, 201, 202]:
                logger.info(f"📧 [EMAIL SUCCESS] Correo real enviado en producción a: {to_email} vía API HTTP")
            else:
                logger.error(f"❌ [EMAIL ERROR] Error Brevo API en producción: {response.status_code} - {response.text}")
        except Exception as e:
            logger.exception(f"❌ [EMAIL ERROR] Caída de red en producción al enviar HTTP: {e}")





