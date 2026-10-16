FROM postgres

COPY shell-scripts/* /docker-entrypoint-initdb.d/

RUN mkdir /tmp/scripts

COPY sql-scripts/* /tmp/scripts/
COPY migrations/ /migrations/

RUN chmod -R 777 /docker-entrypoint-initdb.d/ && chmod -R 777 /tmp/scripts

EXPOSE 5432
