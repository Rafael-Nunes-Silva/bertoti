import telebot
from transformers import pipeline

API_TOKEN = "7035694685:AAEG6eT7h-CNxxgh8LVo-XH5CHb3YNRRRXE"
bot = telebot.TeleBot(API_TOKEN)

intencoes = [
    ASK_MENU := "menu",
    ASK_BILL := "bill",
    GIVE_TIP := "give a tip",
    ORDER_FOOD := "order food",
    ORDER_DRINK := "order drink"
]

classi = pipeline("zero-shot-classification")
question_awnsering = pipeline("question-answering") #, model="ktrapeznikov/biobert_v1.1_pubmed_squad_v2", tokenizer="ktrapeznikov/biobert_v1.1_pubmed_squad_v2")

nome_cliente = ""
intencoes_enviadas = []
bill = []
tip = 0

appetizers = [
    ("Caprese Salad", 8.99),
    ("Garlic Bread", 4.99),
    ("Vegetable Spring Rolls", 6.99)
]
main_courses = [
    ("Grilled Chicken Caesar Salad", 12.99),
    ("Spaghetti Bolognese", 14.99),
    ("Teriyaki Salmon", 16.99)
]
desserts = [
    ("Chocolate Lava Cake", 7.99),
    ("New York Cheesecake", 6.99),
    ("Fruit Salad", 5.99)
]
beverages = [
    ("Soda", 2.50),
    ("Iced Tea", 2.99),
    ("Freshly Squeezed Orange Juice", 3.99),
    ("Bottled Water (Still or sparkling)", 1.99)
]

class STATES:
    START = "start"
    MENU = "menu"
    BILL = "bill"
    TIP = "tip"
    FOOD = "food"
    DRINK = "drink"
    END = "end"
    NOT_UNDERSTOOD = "not understood"
    FINISH = "finish"

STATE = STATES.START

@bot.message_handler(commands = ["start", "help"])
def msg_inicial(message):
    global nome_cliente
    nome_cliente = message.from_user.first_name

    bot.reply_to(message, f"Wellcome to PA's Restaurant, {nome_cliente}")
    bot.reply_to(message, "Tell me what your order is")
    bot.reply_to(message, "When you're finished ordering, ask for your bill")

@bot.message_handler(func=lambda message: True)
def reply(message):
    global STATE, STATES, intencoes, nome_cliente, intencoes_enviadas, bill, tip
    nome_cliente = message.from_user.first_name

    print("-----------------------------------------------")

    print(f"{intencoes=}")
    print(f"{nome_cliente=}")
    print(f"{intencoes_enviadas=}")

    STATE = filtro(message.text)
    print(f"{STATE=}")

    if STATE == STATES.START:
        res = ""
        i = 0
        intencoes_atuais = []
        for intencao in classi(message.text, intencoes)["labels"][:3]:
        intencoes_atuais.append(intencao)

        i += 1
        res += f"{i} - {intencao}\n"

        intencoes_enviadas = intencoes_atuais
        bot.reply_to(message, f"Please confirm your choice:\n{res}")

    elif STATE == STATES.NOT_UNDERSTOOD:
        bot.reply_to(message, "Sorry, I couldn't understand that")

    elif STATE == STATES.END:
        bot.reply_to(message, "I've added it to your bill")

    elif STATE == STATES.FINISH:
        bot.reply_to(message, f"Thank you {nome_cliente}, come back always")

    elif STATE == STATES.MENU:
        bot.reply_to(message, '\n'.join([
        "Menu:",
        "",
        "Appetizers:",
        *[f"{a[0]} - {a[1]:.2f}" for a in appetizers],
        "",
        "Main Courses:",
        *[f"{mc[0]} - {mc[1]:.2f}" for mc in main_courses],
        "",
        "Desserts:",
        *[f"{d[0]} - {d[1]:.2f}" for d in desserts],
        "",
        "Beverages:",
        *[f"{b[0]} - {b[1]:.2f}" for b in beverages],
        "",
        "What's it going to be?"
        ]))
    elif STATE == STATES.BILL:
        if bill:
        bill_txt = f"{nome_cliente}'s Bill\n"

        print(f"{bill=}")

        total = tip
        for item in bill:
            bill_txt += f"\t{item[0]} - {item[1]:.2f}\n"
            total += item[1]
        if tip:
            bill_txt += f"Tip: {tip}\n"
        bill_txt += f"Total: {total:.2f}"

        bill = []
        tip = 0

        bot.reply_to(message, bill_txt)
        STATE = STATES.FINISH
        else:
        bot.reply_to(message, "You didn't order anything yet")
        STATE = STATES.START
    elif STATE == STATES.TIP:
        bot.reply_to(message, "How much do you wish to tip?")
        STATE = STATES.TIP
    elif STATE == STATES.FOOD:
        bot.reply_to(message, '\n'.join([
        "Appetizers:",
        *[f"{a[0]} - {a[1]:.2f}" for a in appetizers],
        "",
        "Main Courses:",
        *[f"{mc[0]} - {mc[1]:.2f}" for mc in main_courses],
        "",
        "Desserts:",
        *[f"{d[0]} - {d[1]:.2f}" for d in desserts],
        "",
        "What's it going to be?"
        ]))
    elif STATE == STATES.DRINK:
        bot.reply_to(message, '\n'.join([
        "Beverages:",
        *[f"{b[0]} - {b[1]:.2f}" for b in beverages],
        "",
        "What's it going to be?"
        ]))

def filtro(msg_text: str) -> str:
    global STATES, intencoes, nome_cliente, intencoes_enviadas, bill, tip

    if STATE == STATES.TIP:
        amount = question_awnsering(context=msg_text, question="How much will it tip?")["answer"]
        tip = float(amount)

        if not amount:
        return STATES.NOT_UNDERSTOOD
        return STATES.END
    
    elif msg_text.isnumeric():
        msg_number = int(msg_text)
        intencao = intencoes[intencoes.index(intencoes_enviadas[msg_number-1])]

        if intencao == ASK_MENU:      return STATES.MENU
        elif intencao == ASK_BILL:    return STATES.BILL
        elif intencao == GIVE_TIP:    return STATES.TIP
        elif intencao == ORDER_FOOD:  return STATES.FOOD
        elif intencao == ORDER_DRINK: return STATES.DRINK
        return STATES.NOT_UNDERSTOOD

    elif STATE == STATES.MENU or STATE == STATES.FOOD or STATE == STATES.DRINK:
        order = question_awnsering(context=msg_text, question="What does it want?")["answer"]
        print(f"{order=}")

        complete_menu = appetizers + main_courses + desserts + beverages

        found = False
        for item in complete_menu:
        if item[0].lower() in order.lower() or order.lower() in item[0].lower():
            bill.append(item)
            found = True
            break

        if not found:
        return STATES.NOT_UNDERSTOOD

        print(f"{bill=}")
        return STATES.END

    return STATES.START



bot.polling()