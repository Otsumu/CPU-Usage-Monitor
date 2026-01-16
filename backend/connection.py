import sqlite3

"""データベース接続、テーブル設計
- CPUの使用率データを保存するための生データ、集計データの各テーブルを作成
"""
#定数定義
DATABASE_PATH = "../data/metrics.db"
CPU_NUMBERS = {i: f'cpu{i}' for i in range(16)}

class ConnectMetrics: #データベース接続、テーブル設計クラス
    def __init__(self, db_path: str="../data/metrics.db"):
        self.db_path = db_path
        self.CPU_NUMBERS = {i: f'cpu{i}' for i in range(16)}
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        #生データテーブル
        cursor.execute ('''
            CREATE TABLE IF NOT EXISTS cpu_load (
                id INTEGER PRIMARY KEY,
                timestamp INTEGER NOT NULL, --UNIX秒
                cpu_id INTEGER, -- cpu_name → cpu_id に改名
                utilization INTEGER
            )
       ''')
        #集計データテーブル
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cpu_load_summary (
                id INTEGER PRIMARY KEY,
                bucket_timestamp INTEGER, --バケット開始時刻、集計期間の特定のために設定
                interval_type INTEGER, --'10min''1hour'等の時間の間隔指定で利用
                cpu_id INTEGER,
                avg_utilization INTEGER,
                max_utilization INTEGER,
                min_utilization INTEGER,
                sample_count INTEGER
            )                  
        ''')
        #timestampとcpu_idにindexを貼付
        #cursor.execute('''
            #CREATE INDEX IF NOT EXISTS index_ts_cpuid ON cpu_load(timestamp,cpu_id);            
        #''')
        
        #bucket or timestampとinterval_time、cpu_idにindexを貼付
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS index_bucket_type_cpu_id ON cpu_load_summary(bucket_timestamp,interval_type,cpu_id);           
        ''')
    
        conn.commit()
        conn.close()
        print("データベースに接続できました")