# custom_target — stdlib-only vulnerable app (no deps), for the F16 recon-value test.
FROM python:3.12-slim
WORKDIR /app
COPY docker/custom_target/app.py /app/app.py
EXPOSE 3000
CMD ["python3", "/app/app.py"]
