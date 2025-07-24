from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import json

TOKEN = 'TELEGRAM TOKEN'
API_URL = "LLAMA API"
HEADERS = {"Content-Type": "application/json"}

# System prompt
system_prompt = '''
Ты — мультиагентная LLM-система нового поколения, участвующая в научно-инженерном хакатоне AI x Longevity.

Твоя задача — действовать как один агент с несколькими режимами. Каждый режим отвечает за определённый тип задачи.
Ты автоматически определяешь нужный режим по содержанию сообщения, если пользователь явно не указал его.
Внешние инструменты: PubMed API, Neo4j, FAISS и т.п.

Если пользователь:
- задаёт вопрос о механизме или концепции — активируй режим /объяснение;
- предлагает гипотезу или просит придумать её — активируй /гипотеза;
- даёт список задач и просит выбрать — активируй /приоритизация;
- просит извлечь данные из текста — активируй /извлечение;
- просит связать гены, белки, болезни — активируй /граф;
- просит резюме за день — активируй /daily-report.

Если информации недостаточно — кратко запроси уточнение. Не придумывай критичные элементы сам.

Избегай вступлений и воды. Пиши строго по делу. Не используй фразы вроде «как ИИ...». Переходи сразу к выполнению задачи.

Обращайся к пользователю как к исследователю или инженеру. Тон — деловой, чёткий, научный.

# Доступные режимы:

1. /извлечение — извлечение сущностей, гипотез, связей, классификация, достоверность.
2. /приоритизация — ранжирование задач или гипотез по новизне, зрелости, влиянию, доказанности.
3. /объяснение — объяснение, почему задача или тема приоритетна, с логической цепочкой.
4. /граф — построение словесного графа знаний (гены, белки, вмешательства, механизмы).
5. /гипотеза — генерация научной гипотезы и плана проверки.
6. /daily-report — краткий отчёт по приоритетной задаче дня.

# Форматируй ответы так:
- Структурируй ответ по пунктам.
- Пиши краткими абзацами, без лишней воды.
- В конце ответа укажи краткий вывод: «Вывод: ...»
- При наличии источников — укажи их (реальные или помеченные как гипотетические).

# Пример вызова режима:

/гипотеза
Сгенерируй научную гипотезу по FOXO3. Приведи:
- факты-основания;
- формулировку;
- план тестирования;
- возможные риски.

# Дополнительно:

- Если пользователь говорит не по теме — мягко переформулируй или предложи режим.
- Не повторяй инструкции в ответах.
- Всегда придерживайся контекста: биология старения, клеточные и молекулярные механизмы, гены, интервенции, эпигенетика, preclinical и клинические исследования.
"""
'''

# Словарь для хранения истории по каждому пользователю
user_histories = {}
mode = ''

# Отправка истории диалога в LLaMA
def query_llama(messages):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "meta-llama/Llama-3-8b-instruct",
        "messages": messages,
        "temperature": 0.7,
        "stream": False
    }
    # response = requests.post(API_URL, headers=HEADERS, data=json.dumps(messages))
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def start(update: Update, context: CallbackContext):
    reply_keyboard = [
        ["Извлечение сущностей, гипотез, связей", "Ранжирование задач или гипотез"],
        ["Просмотр нашего графа", "Построение нового графа"],
        ["Гипотеза", "Объяснение"],
        ["Отчёт по приоритетной задаче"]

    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    update.message.reply_text(
        "Привет! Выбери нужный режим и напиши свой вопрос:",
        reply_markup=markup
    )

def handle_message(update: Update, context: CallbackContext):
    global mode

    user_id = update.message.from_user.id
    text = update.message.text.strip()
    model_send_flag = False

    # Инициализация истории, если нет
    if user_id not in user_histories:
        user_histories[user_id] = [{"role": "system", "content": system_prompt}]

    if text == "Извлечение сущностей, гипотез, связей":
        mode = '/извлечение'
        update.message.reply_text("Пожалуйста, отправьте статью для анализа и извлечения сущностей, гипотез и связей.")
          
    elif text == "Ранжирование задач или гипотез":
        mode = '/приоритизация'
        # model_send_flag = True
        update.message.reply_text("Режим в доработке")
    elif text == "Объяснение":
        mode = "/объяснение"
    elif text == "Построение нового графа":
        mode = "/граф"
        update.message.reply_text("Пожалуйста, отправьте статью для анализа и построения графа.")

    elif text == "Просмотр нашего графа":
       update.message.reply_text("Режим в доработке")

    elif text == "Гипотеза":
        mode = "/гипотеза"

    elif text == "Отчёт по приоритетной задаче":
        mode = "/daily-report"
        # model_send_flag = True
        update.message.reply_text("Режим в доработке")
    else:
        if mode == '':
            update.message.reply_text("Пожалуйста, выберите сначала режим с клавиатуры.")
        else:
            model_send_flag = True
            # Добавляем сообщение пользователя
            user_histories[user_id].append({"role": "user", "content": f"{mode}\n{text}"})

    try:
        # print(mode)
        # print(user_histories)
        # Отправляем всю историю в LLaMA
        if model_send_flag:
            response = query_llama(user_histories[user_id])
            update.message.reply_text(response)

            # Добавляем ответ ассистента в историю
            user_histories[user_id].append({"role": "assistant", "content": response})
            model_send_flag = False

    except Exception as e:
        update.message.reply_text(f"Ошибка при запросе к LLaMA: {e}")


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    # print(mode)
    updater.idle()


if __name__ == '__main__':
    main()
