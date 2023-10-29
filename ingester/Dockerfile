FROM python:3.11
COPY . /app
WORKDIR /app
RUN pip3 --no-cache-dir install --upgrade awscli
RUN pip install -r requirements.txt
ENV PYTHONPATH=/app

entrypoint ["python", "main.py"]