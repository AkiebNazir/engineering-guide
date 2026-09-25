FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
# Run the app PRE-LOADED with the tracing SDK
CMD ["node", "--require", "./tracing.js", "app.js"]
