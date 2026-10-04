FROM docker.io/neo4j:{{ cookiecutter.neo4j_version }}-community

COPY ./compose/production/neo4j/maintenance /usr/local/bin/maintenance
COPY ./compose/production/postgres/maintenance/_sourced /usr/local/bin/maintenance/_sourced
RUN chmod +x /usr/local/bin/maintenance/*
RUN mv /usr/local/bin/maintenance/* /usr/local/bin \
    && rmdir /usr/local/bin/maintenance

# Maintenance scripts run as the neo4j user, so the backups volume must belong to it.
# Docker copies this ownership into the named volume the first time it is mounted.
RUN mkdir -p /backups \
    && chown neo4j:neo4j /backups
