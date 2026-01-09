import inngest
import os

signing_key = os.getenv("INNGEST_SIGNING_KEY")

if not signing_key:
    print("[INNGEST WARNING] INNGEST_SIGNING_KEY não está definida!")
    print("[INNGEST WARNING] O Inngest Cloud não conseguirá se comunicar com seu app")

inngest_client = inngest.Inngest(
    app_id="inngest_functions",
    signing_key=signing_key,  
    is_production=bool(signing_key), 
)

print(f"[INNGEST] Cliente configurado:")
print(f"  - App ID: inngest_functions")
print(f"  - Signing Key: {'✓ Configurada' if signing_key else '✗ FALTANDO'}")
print(f"  - Modo Produção: {bool(signing_key)}")

__all__ = ['inngest_client']