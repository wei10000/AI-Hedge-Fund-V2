"""
AI Hedge Fund V3 主入口
使用混合控制工作流引擎 (HybridWorkflowEngineV3)
"""

import os
import json
from workflow.engine_v3 import HybridWorkflowEngineV3
from agents.registry import AgentRegistry
from agents.moderator import ModeratorAgent


def create_default_config_v3():
    """建立預設的 Agent JSON 設定檔（V3 版本）"""
    config_dir = "config"
    config_path = os.path.join(config_dir, "agents_config_v3.json")
    
    if not os.path.exists(config_path):
        os.makedirs(config_dir, exist_ok=True)
        default_config = {
            "control_strategy": "adaptive",  # "fixed" | "ai_driven" | "adaptive"
            
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
                    "id": "Moderator",
                    "class_name": "ModeratorAgent",
                    "module_path": "agents.moderator",
                    "model": "llama3.1:latest",
                    "role_description": "會議主持人，負責協調專家意見並推動共識形成。",
                    "enabled": True
                },
                {
                    "id": "Auditor",
                    "class_name": "AuditorAgentV2",
                    "module_path": "agents.auditor_v2",
                    "model": "llama3.1:latest",
                    "role_description": "最高風控官 (CRO)，負責嚴格審核會議紀錄，識別數據缺失與風險因子。",
                    "enabled": True
                },
                {
                    "id": "Advisor",
                    "class_name": "AdvisorAgent",
                    "module_path": "agents.advisor",
                    "model": "llama3.1:latest",
                    "role_description": "首席顧問 (CIO)，負責將專家意見轉化為結構化的最終決策白皮書。",
                    "enabled": True
                }
            ],
            
            "decision_layers": {
                "program": {
                    "description": "程式層的量化決策參數",
                    "consensus_threshold": 0.85,  # 共識度閾值
                    "token_limit_percent": 0.80,  # Token 消耗到 80% 時警告
                    "max_rounds": 5  # 最大輪數
                },
                "ai": {
                    "description": "AI 層的決策開關",
                    "moderator_enabled": True,  # 啟用 Moderator 制定計劃
                    "cro_checkpoint_enabled": True,  # 啟用 CRO 檢查點
                    "auto_data_collection": True  # 自動補充數據
                }
            },
            
            "fallback_rules": {
                "if_ai_fails": "use_program_defaults",
                "if_token_critical": "force_terminate",
                "if_time_critical": "skip_rounds"
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        
        print(f"✨ [V3 準備工作] 已生成預設專家設定檔: {config_path}")
        return config_path
    
    return config_path


def create_dummy_report(ticker: str):
    """為展示工具調用能力，動態生成一份假財報原始檔供 AI 翻閱"""
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


def main():
    print("="*70)
    print(" ⚡ AI Hedge Fund OS V3 - 混合控制架構 ⚡")
    print(" 🎯 選項 C：程式框架 + AI 決策 + 資源感知")
    print("="*70)
    print()
    
    # 準備工作
    target_ticker = "NVDA"
    create_dummy_report(target_ticker)
    config_path = create_default_config_v3()
    
    # 初始化 Agent 註冊表
    print("\n🧠 [準備工作] 正在動態註冊專家模組...")
    registry = AgentRegistry(config_path=config_path)
    registry.initialize()
    
    # 獲取 FRED API Key（可選）
    fred_api_key = os.getenv("FRED_API_KEY", None)
    
    # 初始化並運行 V3 引擎
    print("\n🚀 [啟動] 初始化混合控制工作流引擎 V3...")
    engine = HybridWorkflowEngineV3(registry=registry, fred_api_key=fred_api_key)
    
    # 配置引擎參數
    engine.config.update({
        "consensus_threshold": 0.85,
        "token_limit_percent": 0.80,
        "max_rounds": 5,
        "enable_ai_moderator": True,
        "enable_cro_checkpoint": True,
        "enable_auto_data_collection": True,
    })
    
    # 運行分析
    import time
    start_time = time.time()
    engine.run_analysis(target_ticker)
    end_time = time.time()
    
    # 輸出摘要
    print("\n" + "="*70)
    print("📈 【分析完成】會議摘要")
    print("="*70)
    
    if engine.meeting:
        print(f"\n📊 整體狀態:")
        print(f"   - 標的: {engine.meeting.ticker}")
        print(f"   - 輪數: {engine.meeting.current_round}/{engine.meeting.max_rounds}")
        print(f"   - 共識度: {engine.meeting.overall_consensus:.0%}")
        print(f"   - 信心分: {engine.meeting.overall_confidence:.0%}")
        print(f"   - 狀態: {engine.meeting.status}")
        
        if engine.meeting.termination_reason:
            print(f"   - 終止原因: {engine.meeting.termination_reason}")
        
        print(f"\n🔍 決策路徑:")
        for decision in engine.meeting.decisions:
            print(f"   - Round {decision.round_number}: [{decision.source.value}] {decision.action.value}")
            print(f"     原因: {decision.reason}")
        
        print(f"\n⚡ 資源消耗:")
        print(f"   - 執行時間: {end_time - start_time:.2f} 秒")
        
        resource_status = engine.resource_monitor.get_resource_status()
        print(f"   - Token 消耗: {resource_status['token_usage']['used']:,} / {resource_status['token_usage']['limit']:,}")
        print(f"   - Token 百分比: {resource_status['token_usage']['percent']:.0%}")
        print(f"   - 預估成本: ${resource_status['cost']['total']:.4f}")
    
    print("\n" + "="*70)
    print("✅ 分析流程完成！")
    print("="*70)


if __name__ == "__main__":
    main()
