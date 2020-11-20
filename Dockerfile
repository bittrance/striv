FROM alpine:3.12 AS buildenv

COPY requirements.txt /requirements.txt
RUN apk add --no-cache linux-headers make g++ python3-dev py3-pip py3-virtualenv
RUN virtualenv /venv
RUN /bin/sh /venv/bin/activate
RUN /venv/bin/pip3 install -r /requirements.txt

FROM alpine:3.12

RUN apk add --no-cache python3 libstdc++ && adduser -D -h /striv -s /bin/false striv
COPY striv /striv/striv
COPY dist /striv/dist
COPY --from=buildenv /venv /venv
USER striv
WORKDIR /striv

EXPOSE  8080
ENTRYPOINT ["/venv/bin/uwsgi"]
CMD ["--http", ":8080", "--virtualenv", "/venv", "--wsgi-file", "/striv/striv/striv_app.py", "--callable", "entrypoint", "--processes", "4"]
