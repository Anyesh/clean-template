FROM python:3.11.5

RUN apt-get -qq update
RUN pip install --upgrade pip && pip install pip-tools
RUN apt-get install -y --no-install-recommends g++

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE {{cookiecutter.port}}