import ollama
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse

class AuditorAgent(BaseAgent):
    """
    最高風控官 (Chief Risk Officer, CRO)
    負責審核專家意見是否矛盾或越界。
    """
    def __init__(self, config: dict):
        super().__init__(config)
    
    def prepare(self, knowledge: StockKnowledge) -> str:
        return "【系統提示】：你負責審核會議紀錄，不直接分析生數據。"
        
    def think(self, context: str, debate_history: str) -> AgentResponse:
        system_prompt = f"""你是{self.role_description}。
{context}

【任務指示】：
以下是本次會議中各專家的發言紀錄：
{debate_history}

請判斷這些專家的結論是否存在嚴重矛盾（例如基本面看多但技術面強烈看空，或者數據引用錯誤）。
1. 若有矛盾或高風險，請以「TERMINATE」開頭，並簡述警告理由。
2. 若邏輯一致且安全，請以「CONTINUE」開頭。
"""
        try:
            res = ollama.generate(model=self.model_name, prompt=system_prompt)
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text=res['response'].strip(),
                self_confidence=1.0
            )
        except Exception as e:
            return AgentResponse(agent_name=self.name, role=self.role_description, response_text="CONTINUE (風控系統異常，預設放行)", self_confidence=0.0)

    def validate(self, response: AgentResponse) -> bool:
        return True