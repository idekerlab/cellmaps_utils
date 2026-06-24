# ---- build stage ----
FROM python:3.9-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY . /src
# build wheels for your package + deps
RUN pip install --no-cache-dir --upgrade pip wheel \
 && pip wheel --no-cache-dir --wheel-dir /wheels .
# ---- runtime stage ----
FROM python:3.9-slim
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
 && rm -rf /wheels
# the package exposes a CLI users run as `cellmaps_utilscmd.py -h`
ENTRYPOINT ["cellmaps_utilscmd.py"]
CMD ["--help"]


