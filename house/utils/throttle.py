from rest_framework.throttling import BaseThrottle, SimpleRateThrottle


class MyThrottle(SimpleRateThrottle):
    scope = "xxx"
    THROTTLE_RATES = {'xxx': '1/m'}

    def get_cache_key(self, request, view):
        if request.user:
            ident=request.user.id
        else:
            ident=self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }