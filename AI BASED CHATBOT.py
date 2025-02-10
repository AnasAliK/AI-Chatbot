import gradio as gr
import openai
import time

openai.api_key = ""


with gr.Blocks(css=".gradio-container {background: url('https://www.pixelstalk.net/wp-content/uploads/2016/06/Technology-Desktop-Backgrounds.jpg');background-size: 150% 150%;}") as demo:
    header = gr.HTML("<h1 style='font-weight:bold;text-align:center;font-size:40px;');'>AI BASED CHATBOT</h1>")
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    send = gr.Button("Send")
    clear = gr.Button("Clear")

    messages = [{"role": "system", "content": "You are an AI pre-trained bot."}]
    
    def user(user_message, history):
        return "", history + [[user_message, None]]
    
    def bot(history):
        messages.append({"role": "user", "content": history[-1][0]})
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt="Conversation with AI:\n\nUser: " + history[-1][0] + "\nCHAT-BOT:",
            temperature=0.5,
            max_tokens=1024,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        bot_message = response.choices[0].text
        messages.append({"role": "assistant", "content": bot_message})
        history[-1][1] = ""
        for character in bot_message:
            history[-1][1] += character
            time.sleep(0.05)
            yield history
    
    def send_message():
        msg.process()
        chatbot.process()
        msg_str = msg.value.strip()
        if msg_str:
            chatbot.append(msg_str)
            user_result = user(msg_str, chatbot.history)
            messages.append({"role": "user", "content": msg_str})
            chatbot.history = user_result[1]
            msg.update("")
            chatbot.update(chatbot.history)
            bot(chatbot.history)
    
    msg_submit = msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False)
    msg_submit.then(bot, chatbot, chatbot)
    send.click(send_message)
    clear.click(lambda: None, None, chatbot, queue=False)
    


demo.queue()
demo.launch(share=True)
