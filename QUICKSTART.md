# AI Hedge Fund V3 - 快速參考指南

## 🚀 5 分鐘快速開始

### 1. 安裝和設置
```bash
# 克隆項目
git clone https://github.com/wei10000/AI-Hedge-Fund-V2.git
cd AI-Hedge-Fund-V2

# 安裝依賴
pip install -r requirements.txt

# 設置 API Key（可選）
export FRED_API_KEY="your_api_key_here"
```

### 2. 運行分析
```bash
# 使用 V3 混合控制引擎
python main_v3.py

# 輸出範例：
# ⚡ AI Hedge Fund OS V3 - 混合控制架構
# 📥 [Phase 1] 知識構建...
# ⚔️ [Phase 3] 啟動多輪辯論...
# 🚨 [Phase 4] 最終風控審核...
# 📄 [Phase 5] 生成決策白皮書...
```

---

## 📊 架構一覽

### 三層混合控制
```
┌─────────────────────────────┐
│  資源監控層                 │  ← Token/時間/成本
├─────────────────────────────┤
│  決策層 (程式 + AI)          │  ← 量化 + 邏輯決策
├─────────────────────────────┤
│  執行層 (Agent + 工具)       │  ← 並行辯論 + ReAct
└─────────────────────────────┘
```

### 核心角色
| 角色 | 職責 | 決策類型 |
|------|------|---------|
| **Fundamental Analyst** | 基本面分析 | 邏輯決策 |
| **Technical Analyst** | 技術面分析 | 邏輯決策 |
| **Macro Analyst** | 宏觀分析 | 邏輯決策 |
| **Moderator** | 管理流程 | AI 決策 |
| **CRO (Auditor)** | 風險審核 | AI 決策 |
| **Program Layer** | 資源管理 | 量化決策 |

---

## 🔄 多輪辯論流程

```
Round 1
  ├─ Moderator 計劃 (AI)
  ├─ 程式量化檢查 (Program)
  ├─ 三位分析師發言 (Parallel)
  ├─ 共識度計算 (Program)
  └─ CRO 檢查點 (AI)
    ↓
Round 2 (如果需要)
  └─ ...重複上述流程
    ↓
Round 3-5 (逐漸簡化)
    ↓
最終決策白皮書
```

---

## 📈 關鍵指標

### 共識度 (Consensus Score)
- **計算公式**：`(多數百分比 - 對立懲罰) × 0.7 + 信心分 × 0.3`
- **解讀**：
  - 0.85+ ：高共識，準備結束
  - 0.70-0.85：良好共識，繼續討論
  - 0.50-0.70：低共識，需要深化
  - <0.50 ：分歧嚴重，可能叫停

### 信心分 (Confidence)
- 各 Agent 對自己結論的信心度 (0-1)
- 用於調整共識度權重

### 分歧嚴重程度
- **0-0.3**：輕微差異
- **0.3-0.5**：可接受的分歧
- **0.5+**：重大分歧，需要澄清

---

## 🎯 決策邏輯

### 程式層 (最高優先級)
```python
# 量化決策 - 閾值判斷
if token_usage > 90%:
    → 強制終止 (FORCE_TERMINATE)
elif consensus > 85%:
    → 進入最終 (FINALIZE)
elif round >= max_rounds:
    → 進入最終 (FINALIZE)
else:
    → 繼續 (CONTINUE)
```

### AI 層 (Moderator)
```python
# 邏輯決策
if consensus > 85%:
    → 建議結束 (FINALIZE)
elif major_disagreement AND round < 3:
    → 建議深化 (CLARIFY)
else:
    → 建議常規辯論 (DEBATE)
```

### AI 層 (CRO)
```python
# 風控決策
if logic_contradiction > 0.7:
    → 叫停 (TERMINATE)
elif missing_critical_data:
    → 請求補充 (REQUEST_DATA)
elif consensus < 0.6 AND round > 3:
    → 叫停 (TERMINATE)
else:
    → 通過 (CONTINUE)
```

---

## 💾 配置調整

編輯 `config/agents_config_v3.json`：

```json
{
    "control_strategy": "adaptive",
    
    "decision_layers": {
        "program": {
            "consensus_threshold": 0.85,      // ← 調整共識度閾值
            "token_limit_percent": 0.80,      // ← 調整 Token 警告位置
            "max_rounds": 5                   // ← 調整最大輪數
        },
        "ai": {
            "moderator_enabled": true,        // ← 禁用 Moderator
            "cro_checkpoint_enabled": true,   // ← 禁用 CRO
            "auto_data_collection": true      // ← 禁用自動補充數據
        }
    }
}
```

