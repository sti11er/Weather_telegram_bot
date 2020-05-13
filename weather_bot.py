import telebot 
import config
import requests
from googletrans import Translator
from telebot import types
import sqlite3

bot = telebot.TeleBot(config.TOKEN)
translator = Translator()
DATABASE = '/home/denis/telegabot/sql/bot.bd'

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
  text = "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный чтобы определять погоду в вашем городе.".format(message.from_user, bot.get_me())

  # keyboard
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  item1 = types.KeyboardButton("Погода на день")
  item2 = types.KeyboardButton("Погода на 5 дней")

  markup.add(item1, item2)
  bot.send_message(message.chat.id, text,
  parse_mode='html', reply_markup=markup)

@bot.message_handler(content_types = ['text'])
def weather(message):
  if message.chat.type == 'private':
    location = message.text

    #api_key вы можете получить если зарегистрируйтесь на сайте https://api.openweathermap.org/
    api_key = "****************"
    url_by_day = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid={}".format(location, api_key)
    day = requests.get(url_by_day)
    weather_by_day = day.json()
    url_by_weeks = "https://api.openweathermap.org/data/2.5/forecast?q={}&units=metric&appid={}".format(location, api_key)
    week = requests.get(url_by_weeks)
    weather_by_week = week.json()
		

    choice = ["Погода на день", "Погода на 5 дней"]
    if location in choice:
      #добавляем записи в таблицу
      try:
          with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute("INSERT INTO BOT (id, status) VALUES (?, ?)", (message.from_user.first_name, location))
            con.commit()
            bot.send_message(message.chat.id, 'Введите город')

      except:				
        with sqlite3.connect(DATABASE) as con:
          cur = con.cursor()
          cur.execute("UPDATE BOT SET status = ? WHERE id = ?", (location, message.from_user.first_name))
					con.commit()
					bot.send_message(message.chat.id, 'Введите город')

    else:
      try:
        with sqlite3.connect(DATABASE) as con:
          cur = con.cursor()
          cur.execute("SELECT * FROM BOT WHERE id = ?", [message.from_user.first_name])
          status = cur.fetchall()
          status = status[0][1]

        if status == "Погода на день":
          try:					
              sky = weather_by_day['weather'][0]['description']
              sky = translator.translate(sky, src='en', dest='ru')
              sky = sky.text
              sky = 'Погода в ' + str(location) + ':\n\n' + str(sky) + '\n'
              humidity = 'Влажность: ' + str(weather_by_day['main']['humidity']) + "% \n"
              wind = 'Ветер: ' + str(weather_by_day['wind']['speed']) + ' м/с \n'
              pressure = 'Давление: ' + str(weather_by_day['main']['pressure']) + ' pgh\n'
              temp = 'Температура: ' + str(weather_by_day['main']['temp']) +  ' ℃\n'

              try:
                visibility = 'Видимость: ' + str(weather_by_day['visibility']) + ' м' + '\n'
                result = str(sky) + str(humidity) + str(wind) + str(pressure) + str(visibility) + str(temp)
						
              except KeyError:
                 result = str(sky) + str(humidity) + str(wind) + str(pressure) + str(temp)
              bot.send_message(message.chat.id, result)

            except KeyError:
              bot.send_message(message.chat.id, 'Такого города нет!)')

        if status == "Погода на 5 дней":
          try:
             for i in weather_by_week['list']:
                sky = i['weather'][0]['description']
                sky = translator.translate(sky, src='en', dest='ru')
                sky = sky.text
                sky = 'Погода в ' + str(location) + ':\n\n' + str(sky) + '\n'
                data = str(i['dt_txt']) + "\n"
                humidity = 'Влажность: ' + str(i['main']['humidity']) + "% \n"
                wind = 'Ветер: ' + str(i['wind']['speed']) + ' м/с \n'
                pressure = 'Давление: ' + str(i['main']['pressure']) + ' pgh\n'
                temp = 'Температура: ' + str(i['main']['temp']) +  ' ℃\n'
							
                try:
                  visibility = 'Видимость: ' + str(i['visibility']) + ' м' + '\n'
                  result = str(sky) + str(data) + str(humidity) + str(wind) + str(pressure) + str(visibility) + str(temp) 

                except KeyError:
                  result = str(sky) + str(data) + str(humidity) + str(wind) + str(pressure) + str(temp) 

              bot.send_message(message.chat.id, result)
          
         except KeyError:
           bot.send_message(message.chat.id, 'Такого города нет!)')

      except:
        bot.send_message(message.chat.id, 'выберите тип погоды!')

#run
if __name__ == '__main__':
  bot.polling(none_stop=True)
