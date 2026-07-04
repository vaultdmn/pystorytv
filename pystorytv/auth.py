"""OTPLess authentication flow for StoryTV.

The StoryTV app uses OTPLess (https://otpless.com) for phone-number OTP login.
This module re-implements the exact API calls observed in the network dump.

Flow:
  1. send_otp(phone)            → channelAuthToken, asId
  2. poll_otp_status(...)        → waits until COMPLETED
  3. client.verify_otpless(...)  → StoryTV JWT

The OTPLess app_id and merchant_id are hard-coded from the Android APK strings.
"""
from __future__ import annotations

import time
import uuid
from typing import Optional

import httpx
from rich.console import Console

# OTPLess constants extracted from the APK / network dump
OTPLESS_APP_ID = "L96360HUEYI16BJASDPE"
OTPLESS_MERCHANT_ID = "9e3ee600-195d-415d-8975-97610d33de47"
OTPLESS_BASE = "https://user-auth.otpless.app"

DEVICE_INFO = (
    '{"platform":"android","vendor":"OnePlus","browser":"",'
    '"connection":"","language":"en-US","cookieEnabled":"",'
    '"screenWidth":900,"screenHeight":1600,'
    '"userAgent":"Dalvik/2.1.0 (Linux; U; Android 9; A5010 Build/PI) otplesssdk",'
    '"timezoneOffset":330,"cpuArchitecture":"x86_64"}'
)

console = Console(stderr=True)


def _otpless_headers() -> dict[str, str]:
    return {
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": "okhttp/5.3.2",
        "Content-Type": "application/json; charset=utf-8",
    }


def send_otp(phone_e164: str) -> tuple[str, str]:
    """
    Initiate OTP send.

    Args:
        phone_e164: Phone number in E.164 format, e.g. "918874163264" (no +)

    Returns:
        (channelAuthToken, asId) needed for polling
    """
    ts_id = f"{uuid.uuid4()}-{int(time.time() * 1000)}"
    in_id = f"{uuid.uuid4()}-{int(time.time() * 1000) - 100000}"
    uid = uuid.uuid4().hex.upper()

    payload = {
        "channel": "OTP",
        "identifierType": "MOBILE",
        "mobile": phone_e164,
        "selectedCountryCode": f"+{phone_e164[:2]}",
        "silentAuthEnabled": False,
        "triggerWebauthn": False,
        "type": "INPUT",
        "uid": uid,
        "value": "",
        "origin": "https://otpless.com",
        "version": "V4",
        "tsId": ts_id,
        "inId": in_id,
        "deviceInfo": DEVICE_INFO,
        "loginUri": f"otpless.{OTPLESS_APP_ID.lower()}://otpless",
        "appId": OTPLESS_APP_ID,
        "isHeadless": True,
        "packageName": "story.tv.drama.reels",
        "package": "story.tv.drama.reels",
        "platform": "HEADLESS",
        "hasWhatsapp": "false",
        "fireIntent": True,
        "clientMetaData": "{}",
        "deviceLockCapability": 7,
    }

    with httpx.Client(timeout=20, verify=False) as http:
        r = http.post(
            f"{OTPLESS_BASE}/v3/lp/user/transaction/intent/{OTPLESS_MERCHANT_ID}",
            json=payload,
            headers=_otpless_headers(),
        )
    r.raise_for_status()
    j = r.json()
    ql = j.get("quantumLeap", {})
    token = ql.get("channelAuthToken", "")
    as_id = ql.get("asId", "")
    if not token:
        raise RuntimeError(f"OTP send failed: {j}")
    return token, as_id

def send_otp_full(phone_e164: str) -> tuple[str, str, str, str, str, dict]:
    """Like send_otp, but returns state needed for manual verify."""
    ts_id = f"{uuid.uuid4()}-{int(time.time() * 1000)}"
    in_id = f"{uuid.uuid4()}-{int(time.time() * 1000) - 100000}"
    uid = uuid.uuid4().hex.upper()

    payload = {
        "channel": "OTP",
        "identifierType": "MOBILE",
        "mobile": phone_e164,
        "selectedCountryCode": f"+{phone_e164[:2]}",
        "silentAuthEnabled": False,
        "triggerWebauthn": False,
        "type": "INPUT",
        "uid": uid,
        "value": "",
        "origin": "https://otpless.com",
        "version": "V4",
        "tsId": ts_id,
        "inId": in_id,
        "deviceInfo": DEVICE_INFO,
        "loginUri": f"otpless.{OTPLESS_APP_ID.lower()}://otpless",
        "appId": OTPLESS_APP_ID,
        "isHeadless": True,
        "packageName": "story.tv.drama.reels",
        "package": "story.tv.drama.reels",
        "platform": "HEADLESS",
        "hasWhatsapp": "false",
        "fireIntent": True,
        "clientMetaData": "{}",
        "deviceLockCapability": 7,
    }

    with httpx.Client(timeout=20, verify=False) as http:
        r = http.post(
            f"{OTPLESS_BASE}/v3/lp/user/transaction/intent/{OTPLESS_MERCHANT_ID}",
            json=payload,
            headers=_otpless_headers(),
        )
    r.raise_for_status()
    j = r.json()
    ql = j.get("quantumLeap", {})
    token = ql.get("channelAuthToken", "")
    as_id = ql.get("asId", "")
    if not token:
        raise RuntimeError(f"OTP send failed: {j}")
    return token, as_id, uid, ts_id, in_id, payload

