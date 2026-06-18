FROM python:3.14-alpine
RUN pip install bandit --quiet
COPY --chmod=755 entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
