# FraudShield

FraudShield là project phát hiện giao dịch gian lận, đồng thời là đồ án cuối kì cho môn Intro to Data Science của nhóm. Repo này đi theo một luồng khá đầy đủ: lấy dữ liệu, xử lý đặc trưng, huấn luyện mô hình, tinh chỉnh ngưỡng dự đoán, chạy API, mở giao diện thử nhanh và sinh báo cáo drift để theo dõi sau khi triển khai.

Dữ liệu dùng trong project là bộ Kaggle `fraud-detection-1m-transactions-7-fraud-types`. Trong bộ đó có nhiều file, nhưng pipeline của repo chỉ dùng đúng file `transactions.csv`.

## Cấu trúc repo

```text
.
├── configs/                  # Cấu hình các mô hình đem ra so sánh lúc train
├── data/
│   ├── raw/                  # Dữ liệu gốc, lấy từ Kaggle hoặc kéo qua DVC
│   └── processed/            # Dữ liệu đã xử lý, sinh ra sau bước feature engineering
├── deployment/
│   ├── k8s/                  # Manifest để triển khai API, monitoring job và Grafana
│   └── mlflow/               # Docker Compose để chạy MLflow local
├── models/
│   ├── artifacts/            # Encoder, scaler và các phần cần dùng lại lúc dự đoán
│   └── trained/              # Model cuối cùng, metadata và danh sách cột đầu vào
├── notebooks/                # Notebook phân tích đã chốt, để tham khảo logic và kết quả
├── reports/
│   ├── training/             # Bảng so sánh model và thông tin model tốt nhất
│   └── drift_report.html     # Báo cáo drift, sinh ra khi chạy monitoring
├── src/
│   ├── api/                  # FastAPI, schema request/response và logic dự đoán
│   ├── data/                 # Script tải riêng transactions.csv từ Kaggle
│   ├── features/             # Xử lý đặc trưng, dùng chung cho train và inference
│   ├── model/                # Train baseline, chọn model và tuning
│   ├── monitoring/           # Metric, drift report và phần đẩy report lên cloud
│   └── streamlit/            # Giao diện nhập giao dịch và gọi API để xem kết quả
├── dvc.yaml                  # Luồng chạy chính: xử lý dữ liệu -> train -> tuning
├── dvc.lock                  # Trạng thái đã khóa của pipeline DVC
├── params.yaml               # Tham số cho lần chạy full data
├── pyproject.toml            # Dependency Python, repo này thống nhất dùng uv
└── uv.lock                   # Lockfile để cài dependency ổn định hơn
```

## Téch Stáck

- Python 3.11+
- `uv` để cài dependency và chạy command Python
- DVC để quản lý dữ liệu, artifact và pipeline
- pandas, scikit-learn, LightGBM, XGBoost, CatBoost, Optuna cho phần dữ liệu và mô hình
- MLflow để ghi lại thí nghiệm huấn luyện
- FastAPI và Uvicorn để chạy API dự đoán
- Streamlit để có giao diện thử nhanh
- Evidently, Prometheus, BigQuery và GCS cho phần theo dõi vận hành
- Docker, Kubernetes, Helm và GitHub Actions cho phần triển khai

## Chuẩn bị máy local

Cần có sẵn:

- Git
- Python nằm trong khoảng `>=3.11,<3.14`
- `uv`
- Docker và Docker Compose, để chạy MLflow hoặc build image API
- `curl`, để test API nhanh từ terminal
- Kaggle API credential nếu Kaggle bắt đăng nhập khi tải dữ liệu
- AWS credential nếu muốn dùng DVC remote S3
- Google Cloud CLI, `kubectl` và Helm nếu muốn test phần GKE/Kubernetes

Clone đúng repo:

```bash
git clone git@github.com:DDuckG/FraudShield.git
cd FraudShield
```

Cài dependency:

```bash
uv sync
cp .env.example .env
```

File `.env` dùng cho local. Nếu chỉ train và chạy API trên máy cá nhân thì có thể để trống các biến cloud trước, nhưng phần lưu prediction, feedback và drift report sẽ cần GCS/BigQuery.

## Cấu hình `.env`

Mẫu nằm ở `.env.example`.

