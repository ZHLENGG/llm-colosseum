import streamlit as st
import requests
import time

st.set_page_config(page_title="LLM Colosseum", page_icon="⚔️", layout="wide")
API_URL = "http://127.0.0.1:8000"

st.title("⚔️ LLM Colosseum")
st.markdown("Добро пожаловать на арену! Здесь нейросети сражаются в интеллектуальных дебатах.")

with st.sidebar:
    st.header("Настройки битвы")
    question = st.text_area("Введите ваш вопрос:", "Стоит ли учить Rust в 2024 году?")
    
    if st.button("🚀 Начать битву!", use_container_width=True):
        with st.spinner("Отправляем запрос на арену..."):
            response = requests.post(f"{API_URL}/battles/", json={"question": question, "models": ["phi3", "mistral"]})
            if response.status_code == 201:
                st.session_state['battle_id'] = response.json()['id']
            else:
                st.error("Ошибка при создании баттла")

if 'battle_id' in st.session_state:
    battle_id = st.session_state['battle_id']
    placeholder = st.empty()
    
    while True:
        res = requests.get(f"{API_URL}/battles/{battle_id}")
        if res.status_code != 200:
            st.error("Баттл не найден")
            break
            
        battle = res.json()
        status = battle['status']
        
        with placeholder.container():
            st.subheader(f"Вопрос: {battle['question']}")
            
            # --- Красивый статус-бар ---
            if status == "pending":
                st.info("⏳ В очереди на арену...")
            elif "round_1" in status:
                st.warning("🧠 Раунд 1: Модели генерируют ответы...")
            elif "round_2" in status:
                st.warning("🥊 Раунд 2: Модели критикуют друг друга...")
            elif "judge" in status:
                st.warning("⚖️ Финал: Судья выносит вердикт...")
            elif status == "completed":
                st.success("🏆 Битва завершена!")

            st.divider()

            # --- ОТВЕТЫ (Раунд 1) ---
            if battle['participants']:
                cols = st.columns(len(battle['participants']))
                for idx, participant in enumerate(battle['participants']):
                    with cols[idx]:
                        st.markdown(f"### 🤖 {participant['display_name']}")
                        st.markdown(f"**Баллы:** {participant.get('total_score', 0) or 0}")
                        
                        round1_resp = next((r for r in participant['responses'] if r['round'] == 1), None)
                        if round1_resp:
                            st.success(round1_resp['content'])
                        else:
                            # Вот наша визуализация "раздумий"
                            with st.spinner("🔄 Генерирует ответ..."):
                                time.sleep(0.1) # Просто чтобы спиннер отрисовался

            # --- КРИТИКА (Раунд 2) ---
            if battle.get('critiques'):
                st.divider()
                st.subheader("🥊 Перекрестная критика")
                for c in battle['critiques']:
                    author = next((p['display_name'] for p in battle['participants'] if p['id'] == c['author_participant_id']), "Unknown")
                    target_author = "Unknown"
                    for p in battle['participants']:
                        for r in p['responses']:
                            if r['id'] == c['target_response_id']:
                                target_author = p['display_name']
                    
                    # Красивый прогресс-бар для оценки
                    score_color = "green" if c['score'] >= 7 else "orange" if c['score'] >= 4 else "red"
                    with st.expander(f"{author} ➡️ {target_author} (Оценка: {c['score']}/10)"):
                        st.progress(c['score'] / 10.0, text=f"Оценка: {c['score']}/10")
                        st.write(c['content'])

            # --- ВЕРДИКТ ---
            if status == "completed":
                st.divider()
                st.subheader("⚖️ Вердикт Судьи")
                
                winner_name = "Не определен"
                if battle.get('winner_participant_id'):
                    winner = next((p for p in battle['participants'] if p['id'] == battle['winner_participant_id']), None)
                    if winner:
                        winner_name = winner['display_name']
                
                st.success(f"🏆 Победитель: **{winner_name}**")
                st.info(battle.get('judge_summary') or 'Судья еще пишет вердикт...')
                st.balloons()
                break
                
        time.sleep(2)
        st.rerun()