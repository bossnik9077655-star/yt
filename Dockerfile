# Python का स्थिर इमेज इस्तेमाल करें
FROM python:3.10-slim

# कंटेनर के अंदर काम करने की जगह सेट करें
WORKDIR /app

# अपनी सभी फाइलों को कंटेनर में कॉपी करें
COPY . /app

# ज़रूरी लाइब्रेरीज़ इनस्टॉल करें
RUN pip install --no-cache-dir -r requirements.txt

# Render के लिए पोर्ट 8080 को ओपन करें
EXPOSE 8080

# बॉट को स्टार्ट करें
CMD ["python", "bot.py"]
