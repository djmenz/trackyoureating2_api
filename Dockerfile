FROM python:3.9.6

COPY . .

EXPOSE 8000

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

ENTRYPOINT ["python3", "main.py"]
