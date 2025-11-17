"""
AIアバター動画生成システム - Streamlit UI

スクリプトから音声・動画を生成してダウンロード
"""

import streamlit as st
from pathlib import Path
import sys

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.schemas import (
    VideoLength,
    CartesiaConfig,
    DIDConfig,
    CloudinaryConfig
)
from src.modules import validator, cartesia, did
from src.utils.logger import get_logger, setup_logger
from src.utils.config import load_config
from src.utils.errors import ValidationError
from src.utils.script_optimizer import optimize_for_cartesia, compare_versions

# ロガー設定
setup_logger("INFO")
logger = get_logger(__name__)

# 設定読み込み
config = load_config()


def main():
    """メインアプリケーション"""

    # ページ設定
    st.set_page_config(
        page_title="AIアバター動画生成",
        page_icon="📹",
        layout="wide"
    )

    # ヘッダー
    st.title("📹 AIアバター動画生成")
    st.markdown("---")

    # セッション状態の初期化
    initialize_session_state()

    # メイン画面
    if st.session_state.step == "input":
        render_input_screen()
    elif st.session_state.step == "generating":
        render_generating_screen()
    elif st.session_state.step == "completed":
        render_completed_screen()


def initialize_session_state():
    """セッション状態の初期化"""
    if "step" not in st.session_state:
        st.session_state.step = "input"

    if "script" not in st.session_state:
        st.session_state.script = ""

    if "voice_speed" not in st.session_state:
        st.session_state.voice_speed = 1.0

    if "audio_url" not in st.session_state:
        st.session_state.audio_url = None

    if "video_url" not in st.session_state:
        st.session_state.video_url = None


def render_input_screen():
    """入力画面"""
    st.header("📝 スクリプト入力")

    # スクリプト入力
    script = st.text_area(
        "スクリプト",
        value=st.session_state.script,
        height=300,
        placeholder="ここにスクリプトを入力してください...\n\n例:\n今日は〇〇について解説します。\nまず最初に...",
        help="動画のナレーション用スクリプトを入力してください"
    )

    # リアルタイム文字数・時間表示
    if script:
        char_count = validator.count_chars(script)
        estimated_duration = validator.estimate_duration(script)
        max_chars = validator.get_max_chars()
        max_estimated_duration = config.get("script.max_estimated_duration", 350)

        col1, col2 = st.columns(2)

        with col1:
            # 文字数表示（超過時は赤色）
            if char_count > max_chars:
                st.markdown(f"### :red[📝 文字数: {char_count} / {max_chars}]")
                st.error(f"⚠️ 推奨文字数を{char_count - max_chars}文字超過")
            else:
                st.markdown(f"### :green[📝 文字数: {char_count} / {max_chars}]")

        with col2:
            # 予想時間表示（超過時は赤色）
            minutes = estimated_duration // 60
            seconds = estimated_duration % 60

            if estimated_duration > max_estimated_duration:
                st.markdown(f"### :red[⏱️ 予想時間: {minutes}分{seconds:02d}秒]")
                st.error(f"⚠️ 推定時間を超過（最大約{max_estimated_duration}秒）")
            elif estimated_duration > 290:
                st.markdown(f"### :orange[⏱️ 予想時間: {minutes}分{seconds:02d}秒]")
                st.warning(f"⚠️ 5分に近いです（実測で確認されます）")
            else:
                st.markdown(f"### :green[⏱️ 予想時間: {minutes}分{seconds:02d}秒]")
                st.success("✅ OK")

    st.markdown("---")

    # 設定
    st.header("⚙️ 設定")

    voice_speed = st.slider(
        "声の速度",
        min_value=0.5,
        max_value=2.0,
        value=st.session_state.voice_speed,
        step=0.1,
        help="1.0が標準速度です"
    )

    st.info("💡 動画の長さはスクリプトの文字数で自動的に決まります（最大5分）")

    st.markdown("---")

    # 動画生成開始ボタン
    if st.button("▶️ 動画生成開始", type="primary", use_container_width=True):
        # バリデーション
        if not script or not script.strip():
            st.error("⚠️ スクリプトを入力してください")
            return

        validation, err = validator.validate_script(script)

        if err:
            if isinstance(err, ValidationError):
                st.error(f"⚠️ {err}")
            else:
                st.error(f"⚠️ バリデーションエラー: {err}")
            return

        # セッション状態に保存
        st.session_state.script = script
        st.session_state.voice_speed = voice_speed

        # 状態遷移
        st.session_state.step = "generating"
        st.rerun()


