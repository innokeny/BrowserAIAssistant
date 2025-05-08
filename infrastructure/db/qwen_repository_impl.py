from datetime import datetime
from typing import List, Optional, Dict, Any
from infrastructure.db.db_connection import get_db_session
from infrastructure.db.models import QwenHistory

class QwenRepositoryImpl:
    def process_request(
        self,
        user_id: int,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Process a Qwen chat request"""
        # TODO: Implement actual Qwen model integration
        response = f"Mock response for prompt: {prompt}"
        
        # Save history
        with get_db_session() as session:
            history = QwenHistory(
                user_id=user_id,
                prompt=prompt,
                response=response,
                tokens_used=len(response.split()),
                created_at=datetime.now()
            )
            session.add(history)
            session.commit()
            session.refresh(history)
        
        return response

    def get_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        with get_db_session() as session:
            history = session.query(QwenHistory)\
                .filter(QwenHistory.user_id == user_id)\
                .order_by(QwenHistory.created_at.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            return [
                {
                    "id": h.id,
                    "prompt": h.prompt,
                    "response": h.response,
                    "tokens_used": h.tokens_used,
                    "created_at": h.created_at.isoformat()
                }
                for h in history
            ] 