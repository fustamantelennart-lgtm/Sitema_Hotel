import requests
from django.conf import settings


def consultar_dni(dni):
    try:
        response = requests.get(
            f'{settings.RENIEC_URL}/{dni}',
            headers={
                'Authorization': f'Bearer {settings.RENIEC_TOKEN}',
            },
            timeout=10
        )

        try:
            data_json = response.json()
        except ValueError:
            return {'error': 'Respuesta inválida del servicio.'}

        if response.status_code == 200 and data_json.get('success'):
            data = data_json.get('data', {})
            return {
                'dni':              data.get('numero', dni),
                'nombres':          data.get('nombres', ''),
                'apellido_paterno': data.get('apellido_paterno', ''),
                'apellido_materno': data.get('apellido_materno', ''),
            }

        elif response.status_code == 401:
            return {'error': 'Token inválido o expirado.'}

        elif response.status_code == 400:
            # Aquí caen: DNI no encontrado, saldo agotado, DNI mal formado, etc.
            mensaje = data_json.get('message', 'DNI no encontrado o solicitud inválida.')
            return {'error': mensaje}

        else:
            return {'error': f'Error del servicio ({response.status_code}).'}

    except requests.exceptions.Timeout:
        return {'error': 'Tiempo de espera agotado.'}
    except requests.exceptions.ConnectionError:
        return {'error': 'No se pudo conectar con el servicio de consulta.'}
    except Exception as e:
        return {'error': f'Error de conexión: {str(e)}'}