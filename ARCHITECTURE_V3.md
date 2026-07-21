"""
AI Hedge Fund V3 - 完整架構文檔
混合控制工作流引擎架構設計文件
"""

# ============================================================================
# 【AI Hedge Fund V3】- 混合控制工作流引擎
# ============================================================================

## 1. 架構概述

### 1.1 設計理念
- **混合控制**：程式框架 + AI 決策 + 資源感知的三層結合
- **適應性**：根據實時狀態動態調整流程
- **透明性**：完整記錄所有決策和理由
- **健壯性**：資源限制和回滾機制

### 1.2 三層控制架構

```
┌─────────────────────────────────────────┐
│     資源感知層 (Resource Aware)         │ ← 監控 Token、時間、成本
├─────────────────────────────────────────┤
│  決策層 (Hybrid Decision Layer)         │
│  ┌──────────────┬──────────────┐       │
│  │ 程式層(P)    │  AI層(M/C)   │       │
│  │ 量化決策     │  邏輯決策    │       │
│  └──────────────┴──────────────┘       │
├─────────────────────────────────────────┤
│    執行層 (Execution Layer)             │
│  - 多輪辯論引擎                         │
│  - Agent 管理                           │
│  - 工具調用 (ReAct)                     │
└─────────────────────────────────────────┘
```

## 2. 核心組件

### 2.1 MeetingContext（會議上下文）
**職責**：追蹤整個分析過程的完整狀態

```python
class MeetingContext:
    - ticker: 分析標的
    - current_round: 當前輪數
    - round_history: 歷史記錄（包含立場、分歧、決策）
    - overall_consensus: 整體共識度 (0-1)
    - overall_confidence: 整體信心分 (0-1)
    - decisions: 所有決策記錄
    - cro_decisions: CRO 的決策記錄
    - data_requests: 補充數據請求
    - knowledge: 知識庫（基本面、技術面、宏觀等）
```

**重要方法**：
- `add_round()`：記錄每一輪的完整信息
- `add_decision()`：記錄決策
- `get_disagreements_summary()`：統計分歧
- `get_decision_path()`：生成決策路徑

### 2.2 ConsensusAnalyzer（共識分析器）
**職責**：計算共識度、分歧嚴重程度、一致性指標

**核心演算法**：
```python
consensus = (立場多數百分比 - 對立懲罰) * 0.7 + 信心分 * 0.3

其中：
- 對立懲罰 = min(看多數, 看空數) / 總數 * 0.5
- 信心分 = 各 Agent 信心的平均值
```

**分歧分類**：
- `OPPOSITE`：完全對立（看多 vs 看空）
- `COMPLEMENTARY`：互補性（立場相同但論點不同）
- `UNCLEAR`：有一方態度不明確

### 2.3 ModeratorAgent（主持人代理）
**職責**：管理流程、制定計劃、提出澄清問題

**決策方法 - decide_round_plan()**：
```
if 共識度 > 85%:
    → 行動: FINALIZE（進入最終審核）
elif 存在重大分歧 AND 輪數 < 3:
    → 行動: CLARIFY（深化討論）
elif 輪數 >= max_rounds:
    → 行動: FINALIZE（達到上限）
else:
    → 行動: DEBATE（常規辯論）
```

### 2.4 AuditorAgentV2（風控官 V2）
**職責**：檢查邏輯一致性、識別數據缺失、決定流程走向

**檢查點方法 - checkpoint()**：
```
1. 檢查邏輯一致性
   - 如果嚴重程度 > 0.7 → 行動: TERMINATE

2. 識別數據缺失
   - 如果缺失關鍵數據 → 行動: REQUEST_DATA

3. 檢查共識質量
   - 如果經多輪仍 < 60% 共識 → 行動: TERMINATE

4. 檢查信心分趨勢
   - 如果下降 > 15% → 行動: REQUEST_DATA

通過所有檢查 → 行動: CONTINUE
```

### 2.5 ResourceMonitor（資源監控器）
**職責**：監控 Token、時間、成本消耗

**監控指標**：
- `token_usage_percent`：Token 消耗百分比
- `time_usage_percent`：時間消耗百分比
- `estimated_remaining_rounds`：還能進行多少輪
- `is_critical()`：是否接近臨界值

