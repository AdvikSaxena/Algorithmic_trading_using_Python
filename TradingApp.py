###All the essential libraries
from SmartApi import SmartConnect 
import os
import urllib
import pyotp
import json
import pandas as pd
import datetime as dt
import time
import numpy as np

###acessing the file which are important through key.txt
key_path=r"C:\Users\acer\Desktop\TradingApp"
os.chdir(key_path)

key_secret=open("key.txt.txt","r").read().split()

###generating TOTP
token =key_secret[4]
totp = pyotp.TOTP(token).now()


###Acessing the angel one thorugh API or  authenticating with a service
try:
    obj=SmartConnect(api_key=key_secret[0])
    data = obj.generateSession(key_secret[2],key_secret[3],totp)
    print("Smart API connected suceesfully!")
except Exception as e:
    print("Error" ,e, "occured!")    


###reading the JSON files
instrument_url="https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

###same as opening it in chrome
response=urllib.request.urlopen(instrument_url)


###takes a JSON-formatted string and converts it into a Python dictionary
instrument_list=json.loads(response.read())


###function to get token number of a ticker through ticker name
def token_lookup(ticker,instrument_list,exchange="NSE"):
    for instrument in instrument_list:
        if instrument["name"]==ticker and instrument["exch_seg"]==exchange and instrument["symbol"].split('-')[-1]=="EQ":
            return instrument["token"]

#print(token_lookup("HDFCBANK", instrument_list))


###function to get the name of the ticker through token number
def name_lookup(token,instrument_list,exchange="NSE"):
    for instrument in instrument_list:
        if instrument["token"]==token and instrument["exch_seg"]==exchange and instrument["symbol"].split('-')[-1]=="EQ":
            return instrument["name"]
        
#print(name_lookup("18252", instrument_list))


###Tickers List
tickers=["HDFCBANK","SPAL","TATAGOLD","JINDALSAW"]



###To get the historical Data through API's params
def get_historical_data(duration,interval="FIVE_MINUTE",exchange="NSE"):
    hist_data_tickers={}
    for ticker in tickers:
        params={
          "exchange": "NSE",
          "symboltoken": token_lookup(ticker,instrument_list),
          "interval": interval,
          "fromdate":(dt.datetime.today() - dt.timedelta(duration)).strftime("%Y-%m-%d %H:%M"),
          "todate":dt.datetime.today().strftime("%Y-%m-%d %H:%M") }
          
        hist_data=obj.getCandleData(params)
        df_data=pd.DataFrame(hist_data["data"],columns=["Date","open", "high", "low", "close", "volume"])
        df_data.set_index("Date",inplace=True)
        df_data.index=pd.to_datetime(df_data.index)
        df_data.index=df_data.index.tz_localize(None)
        # df_data.index=range(len(hist_data["data"]))
        hist_data_tickers[ticker]=df_data
    return hist_data_tickers

df=get_historical_data(5)



###To get the historical Data without API's limitation through API's params
def hist_data_extended(ticker,duration,interval,instrument_list,exchange="NSE"):
    st_date = dt.date.today() - dt.timedelta(duration)
    end_date = dt.date.today()
    st_date = dt.datetime(st_date.year, st_date.month, st_date.day, 9, 15)
    end_date = dt.datetime(end_date.year, end_date.month, end_date.day)
    df_data = pd.DataFrame(columns=["date","open","high","low","close","volume",])
    while st_date < end_date:
        time.sleep(0.2) #avoiding throttling rate limit
        params = {
                  "exchange": exchange,
                  "symboltoken": token_lookup(ticker,instrument_list),
                  "interval": interval,
                  "fromdate": (st_date).strftime('%Y-%m-%d %H:%M'),
                  "todate": (end_date).strftime('%Y-%m-%d %H:%M') 
                  }
        hist_data = obj.getCandleData(params)
        temp = pd.DataFrame(hist_data["data"],
                            columns = ["date","open","high","low","close","volume"])
        
        
        if not temp.empty and not temp.isna().all().all():
            df_data = pd.concat([temp, df_data])
            
            
        end_date = dt.datetime.strptime(temp['date'].iloc[0][:16], "%Y-%m-%dT%H:%M")
        if len(temp) <= 1: #this takes care of the edge case where start date and end date become same
            break
    df_data.set_index("date",inplace=True)
    df_data.index = pd.to_datetime(df_data.index)
    df_data.drop_duplicates(keep="first", inplace=True)    
    return df_data

#hdfc_data = hist_data_extended("HDFCBANK", 28, "FIVE_MINUTE", instrument_list)



###To get the Exponential Moving Average
def EMA(ser, n=9):
    multiplier = 2/(n+1)    
    sma = ser.rolling(n).mean()
    ema = np.full(len(ser), np.nan)
    ema[len(sma) - len(sma.dropna())] = sma.dropna()[0]
    for i in range(len(ser)):
        if not np.isnan(ema[i-1]):
            ema[i] = ((ser.iloc[i] - ema[i-1])*multiplier) + ema[i-1]
    ema[len(sma) - len(sma.dropna())] = np.nan
    return ema



