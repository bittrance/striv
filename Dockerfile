FROM ubuntu:20.04 AS buildenv

COPY requirements.txt /requirements.txt
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
    make g++ python3.8 python3.8-dev python3-virtualenv
RUN virtualenv /venv
RUN /bin/sh /venv/bin/activate && \
    /venv/bin/pip install -r /requirements.txt

FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install --yes python3.8 libpython3.8 && \
    useradd -d /striv -s /bin/false striv
COPY striv /striv/striv
COPY dist /striv/dist
COPY --from=buildenv /venv /venv
USER striv
WORKDIR /striv

EXPOSE  8080
ENTRYPOINT ["/venv/bin/uwsgi"]
CMD ["--http", ":8080", "--virtualenv", "/venv", "--wsgi-file", "/striv/striv/striv_app.py", "--callable", "prod_entrypoint", "--processes", "4"]
