"""
Step 5: Form co-pilot.

Turns a short conversation into a completed DRAFT of one real application: an
employer-transfer request. It asks only for the fields it needs, then produces a
plain-text draft for the worker or an NGO caseworker to review.

Important boundaries by design:
- It DRAFTS only. It never submits anything to any government system.
- The field list here is a reasonable starter. Confirm the exact required
  fields against the current official form before real use.
"""

from dataclasses import dataclass, field


@dataclass
class FormField:
    key: str
    question: str  # plain-language prompt shown to the worker
    required: bool = True


# Starter field set for an employer-transfer request. Adjust to the real form.
EMPLOYER_TRANSFER_FIELDS = [
    FormField("full_name", "What is your full name, as written on your ARC?"),
    FormField("nationality", "What is your nationality?"),
    FormField("arc_number", "What is your ARC (resident certificate) number?"),
    FormField("passport_number", "What is your passport number?"),
    FormField("current_employer", "What is the name of your current employer?"),
    FormField("job_category", "What is your job type? (for example: caregiver, factory worker)"),
    FormField("reason", "Why do you want to transfer to a new employer?"),
    FormField("new_employer", "Do you already have a new employer? If yes, their name (or write 'none yet').", required=False),
    FormField("contact_phone", "What is your phone number, so you can be contacted?"),
]


@dataclass
class FormSession:
    """Tracks answers as they are collected for one form."""
    fields: list[FormField]
    answers: dict = field(default_factory=dict)

    def next_missing(self) -> FormField | None:
        """Return the next required field still unanswered, or None if done."""
        for f in self.fields:
            if f.required and not self.answers.get(f.key):
                return f
        return None

    def record(self, key: str, value: str) -> None:
        self.answers[key] = value.strip()

    def is_complete(self) -> bool:
        return self.next_missing() is None

    def render_draft(self) -> str:
        """Produce the plain-text draft application from collected answers."""
        a = self.answers
        lines = [
            "DRAFT - EMPLOYER TRANSFER REQUEST",
            "(Please review carefully. This is a draft, not a submitted form.)",
            "",
            f"Full name:           {a.get('full_name', '')}",
            f"Nationality:         {a.get('nationality', '')}",
            f"ARC number:          {a.get('arc_number', '')}",
            f"Passport number:     {a.get('passport_number', '')}",
            f"Current employer:    {a.get('current_employer', '')}",
            f"Job category:        {a.get('job_category', '')}",
            f"New employer:        {a.get('new_employer') or 'None yet'}",
            f"Contact phone:       {a.get('contact_phone', '')}",
            "",
            "Reason for transfer:",
            f"  {a.get('reason', '')}",
            "",
            "Next steps:",
            "  1. Check the current required documents and the official form.",
            "  2. If anything is unclear, call the free 1955 hotline (dial 1955).",
            "  3. Have an NGO caseworker or the labor bureau review this before submitting.",
        ]
        return "\n".join(lines)


def new_employer_transfer_session() -> FormSession:
    return FormSession(fields=list(EMPLOYER_TRANSFER_FIELDS))
