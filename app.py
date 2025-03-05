"""
@File: apptest
@Date: 17/02/2025
@Author: Chris Tu
@Version: 1.0
@Description: ChatGPT written App for TW stock visualised analysis tools
"""
import os
import subprocess
import pandas as pd
import webbrowser
from dash import Dash, dcc, html, Input, Output, State
from threading import Timer

# 初始化 Dash App
app = Dash(__name__)

# `master/` 資料夾路徑
df_dir = os.path.join(os.path.dirname(__file__), "master")

# **🔹 更新股票代碼選單（每 5 秒檢查一次 `master/` 資料夾）**
app.layout = html.Div([
    html.H1("台股資訊視覺化分析工具"),

    # 1️⃣ 爬蟲輸入框 + 按鈕
    html.Div([
        html.Label("輸入股票代碼以獲取最新資料:"),
        dcc.Input(id="stock-input", type="text", placeholder="輸入股票代碼", style={'marginRight': '10px'}),
        html.Button("執行", id="run-crawler", n_clicks=0),
        html.Div(id="crawler-output", style={'marginTop': '10px', 'color': 'blue'}),
    ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '10px'}),

    # 2️⃣ 股票代碼選擇器(手動更新)
    html.Button("更新股票列表", id="update-stock-list", n_clicks=0, style={'marginTop': '10px'}),
    html.Label("選擇股票代碼:"),
    dcc.Dropdown(id='stock-selector', style={'marginBottom': '10px'}),

    # 3️⃣ 設定定時更新 `stock-selector`
    # dcc.Interval(
    #     id='interval-update-stock-list',
    #     interval=5000,  # 每 5 秒更新一次
    #     n_intervals=0
    # ),

    # 4️⃣ 選擇圖表數量
    html.Label("選擇圖表數量:"),
    dcc.Dropdown(
        id='chart-count',
        options=[{'label': f"{i} 張圖", 'value': i} for i in range(1, 6)],  # 最多支持 5 張圖
        value=1
    ),

    html.Div(id='charts-container'),
])


