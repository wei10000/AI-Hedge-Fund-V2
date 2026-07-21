"""
會議上下文模型 (Meeting Context Model)
追蹤整個多代理人辯論的完整狀態和決策歷史
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum


class DecisionActionType(str, Enum):
    """決策行為類型"""
    CONTINUE = "CONTINUE"  # 繼續下一輪
    TERMINATE = "TERMINATE"  # 終止流程
    REQUEST_DATA = "REQUEST_DATA"  # 請求補充數據
    FINALIZE = "FINALIZE"  # 進入最終報告
    DEEPEN = "DEEPEN"  # 深化討論


class DecisionSource(str, Enum):
    """決策來源"""
    PROGRAM = "PROGRAM"  # 程式邏輯決策
    AI_MODERATOR = "AI_MODERATOR"  # Moderator AI 決策
    AI_CRO = "AI_CRO"  # CRO AI 決策
    RESOURCE_LIMIT = "RESOURCE_LIMIT"  # 資源限制（Token、時間）


class AgentPosition(BaseModel):
    """某個 Agent 在某一輪的立場"""
    agent_id: str
    agent_name: str
    round_number: int
    position: str  # "BULLISH" | "BEARISH" | "NEUTRAL"
    confidence: float = Field(ge=0.0, le=1.0)
    key_argument: str  # 核心論點（一句話）
    response_text: str  # 完整回應
    cited_data: List[str] = Field(default_factory=list)  # 引用的數據
    timestamp: datetime = Field(default_factory=datetime.now)


class Disagreement(BaseModel):
    """檢測到的重大分歧"""
    agent_1_id: str
    agent_2_id: str
    disagreement_type: str  # "OPPOSITE" | "COMPLEMENTARY" | "UNCLEAR"
    severity: float = Field(ge=0.0, le=1.0)  # 0-1，分歧程度
    description: str
    suggested_clarification: str  # 建議的澄清問題


class Decision(BaseModel):
    """流程決策記錄"""
    decision_id: str  # 決策唯一 ID
    round_number: int
    decision_maker: str  # "Program" | "Moderator" | "CRO"
    source: DecisionSource
    action: DecisionActionType
    reason: str
    data: Dict = Field(default_factory=dict)  # 決策的支撐數據
    timestamp: datetime = Field(default_factory=datetime.now)


class RoundMemory(BaseModel):
    """某一輪辯論的完整記錄"""
    round_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # 這一輪的參與者和立場
    positions: List[AgentPosition] = Field(default_factory=list)
    
    # 這一輪檢測到的分歧
    disagreements: List[Disagreement] = Field(default_factory=list)
    
    # 這一輪的主題/焦點
    debate_topic: str
    
    # 這一輪的決策（由 Moderator 制定的計劃）
    moderator_plan: Optional[Dict] = None
    
    # 計算結果
    round_consensus: float = 0.0  # 0-1，這一輪的共識度
    average_confidence: float = 0.0  # 平均信心分
    
    # 這一輪結束後的決策
    round_decision: Optional[Decision] = None


class MeetingContext(BaseModel):
    """整個會議的完整上下文"""
    
    # 基本信息
    ticker: str
    meeting_id: str = Field(default_factory=lambda: f"meeting_{datetime.now().timestamp()}")
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # 會議狀態
    status: str = "RUNNING"  # "RUNNING" | "COMPLETED" | "TERMINATED" | "PAUSED"
    termination_reason: Optional[str] = None
    
    # 輪次管理
    current_round: int = 0
    max_rounds: int = 5
    round_history: List[RoundMemory] = Field(default_factory=list)
    
    # 全局狀態
    overall_consensus: float = 0.0  # 當前整體共識度
    overall_confidence: float = 0.0  # 當前整體信心度
    
    # 所有 Agent 的最終立場
    final_positions: Dict[str, str] = Field(default_factory=dict)  # {agent_id: position}
    
    # 決策歷史
    decisions: List[Decision] = Field(default_factory=list)
    
    # 數據補充請求
    data_requests: List[str] = Field(default_factory=list)
    collected_data: Dict[str, str] = Field(default_factory=dict)  # {request -> result}
    
    # 資源消耗追蹤
    total_tokens_estimated: int = 0
    token_per_round: List[int] = Field(default_factory=list)
    
    # AI 決策痕跡
    moderator_decisions: List[Dict] = Field(default_factory=list)
    cro_decisions: List[Dict] = Field(default_factory=list)

    def add_round(self, round_memory: RoundMemory):
        """添加一輪辯論記錄"""
        self.round_history.append(round_memory)
        self.current_round = round_memory.round_number
        self.overall_consensus = self._calculate_overall_consensus()
        self.overall_confidence = self._calculate_overall_confidence()

    def add_decision(self, decision: Decision):
        """記錄一個重要決策"""
        self.decisions.append(decision)

    def add_moderator_decision(self, decision_data: Dict):
        """記錄 Moderator 的決策"""
        self.moderator_decisions.append({
            "round": self.current_round,
            "timestamp": datetime.now().isoformat(),
            **decision_data
        })

    def add_cro_decision(self, decision_data: Dict):
        """記錄 CRO 的決策"""
        self.cro_decisions.append({
            "round": self.current_round,
            "timestamp": datetime.now().isoformat(),
            **decision_data
        })

    def _calculate_overall_consensus(self) -> float:
        """計算當前整體共識度"""
        if not self.round_history:
            return 0.0
        
        # 最新一輪的共識度權重最高
        recent_rounds = self.round_history[-3:]
        if not recent_rounds:
            return 0.0
        
        total_consensus = sum(r.round_consensus for r in recent_rounds)
        return total_consensus / len(recent_rounds)

    def _calculate_overall_confidence(self) -> float:
        """計算當前整體信心度"""
        if not self.round_history:
            return 0.0
        
        recent_rounds = self.round_history[-3:]
        if not recent_rounds:
            return 0.0
        
        total_confidence = sum(r.average_confidence for r in recent_rounds)
        return total_confidence / len(recent_rounds)

    def get_all_agent_responses(self) -> Dict[str, List[Tuple[int, str]]]:
        """
        取得所有 Agent 跨輪次的回應
        Returns: {agent_id: [(round_num, response_text), ...]}
        """
        responses = {}
        for round_mem in self.round_history:
            for position in round_mem.positions:
                if position.agent_id not in responses:
                    responses[position.agent_id] = []
                responses[position.agent_id].append(
                    (round_mem.round_number, position.response_text)
                )
        return responses

    def get_disagreements_summary(self) -> List[Disagreement]:
        """取得所有檢測到的分歧"""
        all_disagreements = []
        for round_mem in self.round_history:
            all_disagreements.extend(round_mem.disagreements)
        return all_disagreements

    def get_decision_path(self) -> str:
        """生成決策路徑的文本描述"""
        path = f"會議 {self.ticker} 決策路徑：\n"
        for decision in self.decisions:
            path += f"  Round {decision.round_number}: [{decision.source.value}] {decision.action.value} - {decision.reason}\n"
        return path
