from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.data_models import StockKnowledge, AgentResponse

class BaseAgent(ABC):
    """
    所有專家的標準化基礎介面 (Standard Base Interface)。
    任何人要新增專家，都必須且只能繼承此類別，並實作以下三個方法。
    """
    def __init__(self, config: dict):
        self.id = config.get("id")
        self.name = config.get("id") # 保留 name 屬性以向下相容
        self.role_description = config.get("role_description", "")
        self.model_name = config.get("model", "llama3.1:latest")
        self.config = config

    @abstractmethod
    def prepare(self, knowledge: StockKnowledge) -> str:
        """
        準備階段：Agent 讀取結構化的 Knowledge，轉換成自己的 System Prompt Context。
        """
        pass

    @abstractmethod
    def think(self, context: str, user_query: str) -> AgentResponse:
        """
        思考階段：呼叫 LLM 進行推理，並回傳標準化 AgentResponse 物件。
        """
        pass

    @abstractmethod
    def validate(self, response: AgentResponse) -> bool:
        """
        驗證階段：檢查 LLM 輸出的內容是否包含幻覺或越界。
        """
        pass