import os
import time
import json
from workflow.engine import WorkflowEngine
from agents.registry import AgentRegistry

def create_dummy_report(ticker: str):
    """為展示 Tool Calling 能力，動態生成一份假財報原始檔供 AI 翻閱"""
    filepath = f"{ticker}_Full_Report.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"=== {ticker} Q1 2026 Raw Financial Data ===\n")
        f.write("Operating Expenses: $3,200,000,000\n")
        f.write("R&D Expenses: $2,800,000,000\n")
        f.write("Total Revenue Growth YoY: 265%\n")
        f.write("Data Center Revenue: $22,600,000,000\n")
        f.write("Gaming Revenue: $2,870,000,000\n")
        f.write("Automotive Revenue: $281,000,000\n")
    print(f"📄 [準備工作] 已生成供 AI 查閱的本地財報檔案: {filepath}")

def create_default_config():
    """建立預設的 Agent JSON 設定檔"""
    config_dir = "config"
    config_path = os.path.join(config_dir, "agents_config.json")
    
    if not os.path.exists(config_path):
        os.makedirs(config_dir, exist_ok=True)
        default_config = {
            "debate_agents": [
                {
                    "id": "Fundamental_Analyst",
                    "class_name": "FundamentalAgent",
                    "module_path": "agents.fundamental",
                    "model": "llama3.1:latest",
                    "role_description": "華爾街資深基本面分析師，專注於企業內在價值與現金流健康度評估。",
                    "enabled": True
                },
                {
                    "id": "Technical_Analyst",
                    "class_name": "TechnicalAgent",
                    "module_path": "agents.technical",
                    "model": "llama3.1:latest",
                    "role_description": "華爾街頂尖技術線型大師，專注於量價動能與防守點位推演。",
                    "enabled": True
                },
                {
                    "id": "Chips_Macro_Analyst",
                    "class_name": "ChipsMacroAgent",
                    "module_path": "agents.chips_macro",
                    "model": "llama3.1:latest",
                    "role_description": "華爾街總經與籌碼分析大師，專注於流動性、通膨環境、政策利率與機構資金動向。",
                    "enabled": True
                }
            ],
            "system_agents": [
                {
                    "id": "Auditor",
                    "class_name": "AuditorAgent",
                    "module_path": "agents.auditor",
                    "model": "llama3.1:latest",
                    "role_description": "最高風控官 (CRO)，負責嚴格審核會議紀錄，抓出邏輯矛盾與 AI 幻覺。",
                    "enabled": True
                },
                {
                    "id": "Advisor",
                    "class_name": "AdvisorAgent",
                    "module_path": "agents.advisor",
                    "model": "llama3.1:latest",
                    "role_description": "華爾街 5+2 智囊團首席顧問 (CIO)，負責將專家意見轉化為結構化的最終決策白皮書。",
                    "enabled": True
                }
            ]
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        print(f"✨ [準備工作] 已生成預設專家設定檔: {config_path}")

def main():
    print("==================================================")
    print(" ⚡ 啟動 AI Hedge Fund OS V2 (配置驅動架構) ⚡ ")
    print("==================================================")
    
    target_ticker = "NVDA"
    create_dummy_report(target_ticker)
    
    # 確保 Config 檔案存在
    create_default_config()
    
    fred_api_key = os.getenv("FRED_API_KEY", None) 
    
    print("\n🧠 正在動態註冊專家模組 (Dynamic Plugin System)...")
    registry = AgentRegistry(config_path="config/agents_config.json")
    registry.initialize()
    
    engine = WorkflowEngine(registry=registry, fred_api_key=fred_api_key)
    
    start_time = time.time()
    engine.run_analysis(target_ticker)
    end_time = time.time()
    
    print(f"\n⏱️ 執行總耗時: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    main()