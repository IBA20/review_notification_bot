FROM python:3.8
RUN apt-get update
RUN mkdir /app
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV DEVMAN_TOKEN=${DEVMAN_TOKEN}
ENV TG_BOT_REQUEST_TIMEOUT=${TG_BOT_REQUEST_TIMEOUT}
ENV TG_BOT_TOKEN=${TG_BOT_TOKEN}
ENV TG_CHATID=${TG_CHATID}
ENTRYPOINT ["python3", "bot.py"]