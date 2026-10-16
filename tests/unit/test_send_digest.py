"""send_digest — publish-on-send, draft/empty/already-sent gates (ADMIN-03/07/08, D-85…D-90)."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from backend.application.use_cases.send_digest import send_digest
from backend.domain.current_user import CurrentUser
from backend.domain.errors import (
    AlreadySentError,
    DraftInSendPoolError,
    EmptySendPoolError,
    InvalidSendOrderError,
    MailDeliveryError,
    PersistenceError,
)
from backend.domain.recipient import Recipient
from backend.domain.shortlist import ShortlistBatch, ShortlistItem
from backend.infrastructure.stub_mailer import StubMailer
from backend.tests_support.in_memory import (
    InMemoryDigestPublisher,
    InMemoryIssueRepository,
    InMemoryPingRecorder,
    InMemoryProfileRepository,
    InMemoryShortlistRepository,
)


def _item(
    *,
    material_id: int,
    rank: int = 1,
    title: str = "Ready approved",
    material_status: str = "ready",
    decision: str = "approved",
    dek: str | None = None,
    slug: str | None = None,
) -> ShortlistItem:
    return ShortlistItem(
        material_id=material_id,
        rank=rank,
        title=title,
        material_status=material_status,
        decision=decision,
        score=0.9,
        score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
        dek=dek,
        slug=slug,
    )


def _batch(*items: ShortlistItem, sent_at: datetime | None = None) -> ShortlistBatch:
    return ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=sent_at,
        items=items,
    )


def _publisher(
    shortlist: InMemoryShortlistRepository,
    issues: InMemoryIssueRepository,
) -> InMemoryDigestPublisher:
    """Atomic claim+publish backed by the same in-memory repos the assertions inspect."""
    return InMemoryDigestPublisher(lambda: shortlist, lambda: issues)


def _profiles(*entries: tuple[str, str]) -> InMemoryProfileRepository:
    """In-memory profiles seeded with (email, role) rows — D-01 includes every role."""
    repo = InMemoryProfileRepository()
    for index, (email, role) in enumerate(entries, start=1):
        repo._by_id[f"user-{index}"] = CurrentUser(
            id=f"user-{index}", email=email, role=role, display_name=None
        )
    return repo


class _RecordingPublisher(InMemoryDigestPublisher):
    """InMemoryDigestPublisher that captures the claim kwargs (planned M at claim, D-06)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.claim_kwargs: dict = {}

    def claim_and_publish(self, **kwargs):  # type: ignore[override]
        self.claim_kwargs = dict(kwargs)
        return super().claim_and_publish(**kwargs)


class _StatusMailer:
    """Fake Mailer returning a fixed delivery dict (D-07 live statuses; SmtpMailer stand-in)."""

    def __init__(self, *, delivery_status: str, delivered_count: int) -> None:
        self.delivery_status = delivery_status
        self.delivered_count = delivered_count
        self.last_recipients: tuple[Recipient, ...] = ()
        self.last_recipient_count: int | None = None

    def send_digest(
        self,
        *,
        batch_id: int,
        issue_url: str,
        subject: str,
        body_text: str,
        recipient_count: int,
        recipients: tuple[Recipient, ...] = (),
        body_html: str | None = None,
    ) -> dict[str, object]:
        self.last_recipients = tuple(recipients)
        self.last_recipient_count = recipient_count
        return {
            "delivery_status": self.delivery_status,
            "recipient_count": recipient_count,
            "delivered_count": self.delivered_count,
            "issue_url": issue_url,
        }


class _MailFailingMailer(StubMailer):
    """Mailer that raises a domain mail error after publish (MAIL-04 / D-88 probe)."""

    def send_digest(self, **kwargs):  # type: ignore[override]
        raise MailDeliveryError("smtp delivery failed (simulated)")


class _FailingIssueRepository(InMemoryIssueRepository):
    """IssueRepository whose publish always fails (CR-01 atomicity probe)."""

    def publish(self, *args, **kwargs):  # type: ignore[override]
        raise PersistenceError("digest_issues publish failed (simulated)")


