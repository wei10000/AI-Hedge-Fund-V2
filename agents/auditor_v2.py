"""
改進的 CRO Agent - 風控官
升級功能：主動決策流程、要求補充數據、自動恢復
"""

import ollama
from typing import Dict, Optional
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse
from core.meeting_context import MeetingContext, DecisionActionType, DecisionSource, Decision
import uuid


class AuditorAgentV2(BaseAgent):
    """
    改進版風控官 (Chief Risk Officer, CRO) - V2
    
    升級功能：
    1. 主動決策：決定流程是否繼續、何時叫停
    2. 智能審核：不只檢查矛盾，還分析風險
    3. 數據補充：自動識別缺失的關鍵信息
    4. 決策追蹤：記錄所有決策和理由
    """

    def __init__(self, config: dict):
        super().__init__(config)

    def prepare(self, knowledge: StockKnowledge) -> str:
        return f"""【風控官準備就緒】
分析標的: {knowledge.company.ticker}
當前現價: ${knowledge.technicals.current_price:.2f}

風控官職責：
1. 審核專家意見的邏輯一致性
2. 識別關鍵數據缺失
3. 評估分析質量和可信度
4. 決定流程走向（繼續/叫停/補充數據）
"""

    def checkpoint(self, meeting: MeetingContext) -> Dict:
        """
        CRO 在關鍵節點的檢查點決策
        
        Returns:
        {
            "action": "CONTINUE" | "TERMINATE" | "REQUEST_DATA",
            "reason": "...",
            "severity": 0-1,
            "missing_info": ["info1", "info2"],  # 如果 action == REQUEST_DATA
            "risk_factors": ["risk1", "risk2"]   # 識別的風險因子
        }
        """
        
        if not meeting.round_history:
            return {"action": "CONTINUE", "reason": "首輪辯論，無法審核"}
        
        latest_round = meeting.round_history[-1]
        
        # ========== 檢查 1: 邏輯一致性 ==========
        consistency_issues = self._check_consistency(latest_round.positions)
        
        if consistency_issues and consistency_issues["severity"] > 0.7:
            return {
                "action": "TERMINATE",
                "reason": f"發現嚴重邏輯矛盾: {consistency_issues['description']}",
                "severity": consistency_issues["severity"],
                "risk_factors": consistency_issues["factors"]
            }
        
        # ========== 檢查 2: 數據完整性 ==========
        missing_data = self._identify_missing_data(latest_round.positions, meeting)
        
        if missing_data:
            return {
                "action": "REQUEST_DATA",
                "reason": f"缺失關鍵信息，需要補充調查",
                "severity": missing_data["severity"],
                "missing_info": missing_data["items"]
            }
        
        # ========== 檢查 3: 共識質量 ==========
        if meeting.overall_consensus < 0.6 and meeting.current_round > 3:
            return {
                "action": "TERMINATE",
                "reason": f"經過多輪討論仍未達成共識 (共識度 {meeting.overall_consensus:.0%})，可能存在結構性分歧",
                "severity": 0.6,
                "risk_factors": ["結構性分歧", "信息不對稱"]
            }
        
        # ========== 檢查 4: 信心分下降 ==========
        if meeting.round_history and len(meeting.round_history) > 1:
            prev_conf = meeting.round_history[-2].average_confidence
            curr_conf = latest_round.average_confidence
            
            if curr_conf < prev_conf - 0.15:
                return {
                    "action": "REQUEST_DATA",
                    "reason": f"整體信心分下降明顯 ({prev_conf:.0%} → {curr_conf:.0%})，需要更多數據支持",
                    "severity": 0.5,
                    "missing_info": ["更詳細的基本面分析", "技術面強度驗證"]
                }
        
        # 通過檢查
        return {
            "action": "CONTINUE",
            "reason": "未發現重大風險，可繼續進行",
            "severity": 0.0
        }

    def think(self, context: str, debate_history: str) -> AgentResponse:
        """
        CRO 的推理方法（升級版，更詳細的分析）
        """
        system_prompt = f"""你是{self.role_description}。
{context}

【會議紀錄】：
{debate_history}

【CRO 審核任務】：
1. 分析各專家的論點是否存在邏輯矛盾或數據錯誤
2. 識別是否存在「過度自信」或「信息缺失」
3. 評估結論的風險程度 (LOW | MEDIUM | HIGH)
4. 如果發現問題，提出具體改進建議

請給出結構化的審核意見：
【發現的問題】(如無則說「無重大問題」)
【風險程度】
【建議】
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
                response_text=f"審核失敗: {e}",
                self_confidence=0.0
            )

    def validate(self, response: AgentResponse) -> bool:
        return True

    # ========== 內部檢查方法 ==========

    def _check_consistency(self, positions) -> Dict:
        """
        檢查邏輯一致性
        
        返回:
        {
            "severity": 0-1,
            "description": "...",
            "factors": ["factor1", "factor2"]
        }
        """
        from core.consensus_analyzer import DisagreementDetector, ConsensusCalculator
        
        disagreements = DisagreementDetector.detect_disagreements(positions, threshold=0.3)
        major_disagreements = [d for d in disagreements if d.disagreement_type == "OPPOSITE" and d.severity > 0.7]
        
        if not major_disagreements:
            return None
        
        # 如果存在多個嚴重對立，標記為高風險
        if len(major_disagreements) > 1:
            return {
                "severity": 0.8,
                "description": f"檢測到 {len(major_disagreements)} 個嚴重對立意見",
                "factors": [d.description for d in major_disagreements]
            }
        
        return {
            "severity": major_disagreements[0].severity,
            "description": major_disagreements[0].description,
            "factors": [major_disagreements[0].description]
        }

    def _identify_missing_data(self, positions, meeting: MeetingContext) -> Optional[Dict]:
        """
        識別缺失的關鍵數據
        
        返回:
        {
            "severity": 0-1,
            "items": ["missing_data_1", "missing_data_2"]
        }
        """
        missing = []
        
        # 檢查基本面數據
        if meeting.knowledge and meeting.knowledge.financials:
            fin = meeting.knowledge.financials
            if not fin.revenue_ttm or not fin.net_income:
                missing.append("完整的財務指標 (營收、淨利)")
            if not fin.fcf_normalized:
                missing.append("自由現金流數據")
        
        # 檢查技術面數據
        if meeting.knowledge and meeting.knowledge.technicals:
            tech = meeting.knowledge.technicals
            if not tech.ma_20 or not tech.ma_50:
                missing.append("均線數據驗證")
            if not tech.atr_14:
                missing.append("ATR 波動率數據")
        
        # 檢查宏觀數據
        if meeting.knowledge and meeting.knowledge.macro:
            macro = meeting.knowledge.macro
            if not macro.effr or not macro.yield_10y:
                missing.append("最新的宏觀經濟指標")
        
        # 檢查新聞和催化劑
        if not meeting.knowledge.news_summary or len(meeting.knowledge.news_summary) == 0:
            missing.append("最新的行業新聞和催化劑")
        
        if missing:
            return {
                "severity": min(0.6, len(missing) * 0.2),
                "items": missing
            }
        
        return None

    def create_audit_report(self, meeting: MeetingContext) -> str:
        """
        生成完整的審核報告
        """
        report = f"""
{'='*70}
【CRO 審核報告】- {meeting.ticker}
{'='*70}