###To get the Rolling Moving Average
def RMA(ser, n=9):
    multiplier = 1/n    
    sma = ser.rolling(n).mean()
    rma = np.full(len(ser), np.nan)
    rma[len(sma) - len(sma.dropna())] = sma.dropna()[0]
    for i in range(len(ser)):
        if not np.isnan(rma[i-1]):
            rma[i] = ((ser.iloc[i] - rma[i-1])*multiplier) + rma[i-1]
    rma[len(sma) - len(sma.dropna())] = np.nan
    return rma




###Moving Average Convergence Divergence
# def MACD(df_dict,a=26,b=12,c=9):
#     for df in df_dict:
#         df_dict[df]["MACD_fast"]=df_dict[df]["close"].ewm(span=b, min_periods=b).mean() ##EMA(df_dict[df]["close"],a)
#         df_dict[df]["MACD_slow"]=df_dict[df]["close"].ewm(span=a, min_periods=a).mean() ##EMA(df_dict[df]["close"],b)
#         df_dict[df]["MACD_line"]=df_dict[df]["MACD_slow"]-df_dict[df]["MACD_fast"]
#         df_dict[df]["MACD_signal"]=df_dict[df]["MACD_line"].ewm(span=c, min_periods=c).mean() #EMA(df_dict[df]["close"],c)
#         df_dict[df].drop(["MACD_fast","MACD_slow"], axis=1, inplace=True)

 
        
# MACD(df)   



###Bolinger Band
def Bolinger_Band(df_dict,a=20):
    for df in df_dict:
        df_dict[df]["MB"]=df_dict[df]["close"].rolling(a).mean()
        df_dict[df]["UB"]=df_dict[df]["MB"]-2*df_dict[df]["close"].rolling(a).std(1)
        df_dict[df]["LB"]=df_dict[df]["MB"]+2**df_dict[df]["close"].rolling(a).std(1)
        df_dict[df]["BB_Width"]=df_dict[df]["LB"]-df_dict[df]["UB"]

            
    return df_dict  

 
#BB=Bolinger_Band(df)


def Average_True_Range(df_dict,a=9):
    for df in df_dict:
        df_dict[df]["H-L"]=df_dict[df]["high"]-df_dict[df]["low"]
        df_dict[df]["H-PC"]=abs(df_dict[df]["high"]-df_dict[df]["close"].shift(1))
        df_dict[df]["L-PC"]=abs(df_dict[df]["low"]-df_dict[df]["close"].shift(1))
        df_dict[df]["TR"]=df_dict[df][["H-L","H-PC","L-PC"]].max(axis=1)
        df_dict[df]["ATR"]=EMA(df_dict[df]["TR"],a)
        df_dict[df].drop(["H-L","H-PC","L-PC"],axis=1,inplace=True)
    return df_dict
        
#ATR=Average_True_Range(df)


#Relative Strength Index
def RSI(df_dict,a=14):
    for df in df_dict:
        df_dict[df]["change"]=df_dict[df]["close"]-df_dict[df]["close"].shift(1)
        df_dict[df]["gain"]=np.where(df_dict[df]["change"]>=0,df_dict[df]["change"],0)
        df_dict[df]["loss"]=np.where(df_dict[df]["change"]<0,-1*df_dict[df]["change"],0)
        df_dict[df]["avg_gain"]=RMA(df_dict[df]["gain"],a)
        df_dict[df]["avg_loss"]=RMA(df_dict[df]["loss"],a)
        df_dict[df]["rs"]=df_dict[df]["avg_gain"]/df_dict[df]["avg_loss"]
        df_dict[df]["RSI"]=100-(100/(1+df_dict[df]["rs"]))
        df_dict[df].drop(["change","gain","loss","avg_gain","avg_loss"],axis=1,inplace=True)
    return df_dict

    
#RSI(df)




###function to calculate Stochastic Oscillator lookback = lookback period k and d = moving average window for %K and %D
def stochastic(df_dict, lookback=14, k=1, d=3):
    for df in df_dict:
        df_dict[df]["HH"] = df_dict[df]["high"].rolling(lookback).max()
        df_dict[df]["LL"] = df_dict[df]["low"].rolling(lookback).min()
        df_dict[df]["%K"] = (100 * (df_dict[df]["close"] - df_dict[df]["LL"])/(df_dict[df]["HH"]-df_dict[df]["LL"])).rolling(k).mean()
        df_dict[df]["%D"] = df_dict[df]["%K"].rolling(d).mean()
        df_dict[df].drop(["HH","LL"], axis=1, inplace=True)
        
stochastic(df)











