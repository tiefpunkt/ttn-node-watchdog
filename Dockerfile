FROM python:3
COPY . /app
RUN pip install -r /app/requirements.txt; pip install gunicorn; ln -s /data/config.yml /app/config.yml
WORKDIR /app
ENV FLASK_APP=main.py
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:app"]