⏰ 審核時間: Round {meeting.current_round} / {meeting.max_rounds}

📊 會議狀態:
  - 整體共識度: {meeting.overall_consensus:.0%}
  - 整體信心分: {meeting.overall_confidence:.0%}
  - 輪次進度: {meeting.current_round}/{meeting.max_rounds}

🔍 CRO 決策記錄:
"""
        
        for decision in meeting.cro_decisions:
            report += f"  - {decision['timestamp']}: {decision.get('action', 'N/A')} - {decision.get('reason', 'N/A')}\n"
        
        if not meeting.cro_decisions:
            report += "  - 無決策記錄\n"
        
        report += f"\n⚠️ 識別的風險因子:\n"
        
        disagreements = meeting.get_disagreements_summary()
        if disagreements:
            for d in disagreements:
                if d.severity >= 0.5:
                    report += f"  - {d.description} (嚴重程度: {d.severity:.0%})\n"
        
        if meeting.data_requests:
            report += f"\n📋 補充數據請求:\n"
            for req in meeting.data_requests:
                report += f"  - {req}\n"
                if req in meeting.collected_data:
                    report += f"    ✅ 已補充: {meeting.collected_data[req][:50]}...\n"
                else:
                    report += f"    ⏳ 待補充\n"
        
        report += f"\n{'='*70}\n"
        
        return report
