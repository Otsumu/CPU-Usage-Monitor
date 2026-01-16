let globalCpuData = null; // グローバル変数でCPUデータを保持
let globalAllCpuData = null; // 全CPUデータを保持

//APIからデータを取得（生データ）
async function loadMetricsData(mode = "realtime") {
    try {
        const response = await fetch(`/api/metrics?mode=${mode}`);
        const data  = await response.json();
        return data;
    } 
    catch (error) {
        console.error('データ取得エラー:', error);
        return null;            
    }
}
// APIからデータを取得(集計データ)、データフロー制御のみ、loadSummaryData()を呼び出す
async function modeChange(mode) {
    try {        
        if (mode === "realtime") {
            const data = await loadMetricsData(mode);
            createCpuUsageChart(data, mode);
        } else if (mode === "custom") {
            console.log('時間指定モードが選択されました');
            return;
        } else  {
            const data = await loadSummaryData(mode);
            createCpuUsageChart(data, mode);
        } 
    } catch (error) {
        console.error('モード変更エラー:', error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    //初期データ(HTML)読み込み完了ですぐにグラフを生成、デフォルトは'realtime'
    loadMetricsData().then(data => {
        if (data) {
            createCpuUsageChart(data, 'realtime');
        }
    });
    //カレンダーの表示非表示設定
    const modeSelect = document.getElementById('modeSelect');
    if (modeSelect) {
        modeSelect.addEventListener('change', function() {
            const selectedMode = this.value;
            const customRangeInputs = document.getElementById('customRangeInputs');
            if (selectedMode === "custom")  {
                customRangeInputs.style.display = 'block'; // カレンダーを表示
            } else {
                customRangeInputs.style.display = 'none'; // カレンダーを非表示
                modeChange(selectedMode);
            }
        });
    }

    //CPU毎に表示させる
    const selectCpu = document.getElementById('cpuSelector');
    if (selectCpu) {
        selectCpu.addEventListener('change', function() {
            const selectedCpu = this.value;
            if (globalCpuData) {
                const cpuKey = "cpu" + selectedCpu;
                if (cpuChart) {
                    cpuChart.data.datasets.forEach((dataset) => {
                        dataset.hidden = (dataset.label !== cpuKey);
                    });
                    cpuChart.update();
                }    
            }
        })
    }
})

    //カスタムレンジのボタンイベント
    const customRangeButton = document.getElementById('customRangeButton');
    if (customRangeButton) {
        customRangeButton.addEventListener('click', async function() {
            const data = await fetchCustomRange();
            if (data) {
                createCpuUsageChart(data, 'custom');
            }
        });
    }

// 指定した時間の入力フィールドデータを取得
async function fetchCustomRange() {
    try {
        const startTimeInput = document.getElementById('startTime'); //入力値の取得
        const endTimeInput = document.getElementById('endTime');

        const startTimeValue = startTimeInput.value;
        const endTimeValue = endTimeInput.value;

        if (!startTimeValue || !endTimeValue) {
            alert('開始時刻と終了時刻を入力してください！');
            return;
        }

        const startDate = new Date(startTimeValue); // 日付オブジェクトに変換
        const endDate = new Date(endTimeValue);

        if (startDate >= endDate) {
            alert('開始時刻は終了時刻よりも早くなければなりません！');
            return;
        }
        
        const startTimestamp = Math.floor(startDate.getTime() / 1000); //ミリ秒→秒に変換、小数点以下切り捨て！
        const endTimestamp = Math.floor(endDate.getTime() / 1000);

        console.log("開始時刻:", startTimestamp, "終了時刻:", endTimestamp); 
        const response = await fetch(`/api/summary?start_timestamp=${startTimestamp}&end_timestamp=${endTimestamp}`);
        const data = await response.json();
        createCpuUsageChart(data, 'custom');
        return data;

    } catch (error) {
        console.error('指定時間エラー：', error);
        alert('指定時間を取得できませんでした')
    }
}

//生データ専用の処理関数(mode=realtimeの時のみJSONデータを使用)
function processCpuData(data, mode) {
    const cpuData = {};
    Object.keys(data).forEach(cpuName => {
        cpuData[cpuName] = data[cpuName].map(point => ({
            x : mode === "realtime" ? new Date(point.timestamp * 1000) : point.timestamp,
            y : point.utilization 
        }))
    })
    //10の倍数に切り上げてグラフの見た目を良くする
    const maxUsage = Math.max(...Object.values(cpuData).flat().map(data => data.y));
    const suggestedMax = Math.ceil(maxUsage / 10) * 10;

    return { cpuData, suggestedMax };
}

//集計データを取得する関数
async function loadSummaryData(mode) {
    try {
        const timeRange = calculateTimeRange(mode);
        let interval_type;
        if (mode === "30minutes") {
            interval_type = 1;
        } else if (mode === "1hour") {
            interval_type = 2;
        } else if (mode === "1day") {
            interval_type = 3;
        } else if (mode === "specifictime") {
            interval_type = 2; // カスタムレンジは1時間間隔で取得
        }
        
        const url = `/api/summary?start_timestamp=${timeRange.start}&end_timestamp=${timeRange.end}&interval_type=${interval_type}`;
        console.log("リクエストURL:", url);

        const response = await fetch(`/api/summary?start_timestamp=${timeRange.start}&end_timestamp=${timeRange.end}&interval_type=${interval_type}`);
        const data = await response.json()

        return data;
    }
    catch (error) {
        console.error('データ取得エラー:', error);
        return null;  
    }
}
//calculateTimeRange() → {start: 時刻, end: 時刻}オブジェクトを返す
function calculateTimeRange(mode) {
    const now = Math.floor(Date.now() / 1000);
    if (mode === "30minutes") {
        return {
            start: now - (5 * 3600), // 5時間前からのデータを取得
            end: now
        };
    } else if (mode === "1hour") {
        return {
            start: now - (5 * 3600), // 5時間前からのデータを取得
            end: now 
        };
    } else if (mode === "1day") {
        return {
            start: now - (7 * 24 * 3600), // 7日前からのデータを取得
            end: now  
        };
    } else if (mode === "custom") {
        return {
            start: now - (24 * 3600),
            end: now
        }
    }
}

//CPU使用率グラフ(全体)作成 
//各モードのdataを受け取り、各モードでのグラフを生成する
function createCpuUsageChart(data, mode = 'realtime') {
    //2次元描画モードのグラフを作成
    const context = document.getElementById('cpuLoadChart').getContext('2d');
    //processCpuData()とprocessSummaryData()の呼び出し
    let cpuData, suggestedMax;
    if (mode === "realtime") {
        const result = processCpuData(data, mode);
        cpuData = result.cpuData;
        suggestedMax = result.suggestedMax;
    } else  {
        const result = processSummaryData(data, mode); 
        cpuData = result.cpuData;
        suggestedMax = result.suggestedMax;
    }
    const timeSettings = getTimeSettings(mode);
    console.log("suggestedMax:", suggestedMax);

    // chart.jsのデータを作成
    const datasets = Object.keys(cpuData).map((cpuName, index) => {
        const chartData = mode === "realtime" ? cpuData[cpuName].filter((_, index) => index % 3 === 0) : cpuData[cpuName];
        return {     
            label: cpuName,
            data: chartData,
            borderColor: cpuColor(index),
            backgroundColor: cpuColor(index),
            tension: 0,
            fill: false, 
            pointRadius: 2,
            pointHoverRadius: 4
        };
    });

    // 既存のチャートがあれば破棄
    if (cpuChart) {
        cpuChart.destroy();
    }

    // 新しいチャートを作成
    cpuChart = new Chart(context, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        font: {
                            size: 16
                        }
                    }
                }
            },
            scales: {
                x: { 
                    type: 'time',
                    stepSize: timeSettings.stepSize,
                    title: { 
                        display: true, 
                        text: timeSettings.title,
                        font: {
                            size: 15
                        }       
                    },
                    time: {
                        unit: timeSettings.unit,
                        displayFormats: {
                            [timeSettings.unit]: timeSettings.displayFormat
                        }
                    },
                    ticks: {
                        maxTicksLimit: timeSettings.maxTicksLimit,
                        autoSkip: true,
                        padding: 10,
                        font: {
                            size: 15
                        }   
                    }
                },
                y: { 
                    beginAtZero: true,
                    max: suggestedMax,
                    ticks: {
                        stepSize: 10,
                        padding: 10,
                        font: {
                            size: 15
                        }                           
                    },
                    title: { 
                        display: true, 
                        text: 'CPU使用率(%)',
                        font: {
                            size: 15
                        }
                    },
                }
            }
        }    
    });
    if (!globalAllCpuData) {
        globalAllCpuData = cpuData; // 全CPUデータを保存
    }
    globalCpuData = globalAllCpuData;
    console.log("globalCpuDataに保存:", globalCpuData);  
}

