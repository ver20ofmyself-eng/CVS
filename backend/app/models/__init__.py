from app.models.user import User
from app.models.vacancy import Vacancy
from app.models.analyses import Analysis
from app.models.tariff import Tariff
from app.models.user_tariffs import UserTariff
from app.models.payments import Payment
from app.models.prompt import Prompt, PromptHistory

__all__ = [
    'User', 'Vacancy', 'Analysis', 'Tariff', 
    'UserTariff', 'Payment', 'Prompt', 'PromptHistory'
]
