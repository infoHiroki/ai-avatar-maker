"""
スクリプト最適化ユーティリティ

Cartesiaの早口問題に対処するため、スクリプトを自動調整
"""

import re
from typing import Tuple


def optimize_for_cartesia(script: str, mode: str = "moderate") -> str:
    """
    Cartesia用にスクリプトを最適化

    Args:
        script: 元のスクリプト
        mode: 調整モード
            - "light": 軽い調整（句読点を少し追加）
            - "moderate": 中程度の調整（推奨）
            - "heavy": 強い調整（句読点多め + 改行）

    Returns:
        最適化されたスクリプト
    """

    if mode == "light":
        return _optimize_light(script)
    elif mode == "moderate":
        return _optimize_moderate(script)
    elif mode == "heavy":
        return _optimize_heavy(script)
    else:
        raise ValueError(f"Invalid mode: {mode}")


def _optimize_light(script: str) -> str:
    """軽い調整: 句読点を少し追加"""

    # 接続詞の後に読点を追加
    conjunctions = ["そして", "また", "しかし", "ただし", "なお", "ちなみに"]
    for conj in conjunctions:
        # 既に読点がある場合はスキップ
        script = re.sub(f"({conj})([^、])", r"\1、\2", script)

    return script


def _optimize_moderate(script: str) -> str:
    """中程度の調整（推奨）"""

    # まず軽い調整を適用
    script = _optimize_light(script)

    # 長い文を分割（40文字以上の文に読点を追加）
    lines = script.split('\n')
    optimized_lines = []

    for line in lines:
        if not line.strip():
            optimized_lines.append(line)
            continue

        # 文を「。」で分割
        sentences = line.split('。')
        optimized_sentences = []

        for sentence in sentences:
            if not sentence.strip():
                continue

            # 40文字以上の文に読点を追加
            if len(sentence) > 40:
                sentence = _add_commas_to_long_sentence(sentence)

            optimized_sentences.append(sentence)

        optimized_line = '。'.join(optimized_sentences)
        if optimized_line and not optimized_line.endswith('。'):
            optimized_line += '。'

        optimized_lines.append(optimized_line)

    return '\n'.join(optimized_lines)


def _optimize_heavy(script: str) -> str:
    """強い調整: 句読点多め + 改行"""

    # まず中程度の調整を適用
    script = _optimize_moderate(script)

    # 文ごとに改行を追加
    script = script.replace('。', '。\n\n')

    # 最後の空白行を削除
    script = script.rstrip('\n')

    return script


def _add_commas_to_long_sentence(sentence: str) -> str:
    """長い文に読点を追加"""

    # 接続助詞の後に読点を追加
    patterns = [
        (r"([がですけれども])([^、])", r"\1、\2"),
        (r"(という)([^、])", r"\1、\2"),
        (r"(ため)([^、])", r"\1、\2"),
    ]

    for pattern, replacement in patterns:
        sentence = re.sub(pattern, replacement, sentence)

    return sentence


def compare_versions(original: str) -> Tuple[str, str, str]:
    """
    3つのバージョンを生成して比較

    Returns:
        (light版, moderate版, heavy版)
    """

    light = optimize_for_cartesia(original, "light")
    moderate = optimize_for_cartesia(original, "moderate")
    heavy = optimize_for_cartesia(original, "heavy")

    return light, moderate, heavy


def estimate_speed_improvement(original: str, optimized: str) -> float:
    """
    最適化による速度改善の推定値

    Returns:
        改善率（0.0-1.0）
    """

    # 句読点の数をカウント
    original_commas = original.count('、') + original.count('。')
    optimized_commas = optimized.count('、') + optimized.count('。')

    # 改行の数をカウント
    original_lines = original.count('\n\n')
    optimized_lines = optimized.count('\n\n')

    # 句読点1つあたり約0.3秒、改行1つあたり約0.5秒の間が入る（推定）
    original_pauses = original_commas * 0.3 + original_lines * 0.5
    optimized_pauses = optimized_commas * 0.3 + optimized_lines * 0.5

    # 改善率（間の増加率）
    if original_pauses == 0:
        return 0.0

    improvement = (optimized_pauses - original_pauses) / original_pauses

    return min(improvement, 1.0)  # 最大100%改善


# テスト用
if __name__ == "__main__":

    sample_script = """
今日はAIアバターの活用方法についてお話しします。AIアバターは人工知能を使って作成された仮想的なキャラクターで動画制作の効率が大幅に向上します。これにより従来は数時間かかっていた作業がわずか数分で完了するようになりました。
"""

    print("=" * 60)
    print("元のスクリプト:")
    print("=" * 60)
    print(sample_script)
    print()

    light, moderate, heavy = compare_versions(sample_script)

    print("=" * 60)
    print("Light版:")
    print("=" * 60)
    print(light)
    print()

    print("=" * 60)
    print("Moderate版（推奨）:")
    print("=" * 60)
    print(moderate)
    print()

    print("=" * 60)
    print("Heavy版:")
    print("=" * 60)
    print(heavy)
    print()

    # 改善率を表示
    for version_name, version_script in [("Light", light), ("Moderate", moderate), ("Heavy", heavy)]:
        improvement = estimate_speed_improvement(sample_script, version_script)
        print(f"{version_name}版の改善率: {improvement*100:.1f}%")
