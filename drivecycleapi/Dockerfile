FROM python:3.9-slim

WORKDIR /code

COPY ./drivecycleapi/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# COPY ./drivecycleapi/app /code/app

COPY ./drivecycleapi/drivecycle /code/drivecycle
RUN pip install ./drivecycle

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
