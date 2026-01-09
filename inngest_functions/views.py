from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from inngest._internal import comm, const
from ecommerce_inngest import inngest_client
from .send_verification_email import send_verification_email_fn
from .process_shipping import process_shipping_fn
import json
import asyncio

# Lista de funções registradas
functions = [send_verification_email_fn, process_shipping_fn]

# Criar o handler de comunicação do Inngest
handler = comm.CommHandler(
    api_base_url=const.DEFAULT_API_ORIGIN,
    client=inngest_client,
    framework=const.Framework.DJANGO,
    functions=functions,
)


def run_async(coro):
    """Helper para rodar código async em view sync"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


@csrf_exempt
@require_http_methods(["GET", "PUT", "POST"])
def inngest_endpoint(request):
    """
    Endpoint personalizado para Inngest
    """
    try:
        # Constrói a URL base do app
        app_url = request.build_absolute_uri('/api/inngest/')
        server_kind = const.ServerKind.CLOUD
        
        # GET - Introspection
        if request.method == "GET":
            result = run_async(handler.introspect(
                app_url=app_url,
                server_kind=server_kind,
            ))
            return JsonResponse(result.body, status=result.status_code)
        
        # PUT - Sync (registro de funções)
        elif request.method == "PUT":
            result = run_async(handler.register(
                app_url=app_url,
                server_kind=server_kind,
            ))
            return JsonResponse(result.body, status=result.status_code)
        
        # POST - Execute function
        elif request.method == "POST":
            body = json.loads(request.body)
            
            result = run_async(handler.call_function_sync(
                call=comm.FunctionCallRequest(**body),
                fn_id=body.get("fn_id"),
                raw_request=request,
            ))
            
            return JsonResponse(result.body, status=result.status_code)
    
    except Exception as e:
        print(f"[INNGEST ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse(
            {"error": str(e), "type": type(e).__name__},
            status=500
        )