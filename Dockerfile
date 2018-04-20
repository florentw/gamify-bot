FROM python:3

WORKDIR /usr/src/app

COPY . /usr/src/app
COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt \
&& chmod +x /usr/src/app/release.sh \
&& /usr/src/app/release.sh 1.0

CMD [ "python3", "/usr/src/app/gamifybot.py" ]
