# components.py
import streamlit as st
import constants as ct

def header():
    st.image("assets/header.png", use_container_width=700) # ヘッダー画像
    #st.markdown(f"## {ct.APP_NAME}")
    st.caption("主人公や登場人物を設定して、世界にひとつだけのおはなしをつくろう 📖")

def input_form():
    
    st.markdown("### 主人公を決めよう")
    # 主人公選択
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        choice = st.radio(
            "", 
            ["叶都", "由都", "その他"], 
            index=0, 
            key="main_character_choice"
        )

    with c2:
        custom_name = None
        if choice == "その他":
            custom_name = st.text_input("名前をつけてね", placeholder="例：ゆうた", key="main_character_custom")

    with c3:
        if choice == "その他":
            main_gender = st.radio("性別", ["男の子", "女の子"], index=0, key="main_gender_custom")
        else:
            main_gender = ct.CHARACTER_PRESETS.get(choice, {}).get("gender", "未指定")

    # ---- 主人公の辞書化 ----
    if choice in ct.CHARACTER_PRESETS:
        main_character = choice
        main_info = ct.CHARACTER_PRESETS[choice]
    else:
        main_character = custom_name or ""
        main_info = {"gender": main_gender}

    # ---- 特殊ケース: 叶都 ↔ 由都 のペア処理 ----
    extra_characters, extra_infos = [], []
    if choice == "叶都":
        if st.toggle("由都も登場させる", value=False, key="toggle_yuito"):
            extra_characters.append("由都")
            extra_infos.append(ct.CHARACTER_PRESETS["由都"])
    elif choice == "由都":
        if st.toggle("叶都も登場させる", value=False, key="toggle_kanato"):
            extra_characters.append("叶都")
            extra_infos.append(ct.CHARACTER_PRESETS["叶都"])

    # ---- その他の登場人物 ----
    st.markdown("### 他の登場人物")
    sub_characters, sub_infos = [], []
    for i in range(3):
        c1, c2 = st.columns([2, 1])
        with c1:
            name = st.text_input(f"登場人物 {i+1}", key=f"sub_character_{i}")
        with c2:
            gender = st.radio(
                "性別", ["男の子", "未指定", "女の子"],
                index=0,
                key=f"sub_gender_{i}",
                horizontal=True
            )
        if name.strip():
            sub_characters.append(name)
            sub_infos.append({"gender": gender})

    # ---- お話設定 ----
    style = st.selectbox("おはなしのスタイル", ct.STORY_STYLES, index=0, key="style")
    theme = st.text_input("おはなしのテーマ", placeholder="例：恐竜の世界、宝探し、友達と仲直り", key="theme")

    # ---- 音声設定 ----
    st.subheader("誰に読んでもらう？")
    tts_gender = st.radio(
        "声の種類（TTS）", ["女のひと", "男のひと"],
        index=0,
        key="tts_gender",
        horizontal=True
    )

    generate = st.button("おはなしをつくる 📖", type="primary", use_container_width=True)

    # ---- まとめて返す ----
    return {
        "main_character": main_character,
        "main_info": main_info,
        "sub_characters": sub_characters + extra_characters,
        "sub_infos": sub_infos + extra_infos,
        "style": style,
        "theme": theme,
        "tts_gender": tts_gender,
        "generate": generate,
    }





def show_audio(path, label="再生してみる"):
    st.audio(path)
    st.download_button("音声をダウンロード", data=open(path, "rb"), file_name=path, mime="audio/mpeg")
    st.success(f"{label}：{path}")

def show_error(msg):
    st.error(msg, icon="❗")

def footer_note():
    st.markdown("---")
    st.caption("Powered by Streamlit + GPT + Google Cloud TTS")
