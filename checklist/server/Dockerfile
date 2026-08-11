# Зависимостей нет, поэтому и установки нет: образ — это node и два файла.
FROM node:22-alpine
WORKDIR /app
COPY server.mjs ./
COPY public ./public
ENV DATA_DIR=/data
ENV PORT=3000
EXPOSE 3000
# Каталог /data — это том Railway, он подключается на стороне платформы.
# Инструкцию VOLUME здесь ставить нельзя: сборщик Railway её отвергает.
CMD ["node", "server.mjs"]
