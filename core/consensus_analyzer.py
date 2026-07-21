"""
共識度和分歧檢測器 (Consensus Calculator & Disagreement Detector)
分析 Agent 之間的一致性和分歧
"""

from typing import List, Dict, Tuple
from core.meeting_context import AgentPosition, Disagreement
from core.data_models import AgentResponse
import re


class ConsensusCalculator:
    """計算會議的共識度和一致性指標"""

    @staticmethod
    def calculate_round_consensus(positions: List[AgentPosition]) -> float:
        """
        計算某一輪的共識度 (0-1)
        
        邏輯：
        - 如果所有 Agent 立場相同：1.0（完全共識）
        - 如果有對立立場：降低分數
        - 考慮信心分：高信心的共識更有權重
        """
        if not positions:
            return 0.0

        # 統計立場分布
        bullish_count = sum(1 for p in positions if p.position == "BULLISH")
        bearish_count = sum(1 for p in positions if p.position == "BEARISH")
        neutral_count = sum(1 for p in positions if p.position == "NEUTRAL")
        
        total = len(positions)
        
        # 計算多數派
        max_count = max(bullish_count, bearish_count, neutral_count)
        majority_percent = max_count / total
        
        # 如果有完全對立（既有看多也有看空）
        if bullish_count > 0 and bearish_count > 0:
            # 對立降分
            opposition_penalty = min(bullish_count, bearish_count) / total * 0.5
            base_consensus = majority_percent - opposition_penalty
        else:
            base_consensus = majority_percent
        
        # 加入信心分權重
        avg_confidence = sum(p.confidence for p in positions) / total
        weighted_consensus = base_consensus * 0.7 + avg_confidence * 0.3
        
        return min(1.0, max(0.0, weighted_consensus))

    @staticmethod
    def calculate_confidence_trend(positions_history: List[List[AgentPosition]]) -> Dict:
        """
        分析信心分的趨勢
        
        Returns:
        {
            "trend": "UP" | "DOWN" | "STABLE",
            "current": 0.85,
            "previous": 0.80,
            "direction": 0.05
        }
        """
        if len(positions_history) < 2:
            return {
                "trend": "STABLE",
                "current": 0.0,
                "previous": 0.0,
                "direction": 0.0
            }

        # 計算最後兩輪的平均信心分
        latest_positions = positions_history[-1]
        previous_positions = positions_history[-2]

        latest_avg = sum(p.confidence for p in latest_positions) / len(latest_positions) if latest_positions else 0
        previous_avg = sum(p.confidence for p in previous_positions) / len(previous_positions) if previous_positions else 0

        direction = latest_avg - previous_avg

        if abs(direction) < 0.05:
            trend = "STABLE"
        elif direction > 0:
            trend = "UP"
        else:
            trend = "DOWN"

        return {
            "trend": trend,
            "current": latest_avg,
            "previous": previous_avg,
            "direction": direction
        }

    @staticmethod
    def calculate_agreement_score(position_1: AgentPosition, position_2: AgentPosition) -> float:
        """
        計算兩個 Agent 之間的一致性分數 (0-1)
        
        - 1.0: 完全一致（立場相同 + 信心接近）
        - 0.0: 完全相反
        """
        # 立場匹配
        if position_1.position == position_2.position:
            stance_match = 1.0
        elif (position_1.position == "NEUTRAL" or position_2.position == "NEUTRAL"):
            stance_match = 0.5
        else:
            # 完全相反
            stance_match = 0.0

        # 信心分接近度
        confidence_diff = abs(position_1.confidence - position_2.confidence)
        confidence_match = max(0.0, 1.0 - confidence_diff)

        # 加權平均
        agreement = stance_match * 0.6 + confidence_match * 0.4

        return agreement


