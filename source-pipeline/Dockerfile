FROM python:3.7-alpine
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./ .

ENTRYPOINT ["python3"]
CMD ["data-pipeline.py"]
