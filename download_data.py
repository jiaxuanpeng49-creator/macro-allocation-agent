import pandas as pd
import pandas_datareader.data as web
import yfinance as yf

from datetime import datetime


import pandas as pd
# ==========================
# 时间范围
# ==========================

start = datetime(1995,1,1)

end = datetime(2025,12,31)



# ==========================
# 1. 获取宏观数据
# ==========================


# CPI

cpi = web.DataReader(
    "CPIAUCSL",
    "fred",
    start,
    end
)




# 10年期国债收益率

rate = web.DataReader(
    "DGS10",
    "fred",
    start,
    end
)



macro = pd.concat(
    [
        cpi,
        rate
    ],
    axis=1
)



macro.columns = [

    "CPI",

    "RATE"

]


# 月度化

macro = macro.resample(
    "ME"
).last()



macro.to_csv(
    "data/macro.csv"
)



print(
    "宏观数据下载完成"
)





# ==========================
# 2. 获取资产价格
# ==========================


assets = {


    "stock":"^GSPC",

    "bond":"IEF",

    "gold":"GLD"

}



prices=[]



for name,ticker in assets.items():


    data = yf.download(

        ticker,

        start=start,

        end=end,

        auto_adjust=True

    )


    close = data["Close"]


    close.columns=[name]


    prices.append(close)



market = pd.concat(
    prices,
    axis=1
)



# 转收益率

returns = market.pct_change()



# 月度收益

returns = returns.resample(
    "ME"
).sum()



returns.to_csv(
    "data/market.csv"
)



print(
    "市场数据下载完成"
)