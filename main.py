# Leo da Vinci
# 
# Volpe Stefano (5Bsa)
# 16/02/2020
# Python 3.8.1

import json
import os.path
import sys
import telebot
from telebot import types

token_filename = 'token.txt'
states_filename = 'states.dat'
topics_filename = '5Bsa.dat'

def check_topic(topic):
    if not ('name' in topic and 'tags' in topic and 'subtopics' in topic):
        print("Errore:")
        print(topic)
        return False
    for x in topic['subtopics']:
        if not check_topic(x):
            return False
    return True

def update_states(states):
    with open(states_filename, 'w') as states_file:
        states_file.write(json.dumps(states))

def get_node(topics, state):
    topics_copy = topics
    for x in state:
        for y in topics_copy["subtopics"]:
            if y["name"] == x:
                topics_copy = y
                break
        else:
            print("Topics: ", topics_copy, "\nState: ", x)
            return None
    return topics_copy

def get_links(topics, tags):
    res = []
    found = False
    for x in topics["tags"]:
        for y in tags:
            if x == y:
                res.append(topics["name"])
                found = True
                break
        if found:
            break
    for x in topics["subtopics"]:
        res.extend(get_links(x, tags))
    return res

def node_to_string(node):
    res = node["name"]
    if not len(node["subtopics"]):
        return res + " (nessun sottoargomento)"
    for x in node["subtopics"]:
        res += "\n - " + x["name"]
    return res

def bot_send_subtopics(bot, message, topics, states):
    bot.send_message(message.chat.id, node_to_string(get_node(topics, states[str(message.from_user.id)])))

