from app.crud.document import document
from app.crud.chat import conversation, message
from app.crud.template import template
from app.crud.user import user, user_preference, user_goal

# Export all CRUD instances
__all__ = [
    "document",
    "conversation",
    "message",
    "template",
    "user",
    "user_preference",
    "user_goal",
]