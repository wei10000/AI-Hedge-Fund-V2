"""
混合控制工作流引擎 V3 (Adaptive Hybrid Workflow Engine)
選項 C 的完整實現：程式框架 + AI 決策 + 資源感知
"""

import re
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from core.data_models import StockKnowledge, AgentResponse
from core.meeting_context import (
    MeetingContext, RoundMemory, AgentPosition, Decision,
    DecisionActionType, DecisionSource
)
from core.consensus_analyzer import (
    ConsensusCalculator, DisagreementDetector, PositionExtractor
)
from core.resource_monitor import ResourceMonitor, DecisionMaker
from agents.base_agent import BaseAgent
from agents.research import ResearchAgent
from agents.moderator import ModeratorAgent
from agents.auditor_v2 import AuditorAgentV2
from agents.registry import AgentRegistry
from knowledge.builder import KnowledgeBuilder
import uuid


class HybridWorkflowEngineV3:
    """
    混合控制工作流引擎 V3
    
    控制流程：
    - 程式層：定義邊界、監控資源、執行技術操作
    - AI 層：決策流程、判斷共識、識別分歧
    - 混合層：綜合考量
    
    决策层级：
    1. 量化決策（程式做）- 基於閾值
    2. AI 決策（Moderator/CRO 做）- 基於邏輯
    3. 仲裁決策（程式做）- 資源限制優先
    """

    def __init__(self, registry: AgentRegistry, fred_api_key: str = None):
        self.registry = registry
        self.fred_api_key = fred_api_key
        
        # 引擎內建的專家代理
        self.researcher = ResearchAgent(model_name="llama3.1:latest")
        self.moderator = ModeratorAgent(config={
            "id": "Moderator",
            "model": "llama3.1:latest",
            "role_description": "會議主持人"
        })
        self.cro = AuditorAgentV2(config={
            "id": "Auditor",
            "model": "llama3.1:latest",
            "role_description": "最高風控官 (CRO)"
        })
        
        # 資源監控
        self.resource_monitor = ResourceMonitor(
            token_limit=100000,
            time_limit_seconds=3600
        )
        
        # 會議上下文
        self.meeting: Optional[MeetingContext] = None
        self.knowledge: Optional[StockKnowledge] = None
        
        # 配置參數
        self.config = {
            "consensus_threshold": 0.85,
            "token_limit_percent": 0.80,
            "max_rounds": 5,
            "enable_ai_moderator": True,
            "enable_cro_checkpoint": True,
            "enable_auto_data_collection": True,
        }

    def run_analysis(self, ticker: str):
        """
        混合控制主流程
        """
        print("="*70)
        print(" 🚀 AI Hedge Fund OS V3 - 混合控制架構")
        print("="*70)
        
        # ========== PHASE 1: 準備階段（程式控制） ==========
        print("\n📥 [Phase 1] 知識構建...")
        self.knowledge = self._build_knowledge(ticker)
        
        print("🧠 [Phase 2] 初始化會議上下文...")
        self.meeting = MeetingContext(ticker=ticker)
        self.meeting.knowledge = self.knowledge
        
        # ========== PHASE 2: 多輪辯論（混合控制） ==========
        print("⚔️ [Phase 3] 啟動多輪辯論...\n")
        self._run_adaptive_debate()
        
        # ========== PHASE 3: 最終審核和報告（混合控制） ==========
        print("\n🚨 [Phase 4] 最終風控審核...")
        self._final_cro_audit()
        
        print("\n📄 [Phase 5] 生成決策白皮書...")
        self._generate_final_report()
        
        print("\n🎉 [Workflow] 分析流程圓滿結束！")
        print(f"會議狀態: {self.meeting.status}")
        print(f"整體共識度: {self.meeting.overall_consensus:.0%}")
        print(f"決策輪數: {self.meeting.current_round}")

    # ========== 核心決策邏輯 ==========

    def _run_adaptive_debate(self):
        """
        自適應多輪辯論主循環
        
        邏輯流：
        1. 獲取 Moderator 計劃
        2. 執行辯論
        3. 分析共識和分歧
        4. CRO 檢查點
        5. 決策下一步
        """
        
        for round_num in range(1, self.config["max_rounds"] + 1):
            print(f"\n{'='*70}")
            print(f"Round {round_num}/{self.config['max_rounds']}")
            print(f"{'='*70}")
            
            round_start_time = time.time()
            
            # ========== 決策點 1: Moderator 計劃 ==========
            print("\n📋 [AI] Moderator 制定計劃...")
            moderator_plan = self.moderator.decide_round_plan(self.meeting)
            print(f"   → {moderator_plan['focus']}")
            print(f"   → 行動: {moderator_plan['action']}")
            
            # 如果 Moderator 建議結束
            if moderator_plan["action"] == "FINALIZE":
                print("   ✅ 已達共識，進入最終審核")
                decision = self._make_decision(
                    source=DecisionSource.AI_MODERATOR,
                    action=DecisionActionType.FINALIZE,
                    reason=moderator_plan["reason"]
                )
                self.meeting.add_decision(decision)
                break
            
            # ========== 決策點 2: 程式的量化檢查 ==========
            print("\n🤖 [程式] 執行量化檢查...")
            program_decision = self._program_quantitative_check(round_num)
            
            if program_decision:
                print(f"   → {program_decision['action']}: {program_decision['reason']}")
                decision = self._make_decision(
                    source=DecisionSource.PROGRAM,
                    action=program_decision["action"],
                    reason=program_decision["reason"]
                )
                self.meeting.add_decision(decision)
                
                if program_decision["action"] == DecisionActionType.TERMINATE:
                    self.meeting.termination_reason = program_decision["reason"]
                    self.meeting.status = "TERMINATED"
                    break
            
            # ========== 執行辯論 ==========
            print(f"\n💬 [執行] 進行 Round {round_num} 辯論...")
            round_responses = self._execute_debate_round(moderator_plan)
            
            if not round_responses:
                print("   ⚠️ 無 Agent 回應，終止辯論")
                break
            
            # ========== 分析共識和分歧 ==========
            print(f"\n📊 [分析] 計算共識度和分歧...")
            positions = self._extract_positions(round_responses, round_num)
            
            consensus = ConsensusCalculator.calculate_round_consensus(positions)
            disagreements = DisagreementDetector.detect_disagreements(positions)
            
            print(f"   → 共識度: {consensus:.0%}")
            print(f"   → 分歧數: {len(disagreements)}")
            if disagreements:
                for d in disagreements[:2]:
                    print(f"      - {d.description} (嚴重程度: {d.severity:.0%})")
            
            # 記錄這一輪
            round_memory = RoundMemory(
                round_number=round_num,
                start_time=datetime.now(),
                positions=positions,
                disagreements=disagreements,
                debate_topic=moderator_plan.get("focus", "一般辯論"),
                moderator_plan=moderator_plan,
                round_consensus=consensus,
                average_confidence=sum(p.confidence for p in positions) / len(positions) if positions else 0.0
            )
            self.meeting.add_round(round_memory)
            
            # ========== 決策點 3: CRO 檢查點 ==========
            print(f"\n🚨 [AI] CRO 檢查點...")
            cro_verdict = self.cro.checkpoint(self.meeting)
            print(f"   → {cro_verdict['action']}: {cro_verdict['reason']}")
            
            self.meeting.add_cro_decision(cro_verdict)
            
            if cro_verdict["action"] == "REQUEST_DATA":
                # 自動補充數據
                print(f"   📋 要求補充數據: {cro_verdict['missing_info']}")
                if self.config["enable_auto_data_collection"]:
                    print("   ⏳ 自動補充數據中...")
                    self._collect_additional_data(cro_verdict["missing_info"])
                # 繼續下一輪
                
            elif cro_verdict["action"] == "TERMINATE":
                print(f"   ❌ CRO 叫停分析")
                decision = self._make_decision(
                    source=DecisionSource.AI_CRO,
                    action=DecisionActionType.TERMINATE,
                    reason=cro_verdict["reason"]
                )
                self.meeting.add_decision(decision)
                self.meeting.termination_reason = cro_verdict["reason"]
                self.meeting.status = "TERMINATED"
                break
            
            # 記錄耗時和資源
            round_duration = time.time() - round_start_time
            estimated_tokens = sum(
                self.resource_monitor.estimate_tokens(p.response_text)
                for p in positions
            )
            
            self.resource_monitor.record_round_tokens(estimated_tokens)
            self.resource_monitor.record_round_time(round_duration)
            
            # 打印資源狀態
            self.resource_monitor.print_status()
            
            # 暫停讓用戶看到進度
            print("\n", end="")

    # ========== 輔助方法 ==========

    def _program_quantitative_check(self, round_num: int) -> Optional[Dict]:
        """
        程式層的量化檢查
        
        檢查項：
        1. 共識度是否達到閾值
        2. Token 是否超過限制
        3. 輪數是否達到上限
        """
        
        if not self.meeting.round_history:
            return None
        
        latest_round = self.meeting.round_history[-1]
        
        # 檢查 1: 共識度
        if latest_round.round_consensus > self.config["consensus_threshold"]:
            return {
                "action": DecisionActionType.FINALIZE,
                "reason": f"共識度 {latest_round.round_consensus:.0%} 已超過閾值 {self.config['consensus_threshold']:.0%}"
            }
        
        # 檢查 2: Token 限制
        if self.resource_monitor.get_token_usage_percent() > self.config["token_limit_percent"]:
            action = DecisionMaker.get_emergency_action(self.resource_monitor)
            if action == "FORCE_TERMINATE":
                return {
                    "action": DecisionActionType.TERMINATE,
                    "reason": f"Token 消耗達 {self.resource_monitor.get_token_usage_percent():.0%}，強制終止"
                }
            elif action == "SKIP_ROUNDS":
                return {
                    "action": DecisionActionType.FINALIZE,
                    "reason": f"Token 消耗達 {self.resource_monitor.get_token_usage_percent():.0%}，進入快速收尾"
                }
        
        # 檢查 3: 輪數上限
        if round_num >= self.config["max_rounds"]:
            return {
                "action": DecisionActionType.FINALIZE,
                "reason": f"已達最大輪數 {self.config['max_rounds']}"
            }
        
        return None

    def _execute_debate_round(self, moderator_plan: Dict) -> List[Tuple[str, AgentResponse]]:
        """
        執行一輪辯論
        
        Returns: [(agent_id, response), ...]
        """
        debate_agents = self.registry.get_debate_agents()
        responses = []
        
        for agent in debate_agents:
            print(f"\n  👉 {agent.role_description} 發言...")
            
            context = agent.prepare(self.knowledge)
            user_query = moderator_plan.get("focus", "請根據你的專業領域給出分析")
            
            # 執行 ReAct 迴圈（原有的工具調用邏輯）
            response = self._agent_think_with_tools(agent, context, user_query)
            
            if response:
                responses.append((agent.id, response))
                print(f"  ✔️ {agent.name} 完成 (信心: {response.self_confidence:.0%})")
        
        return responses

    def _agent_think_with_tools(self, agent: BaseAgent, context: str, query: str) -> Optional[AgentResponse]:
        """
        Agent 的思考過程，包含工具調用（原有的 ReAct 邏輯）
        """
        max_loops = 3
        current_history = context
        searched_queries = set()
        
        for step in range(max_loops):
            response = agent.think(current_history, query)
            resp_text = response.response_text
            
            # 攔截工具呼叫
            tool_called = False
            read_match = re.search(r"<READ_FILE>(.*?)\|(.*?)</READ_FILE>", resp_text, re.IGNORECASE)
            
            if read_match:
                filepath = read_match.group(1).strip()
                keyword = read_match.group(2).strip()
                query_key = f"{filepath}|{keyword}"
                
                if query_key in searched_queries:
                    print(f"    ⚠️ [防重複] 跳過重複查詢")
                    tool_result = "〔系統警告：已查閱過相同關鍵字〕"
                else:
                    searched_queries.add(query_key)
                    tool_result = self.researcher.execute_tool("READ_FILE", query_key)
                
                cleaned_resp = re.sub(r"<READ_FILE>.*?</READ_FILE>", "[已執行檔案查閱]", resp_text, flags=re.IGNORECASE)
                current_history += f"\n[查閱結果]：\n{tool_result}\n👉 請繼續分析。"
                tool_called = True
            
            if not tool_called:
                is_valid = agent.validate(response)
                if not is_valid:
                    response.self_confidence -= 0.3
                return response
        
        # 達到最大迴圈
        return response

    def _extract_positions(self, responses: List[Tuple[str, AgentResponse]], round_num: int) -> List[AgentPosition]:
        """
        從 Agent 回應中提取結構化立場
        """
        positions = []
        for agent_id, response in responses:
            position = PositionExtractor.extract_position(response, agent_id, round_num)
            positions.append(position)
        return positions

    def _make_decision(self, 
                      source: DecisionSource,
                      action: DecisionActionType,
                      reason: str,
                      data: Optional[Dict] = None) -> Decision:
        """
        生成決策記錄
        """
        return Decision(
            decision_id=f"dec_{uuid.uuid4().hex[:8]}",
            round_number=self.meeting.current_round,
            decision_maker=source.value,
            source=source,
            action=action,
            reason=reason,
            data=data or {}
        )

    def _collect_additional_data(self, data_requests: List[str]):
        """
        自動補充數據
        """
        for request in data_requests:
            print(f"  📋 補充: {request}")
            # 這裡可以接入真實的數據源
            self.meeting.data_requests.append(request)
            self.meeting.collected_data[request] = f"[補充數據] {request}"

    def _final_cro_audit(self):
        """
        最終風控審核
        """
        if not self.meeting.round_history:
            print("   ℹ️ 無辯論記錄，跳過審核")
            return
        
        cro = self.registry.get_agent("Auditor")
        if cro:
            history_text = "\n".join([
                f"{r.agent_name}: {r.response_text}"
                for round_mem in self.meeting.round_history
                for r in [PositionExtractor.extract_position(
                    AgentResponse(
                        agent_name=p.agent_name,
                        role=p.agent_name,
                        response_text=p.response_text,
                        self_confidence=p.confidence
                    ),
                    p.agent_id,
                    round_mem.round_number
                ) for p in round_mem.positions]
            ])
            
            resp = cro.think("", history_text)
            print(f"\n🚨 [CRO 最終判決]:\n{resp.response_text}")

    def _generate_final_report(self):
        """
        生成最終決策白皮書
        """
        advisor = self.registry.get_agent("Advisor")
        if advisor:
            history_text = "\n".join([
                f"{r.agent_name}: {r.response_text}"
                for round_mem in self.meeting.round_history
                for r in [PositionExtractor.extract_position(
                    AgentResponse(
                        agent_name=p.agent_name,
                        role=p.agent_name,
                        response_text=p.response_text,
                        self_confidence=p.confidence
                    ),
                    p.agent_id,
                    round_mem.round_number
                ) for p in round_mem.positions]
            ])
            
            context = advisor.prepare(self.knowledge)
            resp = advisor.think(context, history_text)
            
            print("\n" + "="*70)
            print(f"📊 【{self.knowledge.company.ticker}】最終決策白皮書")
            print("="*70)
            print(resp.response_text)
            print("="*70 + "\n")

    def _build_knowledge(self, ticker: str) -> StockKnowledge:
        """構建知識庫"""
        builder = KnowledgeBuilder(fred_api_key=self.fred_api_key)
        return builder.build(ticker)
