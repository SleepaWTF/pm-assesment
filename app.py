import streamlit as st
import openai
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_SHEETS_ID = os.environ.get("GOOGLE_SHEETS_ID", "")

def save_to_sheets(data):
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEETS_ID).sheet1
        sheet.append_row(data)
    except Exception as e:
        st.warning(f"Не удалось сохранить в таблицу: {e}")

COMPETENCIES = [
    {
        "id": "discovery",
        "name": "Discovery / Product thinking",
        "weight": 0.20,
        "question": "Опиши, как ты ведёшь discovery на своём направлении. Приведи конкретный пример: с чего начал, какие методы использовал, как связал с бизнес-целями.",
        "case_question": "Опиши конкретный кейс из практики: когда это было, какая была задача, что именно ты сделал и каков результат?",
        "levels": {
            "J1": "Знает базовые фреймворки (JTBD, CustDev, Lean Canvas) на уровне определений. Помогает готовить материалы для интервью под руководством.",
            "J2": "Проводит 5+ интервью по готовому гайду. Формулирует гипотезы в формате если-то-потому что.",
            "J3": "Сам составляет гайд интервью под задачу. Проводит discovery по типовой проблеме end-to-end.",
            "M1": "Полный discovery-цикл фичи: research - инсайт - гипотеза - MVP. Использует 2+ метода исследования.",
            "M2": "Ведёт discovery в условиях неопределённости. Формирует discovery-план для нового направления. Чётко связывает с OKR.",
            "M3": "Ведёт discovery нового направления / вертикали. Менторит junior/middle PM. Внедряет инструменты в команду.",
            "S1": "Discovery на уровне стратегии компании, видение на 1-2 года. Связывает с финансовыми моделями и P&L.",
            "S2": "Формирует discovery-подход для всей продуктовой функции. Создаёт собственные фреймворки. Thought leadership.",
        }
    },
    {
        "id": "data_analytics",
        "name": "Data & Analytics",
        "weight": 0.18,
        "question": "Опиши, как ты используешь данные при принятии продуктовых решений. Приведи пример: как ставил гипотезу, какие данные анализировал, к каким выводам пришёл.",
        "case_question": "Опиши конкретный кейс: какую задачу решал, какие данные использовал, что это дало?",
        "levels": {
            "J1": "Понимает базовые метрики (CR, retention, ARPPU). Использует готовые дашборды. SQL по шаблону.",
            "J2": "Базовый SQL: JOIN, GROUP BY. Строит простые когортные/funnel-отчёты.",
            "J3": "Самостоятельный анализ воронки в BigQuery. Базовая статистика: p-value, размер выборки.",
            "M1": "Полный цикл анализа эксперимента. Уверенный SQL. Делает рекомендации на основе данных.",
            "M2": "Применяет продвинутые методы (CUPED, DiD). Замечает методологические ошибки. Влияет на BI-архитектуру.",
            "M3": "Внедряет стандарты аналитики в команде. Связывает метрики с финансовыми (LTV, CAC, EBITDA).",
            "S1": "Связывает аналитику со стратегией. Формирует культуру data-driven решений. Решения на основе unit-экономики.",
            "S2": "Формирует архитектуру аналитики на уровне компании. Создаёт собственные методологии измерения.",
        }
    },
    {
        "id": "customer_understanding",
        "name": "Customer understanding",
        "weight": 0.12,
        "question": "Как ты понимаешь своего пользователя? Опиши методы, которые применяешь, как сегментируешь аудиторию и как это влияет на продуктовые решения.",
        "case_question": "Приведи конкретный пример: когда понимание пользователя помогло принять важное продуктовое решение?",
        "levels": {
            "J1": "Знает 1-2 ключевых сегмента продукта. Читает фидбэк, группирует под руководством.",
            "J2": "Проводит интервью самостоятельно. Базовые персоны и JTBD по 1-2 сегментам.",
            "J3": "Описывает customer journey по фиче. Связывает фидбэк с приоритетами продукта.",
            "M1": "Поддерживает живые персоны / JTBD. Запускает регулярный feedback loop. Использует 3+ источника инсайтов.",
            "M2": "Глубокое сегментирование (поведение х экономика х контекст). Понимает мотивации B2B и B2C.",
            "M3": "Системно собирает customer insights. Внедряет ритуалы customer-centric работы. Менторит команду.",
            "S1": "Формирует customer strategy на уровне компании. Решения о сегменте на основе LTV/CAC.",
            "S2": "Задаёт стандарты для всей компании. Создаёт собственные сегментационные модели.",
        }
    },
    {
        "id": "prioritization",
        "name": "Prioritization",
        "weight": 0.12,
        "question": "Как ты расставляешь приоритеты в бэклоге? Опиши конкретную ситуацию, когда нужно было выбрать между несколькими задачами при ограниченных ресурсах.",
        "case_question": "Опиши конкретный кейс: какие задачи конкурировали, как ты принял решение и что в итоге получилось?",
        "levels": {
            "J1": "Знает RICE, MoSCoW, value/effort на уровне определений. Не принимает решений самостоятельно.",
            "J2": "Применяет 1-2 метода приоритизации. Защищает выбор приоритета на конкретной задаче.",
            "J3": "Приоритизирует бэклог фичи. Понимает trade-offs scope/time/quality.",
            "M1": "Поддерживает приоритизированный бэклог направления. Балансирует new value / tech debt / KTLO.",
            "M2": "Приоритизирует при конфликтующих стейкхолдерах. Применяет 3+ метода. Фиксирует trade-offs.",
            "M3": "Приоритизация на уровне нескольких команд. Внедряет фреймворки. Связывает с OKR.",
            "S1": "Приоритизация на уровне компании. Балансирует short-term cash и long-term value.",
            "S2": "Формирует методологию приоритизации. Влияет на распределение ресурсов в годовом цикле.",
        }
    },
    {
        "id": "delivery",
        "name": "Delivery / Execution",
        "weight": 0.10,
        "question": "Опиши, как ты ведёшь фичу или инициативу от идеи до релиза. Как управляешь зависимостями, блокерами и качеством delivery?",
        "case_question": "Приведи конкретный пример инициативы: что это было, какие были сложности и как ты их решил?",
        "levels": {
            "J1": "Знает ритуалы Scrum/Kanban. Помогает готовить материалы спринта. Не ведёт релизы самостоятельно.",
            "J2": "Ведёт задачи через цикл разработки. Пишет user stories с acceptance criteria.",
            "J3": "Ведёт фичу через весь цикл delivery без надзора. Замечает блокеры вовремя.",
            "M1": "Доставляет фичи в срок (~80% sprint goal hit rate). Управляет зависимостями между командами.",
            "M2": "Доставляет сложные проекты с зависимостями между 3+ командами. Управляет рисками delivery.",
            "M3": "Ведёт несколько параллельных инициатив. Внедряет delivery-практики (DoD, DoR, retro).",
            "S1": "Ведёт стратегические инициативы с фиксированным дедлайном. Управляет программой проектов.",
            "S2": "Формирует delivery-подходы для всей компании. Связывает метрики с бизнес-результатом.",
        }
    },
    {
        "id": "stakeholder_management",
        "name": "Stakeholder management",
        "weight": 0.10,
        "question": "Как ты работаешь со стейкхолдерами? Приведи пример, когда нужно было получить buy-in или разрешить конфликт приоритетов.",
        "case_question": "Опиши конкретную ситуацию со стейкхолдером: кто был вовлечён, в чём была сложность и как ты её разрешил?",
        "levels": {
            "J1": "Знает основных стейкхолдеров. Готовит материалы под контролем. Не ведёт переговоры самостоятельно.",
            "J2": "Ведёт типовые встречи. Эскалирует проблемы вовремя.",
            "J3": "Управляет ожиданиями на уровне фичи. Различает громких и важных стейкхолдеров.",
            "M1": "Поддерживает регулярный коммуникационный ритм. Получает buy-in на средние инициативы.",
            "M2": "Управляет ожиданиями C-level на уровне направления. Влияет через данные и аргументацию.",
            "M3": "Управляет стейкхолдерами в кросс-функциональных проектах. Выявляет политические риски.",
            "S1": "Управляет founder-ами и инвесторами. Влияет на стратегические решения через альянсы.",
            "S2": "Формирует stakeholder-стратегию на уровне компании. Менторит сениоров.",
        }
    },
    {
        "id": "technical_understanding",
        "name": "Technical understanding",
        "weight": 0.08,
        "question": "Насколько глубоко ты понимаешь техническую сторону продукта? Как взаимодействуешь с инженерами? Приведи пример, где техническое понимание помогло принять лучшее решение.",
        "case_question": "Приведи конкретный пример: какое техническое решение обсуждалось, как ты участвовал и что это дало продукту?",
        "levels": {
            "J1": "Знает общие термины (API, БД, фронт/бэк). Спрашивает разработчиков для уточнения.",
            "J2": "Понимает базовую архитектуру (клиент-сервер, БД, очереди). Корректно описывает технические требования.",
            "J3": "Понимает архитектуру продукта на уровне компонентов. Учитывает технический долг при планировании.",
            "M1": "Свободно обсуждает технические решения с инженерами. Понимает trade-offs (cost vs speed vs flex).",
            "M2": "Участвует в архитектурных решениях направления. Понимает performance, scalability, reliability.",
            "M3": "Влияет на технические решения через продуктовые требования. Связывает tech debt с бизнес-результатом.",
            "S1": "Участвует в стратегических технических решениях. Принимает build/buy/partner решения.",
            "S2": "Формирует технологическую стратегию совместно с CTO. Понимает emerging tech и его применение.",
        }
    },
    {
        "id": "communication",
        "name": "Communication",
        "weight": 0.10,
        "question": "Как ты доносишь продуктовые решения до разных аудиторий (команда, C-level, стейкхолдеры)? Приведи пример сложной коммуникации.",
        "case_question": "Опиши конкретный случай сложной коммуникации: кому, что и как доносил, и каков был результат?",
        "levels": {
            "J1": "Пишет понятные сообщения. Готовит простые презентации по шаблону.",
            "J2": "Пишет структурированные PRD и one-pagers. Готовит и проводит демо на review.",
            "J3": "Пишет PRD, способный пройти review без правок старшим. Использует данные для усиления аргументов.",
            "M1": "Презентует решения founder-ам и C-level. Адаптирует стиль под аудиторию.",
            "M2": "Ведёт сложные презентации в условиях критики. Влияет на решения через storytelling и данные.",
            "M3": "Менторит команду в communication-практиках. Формирует tone of voice продуктовой команды.",
            "S1": "Ведёт стратегические коммуникации (board, инвесторы, all-hands). Управляет нарративом продукта.",
            "S2": "Внешний публичный голос компании. Влияет на индустрию через доклады, статьи, подкасты.",
        }
    },
]

