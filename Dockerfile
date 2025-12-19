# PULL THE BASE IMAGE
FROM python:3.12

## SET ENVIRONMENT VARIABLES
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY requirements.txt .

# INSTALL DEPENDENCIES
RUN apt-get update && apt-get install -y \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

# COPY PROJECT
COPY . .


