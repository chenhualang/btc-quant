import pandas as pd
import mplfinance as mpf
from matplotlib import pyplot as plt


class KLineChart:
    def __init__(self, kline_data):
        self.kline_data = kline_data

    def generate_chart(self):
        # 将数据转换为DataFrame
        df = pd.DataFrame(self.kline_data, columns=["timestamp", "open", "high", "low", "close", "volume", "amount"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # 设置时间作为索引
        df.set_index("timestamp", inplace=True)

        # 画K线图和成交量
        mpf.plot(df, type='candle', volume=True, style='yahoo', title='K线图', ylabel='Price', ylabel_lower='Volume')

    def save_chart(self, filename='kline.jpg'):
        # 保存K线图
        plt.savefig(filename)

    @staticmethod
    def main():
        # 示例数据，替换成你的K线数据
        sample_kline_data = [
            [1704623400000, 0.5876, 0.5919, 0.5613, 0.5808, 3508765, 2015648.9846],
            [1704623100000, 0.5685, 0.589, 0.5682, 0.5876, 3904374, 2258449.4666],
            [1704622800000, 0.566, 0.5729, 0.5422, 0.5685, 5171142, 2894845.7004],
            [1704622500000, 0.5769, 0.5913, 0.5586, 0.566, 4415387, 2528204.2912],
            [1704622200000, 0.5697, 0.5842, 0.5508, 0.5769, 5181948, 2951328.8787]
        ]

        # 创建KLineChart对象
        kline_chart = KLineChart(sample_kline_data)

        # 生成K线图
        kline_chart.generate_chart()

        # 保存K线图
        kline_chart.save_chart()

if __name__ == "__main__":
    KLineChart.main()
