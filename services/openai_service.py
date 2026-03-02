from openai import AsyncOpenAI
from config import config


client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def search_topics(user_prompt: str) -> list[str]:
    """Generate 5 topic ideas based on user prompt."""
    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты эксперт по созданию вирального видеоконтента для YouTube и TikTok. "
                    "На основе запроса пользователя предложи 5 конкретных тем для короткого видео. "
                    "Каждая тема должна быть цепляющей, актуальной и подходить для короткого формата (до 60 сек). "
                    "Верни только нумерованный список тем, без лишних пояснений."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=500,
        temperature=0.8,
    )
    raw = response.choices[0].message.content.strip()
    topics = []
    for line in raw.splitlines():
        line = line.strip()
        if line and line[0].isdigit():
            # Remove "1. ", "1) " etc.
            parts = line.split(". ", 1) if ". " in line else line.split(") ", 1)
            topics.append(parts[-1].strip())
    return topics[:5]


async def create_script(topic: str) -> str:
    """Generate a full video script for the given topic."""
    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты профессиональный сценарист для коротких видео (YouTube Shorts / TikTok). "
                    "Создай увлекательный сценарий на 30-60 секунд. "
                    "Структура: Хук (первые 3 сек) → Основная часть → Призыв к действию. "
                    "Пиши текст диктора — живо, динамично, без воды. "
                    "В конце укажи примерную длительность каждой части."
                ),
            },
            {"role": "user", "content": f"Тема видео: {topic}"},
        ],
        max_tokens=800,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


async def create_storyboard_prompt(topic: str, script: str) -> str:
    """Generate a visual storyboard prompt for NanaBanana/Flow video generation."""
    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты эксперт по созданию промптов для генерации видео с помощью ИИ (NanaBanana, Google Flow). "
                    "На основе темы и сценария создай детальный промпт на английском языке для генерации визуального контента. "
                    "Опиши: визуальный стиль, цветовую палитру, движение камеры, атмосферу, ключевые сцены. "
                    "Промпт должен быть конкретным и подходить для текстово-видео генерации. "
                    "Верни только промпт, без лишних пояснений."
                ),
            },
            {
                "role": "user",
                "content": f"Тема: {topic}\n\nСценарий:\n{script}",
            },
        ],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
