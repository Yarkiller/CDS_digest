from backend.domain.pipeline_config import PipelineConfigError


class DomainError(Exception):
    """Base domain error."""


class MaterialNotFoundError(DomainError):
    def __init__(self, material_id: int | str) -> None:
        super().__init__(f"material {material_id} not found")
        self.material_id = material_id


class IssueNotFoundError(DomainError):
    def __init__(self, number: int) -> None:
        super().__init__(f"issue {number} not found")
        self.number = number


class RazborNotFoundError(DomainError):
    def __init__(self, razbor_id: int) -> None:
        super().__init__(f"razbor {razbor_id} not found")
        self.razbor_id = razbor_id


class NotebookNotAvailableError(DomainError):
    """Raised when a razbor has no notebook or the file is missing (RAZB-03 / D-72)."""

    def __init__(self, razbor_id: int | None = None, *, path: str | None = None) -> None:
        target = f"razbor {razbor_id}" if razbor_id is not None else (path or "notebook")
        super().__init__(f"notebook not available for {target}")
        self.razbor_id = razbor_id
        self.path = path


class NotebookPathInvalidError(DomainError):
    """Raised when notebook_path escapes NOTEBOOK_ROOT (T-04-09)."""

    def __init__(self, path: str) -> None:
        super().__init__(f"notebook path invalid: {path!r}")
        self.path = path


class MaterialValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MaterialNotReadyError(DomainError):
    def __init__(self, material_id: int) -> None:
        super().__init__(f"material {material_id} is not ready for indexing")
        self.material_id = material_id


class PersistenceError(DomainError):
    """Raised when an infrastructure adapter cannot complete a persistence operation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MailDeliveryError(DomainError):
    """Raised when a mail adapter cannot deliver a digest message (MAIL-04 / D-88).

    Mail adapters map transport failures (``SMTPException`` / ``OSError`` /
    ``TimeoutError``) onto this domain type; ``send_digest`` catches it alongside
    ``PersistenceError`` after publish so an already-published digest is never 500-ed.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class KnowledgeQueryValidationError(DomainError):
    """Raised for blank or overlong knowledge search queries (KNOW-01)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class VotingCycleClosedError(DomainError):
    """Raised when cast_vote is attempted while cycle status is not open (D-51)."""

    def __init__(self, cycle_id: str, ballot: object | None = None) -> None:
        super().__init__(f"voting cycle {cycle_id} is closed")
        self.cycle_id = cycle_id
        self.ballot = ballot


class VoteConflictError(DomainError):
    """Raised when expected_updated_at does not match the stored vote (D-54)."""

    def __init__(
        self,
        cycle_id: str,
        user_id: str,
        ballot: object | None = None,
    ) -> None:
        super().__init__(f"vote conflict for cycle {cycle_id} user {user_id}")
        self.cycle_id = cycle_id
        self.user_id = user_id
        self.ballot = ballot


class InvalidVoteError(DomainError):
    """Raised for empty, unknown, or out-of-cycle topic_id."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ShortlistNotFoundError(DomainError):
    """Raised when current batch is missing or material_id is not in the batch."""

    def __init__(self, *, batch_id: int | None = None, material_id: int | None = None) -> None:
        if material_id is not None:
            msg = f"shortlist material {material_id} not found"
        elif batch_id is not None:
            msg = f"shortlist batch {batch_id} not found"
        else:
            msg = "shortlist batch not found"
        super().__init__(msg)
        self.batch_id = batch_id
        self.material_id = material_id


class InvalidShortlistDecisionError(DomainError):
    """Raised when decision is outside pending|approved|rejected (D-82)."""

    def __init__(self, decision: str) -> None:
        super().__init__(f"invalid shortlist decision: {decision!r}")
        self.decision = decision


class EmptySendPoolError(DomainError):
    """Raised when approved∩ready send/preview pool is empty (ADMIN-04/07)."""

    def __init__(self, batch_id: int | None = None) -> None:
        super().__init__(
            f"empty send pool for batch {batch_id}" if batch_id is not None else "empty send pool"
        )
        self.batch_id = batch_id


class InvalidPreviewCompositionError(DomainError):
    """Raised when preview blocks reference material outside approved∩ready (G-05-1)."""

    def __init__(self, material_id: int | None = None) -> None:
        if material_id is not None:
            msg = f"invalid preview composition: material {material_id} not in approved ready pool"
        else:
            msg = "invalid preview composition"
        super().__init__(msg)
        self.material_id = material_id


class DraftInSendPoolError(DomainError):
    """Raised when any approved shortlist item is still draft (ADMIN-03, D-85)."""

    def __init__(self, draft_material_ids: list[int], *, batch_id: int | None = None) -> None:
        ids = list(draft_material_ids)
        super().__init__(f"approved drafts in send pool: {ids}")
        self.draft_material_ids = ids
        self.batch_id = batch_id


class InvalidSendOrderError(DomainError):
    """Raised when send material_ids is not an exact permutation of approved∩ready (G-05-1)."""

    def __init__(self, *, batch_id: int | None = None) -> None:
        super().__init__(
            f"invalid send material_ids for batch {batch_id}"
            if batch_id is not None
            else "invalid send material_ids"
        )
        self.batch_id = batch_id


class AlreadySentError(DomainError):
    """Raised when batch sent_at is set or claim loses the race (ADMIN-07, D-89)."""

    def __init__(self, batch_id: int | None = None) -> None:
        super().__init__(
            f"batch {batch_id} already sent" if batch_id is not None else "batch already sent"
        )
        self.batch_id = batch_id
        self.message_ru = "Уже отправлено"


class PipelineConfigValidationError(DomainError):
    """Raised when the pipeline config fails server-side validation (PIPE-02, D-03/D-05).

    Carries the structured ``PipelineConfigError`` tuple the PUT route maps to a
    top-level ``{"errors": [...]}`` 400 payload.
    """

    def __init__(self, errors: tuple[PipelineConfigError, ...]) -> None:
        super().__init__("pipeline config validation failed")
        self.errors = errors