def verify_otp_full(state: dict, otp: str) -> tuple[str, str]:
    """Manually submit the OTP using the correct endpoint."""
    payload = dict(state["payload"])
    
    # Extract phone from payload
    mobile = payload.get("mobile", "")
    country_code = payload.get("selectedCountryCode", "+91").replace("+", "")
    
    verify_payload = {
        "selectedCountryCode": country_code,
        "mobile": mobile,
        "otp": otp,
        "value": f"{country_code}{mobile}",
        "isOTPAutoRead": "false",
        "uid": state["uid"],
        "token": state["token"],
        "asId": state["as_id"],
        "origin": payload.get("origin"),
        "version": payload.get("version"),
        "tsId": state["ts_id"],
        "inId": state["in_id"],
        "deviceInfo": payload.get("deviceInfo"),
        "loginUri": payload.get("loginUri"),
        "appId": payload.get("appId"),
        "isHeadless": True,
        "packageName": payload.get("packageName"),
        "package": payload.get("package"),
        "otpHash": "3dk7tmKkMxc",
        "platform": "HEADLESS"
    }
    
    with httpx.Client(timeout=20, verify=False) as http:
        r = http.post(
            f"{OTPLESS_BASE}/v3/lp/user/transaction/otp/{OTPLESS_MERCHANT_ID}",
            json=verify_payload,
            headers=_otpless_headers(),
        )
        r.raise_for_status()
        j = r.json()
        
    one_tap = j.get("oneTap", {})
    if one_tap.get("status") == "SUCCESS":
        return one_tap.get("token"), one_tap.get("merchantUserInfo", {}).get("idToken")
        
    raise RuntimeError(f"Failed to verify OTP: {j}")


def poll_otp_status(
    channel_auth_token: str,
    as_id: str,
    *,
    max_wait: int = 120,
    poll_interval: float = 3.0,
) -> tuple[str, str]:
    """
    Poll until OTP is verified (status COMPLETED).

    Returns:
        (otpless_token, id_token) to pass to StoryTVClient.verify_otpless()

    Raises:
        TimeoutError if max_wait seconds elapse without completion.
    """
    params = {
        "origin": "https://otpless.com",
        "version": "V3",
        "isHeadless": "true",
        "platform": "android",
        "appId": OTPLESS_APP_ID,
        "token": channel_auth_token,
        "asId": as_id,
        "packageName": "story.tv.drama.reels",
        "package": "story.tv.drama.reels",
        "deviceInfo": DEVICE_INFO,
    }

    deadline = time.time() + max_wait
    with httpx.Client(timeout=20, verify=False) as http:
        while time.time() < deadline:
            r = http.get(
                f"{OTPLESS_BASE}/v3/lp/user/transaction/status/{OTPLESS_MERCHANT_ID}",
                params=params,
                headers=_otpless_headers(),
            )
            r.raise_for_status()
            j = r.json()
            detail = j.get("authDetail") or {}
            status = detail.get("status", "PENDING")
            if status == "COMPLETED":
                token = detail.get("token", "")
                id_token = detail.get("idToken", "")
                return token, id_token
            if status not in ("PENDING", "INITIATED"):
                raise RuntimeError(f"OTP status unexpected: {status}")
            time.sleep(poll_interval)

    raise TimeoutError("OTP verification timed out after waiting for user input.")


def interactive_login(console: Optional["Console"] = None) -> tuple[str, str]:
    """
    Full interactive login flow for use in TUI/CLI.

    Prompts for phone number and waits for user to enter OTP in the app/SMS.
    Returns (otpless_token, id_token).
    """
    from rich.console import Console as RichConsole
    from rich.prompt import Prompt

    c = console or RichConsole(stderr=True)

    c.print("[bold cyan]StoryTV Login[/]")
    c.print("Enter your mobile number (with country code, e.g. 919876543210):")
    phone = Prompt.ask("[yellow]Phone").strip().lstrip("+")

    c.print(f"[dim]Sending OTP to +{phone}...[/dim]")
    try:
        token, as_id, uid, ts_id, in_id, payload = send_otp_full(phone)
        state = {
            "token": token,
            "as_id": as_id,
            "uid": uid,
            "ts_id": ts_id,
            "in_id": in_id,
            "payload": payload
        }
        c.print("[green]✓ OTP sent![/] [dim]Check your SMS / WhatsApp[/dim]")
        
        otp = Prompt.ask("[yellow]Enter OTP (or type 'cancel' to abort)[/yellow]").strip()
        if otp.lower() == 'cancel':
            raise Exception("Cancelled")
            
        c.print("[dim]Verifying OTP...[/dim]")
        otpless_token, id_token = verify_otp_full(state, otp)
        c.print("[green]✓ OTP verified![/]")
        return otpless_token, id_token
    except Exception as e:
        c.print(f"[red]OTP flow failed:[/] {e}")
        c.print("[yellow]Alternative: Login using your StoryTV JWT directly.[/yellow]")
        jwt = Prompt.ask("[cyan]Enter StoryTV JWT[/cyan]").strip()
        if jwt:
            return "JWT_DIRECT", jwt
        raise e
