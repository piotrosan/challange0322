FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
RUN if [[ -z "$WITH_DATABASE" ]]; then cp bin/db.sqlite3 /code fi;
RUN if [[ -z "$WITH_DATABASE" ]]; then python /code/manage.py run_migrates fi;