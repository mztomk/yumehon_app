# utils.py
# utils.py の冒頭部分を以下に置き換え
import os
import re
from google.cloud import texttospeech
from pydub import AudioSegment
import constants as ct
import base64
import requests
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import os
import json
from dotenv import load_dotenv
import streamlit as st
from pydub import AudioSegment
import imageio_ffmpeg as ffmpeg
import shutil

# FFmpeg設定の修正
try:
    # imageio-ffmpegからパスを取得
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()
    
    # FFprobeのパスも設定（ffmpegと同じディレクトリにある）
    ffprobe_path = ffmpeg_path.replace('ffmpeg', 'ffprobe')
    if os.name == 'nt':  # Windows
        ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
    
    # システムのFFmpegを探す（フォールバック）
    if not os.path.exists(ffprobe_path):
        system_ffprobe = shutil.which('ffprobe')
        if system_ffprobe:
            ffprobe_path = system_ffprobe
        else:
            st.warning("FFprobeが見つかりません。音声処理でエラーが発生する可能性があります。")
    
    # pydubにパスを設定
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    AudioSegment.ffprobe = ffprobe_path
    
    st.success(f"FFmpeg設定完了: {ffmpeg_path}")
    st.success(f"FFprobe設定完了: {ffprobe_path}")
    
except Exception as e:
    st.error(f"FFmpeg設定エラー: {e}")
    # フォールバック：システムのFFmpegを使用
    AudioSegment.converter = "ffmpeg"
    AudioSegment.ffmpeg = "ffmpeg"
    AudioSegment.ffprobe = "ffprobe"




def ensure_outdir():
    os.makedirs(ct.OUT_DIR, exist_ok=True)

def build_character_cards(main_character: str, main_info: dict, sub_characters: list[str], sub_infos: list[dict]) -> dict:
    """
    主人公とサブキャラからキャラカード辞書を作成
    {
        "叶都": {"gender": "男の子", "face": "...", "clothes": "..."},
        "ママ": {"gender": "女の子"}
    }
    """
    characters = {}

    # 主人公
    characters[main_character] = main_info

    # サブキャラ
    for name, info in zip(sub_characters, sub_infos):
        if name.strip():
            characters[name] = info

    return characters



