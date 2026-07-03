import requests
from django.conf import settings


def consultar_dni(dni):
    try:
        response = requests.get(
            f'{settings.RENIEC_URL}/{dni}',
            headers={
                'Authorization': f'Bearer {settings.RENIEC_TOKEN}',
                'Content-Type':  'application/json',
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json().get('data', {})
            return {
                'dni':              data.get('numero', dni),
                'nombres':          data.get('nombres', ''),
                'apellido_paterno': data.get('apellido_paterno', ''),
                'apellido_materno': data.get('apellido_materno', ''),
            }
        elif response.status_code == 404:
            return {'error': 'DNI no encontrado.'}
        elif response.status_code == 401:
            return {'error': 'Token inválido.'}
        else:
            return {'error': f'Error del servicio ({response.status_code}).'}

    except requests.exceptions.Timeout:
        return {'error': 'Tiempo de espera agotado.'}
    except Exception as e:
        return {'error': f'Error de conexión: {str(e)}'}