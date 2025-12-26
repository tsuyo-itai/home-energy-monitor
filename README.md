# Home Energy Monitor (Echonet Lite Dashboard)

俺用の自宅のEchonet Lite対応機器（スマートメーター、太陽光発電システム）から電力情報を取得し、可視化するFletアプリケーションです。Raspberry Pi等のLinux環境での実行を想定しています。

※ 俺の自宅用に組んでいるのでおそらく他の環境では動かない

## 機能

- **電力収支の可視化**: 現在の消費電力と太陽光発電量をリアルタイム表示
- **EV充電推奨機能**: 余剰電力（発電量 > 消費量）がある場合にEV充電を推奨
- **ログ機能**: Echonet機器への要求(TX)と応答(RX)、およびタイムアウトエラー等の詳細ログを出力
- **モダンなUI**: Fletを使用したダークテーマのダッシュボード

## 必要要件

- Python 3.x
- ネットワーク接続（Echonet Lite機器と同じLAN内にあること）

## インストール

1. **リポジトリのクローンまたはファイルの配置**
   プロジェクトフォルダに移動します。

2. **仮想環境の作成と有効化（推奨）**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

## 設定

`echonet.py` 内の以下の定数を環境に合わせて変更してください（デフォルトはユーザー指定の構成になっています）。

- `TARGET_IP`: Echonet機器への中継を行うノードのIPアドレス（デフォルト: `192.168.11.10`）
- `ECHONET_PORT`: ポート番号（デフォルト: `3610`）

## 実行方法

### 1. デスクトップアプリとして実行（Raspberry Pi等）
HDMIディスプレイ等に直接GUIを表示する場合です。

```bash
python main.py
```

### 2. ブラウザでアクセスする場合
ヘッドレス環境のRaspberry Piで実行し、PCやスマホのブラウザから閲覧する場合です。

```bash
flet run --web --port 8550 main.py
```
実行後、ブラウザで `http://<RaspberryPiのIP>:8550` にアクセスしてください。

### 3. テスト実行（モックモード）
Echonet機器がない環境で、UIの動作確認を行うためのモードです。ランダムなダミーデータが表示されます。

**Mac/Linux:**
```bash
export ECHONET_MOCK=1
python main.py

# ブラウザ起動の場合
ECHONET_MOCK=1 flet run --web --port 8550 main.py 
```

## ログについて

実行中はコンソール（標準出力）に以下のような通信ログが表示されます。

```text
INFO - TX [SmartMeter] -> 192.168.11.10: 10814d320130010287016201c600
WARNING - RX [SmartMeter]: Timed out waiting for response.
```
応答がない場合は自動的にタイムアウトし、ログに警告が出力されます（アプリはクラッシュしません）。

## トラブルシューティング

- **画面が表示されない場合**: Fletは初回起動時に必要なバイナリをダウンロードすることがあります。インターネット接続を確認してください。
- **値が更新されない場合**: `TARGET_IP` が正しいか、Raspberry Piがネットワークに接続されているか確認してください。また、ファイアウォールがUDP 3610番ポートをブロックしていないか確認してください。