## 3. 多輪辯論流程

### 3.1 完整流程圖

```
Round N 開始
    ↓
[AI] Moderator 制定計劃
    ↓
[程式] 量化檢查 ─→ 共識達到/資源耗盡? → FINALIZE/TERMINATE
    ↓ (否則繼續)
[執行] 各 Agent 發言
    ↓
[分析] 提取立場 → 計算共識度 → 檢測分歧
    ↓
[AI] CRO 檢查點 ─→ 邏輯矛盾? → TERMINATE
                  ├→ 數據缺失? → REQUEST_DATA + CONTINUE
                  └→ 通過檢查 → CONTINUE
    ↓
資源狀態監控 ─→ Token/時間臨界? → FINALIZE
    ↓
Round N 結束
```

### 3.2 各環節的決策者

| 環節 | 決策者 | 決策類型 | 優先級 |
|------|--------|---------|--------|
| 計劃 | AI (Moderator) | 邏輯決策 | 低 |
| 量化檢查 | 程式 | 閾值決策 | 高 |
| 執行 | Agent Registry | 並行執行 | 低 |
| 分析 | 程式 + 分析器 | 計算 | 低 |
| CRO 檢查 | AI (CRO) | 邏輯決策 | 高 |
| 資源檢查 | 程式 | 強制決策 | 最高 |

## 4. 決策層級和優先級

### 4.1 三層決策模型

```
【第 1 層】程式決策（絕對優先）
- 資源限制（Token > 90%）→ 強制 TERMINATE
- 輪數上限 → 進入 FINALIZE
- 共識度高 (> 85%) → 進入 FINALIZE

    ↓ （程式決策通過，再看 AI 決策）

【第 2 層】AI 決策
- Moderator 計劃（DEBATE/CLARIFY/FINALIZE）
- CRO 檢查點（CONTINUE/REQUEST_DATA/TERMINATE）

    ↓ （AI 決策執行）

【第 3 層】資源救援
- Token 即將用盡 → 快速收尾
- 時間即將到期 → 簡化流程
```

### 4.2 衝突解決規則

```python
優先級排序（從高到低）：
1. 資源限制（程式） > AI 決策
2. CRO 的 TERMINATE > Moderator 的 DEBATE
3. 程式的量化檢查 > AI 的邏輯決策
```

## 5. 數據流

### 5.1 信息流動

```
知識庫 (Stock Knowledge)
  ├─ 基本面數據 (Fundamentals)
  ├─ 技術面數據 (Technicals)
  ├─ 宏觀數據 (Macro)
  ├─ 新聞數據 (News)
  └─ 衍生計算 (Calculations)
    ↓
會議上下文 (Meeting Context)
    ├─ Round Memory 1: 位置、分歧、決策
    ├─ Round Memory 2: 位置、分歧、決策
    ├─ ...
    └─ Round Memory N: 位置、分歧、決策
    ↓
最終決策白皮書 (Final Report)
```

### 5.2 Agent 回應流

```
Agent 回應 (AgentResponse)
  ├─ response_text: 完整回應
  ├─ self_confidence: 信心分
  └─ [工具調用]: READ_FILE / SEARCH 等
    ↓
位置提取 (PositionExtractor)
  ├─ 立場偵測 (BULLISH/BEARISH/NEUTRAL)
  ├─ 信心分提取
  ├─ 核心論點
  └─ 數據引用
    ↓
AgentPosition 物件
    ↓
共識分析 (ConsensusAnalyzer)
    ├─ 共識度計算
    ├─ 分歧檢測
    └─ 信心分趨勢
```

## 6. 資源管理策略

### 6.1 Token 管理

```
總預算: 100,000 tokens

階段分配:
- 知識構建 (20,000): 基本面、技術面、宏觀分析
- Round 1-3 辯論 (40,000): ~13,000 per round
- Round 4-5 深化 (20,000): ~10,000 per round (簡化)
- 最終審核 (15,000): CRO、顧問報告
- 緩衝 (5,000): 應急

臨界值：
- 75% (75,000 tokens): 進入簡化模式
- 80% (80,000 tokens): 考慮快速收尾
- 90% (90,000 tokens): 強制終止
```

