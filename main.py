# main.py
import os
import streamlit as st
import components as ui
import constants as ct
import utils
from dotenv import load_dotenv
from openai import OpenAI

# .env の読み込み
load_dotenv()

# OpenAI client を作成（台本生成用）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#google_project_id = os.getenv("GOOGLE_PROJECT_ID")
#google_client_email = os.getenv("GOOGLE_CLIENT_EMAIL")
#google_private_key = os.getenv("GOOGLE_PRIVATE_KEY")

# ▼ GCPキーの設定（Google TTS用）
#if os.path.exists("yumehon.json"):
    #os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("yumehon.json")

# ページ設定
st.set_page_config(page_title=ct.APP_NAME, page_icon="📚", layout="centered")
ui.header()

# --- 入力フォーム（components.py） ---
form = ui.input_form()

if form["generate"]:
    # キャラカード作成
    characters = utils.build_character_cards(
        form["main_character"],
        form["main_info"],
        form["sub_characters"],
        form["sub_infos"]
    )

    if not form["main_character"].strip():
        ui.show_error("主人公の名前を入力してください。")
        st.stop()

    # プレースホルダーを用意
    placeholder = st.empty()

    # GIFを表示
    if os.path.exists("assets/chottomatte.gif"):
        placeholder.image("assets/chottomatte.gif", caption="おはなしを作っているよ...", use_container_width=True)

    # GPTで台本生成
    with st.spinner("台本を作成中…"):
        story_text = utils.build_script(
            client,
            form["main_character"],   # 名前
            form["main_info"],        # 性別や特徴の辞書
            form["sub_characters"],
            form["sub_infos"],
            form["style"],
            form["theme"],
        )

    # SSMLに変換（句読点や！、？ごとに休符を挿入）
    ssml = utils.add_breaks_for_ssml(story_text)

    with st.spinner("読み聞かせ練習中…"):
        scenes, blocks = utils.split_into_scenes(story_text, characters)   # ← characters を渡す
        block_audio_paths, durations = utils.synthesize_blocks(blocks, tts_gender=form["tts_gender"])

    # --- 挿絵生成テスト ---
    with st.spinner("絵本を生成中…"):

        #st.markdown("### 抽出されたシーン")
        #for s in scenes:
            #st.write(f"◆ {s}")

        #st.markdown("### シーン分割されたブロック")
        #for s in blocks:
            #st.write(f"◆ {s}")

        image_paths = utils.generate_illustrations(client, scenes, characters)  # ← characters を渡す

        for path in image_paths:
            if path and os.path.exists(path): 
                continue  # ← 追加チェック
            else:
                st.warning(f"画像の生成に失敗しました: {path}")


                


        # 動画作成
    #if st.button("動画を生成する 🎬"):
    with st.spinner("もうすぐできるよ！"):
    
        # BGM付き動画を生成
        video_path = utils.create_story_video(image_paths, block_audio_paths, blocks)
        final_video_path = utils.add_bgm_to_video(video_path, ct.DEFAULT_BGM_PATH)

        st.success("動画が完成しました！")
        st.video(final_video_path)

        # ダウンロードボタン
        with open(final_video_path, "rb") as f:
            st.download_button(
                label="📥 動画をダウンロード",
                data=f,
                file_name="storybook_final.mp4",
                mime="video/mp4"
            )

    # 生成完了 → GIFを消す
    placeholder.empty()


ui.footer_note()
