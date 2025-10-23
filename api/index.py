from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ユーザーIDとトークンを保存する辞書（本番では DB 等を利用してください）
user_tokens = {}

# Dify からの認証に使う API キー（Dify の管理画面と一致させてください）
YOUR_PRESET_API_KEY = "YOUR_SECRET_KEY"

@app.route('/bind', methods=['POST'])
def bind_user():
    """
    Bubble から送られてくる user_id、access_token、refresh_token を保存します。
    """
    data = request.get_json()
    user_id = data.get('user_id')
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    user_tokens[user_id] = {
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    return jsonify({'status': 'ok'})

@app.route('/retrieval', methods=['POST'])
def retrieval():
    """
    Dify からの問い合わせを受け取り、Google Drive を検索して結果を返します。
    """
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {YOUR_PRESET_API_KEY}":
        # API キーが一致しない場合は認証エラー
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    knowledge_id = data.get('knowledge_id')
    query = data.get('query')

    # 保存しておいたトークンを取得
    tokens = user_tokens.get(knowledge_id)
    if not tokens:
        return jsonify({'records': []})

    access_token = tokens['access_token']
    # 必要に応じて refresh_token を使い、アクセストークンの更新処理を実装してください。

    # Google Drive API を呼び出し、ファイルを検索
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'q': f"name contains '{query}' or fullText contains '{query}'",
        'fields': 'files(id,name,webViewLink)'
    }
    drive_res = requests.get('https://www.googleapis.com/drive/v3/files',
                             headers=headers, params=params)
    files = drive_res.json().get('files', [])

    # Dify 用の records 形式に整形して返却
    records = []
    for f in files:
        records.append({
            'metadata': {
                'path': f.get('webViewLink', ''),
                'description': ''
            },
            'score': 1.0,
            'title': f.get('name'),
            'content': ''
        })
    return jsonify({'records': records})
