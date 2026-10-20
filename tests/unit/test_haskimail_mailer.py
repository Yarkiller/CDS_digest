"""HaskimailMailer — HTTP digest delivery behind the ``Mailer`` port (MAIL-01/04/05, ADR-0005).

All coverage uses an injected session double: these tests never open a socket and never
call the real API. The API token, base URL and channel arrive as ready primitives from
``Settings``; the adapter never reads ``os.environ`` (MAIL-05).

ADR-0005: the digest is delivered through the Haskimail HTTP API instead of a corporate
SMTP relay. The port contract is unchanged — only the adapter behind it.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

import pytest
from haskimail import (
    ApiInputError,
    HaskimailError,
    InactiveRecipientsError,
    InvalidAPIKeyError,
    RateLimitExceededError,
    ServerClient,
    ServiceUnavailableError,
)

import backend
from backend.composition.config_error import ConfigurationError
from backend.composition.mailer_factory import resolve_mailer
from backend.composition.settings import Settings
from backend.domain.errors import MailDeliveryError
from backend.domain.recipient import Recipient
from backend.infrastructure.haskimail_mailer import (
    DEFAULT_HASKIMAIL_API_URL,
    HASKIMAIL_SEND_PATH,
    HaskimailMailer,
    HaskimailResponse,
    _default_session_factory,
)
from backend.infrastructure.stub_mailer import StubMailer

ISSUE_URL = "/issues/7"
BODY_TEXT = f"Новый выпуск Digest CDS.\nЧитать: {ISSUE_URL}"
BODY_HTML = "<p>Новый выпуск Digest CDS</p>"
API_KEY = "server-token-do-not-leak"


class FakeHaskimailSession:
    """Scripted session double: one outcome per ``send`` attempt."""

    def __init__(self, outcomes: Sequence[Exception | HaskimailResponse | None] = ()) -> None:
        self._outcomes = list(outcomes)
        self.attempts: list[dict[str, object]] = []
        self.closed = False

    def send(self, payload: dict[str, object]) -> HaskimailResponse:
        index = len(self.attempts)
        self.attempts.append(payload)
        outcome = self._outcomes[index] if index < len(self._outcomes) else None
        if isinstance(outcome, Exception):
            raise outcome
        if outcome is not None:
            return outcome
        return HaskimailResponse(status_code=200, message_id=f"msg-{index}", error_code=0)

    def close(self) -> None:
        self.closed = True


class FakeSessionFactory:
    """Records factory calls and returns a scripted session (or raises on open)."""

    def __init__(
        self,
        session: FakeHaskimailSession | None = None,
        *,
        error: Exception | None = None,
    ) -> None:
        self.session = session if session is not None else FakeHaskimailSession()
        self.error = error
        self.calls: list[tuple[str, float, str]] = []

    def __call__(self, *, api_url: str, api_key: str, timeout: float):
        self.calls.append((api_url, timeout, api_key))
        if self.error is not None:
            raise self.error
        return self.session


def _recipients(count: int) -> list[Recipient]:
    return [
        Recipient(email=f"user{i}@sberbank.ru", display_name=f"User {i}")
        for i in range(1, count + 1)
    ]


def _mailer(factory: FakeSessionFactory, **overrides: object) -> HaskimailMailer:
    kwargs: dict[str, object] = {
        "api_key": API_KEY,
        "api_url": DEFAULT_HASKIMAIL_API_URL,
        "from_addr": "digest@knowledge-db.ru",
        "from_name": "Digest CDS",
        "message_stream": "outbound",
        "request_timeout": 30.0,
        "session_factory": factory,
    }
    kwargs.update(overrides)
    return HaskimailMailer(**kwargs)  # type: ignore[arg-type]


def _send(mailer: HaskimailMailer, recipients: Sequence[Recipient], **overrides: object):
    kwargs: dict[str, object] = {
        "batch_id": 42,
        "issue_url": ISSUE_URL,
        "subject": "Digest CDS — выпуск 7",
        "body_text": BODY_TEXT,
        "recipient_count": len(recipients),
        "recipients": list(recipients),
    }
    kwargs.update(overrides)
    return mailer.send_digest(**kwargs)  # type: ignore[arg-type]


# --- D-05 / D-07: honest per-recipient delivery -------------------------------------


def test_haskimail_mailer_sends_one_request_per_recipient() -> None:
    """D-05: N requests for N recipients, each with exactly one ``To`` and no Cc/Bcc."""
    recipients = _recipients(3)
    factory = FakeSessionFactory()
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "sent"
    assert result["recipient_count"] == 3
    assert result["delivered_count"] == 3
    assert result["issue_url"] == ISSUE_URL
    assert "stop_reason" not in result
    assert len(factory.session.attempts) == 3
    for payload, recipient in zip(factory.session.attempts, recipients, strict=True):
        assert payload["To"] == recipient.email
        assert "Cc" not in payload
        assert "Bcc" not in payload
        assert payload["Subject"] == "Digest CDS — выпуск 7"
        assert payload["From"] == "Digest CDS <digest@knowledge-db.ru>"
        assert ISSUE_URL in str(payload["TextBody"])


def test_haskimail_mailer_attaches_html_body_and_message_stream_when_configured() -> None:
    factory = FakeSessionFactory()
    mailer = _mailer(factory)

    _send(mailer, _recipients(1), body_html=BODY_HTML)

    payload = factory.session.attempts[0]
    assert payload["HtmlBody"] == BODY_HTML
    assert payload["MessageStream"] == "outbound"


def test_haskimail_mailer_omits_html_and_stream_when_not_configured() -> None:
    """Optional keys stay out of the payload so the API defaults apply."""
    factory = FakeSessionFactory()
    mailer = _mailer(factory, message_stream="")

    _send(mailer, _recipients(1))

    payload = factory.session.attempts[0]
    assert "HtmlBody" not in payload
    assert "MessageStream" not in payload


def test_haskimail_mailer_uses_bare_address_when_from_name_is_absent() -> None:
    factory = FakeSessionFactory()
    mailer = _mailer(factory, from_name="")

    _send(mailer, _recipients(1))

    assert factory.session.attempts[0]["From"] == "digest@knowledge-db.ru"


def test_haskimail_mailer_zero_recipients_reports_sent_with_zero_delivered() -> None:
    """D-04 / RESEARCH Q3: an empty live audience is honestly ``sent`` with N=0."""
    factory = FakeSessionFactory()
    mailer = _mailer(factory)

    result = _send(mailer, [], recipient_count=0)

    assert result["delivery_status"] == "sent"
    assert result["delivered_count"] == 0
    assert factory.calls == []
    assert factory.session.attempts == []


def test_haskimail_mailer_partial_when_some_recipients_fail() -> None:
    """D-07: 0 < N < M → partial; sending continues past a lone failure."""
    recipients = _recipients(3)
    factory = FakeSessionFactory(
        FakeHaskimailSession(
            [
                HaskimailResponse(status_code=500, error_code=500, error_message="boom"),
                None,
                None,
            ]
        )
    )
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "partial"
    assert result["delivered_count"] == 2
    assert result["recipient_count"] == 3
    assert "stop_reason" not in result
    assert len(factory.session.attempts) == 3


def test_haskimail_mailer_failed_when_all_recipients_fail() -> None:
    recipients = _recipients(2)
    factory = FakeSessionFactory(
        FakeHaskimailSession(
            [
                HaskimailResponse(status_code=500, error_code=500, error_message="boom"),
                HaskimailResponse(status_code=500, error_code=500, error_message="boom"),
            ]
        )
    )
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "failed"
    assert result["delivered_count"] == 0
    assert "stop_reason" not in result


def test_haskimail_mailer_treats_non_zero_error_code_as_failure() -> None:
    """A 200 body carrying a non-zero ``ErrorCode`` is a failure, never a delivery."""
    factory = FakeSessionFactory(
        FakeHaskimailSession(
            [HaskimailResponse(status_code=200, error_code=300, error_message="bad address")]
        )
    )
    mailer = _mailer(factory)

    result = _send(mailer, _recipients(1))

    assert result["delivery_status"] == "failed"
    assert result["delivered_count"] == 0


@pytest.mark.parametrize("status_code", [400, 401, 422, 429, 500, 503])
def test_haskimail_mailer_treats_every_http_error_status_as_failure(status_code: int) -> None:
    factory = FakeSessionFactory(
        FakeHaskimailSession([HaskimailResponse(status_code=status_code)])
    )
    mailer = _mailer(factory)

    result = _send(mailer, _recipients(1))

    assert result["delivery_status"] == "failed"


# --- MAIL-04: SDK exceptions are counted per recipient, never escaping ----------------


@pytest.mark.parametrize(
    "error",
    [
        InvalidAPIKeyError(message="unauthorized", status_code=401),
        ApiInputError(message="bad payload", status_code=422),
        InactiveRecipientsError(recipients=["gone@sberbank.ru"], message="inactive"),
        RateLimitExceededError(message="slow down", status_code=429),
        ServiceUnavailableError(message="maintenance", status_code=503),
        HaskimailError("sdk blew up"),
    ],
)
def test_haskimail_mailer_counts_sdk_error_as_one_failed_recipient(
    error: HaskimailError,
) -> None:
    """Every SDK error is ONE failed recipient: the loop continues and nothing escapes."""
    factory = FakeSessionFactory(FakeHaskimailSession([error, None]))
    mailer = _mailer(factory)

    result = _send(mailer, _recipients(2))

    assert result["delivery_status"] == "partial"
    assert result["delivered_count"] == 1
    assert len(factory.session.attempts) == 2


def test_haskimail_mailer_counts_network_error_as_one_failure_without_escaping() -> None:
    """``requests`` network failures surface as ``OSError`` — counted, never escaping."""
    factory = FakeSessionFactory(
        FakeHaskimailSession([OSError("connection reset"), None])
    )
    mailer = _mailer(factory)

    result = _send(mailer, _recipients(2))

    assert result["delivery_status"] == "partial"
    assert result["delivered_count"] == 1
    assert len(factory.session.attempts) == 2


def test_haskimail_mailer_counts_timeout_as_one_failure_without_escaping() -> None:
    factory = FakeSessionFactory(FakeHaskimailSession([TimeoutError("read timed out")]))
    mailer = _mailer(factory)

    result = _send(mailer, _recipients(1))

    assert result["delivery_status"] == "failed"


def test_haskimail_mailer_rejects_control_characters_in_recipient() -> None:
    """CR-01 analogue: a malformed address is ONE failed recipient and never hits the wire."""
    recipients = [Recipient(email="victim@x.ru\r\nBcc: attacker@y.ru")]
    factory = FakeSessionFactory()
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert result["delivery_status"] == "failed"
    assert result["delivered_count"] == 0
    assert factory.session.attempts == []


# --- D-08: consecutive-failure stop with streak reset --------------------------------


def test_haskimail_mailer_stops_after_three_consecutive_failures() -> None:
    """D-08: three consecutive failures stop the loop — remaining recipients untouched."""
    recipients = _recipients(5)
    failure = HaskimailResponse(status_code=503, error_code=503, error_message="unavailable")
    factory = FakeSessionFactory(FakeHaskimailSession([failure, failure, failure]))
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert len(factory.session.attempts) == 3
    assert result["delivered_count"] == 0
    assert result["delivery_status"] == "failed"
    assert result["stop_reason"] == "consecutive_failures"


def test_haskimail_mailer_streak_reset_on_success_continues_sending() -> None:
    """A success resets the streak, so two fails + success continue sending."""
    recipients = _recipients(4)
    failure = HaskimailResponse(status_code=500, error_code=500, error_message="boom")
    factory = FakeSessionFactory(FakeHaskimailSession([failure, None, failure, None]))
    mailer = _mailer(factory)

    result = _send(mailer, recipients)

    assert len(factory.session.attempts) == 4
    assert result["delivered_count"] == 2
    assert result["delivery_status"] == "partial"
    assert "stop_reason" not in result


def test_haskimail_mailer_closes_the_session_after_a_run() -> None:
    """The SDK session is always released, including after a stop."""
    factory = FakeSessionFactory()
    mailer = _mailer(factory)

    _send(mailer, _recipients(2))

    assert factory.session.closed is True


def test_haskimail_mailer_closes_the_session_after_a_stopped_run() -> None:
    failure = HaskimailResponse(status_code=503, error_code=503, error_message="unavailable")
    factory = FakeSessionFactory(FakeHaskimailSession([failure, failure, failure]))
    mailer = _mailer(factory)

    _send(mailer, _recipients(5))

    assert factory.session.closed is True


@pytest.mark.parametrize("error", [HaskimailError("bad token"), OSError("dns failure")])
def test_haskimail_mailer_session_open_failure_maps_to_mail_delivery_error(
    error: Exception,
) -> None:
    """MAIL-04: a setup failure raises the domain error so the use case can contain it."""
    factory = FakeSessionFactory(error=error)
    mailer = _mailer(factory)

    with pytest.raises(MailDeliveryError):
        _send(mailer, _recipients(1))


# --- the official SDK is the transport -----------------------------------------------


def test_default_session_factory_builds_the_official_sdk_client() -> None:
    """ADR-0005: the live transport is the ``haskimail`` SDK, not a hand-rolled client."""
    session = _default_session_factory(
        api_url=DEFAULT_HASKIMAIL_API_URL,
        api_key=API_KEY,
        timeout=30.0,
    )

    try:
        assert isinstance(session._client, ServerClient)
    finally:
        session.close()


def test_default_api_url_and_send_path_match_the_api_contract() -> None:
    """The SDK posts to ``{base_url}/email`` — the base URL carries no path."""
    assert DEFAULT_HASKIMAIL_API_URL == "https://api.haskimail.ru"
    assert HASKIMAIL_SEND_PATH == "/email"


# --- MAIL-05: secret handling + environment boundary ---------------------------------


def test_haskimail_mailer_passes_token_to_the_session_not_the_payload() -> None:
    """The API key travels in the SDK client, never inside a request body."""
    factory = FakeSessionFactory()
    mailer = _mailer(factory)

    _send(mailer, _recipients(1))

    assert factory.calls == [(DEFAULT_HASKIMAIL_API_URL, 30.0, API_KEY)]
    assert API_KEY not in repr(factory.session.attempts[0])


def test_haskimail_mailer_logs_never_contain_the_api_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    failure = HaskimailResponse(status_code=401, error_code=401, error_message="unauthorized")
    factory = FakeSessionFactory(FakeHaskimailSession([failure, failure]))
    mailer = _mailer(factory)

    with caplog.at_level(logging.DEBUG):
        _send(mailer, _recipients(2))

    assert API_KEY not in caplog.text


def test_haskimail_mailer_never_reads_process_environment() -> None:
    """MAIL-05: the adapter receives primitives only — no env reads in the module source."""
    source = Path(__file__).resolve().parents[2].joinpath(
        "backend/src/backend/infrastructure/haskimail_mailer.py"
    ).read_text(encoding="utf-8")

    assert "os.environ" not in source
    assert "getenv" not in source
    assert "import os" not in source


@pytest.mark.parametrize(
    "forbidden",
    ["import haskimail", "from haskimail", "import requests", "from requests", "import httpx"],
)
def test_transport_libraries_stay_out_of_domain_and_application(forbidden: str) -> None:
    """MAIL-04 analogue: use cases and domain must never import a transport library."""
    package_root = Path(backend.__file__).resolve().parent
    guarded = [package_root / "domain", package_root / "application"]
    offenders: list[str] = []
    for directory in guarded:
        for path in directory.rglob("*.py"):
            if forbidden in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(package_root)))

    assert offenders == []


# --- composition: MAILER=haskimail selection + fail-fast -----------------------------


def _haskimail_settings(**overrides: object) -> Settings:
    complete: dict[str, object] = {
        "mailer": "haskimail",
        "haskimail_api_key": API_KEY,
        "haskimail_from": "digest@knowledge-db.ru",
    }
    complete.update(overrides)
    return Settings(**complete)  # type: ignore[arg-type]


def test_resolve_mailer_haskimail_with_complete_settings_builds_haskimail_mailer() -> None:
    mailer = resolve_mailer(_haskimail_settings())

    assert isinstance(mailer, HaskimailMailer)
    assert not isinstance(mailer, StubMailer)


@pytest.mark.parametrize(
    ("missing_field", "blank"),
    [("haskimail_api_key", ""), ("haskimail_from", "")],
)
def test_resolve_mailer_haskimail_requires_each_field(
    missing_field: str, blank: object
) -> None:
    """D-16 analogue: API_KEY and FROM are both required for live HTTP delivery."""
    with pytest.raises(ConfigurationError):
        resolve_mailer(_haskimail_settings(**{missing_field: blank}))


def test_resolve_mailer_haskimail_never_silently_returns_stub() -> None:
    """D-16 honesty tripwire: a misconfigured haskimail mode must not produce a StubMailer."""
    settings = Settings(mailer="haskimail", haskimail_api_key=API_KEY)

    with pytest.raises(ConfigurationError):
        resolve_mailer(settings)


def test_resolve_mailer_haskimail_rejects_non_https_endpoint() -> None:
    """MAIL-05: the server token must never travel over plaintext HTTP."""
    with pytest.raises(ConfigurationError, match="HASKIMAIL_API_URL"):
        resolve_mailer(_haskimail_settings(haskimail_api_url="http://api.haskimail.ru"))


def test_resolve_mailer_haskimail_forwards_the_configured_base_url() -> None:
    mailer = resolve_mailer(
        _haskimail_settings(haskimail_api_url="https://api.haskimail.ru")
    )

    assert isinstance(mailer, HaskimailMailer)
    assert mailer.api_url == "https://api.haskimail.ru"


def test_resolve_mailer_rejects_unknown_mode_listing_all_three() -> None:
    with pytest.raises(ConfigurationError, match="haskimail"):
        resolve_mailer(Settings(mailer="sendmail"))


def test_settings_from_env_reads_haskimail_fields() -> None:
    settings = Settings.from_env(
        {
            "MAILER": "haskimail",
            "HASKIMAIL_API_KEY": API_KEY,
            "HASKIMAIL_API_URL": "https://api.haskimail.ru",
            "HASKIMAIL_FROM": "digest@knowledge-db.ru",
            "HASKIMAIL_FROM_NAME": "Digest CDS",
            "HASKIMAIL_MESSAGE_STREAM": "outbound",
        }
    )

    assert settings.mailer == "haskimail"
    assert settings.haskimail_api_key == API_KEY
    assert settings.haskimail_api_url == "https://api.haskimail.ru"
    assert settings.haskimail_from == "digest@knowledge-db.ru"
    assert settings.haskimail_from_name == "Digest CDS"
    assert settings.haskimail_message_stream == "outbound"


def test_settings_haskimail_fields_default_to_unset_when_env_absent() -> None:
    settings = Settings.from_env({})

    assert settings.haskimail_api_key == ""
    assert settings.haskimail_api_url == ""
    assert settings.haskimail_from == ""
    assert settings.haskimail_from_name == ""
    assert settings.haskimail_message_stream == ""


def test_settings_repr_never_leaks_the_haskimail_api_key() -> None:
    """A logged Settings must not disclose the server token."""
    settings = Settings(mailer="haskimail", haskimail_api_key="token-hunter2")

    assert "token-hunter2" not in repr(settings)


def test_settings_haskimail_timeout_is_not_env_driven() -> None:
    settings = Settings.from_env({"HASKIMAIL_REQUEST_TIMEOUT": "600"})

    assert settings.haskimail_request_timeout == 30.0
