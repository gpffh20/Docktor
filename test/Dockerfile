#FROM node:20-slim
#CMD ["node", "--version"]

#FROM python:3.11-slim
#RUN pip install 존재하지않는패키지
#CMD ["python", "--version"]


#캐시 효율화 테스트용
#FROM python:3.11-slim
#COPY . .
#RUN pip install -r requirements.txt
#CMD ["python", "--version"]

#보안 이슈 탐지 테스트용
#FROM python:3.11-slim
#RUN chmod u+s /bin/bash
#RUN echo "SECRET_KEY=abc123" > /tmp/.env
#RUN echo "test" > /tmp/config.py && chmod o+w /tmp/config.py
#CMD ["python", "--version"]

#FROM python:3.11-slim
#RUN chmod u+s /bin/bash
#RUN echo "DB_PASSWORD=super_secret" > /tmp/secret.txt
#RUN rm /tmp/secret.txt
#RUN echo "SECRET_KEY=abc123" > /tmp/.env
#RUN echo "test" > /tmp/config.py && chmod o+w /tmp/config.py
#CMD ["python", "--version"]


#캐시 효율화 테스트용
#FROM python:3.11-slim
#COPY . .
#RUN pip install -r requirements.txt
#CMD ["python", "--version"]

#보안 이슈 탐지 테스트용
#FROM python:3.11-slim
#RUN chmod u+s /bin/bash
#RUN echo "SECRET_KEY=abc123" > /tmp/.env
#RUN echo "test" > /tmp/config.py && chmod o+w /tmp/config.py
#CMD ["python", "--version"]

FROM python:3.11-slim
RUN chmod u+s /bin/bash
RUN echo "DB_PASSWORD=super_secret" > /tmp/secret.txt
RUN rm /tmp/secret.txt
RUN echo "SECRET_KEY=abc123" > /tmp/.env
RUN echo "test" > /tmp/config.py && chmod o+w /tmp/config.py
CMD ["python", "--version"]

# 빌드가 오래 걸리지 않도록 네트워크 설치 없이, 오래된 베이스 이미지와
# Dockerfile misconfiguration만으로 Trivy 결과를 유도하는 샘플입니다.

FROM debian:buster-slim

WORKDIR /app

COPY . .
ADD dummy.txt /tmp/dummy.txt

ENV APP_ENV=dev
ENV AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
ENV GITHUB_TOKEN=ghp_exampleexampleexampleexample123456

CMD ["sh", "-c", "sleep 3600"]
