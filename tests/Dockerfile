FROM python:3.7-alpine
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./app.py .

ENTRYPOINT ["python3"]
CMD ["app.py"]
