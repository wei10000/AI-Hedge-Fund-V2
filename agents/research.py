import os
from .base_agent import BaseAgent
from core.data_models import StockKnowledge, AgentResponse

class ResearchAgent(BaseAgent):
    """
    專屬搜尋專家 (Research Agent)
    負責執行聯網搜尋或讀取本地檔案。它是系統中唯一具備「物理操作權限」的 Agent。
    """
    def __init__(self, model_name: str = "llama3.1:latest"):
        # 因為 ResearchAgent 是 Engine 內部自用，不在 JSON Config 裡，
        # 所以我們在這邊手動組裝一個虛擬的 config 丟給 BaseAgent。
        mock_config = {
            "id": "Research_Agent",
            "model": model_name,
            "role_description": "資料探勘專家，專注於執行搜尋、檔案讀取與資訊提取。"
        }
        super().__init__(config=mock_config)

    def prepare(self, knowledge: StockKnowledge) -> str:
        return "你是一個工具執行專家，只需依據指令執行搜尋或讀取檔案。"

    def think(self, context: str, task: str) -> AgentResponse:
        # Research Agent 直接由 Engine 操控工具，這個方法僅為符合 BaseAgent 介面
        return AgentResponse(agent_name=self.id, role=self.role_description, response_text=task, self_confidence=1.0)

    def validate(self, response: AgentResponse) -> bool:
        return True

    def execute_tool(self, tool_name: str, tool_args: str) -> str:
        """接收 Engine 傳來的指令並執行對應的底層 Python 程式碼"""
        if tool_name.upper() == "READ_FILE":
            # 預期 args 格式: "filepath|keyword"
            args = tool_args.split("|")
            filepath = args[0].strip()
            keyword = args[1].strip() if len(args) > 1 else ""
            return self._read_local_file(filepath, keyword)
            
        elif tool_name.upper() == "SEARCH":
            # 模擬搜尋結果 (未來可接真正的搜尋 API)
            return f"〔系統回報：執行網路搜尋 '{tool_args}'... 找到以下結果：市場關注最新的財報指引。〕"
            
        return f"〔系統回報：未知的工具指令 {tool_name}〕"

    def _read_local_file(self, filepath: str, keyword: str) -> str:
        """AI 使用的底層工具：讀取本地檔案並擷取關鍵字前後文"""
        if not os.path.exists(filepath):
            return f"〔系統回報：找不到檔案 {filepath}，請確認檔名是否正確。〕"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            results = []
            for i, line in enumerate(lines):
                if keyword.lower() in line.lower():
                    # 抓取關鍵字前後 2 行作為上下文，避免 Token 爆掉
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    results.append("".join(lines[start:end]).strip())
            
            if results:
                return "\n...[擷取片段]...\n".join(results[:3]) # 最多回傳 3 個片段
            return f"〔系統回報：在檔案中找不到關於 '{keyword}' 的數據。〕"
            
        except Exception as e:
            return f"〔系統回報：讀取失敗 ({e})〕"