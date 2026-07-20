import re
from typing import List, Dict
from core.data_models import StockKnowledge, MeetingRound, DebateMemory, AgentResponse
from agents.base_agent import BaseAgent
from agents.research import ResearchAgent
from knowledge.builder import KnowledgeBuilder
from agents.registry import AgentRegistry

class WorkflowEngine:
    """
    會議主控台 (Workflow Orchestrator)。
    V2 終極型態：具備 ReAct 動態路由攔截能力！
    """
    def __init__(self, registry: AgentRegistry, fred_api_key: str = None):
        self.registry = registry
        self.fred_api_key = fred_api_key
        
        # 引擎內建一個專屬的探險家！
        self.researcher = ResearchAgent(model_name="llama3.1:latest")
        
        self.debate_history: List[AgentResponse] = []
        self.knowledge: StockKnowledge = None
        self.cro_decision: str = ""

    def run_analysis(self, ticker: str):
        print(f"\n🚀 啟動 AI Hedge Fund OS 分析流程 - 標的: {ticker}")
        
        print("📥 [Step 1] 正在組裝結構化知識庫 (Knowledge Builder)...")
        self.knowledge = self._build_knowledge(ticker)
        
        print("⚔️ [Step 2] 啟動多代理人交叉辯論 (具備動態路由攔截)...")
        self._run_debate()
        
        print("🚨 [Step 3] 最高風控官審核中 (CRO Audit)...")
        self._audit_debate()
        
        print("📄 [Step 4] 首席顧問撰寫決策白皮書 (Whitepaper Generation)...")
        self._generate_report()

        print("\n🎉 [Workflow] 分析流程圓滿結束！")

    def _build_knowledge(self, ticker: str) -> StockKnowledge:
        builder = KnowledgeBuilder(fred_api_key=self.fred_api_key)
        return builder.build(ticker)

    def _run_debate(self):
        debate_agents = self.registry.get_debate_agents()
        
        for agent in debate_agents:
            print(f"\n  👉 換 {agent.role_description} 發言...")
            
            context = agent.prepare(self.knowledge)
            user_query = "請根據你的專業領域，給出對該標的的核心量化結論與防守點位建議。"
            
            # 🔥 Agentic Routing (動態路由迴圈)
            # 給予每個專家最多 3 次呼叫工具的機會
            max_loops = 3
            current_history = context
            searched_queries = set() # 🚀 新增：用來記錄這個專家在這輪查過什麼
            
            for step in range(max_loops):
                response = agent.think(current_history, user_query)
                resp_text = response.response_text
                
                # 攔截工具呼叫指令
                tool_called = False
                read_match = re.search(r"<READ_FILE>(.*?)\|(.*?)</READ_FILE>", resp_text, re.IGNORECASE)
                
                if read_match:
                    filepath = read_match.group(1).strip()
                    keyword = read_match.group(2).strip()
                    query_key = f"{filepath}|{keyword}"
                    
                    # 🚀 防鬼打牆機制：檢查是否查過一樣的東西
                    if query_key in searched_queries:
                        print(f"    ⚠️ [Engine 攔截] 發現 {agent.name} 鬼打牆重複搜尋 '{keyword}'！")
                        tool_result = "〔系統警告：你剛才已經查閱過相同的關鍵字了！請停止重複搜尋，根據現有數據給出結論，或搜尋『不同』的關鍵字。〕"
                    else:
                        searched_queries.add(query_key)
                        print(f"    ⏸️ [Engine 攔截] 發現 {agent.name} 請求查閱檔案 {filepath} 尋找 '{keyword}'...")
                        
                        # 將任務轉發給專屬探險家 (Research Agent)
                        tool_result = self.researcher.execute_tool("READ_FILE", query_key)
                        print(f"    🕵️‍♂️ [Research Agent] 探勘完畢，已將數據返回記憶體。")
                    
                    # 🚀 遮蔽魔法：把 LLM 剛才輸出的 XML 標籤「拔掉」，防止它模仿自己！
                    cleaned_resp = re.sub(r"<READ_FILE>.*?</READ_FILE>", "[已執行檔案查閱指令]", resp_text, flags=re.IGNORECASE)
                    
                    # 將結果塞回 Context，讓 Agent 下一個迴圈重新思考
                    current_history += f"\n\n[你的上一步思考]：{cleaned_resp}\n[探險家回傳數據]：\n{tool_result}\n👉 請繼續分析。若需其他不同數據可再次呼叫，若資訊已足夠，請直接給出『量化結論』。"
                    tool_called = True
                
                # 如果這回合沒有呼叫工具，代表專家已經得出最終結論，跳出迴圈
                if not tool_called:
                    is_valid = agent.validate(response)
                    if not is_valid:
                        response.self_confidence -= 0.3
                        response.response_text = f"【驗證未通過，可能有越界或幻覺】\n{resp_text}"
                    self.debate_history.append(response)
                    print(f"  ✔️ {agent.name} 產出完成。(信心分數: {response.self_confidence:.2f})")
                    break
            else:
                # 萬一超過 max_loops，強制收斂並儲存最後的回答
                print(f"  ⚠️ {agent.name} 達到最大工具呼叫次數限制，強制收斂。")
                response.response_text += "\n(系統提示：已達最大檔案查閱次數限制)"
                self.debate_history.append(response)

    def _audit_debate(self):
        auditor = self.registry.get_agent("Auditor")
        if auditor:
            history_text = "\n".join([f"{r.agent_name}: {r.response_text}" for r in self.debate_history])
            resp = auditor.think("", history_text)
            print(f"\n🚨 [CRO 判決]: {resp.response_text}")
            self.cro_decision = resp.response_text
        else:
            self.cro_decision = "CONTINUE"
            print("  ℹ️ 尚未註冊 CRO 專家，跳過風控審核。")
        
    def _generate_report(self):
        advisor = self.registry.get_agent("Advisor")
        if advisor:
            history_text = "\n".join([f"{r.agent_name}: {r.response_text}" for r in self.debate_history])
            context = advisor.prepare(self.knowledge)
            resp = advisor.think(context, history_text)
            print("\n==================================================")
            print(f"📊 【{self.knowledge.company.ticker}】 最終決策白皮書")
            print("==================================================")
            print(resp.response_text)
            print("==================================================\n")
        else:
            print("  ℹ️ 尚未註冊 CIO 專家，無法生成最終白皮書。")