//集計処理専用の処理関数
function processSummaryData(data, mode) {
    try {
        console.log("avg_utilization の値:", data.map(d => d.avg_utilization));

        const cpuData = {};
        data.forEach(item => {
        const cpuKey = `cpu${item.cpu_id}`;
        if(!cpuData[cpuKey]) cpuData[cpuKey] = [];
            cpuData[cpuKey].push({
            x : new Date(item.bucket_timestamp * 1000),
            y : item.avg_utilization 
        });
    })
    //10の倍数に切り上げてグラフの見た目を良くする
    const maxUsage = Math.max(...Object.values(cpuData).flat().map(data => data.y));
    const suggestedMax = Math.ceil(maxUsage / 10) * 10;

    return { cpuData, suggestedMax };
    }
    catch (error) {
        console.error("データ取得エラー：", error);
    }
}

//cpuのグラフ色生成
function cpuColor(index) {
    const baseColors = ['#06B6D0', '#8B5CF3', '#F97312', '#DC2620', '#10B982', '#F59E0C', '#EF4445', '#8B5A2C'];
    const colorSteps = 16;

    if (index < baseColors.length) {
        return baseColors[index];
    } else {
        const hue = (index * 360 / colorSteps) % 360;
        return  `hsl(${hue}, 70%, 50%)`;
    }
}

