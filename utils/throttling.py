from rest_framework.throttling import SimpleRateThrottle

class AuthRateThrottle(SimpleRateThrottle):
    """
    Limits authentication endpoints (login, register) to 15 requests per 15 minutes per IP.
    Matches Express authLimiter to prevent brute force attacks.
    """
    scope = 'auth'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    def parse_rate(self, rate):
        if not rate:
            return (15, 900)
        try:
            num, period = rate.split('/')
            num_requests = int(num)
            if period.endswith('m'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 60)
            elif period.endswith('s'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier)
            elif period.endswith('h'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 3600)
            elif period.endswith('d'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 86400)
        except Exception:
            pass
        return super().parse_rate(rate)


class GeneralAnonRateThrottle(SimpleRateThrottle):
    """
    Limits unauthenticated API requests to 100 requests per 15 minutes per IP.
    Matches Express generalLimiter.
    """
    scope = 'anon'

    def get_cache_key(self, request, view):
        if request.user and getattr(request.user, 'is_authenticated', False):
            return None
        ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

    def parse_rate(self, rate):
        if not rate:
            return (100, 900)
        try:
            num, period = rate.split('/')
            num_requests = int(num)
            if period.endswith('m'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 60)
            elif period.endswith('s'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier)
            elif period.endswith('h'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 3600)
            elif period.endswith('d'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 86400)
        except Exception:
            pass
        return super().parse_rate(rate)


class GeneralUserRateThrottle(SimpleRateThrottle):
    """
    Limits authenticated requests to 1000 requests per hour per user.
    """
    scope = 'user'

    def get_cache_key(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': request.user.pk
        }

    def parse_rate(self, rate):
        if not rate:
            return (1000, 3600)
        try:
            num, period = rate.split('/')
            num_requests = int(num)
            if period.endswith('m'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 60)
            elif period.endswith('h'):
                multiplier = int(period[:-1]) if len(period) > 1 else 1
                return (num_requests, multiplier * 3600)
        except Exception:
            pass
        return super().parse_rate(rate)
