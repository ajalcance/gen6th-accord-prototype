"""Request authentication → a Principal that the audit spine records as the event actor."""

from .principal import ANONYMOUS, Principal, get_principal, require_user

__all__ = ["ANONYMOUS", "Principal", "get_principal", "require_user"]
