import json
import boto3
import urllib.parse
from datetime import datetime, timezone, timedelta
import base64

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('DailyHealthLog')

def lambda_handler(event, context):
    try:
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('utf-8')

        parsed_data = urllib.parse.parse_qs(body)
        def get_val(key):
            return parsed_data.get(key, [''])[0]
        
        jst = timezone(timedelta(hours=+9), 'JST')
        now = datetime.now(jst)
        today = now.date().isoformat() #PK用 YYYY-MM-DD

        # Periodの表示名変換(ユーザーへのメッセージ用)
        period_label = "朝" if get_val('period') == 'morning' else "夕方"

        # CSVの項目 + 数値指標を統合したデータ構造
        item = {
            'Date': today,                        # PK 日付  YYYY-MM-DD
            'Period': get_val('period'),          # SK 朝or夕方?
            'Condition': get_val('condition'),      # 今朝の体調は？
            'IsRoutine': get_val('routine'),          # 朝のルーティーンはできたか？
            'WorkPlace': get_val('location'),        # 本日の学習場所は？
            'WorkDetail': get_val('study_content'), # 本日の学習内容は？
            'Notes': get_val('notes'),              # その他、気になることや懸念事項は？
            # 数値データ（分析用）
            'SleepingHours': get_val('sleeping_hours'), #　睡眠時間
            'EnergyMorning': get_val('energy_morning'), # 気力（朝）
            'EnergyEvening': get_val('energy_evening'), # 気力(夕方)
            'StaminaMorning': get_val('stamina_morning'), # 体力(朝)
            'StaminaEvening': get_val('stamina_evening'), # 体力(夕方)
            'Timestamp': now.isoformat()             # 登録日時　YYYY-MM-DD HH:MM:SS
        }

        table.put_item(Item=item)

        if get_val('period') == 'morning':
            response_html = f"""
            <div class="animate-bounce p-4 mb-4 text-sm text-blue-800 rounded-lg bg-blue-50 border border-blue-200">
                <span class="font-bold">{get_val('period')}の記録を完了しました</span><br>
                今日も一日、無理せず頑張りましょう！
                <button onclick="location.reload()" class="block mt-3 text-xs text-blue-600 underline text-right w-full">入力をやり直す</button>
            </div>
            """
        else:
            response_html = f"""
            <div class="animate-bounce p-4 mb-4 text-sm text-blue-800 rounded-lg bg-blue-50 border border-blue-200">
                <span class="font-bold">{get_val('period')}の記録を完了しました</span><br>
                お疲れ様でした！
                <button onclick="location.reload()" class="block mt-3 text-xs text-blue-600 underline text-right w-full">入力をやり直す</button>
            </div>
            """ 

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/html; charset=utf-8'},
            'body': response_html
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html; charset=utf-8'},
            'body': f"<div class='p-4 text-red-500 bg-red-50 rounded-lg'>エラー: {str(e)}</div>"
        }