def build_script(client, main_character: str, main_info: dict, sub_characters: list[str], sub_infos: list[dict], style: str, theme: str) -> str:
    """
    gpt-4o-mini を使って読み聞かせ用の台本を生成する。
    台本には名前と性別のみを入れる。
    """
    # 主人公 → 名前と性別だけ
    main_desc = f"{main_character}（{main_info['gender']}）"

    # サブキャラ → 名前と性別だけ
    subs_info = []
    for name, info in zip(sub_characters, sub_infos):
        if name.strip():
            subs_info.append(f"{name}（{info['gender']}）")
    subs_text = "、".join(subs_info) if subs_info else "なし"

    # プロンプト
    prompt = f"""
あなたは子ども向けの絵本作家です。
以下の条件に従って、3分以内の短い物語を作ってください。

- 主人公: {main_desc}
- 他の登場人物: {subs_text}
- お話のスタイル: {style}
- お話のテーマ: {theme}

条件:
- 3〜6歳の子ども向けに分かりやすく。
- 短い文を中心に書く。
- 句読点をできるだけ多く入れる。
- **絶対にふりがな（かなと、ゆいと等）は書かないこと。**
- 名前は必ず「叶都」「由都」と漢字だけで表記すること。
- 出力は本文のみ。『シーン1』などの見出しや番号は絶対に入れない。
- 出力は段落ちょうど5つ。6つ以上にも4つ以下にもしてはいけない。
- 各段落の間は必ず一行空ける。
- 最後の段落は必ず『おしまい』で終える。
- TTSでそのまま読み上げられることを想定して、余計な補足を入れない。

構成（段落ごとに内容を割り当てること）:
1段落目: 主人公と登場人物の状況説明  
2段落目: 何か出来事が起きる  
3段落目: 出来事の解決へと向かう  
4段落目: 解決  
5段落目: まとめ、最後は必ず『おしまい』と入れる

出力フォーマット（絶対に守ること）:
[段落1の本文]

[段落2の本文]

[段落3の本文]

[段落4の本文]

[段落5の本文（最後は必ず『おしまい』で終える）]
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは優しい絵本作家です。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()




def add_breaks_for_ssml(text: str) -> str:
    """
    テキストに句読点や「！」「？」ごとに <break> を挿入しつつ、
    固有名詞の読みを <sub> タグで指定する。
    """

    # --- 固有名詞の読み辞書 ---
    readings = {
        "由都": "ゆいと",
        "叶都": "かなと",
    }

    # 読み置換（表示は元の漢字、発音だけ alias）
    for word, yomi in readings.items():
        text = text.replace(word, f"<sub alias='{yomi}'>{word}</sub>")

    # 「、」「。」「！」「？」ごとに休符を挿入
    import re
    text = re.sub(r'([、])', r'\1<break time="600ms"/>', text)
    text = re.sub(r'([！？!?])', r'\1<break time="1000ms"/>', text)
    text = re.sub(r'([。])', r'\1<break time="1500ms"/>', text)
    text = re.sub(r'\n+', '<break time="1500ms"/>', text)

    return f"<speak><p>{text}</p></speak>"





def synthesize_tts_google(ssml: str, out_path: str, tts_gender: str = "女のひと") -> str:
    try:
        credentials_info = st.secrets["gcp_service_account"]
        client = texttospeech.TextToSpeechClient.from_service_account_info(dict(credentials_info))

        if tts_gender == "女のひと":
            voice_name = "ja-JP-Wavenet-A"
        else:
            voice_name = "ja-JP-Wavenet-C"

        synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.8,
            pitch=-3.0,
            volume_gain_db=0.0
        )

        resp = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        with open(out_path, "wb") as f:
            f.write(resp.audio_content)

        return out_path
    except Exception as e:
        st.error(f"TTS生成に失敗しました: {e}")
        return None


def synthesize_blocks(blocks, tts_gender="女のひと"):
    ensure_outdir()
    block_audios_paths = []
    durations = []

    for i, block in enumerate(blocks):
        ssml = add_breaks_for_ssml(block)
        out_path = f"outputs/block_{i+1}.mp3"
        result = synthesize_tts_google(ssml, out_path, tts_gender)
        # ファイルが存在し、かつサイズが0でないことを確認
        if result is None or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            st.error(f"音声ファイルの生成に失敗しました: {out_path}")
            continue

        try:
            audio = AudioSegment.from_file(out_path)
        except Exception as e:
            st.error(f"音声ファイルの読み込みに失敗しました: {out_path}\n{e}")
            continue

        block_audios_paths.append(out_path)
        durations.append(len(audio) / 1000)  # 秒

    return block_audios_paths, durations


def split_into_scenes(story_text: str, characters: dict) -> list[str]:
    """
    台本を空行ごとに分割して5シーンにする。
    各シーンにはキャラカード情報を付け加える。
    """
    # キャラ情報を文字列化
    char_text = "\n".join(
        [f"- {name}: {info.get('gender','')} {info.get('age','')} {info.get('face','')} {info.get('clothes','')}" for name, info in characters.items()]
    )

    # 台本を段落ごとに分割
    blocks = [b.strip() for b in story_text.split("\n\n") if b.strip()]

    # 5つに制限
    blocks = blocks[:5]

    # 各ブロックにキャラ情報を付加
    scenes = [f"{block}\n\nキャラクター設定:\n{char_text}" for block in blocks]

    return scenes, blocks


def extract_scenes(client, story_text: str, characters: dict) -> list[str]:
    """
    GPTで物語から代表的な5シーンを抽出。
    キャラカードを必ず反映させる。
    """
    char_text = "\n".join(
        [f"- {name}: {info.get('gender','')} {info.get('face','')} {info.get('clothes','')}" for name, info in characters.items()]
    )

    prompt = f"""
次の物語を5つのシーンに分けてください。
各シーンの説明には必ず以下のキャラクター設定を反映してください。

キャラクター設定:
{char_text}

物語:
{story_text}

出力フォーマット（絶対に守ること）:
- 箇条書きで5行だけ
- 1行目では話は展開せず登場人物や状況の説明のみを書く
- 各行の登場人物にキャラクター設定を必ず反映させる
- 数字や「シーン1:」などは不要
- 最後は必ずハッピーエンドで終わるようにする

"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    #scenes = res.choices[0].message.content.strip().split("\n")
    #scenes = [s.strip("12345. ") for s in scenes if s.strip()]
    #return scenes[:5]


