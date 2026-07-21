"""
Moderator Agent - 會議主持人
負責管理辯論流程、決定參與者、提出澄清問題、判斷共識度
"""

import ollama
from typing import Dict, List, Optional
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse
from core.meeting_context import MeetingContext, DecisionActionType, DecisionSource, Decision
from core.consensus_analyzer import ConsensusCalculator, DisagreementDetector
import json


class ModeratorAgent(BaseAgent):
    """
    會議主持人 (Moderator / Meeting Facilitator)
    
    職責：
    1. 決定每一輪誰發言、討論什麼
    2. 監測共識度和分歧
    3. 提出澄清問題，深化討論
    4. 決定何時進入最終階段
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.config = config or {
            "id": "Moderator",
            "role_description": "會議主持人，負責協調專家意見並推動共識形成。"
        }

    def prepare(self, knowledge: StockKnowledge) -> str:
        """
        Moderator 不直接分析數據，而是協調和管理流程
        """
        return f"""【主持人準備就緒】
分析標的: {knowledge.company.ticker}
現價: ${knowledge.technicals.current_price:.2f}

主持人職責：
1. 監測各專家的共識度
2. 偵測重大分歧
3. 提出澄清性問題
4. 決定流程走向
"""

    def decide_round_plan(self, meeting: MeetingContext) -> Dict:
        """
        根據當前會議狀態，決定下一輪的計劃
        
        Returns:
        {
            "action": "DEBATE" | "CLARIFY" | "DEEPEN" | "FINALIZE",
            "participants": ["Agent_1", "Agent_2"],
            "focus": "討論焦點",
            "reason": "決策理由"
        }
        """
        
        # 分析當前狀態
        current_consensus = meeting.overall_consensus
        disagreements = meeting.get_disagreements_summary()
        major_disagreements = any(d.severity >= 0.5 for d in disagreements)
        
        # 決策邏輯
        if current_consensus > 0.85:
            # 已達高度共識
            return {
                "action": "FINALIZE",
                "participants": [],
                "focus": "已達共識，進入最終審核",
                "reason": f"共識度 {current_consensus:.0%} 已超過閾值"
            }
        
        elif major_disagreements and meeting.current_round < 3:
            # 存在重大分歧，需要深化討論
            primary_disagreements = [d for d in disagreements if d.severity >= 0.5]
            if primary_disagreements:
                d = primary_disagreements[0]
                return {
                    "action": "CLARIFY",
                    "participants": [d.agent_1_id, d.agent_2_id],
                    "focus": f"澄清分歧：{d.description}",
                    "reason": f"檢測到重大分歧 (嚴重程度 {d.severity:.0%})",
                    "clarification_question": d.suggested_clarification
                }
        
        elif meeting.current_round >= meeting.max_rounds - 1:
            # 接近最大輪數，準備結束
            return {
                "action": "FINALIZE",
                "participants": [],
                "focus": "達到最大輪數，進入最終階段",
                "reason": f"已進行 {meeting.current_round} 輪，接近上限"
            }
        
        else:
            # 常規辯論
            return {
                "action": "DEBATE",
                "participants": "ALL",
                "focus": f"第 {meeting.current_round + 1} 輪常規辯論",
                "reason": f"共識度 {current_consensus:.0%}，繼續討論"
            }

    def assess_continuation(self, meeting: MeetingContext) -> Dict:
        """
        Moderator 評估是否應繼續辯論或進入下一階段
        
        Returns:
        {
            "should_continue": True | False,
            "reason": "...",
            "recommendation": "CONTINUE" | "DEEPEN" | "FINALIZE"
        }
        """
        
        current_consensus = meeting.overall_consensus
        confidence_trend = ConsensusCalculator.calculate_confidence_trend(
            [r.positions for r in meeting.round_history]
        )
        
        # 檢查是否進展停滯
        if confidence_trend["trend"] == "DOWN" and meeting.current_round > 2:
            return {
                "should_continue": False,
                "reason": "信心分呈下降趨勢，辯論陷入困境",
                "recommendation": "FINALIZE"
            }
        
        # 檢查是否已收斂
        if current_consensus > 0.80 or confidence_trend["trend"] == "STABLE":
            return {
                "should_continue": False,
                "reason": "共識度已達理想水平或進展停滯",
                "recommendation": "FINALIZE"
            }
        
        return {
            "should_continue": True,
            "reason": f"共識度 {current_consensus:.0%}，信心分趨勢 {confidence_trend['trend']}",
            "recommendation": "CONTINUE"
        }

    def think(self, context: str, debate_state: str) -> AgentResponse:
        """
        Moderator 的推理方法
        
        這裡用 LLM 生成更自然的主持人評論
        """
        system_prompt = f"""你是{self.role_description}。
{context}

當前會議狀態：
{debate_state}

【任務】：
請作為主持人提供你的觀察和建議：
1. 各專家的主要分歧點是什麼？
2. 目前的共識程度如何？
3. 是否需要進一步討論？若需要，建議討論什麼？
4. 你認為何時適合進入最終決策階段？

請直接給出結構化的評估，不要客套話。
"""
        
        try:
            res = ollama.generate(model=self.model_name, prompt=system_prompt)
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text=res['response'].strip(),
                self_confidence=0.95
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name,
                role=self.role_description,
                response_text=f"主持人評估失敗: {e}",
                self_confidence=0.0
            )

    def validate(self, response: AgentResponse) -> bool:
        """Moderator 的回應通常總是有效的"""
        return True

    def generate_clarification_questions(self, 
                                        agent_1_name: str, 
                                        agent_2_name: str,
                                        disagreement: str) -> List[str]:
        """
        根據分歧生成澄清問題
        """
        questions = [
            f"{agent_1_name}，你的結論是否考慮了{agent_2_name}提出的{disagreement}？",
            f"{agent_2_name}，你能否詳細解釋為什麼不同意{agent_1_name}的觀點？",
            f"雙方能否指出對方論證中最薄弱的環節？",
            f"是否存在某些關鍵數據是一方遺漏而另一方掌握的？"
        ]
        return questions

    def create_meeting_summary(self, meeting: MeetingContext) -> str:
        """
        生成會議摘要
        """
        summary = f"""
{'='*60}
會議摘要 - {meeting.ticker}
{'='*60}

📊 整體狀態:
  - 當前輪數: {meeting.current_round}/{meeting.max_rounds}
  - 整體共識度: {meeting.overall_consensus:.0%}
  - 整體信心分: {meeting.overall_confidence:.0%}
  - 會議狀態: {meeting.status}

🔍 立場分佈:
"""
        
        if meeting.round_history:
            latest_round = meeting.round_history[-1]
            breakdown = DisagreementDetector.get_consensus_breakdown(latest_round.positions)
            summary += f"  - 看多: {breakdown['BULLISH']} 位\n"
            summary += f"  - 看空: {breakdown['BEARISH']} 位\n"
            summary += f"  - 中立: {breakdown['NEUTRAL']} 位\n"
        
        summary += f"\n⚡ 重大分歧:\n"
        disagreements = meeting.get_disagreements_summary()
        if disagreements:
            for d in disagreements:
                if d.severity >= 0.5:
                    summary += f"  - {d.description} (嚴重程度: {d.severity:.0%})\n"
        else:
            summary += f"  - 無重大分歧\n"
        
        summary += f"\n📋 決策路徑:\n"
        for decision in meeting.decisions[-3:]:  # 最後3個決策
            summary += f"  - Round {decision.round_number}: [{decision.source.value}] {decision.action.value}\n"
        
        summary += f"\n{'='*60}\n"
        
        return summary
