FROM python:3.10

ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt
ADD . /code/

RUN apt-get update && apt-get install cron -y
ADD ./cron/pisces_cron /etc/cron.d/pisces_cron
RUN chmod 0644 /etc/cron.d/pisces_cron
RUN touch /var/log/cron.log
CMD cron && tail -f /var/log/cron.log

ENTRYPOINT ["/code/entrypoint.sh"]
