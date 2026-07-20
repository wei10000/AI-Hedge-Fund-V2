import ollama
from typing import Optional
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse

class ChipsMacroAgent(BaseAgent):
    """
    宏觀籌碼專家 (Chips & Macro Analyst)
    專注於聯準會利率、通膨環境與市場資金動向。
    """
    def __init__(self, config: dict):
        super().__init__(config)

    def prepare(self, knowledge: StockKnowledge) -> str:
        macro = knowledge.macro
        comp = knowledge.company
        
        def safe_fmt(val, suffix=""):
            return f"{val:.2f}{suffix}" if val is not None else "N/A"

        # 整理聯準會與總經數據給大腦
        news_list = "\n".join(knowledge.news_summary) if knowledge.news_summary else "無最新重大新聞"
        
        context = f"""【絕對客觀情報區 - 總經與流動性】
分析標的：{comp.ticker} ({comp.sector})

[總體經濟與政策利率]
- 美國 10 年期公債殖利率: {safe_fmt(macro.yield_10y, '%')}
- 聯邦資金有效利率 (EFFR): {safe_fmt(macro.effr, '%')}
- CPI 年增率: {safe_fmt(macro.cpi_yoy, '%')}
- 失業率: {safe_fmt(macro.unemployment_rate, '%')}
- 製造業 PMI: {safe_fmt(macro.pmi_manufacturing)}

[近期新聞與催化劑]
{news_list}
"""
        return context

    def think(self, context: str, user_query: str) -> AgentResponse:
        system_prompt = f"""你是{self.role_description}。
{context}

【任務指示】：
首席顧問 (CIO) 的提問是：「{user_query}」

🔥🔥🔥【工具使用權限 (Tool Calling)】：
如果你覺得需要調查最新的市場動態、聯準會(Fed)決策或機構籌碼變化，你可以請求聯網搜索！
請嚴格輸出以下格式來呼叫工具（輸出後請立刻停止發言，等待系統回傳）：
<SEARCH>你要查的英文關鍵字</SEARCH>
例如：<SEARCH>NVDA institutional ownership recent changes</SEARCH>

🚨【行動鐵律】：
1. 嚴禁客套話。
2. 你的職責是結合總經環境（如利率對科技股估值的影響）與資金流向，給出該標的目前的「大環境順風/逆風」評估。
3. 如果資訊已經足夠，請直接給出量化結論，不要再使用 SEARCH。
"""
        try:
            res = ollama.generate(model=self.model_name, prompt=system_prompt)
            response_text = res['response'].strip()
            
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text=response_text,
                self_confidence=0.85
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name, 
                role=self.role_description, 
                response_text=f"推理失敗: {e}", 
                self_confidence=0.0
            )

    def validate(self, response: AgentResponse) -> bool:
        return True