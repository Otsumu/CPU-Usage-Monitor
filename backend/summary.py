import sqlite3

"""集計処理を行うクラス
- CPUの使用率データを指定された時間間隔で集計し、データベースに保存する
- 集計データを取得するためのメソッドも提供
"""

class CreateSummary: #集計処理
    #10分、30分、1時間、１日の時間インターバルをクラス変数で定義
    INTERVAL_TYPE = (600, 1800, 3600, 86400)  

    #CPU0,1,2,3の４つだけなのでこのクラスではこの定義は無視！
    def __init__(self, db_path: str="../data/metrics.db"):
        self.db_path = db_path
        #self.CPU_NUMBERS = {i: f'cpu{i}' for i in range(16)}

    def create_summary_data(self, seconds, index):
        if index < 0 or index >= len(CreateSummary.INTERVAL_TYPE):
            raise ValueError(f"有効なインデックスを選択してください: {index}")
        
        seconds = CreateSummary.INTERVAL_TYPE[index]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        created_count = 0

        try:
            cursor.execute("""
                SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time
                            FROM cpu_load
                """)
            time_range = cursor.fetchone() #fetchone()での返り値はtuple！
            if not time_range or not time_range[0]:
                print("集計データがありません")
                return 0
            
            min_time, max_time = time_range    
            cursor.execute("SELECT DISTINCT cpu_id FROM cpu_load ORDER BY cpu_id")
            exsiting_cpu_ids = [row[0] for row in cursor.fetchall()]
            current_time = min_time
            while current_time <= max_time:
                next_time = current_time + seconds
                        
                for cpu_id in exsiting_cpu_ids:    
                    cursor.execute("""
                    SELECT
                        AVG(utilization) as avg_util,
                        MAX(utilization) as max_util,
                        MIN(utilization) as min_util,
                        COUNT(*) as sample_count
                    FROM cpu_load
                    WHERE timestamp >= ? AND timestamp < ? AND cpu_id = ?
                        """,(current_time, next_time, cpu_id))

                    result = cursor.fetchone()
                    avg_util = int(result[0]) if result[0] is not None else 0
                    max_util = int(result[1]) if result[1] is not None else 0 
                    min_util = int(result[2]) if result[2] is not None else 0
                    sample_count = int(result[3]) if result[3] is not None else 0

                    cursor.execute("""
                    INSERT INTO cpu_load_summary(bucket_timestamp, interval_type, cpu_id, avg_utilization, max_utilization, min_utilization, sample_count)
                        VALUES(?, ?, ?, ?, ?, ?, ?)
                    """, (current_time, index, cpu_id , avg_util, max_util, min_util, sample_count))
                    created_count += 1

                current_time += seconds

            conn.commit()
            print(f"{created_count}件のデータが作成できました")
            return created_count        
        
        except Exception as error:
            print(f"予期しないエラー：{error}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    #時間別、CPU別データの取得と表示をdef get summary_data()で定義！
    #cpu_id=NoneはCPU別データ取得時に使用するためのパラメータ
    def get_summary_data(self, start_timestamp, end_timestamp, cpu_id= None, interval_type= None): 
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # Row_factoryを設定して、列名をキーに値にアクセス！
        cursor = conn.cursor()
        query = """
            SELECT bucket_timestamp, cpu_id, avg_utilization, max_utilization, min_utilization, sample_count
            FROM cpu_load_summary
            WHERE bucket_timestamp BETWEEN ? AND ?
        """
        params = [start_timestamp, end_timestamp]

        if cpu_id is not None:
            query += " AND cpu_id = ?"
            params.append(cpu_id)

        if interval_type is not None:
            query += " AND interval_type = ?"
            params.append(interval_type)

        query += " ORDER BY bucket_timestamp"
        return cursor.execute(query, params).fetchall() 


