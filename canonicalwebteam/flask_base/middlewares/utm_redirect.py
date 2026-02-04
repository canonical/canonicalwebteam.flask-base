from flask import request
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def add_utm_params_to_redirect(response):
    """Middleware to automatically add UTM params to redirects"""
    if response.status_code in (301, 302, 303, 307, 308):
        location = response.headers.get('Location')
        if location:
            # Get UTM params from cookies
            utm_params = request.cookies.get('utms', '')

            if utm_params:
                parsed_url = urlparse(location)
                query_params = parse_qs(parsed_url.query)

                # Parse UTM params (assuming they're stored as a query string)
                utm_dict = parse_qs(utm_params)

                # Merge UTM params (don't override existing params)
                for key, value in utm_dict.items():
                    if key not in query_params:
                        query_params[key] = value

                # Rebuild URL with params
                new_query = urlencode(query_params, doseq=True)
                new_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query,
                    parsed_url.fragment
                ))

                response.headers['Location'] = new_url

    return response
