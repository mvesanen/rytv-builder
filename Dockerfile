FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        pandoc \
        texlive-xetex \
        texlive-fonts-recommended \
        lmodern \
        fonts-dejavu \
        nodejs \
        npm \
        chromium \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    MMDC_PUPPETEER_CONFIG=/puppeteer-config.json

RUN npm install -g @mermaid-js/mermaid-cli

WORKDIR /opt/rytv-builder
COPY docker/puppeteer-config.json /puppeteer-config.json
COPY builder /opt/rytv-builder/builder
ENV PYTHONPATH=/opt/rytv-builder

ENTRYPOINT ["python", "-m", "builder"]
CMD ["/publication"]
