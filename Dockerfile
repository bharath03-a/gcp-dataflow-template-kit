FROM python:3.12-slim

COPY --from=apache/beam_python3.12_sdk:2.66.0 /opt/apache/beam /opt/apache/beam

COPY --from=gcr.io/dataflow-templates-base/python312-template-launcher-base:latest /opt/google/dataflow/python_template_launcher /opt/google/dataflow/python_template_launcher

ARG WORKDIR=/template
WORKDIR ${WORKDIR}

COPY pyproject.toml .
COPY uv.lock .
COPY dataflow_starter_kit dataflow_starter_kit

RUN pip install uv && uv pip install --system -e .

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="${WORKDIR}/dataflow_starter_kit/main.py"

RUN pip check

RUN pip freeze

ENTRYPOINT ["/opt/apache/beam/boot"]