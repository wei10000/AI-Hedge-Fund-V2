import json
import importlib
from typing import Dict, List, Optional
from .base_agent import BaseAgent

class AgentRegistry:
    """
    智慧體註冊中心 (Agent Registry)
    負責管理所有專家的生命週期，解耦 Engine 與具體的 Agent 實作。
    """
    def __init__(self, config_path: str = "config/agents_config.json"):
        self._agents: Dict[str, BaseAgent] = {}
        self.config_path = config_path

    def initialize(self):
        """讀取 JSON 設定檔並動態載入啟用的 Agent"""
        print(f"🧠 [Registry] 正在從 {self.config_path} 載入智慧體配置...")
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ [Registry] 找不到設定檔 {self.config_path}，請確定檔案存在。")
            return
        except json.JSONDecodeError:
            print(f"❌ [Registry] 設定檔 {self.config_path} 格式錯誤。")
            return

        all_configs = config_data.get("debate_agents", []) + config_data.get("system_agents", [])
        
        for agent_cfg in all_configs:
            if agent_cfg.get("enabled", False):
                self._dynamic_load(agent_cfg)

    def _dynamic_load(self, agent_cfg: dict):
        """核心魔法：將字串轉換為實際的 Python 物件"""
        module_path = agent_cfg.get("module_path")
        class_name = agent_cfg.get("class_name")
        
        if not module_path or not class_name:
            print(f"⚠️ [Registry] 配置缺少 module_path 或 class_name，略過: {agent_cfg.get('id')}")
            return

        try:
            # 動態 import 模組 (例如: import agents.fundamental)
            module = importlib.import_module(module_path)
            # 取得該模組中的類別 (例如: getattr(module, "FundamentalAgent"))
            agent_class = getattr(module, class_name)
            
            # 實例化該類別並傳入 config
            agent_instance = agent_class(config=agent_cfg)
            
            if not isinstance(agent_instance, BaseAgent):
                 raise TypeError(f"[{class_name}] 必須繼承自 BaseAgent！")

            self._agents[agent_instance.id] = agent_instance
            print(f"✅ [Registry] 已動態載入並註冊: {agent_instance.id} ({class_name})")
            
        except Exception as e:
            print(f"❌ [Registry] 載入 {class_name} 失敗: {e}")

    def register(self, agent: BaseAgent):
        """(向下相容) 手動註冊專家"""
        if not isinstance(agent, BaseAgent):
            raise TypeError(f"[{agent.__class__.__name__}] 必須繼承自 BaseAgent！")
        self._agents[agent.name] = agent
        print(f"✅ [Registry] 手動註冊專家插件: {agent.name}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def get_debate_agents(self) -> List[BaseAgent]:
        """取得所有需要參與『交叉辯論』的專家 (自動排除風控、決策與系統工具)"""
        return [
            agent for agent in self._agents.values() 
            if "Auditor" not in agent.id and "Advisor" not in agent.id and "Research" not in agent.id
        ]
        
    def get_all(self) -> List[BaseAgent]:
        return list(self._agents.values())