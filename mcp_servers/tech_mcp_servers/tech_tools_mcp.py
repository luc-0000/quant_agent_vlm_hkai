import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mcp_servers.utils import get_mcp_studio_tools_async
import matplotlib
from fastmcp import FastMCP
from trading_agents.quant_agent_vlm.src import color_style
from mcp_servers.tech_mcp_servers.tech_tools_mcp_utils import split_line_into_segments, get_line_points, fit_trendlines_high_low, \
    fit_trendlines_single

matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
import talib
import numpy as np
from typing import Annotated
import base64
import io
import mplfinance as mpf 

tool_kit_name = 'TechToolsMCP'
tech_tools_mcp = FastMCP("TechToolsMCP")

class TechToolsMCP:

    @staticmethod
    @tech_tools_mcp.tool()
    def generate_trend_image(
        kline_data: Annotated[dict, "Dictionary containing OHLCV data with keys 'Datetime', 'Open', 'High', 'Low', 'Close'."]
    ) -> dict:
        """
        Generate a candlestick chart with trendlines from OHLCV data,
        save it locally as 'trend_graph.png', and return a base64-encoded image.

        Returns:
            dict: base64 image and description
        """
        data = pd.DataFrame(kline_data)
        candles = data.iloc[-50:].copy()

        candles["Datetime"] = pd.to_datetime(candles["Datetime"])
        candles.set_index("Datetime", inplace=True)

        # Trendline fit functions assumed to be defined outside this scope
        support_coefs_c, resist_coefs_c = fit_trendlines_single(candles['Close'])
        support_coefs, resist_coefs = fit_trendlines_high_low(candles['High'], candles['Low'], candles['Close'])

        # Trendline values
        support_line_c = support_coefs_c[0] * np.arange(len(candles)) + support_coefs_c[1]
        resist_line_c = resist_coefs_c[0] * np.arange(len(candles)) + resist_coefs_c[1]
        support_line = support_coefs[0] * np.arange(len(candles)) + support_coefs[1]
        resist_line = resist_coefs[0] * np.arange(len(candles)) + resist_coefs[1]

        # Convert to time-anchored coordinates
        s_seq = get_line_points(candles, support_line)
        r_seq = get_line_points(candles, resist_line)
        s_seq2 = get_line_points(candles, support_line_c)
        r_seq2 = get_line_points(candles, resist_line_c)

        s_segments = split_line_into_segments(s_seq)
        r_segments = split_line_into_segments(r_seq)
        s2_segments = split_line_into_segments(s_seq2)
        r2_segments = split_line_into_segments(r_seq2)

        all_segments = s_segments + r_segments + s2_segments + r2_segments
        colors = ['white'] * len(s_segments) + ['white'] * len(r_segments) + ['blue'] * len(s2_segments) + ['red'] * len(r2_segments)

        # Create addplot lines for close-based support/resistance
        apds = [
            mpf.make_addplot(support_line_c, color='blue', width=1, label="Close Support"),
            mpf.make_addplot(resist_line_c, color='red', width=1, label="Close Resistance")
        ]

        # Generate figure with legend and save locally
        fig, axlist = mpf.plot(
            candles,
            type='candle',
            style=color_style.my_color_style,
            addplot=apds,
            alines=dict(alines=all_segments, colors=colors, linewidths=1),
            returnfig=True,
            figsize=(12, 6),
            block=False,
        )

        axlist[0].set_ylabel('Price', fontweight='normal')
        axlist[0].set_xlabel('Datetime', fontweight='normal')

        #save fig locally
        fig.savefig(
            "./data/trend_graph.png",
            format="png",
            dpi=600,
            bbox_inches="tight",
            pad_inches=0.1
        )
        plt.close(fig) 

        # Add legend manually
        axlist[0].legend(loc='upper left')

        # Save to base64
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)

        return {
            "trend_image": img_b64,
            "trend_image_description": "Trend-enhanced candlestick chart with support/resistance lines."
        }



    @staticmethod
    @tech_tools_mcp.tool()
    def generate_kline_image(
        kline_data: Annotated[dict, "Dictionary containing OHLCV data with keys 'Datetime', 'Open', 'High', 'Low', 'Close'."],
    ) -> dict:
        """
        Generate a candlestick (K-line) chart from OHLCV data, save it locally, and return a base64-encoded image.

        Args:
            kline_data (dict): Dictionary with keys including 'Datetime', 'Open', 'High', 'Low', 'Close'.
            filename (str): Name of the file to save the image locally (default: 'kline_chart.png').

        Returns:
            dict: Dictionary containing base64-encoded image string and local file path.
        """

        df = pd.DataFrame(kline_data)
        # take recent 40
        df = df.tail(40)

        # df.to_csv("record.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
        try:
            df.index = pd.to_datetime(df["Datetime"], format="%Y-%m-%d %H:%M:%S")

        except ValueError:
            print("ValueError at graph_util.py\n")

        # Save image locally
        fig, axlist = mpf.plot(
            df[["Open", "High", "Low", "Close"]],
            type="candle",
            style=color_style.my_color_style,
            figsize=(12, 6),
            returnfig=True,           
            block=False,             
            
        )
        axlist[0].set_ylabel('Price', fontweight='normal')
        axlist[0].set_xlabel('Datetime', fontweight='normal')

        fig.savefig(             
            fname="./data/kline_chart.png",
            dpi=600,
            bbox_inches="tight",
            pad_inches=0.1,
        )
        plt.close(fig)
        # ---------- Encode to base64 -----------------
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=600, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)                # release memory

        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("utf-8")

        return {
            "pattern_image": img_b64,
            "pattern_image_description": "Candlestick chart saved locally and returned as base64 string."
        }


    @staticmethod
    @tech_tools_mcp.tool()
    def compute_rsi(
        kline_data: Annotated[dict, "Dictionary with a 'Close' key containing a list of float closing prices."],
        period: Annotated[int, "Lookback period for RSI calculation (default is 14)"] = 14
    ) -> dict:
        """
        Compute the Relative Strength Index (RSI) using TA-Lib.

        Args:
            data (dict): Dictionary containing at least a 'Close' key with a list of float values.
            period (int): Lookback period for RSI calculation (default is 14).

        Returns:
            dict: A dictionary with a single key 'rsi' mapping to a list of RSI values.
        """
        df = pd.DataFrame(kline_data)
        rsi = talib.RSI(df["Close"], timeperiod=period)
        return {"rsi": rsi.fillna(0).round(2).tolist()[-28:]}

    @staticmethod
    @tech_tools_mcp.tool()
    def compute_macd(
        kline_data: Annotated[dict, "Dictionary with a 'Close' key containing a list of float closing prices."],
        fastperiod: Annotated[int, "Fast EMA period"] = 12,
        slowperiod: Annotated[int, "Slow EMA period"] = 26,
        signalperiod: Annotated[int, "Signal line EMA period"] = 9
    ) -> dict:
        """
        Compute the Moving Average Convergence Divergence (MACD) using TA-Lib.

        Args:
            kline_data (dict): Dictionary containing a 'Close' key with list of float values.
            fastperiod (int): Fast EMA period.
            slowperiod (int): Slow EMA period.
            signalperiod (int): Signal line EMA period.

        Returns:
            dict: Dictionary containing 'macd', 'macd_signal', and 'macd_hist' as lists of values.
        """
        df = pd.DataFrame(kline_data)
        macd, macd_signal, macd_hist = talib.MACD(df["Close"], fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        return {
            "macd": macd.fillna(0).round(2).tolist(),
            "macd_signal": macd_signal.fillna(0).round(2).tolist()[-28:],
            "macd_hist": macd_hist.fillna(0).round(2).tolist()[-28:]
        }

    @staticmethod
    @tech_tools_mcp.tool()
    def compute_stoch(kline_data: Annotated[dict, "Dictionary with 'High', 'Low', and 'Close' keys, each mapping to lists of float values."]
    ) -> dict:
        """
        Compute the Stochastic Oscillator %K and %D using TA-Lib.

        Args:
            kline_data (dict): Dictionary with 'High', 'Low', and 'Close' keys, each mapping to lists of float values.

        Returns:
            dict: A dictionary with keys 'stoch_k' and 'stoch_d',
                each mapping to a list representing %K and %D values.
        """
        df = pd.DataFrame(kline_data)
        stoch_k, stoch_d = talib.STOCH(df["High"], df["Low"], df["Close"], fastk_period=14, slowk_period=3, slowd_period=3)
        return {
            "stoch_k": stoch_k.fillna(0).round(2).tolist()[-28:],
            "stoch_d": stoch_d.fillna(0).round(2).tolist()[-28:]
        }

    @staticmethod
    @tech_tools_mcp.tool()
    def compute_roc(kline_data: Annotated[dict, "Dictionary with a 'Close' key containing a list of float closing prices."],
        period: Annotated[int, "Number of periods over which to calculate ROC (default is 10)"] = 10
    ) -> dict:
        """
        Compute the Rate of Change (ROC) indicator using TA-Lib.

        Args:
            kline_data (dict): Dictionary containing a 'Close' key with a list of float values.
            period (int): Number of periods over which to calculate ROC (default is 10).

        Returns:
            dict: A dictionary with a single key 'roc' mapping to a list of ROC values.
        """

        df = pd.DataFrame(kline_data)
        roc = talib.ROC(df["Close"], timeperiod=period)
        return {"roc": roc.fillna(0).round(2).tolist()[-28:]}

    @staticmethod
    @tech_tools_mcp.tool()
    def compute_willr(
        kline_data: Annotated[dict, "Dictionary with 'High', 'Low', and 'Close' keys containing float lists."],
        period: Annotated[int, "Lookback period for Williams %R"] = 14
    ) -> dict:
        """
        Compute the Williams %R indicator using TA-Lib.

        Args:
            kline_data (dict): Dictionary with 'High', 'Low', and 'Close' keys.
            period (int): Lookback period for Williams %R calculation.

        Returns:
            dict: Dictionary with key 'willr' mapping to the list of Williams %R values.
        """
        # print("-------------------------CALLED COMPUTE WILLR--------------------------\n")
        df = pd.DataFrame(kline_data)
        willr = talib.WILLR(df["High"], df["Low"], df["Close"], timeperiod=period)
        return {"willr": willr.fillna(0).round(2).tolist()[-28:]}


async def get_tech_tools_mcp_async():
    current_file_path = os.path.abspath(__file__)
    client, all_tools = await get_mcp_studio_tools_async(current_file_path, tool_kit_name)
    return client, all_tools


if __name__ == '__main__':
    tech_tools_mcp.run(transport="stdio")
