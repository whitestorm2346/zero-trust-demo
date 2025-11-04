**設定變數**

```bash
PROJECT_ID=zero-trust-demo-475103  \
REGION=asia-east1 \
ZONE=$REGION-b \
REPO=gcp-app \
CLUSTER=zta-cluster
```

**建立 GKE cluster（Cloud 原生環境）**

```bash
gcloud container clusters create $CLUSTER \
  --zone=$ZONE \
  --num-nodes=1 \
  --machine-type=e2-standard-2 \
  --disk-type=pd-standard \
  --disk-size=30
```

**取得 cluster 憑證 (讓本機可以使用 `kubectl apply`)**

```bash
gcloud container clusters get-credentials $CLUSTER --zone=$ZONE --project=$PROJECT_ID
kubectl get nodes
```

看到節點列表就表示連線成功。

**建 Artifact Registry（放 image 用）**

```bash
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description="ZTA demo repo" || true

gcloud auth configure-docker $REGION-docker.pkg.dev -q
```

**Build & Push 兩個服務的 image**

```bash
# service-a
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-a:latest gcp-app/service-a
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-a:latest

# service-b
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-b:latest gcp-app/service-b
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/service-b:latest
```

**安裝 Istio**

```bash
istioctl install -y \
  --set profile=demo \
  --set values.gateways.istio-ingressgateway.type=LoadBalancer \
  --set values.gateways.istio-egressgateway.enabled=true
```

**啟用 sidecar**

```bash
kubectl apply -f gcp-app/k8s/namespace.yaml
kubectl apply -f gcp-app/k8s/istio/ns-injection.yaml
kubectl apply -f gcp-app/k8s/istio/peer-authn-mtls.yaml
```

**部署兩個 services**

```bash
kubectl apply -f gcp-app/k8s/svc-b.yaml
kubectl apply -f gcp-app/k8s/svc-a.yaml

kubectl rollout restart deploy/service-b
kubectl rollout restart deploy/service-a
kubectl get pods
```

應該會看到兩個 Pod 都是 `2/2 READY`（代表 sidecar 已注入）。

**建立 ingress**

```bash
kubectl apply -f gcp-app/k8s/istio/ingress-a.yaml
kubectl get svc -n istio-system
```

複製 `EXTERNAL-IP` 記下來，用來測試網站。

**建立 egress**

```bash
kubectl apply -f gcp-app/k8s/istio/egress-httpbin.yaml
kubectl apply -f gcp-app/k8s/istio/egress-route.yaml
```

**套用 Identity-tier Policy（加強側邊安全）**

```bash
kubectl apply -f gcp-app/k8s/istio/authz-identity.yaml
```

**清理 節省費用**

```bash
kubectl delete -f gcp-app/k8s/istio/ingress-a.yaml
gcloud container clusters delete $CLUSTER --zone=$ZONE --project=$PROJECT_ID
```

**網頁測試**

```txt
http://<EXTERNAL-IP>/
```

**CURL 測試**

```bash
kubectl run curlpod --image=curlimages/curl -it --rm -- sh

curl -v http://service-b:8080/public    # 要 200
curl -v http://service-b:8080/private   # 要 403
```

**Local Docker 測試**

```bash
cd gcp-app/service-a
docker build -t service-a:local .
docker run -p 8080:8080 service-a:local
```
