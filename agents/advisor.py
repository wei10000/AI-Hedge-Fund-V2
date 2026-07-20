import ollama
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse

class AdvisorAgent(BaseAgent):
    """
    首席顧問 (Chief Investment Officer, CIO)
    負責彙整所有專家意見，撰寫最終決策白皮書。
    """
    def __init__(self, config: dict):
        super().__init__(config)
    
    def prepare(self, knowledge: StockKnowledge) -> str:
        return f"【投資標的】：{knowledge.company.ticker} ({knowledge.company.company_name})\n當前市值：{knowledge.company.market_cap}"
        
    def think(self, context: str, debate_history: str) -> AgentResponse:
        system_prompt = f"""你是{self.role_description}。
{context}

【任務指示】：
請閱讀以下各專家的分析紀錄：
{debate_history}

請撰寫一份最終的 Markdown 決策白皮書。必須包含以下章節：
### 1. 核心觀點總結
### 2. 基本面診斷
### 3. 技術面與防守點位
### 4. 最終行動建議
"""
        try:
            res = ollama.generate(model=self.model_name, prompt=system_prompt, options={"temperature": 0.2})
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text=res['response'].strip(),
                self_confidence=1.0
            )
        except Exception as e:
            return AgentResponse(agent_name=self.name, role=self.role_description, response_text="白皮書生成失敗。", self_confidence=0.0)

    def validate(self, response: AgentResponse) -> bool:
        return True