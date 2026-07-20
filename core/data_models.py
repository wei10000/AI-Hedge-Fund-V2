from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date

# ==========================================
# 1. 證據與信心引擎 (Evidence & Confidence)
# ==========================================
class Evidence(BaseModel):
    id: str = Field(description="證據的唯一識別碼 (如: EV_REV_001)")
    metric_name: str = Field(description="指標名稱 (如: Revenue Growth)")
    value: str = Field(description="指標數值或結論 (如: 35%)")
    source: str = Field(description="資料來源 (如: Yahoo Finance, SEC, Google News)")
    timestamp: date = Field(description="取得資料的時間")
    confidence_score: float = Field(ge=0.0, le=1.0, description="系統對此數據的信心水準 (0.0~1.0)")

# ==========================================
# 2. 股票情報庫 (Shared Knowledge Layer)
# ==========================================
class CompanyInfo(BaseModel):
    ticker: str
    company_name: str
    sector: str
    industry: str
    market_cap: float

class FinancialMetrics(BaseModel):
    revenue_ttm: Optional[float] = None
    net_income: Optional[float] = None
    gross_margin: Optional[float] = None
    fcf_normalized: Optional[float] = None  # 常態化自由現金流
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    
    # 將證據綁定到財務數據上
    evidences: List[Evidence] = Field(default_factory=list)

class TechnicalIndicators(BaseModel):
    current_price: float
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    poc_support: Optional[float] = None  # 籌碼密集區鐵底
    
    evidences: List[Evidence] = Field(default_factory=list)

class MacroData(BaseModel):
    cpi_yoy: Optional[float] = None
    unemployment_rate: Optional[float] = None
    pmi_manufacturing: Optional[float] = None
    yield_10y: Optional[float] = None
    effr: Optional[float] = None # 聯邦資金利率
    
    evidences: List[Evidence] = Field(default_factory=list)

# 知識庫總體 (Agent 只能讀取這個 Object，不能自己亂抓網路)
class StockKnowledge(BaseModel):
    company: CompanyInfo
    financials: FinancialMetrics
    technicals: TechnicalIndicators
    macro: MacroData
    news_summary: List[str] = Field(default_factory=list)

# ==========================================
# 3. 會議與辯論模型 (Meeting & Memory Model)
# ==========================================
class AgentResponse(BaseModel):
    agent_name: str
    role: str
    response_text: str
    # 標記此回答引用了哪些證據 ID，方便 CRO 查核
    cited_evidence_ids: List[str] = Field(default_factory=list)
    # Agent 自身對此結論的信心程度
    self_confidence: float = Field(ge=0.0, le=1.0)

class MeetingRound(BaseModel):
    round_number: int
    cio_question: str
    targeted_agents: List[str] = Field(description="CIO 點名的 Agent 列表")
    responses: List[AgentResponse] = Field(default_factory=list)

class DebateMemory(BaseModel):
    ticker: str
    meeting_date: date
    rounds: List[MeetingRound] = Field(default_factory=list)
    cro_decision: str = Field(description="CONTINUE or TERMINATE")