### 6.2 時間管理

```
總預算: 3600 秒 (1 小時)

階段分配:
- 知識構建: 600 秒
- Round 1-3: 1800 秒 (~600s per round)
- Round 4-5: 600 秒 (~300s per round)
- 最終審核: 400 秒
- 緩衝: 200 秒

臨界值：
- 75% (2700s): 簡化討論
- 85% (3060s): 快速收尾
- 90% (3240s): 強制結束
```

## 7. 異常處理和回滾

### 7.1 異常情況

| 異常 | 觸發 | 處理 |
|------|------|------|
| AI 不可用 | Moderator/CRO 返回異常 | 使用程式預設決策 |
| Agent 無回應 | 5秒超時 | 跳過該 Agent，繼續 |
| Token 用盡 | Token > 95% | 強制終止，進入報告 |
| 分歧無法解決 | 多輪後仍 < 50% 共識 | CRO 決定叫停 |
| 數據缺失 | CRO 檢測 | 自動請求補充，允許一次 |

### 7.2 回滾機制

```
if 前一輪決策失敗:
    使用上一輪的狀態
    簡化下一輪的討論
    記錄失敗原因

if 多次失敗:
    觸發緊急終止
    生成部分報告
```

## 8. 使用指南

### 8.1 快速開始

```bash
# 安裝依賴
pip install -r requirements.txt

# 設置 FRED API Key（可選）
export FRED_API_KEY="your_key"

# 運行 V3 引擎
python main_v3.py
```

### 8.2 自定義配置

編輯 `config/agents_config_v3.json`：

```json
{
    "control_strategy": "adaptive",
    "debate_agents": [
        {
            "id": "Fundamental_Analyst",
            "enabled": true,
            "model": "llama3.1:latest"
        }
    ],
    "decision_layers": {
        "program": {
            "consensus_threshold": 0.85,
            "token_limit_percent": 0.80,
            "max_rounds": 5
        }
    }
}
```

### 8.3 輸出解讀

```
📊 分析完成 - 會議摘要
├─ 共識度: 0.82 (82%)        → 接近但未達高共識
├─ 信心分: 0.75 (75%)        → 中等信心水平
├─ 輪數: 4/5                  → 提前收斂
├─ Token 消耗: 65,000/100,000 → 65% 使用率
└─ 決策路徑:
   - Round 1: [程式] CONTINUE
   - Round 2: [AI/Moderator] DEBATE
   - Round 3: [AI/CRO] REQUEST_DATA → 補充數據
   - Round 4: [程式] FINALIZE → 共識度達到
```

## 9. 性能優化

### 9.1 優化策略

1. **並行執行**：所有 Agent 同時發言（不順序等待）
2. **快速失敗**：異常 Agent 立即跳過
3. **緩存結果**：重複查詢結果緩存
4. **早期終止**：提前達成共識時立即結束

### 9.2 預期性能

```
典型分析耗時: 8-12 分鐘
- 知識構建: 1-2 分鐘
- 多輪辯論: 4-6 分鐘（4-5 輪）
- 最終報告: 1-2 分鐘

Token 消耗: 50,000-80,000
- 平均每輪: 12,000-15,000 tokens

成本估計: $0.10-0.16 (使用 Llama 本地)
```

## 10. 故障排除

### 10.1 常見問題

**Q: 為什麼提前終止？**
A: 檢查 `meeting.termination_reason`，可能原因：
   - 資源不足
   - 分歧無法解決
   - CRO 檢測到邏輯矛盾

**Q: 共識度為什麼停滯？**
A: 可能是結構性分歧，需要更多數據或不同視角。

**Q: Token 消耗過多？**
A: 調整 `max_rounds` 或簡化 Agent 的 prompt。

## 11. 未來改進方向

- [ ] 動態調整 Agent 權重
- [ ] 支持多個 Moderator/CRO
- [ ] 實時 Token 流估計
- [ ] 自動報告生成優化
- [ ] 支持 A/B 測試不同策略
- [ ] 決策過程的可視化界面
"""