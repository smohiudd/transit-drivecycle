FROM python:3.9-slim

RUN apt-get update && apt-get install -y git

WORKDIR /code

COPY ./drivecycleapi/requirements.txt /code/requirements.txt

RUN pip install -e git+https://github.com/smohiudd/drivecycle.git@50472ce981d18d003146c89febb6ec0a61abdec9#egg=drivecycle

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./drivecycleapi/app /code/app

EXPOSE 81

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "81"]
