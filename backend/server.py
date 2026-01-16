from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from insert import InsertMetrics
from summary import CreateSummary
from typing import Optional

app = FastAPI()

#フロントエンドの静的ファイルを使用するためにマウント
app.mount("/frontend/static", StaticFiles(directory="../frontend/static"), name="static")

#既存インスタンスの作成
db = InsertMetrics()
summary_db = CreateSummary()

"""生データの取得"""
@app.get("/api/metrics")
def get_metrics(mode: str ="realtime"):
    metrics = db.get_metrics(mode)
    return metrics

@app.post("/api/metrics")
def post_metrics(json_data: dict):
    print(f"Inserting data: {json_data}")
    result = db.insert_cpu_utilization(json_data)
    if result > 0:
        return {"status": "success", "inserted": result}
    else:
        return {"status": "error", "message": "データ挿入に失敗しました"}


 #get_summary_dataのデータポイント設定
 #cpu_id: int = None = Union[int, None]と同じ意味
 #cpu_idの指定がない場合、Noneをデフォルト値として使用、全てのCPUの集計データが返される(interval_typeも同様)
"""集計加工ダミーデータの取得"""
@app.get("/api/summary")
def get_summary_data(start_timestamp: int, end_timestamp: int, cpu_id: Optional[int] = None): #interval_type: Optional[int] = None 集計データを使用する場合は必要！
    import random   # ダミーデータ生成用
    dummy_data = []
    points_count = 10
    interval = (end_timestamp - start_timestamp) // (points_count - 1) # 各mode期間内にpoints_count個のデータポイントを等間隔で配置、例: 6時間(21600秒÷(10-1))=2400秒
    for i in range(points_count):
        current_time = start_timestamp + (i  * interval) # x軸の計測時間ポイントの算出
        for cpu_id in range(4): # cpu_id0～3のダミーデータを生成
            base = 25 + (cpu_id * 5) # CPUごとのベース値を設定
            variation = random.randint(-15, 15) # ランダムな変動値を生成
            utilization = base + variation + (i * 1.5) # 時間経過に伴う変動を加える
            dummy_data.append({
                "bucket_timestamp": current_time,           
                "cpu_id": cpu_id,                        
                "avg_utilization": max(20, min(70, int(utilization))), 
                "sample_count": random.randint(1, 20),
            }) 
    return dummy_data

    #加工集計データで出力する場合はこっちを使用！
    #print(f"=== API呼び出し ===")
    #print(f"interval_type: {interval_type}")
    #summary_data = summary_db.get_summary_data(start_timestamp, end_timestamp, cpu_id, interval_type)
    #print(f"取得件数: {len(summary_data)}")
    
    #return summary_data

@app.post("/api/summary")
def create_summary(seconds: int = 600, index: int = 0):
    created_count = summary_db.create_summary_data(seconds, index)
    if created_count > 0:
        return {"status": "success", "created": created_count}
    else:
        return {"status": "error", "message": "集計データ作成に失敗しました"} 