FROM python:3.11-slim

WORKDIR /app/server

COPY server/requirements.txt /requirements.txt

RUN pip install --upgrade pip

RUN pip install --retries 10 --timeout=100 --no-cache-dir -r /requirements.txt

COPY . .

RUN chmod +x run.sh

EXPOSE 8000

CMD ["sh", "run.sh"]
