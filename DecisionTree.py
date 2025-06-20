import pandas as pd

# Load data
df = pd.read_csv("btc_1d_data_2018_to_2025.csv")

# Data preprocessing
df['Open time']  = pd.to_datetime(df['Open time'])
df['Close time'] = pd.to_datetime(df['Close time'])

df['Date'] = df['Close time'].dt.date         
df.set_index('Date', inplace=True)             

# pastikan angka
num_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
df[num_cols] = df[num_cols].apply(pd.to_numeric, errors='coerce')
df.dropna(subset=num_cols, inplace=True)

# RSI
def rsi(series, n=14):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(n).mean()
    loss  = -delta.where(delta < 0, 0).rolling(n).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)

df['RSI'] = rsi(df['Close'])

#EMA
ema12 = df['Close'].ewm(span=12, adjust=False).mean()
ema26 = df['Close'].ewm(span=26, adjust=False).mean()
df['MACD']         = ema12 - ema26
df['MACD_signal']  = df['MACD'].ewm(span=9,  adjust=False).mean()
df['MACD_hist']    = df['MACD'] - df['MACD_signal']

df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

# MACD
df.dropna(subset=['RSI', 'MACD', 'MACD_signal', 'MACD_hist', 'EMA_50'], inplace=True)

# Decision-tree rule 
def rule(row, prev):
    above = row['Close'] > row['EMA_50']
    bull = row['MACD'] > row['MACD_signal']
    bear = row['MACD'] < row['MACD_signal']
    hist_up = prev is not None and row['MACD_hist'] > prev['MACD_hist']
    hist_down = prev is not None and row['MACD_hist'] < prev['MACD_hist']

    if above:
        if row['RSI'] < 30:
            if bull:
                if hist_up:
                    return 1  
                else:
                    return 0  
            else:
                return 0  
        else:
            if row['RSI'] >= 30:
                if row['RSI'] <= 50:
                    if bull:
                        return 1  
                    else:
                        return 0 
                else:
                    return 0 
            else:
                return 0  
    else:
        if row['RSI'] > 70:
            if bear:
                if hist_down:
                    return -1  
                else:
                    return 0 
            else:
                return 0  
        else:
            if row['RSI'] >= 50:
                if row['RSI'] <= 70:
                    if bear:
                        return -1  
                    else:
                        return 0 
                else:
                    return 0 
            else:
                return 0  

df['Signal'] = 0
dates = df.index.tolist()
for i in range(1, len(dates)):
    today, yesterday = dates[i], dates[i-1]
    df.loc[today, 'Signal'] = rule(df.loc[today], df.loc[yesterday])


print("Available date range:", df.index.min(), "to", df.index.max())
target = input("Enter target date (YYYY-MM-DD): ").strip()

try:
    date_obj = pd.to_datetime(target).date()   
    if date_obj not in df.index:
        raise ValueError("Date out of range or indicators missing.")

    row = df.loc[date_obj]
    sig_txt = {1: "📈 LONG", 0: "⏸ HOLD", -1: "📉 SHORT"}[row['Signal']]

    print(f"\n Signal for {date_obj}:")
    print(f"  Close          : {row['Close']:.2f} USD")
    print(f"  EMA-50         : {row['EMA_50']:.2f}")
    print(f"  RSI            : {row['RSI']:.2f}")
    print(f"  MACD           : {row['MACD']:.2f}")
    print(f"  MACD Signal    : {row['MACD_signal']:.2f}")
    print(f"  MACD Histogram : {row['MACD_hist']:.2f}")
    print(f"  Decision       : {sig_txt}")

except Exception as e:
    print("⚠", e)

