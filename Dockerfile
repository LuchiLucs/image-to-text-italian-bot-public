# syntax=docker/dockerfile:1

FROM public.ecr.aws/lambda/python:3.12

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY .env ${LAMBDA_TASK_ROOT}
COPY lambda_main.py ${LAMBDA_TASK_ROOT}
COPY configs/ ${LAMBDA_TASK_ROOT}/configs/
COPY core/ ${LAMBDA_TASK_ROOT}/core/

# avoid writing bytecode files during runtime
# (due to docker storage being temp)
ENV PYTHONDONTWRITEBYTECODE=1

# avoid buffering the stdout and stderr streams
# (logs are sent straight to the streams: avoid losing events when the container exits)
# Ref: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED=1

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_main.lambda_handler" ]