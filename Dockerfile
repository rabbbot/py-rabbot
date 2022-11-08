FROM python:3

COPY scripts/*.py /src/
COPY requirements.txt /src/
RUN mkdir -p src/logs

RUN pip install -r src/requirements.txt

CMD [ "python", "src/bot.py" ]