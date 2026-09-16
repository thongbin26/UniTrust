from pydantic import BaseModel, Field

from app.models.obligation import ActionType


class DraftAudience(BaseModel):
    raw_text: str

    applies_to_all_students: bool = False

    faculties: list[str] = Field(
        default_factory=list
    )

    majors: list[str] = Field(
        default_factory=list
    )

    cohorts: list[str] = Field(
        default_factory=list
    )

    programs: list[str] = Field(
        default_factory=list
    )


class DraftAction(BaseModel):
    action_type: ActionType

    # Should be a short phrase copied or nearly copied
    # from RAW_TEXT, not a free paraphrase.
    text: str


class DraftDeadline(BaseModel):
    # Keep the original Vietnamese phrase.
    # Deterministic code will normalize the date.
    raw_text: str


class DraftMoney(BaseModel):
    # Keep the original money phrase.
    # Deterministic code will normalize the value.
    raw_text: str


class DraftText(BaseModel):
    text: str


class DraftObligation(BaseModel):
    audience: DraftAudience | None = None

    action: DraftAction

    deadline: DraftDeadline | None = None

    amount: DraftMoney | None = None

    location: DraftText | None = None

    required_documents: list[DraftText] = Field(
        default_factory=list
    )

    exceptions: list[DraftText] = Field(
        default_factory=list
    )


class ExtractionDraft(BaseModel):
    obligations: list[DraftObligation] = Field(
        default_factory=list
    )

from app.models.obligation import CanonicalNoticeAnnotation


def draft_from_annotation(
    annotation: CanonicalNoticeAnnotation,
) -> ExtractionDraft:
    obligations = []

    for obligation in (
        annotation.obligations
    ):
        audience = None

        if obligation.audience:
            audience = DraftAudience(
                raw_text=(
                    obligation
                    .audience
                    .raw_text
                ),
                applies_to_all_students=(
                    obligation
                    .audience
                    .applies_to_all_students
                ),
                faculties=list(
                    obligation
                    .audience
                    .faculties
                ),
                majors=list(
                    obligation
                    .audience
                    .majors
                ),
                cohorts=list(
                    obligation
                    .audience
                    .cohorts
                ),
                programs=list(
                    obligation
                    .audience
                    .programs
                ),
            )

        deadline = None

        if obligation.deadline:
            deadline = DraftDeadline(
                raw_text=(
                    obligation
                    .deadline
                    .raw_text
                )
            )

        amount = None

        if obligation.amount:
            amount = DraftMoney(
                raw_text=(
                    obligation
                    .amount
                    .raw_text
                )
            )

        location = None

        if obligation.location:
            location = DraftText(
                text=(
                    obligation
                    .location
                    .text
                )
            )

        required_documents = [
            DraftText(
                text=document.text
            )
            for document
            in obligation.required_documents
        ]

        exceptions = [
            DraftText(
                text=exception.text
            )
            for exception
            in obligation.exceptions
        ]

        obligations.append(
            DraftObligation(
                audience=audience,
                action=DraftAction(
                    action_type=(
                        obligation
                        .action
                        .action_type
                    ),
                    text=(
                        obligation
                        .action
                        .text
                    ),
                ),
                deadline=deadline,
                amount=amount,
                location=location,
                required_documents=(
                    required_documents
                ),
                exceptions=exceptions,
            )
        )

    return ExtractionDraft(
        obligations=obligations
    )