class DisagreementDetector:
    """偵測和分析 Agent 之間的分歧"""

    @staticmethod
    def detect_disagreements(positions: List[AgentPosition], threshold: float = 0.3) -> List[Disagreement]:
        """
        檢測本輪中的重大分歧
        
        Args:
            positions: 該輪所有 Agent 的立場
            threshold: 分歧嚴重程度的閾值 (0-1)
        
        Returns:
            List of Disagreement objects
        """
        disagreements = []

        # 兩兩比較
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                pos_i = positions[i]
                pos_j = positions[j]

                agreement_score = ConsensusCalculator.calculate_agreement_score(pos_i, pos_j)
                severity = 1.0 - agreement_score

                # 如果分歧嚴重程度超過閾值，記錄下來
                if severity >= threshold:
                    disagreement_type = DisagreementDetector._classify_disagreement(pos_i, pos_j)
                    
                    disagreement = Disagreement(
                        agent_1_id=pos_i.agent_id,
                        agent_2_id=pos_j.agent_id,
                        disagreement_type=disagreement_type,
                        severity=severity,
                        description=DisagreementDetector._describe_disagreement(pos_i, pos_j),
                        suggested_clarification=DisagreementDetector._suggest_clarification(pos_i, pos_j)
                    )
                    disagreements.append(disagreement)

        return disagreements

    @staticmethod
    def _classify_disagreement(pos_1: AgentPosition, pos_2: AgentPosition) -> str:
        """分類分歧類型"""
        if pos_1.position == pos_2.position:
            return "COMPLEMENTARY"  # 立場相同但論點互補
        elif (pos_1.position == "NEUTRAL" or pos_2.position == "NEUTRAL"):
            return "UNCLEAR"  # 一方態度不明確
        else:
            return "OPPOSITE"  # 完全對立

    @staticmethod
    def _describe_disagreement(pos_1: AgentPosition, pos_2: AgentPosition) -> str:
        """生成分歧的文本描述"""
        agent_1_role = pos_1.agent_name
        agent_2_role = pos_2.agent_name
        
        if pos_1.position == "BULLISH" and pos_2.position == "BEARISH":
            return f"{agent_1_role} 看多（信心 {pos_1.confidence:.0%}）vs {agent_2_role} 看空（信心 {pos_2.confidence:.0%}）"
        elif pos_1.position == "BEARISH" and pos_2.position == "BULLISH":
            return f"{agent_1_role} 看空（信心 {pos_1.confidence:.0%}）vs {agent_2_role} 看多（信心 {pos_2.confidence:.0%}）"
        else:
            return f"{agent_1_role} ({pos_1.position}) vs {agent_2_role} ({pos_2.position})"

    @staticmethod
    def _suggest_clarification(pos_1: AgentPosition, pos_2: AgentPosition) -> str:
        """建議澄清問題"""
        agent_1_role = pos_1.agent_name
        agent_2_role = pos_2.agent_name
        
        return f"為何 {agent_1_role} 與 {agent_2_role} 的結論相反？哪一方忽視了關鍵數據？"

    @staticmethod
    def detect_major_disagreements(positions: List[AgentPosition]) -> bool:
        """
        判斷是否存在重大分歧
        
        標準：存在「相反」的分歧且嚴重程度 >= 0.5
        """
        disagreements = DisagreementDetector.detect_disagreements(positions, threshold=0.4)
        
        for d in disagreements:
            if d.disagreement_type == "OPPOSITE" and d.severity >= 0.5:
                return True
        
        return False

    @staticmethod
    def get_consensus_breakdown(positions: List[AgentPosition]) -> Dict[str, int]:
        """
        取得立場分佈
        
        Returns:
        {
            "BULLISH": 2,
            "BEARISH": 1,
            "NEUTRAL": 0
        }
        """
        breakdown = {
            "BULLISH": sum(1 for p in positions if p.position == "BULLISH"),
            "BEARISH": sum(1 for p in positions if p.position == "BEARISH"),
            "NEUTRAL": sum(1 for p in positions if p.position == "NEUTRAL")
        }
        return breakdown


class PositionExtractor:
    """從 AgentResponse 中提取結構化的立場"""

    @staticmethod
    def extract_position(response: AgentResponse, agent_id: str, round_num: int) -> AgentPosition:
        """
        從 Agent 的回應中提取立場
        
        邏輯：
        1. 搜尋關鍵詞（買入、賣出、持守等）
        2. 嘗試提取信心分（如果有）
        3. 提取核心論點
        """
        response_text = response.response_text.lower()
        
        # 立場檢測
        if any(keyword in response_text for keyword in ["買入", "看多", "推薦", "positive", "bullish", "upside"]):
            position = "BULLISH"
        elif any(keyword in response_text for keyword in ["賣出", "看空", "避免", "negative", "bearish", "downside"]):
            position = "BEARISH"
        else:
            position = "NEUTRAL"
        
        # 信心分提取（如果 AgentResponse 中有則用，否則用默認值）
        confidence = response.self_confidence if hasattr(response, 'self_confidence') else 0.7
        
        # 核心論點提取（取前 100 字）
        key_argument = response_text[:100] if response_text else "無明確論點"
        
        return AgentPosition(
            agent_id=agent_id,
            agent_name=response.agent_name,
            round_number=round_num,
            position=position,
            confidence=confidence,
            key_argument=key_argument,
            response_text=response.response_text,
            cited_data=PositionExtractor._extract_data_citations(response.response_text)
        )

    @staticmethod
    def _extract_data_citations(text: str) -> List[str]:
        """從文本中提取被引用的數據"""
        citations = []
        
        # 搜尋常見的數據模式
        patterns = [
            r"營收[\s:]*[\$￥]?[\d,\.]+",
            r"淨利[\s:]*[\$￥]?[\d,\.]+",
            r"PE[\s:]*[\d,\.]+",
            r"PEG[\s:]*[\d,\.]+",
            r"增長[\s:]*[\d,\.]+%",
            r"現價[\s:]*[\$￥][\d,\.]+",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return list(set(citations))  # 去重
