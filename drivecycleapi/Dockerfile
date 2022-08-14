FROM python:3.9-slim

RUN apt-get update && apt-get install -y git

WORKDIR /code

COPY ./drivecycleapi/requirements.txt /code/requirements.txt

RUN pip install -e git+https://github.com/smohiudd/drivecycle.git@c1609b97679650e3c304bfc4e912ee69232ba7fb#egg=drivecycle

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# COPY ./drivecycleapi/app /code/app

# COPY ./drivecycleapi/drivecycle /code/drivecycle
# RUN pip install ./drivecycle

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
