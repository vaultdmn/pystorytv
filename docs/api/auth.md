# Authentication

`pystorytv` handles authentication via OTPLess. You only need to verify your phone number once. The session is stored and reused.

## AuthManager

The `AuthManager` class orchestrates the OTP flow and session loading.

```python
from pystorytv import AuthManager

auth = AuthManager()

if not auth.is_logged_in():
    # 1. Request OTP
    auth.request_otp(mobile="9876543210", country_code="+91")
    
    # 2. Wait for user input
    otp = input("Enter OTP: ")
    
    # 3. Verify
    auth.verify_otp(mobile="9876543210", country_code="+91", otp=otp)
    print("Logged in successfully!")

# The session token is available at `auth.session`
```

### Methods

#### `request_otp(mobile: str, country_code: str)`
Sends a 4-digit OTP to the given mobile number.

#### `verify_otp(mobile: str, country_code: str, otp: str)`
Validates the OTP. If successful, creates a `Session` and persists it securely to the system's keyring and platform-specific app data directory.

#### `is_logged_in() -> bool`
Returns `True` if a valid session exists on disk.
