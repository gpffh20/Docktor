FROM node:10.19-slim
WORKDIR /app

COPY package*.json .
# 패키지목록만 복사. 어지간해선 안바뀌는.
RUN npm install
# 패키지만 설치
COPY . .
# 소스코드 복사.

CMD ["node","app.js"]