class _FailingPingRecorder(InMemoryPingRecorder):
    """PingRecorder that always fails after publish (CR-02 false-failure probe)."""

    def record(self, *args, **kwargs):  # type: ignore[override]
        raise PersistenceError("ping audit failed (simulated)")


def test_in_memory_get_current_batch_hides_sent_and_latest_exposes_it() -> None:
    """WR-03: in-memory must match the live `sent_at IS NULL` contract for get_current_batch;
    get_latest_batch still exposes the sent batch (used for the D-89 already-sent signal)."""
    now = datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc)
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))

    # Before claim: current batch is the unsent one.
    assert shortlist.get_current_batch() is not None

    shortlist.claim_sent(batch_id=42, sent_at=now)

    # After claim: current batch is hidden (sent_at set), but latest still exposes it.
    assert shortlist.get_current_batch() is None
    latest = shortlist.get_latest_batch()
    assert latest is not None
    assert latest.id == 42
    assert latest.sent_at == now


def test_send_happy_path_publishes_issue_claims_sent_and_stubs_mail() -> None:
    """ADMIN-07/08 / D-88/D-90: publish + claim + stub body with /issues/{n}."""
    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(material_id=101, rank=1, title="RAG в продакшене"),
            _item(
                material_id=102,
                rank=2,
                title="Rejected ready",
                decision="rejected",
            ),
        )
    )
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()
    actor = "admin-uuid-1"
    now = datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc)

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        pings,
        _profiles(),
        actor_user_id=actor,
        now=now,
    )

    assert result.issue_number >= 1
    assert result.issue_url == f"/issues/{result.issue_number}"
    assert result.delivery_status == "stubbed"
    assert result.message == "Выпуск опубликован. Доставка писем: stub (0 из 0)"
    assert result.delivered_count == 0

    # WR-03: the claimed batch leaves the unsent pool (matches live `sent_at IS NULL`);
    # get_latest_batch still exposes it with the stamped sent_at.
    assert shortlist.get_current_batch() is None
    latest = shortlist.get_latest_batch()
    assert latest is not None
    assert latest.sent_at == now

    published = issues.get_by_number(result.issue_number)
    assert published is not None
    assert published.published_at == now
    assert len(published.items) == 1
    assert published.items[0].title == "RAG в продакшене"

    assert mailer.last_body_text is not None
    assert f"/issues/{result.issue_number}" in mailer.last_body_text
    assert pings.entries
    audit = pings.entries[-1]
    assert audit.user_id == actor
    assert audit.kind == "digest_send"
    assert audit.payload.get("action") == "send"
    assert audit.payload.get("batch_id") == 42
    assert audit.payload.get("delivery_status") == "stubbed"


def test_send_resolves_audience_from_profiles_and_reports_stub_honesty() -> None:
    """MAIL-01/MAIL-03 (D-01/D-02/D-06/D-12): M = usable profiles emails; planned M stamped."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()
    publisher = _RecordingPublisher(lambda: shortlist, lambda: issues)
    profiles = _profiles(
        ("admin@sberbank.ru", "admin"),          # D-01: admins are not excluded
        ("employee@sberbank.ru", "employee"),     # D-01: every usable profile email
        ("not-an-email", "employee"),             # D-02: malformed → excluded from M
        ("", "employee"),                         # D-02: empty → excluded from M
    )

    result = send_digest(
        shortlist,
        publisher,
        mailer,
        pings,
        profiles,
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )

    # M is the usable audience, not every profile row (D-02).
    assert result.recipient_count == 2
    assert result.delivered_count == 0
    assert result.delivery_status == "stubbed"
    assert result.message == "Выпуск опубликован. Доставка писем: stub (0 из 2)"

    # Planned M is stamped at claim (D-06 option i) and echoed by the stub mailer.
    assert publisher.claim_kwargs.get("recipient_count") == 2
    assert mailer.last_recipient_count == 2
    assert len(mailer.last_recipients) == 2

    # ping payload carries the honesty triplet (D-06).
    ping = pings.entries[-1]
    assert ping.payload.get("recipient_count") == 2
    assert ping.payload.get("delivered_count") == 0
    assert ping.payload.get("delivery_status") == "stubbed"


def test_send_with_empty_audience_still_publishes_sent_status() -> None:
    """MAIL-01a (D-04 / RESEARCH Q3): M=0 still publishes; live path status is `sent`, N=0."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    mailer = _StatusMailer(delivery_status="sent", delivered_count=0)
    pings = InMemoryPingRecorder()
    # Only empty / malformed addresses → usable audience is empty (D-02).
    profiles = _profiles(("", "employee"), ("no-at", "employee"), ("@", "admin"))

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        pings,
        profiles,
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )

    assert result.recipient_count == 0
    assert result.delivered_count == 0
    assert result.delivery_status == "sent"
    assert result.message == "Выпуск опубликован. Получателей нет (0 из 0)"
    assert issues.get_by_number(result.issue_number) is not None