# 🕷 **執行爬蟲腳本**
@app.callback(
    Output("crawler-output", "children"),
    Input("run-crawler", "n_clicks"),
    State("stock-input", "value")
)
def run_crawler(n_clicks, stock_code):
    if n_clicks > 0 and stock_code:
        try:
            # 執行爬蟲腳本 main.py {code}
            result = subprocess.run(
                ["python", "main.py", stock_code],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return f"✅ 獲取成功：{stock_code}，數據已更新"
            else:
                return f"❌ 獲取失敗：{result.stderr}"
        except Exception as e:
            return f"⚠️ 執行錯誤：{str(e)}"
    return "請輸入股票代碼後點擊「執行」"


# **🔹 自動更新 `stock-selector` 下拉選單**
# @app.callback(
#     Output('stock-selector', 'options'),
#     Output('stock-selector', 'value'),
#     Input('interval-update-stock-list', 'n_intervals')
# )
# def update_stock_list(n_intervals):
#     # 重新讀取 `master/` 內的所有 `code.csv`
#     csv_files = [f for f in os.listdir(df_dir) if f.endswith(".csv")]
#     stock_codes = [f.split(".csv")[0] for f in csv_files]
#
#     # 如果有可用的代碼，則選擇第一個；否則回傳 None
#     value = stock_codes[0] if stock_codes else None
#     options = [{'label': code, 'value': code} for code in stock_codes]
#
#     return options, value

# **🔹 使用按鈕手動更新 `stock-selector` 下拉選單**
@app.callback(
    Output('stock-selector', 'options'),
    Output('stock-selector', 'value'),
    Input('update-stock-list', 'n_clicks'),
    State('stock-selector', 'value')
)
def update_stock_list(n_clicks, current_selected):
    """當使用者點擊按鈕時，更新股票代碼選單"""
    # 讀取 `master/` 內的所有 `code.csv`
    csv_files = [f for f in os.listdir(df_dir) if f.endswith(".csv")]
    stock_codes = [f.split(".csv")[0] for f in csv_files]

    # 如果當前選擇的代碼仍然存在，就保持不變；否則選擇第一個
    value = current_selected if current_selected in stock_codes else (stock_codes[0] if stock_codes else None)
    options = [{'label': code, 'value': code} for code in stock_codes]

    return options, value

# **動態生成圖表**
@app.callback(
    Output('charts-container', 'children'),
    [Input('chart-count', 'value'),
     Input('stock-selector', 'value')]
)
def update_charts(chart_count, stock_code):
    if not stock_code:
        return []

    # 讀取對應的 CSV 檔案
    df_file_path = os.path.join(df_dir, f"{stock_code}.csv")
    if not os.path.exists(df_file_path):
        return [html.Div(f"⚠️ 錯誤: {stock_code}.csv 文件不存在")]

    df = pd.read_csv(df_file_path)
    df['資料日期'] = pd.to_datetime(df['資料日期'], format='%Y%m%d')

    # 生成圖表選擇與顯示
    charts = []
    for i in range(chart_count):
        charts.append(html.Div([
            html.Label(f"圖表 {i + 1}: 選擇兩個 Y 軸變量"),
            dcc.Dropdown(
                id=f'y-axis-1-{i}',
                options=[{'label': col, 'value': col} for col in df.columns if col != '資料日期'],
                value=df.columns[2],
                style={'marginBottom': '10px'}
            ),
            dcc.Dropdown(
                id=f'y-axis-2-{i}',
                options=[{'label': col, 'value': col} for col in df.columns if col != '資料日期'],
                value=df.columns[5],
                style={'marginBottom': '20px'}
            ),
            dcc.Graph(id=f'chart-{i}')
        ], style={'border': '1px solid #ccc', 'padding': '10px', 'margin': '10px', 'width': '90%'}))
    return charts


# 更新每張圖表
for i in range(5):  # 預設支持最多 5 張圖表
    @app.callback(
        Output(f'chart-{i}', 'figure'),
        [Input(f'y-axis-1-{i}', 'value'),
         Input(f'y-axis-2-{i}', 'value'),
         Input('stock-selector', 'value')]
    )

    def update_chart(y1, y2, stock_code):
        if not y1 or not y2 or not stock_code:
            return {}

        df_file_path = os.path.join(df_dir, f"{stock_code}.csv")
        if not os.path.exists(df_file_path):
            return {}

        df = pd.read_csv(df_file_path)
        df['資料日期'] = pd.to_datetime(df['資料日期'], format='%Y%m%d')

        figure = {
            'data': [
                {
                    'x': df['資料日期'],
                    'y': df[y1],
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': y1,
                    'yaxis': 'y1',  # 使用左側 Y 軸
                    'fill': 'tozeroy',  # Area chart填滿
                    'fillcolor': 'rgba(0,0,255,0.1)',  # 40%透明度的藍色
                    'line': {'color': 'blue'}
                },
                {
                    'x': df['資料日期'],
                    'y': df[y2],
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': y2,
                    'yaxis': 'y2',  # 使用右側 Y 軸
                },
            ],
            'layout': {
                'title': f'{y1} 與 {y2} 的趨勢圖',
                'xaxis': {
                    'title': '資料日期',
                    # 設定日期格式顯示為 YYYY/MM
                    'tickformat': '%Y/%m',
                    # 如果需要確保X軸為時間軸，可強制類型為 date
                    'type': 'date'
                },
                'yaxis': {
                    'title': y1,
                    # 可依需求調整刻度距，如 dtick=10
                    # 'dtick': 10,
                },
                'yaxis2': {
                    'title': y2,
                    'overlaying': 'y',   # 疊加在 y 軸上
                    'side': 'right',     # 移到右側
                    # 可依需求調整刻度距，如 dtick=5
                    # 'dtick': 5,
                },
                'hovermode': 'x',   # 滑鼠移動時顯示該 x 座標的所有資料
                'legend': {'x': 0, 'y': 1},
                'plot_bgcolor': '#f9f9f9',
                'paper_bgcolor': '#ffffff',
                'font': {'family': 'Arial', 'size': 12, 'color': '#333'}
            }
        }
        return figure


# **瀏覽器自動開啟**
def open_browser():
    webbrowser.open("http://127.0.0.1:8050/")


# **啟動 Dash 伺服器**
if __name__ == '__main__':
    Timer(1, open_browser).start()  # 1 秒後開啟瀏覽器
    app.run_server(debug=False)