```bash
APP_ENV=dev
SERVICE_NAME=fraud-detection-api
MODEL_VERSION=local
MODELS_DIR=models

MLFLOW_TRACKING_URI=http://localhost:5555

GCS_BUCKET_NAME=
PREDICTION_PREFIX=predictions
FEEDBACK_PREFIX=feedbacks
DRIFT_REPORT_PREFIX=drift-reports

PROJECT_ID=
BQ_DATASET=fraud_monitoring
REFERENCE_DATA_PATH=data/raw/transactions.csv
MIN_ROWS=50
MIN_UNIQUE=2

FRAUD_API_URL=http://localhost:8000
```

Các biến hay phải chỉnh:

| Biến | Dùng để làm gì |
| --- | --- |
| `MODEL_VERSION` | Ghi version model kèm mỗi prediction |
| `MODELS_DIR` | Thư mục chứa model và artifact, mặc định là `models` |
| `MLFLOW_TRACKING_URI` | Địa chỉ MLflow server khi train |
| `GCS_BUCKET_NAME` | Bucket lưu prediction, feedback và drift report |
| `PROJECT_ID` | Google Cloud project dùng cho BigQuery và GCS |
| `BQ_DATASET` | Dataset BigQuery chứa bảng/view monitoring |
| `REFERENCE_DATA_PATH` | File dữ liệu tham chiếu để so drift |
| `FRAUD_API_URL` | URL API mà Streamlit gọi tới |

## Lấy dữ liệu

### Tải từ Kaggle

Chạy lệnh:

```bash
uv run python src/data/get_data.py
```

Script sẽ tải archive Kaggle, lấy đúng `transactions.csv`, rồi lưu vào:

```text
data/raw/transactions.csv
```

Nếu Kaggle yêu cầu đăng nhập, tạo file credential của Kaggle trên máy rồi chạy lại. Thường file nằm ở:

```text
~/.kaggle/kaggle.json
```

### Kéo bằng DVC

Repo đang cấu hình DVC remote ở S3:

```text
s3://mlops-data-storage/dvc-storage/
```

Nếu đã có quyền AWS, cấu hình credential trước:

```bash
aws configure
```

