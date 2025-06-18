from fastapi import HTTPException
from typing import Any, Dict, Optional

class BusinessException(HTTPException):
    """Business exception class for throwing business-related exceptions"""
    def __init__(
        self, 
        business_code: int,
        status_code: int = 400, 
        detail: str = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize business exception
: Param business_code: business error code
: Param status_code: HTTP status code
: Param detail: Detailed error information, if None, from error_codes
: param headers: response headers"""
        from .error_codes import get_error_message

        # If no details are provided, it is obtained according to the business error code
        if detail is None:
            detail = get_error_message(business_code)

        # Save business error code
        self.business_code = business_code
        
        # Call the parent class constructor
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        
    def get_error_response(self) -> Dict[str, Any]:
        """Get error response information
: return: error response dictionary"""
        return {
            "code": self.business_code,
            "message": self.detail
        } 