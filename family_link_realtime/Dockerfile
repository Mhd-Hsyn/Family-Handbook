FROM python:3.9-slim

RUN mkdir /family_link_realtime
WORKDIR /family_link_realtime

COPY ./requirements.txt /family_link_realtime/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /family_link_realtime/requirements.txt

COPY . /family_link_realtime/

CMD [ "python", "main.py"]