---

## 📊 輸出解讀

### 會議摘要
```
📊 整體狀態:
   - 標的: NVDA
   - 輪數: 4/5
   - 共識度: 0.82 (82%)         ← 接近高共識
   - 信心分: 0.75 (75%)         ← 中等信心
   - 狀態: FINALIZED             ← 已結束

⚡ 資源消耗:
   - 執行時間: 245.3 秒
   - Token: 65,432 / 100,000     ← 65% 使用率
   - 預估成本: $0.13

🔍 決策路徑:
   - Round 1: [程式] CONTINUE
   - Round 2: [AI/Moderator] DEBATE
   - Round 3: [AI/CRO] REQUEST_DATA
   - Round 4: [程式] FINALIZE
```

### 立場分布
```
Round 4 立場分布:
  - 看多 (BULLISH): 2 位分析師
  - 看空 (BEARISH): 1 位分析師
  - 中立 (NEUTRAL): 0 位分析師
  → 共識度: 67% (2/3 看多 - 1/3 對立懲罰)
```

---

## 🐛 常見問題

### Q1: 為什麼提前終止 (Round 2 就結束了)？
**A:**
- 資源不足 (Token > 90%)
- 共識度已達到 (> 85%)
- 分歧無法解決 (CRO 叫停)

→ 檢查 `meeting.termination_reason`

### Q2: 共識度不動？
**A:**
- 可能存在結構性分歧（看多 vs 看空 1:1）
- 需要額外數據支持
- CRO 已要求補充數據

→ 檢查 `meeting.data_requests`

### Q3: Token 消耗過多？
**A:**
- 調整 `max_rounds` 減少輪數
- 簡化 Agent 的 prompt
- 使用更小的模型 (llama2:7b 而非 llama3.1)

### Q4: 如何禁用某個 Agent？
**A:**
在 `agents_config_v3.json` 中：
```json
{
    "id": "Technical_Analyst",
    "enabled": false    // ← 設為 false
}
```

---

## 📁 項目結構

```
AI-Hedge-Fund-V2/
├── agents/                    # Agent 模組
│   ├── base_agent.py         # 基類
│   ├── fundamental.py        # 基本面分析
│   ├── technical.py          # 技術面分析
│   ├── chips_macro.py        # 宏觀分析
│   ├── moderator.py          # 主持人
│   ├── auditor_v2.py         # 風控官 V2
│   └── registry.py           # Agent 管理
│
├── core/                      # 核心模組
│   ├── data_models.py        # 數據模型
│   ├── meeting_context.py    # 會議上下文
│   ├── consensus_analyzer.py # 共識分析
│   ├── resource_monitor.py   # 資源監控
│   └── ...
│
├── workflow/
│   └── engine_v3.py          # 混合控制引擎 V3
│
├── config/
│   └── agents_config_v3.json # 配置檔
│
├── main_v3.py                # 新入口
├── ARCHITECTURE_V3.md        # 架構文檔
└── QUICKSTART.md             # 本文檔
```

---

## 🔧 自定義開發

### 添加新的 Agent

1. 繼承 `BaseAgent`：
```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def prepare(self, knowledge):
        return "準備工作..."
    
    def think(self, context, query):
        # 你的邏輯
        return AgentResponse(...)
```

2. 在 `agents_config_v3.json` 中註冊：
```json
{
    "id": "My_Agent",
    "class_name": "MyAgent",
    "module_path": "agents.my_module",
    "enabled": true
}
```

### 修改決策規則

編輯 `workflow/engine_v3.py` 中的 `_program_quantitative_check()` 方法：
```python
def _program_quantitative_check(self, round_num):
    # 添加你的自定義檢查邏輯
    if your_condition:
        return {
            "action": DecisionActionType.YOUR_ACTION,
            "reason": "..."
        }
```

---

## 📚 相關文檔

- 詳細架構設計：見 `ARCHITECTURE_V3.md`
- API 參考：見各模組中的 docstring
- 開發指南：見 `DEVELOPMENT.md`（待補充）

---

## 📞 支持和反饋

遇到問題？
1. 檢查 `ARCHITECTURE_V3.md` 的故障排除部分
2. 查看 `meeting.decisions` 的決策路徑
3. 啟用調試模式查看詳細日誌

---

**版本**: V3 (2026-07-21)  
**架構**: 混合控制 (程式 + AI + 資源感知)  
**維護者**: AI Hedge Fund Team
