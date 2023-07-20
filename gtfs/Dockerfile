FROM ghcr.io/public-transport/gtfs-via-postgres

RUN apk --update add postgresql-client
RUN apk add --no-cache bash

COPY ./gtfs/entrypoint.sh /
RUN chmod +x /entrypoint.sh

COPY ./scripts/wait-for-it.sh /

ENTRYPOINT ["sh", "/entrypoint.sh"]