def _three_profiles() -> InMemoryProfileRepository:
    return _profiles(
        ("alpha@sberbank.ru", "employee"),
        ("beta@sberbank.ru", "employee"),
        ("gamma@sberbank.ru", "admin"),
    )


def test_send_live_sent_message_is_two_honest_sentences() -> None:
    """D-09/D-10: live `sent` (N=M>0) → two sentences «Доставлено N из M», never stub-Labelled."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    mailer = _StatusMailer(delivery_status="sent", delivered_count=3)

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        InMemoryPingRecorder(),
        _three_profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )

    assert result.delivery_status == "sent"
    assert result.recipient_count == 3
    assert result.delivered_count == 3
    assert result.message == "Выпуск опубликован. Доставлено 3 из 3"
    assert result.message.count(".") == 1
    assert "stub" not in result.message


def test_send_live_partial_message_reflects_planned_vs_delivered() -> None:
    """D-09/D-10: live `partial` (0<N<M) → two sentences with N из M, not stub copy."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    mailer = _StatusMailer(delivery_status="partial", delivered_count=1)

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        InMemoryPingRecorder(),
        _three_profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )

    assert result.delivery_status == "partial"
    assert result.recipient_count == 3
    assert result.delivered_count == 1
    assert result.message == "Выпуск опубликован. Доставлено 1 из 3 (частично)"
    assert result.message.count(".") == 1
    assert "stub" not in result.message


def test_send_live_failed_message_is_full_mail_fail_copy() -> None:
    """D-09/D-10: live `failed` (N=0, M>0) → two sentences «Письма не доставлены»."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    mailer = _StatusMailer(delivery_status="failed", delivered_count=0)

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        InMemoryPingRecorder(),
        _three_profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )

    assert result.delivery_status == "failed"
    assert result.recipient_count == 3
    assert result.delivered_count == 0
    assert result.message == "Выпуск опубликован. Письма не доставлены (0 из 3)"
    assert result.message.count(".") == 1
    assert "stub" not in result.message


def test_send_mail_failure_after_publish_still_returns_success() -> None:
    """MAIL-04 / D-88: MailDeliveryError after claim+publish must not fail the send."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    pings = InMemoryPingRecorder()
    profiles = _profiles(("employee@sberbank.ru", "employee"))

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        _MailFailingMailer(),
        pings,
        profiles,
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )

    assert result.recipient_count == 1
    assert result.delivered_count == 0
    assert result.delivery_status == "failed"
    assert result.message == "Выпуск опубликован. Письма не доставлены (0 из 1)"
    assert issues.get_by_number(result.issue_number) is not None
    ping = pings.entries[-1]
    assert ping.payload.get("delivery_status") == "failed"
    assert ping.payload.get("delivered_count") == 0


