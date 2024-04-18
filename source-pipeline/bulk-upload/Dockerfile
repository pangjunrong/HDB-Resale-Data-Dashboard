FROM python:3.11-alpine
RUN apk update \
&& apk upgrade \
&& apk add --no-cache bash \
&& apk add --no-cache --virtual=build-dependencies unzip \
&& apk add --no-cache curl \
&& apk add --no-cache openjdk8-jre
ENV JAVA_HOME="/usr/lib/jvm/java-1.8-openjdk"
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY ./ .

ENTRYPOINT ["python3"]
CMD ["historical-data.py"]