st.set_page_config(page_title="PM Assessment", page_icon="🎯", layout="centered")

if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "cases" not in st.session_state:
    st.session_state.cases = {}
if "result" not in st.session_state:
    st.session_state.result = None
if "name" not in st.session_state:
    st.session_state.name = ""
if "email" not in st.session_state:
    st.session_state.email = ""

total_steps = len(COMPETENCIES)

if st.session_state.step == 0:
    st.title("🎯 PM Grade Assessment")
    st.subheader("Оценка квалификации Product Manager")
    st.markdown("---")
    st.markdown("""
    **Как это работает:**
    - 8 вопросов по ключевым компетенциям PM
    - Отвечай развёрнуто, с конкретными примерами из практики
    - В конце получишь грейд и детальный разбор по каждой компетенции

    **Время:** ~20-30 минут
    """)
    st.markdown("---")

    name = st.text_input("Твоё имя", placeholder="Например: Дмитрий")
    email = st.text_input("Рабочая почта", placeholder="example@company.com")

    if st.button("🚀 Начать оценку", use_container_width=True):
        if not name.strip():
            st.error("Введи своё имя")
        elif not email.strip() or "@" not in email:
            st.error("Введи корректную рабочую почту")
        else:
            st.session_state.name = name.strip()
            st.session_state.email = email.strip()
            st.session_state.step = 1
            st.rerun()

