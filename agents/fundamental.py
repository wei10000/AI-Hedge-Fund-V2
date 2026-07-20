import ollama
import re
from typing import Optional
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse

class FundamentalAgent(BaseAgent):
    """
    基本面分析師 (Fundamental Analyst)
    升級版：移除了原本笨重的內部迴圈，現在它只專注於推理與輸出 <READ_FILE> 標籤！
    """
    def __init__(self, config: dict):
        super().__init__(config)

    def prepare(self, knowledge: StockKnowledge) -> str:
        fin = knowledge.financials
        comp = knowledge.company
        
        def safe_fmt(val):
            return val if val is not None else "N/A"

        context = f"""【絕對客觀情報區 - 企業基本面】
公司名稱：{comp.company_name} ({comp.ticker})
所屬板塊：{comp.sector} / {comp.industry}

[核心財務指標]
- TTM 總營收: {safe_fmt(fin.revenue_ttm)}
- 淨利潤: {safe_fmt(fin.net_income)}
- 自由現金流 (平滑後): {safe_fmt(fin.fcf_normalized)}

[可用本地檔案 (供深度查閱)]
- {comp.ticker}_Full_Report.txt (包含完整三大財務報表原始數據)
"""
        return context

    def think(self, context: str, user_query: str) -> AgentResponse:
        system_prompt = f"""你是{self.role_description}。
{context}

【任務指示】：
首席顧問 (CIO) 的提問是：「{user_query}」

🔥🔥🔥【工具使用權限 (Tool Calling)】：
如果你覺得情報區的數據不足（例如缺乏具體營收增長率），你擁有查閱本地檔案的能力！
請嚴格輸出以下格式來呼叫工具（輸出後請立刻停止發言，等待系統回傳）：
<READ_FILE>檔案名稱|英文關鍵字</READ_FILE>
例如：<READ_FILE>NVDA_Full_Report.txt|Revenue</READ_FILE>

如果你認為現有數據已經足夠，請直接給出量化結論，嚴禁客套話。
"""
        try:
            # 這裡只做「單次生成」，如果生成結果帶有 XML 標籤，WorkflowEngine 會攔截它！
            res = ollama.generate(model=self.model_name, prompt=system_prompt)
            response_text = res['response'].strip()
            
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text=response_text,
                self_confidence=0.9
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