FROM python:3.9-bullseye

ENV tz=Asia/Taipei

COPY . /app/

WORKDIR /app
RUN pip install -U pip \
    && pip install -r requirements.txt

CMD python3 youtube_crawler.py
