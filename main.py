from dotenv import load_dotenv, dotenv_values
import json
import urllib.request
import schedule
import datetime

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

temp_value = {
    '0': ['Пн', 'I 8:30-10:05', 'II 10:20-11:55', 'П', 'ОБЛАЧНЫЕ ТЕХНОЛОГИИ лекц. 5-232 Белов', 'III 12:10-13:45', 'П',
          'УПРАВЛЕНИЕ ПРОГРАМ. ПРОЕКТАМИ упр. 5-222 Амеличева', 'IV 14:15-15:50', 'V 16:05-17:40'],
    '1': ['Вт', 'I 8:30-10:05', 'II 10:20-11:55', 'III 12:10-13:45', 'IV 14:15-15:50', 'V 16:05-17:40', 'П',
          'ОБЛАЧНЫЕ ТЕХНОЛОГИИ лаб. I 5-158 Амеличев ТЕХНОЛ. АНАЛИЗА ДАННЫХ лаб. II 5-219 Ерохин', 'VI 17:50-19:25',
          'Ч', 'ПРОЕКТИР. ПРОГРАМ. ОБЕСПЕЧЕНИЯ лаб. II 5-231 Красавин', 'З',
          'ПРОЕКТИР. ПРОГРАМ. ОБЕСПЕЧЕНИЯ лаб. I 5-231 Красавин', 'VII 19:35-21:10'],
    '2': ['Ср', 'I 8:30-10:05', 'II 10:20-11:55', 'П', 'БЕСПРОВ. ТЕХНОЛ. ПЕРЕДАЧИ ДАННЫХ лекц. 5-108 Гришунов',
          'III 12:10-13:45', 'П',
          'БЕСПРОВ. ТЕХНОЛ. ПЕРЕДАЧИ ДАННЫХ лаб. I 5-224 Красавин ОБЛАЧНЫЕ ТЕХНОЛОГИИ лаб. II 5-219 Амеличев',
          'IV 14:15-15:50', 'V 16:05-17:40'],
    '3': ['Чт', 'I 8:30-10:05', 'Ч', 'ТЕХНОЛ. АНАЛИЗА ДАННЫХ лекц. 5-108 Ерохин', 'З',
          'УПРАВЛЕНИЕ ПРОГРАМ. ПРОЕКТАМИ лекц. 5-108 Амеличева', 'II 10:20-11:55', 'П',
          'ТЕХНОЛ. АНАЛИЗА ДАННЫХ лаб. I 5-219 Ерохин БЕСПРОВ. ТЕХНОЛ. ПЕРЕДАЧИ ДАННЫХ лаб. II 5-224 Красавин',
          'III 12:10-13:45', 'Ч',
          'ТЕХНОЛ. АНАЛИЗА ДАННЫХ лаб. I 5-219 Ерохин ПРОЕКТИР. ПРОГРАМ. ОБЕСПЕЧЕНИЯ лаб. II 5-231 Красавин', 'З',
          'ПРОЕКТИР. ПРОГРАМ. ОБЕСПЕЧЕНИЯ лаб. I 5-231 Красавин ТЕХНОЛ. АНАЛИЗА ДАННЫХ лаб. II 5-219 Ерохин',
          'IV 14:15-15:50'],
    '4': ['Пт', 'I 8:30-10:05', 'П', 'ВОЕННАЯ ПОДГОТОВКА к.4', 'II 10:20-11:55', 'П', 'ВОЕННАЯ ПОДГОТОВКА к.4',
          'III 12:10-13:45', 'П', 'ВОЕННАЯ ПОДГОТОВКА к.4', 'IV 14:15-15:50', 'П', 'ВОЕННАЯ ПОДГОТОВКА к.4',
          'V 16:05-17:40', 'П', 'ВОЕННАЯ ПОДГОТОВКА к.4', 'VI 17:50-19:25'],
    '5': ['Сб', 'I 8:30-10:05', 'П', 'НИР  к.5', 'II 10:20-11:55', 'П',
          'ПРОЕКТИР. ПРОГРАМ. ОБЕСПЕЧЕНИЯ лекц. 5-162 Красавин', 'III 12:10-13:45']}

load_dotenv()
envs = dotenv_values()
timetable_api_url = envs['TIMETABLE_URL']


class DataTimetable:
    timetable_data = {}
    days_short = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
    days_greek = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    parity_syms = ['П', 'З', 'Ч']
    exception_list = ['ВОЕННАЯ ПОДГОТОВКА к.4']

    def __init__(self):
        self.old_timetable_str = json.dumps(temp_value)

    def check_update(self):
        pass
        timetable_str = urllib.request.urlopen(timetable_api_url).read().decode('utf-8')
        if timetable_str == self.old_timetable_str:
            return
        self.timetable_data = self.parse_timetable(json.loads(timetable_str))

    def auto_message(self):
        current_weekday = datetime.datetime.now().weekday()
        if current_weekday == 6:
            print('сейчас воскресенье')
            current_weekday = 0
        print(self.timetable_data)

    def parse_timetable(self, json_obj):
        table = {}
        for day in json_obj:
            info = json_obj[day][1:]
            greek_time = None
            is_sym = False
            for line in info:
                if is_sym is True:
                    if line not in self.exception_list:
                        if day not in table:
                            table[day] = []
                        if greek_time is not None:
                            table[day].append(f'{greek_time} {line}')
                        else:
                            table[day][-1] += '\n-> ' + line
                    is_sym = False
                    greek_time = None
                    continue
                command = line.split(' ')[0]
                temp_greek = get_index(self.days_greek, command)
                temp_sym = get_index(self.parity_syms, command)

                if temp_greek is not None:
                    greek_time = line

                if temp_sym is not None:
                    is_sym = True

        return table

    async def yesterday_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        yesterday_weekday = datetime.datetime.now().weekday() - 1
        if yesterday_weekday < 0:
            yesterday_weekday = 5
        await update.message.reply_text(self.get_table_str(yesterday_weekday))

    async def today_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current_weekday = datetime.datetime.now().weekday()
        if current_weekday == 6:
            current_weekday = 0
        await update.message.reply_text(self.get_table_str(current_weekday))

    async def tomorrow_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        tomorrow_weekday = datetime.datetime.now().weekday() + 1
        if tomorrow_weekday >= 6:
            tomorrow_weekday = 0
        await update.message.reply_text(self.get_table_str(tomorrow_weekday))

    async def full_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for day in self.timetable_data:
            await update.message.reply_text(f'{self.days_short[int(day)]} \n{self.get_table_str(day)}')

    def get_table_str(self, day):
        return self.days_short[int(day)] + '\n' + '\n\n'.join(self.timetable_data[str(day)])



def get_index(arr: list, elem):
    temp = None
    try:
        temp = arr.index(elem)
    except ValueError:
        pass

    return temp


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)


if __name__ == '__main__':
    application = Application.builder().token(envs['API_KEY']).build()
    application.bot.set_chat_menu_button()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    data_timetable = DataTimetable()
    data_timetable.check_update()

    application.add_handler(CommandHandler("yesterday", data_timetable.yesterday_message))
    application.add_handler(CommandHandler("today", data_timetable.today_message))
    application.add_handler(CommandHandler("tomorrow", data_timetable.tomorrow_message))
    application.add_handler(CommandHandler("full", data_timetable.full_message))

    schedule.every().day.at('18:00:00').do(data_timetable.check_update)
    schedule.every().day.at('20:00:00').do(data_timetable.auto_message)
    application.run_polling()
