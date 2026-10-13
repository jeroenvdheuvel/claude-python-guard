FROM python:3.15-alpine
RUN --mount=type=bind,source=requirements.txt,target=/requirements.txt \
    pip install -r /requirements.txt --quiet
COPY --chmod=755 entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