def test_send_blocks_approved_draft_in_pool() -> None:
    """ADMIN-03 / D-85: any approved draft → DraftInSendPoolError; not sent."""
    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(material_id=101, rank=1),
            _item(
                material_id=102,
                rank=2,
                title="Черновик",
                material_status="draft",
                decision="approved",
            ),
        )
    )
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()

    with pytest.raises(DraftInSendPoolError) as exc_info:
        send_digest(
            shortlist,
            _publisher(shortlist, issues),
            mailer,
            pings,
            _profiles(),
            actor_user_id="admin-uuid-1",
        )

    assert 102 in exc_info.value.draft_material_ids
    assert shortlist.get_current_batch().sent_at is None
    assert issues.get_latest_published() is None
    assert mailer.last_body_text is None
    assert pings.entries == []


def test_send_empty_approved_ready_raises() -> None:
    """ADMIN-07 empty probe: no approved∩ready → EmptySendPoolError."""
    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=101,
                decision="pending",
            ),
        )
    )
    issues = InMemoryIssueRepository()
    with pytest.raises(EmptySendPoolError):
        send_digest(
            shortlist,
            _publisher(shortlist, issues),
            StubMailer(),
            InMemoryPingRecorder(),
            _profiles(),
            actor_user_id="admin-uuid-1",
        )


def test_send_already_sent_raises_and_does_not_republish() -> None:
    """ADMIN-07 / D-89: second send → AlreadySentError; no second issue/mail."""
    sent_at = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    shortlist = InMemoryShortlistRepository(
        batch=_batch(_item(material_id=101), sent_at=sent_at)
    )
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()

    with pytest.raises(AlreadySentError):
        send_digest(
            shortlist,
            _publisher(shortlist, issues),
            mailer,
            pings,
            _profiles(),
            actor_user_id="admin-uuid-1",
        )

    assert issues.get_latest_published() is None
    assert mailer.last_body_text is None
    # Sent batch stays hidden from the unsent pool; still visible via get_latest_batch (D-89).
    assert shortlist.get_current_batch() is None
    assert shortlist.get_latest_batch().sent_at == sent_at


def test_send_publish_failure_releases_claim_for_retry() -> None:
    """CR-01: a publish failure inside the atomic op must leave the batch un-claimed for retry."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = _FailingIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()

    with pytest.raises(PersistenceError):
        send_digest(
            shortlist,
            _publisher(shortlist, issues),
            mailer,
            pings,
            _profiles(),
            actor_user_id="admin-uuid-1",
            now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
        )

    # The atomic claim+publish rolled back — otherwise the batch is permanently stuck as
    # "sent" with no published issue and no recoverable retry (CR-01).
    batch = shortlist.get_current_batch()
    assert batch is not None
    assert batch.sent_at is None
    # No side effects leaked from the failed send.
    assert issues.get_latest_published() is None
    assert mailer.last_body_text is None
    assert pings.entries == []


def test_send_repeat_after_success_is_idempotent_409_path() -> None:
    """D-89: after successful send, claim fails — no second stub send."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()
    publisher = _publisher(shortlist, issues)
    profiles = _profiles()

    first = send_digest(
        shortlist,
        publisher,
        mailer,
        pings,
        profiles,
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )
    first_number = first.issue_number
    first_body = mailer.last_body_text
    ping_count = len(pings.entries)

    with pytest.raises(AlreadySentError):
        send_digest(
            shortlist,
            publisher,
            mailer,
            pings,
            profiles,
            actor_user_id="admin-uuid-1",
        )

    assert issues.get_by_number(first_number) is not None
    assert len([i for i in issues._issues if i.published_at is not None]) == 1
    assert mailer.last_body_text == first_body
    assert len(pings.entries) == ping_count


