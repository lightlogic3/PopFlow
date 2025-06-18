"""Parameter Handling Utility Functions"""
from typing import Optional, Any, Dict


def build_filters(**kwargs) -> Dict[str, Any]:
    """Build filter condition dictionaries to automatically handle null values and type conversions

Args:
** kwargs: parameters to be processed

Returns:
Dict [str, Any]: Dictionary of filter conditions after processing"""
    filters = {}
    
    for key, value in kwargs.items():
        if value is None or value == "":
            continue
            
        # If it is a number of type string, try converting it to an integer
        if isinstance(value, str):
            if value.isdigit():
                filters[key] = int(value)
            elif value.lower() in ('true', 'false'):
                filters[key] = value.lower() == 'true'
            else:
                filters[key] = value
        else:
            filters[key] = value
    
    return filters


def safe_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    """Safely convert strings to integers

Args:
Value: string to be converted
Default: default value

Returns:
Optional [int]: Converted integer or default value"""
    if value is None or value == "":
        return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Optional[str], default: Optional[bool] = None) -> Optional[bool]:
    """Safely convert strings to Boolean values

Args:
Value: string to be converted
Default: default value

Returns:
Optional [bool]: converted boolean or default value"""
    if value is None or value == "":
        return default
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    
    return bool(value) 