elif 1 <= st.session_state.step <= total_steps:
    comp = COMPETENCIES[st.session_state.step - 1]

    st.progress(st.session_state.step / total_steps)
    st.caption(f"Вопрос {st.session_state.step} из {total_steps}")
    st.markdown(f"## {comp['name']}")
    st.markdown(f"*Вес в итоговой оценке: {int(comp['weight']*100)}%*")
    st.markdown("---")

    st.markdown(f"**{comp['question']}**")
    answer = st.text_area(
        label="Твой ответ",
        height=200,
        placeholder="Пиши развёрнуто, с конкретными примерами из практики...",
        key=f"answer_{comp['id']}",
        value=st.session_state.answers.get(comp['id'], "")
    )

    st.markdown("---")
    st.markdown(f"**{comp['case_question']}**")
    st.caption("Этот ответ не влияет на оценку — он нужен для контекста.")
    case = st.text_area(
        label="Конкретный кейс",
        height=150,
        placeholder="Когда это было, какая была задача, что сделал, каков результат...",
        key=f"case_{comp['id']}",
        value=st.session_state.cases.get(comp['id'], "")
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.session_state.step > 1:
            if st.button("← Назад", use_container_width=True):
                st.session_state.answers[comp['id']] = answer
                st.session_state.cases[comp['id']] = case
                st.session_state.step -= 1
                st.rerun()
    with col2:
        btn_label = "Далее →" if st.session_state.step < total_steps else "Получить результат 🎯"
        if st.button(btn_label, use_container_width=True):
            if not answer or len(answer.strip()) < 200:
                st.warning("Напиши более развёрнутый ответ — минимум 200 символов")
            else:
                st.session_state.answers[comp['id']] = answer
                st.session_state.cases[comp['id']] = case
                st.session_state.step += 1
                st.rerun()

elif st.session_state.step == total_steps + 1:

    if st.session_state.result is None:
        with st.spinner("Анализирую ответы... это займёт ~30 секунд"):

            matrix_text = ""
            for comp in COMPETENCIES:
                matrix_text += f"\n\n### {comp['name']} (вес: {int(comp['weight']*100)}%)\n"
                for level, desc in comp["levels"].items():
                    matrix_text += f"- {level}: {desc}\n"

            answers_text = ""
            for comp in COMPETENCIES:
                answer = st.session_state.answers.get(comp['id'], "")
                answers_text += f"\n\n### {comp['name']}\n{answer}"

            name = st.session_state.name
            email = st.session_state.email

            prompt = (
                "Ты — опытный ментор и эксперт по оценке квалификации Product Manager.\n\n"
                f"Кандидат: {name} ({email})\n\n"
                "Матрица компетенций:\n" + matrix_text +
                "\n\nОтветы кандидата:\n" + answers_text +
                "\n\nВерни результат СТРОГО в формате JSON без markdown:\n\n"
                "{\n"
                f'  "name": "{name}",\n'
                '  "overall_grade": "M2",\n'
                f'  "overall_summary": "Персональное резюме для {name} - 3-4 предложения с обращением по имени",\n'
                '  "competencies": [\n'
                '    {\n'
                '      "name": "название компетенции",\n'
                '      "grade": "M2",\n'
                '      "score_explanation": "2-3 наблюдения из ответа",\n'
                '      "strengths": "конкретные сильные стороны",\n'
                '      "growth_zone": "конкретный план роста до следующего грейда"\n'
                '    }\n'
                '  ],\n'
                f'  "development_plan": "Персональный план для {name} на 3-6 месяцев: 3 приоритета, конкретные действия, целевой грейд",\n'
                '  "ai_suspicion_score": 5,\n'
                '  "ai_suspicion_comment": "Оценка от 1 до 10: насколько текст похож на сгенерированный ИИ. 1 - явно человек, 10 - явно ИИ. Укажи признаки."\n'
                "}\n\n"
                "Важно:\n"
                f"- Обращайся по имени ({name})\n"
                "- Оценивай строго по матрице, не завышай\n"
                "- ai_suspicion_score и ai_suspicion_comment — только для руководителя, не упоминай их в summary\n"
                "- Только валидный JSON"
            )

            try:
                client = openai.OpenAI(api_key=OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                raw = response.choices[0].message.content
                clean = raw.replace("```json", "").replace("```", "").strip()
                result = json.loads(clean)
                st.session_state.result = result

                # Сохраняем в Google Sheets
                cases_text = ""
                for comp in COMPETENCIES:
                    case = st.session_state.cases.get(comp['id'], "")
                    cases_text += f"{comp['name']}: {case}\n\n"

                row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    name,
                    email,
                    result.get("overall_grade", ""),
                    result.get("overall_summary", ""),
                    result.get("development_plan", ""),
                    cases_text,
                    result.get("ai_suspicion_score", ""),
                    result.get("ai_suspicion_comment", ""),
                ]
                save_to_sheets(row)

            except json.JSONDecodeError:
                st.error("GPT вернул неожиданный формат. Попробуй ещё раз.")
                if st.button("🔄 Попробовать снова"):
                    st.session_state.result = None
                    st.rerun()
                st.stop()
            except Exception as e:
                st.error(f"Ошибка: {e}")
                st.stop()

    result = st.session_state.result
    st.title("🎯 Результаты оценки")
    st.markdown(f"### {result.get('name', '')} - грейд: **{result.get('overall_grade', '')}**")
    st.markdown("---")

    st.markdown("#### 💬 Общее резюме")
    st.info(result.get("overall_summary", ""))

    st.markdown("---")
    st.subheader("📊 По компетенциям")

    for comp_result in result.get("competencies", []):
        with st.expander(f"{comp_result['name']} - {comp_result['grade']}", expanded=False):
            st.markdown(f"**📌 Обоснование грейда:**\n\n{comp_result['score_explanation']}")
            st.markdown(f"**✅ Сильные стороны:**\n\n{comp_result['strengths']}")
            st.markdown(f"**🚀 Зона роста:**\n\n{comp_result['growth_zone']}")

    st.markdown("---")
    st.subheader("📅 Персональный план развития")
    st.success(result.get("development_plan", ""))

    st.markdown("---")
    if st.button("🔄 Пройти заново", use_container_width=True):
        st.session_state.step = 0
        st.session_state.answers = {}
        st.session_state.cases = {}
        st.session_state.result = None
        st.session_state.name = ""
        st.session_state.email = ""
        st.rerun()
