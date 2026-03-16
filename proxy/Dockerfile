FROM python:3.12-slim
RUN apt-get -y update
RUN mkdir -p /app
WORKDIR /app
COPY proxy/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY proxy/src /app
COPY proxy/tiktoken_cache/ /app
ENV TIKTOKEN_CACHE_DIR=/app/tiktoken_cache
RUN python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"
CMD ["python", "-m", "main_entry"]