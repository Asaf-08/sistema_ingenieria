class NoCacheMiddleware:
    """
    Middleware que evita que el navegador guarde en caché las páginas 
    de usuarios autenticados. Previene el problema del botón 'Atrás' tras el Logout.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Si el usuario ha iniciado sesión, le decimos al navegador que destruya la página al salir
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
        return response