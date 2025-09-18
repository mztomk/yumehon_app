APP_NAME = "ゆめほん（MVP）"

# ストーリー方向性プリセット
STORY_STYLES = ["ナチュラル", "冒険", "ファンタジー", "SF"]

# BGM（任意/無くても動く）
DEFAULT_BGM_PATH = "assets/bgm.mp3"
BGM_GAIN_DB = -5.0  # 小さめ（-12〜-18推奨）

# 出力
OUT_DIR = "outputs"
NARRATION_FILENAME = "narration.mp3"
NARRATION_WITH_BGM_FILENAME = "narration_with_bgm.mp3"
NARRATION_PATH = "outputs/narration.mp3"
NARRATION_WITH_BGM_PATH = "outputs/narration_with_bgm.mp3"

# プリセットキャラ
CHARACTER_PRESETS = {
    "叶都": {
        "gender": "男の子",
        "age": "3歳",
        "face": "活発、丸くて優しい目、髪はストレートで長い前髪、襟足は短い。",
        "clothes": "グレーの半袖シャツとカーキ色の短パン"
    },
    "由都": {
        "gender": "男の子",
        "age": "1歳",
        "face": "落ち着いた優しい目。少し癖っ毛で色白",
        "clothes": "紺色と茶色の半袖ボーダーシャツとベージュのパンツ"
    }
}

