import gradio as gr
import paramiko
import google.generativeai as genai
from datetime import datetime
import os
import webbrowser
import pywhatkit as kit
import pyautogui
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from instagrapi import Client
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import numpy as np
import matplotlib.pyplot as plt
from twilio.rest import Client as TwilioClient

# Gemini Setup
genai.configure(api_key="")  # Add your Gemini API key here
model = genai.GenerativeModel("gemini-1.5-flash")

# Convert instruction to Linux command
def get_command(prompt):
    gemini_prompt = f"""You are a helpful assistant. Convert the following natural language instruction to a single Linux command. Do NOT include quotes or any explanation. Just the command:\n\"{prompt}\" """
    response = model.generate_content(gemini_prompt)
    return response.text.strip()

# SSH Execution
def run_ssh_command(host, username, password, command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode() + stderr.read().decode()
        ssh.close()
        return result
    except Exception as e:
        return f"SSH Connection Failed: {e}"

# Process Input using Gemini-generated command
def process_input(user_input, host, username, password):
    linux_command = get_command(user_input)
    output = run_ssh_command(host, username, password, linux_command)
    with open("command_logs.txt", "a") as f:
        f.write(f"\n[{datetime.now()}] Input: {user_input}\nCommand: {linux_command}\nOutput:\n{output}\n")
    return f"🧠 Command: {linux_command}\n📤 Output:\n{output}"

# Predefined command dropdown handler
def handle_linux_command(command, host, username, password):
    output = run_ssh_command(host, username, password, command)
    with open("command_logs.txt", "a") as f:
        f.write(f"\n[{datetime.now()}] Command: {command}\nOutput:\n{output}\n")
    return f"📤 Output:\n{output}"

# Web launcher
def launch_app_or_website(app_name):
    app_name = app_name.lower()
    try:
        if "youtube" in app_name:
            webbrowser.open("https://www.youtube.com")
        elif "google" in app_name:
            webbrowser.open("https://www.google.com")
        elif "linkedin" in app_name:
            webbrowser.open("https://www.linkedin.com")
        elif "whatsapp" in app_name:
            webbrowser.open("https://web.whatsapp.com")
        elif "notepad" in app_name:
            os.system("notepad.exe")
        else:
            return f"❌ '{app_name}' not recognized. Try YouTube, Google, LinkedIn, WhatsApp, Notepad."
        return f"✅ Launching {app_name.capitalize()}..."
    except Exception as e:
        return f"❌ Failed to launch {app_name}: {e}"

# WhatsApp
def send_whatsapp(receiver_number, message):
    try:
        kit.sendwhatmsg_instantly(receiver_number, message, wait_time=10, tab_close=True)
        time.sleep(12)
        pyautogui.press('enter')
        return "✅ WhatsApp message sent!"
    except Exception as e:
        return f"❌ Failed to send WhatsApp message: {e}"

# Email
def send_email(sender_email, password, receiver_email, subject, body):
    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return "✅ Email sent successfully!"
    except Exception as e:
        return f"❌ Failed to send email: {e}"

# Instagram
def post_to_instagram(username, password, image_path, caption):
    try:
        cl = Client()
        cl.login(username, password)
        cl.photo_upload(image_path.name, caption)
        return "✅ Photo posted successfully!"
    except Exception as e:
        return f"❌ Failed to post on Instagram: {e}"

# Google Search
def google_search(query):
    try:
        results = list(search(query, num_results=5))
        return "\n".join(results)
    except Exception as e:
        return f"❌ Google search failed: {e}"

# Web Data Download
def download_web_data(url):
    folder = "downloaded_data"
    os.makedirs(folder, exist_ok=True)
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        with open(os.path.join(folder, "page.html"), "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        for tag in soup.find_all("a"):
            href = tag.get("href")
            if href and any(href.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".docx", ".zip"]):
                file_url = urljoin(url, href)
                filename = os.path.join(folder, os.path.basename(file_url))
                file_data = requests.get(file_url)
                with open(filename, "wb") as f:
                    f.write(file_data.content)
        files = os.listdir(folder)
        return "Downloaded files:\n" + "\n".join(files)
    except Exception as e:
        return f"❌ Failed to download data: {e}"

# Send SMS using Twilio

def send_sms(account_sid, auth_token, from_number, to_number, message):
    try:
        client = TwilioClient(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        return f"✅ SMS sent! SID: {message.sid}"
    except Exception as e:
        return f"❌ Failed to send SMS: {e}"

def make_call(account_sid, auth_token, from_number, to_number, message):
    try:
        client = TwilioClient(account_sid, auth_token)
        call = client.calls.create(
            twiml=f'<Response><Say>{message}</Say></Response>',
            to=to_number,
            from_=from_number
        )
        return f"✅ Call initiated! SID: {call.sid}"
    except Exception as e:
        return f"❌ Failed to make call: {e}"

# Command List
command_list = [
     "whoami", "hostname", "pwd", "ls -la", "df -h", "free -m", "uptime",
    "top -n 1 -b | head -n 10", "ps aux --sort=-%mem | head -n 10", "id",
    "uname -a", "cat /etc/os-release", "lscpu", "lsblk", "mount", "ifconfig",
    "ip a", "ping -c 4 google.com", "traceroute google.com", "netstat -tuln",
    "ss -tuln", "systemctl status", "journalctl -xe", "who", "last",
    "du -sh *", "find / -name '*.conf'", "grep 'root' /etc/passwd",
    "echo $PATH", "env", "crontab -l", "history | tail -n 20"
]

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# 🐧 AI Linux Assistant + Automation Menu")

    with gr.Tab("🔧 Linux Command"):
        host = gr.Textbox(label="Remote Host (IP Address)")
        user = gr.Textbox(label="Username", value="root")
        passwd = gr.Textbox(label="Password", type="password")

        gr.Markdown("### Select from dropdown OR enter natural language instruction")

        selected_command = gr.Dropdown(command_list, label="Choose a Command")
        command_btn = gr.Button("Run Selected Command")
        command_output = gr.Textbox(label="Result", lines=8)

        command_btn.click(fn=handle_linux_command, inputs=[selected_command, host, user, passwd], outputs=command_output)

        prompt = gr.Textbox(label="Instruction (e.g., list files in home)")
        run_btn = gr.Button("Run Instruction")
        run_btn.click(fn=process_input, inputs=[prompt, host, user, passwd], outputs=command_output)

    with gr.Tab("🌐 Launch App/Website"):
        app_input = gr.Textbox(label="App or Website (e.g., YouTube)")
        launch_btn = gr.Button("Launch")
        launch_result = gr.Textbox(label="Status")
        launch_btn.click(fn=launch_app_or_website, inputs=app_input, outputs=launch_result)

    with gr.Tab("📱 WhatsApp"):
        wa_num = gr.Textbox(label="Receiver Number (with +91)")
        wa_msg = gr.Textbox(label="Message")
        wa_btn = gr.Button("Send WhatsApp")
        wa_result = gr.Textbox(label="Status")
        wa_btn.click(fn=send_whatsapp, inputs=[wa_num, wa_msg], outputs=wa_result)

    with gr.Tab("📧 Email"):
        sender = gr.Textbox(label="Sender Email")
        sender_pwd = gr.Textbox(label="Sender Password", type="password")
        receiver = gr.Textbox(label="Receiver Email")
        subject = gr.Textbox(label="Subject")
        body = gr.Textbox(label="Body", lines=4)
        email_btn = gr.Button("Send Email")
        email_status = gr.Textbox(label="Status")
        email_btn.click(fn=send_email, inputs=[sender, sender_pwd, receiver, subject, body], outputs=email_status)

    with gr.Tab("📸 Instagram Post"):
        insta_user = gr.Textbox(label="Instagram Username")
        insta_pass = gr.Textbox(label="Instagram Password", type="password")
        image = gr.File(label="Upload Image")
        caption = gr.Textbox(label="Caption")
        insta_btn = gr.Button("Post to Instagram")
        insta_status = gr.Textbox(label="Status")
        insta_btn.click(fn=post_to_instagram, inputs=[insta_user, insta_pass, image, caption], outputs=insta_status)

    with gr.Tab("🔍 Google Search"):
        g_query = gr.Textbox(label="Search Query")
        g_btn = gr.Button("Search")
        g_results = gr.Textbox(label="Top 5 Results", lines=5)
        g_btn.click(fn=google_search, inputs=g_query, outputs=g_results)

    with gr.Tab("📂 Web Data Downloader"):
        url_input = gr.Textbox(label="Enter URL")
        download_btn = gr.Button("Download")
        download_result = gr.Textbox(label="Status", lines=6)
        download_btn.click(fn=download_web_data, inputs=url_input, outputs=download_result)

    with gr.Tab("📲 SMS (Twilio)"):
        sms_sid = gr.Textbox(label="Twilio Account SID")
        sms_token = gr.Textbox(label="Twilio Auth Token", type="password")
        sms_from = gr.Textbox(label="From Number (Twilio)")
        sms_to = gr.Textbox(label="To Number")
        sms_msg = gr.Textbox(label="Message")
        sms_btn = gr.Button("Send SMS")
        sms_result = gr.Textbox(label="Status")
        sms_btn.click(fn=send_sms, inputs=[sms_sid, sms_token, sms_from, sms_to, sms_msg], outputs=sms_result)

    with gr.Tab("📞 Call (Twilio)"):
        call_sid = gr.Textbox(label="Twilio Account SID")
        call_token = gr.Textbox(label="Twilio Auth Token", type="password")
        call_from = gr.Textbox(label="From Number (Twilio)")
        call_to = gr.Textbox(label="To Number")
        call_msg = gr.Textbox(label="Message to Speak")
        call_btn = gr.Button("Make Call")
        call_result = gr.Textbox(label="Status")
        call_btn.click(fn=make_call, inputs=[call_sid, call_token, call_from, call_to, call_msg], outputs=call_result)

demo.launch()
