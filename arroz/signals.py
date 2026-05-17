import socket
import json
import urllib.request
import django.dispatch
import django.conf
# pyrefly: ignore [missing-import]
import django_rest_passwordreset.signals

@django.dispatch.receiver(django_rest_passwordreset.signals.reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
            reset_url = f"https://sig-arroz-frontend.vercel.app/reset-password?token={reset_password_token.key}"
            subject = "Recuperacion de Contrasena - SIG-ARROZ"
            from_email = getattr(django.conf.settings, 'DEFAULT_FROM_EMAIL', 'no-reply@sig-arroz.com')
            to_email = reset_password_token.user.email
            text_content = (
                f"Hola,\n\n"
                f"Hemos recibido una solicitud para restablecer tu contrasena en SIG-ARROZ.\n"
                f"Haz clic en el siguiente enlace para crear una nueva contrasena:\n"
                f"{reset_url}\n\n"
                f"Si no solicitaste este cambio, puedes ignorar este correo.\n\n"
                f"Saludos,\nEl equipo de SIG-ARROZ"
            )
            html_content = f"""
            <html>
            <body>
                <h2>SIG-ARROZ</h2>
                <p>Hola,</p>
                <p>Hemos recibido una solicitud para restablecer tu contrasena.</p>
                <p><a href="{reset_url}" style="background:#10b981;color:#fff;padding:10px 20px;text-decoration:none;border-radius:5px;">Restablecer Contrasena</a></p>
                <p>Si no solicitaste este cambio, ignora este correo.</p>
    </body>
    </html>
    """
        # Brevo API configuration
            api_key = getattr(django.conf.settings, 'EMAIL_HOST_PASSWORD', '')
                url = "https://api.brevo.com/v3/smtp/email"

                        payload = {
                                "sender": {
                                            "name": "SIG-ARROZ",
                                                        "email": from_email
                                                                },
                                                                        "to": [
                                                                                    {
                                                                                                    "email": to_email
                                                                                                                }
                                                                                                                        ],
                                                                                                                                "subject": subject,
                                                                                                                                        "htmlContent": html_content,
                                                                                                                                                "textContent": text_content
                                                                                                                                                    }
                                                                                                                                                        
                                                                                                                                                            headers = {
                                                                                                                                                                    "accept": "application/json",
                                                                                                                                                                            "api-key": api_key,
                                                                                                                                                                                    "content-type": "application/json"
                                                                                                                                                                                        }
                                                                                                                                                                                            
                                                                                                                                                                                                try:
                                                                                                                                                                                                        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                                                                                                                                                                                                                with urllib.request.urlopen(req, timeout=5) as response:
                                                                                                                                                                                                                            res_body = response.read().decode('utf-8')
                                                                                                                                                                                                                                        print(f"EMAIL SUCCESS: Correo enviado por HTTP API a {to_email}. Respuesta: {res_body}")
                                                                                                                                                                                                                                            except Exception as e:
                                                                                                                                                                                                                                                    print(f"EMAIL ERROR: No se pudo enviar el correo a {to_email} por HTTP API. Detalle: {e}")
                                                                                                                                                                                                                                                    
    
