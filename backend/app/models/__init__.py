"""Import every model so `Base.metadata` (and Alembic autogenerate) sees them."""

from app.models.analysis import Analysis  # noqa: F401
from app.models.interest_area import InterestArea  # noqa: F401
from app.models.interest_test import (  # noqa: F401
    InterestAnswer,
    InterestOption,
    InterestQuestion,
    InterestTestSet,
    InterestTestSetQuestion,
)
from app.models.program import Campus, Program  # noqa: F401
from app.models.requirement import GeneralRequirement, ProgramRequirement  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.spm_result import SPMResult  # noqa: F401
from app.models.subject import Subject, SubjectGroup  # noqa: F401
from app.models.university import University  # noqa: F401
from app.models.user import User  # noqa: F401
