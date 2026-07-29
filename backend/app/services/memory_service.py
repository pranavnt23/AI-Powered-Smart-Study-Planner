import logging
from sqlalchemy.orm import Session
from app.models.chat_message import ChatMessage

logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service responsible for persisting, loading, and managing conversation history
    for multi-turn chat sessions.
    """

    @classmethod
    def save_message(
        cls,
        db: Session,
        session_id: str,
        user_id: int,
        role: str,
        content: str
    ) -> ChatMessage:
        """
        Saves a single dialogue turn to the database.

        Args:
            db (Session): Database session.
            session_id (str): Chat session identifier.
            user_id (int): ID of the user.
            role (str): Role of the sender ('user' or 'assistant').
            content (str): Text contents of the message.

        Returns:
            ChatMessage: The created DB record.
        """
        try:
            logger.info(f"Saving {role} message for session {session_id}...")
            db_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content.strip()
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            return db_message
        except Exception as error:
            db.rollback()
            logger.error(f"Failed to save chat message: {str(error)}")
            raise error

    @classmethod
    def get_session_history(
        cls,
        db: Session,
        session_id: str,
        user_id: int,
        limit: int = 6
    ) -> list[ChatMessage]:
        """
        Loads the most recent dialogue turns for a session in chronological order (ascending),
        filtered strictly by the requesting user_id to ensure tenant isolation.

        Args:
            db (Session): Database session.
            session_id (str): Chat session identifier.
            user_id (int): ID of the requesting user.
            limit (int): Maximum messages to load (sliding window size). Defaults to 6.

        Returns:
            list[ChatMessage]: Chronologically sorted list of recent dialogue messages.
        """
        try:
            logger.info(f"Loading chat history for session {session_id} for user {user_id} (limit={limit})...")
            # Query the latest messages sorted descending, then reverse them to return chronologically
            latest_messages = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.user_id == user_id
                )
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
                .all()
            )
            return list(reversed(latest_messages))
        except Exception as error:
            logger.error(f"Failed to retrieve chat history: {str(error)}")
            return []
