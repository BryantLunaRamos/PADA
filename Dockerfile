FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common.py diit_pipeline.py diit_award_size_test.py diit_award_method_fisher_test.py run_all.py ./

RUN mkdir -p /app/data /app/output

ENTRYPOINT ["python3", "run_all.py"]
