from dataclasses import dataclass
from typing import Optional
from aiohttp import ClientTimeout


@dataclass
class TimeoutRules:
    total: Optional[float]
    connect: Optional[float]
    sock_read: Optional[float]
    sock_connect: Optional[float]

    def _to_aiohttp(self) -> ClientTimeout:
        return ClientTimeout(
            self.total, self.connect, self.sock_read, self.sock_connect
        )


def get_default_timeout() -> TimeoutRules:
    return TimeoutRules(
        30.0,
        10.0,
        10.0,
        10.0,
    )
