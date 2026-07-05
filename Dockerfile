ARG PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.12-slim
FROM ${PYTHON_IMAGE}

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .
RUN useradd --create-home --shell /usr/sbin/nologin codetrap \
    && mkdir -p /data \
    && chown -R codetrap:codetrap /data

EXPOSE 3141
USER codetrap
CMD ["codetrap-agent", "serve", "--host", "0.0.0.0", "--port", "3141", "--data-dir", "/data"]