def test_send_material_ids_reversed_order_becomes_publication_and_mail_order() -> None:
    """G-05-1 / ADMIN-07: material_ids permutation is publication + mail order (not rank)."""
    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(material_id=101, rank=1, title="First by rank"),
            _item(material_id=102, rank=2, title="Second by rank"),
        )
    )
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        pings,
        _profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
        material_ids=[102, 101],
    )

    published = issues.get_by_number(result.issue_number)
    assert published is not None
    assert [item.title for item in published.items] == ["Second by rank", "First by rank"]
    assert mailer.last_body_text is not None
    second_at = mailer.last_body_text.index("Second by rank")
    first_at = mailer.last_body_text.index("First by rank")
    assert second_at < first_at


def test_send_material_ids_mismatched_set_raises() -> None:
    """G-05-1: material_ids must be exact permutation of approved∩ready → domain error."""
    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(material_id=101, rank=1, title="A"),
            _item(material_id=102, rank=2, title="B"),
        )
    )
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()

    with pytest.raises(InvalidSendOrderError):
        send_digest(
            shortlist,
            _publisher(shortlist, issues),
            mailer,
            pings,
            _profiles(),
            actor_user_id="admin-uuid-1",
            material_ids=[101],
        )

    with pytest.raises(InvalidSendOrderError):
        send_digest(
            shortlist,
            _publisher(shortlist, issues),
            mailer,
            pings,
            _profiles(),
            actor_user_id="admin-uuid-1",
            material_ids=[101, 102, 999],
        )

    assert shortlist.get_current_batch().sent_at is None
    assert issues.get_latest_published() is None
    assert mailer.last_body_text is None


def test_send_audit_failure_after_publish_still_returns_success() -> None:
    """CR-02: after claim_and_publish succeeds, audit/mail errors must not fail the send."""
    shortlist = InMemoryShortlistRepository(batch=_batch(_item(material_id=101)))
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = _FailingPingRecorder()

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        pings,
        _profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    )

    assert result.message == "Выпуск опубликован. Доставка писем: stub (0 из 0)"
    assert result.issue_url.startswith("/issues/")
    assert shortlist.get_current_batch() is None
    assert shortlist.get_latest_batch().sent_at is not None
    assert issues.get_by_number(result.issue_number) is not None
    assert mailer.last_body_text is not None


def test_send_body_includes_intro_and_interstitial_text_blocks() -> None:
    """WR-02: mail body must match preview composition (intro + ordered blocks)."""
    from backend.application.use_cases.preview_digest_email import (
        PreviewMaterialBlock,
        PreviewTextBlock,
    )

    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(material_id=101, rank=1, title="First by rank"),
            _item(material_id=102, rank=2, title="Second by rank"),
        )
    )
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        pings,
        _profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
        material_ids=[102, 101],
        intro="Коллеги, добрый день!",
        blocks=[
            PreviewMaterialBlock(material_id=102),
            PreviewTextBlock(text="связка"),
            PreviewMaterialBlock(material_id=101),
        ],
    )

    body = mailer.last_body_text or ""
    assert f"/issues/{result.issue_number}" in body
    intro_at = body.index("Коллеги, добрый день!")
    second_at = body.index("Second by rank")
    bridge_at = body.index("связка")
    first_at = body.index("First by rank")
    assert intro_at < second_at < bridge_at < first_at


def test_send_validates_against_top_five_visible_pool() -> None:
    """WR-05: send pool must match GET ≤5 so SPA material_ids cannot hit InvalidSendOrderError."""
    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            *(_item(material_id=100 + i, rank=i, title=f"Item {i}") for i in range(1, 7)),
        )
    )
    batch = shortlist.get_current_batch()
    assert batch is not None
    for item in batch.items:
        shortlist.set_decision(
            batch_id=batch.id,
            material_id=item.material_id,
            decision="approved",
            actor_user_id="admin-uuid-1",
            decided_at=datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc),
        )

    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()
    visible_ids = [101, 102, 103, 104, 105]

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        pings,
        _profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
        material_ids=visible_ids,
    )

    published = issues.get_by_number(result.issue_number)
    assert published is not None
    assert len(published.items) == 5
    assert [item.title for item in published.items] == [
        "Item 1",
        "Item 2",
        "Item 3",
        "Item 4",
        "Item 5",
    ]
    assert "Item 6" not in {item.title for item in published.items}


