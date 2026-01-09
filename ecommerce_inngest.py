import inngest
import os

signing_key = os.getenv("INNGEST_SIGNING_KEY")  
event_key = os.getenv("INNGEST_EVENT_KEY")    

if not signing_key:
    print("[INNGEST WARNING] INNGEST_SIGNING_KEY não está definida!")
    print("[INNGEST WARNING] O Inngest Cloud não conseguirá chamar suas funções")

if not event_key:
    print("[INNGEST WARNING] INNGEST_EVENT_KEY não está definida!")
    print("[INNGEST WARNING] Você não conseguirá enviar eventos para o Inngest")

inngest_client = inngest.Inngest(
    app_id="inngest_functions",
    signing_key=signing_key,
    event_key=event_key,
    is_production=bool(signing_key),
)

print(f"[INNGEST] Cliente configurado:")
print(f"  - App ID: inngest_functions")
print(f"  - Signing Key: {'✓' if signing_key else '✗ FALTANDO'}")
print(f"  - Event Key: {'✓' if event_key else '✗ FALTANDO'}")
print(f"  - Modo Produção: {bool(signing_key)}")

__all__ = ['inngest_client']