# webapp/bankapp/branches/middleware.py
import logging
import json
import time
from django.shortcuts import redirect

logger = logging.getLogger('django')

class InsiderThreatMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        ip = self.get_client_ip(request)
        method = request.method
        url = request.get_full_path()
        user_agent = request.headers.get('User-Agent', 'Unknown')
        employee_id = request.session.get('employee_id', request.POST.get('employee_id', 'N/A'))
        user = request.user.username if request.user.is_authenticated else 'Anonymous'

        response = self.get_response(request)

        process_time = time.time() - start_time
        log_data = {
            'ip': ip,
            'method': method,
            'url': url,
            'user_agent': user_agent,
            'employee_id': employee_id,
            'user': user,
            'status_code': response.status_code,
            'process_time': process_time,
        }

        logger.info(json.dumps(log_data))

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/dashboard') and request.session.get('user_role') not in ['compliance', 'employee']:
            return redirect('/')

        response = self.get_response(request)
        return response