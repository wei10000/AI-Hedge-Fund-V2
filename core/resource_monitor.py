"""
資源監控器 (Resource Monitor)
追蹤 Token 消耗、時間、成本等資源指標
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import time


class ResourceMonitor:
    """
    監控和管理系統資源消耗
    """
    
    def __init__(self, token_limit: int = 100000, time_limit_seconds: int = 3600):
        self.token_limit = token_limit
        self.time_limit = timedelta(seconds=time_limit_seconds)
        
        self.start_time = datetime.now()
        self.total_tokens_estimated = 0
        self.tokens_per_round: List[int] = []
        self.round_times: List[float] = []  # 每輪耗時（秒）
        
        # 成本追蹤
        self.cost_per_token = 0.000002  # Llama 大約的成本
        self.total_cost = 0.0

    def estimate_tokens(self, text: str) -> int:
        """
        粗略估計文本的 token 數
        
        規則：1 token ≈ 4 字符
        """
        if isinstance(text, str):
            return max(1, len(text) // 4)
        return 0

    def record_round_tokens(self, tokens: int):
        """記錄某一輪的 Token 消耗"""
        self.tokens_per_round.append(tokens)
        self.total_tokens_estimated += tokens
        self.total_cost += tokens * self.cost_per_token

    def record_round_time(self, duration_seconds: float):
        """記錄某一輪的耗時"""
        self.round_times.append(duration_seconds)

    def get_token_usage_percent(self) -> float:
        """取得 Token 消耗百分比"""
        if self.token_limit == 0:
            return 0.0
        return min(1.0, self.total_tokens_estimated / self.token_limit)

    def get_time_usage_percent(self) -> float:
        """取得時間消耗百分比"""
        elapsed = datetime.now() - self.start_time
        if self.time_limit.total_seconds() == 0:
            return 0.0
        return min(1.0, elapsed.total_seconds() / self.time_limit.total_seconds())

    def is_token_critical(self, threshold: float = 0.80) -> bool:
        """檢查 Token 是否接近上限"""
        return self.get_token_usage_percent() >= threshold

    def is_time_critical(self, threshold: float = 0.85) -> bool:
        """檢查時間是否接近上限"""
        return self.get_time_usage_percent() >= threshold

    def get_estimated_remaining_rounds(self, avg_tokens_per_round: Optional[int] = None) -> int:
        """
        估計還能進行多少輪
        """
        if avg_tokens_per_round is None:
            if not self.tokens_per_round:
                return 3  # 預設
            avg_tokens_per_round = sum(self.tokens_per_round) / len(self.tokens_per_round)
        
        remaining_tokens = self.token_limit - self.total_tokens_estimated
        if avg_tokens_per_round == 0:
            return 0
        
        return max(0, int(remaining_tokens / avg_tokens_per_round))

    def get_resource_status(self) -> Dict:
        """
        取得資源狀態快照
        """
        avg_tokens = (
            sum(self.tokens_per_round) / len(self.tokens_per_round)
            if self.tokens_per_round
            else 0
        )
        
        avg_time = (
            sum(self.round_times) / len(self.round_times)
            if self.round_times
            else 0
        )
        
        return {
            "token_usage": {
                "used": self.total_tokens_estimated,
                "limit": self.token_limit,
                "percent": self.get_token_usage_percent(),
                "remaining": self.token_limit - self.total_tokens_estimated,
                "avg_per_round": avg_tokens,
                "estimated_remaining_rounds": self.get_estimated_remaining_rounds(int(avg_tokens))
            },
            "time_usage": {
                "elapsed": (datetime.now() - self.start_time).total_seconds(),
                "limit": self.time_limit.total_seconds(),
                "percent": self.get_time_usage_percent(),
                "avg_per_round": avg_time
            },
            "cost": {
                "total": self.total_cost,
                "per_token": self.cost_per_token,
                "estimate_per_round": avg_tokens * self.cost_per_token
            },
            "is_critical": {
                "token": self.is_token_critical(),
                "time": self.is_time_critical()
            }
        }

    def print_status(self):
        """打印資源狀態"""
        status = self.get_resource_status()
        
        print("\n" + "="*60)
        print("📊 資源消耗狀態")
        print("="*60)
        
        # Token 狀態
        token_info = status["token_usage"]
        token_bar = self._create_progress_bar(token_info["percent"])
        print(f"Token: {token_info['used']:,} / {token_info['limit']:,} {token_bar}")
        print(f"  → 剩餘: {token_info['remaining']:,} (可再進行 ~{token_info['estimated_remaining_rounds']} 輪)")
        
        # 時間狀態
        time_info = status["time_usage"]
        time_bar = self._create_progress_bar(time_info["percent"])
        print(f"時間: {time_info['elapsed']:.0f}s / {time_info['limit']:.0f}s {time_bar}")
        
        # 成本狀態
        cost_info = status["cost"]
        print(f"成本: ${cost_info['total']:.4f}")
        
        # 警告
        if status["is_critical"]["token"] or status["is_critical"]["time"]:
            print("\n⚠️ 警告：資源即將耗盡！")
        
        print("="*60 + "\n")

    @staticmethod
    def _create_progress_bar(percent: float, width: int = 30) -> str:
        """生成進度條"""
        filled = int(width * percent)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percent:.0%}"


class DecisionMaker:
    """
    資源感知決策制定者
    根據資源狀態做出決策
    """

    @staticmethod
    def should_force_terminate_by_resources(monitor: ResourceMonitor) -> bool:
        """
        是否應因資源限制而強制終止
        """
        return monitor.is_token_critical(0.90) or monitor.is_time_critical(0.90)

    @staticmethod
    def should_enter_fast_mode(monitor: ResourceMonitor) -> bool:
        """
        是否應進入「快速模式」（簡化流程）
        """
        return monitor.is_token_critical(0.75) or monitor.is_time_critical(0.75)

    @staticmethod
    def get_emergency_action(monitor: ResourceMonitor) -> Optional[str]:
        """
        根據資源狀態返回緊急行動
        """
        if monitor.is_token_critical(0.95):
            return "FORCE_TERMINATE"  # 強制立即結束
        
        if monitor.is_token_critical(0.80):
            return "SKIP_ROUNDS"  # 跳過不必要的輪次
        
        if monitor.is_token_critical(0.70):
            return "SIMPLIFY"  # 簡化對話
        
        return None
