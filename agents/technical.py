import ollama
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse

class TechnicalAgent(BaseAgent):
    """
    技術面分析師 (Technical Analyst)
    專注於量價結構、均線排列、布林通道與停損防守點位。
    """
    def __init__(self, config: dict):
        super().__init__(config)

    def prepare(self, knowledge: StockKnowledge) -> str:
        tech = knowledge.technicals
        comp = knowledge.company
        
        def safe_fmt(val):
            return f"{val:.2f}" if val is not None else "N/A"

        # 技術大腦只看這區，絕對不會被基本面財報干擾
        context = f"""【絕對客觀情報區 - 技術面指標】
分析標的：{comp.ticker}
當前現價：{safe_fmt(tech.current_price)}

[動能與防守指標]
- 20日均線 (MA20): {safe_fmt(tech.ma_20)}
- 50日均線 (MA50): {safe_fmt(tech.ma_50)}
- 布林通道上軌 (壓力): {safe_fmt(tech.bollinger_upper)}
- 布林通道下軌 (支撐): {safe_fmt(tech.bollinger_lower)}
- ATR (真實波動幅度): {safe_fmt(tech.atr_14)}
- POC (籌碼密集區鐵底): {safe_fmt(tech.poc_support)}
"""
        return context

    def think(self, context: str, user_query: str) -> AgentResponse:
        system_prompt = f"""你是{self.role_description}。
{context}

【任務指示】：
首席顧問 (CIO) 的提問是：「{user_query}」

【最高防護鐵律】：
1. 嚴禁客套話，請直接推演出具體的支撐、壓力與停損點位。
2. ATR 是用來設定合理停損寬度的，請務必將其納入風險評估。
3. 嚴禁談論公司基本面、營收或未來展望，那不是你的職責！越界將被系統懲罰！
"""
        try:
            res = ollama.generate(model=self.model_name, prompt=system_prompt)
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text=res['response'].strip(),
                self_confidence=0.85 
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text="〔系統異常：技術面大腦推理失敗。〕",
                self_confidence=0.0
            )

    def validate(self, response: AgentResponse) -> bool:
        if "營收" in response.response_text or "淨利" in response.response_text:
            # 如果技術專家談論基本面，直接標記為不合格 (越界)
            return False
        return True