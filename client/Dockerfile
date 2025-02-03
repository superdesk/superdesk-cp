FROM node:14

RUN useradd -ms /bin/sh -u 1001 app
USER app

WORKDIR /opt/client
COPY package.json package-lock.json ./
RUN npm ci

COPY --chown=app:app . /opt/client

RUN npm run build

CMD ["npm", "run", "start"]