def generate_one_scene(client, scene: str, i: int, characters: dict) -> str:
    """1枚の挿絵を生成して保存（画像参照なし）"""
    prompt = (
        "やわらかい水彩画風の絵本イラスト。\n"
        "紙の質感が残るような水彩のにじみ。\n"
        "パステルトーンで、彩度を抑えた淡く優しい色合い。\n"
        "線は細く繊細で、鉛筆で下書きをしたような柔らかさ。\n"
        "全体は温かみがありながらも淡く、落ち着いたトーン。\n"
        "背景は柔らかく霞み、穏やかな立体感を出す。\n"
        "キャラクターは素朴で丸みのある表情、愛らしい雰囲気。\n"
        "キャラクターのサイズはは少し小さめに書く\n"
        "絵の中に文字は入れない。\n"
        f"シーン: {scene}\n"
        f"キャラクター設定: {characters}\n"
    )

    out_path = os.path.join("outputs", f"scene_{i+1}.png")

    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",  # 速さ優先
            n=1
        )

        # Base64データをデコードして保存
        image_b64 = response.data[0].b64_json
        image_data = base64.b64decode(image_b64)
        with open(out_path, "wb") as f:
            f.write(image_data)

        return out_path

    except Exception as e:
        print("画像生成失敗:", e)
        return None







def generate_illustrations(client, scenes: list[str], characters: dict) -> list[str]:
    """5枚の挿絵を並列で生成"""
    image_paths = []
    with ThreadPoolExecutor(max_workers=5) as executor:  # 最大5枚同時
        futures = [executor.submit(generate_one_scene, client, s, i, characters) for i, s in enumerate(scenes)]
        for f in futures:
            image_paths.append(f.result())  # 完了した順に取得
    return image_paths








def mix_bgm(narration_path: str, bgm_path: str, out_path: str, bgm_gain_db: float = ct.BGM_GAIN_DB) -> str:
    """
    pydubでBGMをミックス
    - BGMは最初から再生
    - ナレーションは3秒遅れて開始
    - 朗読終了後にBGMを5秒残して3秒フェードアウト
    """
    if not os.path.exists(bgm_path):
        return narration_path

    narration = AudioSegment.from_file(narration_path)
    bgm = AudioSegment.from_file(bgm_path) + bgm_gain_db

    # ナレーションの前に3秒の無音を追加
    delay = 3000  # ms
    narration = AudioSegment.silent(duration=delay) + narration

    # BGMを (朗読+遅延) の長さ + 5秒 に合わせてループ
    total_length = len(narration) + 5000
    bgm_loop = AudioSegment.silent(duration=0)
    while len(bgm_loop) < total_length:
        bgm_loop += bgm
    bgm_loop = bgm_loop[:total_length]

    # BGMだけ3秒でフェードアウト
    bgm_loop = bgm_loop.fade_out(3000)

    # ミックス（ナレーションは3秒遅れて入る）
    mixed = narration.overlay(bgm_loop)

    mixed.export(out_path, format="mp3")
    return out_path




def create_story_video(image_paths, block_audio_paths, blocks, out_path="outputs/storybook.mp4"):
    """
    image_paths        : 画像ファイルのリスト
    block_audio_paths  : ブロックごとの音声ファイルのリスト
    blocks             : 台本テキストのリスト
    """

    clips = []
    for i, (img, audio_path, text) in enumerate(zip(image_paths, block_audio_paths, blocks)):
        if os.path.exists(img) and os.path.exists(audio_path):
            # 音声の長さを取得
            audio = AudioFileClip(audio_path)
            dur = audio.duration

            # 画像クリップを作成して音声を設定
            clip = ImageClip(img).set_duration(dur).set_audio(audio)

            clips.append(clip)

    # クリップを連結
    video = concatenate_videoclips(clips, method="compose")

    # 動画を書き出し
    video.write_videofile(out_path, fps=24)

    return out_path



from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

def add_bgm_to_video(video_path, bgm_path, out_path="outputs/storybook_final.mp4", bgm_gain=-8):
    video = VideoFileClip(video_path)
    narration = video.audio
    bgm = AudioFileClip(bgm_path).volumex(10 ** (bgm_gain / 20))  # dB調整

    # BGMを動画全体にループ
    bgm = bgm.audio_loop(duration=video.duration)

    # ナレーションとBGMを合成
    mixed_audio = CompositeAudioClip([narration, bgm])
    final_video = video.set_audio(mixed_audio)

    final_video.write_videofile(
        out_path,
        fps=24,
        codec="libx264",       # H.264 映像
        audio_codec="aac"      # AAC 音声
    )

    return out_path




