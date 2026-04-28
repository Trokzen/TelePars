import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

# Список каналов для парсинга
CHANNELS = [
    "dnsru",          # DNS - магазин
    "citilink",       # Citilink - магазин
    "overclockers",   # Overclockers.ru - сообщество
    "hardware_ru"     # Hardware.ru - сообщество
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def scrape_telegram_channel(channel_name, max_posts=50):
    """
    Парсинг публичных постов Telegram-канала
    """
    print(f"\n📡 Загрузка канала: @{channel_name}")
    url = f"https://t.me/s/{channel_name}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка доступа к каналу {channel_name}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    posts = soup.select(".tgme_widget_message_wrap")
    
    if not posts:
        print(f"⚠️  Канал @{channel_name} пуст или приватный")
        return []
    
    data = []
    for i, post in enumerate(posts[:max_posts]):
        # Дата публикации
        date_el = post.select_one(".tgme_widget_message_date time")
        date = date_el.get("datetime", "") if date_el else ""
        
        # Текст поста
        text_el = post.select_one(".tgme_widget_message_text")
        text = text_el.get_text(separator=" ", strip=True) if text_el else ""
        
        # Реакции/просмотры
        views_el = post.select_one(".tgme_widget_message_views")
        views = views_el.get_text(strip=True) if views_el else "0"
        
        # Ссылка на пост
        link_el = post.select_one(".tgme_widget_message_date")
        link = link_el.get("href", "") if link_el else ""
        
        # Тип контента (есть ли фото/видео)
        has_media = "Yes" if post.select_one(".tgme_widget_message_photo_wrap, .tgme_widget_message_video") else "No"
        
        data.append({
            "channel": channel_name,
            "date": date,
            "text": text,
            "views": views,
            "has_media": has_media,
            "post_link": link,
            "text_length": len(text)
        })
        
        # Задержка чтобы не блокировали
        time.sleep(1.2)
        
        if (i + 1) % 10 == 0:
            print(f"  Обработано постов: {i + 1}/{min(len(posts), max_posts)}")
    
    print(f"✅ Канал @{channel_name}: собрано {len(data)} постов")
    return data

def analyze_keywords(data, keywords):
    """
    Анализ упоминаний ключевых слов
    """
    results = {}
    for kw in keywords:
        count = sum(1 for post in data if kw.lower() in post['text'].lower())
        if count > 0:
            results[kw] = count
    return results

def main():
    print("=" * 60)
    print(" ПАРСИНГ TELEGRAM-КАНАЛОВ ДЛЯ ЛАБОРАТОРНОЙ РАБОТЫ №2")
    print("=" * 60)
    print(f"📅 Дата начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_posts = []
    
    # Парсинг всех каналов
    for channel in CHANNELS:
        posts = scrape_telegram_channel(channel, max_posts=50)
        all_posts.extend(posts)
        time.sleep(2)  # пауза между каналами
    
    if not all_posts:
        print("\n❌ Не удалось собрать данные. Проверьте названия каналов.")
        return
    
    # Сохранение в CSV
    df = pd.DataFrame(all_posts)
    filename = f"telegram_parse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"\n💾 Все данные сохранены в: {filename}")
    
    # Статистика по каналам
    print("\n" + "=" * 60)
    print("📊 СТАТИСТИКА ПО КАНАЛАМ")
    print("=" * 60)
    channel_stats = df.groupby('channel').agg({
        'post_link': 'count',
        'views': lambda x: x.str.replace('\u202f', '').str.replace(' ', '').astype(int).sum() if len(x) > 0 else 0
    }).rename(columns={'post_link': 'posts_count'})
    print(channel_stats)
    
    # Анализ ключевых слов (для видеокарт)
    print("\n" + "=" * 60)
    print("🔑 АНАЛИЗ УПОМИНАНИЙ КЛЮЧЕВЫХ СЛОВ")
    print("=" * 60)
    keywords = [
        "видеокарта", "RTX", "GTX", "AMD", "NVIDIA", "GPU", 
        "RTX 4060", "RTX 4070", "RX 7700", "цена", "акция", 
        "скидка", "наличие", "гарантия", "купить"
    ]
    
    keyword_stats = analyze_keywords(all_posts, keywords)
    for kw, count in sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {kw:15} → {count} упоминаний")
    
    # Анализ по типам контента
    print("\n" + "=" * 60)
    print("📹 АНАЛИЗ ТИПОВ КОНТЕНТА")
    print("=" * 60)
    media_stats = df.groupby('has_media').size()
    for media_type, count in media_stats.items():
        print(f"  {'С медиа' if media_type == 'Yes' else 'Только текст'}: {count} постов")
    
    # Выводы для лабораторной
    print("\n" + "=" * 60)
    print("📝 ПРЕДВАРИТЕЛЬНЫЕ ВЫВОДЫ ДЛЯ ОТЧЁТА")
    print("=" * 60)
    
    # Активность каналов
    most_active = df['channel'].value_counts().idxmax()
    print(f"1. Самый активный канал: @{most_active}")
    
    # Популярные темы
    if keyword_stats:
        top_keyword = max(keyword_stats, key=keyword_stats.get)
        print(f"2. Наиболее обсуждаемая тема: {top_keyword}")
    
    # Тип контента
    if 'Yes' in media_stats.values and 'No' in media_stats.values:
        if media_stats.get('Yes', 0) > media_stats.get('No', 0):
            print("3. Преобладает контент с медиа (фото/видео)")
        else:
            print("3. Преобладает текстовый контент")
    
    print("\n✅ Парсинг завершён успешно!")
    print(f"📁 Файл для отчёта: {filename}")

if __name__ == "__main__":
    main()
