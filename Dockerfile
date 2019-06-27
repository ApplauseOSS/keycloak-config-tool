FROM alpine:3.9

COPY ./keycloak_config /keycloak-config-tool/keycloak_config
COPY ./setup.py /keycloak-config-tool/setup.py
COPY ./setup.cfg /keycloak-config-tool/setup.cfg
COPY ./README.md /keycloak-config-tool/README.md
COPY ./VERSION /keycloak-config-tool/VERSION

RUN apk add bash python3 py3-cryptography && \
    pip3 install /keycloak-config-tool/.

COPY ./encoding.sh /etc/profile.d/encoding.sh
COPY ./VERSION /IMAGE-VERSION

COPY ./docker-entrypoint.sh /docker-entrypoint.sh

ENTRYPOINT [ "/docker-entrypoint.sh" ]
