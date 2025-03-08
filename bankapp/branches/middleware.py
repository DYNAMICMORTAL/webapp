import logging

logger = logging.getLogger('django')

class InsiderThreatMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract request details
        ip = self.get_client_ip(request)
        method = request.method
        url = request.get_full_path()
        user_agent = request.headers.get('User-Agent', 'Unknown')
        employee_id = request.POST.get('employee_id', 'N/A')  # Capture Employee ID if available

        # Log the details
        logger.info(f"IP: {ip}, Method: {method}, URL: {url}, User-Agent: {user_agent}, Employee ID: {employee_id}")

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """Extracts IP address from the request headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
