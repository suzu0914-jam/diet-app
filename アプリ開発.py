import json
from google import genai
from google.genai import types
import pandas as pd
import streamlit as st

st.title("🥗 ダイエット献立＆栄養チェッカー")
st.write("家にある食材と希望を選ぶと、AIがレシピを考案し、栄養バランスをグラフ化します！")

# 1. APIキーの設定（クラウドのSecretsから安全に読み込む）
api_key = st.secrets["GEMINI_API_KEY"]

# 2. ダイエットの希望・条件を選ぶ
target_cal = st.slider("1食の目標カロリー（kcal）", min_value=200, max_value=1000, value=500, step=50)
theme = st.selectbox("意識したいテーマ", ["高タンパク・低脂質（筋トレ・引き締め）", "糖質オフ（ロカボ）", "野菜たっぷり・むくみ解消", "とにかく簡単・時短ダイエット"])

# 3. 食材を選ぶ（検索付き複数選択 ＋ 自由入力）
food_list = [
    "鶏むね肉", "ささみ", "豚ロース", "牛赤身肉", "鮭", "サバ缶", "ツナ缶",
    "卵", "木綿豆腐", "絹ごし豆腐", "納豆", "無糖ヨーグルト",
    "キャベツ", "ブロッコリー", "もやし", "ほうれん草", "トマト", "玉ねぎ", "きのこ類",
    "オートミール", "玄米", "しらたき"
]
selected_foods = st.multiselect("家にある食材を選んでください（文字を打つと検索できます）", food_list)
extra_foods = st.text_input("リストにない食材があれば入力（例：キムチ、アボカド）")

# 4. 考案ボタン
if st.button("ダイエットメニューを考案する！"):
    all_foods = selected_foods.copy()
    if extra_foods != "":
        all_foods.append(extra_foods)

    if len(all_foods) == 0:
        st.warning("食材を1つ以上選んでください！")
    else:
        with st.spinner("AI栄養士がレシピと栄養素を計算中..."):
         client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

         prompt = f"""
            あなたはプロの栄養士です。以下の食材と条件でダイエットレシピを1つ考案してください。

            【使う食材】{', '.join(all_foods)}
            【目標カロリー】{target_cal}kcal以内
            【テーマ】{theme}

            必ず以下のJSON形式のみで出力してください。
            {{
                "recipe_name": "料理名",
                "steps": "材料の分量と簡単な作り方（箇条書き）",
                "calories": 合計カロリーの数値（整数）,
                "protein": タンパク質のグラム数（小数第1位まで）,
                "fat": 脂質のグラム数（小数第1位まで）,
                "carbs": 炭水化物のグラム数（小数第1位まで）,
                "fiber": 食物繊維のグラム数（小数第1位まで）
            }}
            """

        response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            data = json.loads(response.text)

            st.divider()

            # --- 結果の表示①：レシピ ---
            st.subheader(f"🍽️ 考案メニュー：{data['recipe_name']}")
            st.write(data["steps"])

            st.divider()

            # --- 結果の表示②：カロリー判定 ---
            st.subheader("📊 カロリー＆栄養バランス")
            cal = data["calories"]
            
            if cal <= target_cal:
                st.success(f"合計カロリー：**{cal} kcal** （目標 {target_cal} kcal クリア！残り {target_cal - cal} kcal の余裕があります）")
            else:
                st.warning(f"合計カロリー：**{cal} kcal** （目標を {cal - target_cal} kcal オーバーしています）")

            # --- 結果の表示③：栄養素の棒グラフ ---
            chart_data = pd.DataFrame({
                "栄養素": ["タンパク質 (g)", "脂質 (g)", "炭水化物 (g)", "食物繊維 (g)"],
                "摂取量": [data["protein"], data["fat"], data["carbs"], data["fiber"]]
            })

            st.bar_chart(chart_data, x="栄養素", y="摂取量")