def test_send_records_body_html_with_interstitial_and_omits_issue_url() -> None:
    """ADUX-02 / D-07 / D-11: StubMailer.last_body_html from render_email_html; no /issues/."""
    from backend.application.use_cases.preview_digest_email import (
        PreviewMaterialBlock,
        PreviewTextBlock,
    )

    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=101,
                rank=1,
                title="Send HTML Title",
                dek="Send dek",
                slug="send-html-title",
            ),
        )
    )
    issues = InMemoryIssueRepository()
    mailer = StubMailer()
    pings = InMemoryPingRecorder()

    result = send_digest(
        shortlist,
        _publisher(shortlist, issues),
        mailer,
        pings,
        _profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
        intro="Para one\n\nPara two",
        blocks=[
            PreviewMaterialBlock(material_id=101),
            PreviewTextBlock(text="Bridge A\n\nBridge B"),
        ],
    )

    html = mailer.last_body_html
    assert isinstance(html, str)
    assert html
    assert "<p>Para one</p><p>Para two</p>" in html
    assert "<p>Bridge A</p><p>Bridge B</p>" in html
    assert "Send HTML Title" in html
    assert "Читать →" in html
    assert f"/issues/{result.issue_number}" in (mailer.last_body_text or "")
    assert "/issues/" not in html


def test_send_body_html_uses_site_url_for_chitat_href() -> None:
    """ADUX-02 / D-11: send_digest(site_url=…) drives absolute Читать → href."""
    from backend.application.use_cases.preview_digest_email import PreviewMaterialBlock

    shortlist = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=101,
                rank=1,
                title="Absolute Link",
                slug="absolute-link",
            ),
        )
    )
    mailer = StubMailer()

    send_digest(
        shortlist,
        _publisher(shortlist, InMemoryIssueRepository()),
        mailer,
        InMemoryPingRecorder(),
        _profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
        blocks=[PreviewMaterialBlock(material_id=101)],
        site_url="https://digest.example",
    )

    html = mailer.last_body_html or ""
    assert 'href="https://digest.example/materials/absolute-link"' in html
    assert "Читать →" in html


def test_send_omits_reader_link_in_html_and_plain_body_when_slug_blank() -> None:
    """W-2: a blank slug emits no reader link in either body (HTML or StubMailer plain text)."""
    from backend.application.use_cases.preview_digest_email import PreviewMaterialBlock

    shortlist = InMemoryShortlistRepository(
        batch=_batch(_item(material_id=101, rank=1, title="Blank Slug", slug=None))
    )
    mailer = StubMailer()

    send_digest(
        shortlist,
        _publisher(shortlist, InMemoryIssueRepository()),
        mailer,
        InMemoryPingRecorder(),
        _profiles(),
        actor_user_id="admin-uuid-1",
        now=datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
        blocks=[PreviewMaterialBlock(material_id=101)],
        site_url="https://digest.example",
    )

    html = mailer.last_body_html or ""
    assert "Blank Slug" in html
    assert "Читать →" not in html
    assert "/materials/" not in html

    plain = mailer.last_body_text or ""
    assert "Blank Slug" in plain
    assert "/materials/" not in plain


def test_post_shortlist_send_passes_settings_site_url() -> None:
    """ADUX-02 / D-11 / D-12: send HTTP path uses trusted Settings.site_url like preview."""
    from pathlib import Path

    from backend.interface.http.routes import admin as admin_routes

    src = Path(admin_routes.__file__).read_text(encoding="utf-8")
    send_fn_start = src.index("def post_shortlist_send")
    next_def = src.find("\ndef ", send_fn_start + 1)
    send_fn = src[send_fn_start:] if next_def < 0 else src[send_fn_start:next_def]
    assert "site_url" in send_fn
    assert "settings" in send_fn
    assert "payload.site_url" not in send_fn
    assert "body.site_url" not in send_fn