//各モードに応じた時間設定
function getTimeSettings(mode) {
    switch(mode) {
        case 'realtime':
            return {
                unit: 'minute',
                displayFormat: 'HH:mm',
                stepSize: 10,      // 10分ごとに目盛り
                maxTicksLimit: 20, 
                title: '時刻(リアルタイム)'
            };
        case '30minutes':
            return {
                unit: 'minute',
                displayFormat: 'HH:mm', 
                stepSize: 15, // 30分ごとに目盛り
                maxTicksLimit: 10, 
                title: '時刻(30分間隔)'
            };
        case '1hour':
            return {
                unit: 'hour',
                displayFormat: 'HH:mm',
                stepSize: 1,       // 1時間ごとに目盛り
                maxTicksLimit: 6, 
                title: '時刻(1時間間隔)'
            };
        case '1day':
            return {
                unit: 'day',
                displayFormat: 'MM-dd',
                stepSize: 1,
                maxTicksLimit: 7, // 1週間で7個の目盛り
                title: '時刻(1日間隔)'
            };
        default:
            return {
                unit: 'hour',
                displayFormat: 'MM-dd HH:mm',
                stepSize: 1,
                maxTicksLimit: 6, // 1週間で7個の目盛り
                title: '時刻'
            };
    }
}

//グローバル変数でcpuChartを定義、生成
let cpuChart = null;