Hoặc export biến môi trường:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=ap-southeast-1
```

Kéo dữ liệu và artifact:

```bash
uv run dvc pull
```

Kiểm tra trạng thái:

```bash
uv run dvc status
```

Sau khi train lại và muốn đẩy artifact lên remote:

```bash
uv run dvc push
```

## Chạy MLflow local

MLflow dùng để lưu experiment khi train.

```bash
cd deployment/mlflow
docker compose up -d
cd ../..
```

Mở UI:

```text
http://localhost:5555
```

Nếu muốn tắt:

```bash
cd deployment/mlflow
docker compose down
cd ../..
```

## Chạy pipeline huấn luyện

Pipeline chính nằm trong `dvc.yaml`, gồm 3 stage:

1. `feature_engineering`: đọc dữ liệu raw, tạo thêm biến, chia train/valid/test theo mốc thời gian.
2. `train_models`: train các mô hình trong `configs/model_config.yaml`, rồi chọn model tốt nhất trên tập valid.
3. `tune_model`: tuning model tốt nhất, chọn ngưỡng dự đoán và lưu artifact cho API.

Chạy full pipeline:

```bash
uv run dvc repro
```

Các output chính:

```text
data/processed/*.parquet
reports/training/baseline_leaderboard.csv
reports/training/best_model.json
models/artifacts/*.pkl
models/trained/trained_model.pkl
models/trained/model_columns.pkl
models/trained/trained_model_meta.json
models/trained/tuning_pr_auc_by_trial.png
```

Nếu chỉ muốn kiểm tra pipeline có khớp lockfile không:

```bash
uv run dvc status
```

## Chạy API local

API cần các file model trong `models/trained` và `models/artifacts`. Nếu chưa có, chạy một trong hai lệnh này trước:

```bash
uv run dvc pull
```

hoặc:

```bash
uv run dvc repro
```

Chạy API:

```bash
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Kiểm tra health:

```bash
curl http://localhost:8000/health
```

Mở Swagger UI:

```text
http://localhost:8000/docs
```

Test một request dự đoán:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TX_TEST_001",
    "user_id": "USER_TEST",
    "hour_of_day": 2,
    "day_of_week": 5,
    "is_weekend": 1,
    "amount": 250.0,
    "card_present": 0,
    "device_known": 0,
    "is_foreign_txn": 1,
    "has_2fa": 0,
    "time_since_last_s": 120.0,
    "velocity_1h": 4.0,
    "amount_vs_avg_ratio": 2.5,
    "account_age_days": 120,
    "credit_limit": 5000.0,
    "merchant_category": "electronics",
    "merchant_country": "US",
    "device_type": "mobile",
    "mcc_code": 5732,
    "ip_risk_score": 0.72
  }'
```

Các endpoint chính:

- `GET /health`: kiểm tra API và model đã nạp chưa
- `POST /predict`: dự đoán một giao dịch
- `POST /batch`: dự đoán nhiều giao dịch
- `POST /feedback`: ghi nhận nhãn thực tế sau review
- `GET /metrics`: metric cho Prometheus
- `GET /docs`: giao diện Swagger

## Chạy giao diện Streamlit

Mở API trước, rồi chạy Streamlit ở terminal khác:

```bash
FRAUD_API_URL=http://localhost:8000 uv run streamlit run src/streamlit/app.py
```

Streamlit chỉ là lớp giao diện. Logic dự đoán vẫn nằm ở FastAPI.

## Chạy Docker local

Build image:

```bash
docker build -t fraudshield-api:local .
```

Chạy container:

```bash
docker run --rm -p 8000:8000 --env-file .env fraudshield-api:local
```

Kiểm tra:

```bash
curl http://localhost:8000/health
```

Lưu ý: image cần có model artifact trong context build. Nếu chưa có `models/trained` và `models/artifacts`, kéo bằng DVC hoặc train trước rồi mới build.

## Setup GCS và BigQuery cho monitoring

API lưu prediction và feedback thành Parquet trên GCS:

```text
gs://<GCS_BUCKET_NAME>/predictions/dt=YYYY-MM-DD/hour=HH/*.parquet
gs://<GCS_BUCKET_NAME>/feedbacks/dt=YYYY-MM-DD/hour=HH/*.parquet
```

Drift report cũng được upload lên GCS:

```text
gs://<GCS_BUCKET_NAME>/drift-reports/archive/...
gs://<GCS_BUCKET_NAME>/drift-reports/latest/drift_report.html
```

Các bước setup cơ bản:

```bash
gcloud config set project <PROJECT_ID>
gcloud storage buckets create gs://<GCS_BUCKET_NAME> --location=asia-southeast1
bq --location=US mk --dataset <PROJECT_ID>:fraud_monitoring
```

Service account chạy API/job cần tối thiểu:

- Quyền ghi object vào bucket GCS, ví dụ `roles/storage.objectAdmin`
- Quyền chạy query BigQuery, ví dụ `roles/bigquery.jobUser`
- Quyền đọc dataset/table monitoring, ví dụ `roles/bigquery.dataViewer`

Drift job đang query bảng hoặc view:

```text
<PROJECT_ID>.<BQ_DATASET>.predictions_ext
```

Vì vậy cần tạo external table hoặc view `predictions_ext` đọc từ các file Parquet trong prefix `predictions`. Ví dụ hướng đi thường dùng là tạo external table trên URI:

```text
gs://<GCS_BUCKET_NAME>/predictions/*/*.parquet
```

Sau khi có dữ liệu prediction đủ nhiều, chạy drift report:

```bash
uv run python -m src.monitoring.run_drift_report
```

Output local:

```text
reports/drift_report.html
```

Nếu `GCS_BUCKET_NAME` đã cấu hình, report sẽ được upload lên GCS.

## Triển khai Kubernetes/GKE

Manifest nằm trong `deployment/k8s`.

Các file chính:

- `deployment.yaml`: chạy FastAPI container
- `service.yaml`: expose API bằng LoadBalancer
- `sa.yaml`: Kubernetes ServiceAccount có annotation Workload Identity
- `monitoring-cronjob.yaml`: chạy drift report theo lịch
- `pod-monitoring.yaml`: cấu hình Cloud Managed Prometheus scrape `/metrics`
- `grafana/grafana-values.yaml`: cấu hình Grafana qua Helm

Chuẩn bị GKE:

```bash
gcloud container clusters create fraud-detection-cluster \
  --region <GCP_REGION> \
  --num-nodes 2

