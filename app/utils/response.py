def success_response(data, status_code=200):
    return {
        "success": True,
        "data": data,
        "error": None,
    }, status_code


def error_response(message, status_code=400):
    return {
        "success": False,
        "data": None,
        "error": message,
    }, status_code
