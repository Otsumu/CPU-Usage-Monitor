import sqlite3
from collections import defaultdict

"""データ挿入を行うクラス
- CPUの使用率データをJSON形式で受け取り、データベースに挿入する
- リアルタイムのCPU使用率データを取得する
- CPU使用率データをCPUごとにグループ化して取得する
"""

class InsertMetrics: #データ挿入クラス
    def __init__(self, db_path: str="../data/metrics.db"):
        self.db_path = db_path
        self.CPU_NUMBERS = {i: f'cpu{i}' for i in range(16)}

    def insert_cpu_utilization(self, json_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        inserted_count = 0

        try:    
            all_metrics = []
            for resource_metrics in json_data.get('resourceMetrics',[]):
                for scope_metrics in resource_metrics.get('scopeMetrics',[]):
                    all_metrics.extend(scope_metrics.get('metrics',[]))

            for metric in all_metrics:
                if metric.get('name') == 'system.cpu.utilization':
                    data_points = metric.get('gauge', {}).get('dataPoints', [])
                    #ループの都度初期化
                    for data_point in data_points:
                        cpu_id = None
                        idle_rate = 0
                        timestamp = None
                        
                        attributes = data_point.get('attributes', [])
                        for attr in attributes:
                            if attr.get('key') == 'cpu':
                                cpu_name = attr.get('value', {}).get('stringValue', '')
                                if cpu_name.startswith('cpu') :
                                    try:
                                        cpu_id = int(cpu_name.replace('cpu',''))
                                    except ValueError:
                                        cpu_id = None
                            if attr.get('key') == 'state':
                                state = attr.get('value', {}).get('stringValue', '')
                                if state == 'idle':
                                    idle_rate = data_point.get('asDouble', 0)

                        # タイムスタンプの取得
                        # timeUnixNanoが存在する場合、ナノ秒単位のタイムスタンプを取得
                        # もしtimeUnixNanoが存在しない場合は、0をデフォルト値として使用
                        # timeUnixNanoはナノ秒単位なので、秒単位に変換する必要がある
                        timestamp_nano = data_point.get('timeUnixNano', 0)
                        if timestamp_nano:
                            try:
                            #ナノ秒（10⁻⁹秒）を秒単位に変換するため、10億で割る
                                timestamp_nano_int = int(timestamp_nano)
                                timestamp = timestamp_nano_int // 1000000000
                            except (ValueError, TypeError):
                                timestamp = None
                        # CPU使用率の計算
                        utilization = (1 - idle_rate) * 100
                        utilization_int = int(utilization)

                        if cpu_id is not None and timestamp is not None:
                            cursor.execute('''
                                INSERT INTO cpu_load(timestamp, cpu_id, utilization)
                                VALUES(?, ?, ?)
                            ''', (timestamp, cpu_id, utilization_int))  
                            inserted_count += 1
            
            conn.commit()
            print(f"{inserted_count}件のデータが挿入されました")
            return inserted_count

        except Exception as error:
            print(f"予期しないエラー：{error}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_metrics(self, mode ="realtime"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()    
        try:
            if mode == "realtime":
                query = """
                    SELECT timestamp, cpu_id, utilization 
                    FROM cpu_load 
                    ORDER BY timestamp, cpu_id
                """
            else:
                raise ValueError("いずれかの時間を指定してください")
            
            cursor.execute(query)
            rows = cursor.fetchall()
           
            series_data = defaultdict(list)
            if mode == "realtime":
                for bucket_or_ts, cpu_id, utilization in rows:
                    label = self.CPU_NUMBERS.get(cpu_id, f'cpu{cpu_id}')
                    series_data[label].append({
                    "timestamp": bucket_or_ts,
                    "utilization": utilization
                })
            else:
                for bucket_or_ts, cpu_id, utilization, count_value in rows:
                    print(f"COUNT : {count_value}")
                    label = self.CPU_NUMBERS.get(cpu_id, f'cpu{cpu_id}')
                    series_data[label].append({
                        "timestamp": bucket_or_ts,
                        "utilization": utilization
                })
            return dict(series_data)
                   
        except Exception as error:
            print(f"取得エラー: {error}")
            return {}
        finally:
            conn.close()    

