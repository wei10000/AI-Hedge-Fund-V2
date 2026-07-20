import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta

# 引入 Chapter 2 定義好的 Pydantic 資料結構
from core.data_models import (
    StockKnowledge, CompanyInfo, FinancialMetrics, 
    TechnicalIndicators, MacroData, Evidence
)

class KnowledgeBuilder:
    """
    知識庫建構器 (Knowledge Builder)。
    負責將外部混亂的 API 數據，轉換成系統標準的 Pydantic Object。
    具備 Try-Catch 避震艙與 Google News 備援機制。
    """
    def __init__(self, fred_api_key: str = None):
        self.fred_api_key = fred_api_key

    def build(self, ticker_symbol: str) -> StockKnowledge:
        print(f"📥 [Knowledge Builder] 啟動多維度數據抓取引擎: {ticker_symbol}")
        
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        company_name = info.get('longName', ticker_symbol)
        
        # 1. 組裝公司基本資料
        company_info = self._build_company_info(ticker_symbol, info)
        
        # 2. 組裝財務數據
        financials = self._build_financials(info, ticker)
        
        # 3. 組裝技術面與籌碼數據
        technicals = self._build_technicals(info, ticker)
        
        # 4. 組裝宏觀與流動性數據
        macro = self._build_macro()
        
        # 5. 抓取最新新聞與財報指引 (Google News 備援)
        news_summary = self._fetch_news_summary(company_name, ticker_symbol)
        
        print("✅ [Knowledge Builder] Pydantic 結構化知識庫組裝完成！")
        
        return StockKnowledge(
            company=company_info,
            financials=financials,
            technicals=technicals,
            macro=macro,
            news_summary=news_summary
        )

    def _build_company_info(self, ticker_symbol: str, info: dict) -> CompanyInfo:
        return CompanyInfo(
            ticker=ticker_symbol,
            company_name=info.get('longName', ticker_symbol),
            sector=info.get('sector', 'Unknown'),
            industry=info.get('industry', 'Unknown'),
            market_cap=info.get('marketCap', 0.0)
        )

    def _build_financials(self, info: dict, ticker: yf.Ticker) -> FinancialMetrics:
        # 計算常態化自由現金流
        fcf_val = info.get('freeCashflow', 0.0)
        try:
            cf = ticker.cashflow
            if cf is not None and not cf.empty and 'Free Cash Flow' in cf.index:
                fcf_history = cf.loc['Free Cash Flow'].dropna().values
                if len(fcf_history) >= 3:
                    avg_fcf = sum(fcf_history[:3]) / 3
                    # 如果最新一季遠低於歷史平均，採用平滑處理
                    if fcf_val < (avg_fcf * 0.7):
                        fcf_val = avg_fcf
        except Exception:
            pass

        return FinancialMetrics(
            revenue_ttm=info.get('totalRevenue'),
            net_income=info.get('netIncomeToCommon'),
            gross_margin=info.get('grossMargins'),
            fcf_normalized=fcf_val,
            pe_ratio=info.get('trailingPE'),
            peg_ratio=info.get('pegRatio'),
            ebitda=info.get('ebitda'),
            evidences=[] # 未來可在此加入證據追蹤
        )

    def _build_technicals(self, info: dict, ticker: yf.Ticker) -> TechnicalIndicators:
        current_price = info.get('currentPrice', 0.0)
        ma_20, ma_50, atr_14, bollinger_up, bollinger_low, poc = None, None, None, None, None, None
        
        try:
            hist = ticker.history(period="1y")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                hist['MA_20'] = hist['Close'].rolling(20).mean()
                hist['MA_50'] = hist['Close'].rolling(50).mean()
                ma_20 = hist['MA_20'].iloc[-1]
                ma_50 = hist['MA_50'].iloc[-1]
                
                # 計算 ATR
                hist.ta.atr(length=14, append=True)
                if 'ATR_14' in hist.columns:
                    atr_14 = hist['ATR_14'].iloc[-1]
                
                # 計算 布林通道
                bbands = ta.bbands(hist['Close'], length=20, std=2)
                if bbands is not None and not bbands.empty:
                    bollinger_low = bbands.iloc[-1, 0]
                    bollinger_up = bbands.iloc[-1, 2]
                
                # 計算 POC (成交量密集區鐵底)
                vp_df = hist.tail(90)
                price_bins = pd.cut(vp_df['Close'], bins=20)
                poc_bin = vp_df.groupby(price_bins, observed=False)['Volume'].sum().idxmax()
                poc = (poc_bin.left + poc_bin.right) / 2
        except Exception as e:
            print(f"⚠️ [Technical Builder] 技術指標計算異常: {e}")

        return TechnicalIndicators(
            current_price=current_price,
            ma_20=ma_20 if pd.notna(ma_20) else None,
            ma_50=ma_50 if pd.notna(ma_50) else None,
            atr_14=atr_14 if pd.notna(atr_14) else None,
            bollinger_upper=bollinger_up if pd.notna(bollinger_up) else None,
            bollinger_lower=bollinger_low if pd.notna(bollinger_low) else None,
            poc_support=poc if pd.notna(poc) else None,
            evidences=[]
        )

    def _build_macro(self) -> MacroData:
        # V2 架構：預設給 None，如果 FRED 抓不到也不會讓系統崩潰
        cpi, unrate, yield_10y, effr, pmi = None, None, None, None, None
        evidences = []
        
        if self.fred_api_key:
            from fredapi import Fred
            fred = Fred(api_key=self.fred_api_key)
            try:
                unrate = fred.get_series('UNRATE').dropna().iloc[-1]
                effr = fred.get_series('EFFR').dropna().iloc[-1]
                yield_10y = fred.get_series('DGS10').dropna().iloc[-1]
                cpi_series = fred.get_series('CPIAUCSL').dropna()
                cpi = (cpi_series.iloc[-1] / cpi_series.iloc[-13] - 1) * 100
                pmi = fred.get_series('ISM/MAN_PMI').dropna().iloc[-1]
            except Exception:
                print("⚠️ [Macro Builder] FRED API 擷取部分數據失敗，將啟動備援...")
        
        # 🚀 Google News RSS PMI 備援機制
        if pmi is None or pd.isna(pmi):
            try:
                query = urllib.parse.quote("ISM Manufacturing PMI latest report")
                url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    root = ET.fromstring(response.read())
                    item = root.find('.//item')
                    if item is not None:
                        title = item.find('title').text
                        # 將新聞標題轉換為證據存入 Pydantic
                        evidences.append(Evidence(
                            id="EV_MACRO_PMI_01",
                            metric_name="PMI Manufacturing",
                            value=f"新聞推估: {title}",
                            source="Google News RSS",
                            timestamp=date.today(),
                            confidence_score=0.6 # 備援數據信心分數較低
                        ))
            except Exception as e:
                print(f"⚠️ [Macro Builder] PMI 備援檢索失敗: {e}")

        return MacroData(
            cpi_yoy=cpi if pd.notna(cpi) else None,
            unemployment_rate=unrate if pd.notna(unrate) else None,
            yield_10y=yield_10y if pd.notna(yield_10y) else None,
            effr=effr if pd.notna(effr) else None,
            pmi_manufacturing=pmi if pd.notna(pmi) else None,
            evidences=evidences
        )

    def _fetch_news_summary(self, company_name: str, ticker_symbol: str) -> list:
        news_list = []
        try:
            query = urllib.parse.quote(f"{company_name} earnings guidance forecast")
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                root = ET.fromstring(response.read())
                for item in root.findall('.//item')[:3]:
                    title = item.find('title').text
                    pubDate = item.find('pubDate').text
                    news_list.append(f"[{pubDate}] {title}")
        except Exception:
            pass
            
        return news_list