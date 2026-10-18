"""``is_usable_email`` hardening — malformed addresses never reach the SMTP adapter (D-02).

A CR/LF address passes a naive ``@``-only check but makes ``EmailMessage`` raise a
``ValueError`` during ``_build_message``, which used to escape ``SmtpMailer`` and 500 an
already-published digest (CR-01 / D-88). The audience predicate must reject header/control
characters, surrounding and embedded whitespace, commas, and multi-``@`` addresses so such
rows are excluded and logged at the boundary (D-02) instead of reaching the transport.
"""

from __future__ import annotations

import pytest

from backend.domain.recipient import is_usable_email


@pytest.mark.parametrize(
    "email",
    [
        "victim@x.ru\r\nBcc: attacker@y.ru",  # CR/LF header injection
        "victim@x.ru\n",
        "victim@x.ru\r",
        "victim@x.ru\t",  # embedded control char
        "victim@x.ru ",
        " victim@x.ru",  # surrounding whitespace
        "vic tim@x.ru",  # embedded whitespace
        "a@b.ru, c@d.ru",  # comma → the stdlib would emit two To addresses (D-05)
        "a@b@c.ru",  # more than one @
        "user@ex\x00ample.ru",  # NUL control char
        "",
        "not-an-email",
        "@nodomain",
        "user@",
    ],
)
def test_is_usable_email_rejects_malformed_or_unsafe_addresses(email: str) -> None:
    assert is_usable_email(email) is False


@pytest.mark.parametrize(
    "email",
    [
        "admin@sberbank.ru",
        "a.b+tag@omega.sbrf.ru",
        "user_name@knowledge-db.ru",
    ],
)
def test_is_usable_email_accepts_well_formed_addresses(email: str) -> None:
    assert is_usable_email(email) is True
