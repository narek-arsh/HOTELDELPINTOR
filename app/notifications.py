import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

_initialized = False


def init_firebase():
    """Inicializa Firebase Admin usando el JSON de credenciales en la variable de entorno FIREBASE_CREDENTIALS_JSON."""
    global _initialized
    if _initialized:
        return
    raw = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if not raw:
        print("⚠️  FIREBASE_CREDENTIALS_JSON no configurada — notificaciones push desactivadas")
        return
    try:
        cred_dict = json.loads(raw)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        _initialized = True
        print("✅ Firebase Admin inicializado")
    except Exception as e:
        print(f"⚠️  Error inicializando Firebase: {e}")


def enviar_notificacion(tokens: list[str], titulo: str, cuerpo: str, data: dict = None) -> dict:
    """Envía una notificación push a una lista de tokens de dispositivo. Devuelve un resumen de éxitos/fallos."""
    if not _initialized:
        print("[enviar_notificacion] Firebase no inicializado, abortando")
        return {"enviados": 0, "fallidos": 0, "tokens_invalidos": []}
    if not tokens:
        return {"enviados": 0, "fallidos": 0, "tokens_invalidos": []}

    enviados = 0
    fallidos = 0
    tokens_invalidos = []

    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=titulo, body=cuerpo),
                data={k: str(v) for k, v in (data or {}).items()},
                token=token,
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=titulo,
                        body=cuerpo,
                        icon="/icon-192.png",
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=data.get("link", "/") if data else "/"
                    ),
                ),
            )
            messaging.send(message)
            enviados += 1
        except messaging.UnregisteredError:
            print(f"[enviar_notificacion] Token inválido (no registrado): {token[:20]}...")
            tokens_invalidos.append(token)
            fallidos += 1
        except Exception as e:
            print(f"[enviar_notificacion] ERROR con token {token[:20]}...: {type(e).__name__} - {e}")
            fallidos += 1

    return {"enviados": enviados, "fallidos": fallidos, "tokens_invalidos": tokens_invalidos}