gcloud container clusters get-credentials fraud-detection-cluster \
  --region <GCP_REGION>
```

Tạo Docker Hub pull secret:

```bash
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<DOCKERHUB_USERNAME> \
  --docker-password=<DOCKERHUB_TOKEN>
```

Apply service account:

```bash
kubectl apply -f deployment/k8s/sa.yaml
```

Render image rồi deploy:

```bash
export IMAGE_NAME=<dockerhub-user>/<repo>:<tag>

sed "s|IMAGE_PLACEHOLDER|$IMAGE_NAME|g" deployment/k8s/deployment.yaml | kubectl apply -f -
kubectl apply -f deployment/k8s/service.yaml
sed "s|IMAGE_PLACEHOLDER|$IMAGE_NAME|g" deployment/k8s/monitoring-cronjob.yaml | kubectl apply -f -
kubectl apply -f deployment/k8s/pod-monitoring.yaml
```

Kiểm tra rollout:

```bash
kubectl rollout status deployment/fraud-api-deployment
kubectl get pods -o wide
kubectl get service fraud-api-service
```

Chạy drift job thủ công từ CronJob:

```bash
kubectl delete job drift-report-initial --ignore-not-found=true
kubectl create job drift-report-initial --from=cronjob/drift-report-job
kubectl logs -f -l job-name=drift-report-initial
```

## Grafana

Grafana dùng Helm chart chính thức, values nằm ở:

```text
deployment/k8s/grafana/grafana-values.yaml
```

Deploy:

```bash
kubectl apply -f deployment/k8s/grafana/grafana-sa.yaml

helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install grafana grafana/grafana \
  -n default \
  -f deployment/k8s/grafana/grafana-values.yaml \
  --set adminPassword="<GRAFANA_ADMIN_PASSWORD>"
```

Kiểm tra service:

```bash
kubectl get service grafana
```

## GitHub Actions cần secret gì

Repo có 3 workflow:

- `ci.yaml`: kiểm tra dependency, DVC graph và compile source
- `ct.yaml`: kéo dữ liệu/artifact, chạy full training, đẩy artifact lên S3
- `cd.yaml`: build image, push Docker Hub, deploy lên GKE và chạy drift job

Các secret cần chuẩn bị nếu muốn chạy CT/CD hoàn chỉnh:

| Secret | Dùng ở đâu |
| --- | --- |
| `LOCAL_AWS_ACCESS_KEY_ID` | DVC pull/push trên S3 |
| `LOCAL_AWS_SECRET_ACCESS_KEY` | DVC pull/push trên S3 |
| `S3_BUCKET_NAME` | Tham chiếu bucket S3 trong workflow |
| `TEST_DOCKERHUB_USERNAME` | Push/pull Docker image |
| `TEST_DOCKERHUB_REPO` | Tên repo Docker Hub |
| `TEST_DOCKERHUB_TOKEN` | Token Docker Hub |
| `WIF_PROVIDER` | Workload Identity Federation cho GitHub Actions |
| `WIF_SERVICE_ACCOUNT` | Service account Google Cloud để deploy |
| `GKE_CLUSTER_NAME` | Tên GKE cluster |
| `GCP_REGION` | Region của GKE |
| `GRAFANA_ADMIN_PASSWORD` | Mật khẩu admin Grafana |

## Checklist test hoàn chỉnh

Chạy local từ đầu:

```bash
uv sync
cp .env.example .env
uv run python src/data/get_data.py
cd deployment/mlflow
docker compose up -d
cd ../..
uv run dvc repro
uv run dvc status
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Ở terminal khác:

```bash
curl http://localhost:8000/health
FRAUD_API_URL=http://localhost:8000 uv run streamlit run src/streamlit/app.py
```

Nếu muốn test cloud/monitoring:

```bash
uv run dvc push
uv run python -m src.monitoring.run_drift_report
docker build -t fraudshield-api:local .
kubectl get pods
kubectl get service fraud-api-service
```