def main():
    # Token
    if not os.path.isfile(token_filename):
        print('File token "' + token_filename + '" non trovato.')
        return
    with open(token_filename) as token_file:
        leo = telebot.TeleBot(token_file.readline())
    # States
    states = {}
    if os.path.isfile(states_filename):
        with open(states_filename) as states_file:
            states = json.loads(states_file.read())
    # Topics
    topics = {}
    if os.path.isfile(topics_filename):
        with open(topics_filename) as topics_file:
            topics = json.loads(topics_file.read())
            if not check_topic(topics):
                print('File argomenti "' + topics_filename + '" non valido.')
                return
    else:
        print('File argomenti "' + topics_filename + '" non trovato.')
        return
    print('File argomenti "' + topics_filename + '" valido.')

    @leo.message_handler(commands = ['start'])
    def leo_reply_start(message):
        sticker_filename = 'stickers/greetings.webp'
        if os.path.isfile(sticker_filename):
            with open(sticker_filename, 'rb') as sticker:
                leo.send_sticker(message.chat.id, sticker)
        states[str(message.from_user.id)] = []
        update_states(states)
        leo.send_message(message.chat.id, 'Salve, suddito.')
        bot_send_subtopics(leo, message, topics, states)

    @leo.message_handler(commands = ['help'])
    def leo_reply_help(message):
        sticker_filename = 'stickers/confused.webp'
        if os.path.isfile(sticker_filename):
            with open(sticker_filename, 'rb') as sticker:
                leo.send_sticker(message.chat.id, sticker)
        leo.send_message(message.chat.id,
            'Mi reputo un sovrano illuminato, suddito.'
        )
        leo.send_message(message.chat.id,
            'Digita "/" senza inviare il messaggio: vedrai un elenco di '
            'comandi suggeriti.\n\nPrima di sceglierne uno, ricorda:\n'
            ' - gli elementi delle liste che ti mostro sono "argomenti"\n'
            ' - i titoli delle liste che ti mostro sono "argomenti attuali"\n'
            ' - (+ argomento) ti chiede di specificare il nome di un '
            'argomento dalla lista al quale applicare il comando\n'
            ' - le parole chiave di un argomento sono "temi"\n'
            ' - due argomenti sono collegabili se e solo se hanno almeno '
            'un tema in comune\n'
            ' - (+ tema) ti chiede di specificare un tema qualsiasi'
        )
        bot_send_subtopics(leo, message, topics, states)

    @leo.message_handler(commands = ['close'])
    def leo_reply_close(message):
        if len(states[str(message.from_user.id)]):
            states[str(message.from_user.id)] = states[str(message.from_user.id)][:-1]
            update_states(states)
        else:
            sticker_filename = 'stickers/dunno.webp'
            if os.path.isfile(sticker_filename):
                with open(sticker_filename, 'rb') as sticker:
                    leo.send_sticker(message.chat.id, sticker)
            leo.send_message(message.chat.id, 'Proprio no, suddito...')
            leo.send_message(message.chat.id,
                '"' + topics['name'] + '", in quanto argomento-radice, non ha alcun '
                'argomento che lo contenga.'
            )
        bot_send_subtopics(leo, message, topics, states)
    
    @leo.message_handler(commands = ['open'])
    def leo_reply_open(message):
        command = "/open " # terminating space is so important
        argument = message.text[message.text.find(command) + len(command):]
        node = get_node(topics, states[str(message.from_user.id)])
        for x in node["subtopics"]:
            if x["name"] == argument:
                states[str(message.from_user.id)].append(argument)
                update_states(states)
                break
        else:
            sticker_filename = 'stickers/suspicious.webp'
            if os.path.isfile(sticker_filename):
                with open(sticker_filename, 'rb') as sticker:
                    leo.send_sticker(message.chat.id, sticker)
            leo.send_message(message.chat.id, 'Cosa vai dicendo, suddito?')
            leo.send_message(message.chat.id,
                'Non ho trovato alcun argomento "' +
                argument +
                '" dentro l\'argomento attuale.' if len(argument) else
                'Devi specificare un argomento quando usi questo comando.'
            ) 
        bot_send_subtopics(leo, message, topics, states)

    @leo.message_handler(commands = ['check'])
    def leo_reply_check(message):
        command = "/check " # terminating space is so important
        argument = message.text[message.text.find(command) + len(command):]
        node = get_node(topics, states[str(message.from_user.id)])
        for x in node["subtopics"]:
            if x["name"] == argument:
                if len(x["tags"]):
                    leo.send_message(message.chat.id,
                        'Temi inerenti all\'argomento "' +
                        argument +
                        '":\n' +
                        str(x["tags"])
                    )
                else:
                    leo.send_message(message.chat.id,
                        'Temi inerenti all\'\nargomento "' +
                        argument +
                        '":\nnessuno'
                    )                
                break
        else:
            sticker_filename = 'stickers/suspicious.webp'
            if os.path.isfile(sticker_filename):
                with open(sticker_filename, 'rb') as sticker:
                    leo.send_sticker(message.chat.id, sticker)
            leo.send_message(message.chat.id, 'Cosa vai dicendo, suddito?')
            leo.send_message(message.chat.id,
                'Non ho trovato alcun argomento "' +
                argument +
                '" dentro l\'argomento attuale.' if len(argument) else
                'Devi specificare un argomento quando usi questo comando.'
            ) 
        bot_send_subtopics(leo, message, topics, states)

    @leo.message_handler(commands = ['link'])
    def leo_reply_link(message):
        command = "/link " # terminating space is so important
        argument = message.text[message.text.find(command) + len(command):]
        node = get_node(topics, states[str(message.from_user.id)])
        for x in node["subtopics"]:
            if x["name"] == argument:
                sticker_filename = 'stickers/fanfare.webp'
                if os.path.isfile(sticker_filename):
                    with open(sticker_filename, 'rb') as sticker:
                        leo.send_sticker(message.chat.id, sticker)
                leo.send_message(message.chat.id, 'Per te, suddito. Fanne buon uso!')
                res = 'Collegamenti con l\'argomento "' + argument + '":'
                links = get_links(topics, x["tags"])
                if links:
                    for y in links:
                        if y != x["name"]:
                            res += '\n - ' + y
                else:
                    res += '\nnessuno'
                leo.send_message(message.chat.id, res)
                break
        else:
            sticker_filename = 'stickers/suspicious.webp'
            if os.path.isfile(sticker_filename):
                with open(sticker_filename, 'rb') as sticker:
                    leo.send_sticker(message.chat.id, sticker)
            leo.send_message(message.chat.id, 'Cosa vai dicendo, suddito?')
            leo.send_message(message.chat.id,
                'Non ho trovato alcun argomento "' +
                argument +
                '" dentro l\'argomento attuale.' if len(argument) else
                'Devi specificare un argomento quando usi questo comando.'
            )
        bot_send_subtopics(leo, message, topics, states)

    @leo.message_handler(commands = ['list'])
    def leo_reply_list(message):
        command = "/list " # terminating space is so important
        argument = message.text[message.text.find(command) + len(command):]
        node = get_node(topics, states[str(message.from_user.id)])
        if argument:
            sticker_filename = 'stickers/idea.webp'
            if os.path.isfile(sticker_filename):
                with open(sticker_filename, 'rb') as sticker:
                    leo.send_sticker(message.chat.id, sticker)
            leo.send_message(message.chat.id, 'In quanto re, sono sempre un passo avanti.')
            res = 'Inerenti al tema "' + argument + '":'
            links = get_links(topics, [argument])
            if links:
                for x in links:
                    res += '\n - ' + x
            else:
                res += '\nnessuno'
            leo.send_message(message.chat.id, res)
        else:
            sticker_filename = 'stickers/suspicious.webp'
            if os.path.isfile(sticker_filename):
                with open(sticker_filename, 'rb') as sticker:
                    leo.send_sticker(message.chat.id, sticker)
            leo.send_message(message.chat.id, 'Cosa vai dicendo, suddito?')
            leo.send_message(message.chat.id, 'Devi specificare un argomento quando usi questo comando.')
        bot_send_subtopics(leo, message, topics, states)

    # TODO upload custom JSON

    leo.polling()

if __name__ == '__main__':
    main()