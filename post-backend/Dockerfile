FROM python:3.14

WORKDIR /app

COPY requirements.txt ./

COPY external/ ./external/

RUN pip install -r requirements.txt

COPY . .

CMD ["fastapi", "run", "main.py"]
