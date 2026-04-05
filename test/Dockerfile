#FROM 존재하지않는이미지:latest

#FROM python:3.11-slim
#CMD ["python", "--version"]



#FROM python:3.11
#RUN pip install pandas numpy matplotlib scikit-learn




# 테스트 Dockerfile
## 빌드 스테이지
#FROM node:latest AS builder
#
#COPY . .
#COPY package.json ./
#
#RUN npm install
#RUN npm run build
#
## 실행 스테이지
#FROM node:20-slim
#
#WORKDIR /app
#
#COPY --from=builder /app/dist ./dist
#
#RUN apt-get update && apt-get install -y curl
#
#CMD ["node", "dist/app.js"]


#FROM node:latest AS builder
#RUN echo "building..."

#FROM python:3.11-slim AS tester
#RUN echo "testing..."

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

FROM python:3.11-slim
RUN chmod u+s /bin/bash
RUN echo "DB_PASSWORD=super_secret" > /tmp/secret.txt
RUN rm /tmp/secret.txt
RUN echo "SECRET_KEY=abc123" > /tmp/.env
RUN echo "test" > /tmp/config.py && chmod o+w /tmp/config.py
CMD ["python", "--version"]