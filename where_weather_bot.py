import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": (
            "temperature_2m,"
            "precipitation,"
            "rain,"
            "snowfall,"
            "precipitation_probability"
        ),
        "timezone": "auto",
    }

    r = requests.get(url, params=params, timeout=10).json()
    return r

# Define an asynchronous function for the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Привет {update.effective_user.first_name}! Я твой новый бот о 🌤 погоде!')

# Define an asynchronous function to handle general text messages (an echo bot example)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.text.lower() in ("погода", "🌤 погода"):
        await weather(update, context)
    else:
        await update.message.reply_text(f'Ты написал: {update.message.text}')

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lat = context.user_data.get("latitude")
    lon = context.user_data.get("longitude")

    if lat is None or lon is None:
        await update.message.reply_text(
            "❗ Сначала отправь свою геолокацию 📍"
        )
        return
    
    data = get_weather(lat, lon)

    w = data["current_weather"]

    current_time = w["time"][:13] + ":00"

    times = data["hourly"]["time"]
    precipitation = data["hourly"]["precipitation"]
    precip_prob = data["hourly"]["precipitation_probability"]

    # --- безопасный поиск индекса ---
    if current_time not in times:
        await update.message.reply_text("⚠ Не удалось определить осадки на текущий час")
        return

    # --- индекс текущего часа ---
    idx = times.index(current_time)

    # --- значения осадков ---
    prec_mm = precipitation[idx]
    prec_probability = precip_prob[idx]

    await update.message.reply_text(
        f"🌡 Температура: {w['temperature']} °C\n"
        f"💨 Ветер: {w['windspeed']} м/с\n"
        f"☔ Осадки: {prec_mm} мм\n"
        f"🎯 Вероятность осадков: {prec_probability} %"
    )

# Define an asynchronous function to handle general text messages (an echo bot example)
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Что я умею: /weather или погода - какая погода в ближайший час в указанном месте.')

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    lat = location.latitude
    lon = location.longitude
    context.user_data["latitude"] = location.latitude
    context.user_data["longitude"] = location.longitude
    await update.message.reply_text(f"Получены координаты: Широта={lat}, Долгота={lon}")

if __name__ == '__main__':
    # Replace "YOUR_TOKEN_HERE" with your actual token from BotFather
    bot = ApplicationBuilder().token("0000000000000000").build()

    # Add handlers for commands and messages
    bot.add_handler(CommandHandler("start", start))
    
    bot.add_handler(CommandHandler("help", help))

    bot.add_handler(CommandHandler("weather", weather))

    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    bot.add_handler(MessageHandler(filters.LOCATION & ~filters.COMMAND, handle_location))

    # Start the bot
    print("Fedor Bot is running...")
    bot.run_polling(poll_interval=3.0)
