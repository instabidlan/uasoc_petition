FROM python:3.12-slim
COPY requirements.txt /app/requirements.txt

RUN apt-get update && apt-get install -y 
RUN pip install -r /app/requirements.txt

COPY . /app
WORKDIR /app
EXPOSE 51337
CMD ["python3", "main.py"]

