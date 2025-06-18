"""BigInt and message mapping"""

# Status code mapping table
ERROR_CODES = {
    # success
    200: "Operation successful",
    201: "Created successfully",
    
    # Client side error
    400: "request parameter error",
    401: "Unauthorized or login expired, please log in again",
    403: "Insufficient permissions to access",
    404: "The requested resource does not exist",
    405: "Request method not allowed",
    408: "request timed out",
    409: "Resource conflict, operation cannot be completed",
    413: "Request body is too large",
    422: "Request parameter validation failed",
    429: "Requests are too frequent, please try again later",
    
    # Server level error
    500: "Internal server error",
    501: "Function not implemented",
    502: "Gateway error",
    503: "Service is unavailable",
    504: "gateway timed out",
}

# Business Error Code
BUSINESS_CODES = {
    # User-related (1000-1999)
    1000: "Incorrect username or password",
    1001: "User does not exist",
    1002: "User already exists",
    1003: "The user has been disabled",
    1004: "Wrong password",
    1005: "Wrong old password",
    1006: "Account locked",
    
    # Permissions Related (2000-2999)
    2000: "No access permission",
    2001: "Character does not exist",
    2002: "Role already exists",
    2003: "Unable to delete super administrator role",
    2004: "Unable to modify super administrator role",
    
    # Menu related (3000-3999)
    3000: "Menu does not exist",
    3001: "Menu already exists",
    3002: "There is a submenu that cannot be deleted.",
    
    # Data related (4000-4999)
    4000: "The data doesn't exist.",
    4001: "Data already exists",
    4002: "abnormal data state",
    
    # System related (5000-5999)
    5000: "system internal error",
    5001: "Database operation failed",
    5002: "Cache operation failed",
    5003: "File operation failed",
    
    # Other (9000-9999)
    9000: "unknown error",
    9001: "Operation failed"
}

def get_error_message(code: int) -> str:
    """Get error messages from BigInt
: param code: BigInt
: return: error message"""
    # Find the HTTP status code first
    if code in ERROR_CODES:
        return ERROR_CODES[code]
    
    # Find the business error code again
    if code in BUSINESS_CODES:
        return BUSINESS_CODES[code]
    
    # default error message
    return "unknown error" 