def render_generating_screen():
    """生成中画面"""
    st.header("⏳ 動画生成中...")

    script = st.session_state.script
    voice_speed = st.session_state.voice_speed

    # APIキー取得
    try:
        cartesia_api_key = st.secrets["cartesia"]["api_key"]
        cartesia_voice_id = st.secrets["cartesia"]["voice_id"]
        did_api_key = st.secrets["did"]["api_key"]
        cloudinary_cloud = st.secrets["cloudinary"]["cloud_name"]
        cloudinary_key = st.secrets["cloudinary"]["api_key"]
        cloudinary_secret = st.secrets["cloudinary"]["api_secret"]
    except KeyError as e:
        st.error(f"""
        ### ⚠️ 設定エラー

        APIキーが設定されていません: {e}

        `.streamlit/secrets.toml` を確認してください。
        """)
        return

    # プログレス表示
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # ステップ1: 音声生成
        status_text.text("🎙️ 音声生成中...")
        progress_bar.progress(10)

        cloudinary_config = CloudinaryConfig(
            cloud_name=cloudinary_cloud,
            api_key=cloudinary_key,
            api_secret=cloudinary_secret
        )

        audio, err = cartesia.generate_audio_sync(
            text=script,
            api_key=cartesia_api_key,
            voice_id=cartesia_voice_id,
            cloudinary_config=cloudinary_config,
            speed=voice_speed
        )

        if err:
            st.error(f"""
            ### ⚠️ 音声生成エラー

            **エラー**: {err}

            **対処方法**:
            1. APIキーを確認してください
            2. ネットワーク接続を確認してください
            3. しばらく待ってから再試行してください
            """)
            return

        st.session_state.audio_url = str(audio.audio_url)
        progress_bar.progress(50)

        st.success("✅ 音声生成完了")

        # 音声プレビュー
        st.audio(str(audio.audio_url))

        # 音声時間チェック（D-ID制限）
        max_duration = config.get("script.max_duration_seconds", 290)
        actual_duration = audio.duration_seconds

        st.info(f"📊 音声時間: {actual_duration:.1f}秒 / 最大{max_duration}秒")

        if actual_duration > max_duration:
            st.error(f"""
            ### ⚠️ 音声が長すぎます

            **音声時間**: {actual_duration:.1f}秒
            **制限**: {max_duration}秒（D-ID API制限）
            **超過**: {actual_duration - max_duration:.1f}秒

            **対処方法**:
            スクリプトを2つに分けて、それぞれ別の動画として生成してください。

            例:
            - 前半: {len(script)//2}文字
            - 後半: {len(script)//2}文字
            """)
            return

        # ステップ2: 動画生成
        status_text.text("🎬 動画生成中（3-5分かかります）...")
        progress_bar.progress(60)

        # アバター画像URL（仮）
        # TODO: ユーザーがアップロードできるようにする
        # Note: DefaultPresentersのURLは500エラーを返すため、D-IDのパブリックサンプルを使用
        avatar_url = "https://d-id-public-bucket.s3.amazonaws.com/alice.jpg"

        did_client = did.DIDClient(api_key=did_api_key)

        video, err = did_client.generate(
            audio_url=str(audio.audio_url),
            avatar_url=avatar_url
        )

        if err:
            st.error(f"""
            ### ⚠️ 動画生成エラー

            **エラー**: {err}

            **対処方法**:
            1. 音声URLが正しいか確認してください
            2. D-ID APIキーを確認してください
            3. しばらく待ってから再試行してください
            """)
            return

        st.session_state.video_url = str(video.video_url)
        progress_bar.progress(100)

        st.success("✅ 動画生成完了！")

        # 完了画面へ遷移
        status_text.text("")
        st.session_state.step = "completed"
        st.rerun()

    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)
        st.error(f"""
        ### 🚨 システムエラー

        予期しないエラーが発生しました。

        **エラー**: {e}

        管理者に連絡してください。
        """)


def render_completed_screen():
    """完了画面"""
    st.balloons()

    st.success("🎉 動画生成が完了しました！")

    st.markdown("---")

    # プレビュー
    st.header("👁️ プレビュー")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎙️ 音声")
        if st.session_state.audio_url:
            st.audio(st.session_state.audio_url)

    with col2:
        st.subheader("🎬 動画")
        if st.session_state.video_url:
            st.video(st.session_state.video_url)

    st.markdown("---")

    # アクション
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 動画をダウンロード", use_container_width=True):
            st.info("""
            💡 動画をダウンロードするには:

            1. 上の動画プレビューを右クリック
            2. 「名前を付けて動画を保存」を選択
            3. 保存先を選んで保存

            または、下のリンクを開いてダウンロードしてください。
            """)
            st.markdown(f"[動画リンク]({st.session_state.video_url})")

    with col2:
        if st.button("🔄 新しい動画を作成", use_container_width=True):
            # 状態リセット
            for key in ["script", "audio_url", "video_url"]:
                if key in st.session_state:
                    st.session_state[key] = ""

            st.session_state.step = "input"
            st.rerun()

    st.markdown("---")

    # YouTube投稿ガイド
    with st.expander("📺 YouTubeへの投稿方法"):
        st.markdown("""
        ### YouTube投稿手順

        1. **動画をダウンロード**
           - 上のボタンから動画をダウンロード

        2. **YouTube Studioにアクセス**
           - https://studio.youtube.com/

        3. **動画をアップロード**
           - 「作成」→「動画をアップロード」
           - ダウンロードした動画を選択

        4. **詳細を入力**
           - タイトル、説明文、サムネイルなど

        5. **公開設定**
           - 「公開」または「限定公開」を選択

        6. **公開**
           - 「公開」ボタンをクリック

        完了！
        """)


if __name__ == "__main__":
    main()
